"""
Request validation middleware for API endpoints.
"""

from functools import wraps
from flask import request, jsonify
from marshmallow import Schema, ValidationError
import logging

logger = logging.getLogger(__name__)


def validate_json(schema_class):
    """
    Decorator to validate JSON request body against a Marshmallow schema.
    
    Args:
        schema_class: Marshmallow schema class for validation
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check content type
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Content-Type must be application/json'
                }), 400
            
            # Check if request has JSON data
            if not request.json:
                return jsonify({
                    'status': 'error',
                    'message': 'Request body must contain valid JSON'
                }), 400
            
            # Validate against schema
            try:
                schema = schema_class()
                validated_data = schema.load(request.json)
                
                # Add validated data to request object
                request.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"Validation error in {f.__name__}: {e.messages}")
                return jsonify({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': e.messages
                }), 400
            
            except Exception as e:
                logger.error(f"Unexpected validation error in {f.__name__}: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Validation error'
                }), 400
        
        return decorated_function
    return decorator


def validate_query_params(schema_class):
    """
    Decorator to validate query parameters against a Marshmallow schema.
    
    Args:
        schema_class: Marshmallow schema class for validation
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()
                validated_params = schema.load(request.args)
                
                # Add validated params to request object
                request.validated_params = validated_params
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"Query param validation error in {f.__name__}: {e.messages}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid query parameters',
                    'errors': e.messages
                }), 400
            
            except Exception as e:
                logger.error(f"Unexpected query param validation error in {f.__name__}: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': 'Query parameter validation error'
                }), 400
        
        return decorated_function
    return decorator


def validate_file_upload(allowed_extensions=None, max_file_size=None):
    """
    Decorator to validate file uploads.
    
    Args:
        allowed_extensions: List of allowed file extensions (e.g., ['jpg', 'png'])
        max_file_size: Maximum file size in bytes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No file provided'
                }), 400
            
            file = request.files['file']
            
            # Check if file is selected
            if file.filename == '':
                return jsonify({
                    'status': 'error',
                    'message': 'No file selected'
                }), 400
            
            # Check file extension
            if allowed_extensions:
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if file_ext not in allowed_extensions:
                    return jsonify({
                        'status': 'error',
                        'message': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
                    }), 400
            
            # Check file size
            if max_file_size:
                # Seek to end to get file size
                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                
                if file_size > max_file_size:
                    return jsonify({
                        'status': 'error',
                        'message': f'File too large. Maximum size: {max_file_size} bytes'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_fields(*required_fields):
    """
    Decorator to ensure required fields are present in JSON request.
    
    Args:
        required_fields: Field names that must be present
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Content-Type must be application/json'
                }), 400
            
            data = request.json or {}
            missing_fields = []
            
            for field in required_fields:
                if field not in data or data[field] is None or data[field] == '':
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'missing_fields': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def sanitize_input(f):
    """
    Decorator to sanitize input data.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.is_json and request.json:
            # Sanitize JSON data
            request.json = _sanitize_dict(request.json)
        
        return f(*args, **kwargs)
    
    return decorated_function


def _sanitize_dict(data):
    """Recursively sanitize dictionary data."""
    if isinstance(data, dict):
        return {key: _sanitize_value(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_sanitize_value(item) for item in data]
    else:
        return _sanitize_value(data)


def _sanitize_value(value):
    """Sanitize a single value."""
    if isinstance(value, str):
        # Basic XSS prevention
        value = value.replace('<script', '&lt;script')
        value = value.replace('</script>', '&lt;/script&gt;')
        value = value.replace('javascript:', '')
        value = value.replace('onload=', '')
        value = value.replace('onerror=', '')
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Limit string length
        if len(value) > 10000:  # Reasonable limit
            value = value[:10000]
    
    elif isinstance(value, (dict, list)):
        value = _sanitize_dict(value)
    
    return value


class ValidationError(Exception):
    """Custom validation error."""
    
    def __init__(self, message, errors=None):
        self.message = message
        self.errors = errors or {}
        super().__init__(self.message)


def validate_pagination_params():
    """Validate common pagination parameters."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get pagination params with defaults
                limit = request.args.get('limit', 50, type=int)
                offset = request.args.get('offset', 0, type=int)
                
                # Validate limits
                if limit < 1 or limit > 100:
                    return jsonify({
                        'status': 'error',
                        'message': 'Limit must be between 1 and 100'
                    }), 400
                
                if offset < 0:
                    return jsonify({
                        'status': 'error',
                        'message': 'Offset must be 0 or greater'
                    }), 400
                
                # Add to request object
                request.pagination = {
                    'limit': limit,
                    'offset': offset
                }
                
                return f(*args, **kwargs)
                
            except ValueError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid pagination parameters'
                }), 400
        
        return decorated_function
    return decorator


def validate_date_range():
    """Validate date range parameters."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from datetime import datetime
            
            try:
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')
                
                parsed_start = None
                parsed_end = None
                
                if start_date:
                    parsed_start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                
                if end_date:
                    parsed_end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                # Validate date range
                if parsed_start and parsed_end and parsed_start > parsed_end:
                    return jsonify({
                        'status': 'error',
                        'message': 'Start date must be before end date'
                    }), 400
                
                # Add to request object
                request.date_range = {
                    'start_date': parsed_start,
                    'end_date': parsed_end
                }
                
                return f(*args, **kwargs)
                
            except ValueError as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid date format: {str(e)}'
                }), 400
        
        return decorated_function
    return decorator


def validate_content_length(max_length=1024*1024):  # 1MB default
    """Validate request content length."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            content_length = request.content_length
            
            if content_length and content_length > max_length:
                return jsonify({
                    'status': 'error',
                    'message': f'Request too large. Maximum size: {max_length} bytes'
                }), 413
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
