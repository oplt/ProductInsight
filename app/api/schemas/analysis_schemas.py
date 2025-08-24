"""
Marshmallow schemas for analysis API endpoints.
"""

from marshmallow import Schema, fields, validate, post_load, ValidationError
from datetime import datetime
from typing import Dict, Any

from app.core.analysis.entities.analysis import Platform, AnalysisType, AnalysisStatus


class CreateAnalysisSchema(Schema):
    """Schema for creating a new analysis."""
    
    platform = fields.Str(
        required=True,
        validate=validate.OneOf([p.value for p in Platform]),
        error_messages={
            'required': 'Platform is required',
            'validator_failed': 'Invalid platform. Must be one of: amazon, twitter, instagram, tiktok'
        }
    )
    
    target_identifier = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=500),
        error_messages={
            'required': 'Target identifier is required',
            'validator_failed': 'Target identifier must be between 1 and 500 characters'
        }
    )
    
    analysis_type = fields.Str(
        missing='comprehensive_analysis',
        validate=validate.OneOf([t.value for t in AnalysisType]),
        error_messages={
            'validator_failed': 'Invalid analysis type'
        }
    )
    
    config = fields.Dict(
        missing=dict,
        error_messages={
            'invalid': 'Config must be a valid JSON object'
        }
    )
    
    @post_load
    def validate_platform_target(self, data, **kwargs):
        """Custom validation for platform-specific target identifiers."""
        platform = data.get('platform')
        target = data.get('target_identifier')
        
        if platform == 'amazon':
            # Amazon product URLs or ASINs
            if not (target.startswith('http') or len(target) == 10):
                raise ValidationError(
                    'Amazon target must be a product URL or 10-character ASIN',
                    field_name='target_identifier'
                )
        
        elif platform == 'twitter':
            # Twitter usernames or URLs
            if not (target.startswith('@') or target.startswith('http')):
                raise ValidationError(
                    'Twitter target must be a username (@user) or profile URL',
                    field_name='target_identifier'
                )
        
        elif platform == 'instagram':
            # Instagram usernames or URLs
            if not (target.startswith('@') or target.startswith('http')):
                raise ValidationError(
                    'Instagram target must be a username (@user) or profile URL',
                    field_name='target_identifier'
                )
        
        elif platform == 'tiktok':
            # TikTok usernames or URLs
            if not (target.startswith('@') or target.startswith('http')):
                raise ValidationError(
                    'TikTok target must be a username (@user) or profile URL',
                    field_name='target_identifier'
                )
        
        return data


class UpdateAnalysisSchema(Schema):
    """Schema for updating an analysis."""
    
    config = fields.Dict(
        error_messages={
            'invalid': 'Config must be a valid JSON object'
        }
    )


class AnalysisResponseSchema(Schema):
    """Schema for analysis response."""
    
    id = fields.Int()
    analysis_id = fields.Str()
    platform = fields.Str()
    target_identifier = fields.Str()
    analysis_type = fields.Str()
    status = fields.Str()
    user_id = fields.Int()
    
    # Timestamps
    created_at = fields.DateTime(format='iso')
    updated_at = fields.DateTime(format='iso')
    started_at = fields.DateTime(format='iso', allow_none=True)
    completed_at = fields.DateTime(format='iso', allow_none=True)
    
    # Content and processing info
    content_count = fields.Int()
    processing_duration = fields.Float(allow_none=True)
    error_message = fields.Str(allow_none=True)
    retry_count = fields.Int()
    can_retry = fields.Bool()
    
    # Analysis results summary
    sentiment_summary = fields.Dict(allow_none=True)
    quality_score = fields.Float()
    executive_summary = fields.Str()
    
    # Configuration
    config = fields.Dict()


class AnalysisDetailResponseSchema(AnalysisResponseSchema):
    """Extended schema for detailed analysis response."""
    
    # Full results
    results = fields.Dict(allow_none=True)
    
    # Raw data (optional, for detailed view)
    raw_data = fields.List(fields.Dict(), allow_none=True)


class AnalysisListSchema(Schema):
    """Schema for analysis list response."""
    
    analyses = fields.List(fields.Nested(AnalysisResponseSchema))
    meta = fields.Dict()


