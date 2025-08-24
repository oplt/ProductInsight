#!/usr/bin/env python3
"""
Migration script to move from old architecture to new Clean Architecture.
This script will:
1. Create the new main application entry point
2. Migrate existing services to new infrastructure layer
3. Update imports and references
4. Clean up old structure
"""

import os
import shutil
import sys
from pathlib import Path

def create_new_main_app():
    """Create new main application entry point."""
    
    # Create new main application
    main_app_content = '''"""
ProductInsights - Main Application Factory
Clean Architecture Implementation
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

from config.base import get_config
from app.infrastructure.database.models.base import db
from app.infrastructure.database.models.user import User


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Other extensions
    mail = Mail()
    mail.init_app(app)
    
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    cors = CORS()
    cors.init_app(app)
    
    # Register blueprints
    from app.web.views.auth import auth_bp
    from app.web.views.main import main_bp
    from app.web.views.dashboard import dashboard_bp
    from app.web.views.errors import errors_bp
    from app.api.v1.analysis.routes import analysis_api
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(analysis_api)
    
    # Template filters and globals
    @app.template_filter('from_json')
    def from_json_filter(value):
        import json
        try:
            return json.loads(value) if isinstance(value, str) else value
        except:
            return {}
    
    @app.template_global()
    def csrf_token():
        from flask_wtf.csrf import generate_csrf
        return generate_csrf()
    
    # Initialize configuration
    config.init_app(app)
    
    return app
'''
    
    with open('app/main.py', 'w') as f:
        f.write(main_app_content)
    
    print("✅ Created new main application")

def migrate_services():
    """Migrate existing services to new infrastructure layer."""
    
    # Copy LLM service
    if os.path.exists('product_insight/services/llm_service.py'):
        os.makedirs('app/infrastructure/ai_services', exist_ok=True)
        shutil.copy2('product_insight/services/llm_service.py', 'app/infrastructure/ai_services/')
        print("✅ Migrated LLM service")
    
    # Copy advanced content analyzer
    if os.path.exists('product_insight/services/advanced_content_analyzer.py'):
        shutil.copy2('product_insight/services/advanced_content_analyzer.py', 'app/infrastructure/ai_services/')
        print("✅ Migrated advanced content analyzer")
    
    # Copy platform analysis services
    platform_services = ['amazon_review.py', 'twitter.py', 'instagram.py', 'tiktok.py']
    os.makedirs('app/infrastructure/external_apis', exist_ok=True)
    
    for service in platform_services:
        src_path = f'product_insight/analysis/{service}'
        if os.path.exists(src_path):
            shutil.copy2(src_path, 'app/infrastructure/external_apis/')
            print(f"✅ Migrated {service}")

def create_web_views():
    """Create web view controllers."""
    
    # Create auth views
    auth_views_content = '''"""
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
    
    return render_template('auth/login.html', title='Login')

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
            return render_template('auth/register.html', title='Register')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return render_template('auth/register.html', title='Register')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        user.verify_email()  # Auto-verify for now
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('main.home'))
'''
    
    os.makedirs('app/web/views', exist_ok=True)
    with open('app/web/views/auth.py', 'w') as f:
        f.write(auth_views_content)
    
    # Create main views
    main_views_content = '''"""
Main views for the web interface.
"""

from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/home')
def home():
    """Home page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return render_template('home.html', title='Home')
'''
    
    with open('app/web/views/main.py', 'w') as f:
        f.write(main_views_content)
    
    # Create dashboard views
    dashboard_views_content = '''"""
Dashboard views for the web interface.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def home():
    """Dashboard home."""
    return render_template('dashboard/dashboard.html', title='Dashboard')

@dashboard_bp.route('/profile')
@login_required
def profile():
    """User profile."""
    return render_template('dashboard/profile.html', title='Profile')

@dashboard_bp.route('/settings')
@login_required
def settings():
    """User settings."""
    return render_template('dashboard/settings.html', title='Settings')

@dashboard_bp.route('/new-analysis')
@login_required
def new_analysis():
    """Create new analysis."""
    return render_template('analysis/new_analysis.html', title='New Analysis')

@dashboard_bp.route('/analysis/<platform>')
@login_required
def platform_analysis(platform):
    """Platform analysis list."""
    return render_template('analysis/platform_analysis.html', title=f'{platform.title()} Analysis', platform=platform)

@dashboard_bp.route('/analysis/detail/<analysis_id>')
@login_required
def analysis_detail(analysis_id):
    """Analysis detail view."""
    return render_template('analysis/analysis_detail.html', title='Analysis Detail', analysis_id=analysis_id)
'''
    
    with open('app/web/views/dashboard.py', 'w') as f:
        f.write(dashboard_views_content)
    
    # Create error views
    error_views_content = '''"""
Error handlers for the web interface.
"""

from flask import Blueprint, render_template

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """404 error handler."""
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return render_template('errors/500.html'), 500
'''
    
    with open('app/web/views/errors.py', 'w') as f:
        f.write(error_views_content)
    
    print("✅ Created web view controllers")

def update_wsgi():
    """Create/update WSGI entry point."""
    
    wsgi_content = '''"""
WSGI entry point for ProductInsights application.
"""

import os
from app.main import create_app

# Create application instance
app = create_app(os.environ.get('FLASK_CONFIG'))

if __name__ == "__main__":
    app.run()
'''
    
    with open('wsgi.py', 'w') as f:
        f.write(wsgi_content)
    
    print("✅ Created WSGI entry point")

def update_run_py():
    """Update run.py to use new architecture."""
    
    run_content = '''#!/usr/bin/env python3
"""
Development server entry point for ProductInsights.
"""

import os
from app.main import create_app

if __name__ == '__main__':
    # Create application with development config
    app = create_app('development')
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
'''
    
    with open('run.py', 'w') as f:
        f.write(run_content)
    
    print("✅ Updated run.py")

def cleanup_old_structure():
    """Clean up old structure after migration."""
    
    print("🧹 Cleaning up old structure...")
    
    # Remove old product_insight folder
    if os.path.exists('product_insight'):
        shutil.rmtree('product_insight')
        print("✅ Removed old product_insight folder")
    
    # Remove old documentation files that are no longer needed
    old_docs = [
        'SETUP_GUIDE.md', 'LOGGING_GUIDE.md', 'CONTENT_ANALYSIS_RECOMMENDATIONS.md',
        'IMPLEMENTATION_GUIDE.md', 'TEMPLATE_INTEGRATION_SUMMARY.md',
        'ISSUE_RESOLVED.md', 'TEMPLATE_ISSUES_FIXED.md', 'ARCHITECTURE_RECOMMENDATIONS.md'
    ]
    
    for doc in old_docs:
        if os.path.exists(doc):
            os.remove(doc)
            print(f"✅ Removed {doc}")
    
    print("✅ Cleanup completed")

def main():
    """Main migration function."""
    print("🚀 Starting migration to Clean Architecture...")
    print("=" * 50)
    
    try:
        # Step 1: Create new main application
        create_new_main_app()
        
        # Step 2: Migrate services
        migrate_services()
        
        # Step 3: Create web views
        create_web_views()
        
        # Step 4: Update entry points
        update_wsgi()
        update_run_py()
        
        # Step 5: Clean up old structure
        cleanup_old_structure()
        
        print("=" * 50)
        print("🎉 Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Test the new application: python run.py")
        print("2. Run tests: make test")
        print("3. Try Docker: make docker-quickstart")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
