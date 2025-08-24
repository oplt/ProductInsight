"""
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
from app.infrastructure.database.models.analysis import Analysis


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__, 
                template_folder='web/templates',
                static_folder='web/static')
    
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
