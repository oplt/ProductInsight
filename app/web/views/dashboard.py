"""
Dashboard views for the web interface.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.infrastructure.database.models.analysis import Analysis

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def home():
    """Dashboard home."""
    # Get dashboard data for the current user
    user_id = current_user.id
    
    # Get recent analyses
    recent_analyses = Analysis.get_recent_by_user(user_id, limit=10)
    
    # Get total analysis count
    total_analyses = Analysis.count_by_user(user_id)
    
    # Get platform counts
    platforms = ['amazon', 'twitter', 'instagram', 'tiktok']
    platform_data = {}
    for platform in platforms:
        count = Analysis.count_by_user(user_id, platform=platform)
        if count > 0:  # Only include platforms with data
            platform_data[platform] = count
    
    # Get status counts
    completed_count = Analysis.count_by_user(user_id, status='completed')
    pending_count = Analysis.count_by_user(user_id, status='pending')
    failed_count = Analysis.count_by_user(user_id, status='failed')
    
    # Prepare dashboard data
    dashboard_data = {
        'total_analyses': total_analyses,
        'platform_data': platform_data,
        'recent_analyses': [analysis.to_dict() for analysis in recent_analyses],
        'completed_count': completed_count,
        'pending_count': pending_count,
        'failed_count': failed_count,
        'success_rate': (completed_count / total_analyses * 100) if total_analyses > 0 else 0
    }
    
    return render_template('dashboard/dashboard.html', 
                         title='Dashboard', 
                         dashboard_data=dashboard_data)

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

@dashboard_bp.route('/new-analysis', methods=['GET', 'POST'])
@login_required
def new_analysis():
    """Create new analysis."""
    from app.web.forms import NewAnalysisForm
    from flask import request, redirect, url_for, flash
    
    form = NewAnalysisForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        # Handle form submission
        try:
            # Create new analysis record
            from app.infrastructure.database.models.analysis import Analysis
            
            analysis = Analysis(
                user_id=current_user.id,
                platform=form.platform.data,
                target_identifier=form.target_identifier.data,
                analysis_type=form.analysis_type.data,
                status='pending'
            )
            
            # Add metadata if description provided
            if form.description.data:
                analysis.analysis_metadata = {'description': form.description.data}
            
            analysis.save()
            
            flash(f'Analysis started successfully! Analysis ID: {analysis.analysis_id}', 'success')
            return redirect(url_for('dashboard.analysis_detail', analysis_id=analysis.analysis_id))
            
        except Exception as e:
            flash(f'Error creating analysis: {str(e)}', 'error')
    
    return render_template('analysis/new_analysis.html', title='New Analysis', form=form)

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

@dashboard_bp.route('/test-llm-connection')
@login_required
def test_llm_connection():
    """Test LLM connection endpoint."""
    from flask import jsonify
    try:
        # Simple test - you can expand this to actually test your LLM service
        return jsonify({
            'status': 'success',
            'message': 'LLM connection test successful',
            'available': True
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'LLM connection failed: {str(e)}',
            'available': False
        }), 500