class AnalysisQuerySchema(Schema):
    """Schema for analysis query parameters."""
    
    platform = fields.Str(
        validate=validate.OneOf([p.value for p in Platform]),
        error_messages={
            'validator_failed': 'Invalid platform'
        }
    )
    
    status = fields.Str(
        validate=validate.OneOf([s.value for s in AnalysisStatus]),
        error_messages={
            'validator_failed': 'Invalid status'
        }
    )
    
    limit = fields.Int(
        missing=50,
        validate=validate.Range(min=1, max=100),
        error_messages={
            'validator_failed': 'Limit must be between 1 and 100'
        }
    )
    
    offset = fields.Int(
        missing=0,
        validate=validate.Range(min=0),
        error_messages={
            'validator_failed': 'Offset must be 0 or greater'
        }
    )
    
    search = fields.Str(
        validate=validate.Length(max=100),
        error_messages={
            'validator_failed': 'Search query too long (max 100 characters)'
        }
    )
    
    start_date = fields.DateTime(
        format='iso',
        error_messages={
            'invalid': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
        }
    )
    
    end_date = fields.DateTime(
        format='iso',
        error_messages={
            'invalid': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
        }
    )
    
    @post_load
    def validate_date_range(self, data, **kwargs):
        """Validate date range."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError(
                'Start date must be before end date',
                field_name='start_date'
            )
        
        return data


class AnalysisMetricsSchema(Schema):
    """Schema for analysis metrics response."""
    
    total_content_items = fields.Int()
    processed_items = fields.Int()
    failed_items = fields.Int()
    success_rate = fields.Float()
    
    average_sentiment_score = fields.Float()
    sentiment_distribution = fields.Dict()
    
    top_emotions = fields.List(fields.Dict())
    quality_metrics = fields.Dict()
    engagement_stats = fields.Dict()
    processing_stats = fields.Dict()


class DashboardDataSchema(Schema):
    """Schema for dashboard data response."""
    
    total_analyses = fields.Int()
    platform_counts = fields.Dict()
    pending_count = fields.Int()
    success_rate = fields.Float()
    
    recent_analyses = fields.List(fields.Nested(AnalysisResponseSchema))
    metrics = fields.Nested(AnalysisMetricsSchema)


class ContentItemSchema(Schema):
    """Schema for individual content items."""
    
    id = fields.Str()
    platform = fields.Str()
    content_type = fields.Str()
    text = fields.Str()
    author = fields.Str(allow_none=True)
    timestamp = fields.DateTime(format='iso', allow_none=True)
    metadata = fields.Dict()
    engagement_metrics = fields.Dict()


class AnalysisResultSchema(Schema):
    """Schema for detailed analysis results."""
    
    basic_sentiment = fields.Dict()
    emotions = fields.Dict()
    intents = fields.Dict()
    aspect_sentiment = fields.Dict()
    content_quality = fields.Dict()
    opportunities_risks = fields.Dict()
    recommendations = fields.List(fields.Str())
    engagement_metrics = fields.Dict()
    executive_summary = fields.Str()
    llm_enhanced_insights = fields.Str()
    confidence_score = fields.Float()
    processing_time_seconds = fields.Float()


class ErrorResponseSchema(Schema):
    """Schema for error responses."""
    
    status = fields.Str()
    message = fields.Str()
    errors = fields.Dict(allow_none=True)
    timestamp = fields.DateTime(format='iso', missing=datetime.utcnow)


class SuccessResponseSchema(Schema):
    """Schema for success responses."""
    
    status = fields.Str()
    message = fields.Str(allow_none=True)
    data = fields.Raw(allow_none=True)
    meta = fields.Dict(allow_none=True)


class PaginationMetaSchema(Schema):
    """Schema for pagination metadata."""
    
    count = fields.Int()
    limit = fields.Int()
    offset = fields.Int()
    total = fields.Int(allow_none=True)
    has_next = fields.Bool(allow_none=True)
    has_prev = fields.Bool(allow_none=True)


# Helper functions for response formatting

def format_success_response(data=None, message=None, meta=None) -> Dict[str, Any]:
    """Format a success response."""
    response = {
        'status': 'success'
    }
    
    if message:
        response['message'] = message
    
    if data is not None:
        response['data'] = data
    
    if meta:
        response['meta'] = meta
    
    return response


def format_error_response(message: str, errors=None, status_code=400) -> Dict[str, Any]:
    """Format an error response."""
    response = {
        'status': 'error',
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if errors:
        response['errors'] = errors
    
    return response


def validate_analysis_id(analysis_id: str) -> bool:
    """Validate analysis ID format (UUID)."""
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(analysis_id))


class AnalysisIdValidator:
    """Custom validator for analysis IDs."""
    
    def __call__(self, value):
        if not validate_analysis_id(value):
            raise ValidationError('Invalid analysis ID format')
        return value
