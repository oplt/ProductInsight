"""
User domain entities.
Contains the core business objects for the user domain.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum
import re


class UserRole(Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    PREMIUM = "premium"


class UserStatus(Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class UserEntity:
    """Core user domain entity."""
    id: Optional[int]
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    
    # Profile information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    # Settings and preferences
    preferences: Dict[str, Any] = field(default_factory=dict)
    notification_settings: Dict[str, bool] = field(default_factory=lambda: {
        'email_notifications': True,
        'analysis_complete': True,
        'weekly_summary': True,
        'security_alerts': True
    })
    
    # Usage limits and quotas
    analysis_quota: int = 100  # Monthly analysis limit
    used_analyses_this_month: int = 0
    storage_quota_mb: int = 1000  # Storage limit in MB
    used_storage_mb: int = 0
    
    def __post_init__(self):
        """Validate user entity after initialization."""
        self._validate_email()
        self._validate_username()
        
        # Set default avatar if not provided
        if not self.avatar_url:
            self.avatar_url = self._generate_default_avatar_url()
    
    def _validate_email(self):
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")
    
    def _validate_username(self):
        """Validate username format."""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if len(self.username) > 50:
            raise ValueError("Username must be less than 50 characters")
        
        username_pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(username_pattern, self.username):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
    
    def _generate_default_avatar_url(self) -> str:
        """Generate default avatar URL."""
        return f"https://ui-avatars.com/api/?name={self.username}&background=007bff&color=fff&size=200"
    
    def activate(self):
        """Activate user account."""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate user account."""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def suspend(self):
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
    
    def verify_email(self):
        """Mark email as verified."""
        self.email_verified_at = datetime.utcnow()
        if self.status == UserStatus.PENDING_VERIFICATION:
            self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_profile(self, first_name: Optional[str] = None,
                      last_name: Optional[str] = None,
                      bio: Optional[str] = None,
                      avatar_url: Optional[str] = None):
        """Update user profile information."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if bio is not None:
            if len(bio) > 500:
                raise ValueError("Bio must be less than 500 characters")
            self.bio = bio
        if avatar_url is not None:
            self.avatar_url = avatar_url
        
        self.updated_at = datetime.utcnow()
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences."""
        self.preferences.update(preferences)
        self.updated_at = datetime.utcnow()
    
    def update_notification_settings(self, settings: Dict[str, bool]):
        """Update notification settings."""
        self.notification_settings.update(settings)
        self.updated_at = datetime.utcnow()
    
    def increment_analysis_usage(self):
        """Increment monthly analysis usage."""
        self.used_analyses_this_month += 1
        self.updated_at = datetime.utcnow()
    
    def reset_monthly_usage(self):
        """Reset monthly analysis usage (called at month start)."""
        self.used_analyses_this_month = 0
        self.updated_at = datetime.utcnow()
    
    def can_create_analysis(self) -> bool:
        """Check if user can create new analysis."""
        if self.status != UserStatus.ACTIVE:
            return False
        
        return self.used_analyses_this_month < self.analysis_quota
    
    def get_remaining_analyses(self) -> int:
        """Get remaining analyses for this month."""
        return max(0, self.analysis_quota - self.used_analyses_this_month)
    
    def get_storage_usage_percentage(self) -> float:
        """Get storage usage as percentage."""
        if self.storage_quota_mb == 0:
            return 0.0
        return (self.used_storage_mb / self.storage_quota_mb) * 100.0
    
    def can_upload_file(self, file_size_mb: int) -> bool:
        """Check if user can upload file of given size."""
        return (self.used_storage_mb + file_size_mb) <= self.storage_quota_mb
    
    def get_full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    def is_premium(self) -> bool:
        """Check if user has premium role."""
        return self.role in [UserRole.PREMIUM, UserRole.ADMIN]
    
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE
    
    def is_email_verified(self) -> bool:
        """Check if email is verified."""
        return self.email_verified_at is not None
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert entity to dictionary for serialization."""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email if include_sensitive else self._mask_email(),
            'role': self.role.value,
            'status': self.status.value,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_full_name(),
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
            'email_verified': self.is_email_verified(),
            'analysis_quota': self.analysis_quota,
            'used_analyses_this_month': self.used_analyses_this_month,
            'remaining_analyses': self.get_remaining_analyses(),
            'storage_quota_mb': self.storage_quota_mb,
            'used_storage_mb': self.used_storage_mb,
            'storage_usage_percentage': self.get_storage_usage_percentage(),
            'preferences': self.preferences,
            'notification_settings': self.notification_settings
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data
    
    def _mask_email(self) -> str:
        """Mask email for public display."""
        local, domain = self.email.split('@')
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1] if len(local) > 2 else local
        return f"{masked_local}@{domain}"


@dataclass
class UserSession:
    """User session entity."""
    id: Optional[str]
    user_id: int
    session_token: str
    ip_address: str
    user_agent: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow())
    last_activity_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def refresh(self, duration_hours: int = 24):
        """Refresh session expiration."""
        self.expires_at = datetime.utcnow() + datetime.timedelta(hours=duration_hours)
        self.last_activity_at = datetime.utcnow()
    
    def invalidate(self):
        """Invalidate session."""
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'is_active': self.is_active,
            'is_expired': self.is_expired()
        }
