"""
Analysis forms for web interface.
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError


class NewAnalysisForm(FlaskForm):
    """Form for creating a new content analysis."""
    
    platform = SelectField(
        'Platform',
        choices=[
            ('', 'Select Platform'),
            ('amazon', 'Amazon Reviews'),
            ('twitter', 'Twitter Analysis'),
            ('instagram', 'Instagram Analysis'),
            ('tiktok', 'TikTok Analysis')
        ],
        validators=[DataRequired(message='Please select a platform')],
        render_kw={'class': 'form-control'}
    )
    
    target_identifier = StringField(
        'Target Identifier',
        validators=[
            DataRequired(message='Please enter a target identifier'),
            Length(min=1, max=500, message='Target identifier must be between 1 and 500 characters')
        ],
        render_kw={
            'class': 'form-control',
            'placeholder': 'e.g., @username, product ASIN, #hashtag'
        }
    )
    
    analysis_type = SelectField(
        'Analysis Type',
        choices=[
            ('content_analysis', 'Content Analysis'),
            ('sentiment_analysis', 'Sentiment Analysis'),
            ('trend_analysis', 'Trend Analysis'),
            ('engagement_analysis', 'Engagement Analysis')
        ],
        default='content_analysis',
        validators=[DataRequired()],
        render_kw={'class': 'form-control'}
    )
    
    description = TextAreaField(
        'Description (Optional)',
        render_kw={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional description for this analysis...'
        }
    )
    
    submit = SubmitField(
        'Start Analysis',
        render_kw={'class': 'btn btn-primary'}
    )
    
    def validate_target_identifier(self, field):
        """Custom validation for target identifier based on platform."""
        platform = self.platform.data
        target = field.data.strip()
        
        if not target:
            return
        
        # Platform-specific validation
        if platform == 'amazon':
            # Amazon ASIN should be 10 characters alphanumeric
            if len(target) != 10 or not target.isalnum():
                raise ValidationError('Amazon ASIN must be exactly 10 alphanumeric characters')
        
        elif platform == 'twitter':
            # Twitter usernames start with @ or can be search terms
            if target.startswith('@') and len(target) < 2:
                raise ValidationError('Twitter username must have at least one character after @')
        
        elif platform == 'instagram':
            # Instagram usernames start with @ or hashtags with #
            if target.startswith('@') and len(target) < 2:
                raise ValidationError('Instagram username must have at least one character after @')
            elif target.startswith('#') and len(target) < 2:
                raise ValidationError('Instagram hashtag must have at least one character after #')


class AnalysisConfigForm(FlaskForm):
    """Form for configuring analysis parameters."""
    
    content_limit = SelectField(
        'Content Limit',
        choices=[
            ('10', '10 items'),
            ('25', '25 items'),
            ('50', '50 items'),
            ('100', '100 items'),
            ('250', '250 items')
        ],
        default='50',
        validators=[DataRequired()],
        render_kw={'class': 'form-control'}
    )
    
    time_range = SelectField(
        'Time Range',
        choices=[
            ('1d', 'Last 24 hours'),
            ('3d', 'Last 3 days'),
            ('1w', 'Last week'),
            ('1m', 'Last month'),
            ('3m', 'Last 3 months'),
            ('all', 'All time')
        ],
        default='1w',
        validators=[DataRequired()],
        render_kw={'class': 'form-control'}
    )
    
    include_replies = SelectField(
        'Include Replies',
        choices=[
            ('yes', 'Yes'),
            ('no', 'No')
        ],
        default='no',
        render_kw={'class': 'form-control'}
    )
    
    language_filter = SelectField(
        'Language Filter',
        choices=[
            ('', 'All Languages'),
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('it', 'Italian'),
            ('pt', 'Portuguese'),
            ('tr', 'Turkish')
        ],
        default='en',
        render_kw={'class': 'form-control'}
    )
