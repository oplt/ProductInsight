# Database models package
# Import all models to ensure they are registered with SQLAlchemy

from .base import db, BaseModel
from .user import User, PlatformConfig
from .analysis import Analysis, AnalysisMetricsSnapshot

# Export all models
__all__ = [
    'db',
    'BaseModel', 
    'User',
    'PlatformConfig',
    'Analysis',
    'AnalysisMetricsSnapshot'
]