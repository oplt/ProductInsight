"""
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
