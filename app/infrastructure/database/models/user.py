"""
User database model.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

from .base import BaseModel, db, TimestampMixin, JSONFieldMixin


class User(BaseModel, UserMixin, JSONFieldMixin):
    """User database model."""
    
    __tablename__ = 'users'
    
    # Basic information
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Profile information
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    
    # Status and role
    role = db.Column(db.String(20), default='user', nullable=False)
    status = db.Column(db.String(20), default='pending_verification', nullable=False)
    
    # Timestamps
    last_login_at = db.Column(db.DateTime)
    email_verified_at = db.Column(db.DateTime)
    
    # Usage and quotas
    analysis_quota = db.Column(db.Integer, default=100, nullable=False)
    used_analyses_this_month = db.Column(db.Integer, default=0, nullable=False)
    storage_quota_mb = db.Column(db.Integer, default=1000, nullable=False)
    used_storage_mb = db.Column(db.Integer, default=0, nullable=False)
    
    # JSON fields for settings
    preferences = db.Column(db.JSON, default=dict)
    notification_settings = db.Column(db.JSON, default=dict)
    
    # Relationships
    analyses = db.relationship('Analysis', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    platform_configs = db.relationship('PlatformConfig', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """Initialize user with default settings."""
        super().__init__(**kwargs)
        
        # Set default notification settings
        if not self.notification_settings:
            self.notification_settings = {
                'email_notifications': True,
                'analysis_complete': True,
                'weekly_summary': True,
                'security_alerts': True
            }
        
        # Set default preferences
        if not self.preferences:
            self.preferences = {
                'theme': 'light',
                'language': 'en',
                'timezone': 'UTC'
            }
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def activate(self):
        """Activate user account."""
        self.status = 'active'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def verify_email(self):
        """Mark email as verified."""
        self.email_verified_at = datetime.utcnow()
        if self.status == 'pending_verification':
            self.status = 'active'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def increment_analysis_usage(self):
        """Increment monthly analysis usage."""
        self.used_analyses_this_month += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def reset_monthly_usage(self):
        """Reset monthly analysis usage."""
        self.used_analyses_this_month = 0
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def can_create_analysis(self):
        """Check if user can create new analysis."""
        return (self.status == 'active' and 
                self.used_analyses_this_month < self.analysis_quota)
    
    def get_remaining_analyses(self):
        """Get remaining analyses for this month."""
        return max(0, self.analysis_quota - self.used_analyses_this_month)
    
    def get_storage_usage_percentage(self):
        """Get storage usage as percentage."""
        if self.storage_quota_mb == 0:
            return 0.0
        return (self.used_storage_mb / self.storage_quota_mb) * 100.0
    
    def get_full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def is_admin(self):
        """Check if user is admin."""
        return self.role == 'admin'
    
    def is_premium(self):
        """Check if user has premium role."""
        return self.role in ['premium', 'admin']
    
    def is_active_user(self):
        """Check if user is active."""
        return self.status == 'active'
    
    def is_email_verified(self):
        """Check if email is verified."""
        return self.email_verified_at is not None
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary."""
        data = super().to_dict(exclude_fields=['password_hash'] if not include_sensitive else [])
        
        # Add computed fields
        data.update({
            'full_name': self.get_full_name(),
            'remaining_analyses': self.get_remaining_analyses(),
            'storage_usage_percentage': self.get_storage_usage_percentage(),
            'email_verified': self.is_email_verified(),
            'is_admin': self.is_admin(),
            'is_premium': self.is_premium(),
            'is_active': self.is_active_user()
        })
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'


class PlatformConfig(BaseModel, JSONFieldMixin):
    """Platform configuration model for storing API credentials."""
    
    __tablename__ = 'platform_configs'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    platform = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Encrypted configuration data
    config_data = db.Column(db.JSON, nullable=False)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform', name='uq_user_platform'),
    )
    
    def set_config(self, config_dict):
        """Set configuration data."""
        self.config_data = config_dict
        self.updated_at = datetime.utcnow()
    
    def get_config(self):
        """Get configuration data."""
        return self.config_data or {}
    
    def is_configured(self):
        """Check if platform is properly configured."""
        config = self.get_config()
        
        # Platform-specific validation
        if self.platform == 'twitter':
            required_fields = ['api_key', 'api_secret', 'access_token', 'access_token_secret']
        elif self.platform == 'instagram':
            required_fields = ['access_token', 'client_id']
        elif self.platform == 'tiktok':
            required_fields = ['client_key', 'client_secret']
        elif self.platform == 'amazon':
            required_fields = ['access_key', 'secret_key']
        else:
            required_fields = []
        
        return all(config.get(field) for field in required_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert platform config to dictionary."""
        data = super().to_dict()
        data['is_configured'] = self.is_configured()
        
        # Mask sensitive data unless explicitly requested
        if not include_sensitive and self.config_data:
            masked_config = {}
            for key, value in self.config_data.items():
                if value and len(str(value)) > 4:
                    masked_config[key] = str(value)[:4] + '*' * (len(str(value)) - 4)
                else:
                    masked_config[key] = '*' * len(str(value)) if value else ''
            data['config_data'] = masked_config
        
        return data
    
    def __repr__(self):
        return f'<PlatformConfig {self.user_id}:{self.platform}>'
