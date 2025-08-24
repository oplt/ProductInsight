"""
Authentication middleware for API endpoints.
"""

from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
import jwt
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """Decorator to require authentication for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated via session (Flask-Login)
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # Check for API key or JWT token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        # Handle Bearer token
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            try:
                # Decode JWT token
                payload = jwt.decode(
                    token, 
                    current_app.config['JWT_SECRET_KEY'], 
                    algorithms=['HS256']
                )
                
                # Set user ID in request context
                request.user_id = payload.get('user_id')
                
                return f(*args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                return jsonify({
                    'status': 'error',
                    'message': 'Token has expired'
                }), 401
                
            except jwt.InvalidTokenError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid token'
                }), 401
        
        # Handle API key
        elif auth_header.startswith('ApiKey '):
            api_key = auth_header[7:]  # Remove 'ApiKey ' prefix
            
            # Validate API key (implement your API key validation logic)
            if validate_api_key(api_key):
                # Set user ID from API key
                request.user_id = get_user_id_from_api_key(api_key)
                return f(*args, **kwargs)
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid API key'
                }), 401
        
        return jsonify({
            'status': 'error',
            'message': 'Invalid authentication format'
        }), 401
    
    return decorated_function


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'API key required'
            }), 401
        
        if not validate_api_key(api_key):
            return jsonify({
                'status': 'error',
                'message': 'Invalid API key'
            }), 401
        
        # Set user context
        request.user_id = get_user_id_from_api_key(api_key)
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        if not current_user.is_admin():
            return jsonify({
                'status': 'error',
                'message': 'Admin privileges required'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_premium(f):
    """Decorator to require premium privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        if not current_user.is_premium():
            return jsonify({
                'status': 'error',
                'message': 'Premium account required'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_email_verified(f):
    """Decorator to require email verification."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        
        if not current_user.is_email_verified():
            return jsonify({
                'status': 'error',
                'message': 'Email verification required'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key.
    
    This is a placeholder implementation. In a real application, you would:
    1. Query the database for the API key
    2. Check if it's active and not expired
    3. Validate any rate limits or restrictions
    """
    # TODO: Implement proper API key validation
    # For now, accept any key that starts with 'pi_' (ProductInsights)
    return api_key.startswith('pi_') and len(api_key) >= 20


def get_user_id_from_api_key(api_key: str) -> int:
    """
    Get user ID from API key.
    
    This is a placeholder implementation.
    """
    # TODO: Implement proper API key to user ID mapping
    # For now, return a default user ID
    return 1


def generate_jwt_token(user_id: int, expires_in_hours: int = 24) -> str:
    """Generate JWT token for user."""
    from datetime import datetime, timedelta
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
        'iat': datetime.utcnow(),
        'iss': 'ProductInsights'
    }
    
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token


def decode_jwt_token(token: str) -> dict:
    """Decode JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


class APIKeyManager:
    """Manage API keys for users."""
    
    @staticmethod
    def generate_api_key(user_id: int) -> str:
        """Generate a new API key for user."""
        import secrets
        import string
        
        # Generate random key with ProductInsights prefix
        alphabet = string.ascii_letters + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(32))
        api_key = f"pi_{user_id}_{random_part}"
        
        # TODO: Store in database with metadata (created_at, last_used, etc.)
        
        return api_key
    
    @staticmethod
    def revoke_api_key(api_key: str) -> bool:
        """Revoke an API key."""
        # TODO: Mark API key as revoked in database
        return True
    
    @staticmethod
    def list_user_api_keys(user_id: int) -> list:
        """List all API keys for a user."""
        # TODO: Query database for user's API keys
        return []
