"""
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
