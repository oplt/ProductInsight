"""
Analysis domain entities.
Contains the core business objects for the analysis domain.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class AnalysisStatus(Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisType(Enum):
    """Analysis type enumeration."""
    CONTENT_ANALYSIS = "content_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TREND_ANALYSIS = "trend_analysis"
    ENGAGEMENT_ANALYSIS = "engagement_analysis"
    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"


class Platform(Enum):
    """Supported platforms enumeration."""
    AMAZON = "amazon"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


@dataclass
class ContentItem:
    """Individual content item (review, post, comment, etc.)."""
    id: str
    platform: Platform
    content_type: str  # review, post, comment, reply
    text: str
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    engagement_metrics: Dict[str, int] = field(default_factory=dict)  # likes, shares, comments
    
    def __post_init__(self):
        """Validate content item after initialization."""
        if not self.text or not self.text.strip():
            raise ValueError("Content text cannot be empty")
        
        if len(self.text) > 10000:  # Reasonable limit
            raise ValueError("Content text too long (max 10000 characters)")


@dataclass
class AnalysisResult:
    """Analysis result data."""
    basic_sentiment: Dict[str, Any] = field(default_factory=dict)
    emotions: Dict[str, Any] = field(default_factory=dict)
    intents: Dict[str, Any] = field(default_factory=dict)
    aspect_sentiment: Dict[str, Any] = field(default_factory=dict)
    content_quality: Dict[str, Any] = field(default_factory=dict)
    opportunities_risks: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    engagement_metrics: Dict[str, Any] = field(default_factory=dict)
    executive_summary: str = ""
    llm_enhanced_insights: str = ""
    confidence_score: float = 0.0
    processing_time_seconds: float = 0.0
    
    def get_overall_sentiment(self) -> str:
        """Get overall sentiment from basic sentiment analysis."""
        return self.basic_sentiment.get('sentiment', 'neutral')
    
    def get_confidence_score(self) -> float:
        """Get confidence score for the analysis."""
        return self.basic_sentiment.get('confidence', 0.0)


@dataclass
class AnalysisEntity:
    """Core analysis domain entity."""
    id: Optional[int]
    analysis_id: str  # UUID for external reference
    platform: Platform
    target_identifier: str  # URL, username, product ID, etc.
    analysis_type: AnalysisType
    status: AnalysisStatus
    user_id: int
    
    # Content and results
    content_items: List[ContentItem] = field(default_factory=list)
    results: Optional[AnalysisResult] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def __post_init__(self):
        """Initialize analysis entity after creation."""
        if not self.analysis_id:
            self.analysis_id = str(uuid.uuid4())
        
        if not self.target_identifier or not self.target_identifier.strip():
            raise ValueError("Target identifier cannot be empty")
    
    def start_processing(self):
        """Mark analysis as started."""
        self.status = AnalysisStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_successfully(self, results: AnalysisResult):
        """Mark analysis as completed successfully."""
        self.status = AnalysisStatus.COMPLETED
        self.results = results
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_message = None
    
    def fail_with_error(self, error_message: str):
        """Mark analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.retry_count += 1
    
    def cancel(self):
        """Cancel the analysis."""
        self.status = AnalysisStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if analysis can be retried."""
        return self.status == AnalysisStatus.FAILED and self.retry_count < max_retries
    
    def get_processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def is_completed(self) -> bool:
        """Check if analysis is completed (successfully or failed)."""
        return self.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]
    
    def add_content_item(self, content_item: ContentItem):
        """Add a content item to the analysis."""
        if content_item.platform != self.platform:
            raise ValueError(f"Content platform {content_item.platform} doesn't match analysis platform {self.platform}")
        
        self.content_items.append(content_item)
        self.updated_at = datetime.utcnow()
    
    def get_content_count(self) -> int:
        """Get total number of content items."""
        return len(self.content_items)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for serialization."""
        return {
            'id': self.id,
            'analysis_id': self.analysis_id,
            'platform': self.platform.value,
            'target_identifier': self.target_identifier,
            'analysis_type': self.analysis_type.value,
            'status': self.status.value,
            'user_id': self.user_id,
            'content_count': self.get_content_count(),
            'results': self.results.__dict__ if self.results else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_duration': self.get_processing_duration(),
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'config': self.config
        }


@dataclass
class AnalysisMetrics:
    """Analysis metrics and statistics."""
    total_content_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    average_sentiment_score: float = 0.0
    sentiment_distribution: Dict[str, int] = field(default_factory=dict)
    top_emotions: List[Dict[str, Any]] = field(default_factory=list)
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    engagement_stats: Dict[str, Any] = field(default_factory=dict)
    processing_stats: Dict[str, float] = field(default_factory=dict)
    
    def calculate_success_rate(self) -> float:
        """Calculate processing success rate."""
        if self.total_content_items == 0:
            return 0.0
        return (self.processed_items / self.total_content_items) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_content_items': self.total_content_items,
            'processed_items': self.processed_items,
            'failed_items': self.failed_items,
            'success_rate': self.calculate_success_rate(),
            'average_sentiment_score': self.average_sentiment_score,
            'sentiment_distribution': self.sentiment_distribution,
            'top_emotions': self.top_emotions,
            'quality_metrics': self.quality_metrics,
            'engagement_stats': self.engagement_stats,
            'processing_stats': self.processing_stats
        }
