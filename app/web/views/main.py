"""
Main views for the web interface.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/home')
def home():
    """Home page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return render_template('home.html', title='Home')
