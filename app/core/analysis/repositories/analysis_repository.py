"""
Analysis repository interface.
Defines the contract for data access operations for the analysis domain.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.analysis import AnalysisEntity, AnalysisStatus, Platform, AnalysisType, AnalysisMetrics


class AnalysisRepositoryInterface(ABC):
    """Interface for analysis data access operations."""
    
    @abstractmethod
    async def create(self, analysis: AnalysisEntity) -> AnalysisEntity:
        """Create a new analysis."""
        pass
    
    @abstractmethod
    async def get_by_id(self, analysis_id: int) -> Optional[AnalysisEntity]:
        """Get analysis by database ID."""
        pass
    
    @abstractmethod
    async def get_by_analysis_id(self, analysis_id: str) -> Optional[AnalysisEntity]:
        """Get analysis by analysis UUID."""
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: int, platform: Optional[Platform] = None, 
                         status: Optional[AnalysisStatus] = None, 
                         limit: int = 50, offset: int = 0) -> List[AnalysisEntity]:
        """Get analyses by user with optional filtering."""
        pass
    
    @abstractmethod
    async def update(self, analysis: AnalysisEntity) -> AnalysisEntity:
        """Update an existing analysis."""
        pass
    
    @abstractmethod
    async def delete(self, analysis_id: int) -> bool:
        """Delete an analysis by ID."""
        pass
    
    @abstractmethod
    async def get_pending_analyses(self, limit: int = 10) -> List[AnalysisEntity]:
        """Get pending analyses for processing."""
        pass
    
    @abstractmethod
    async def get_user_analysis_count(self, user_id: int, platform: Optional[Platform] = None) -> int:
        """Get count of analyses for a user."""
        pass
    
    @abstractmethod
    async def get_recent_analyses(self, user_id: int, limit: int = 10) -> List[AnalysisEntity]:
        """Get recent analyses for a user."""
        pass
    
    @abstractmethod
    async def get_analysis_metrics(self, user_id: int, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> AnalysisMetrics:
        """Get analysis metrics for a user within a date range."""
        pass
    
    @abstractmethod
    async def get_platform_analyses(self, user_id: int, platform: Platform, 
                                   limit: int = 50, offset: int = 0) -> List[AnalysisEntity]:
        """Get analyses for a specific platform."""
        pass
    
    @abstractmethod
    async def search_analyses(self, user_id: int, query: str, 
                             limit: int = 50, offset: int = 0) -> List[AnalysisEntity]:
        """Search analyses by target identifier or content."""
        pass
    
    @abstractmethod
    async def get_failed_analyses(self, max_retries: int = 3) -> List[AnalysisEntity]:
        """Get failed analyses that can be retried."""
        pass


class AnalysisQueryFilters:
    """Query filters for analysis repository operations."""
    
    def __init__(self):
        self.user_id: Optional[int] = None
        self.platform: Optional[Platform] = None
        self.status: Optional[AnalysisStatus] = None
        self.analysis_type: Optional[AnalysisType] = None
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.search_query: Optional[str] = None
        self.limit: int = 50
        self.offset: int = 0
        self.order_by: str = 'created_at'
        self.order_direction: str = 'desc'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert filters to dictionary."""
        return {
            'user_id': self.user_id,
            'platform': self.platform.value if self.platform else None,
            'status': self.status.value if self.status else None,
            'analysis_type': self.analysis_type.value if self.analysis_type else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'search_query': self.search_query,
            'limit': self.limit,
            'offset': self.offset,
            'order_by': self.order_by,
            'order_direction': self.order_direction
        }
