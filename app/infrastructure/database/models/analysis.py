"""
Analysis database model.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid

from .base import BaseModel, db, TimestampMixin, JSONFieldMixin


class Analysis(BaseModel, JSONFieldMixin):
    """Analysis database model."""
    
    __tablename__ = 'analyses'
    
    # Basic information
    analysis_id = db.Column(db.String(36), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Analysis configuration
    platform = db.Column(db.String(50), nullable=False, index=True)
    target_identifier = db.Column(db.String(500), nullable=False)  # URL, username, product ID, etc.
    analysis_type = db.Column(db.String(100), nullable=False, default='content_analysis')
    
    # Status and processing
    status = db.Column(db.String(50), default='pending', nullable=False, index=True)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Configuration and metadata
    config = db.Column(db.JSON, default=dict)
    analysis_metadata = db.Column(db.JSON, default=dict)
    
    # Content and results
    raw_data = db.Column(db.JSON)  # Stores ContentItem data
    results = db.Column(db.JSON)   # Stores AnalysisResult data
    
    # Performance metrics
    content_count = db.Column(db.Integer, default=0, nullable=False)
    processing_time_seconds = db.Column(db.Float, default=0.0)
    
    # Indexes for common queries
    __table_args__ = (
        db.Index('ix_user_platform', 'user_id', 'platform'),
        db.Index('ix_user_status', 'user_id', 'status'),
        db.Index('ix_platform_status', 'platform', 'status'),
        db.Index('ix_created_at_desc', 'created_at'),
    )
    
    def __init__(self, **kwargs):
        """Initialize analysis with defaults."""
        super().__init__(**kwargs)
        
        # Ensure analysis_id is set
        if not self.analysis_id:
            self.analysis_id = str(uuid.uuid4())
        
        # Set default config and metadata
        if not self.config:
            self.config = {}
        if not self.analysis_metadata:
            self.analysis_metadata = {}
    
    def start_processing(self):
        """Mark analysis as started."""
        self.status = 'in_progress'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def complete_successfully(self, results_dict, content_count=None):
        """Mark analysis as completed successfully."""
        self.status = 'completed'
        self.results = results_dict
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_message = None
        
        if content_count is not None:
            self.content_count = content_count
        
        # Calculate processing time
        if self.started_at:
            self.processing_time_seconds = (self.completed_at - self.started_at).total_seconds()
        
        db.session.commit()
    
    def fail_with_error(self, error_message):
        """Mark analysis as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.retry_count += 1
        db.session.commit()
    
    def cancel(self):
        """Cancel the analysis."""
        self.status = 'cancelled'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def can_retry(self, max_retries=3):
        """Check if analysis can be retried."""
        return self.status == 'failed' and self.retry_count < max_retries
    
    def get_processing_duration(self):
        """Get processing duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def is_completed(self):
        """Check if analysis is completed (successfully or failed)."""
        return self.status in ['completed', 'failed', 'cancelled']
    
    def get_sentiment_summary(self):
        """Get sentiment summary from results."""
        if not self.results:
            return None
        
        sentiment_data = self.results.get('basic_sentiment', {})
        return {
            'sentiment': sentiment_data.get('sentiment', 'neutral'),
            'confidence': sentiment_data.get('confidence', 0.0),
            'score': sentiment_data.get('score', 0.0)
        }
    
    def get_quality_score(self):
        """Get content quality score from results."""
        if not self.results:
            return 0.0
        
        quality_data = self.results.get('content_quality', {})
        return quality_data.get('quality_score', 0.0)
    
    def get_engagement_metrics(self):
        """Get engagement metrics from results."""
        if not self.results:
            return {}
        
        return self.results.get('engagement_metrics', {})
    
    def get_executive_summary(self):
        """Get executive summary from results."""
        if not self.results:
            return "No analysis results available"
        
        return self.results.get('executive_summary', 'Analysis completed')
    
    def update_raw_data(self, content_items):
        """Update raw data with content items."""
        self.raw_data = content_items
        self.content_count = len(content_items) if content_items else 0
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def add_metadata(self, key, value):
        """Add metadata entry."""
        if not self.analysis_metadata:
            self.analysis_metadata = {}
        self.analysis_metadata[key] = value
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_raw_data=False):
        """Convert analysis to dictionary."""
        data = super().to_dict()
        
        # Add computed fields
        data.update({
            'processing_duration': self.get_processing_duration(),
            'sentiment_summary': self.get_sentiment_summary(),
            'quality_score': self.get_quality_score(),
            'engagement_metrics': self.get_engagement_metrics(),
            'executive_summary': self.get_executive_summary(),
            'is_completed': self.is_completed(),
            'can_retry': self.can_retry()
        })
        
        # Optionally exclude large raw_data field
        if not include_raw_data:
            data.pop('raw_data', None)
        
        return data
    
    @classmethod
    def get_by_analysis_id(cls, analysis_id):
        """Get analysis by analysis_id."""
        return cls.query.filter_by(analysis_id=analysis_id).first()
    
    @classmethod
    def get_by_user(cls, user_id, platform=None, status=None, limit=50, offset=0):
        """Get analyses by user with optional filtering."""
        query = cls.query.filter_by(user_id=user_id)
        
        if platform:
            query = query.filter_by(platform=platform)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(cls.created_at.desc()).offset(offset).limit(limit).all()
    
    @classmethod
    def get_recent_by_user(cls, user_id, limit=10):
        """Get recent analyses for a user."""
        return cls.query.filter_by(user_id=user_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit).all()
    
    @classmethod
    def get_pending_analyses(cls, limit=10):
        """Get pending analyses for processing."""
        return cls.query.filter_by(status='pending')\
                       .order_by(cls.created_at.asc())\
                       .limit(limit).all()
    
    @classmethod
    def get_failed_analyses(cls, max_retries=3):
        """Get failed analyses that can be retried."""
        return cls.query.filter(cls.status == 'failed',
                               cls.retry_count < max_retries).all()
    
    @classmethod
    def count_by_user(cls, user_id, platform=None, status=None):
        """Count analyses by user with optional filtering."""
        query = cls.query.filter_by(user_id=user_id)
        
        if platform:
            query = query.filter_by(platform=platform)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.count()
    
    @classmethod
    def search_by_user(cls, user_id, search_term, limit=50, offset=0):
        """Search analyses by target identifier."""
        return cls.query.filter(
            cls.user_id == user_id,
            cls.target_identifier.contains(search_term)
        ).order_by(cls.created_at.desc()).offset(offset).limit(limit).all()
    
    def __repr__(self):
        return f'<Analysis {self.analysis_id} ({self.platform}:{self.target_identifier})>'


class AnalysisMetricsSnapshot(BaseModel):
    """Daily/weekly/monthly analysis metrics snapshots."""
    
    __tablename__ = 'analysis_metrics_snapshots'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    snapshot_date = db.Column(db.Date, nullable=False, index=True)
    snapshot_type = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly
    
    # Metrics data
    total_analyses = db.Column(db.Integer, default=0)
    completed_analyses = db.Column(db.Integer, default=0)
    failed_analyses = db.Column(db.Integer, default=0)
    
    # Platform breakdown
    amazon_analyses = db.Column(db.Integer, default=0)
    twitter_analyses = db.Column(db.Integer, default=0)
    instagram_analyses = db.Column(db.Integer, default=0)
    tiktok_analyses = db.Column(db.Integer, default=0)
    
    # Performance metrics
    average_processing_time = db.Column(db.Float, default=0.0)
    total_content_items = db.Column(db.Integer, default=0)
    average_sentiment_score = db.Column(db.Float, default=0.0)
    average_quality_score = db.Column(db.Float, default=0.0)
    
    # Additional metrics
    metrics_data = db.Column(db.JSON, default=dict)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'snapshot_date', 'snapshot_type', 
                           name='uq_user_snapshot'),
    )
    
    def calculate_success_rate(self):
        """Calculate analysis success rate."""
        if self.total_analyses == 0:
            return 0.0
        return (self.completed_analyses / self.total_analyses) * 100.0
    
    def to_dict(self):
        """Convert metrics snapshot to dictionary."""
        data = super().to_dict()
        data['success_rate'] = self.calculate_success_rate()
        return data
    
    @classmethod
    def get_user_metrics(cls, user_id, snapshot_type='daily', limit=30):
        """Get user metrics for a period."""
        return cls.query.filter_by(user_id=user_id, snapshot_type=snapshot_type)\
                       .order_by(cls.snapshot_date.desc())\
                       .limit(limit).all()
    
    def __repr__(self):
        return f'<AnalysisMetricsSnapshot {self.user_id}:{self.snapshot_date}>'
