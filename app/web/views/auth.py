"""
Authentication views for the web interface.
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.base import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.home'))
        else:
            flash('Invalid email or password.', 'error')
    
    # Create a mock form object for the template
    form = type('LoginForm', (), {
        'email': type('Field', (), {'data': ''})(),
        'password': type('Field', (), {'data': ''})(),
        'remember': type('Field', (), {'data': False})(),
        'submit': type('Field', (), {'label': {'text': 'Sign In'}})()
    })()
    
    return render_template('auth/simple_login.html', title='Login', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/simple_register.html', title='Register')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('auth/simple_register.html', title='Register')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        user.verify_email()  # Auto-verify for now
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    # Create a mock form object for the template
    form = type('RegisterForm', (), {
        'username': type('Field', (), {'data': ''})(),
        'email': type('Field', (), {'data': ''})(),
        'password': type('Field', (), {'data': ''})(),
        'confirm_password': type('Field', (), {'data': ''})(),
        'submit': type('Field', (), {'label': {'text': 'Sign Up'}})()
    })()
    
    return render_template('auth/simple_register.html', title='Register')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('main.home'))
