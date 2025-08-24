# Web views package
from .auth import auth_bp
from .main import main_bp
from .dashboard import dashboard_bp
from .errors import errors_bp

__all__ = ['auth_bp', 'main_bp', 'dashboard_bp', 'errors_bp']