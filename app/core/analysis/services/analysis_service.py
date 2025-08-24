"""
Analysis domain service.
Contains the core business logic for analysis operations.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.analysis import (
    AnalysisEntity, AnalysisResult, AnalysisStatus, AnalysisType, 
    Platform, ContentItem, AnalysisMetrics
)
from ..repositories.analysis_repository import AnalysisRepositoryInterface


logger = logging.getLogger(__name__)


class AnalysisDomainService:
    """Core analysis domain service containing business logic."""
    
    def __init__(self, analysis_repository: AnalysisRepositoryInterface):
        """Initialize with repository dependency."""
        self.analysis_repository = analysis_repository
        self._max_retries = 3
        self._max_content_items = 10000  # Reasonable limit
    
    async def create_analysis(self, 
                            platform: Platform,
                            target_identifier: str,
                            analysis_type: AnalysisType,
                            user_id: int,
                            config: Optional[Dict[str, Any]] = None) -> AnalysisEntity:
        """Create a new analysis with business validation."""
        
        logger.info(f"Creating analysis for user {user_id}: {platform.value}/{target_identifier}")
        
        # Business validation
        await self._validate_analysis_creation(user_id, platform, target_identifier)
        
        # Create analysis entity
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",  # Will be generated in __post_init__
            platform=platform,
            target_identifier=target_identifier,
            analysis_type=analysis_type,
            status=AnalysisStatus.PENDING,
            user_id=user_id,
            config=config or {}
        )
        
        # Save to repository
        created_analysis = await self.analysis_repository.create(analysis)
        
        logger.info(f"Analysis created with ID: {created_analysis.analysis_id}")
        return created_analysis
    
    async def start_analysis_processing(self, analysis_id: str) -> AnalysisEntity:
        """Start processing an analysis."""
        
        analysis = await self.analysis_repository.get_by_analysis_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        if analysis.status != AnalysisStatus.PENDING:
            raise ValueError(f"Analysis {analysis_id} is not in pending status")
        
        # Update status to in progress
        analysis.start_processing()
        
        # Save updated analysis
        updated_analysis = await self.analysis_repository.update(analysis)
        
        logger.info(f"Analysis {analysis_id} started processing")
        return updated_analysis
    
    async def complete_analysis(self, analysis_id: str, results: AnalysisResult) -> AnalysisEntity:
        """Complete an analysis with results."""
        
        analysis = await self.analysis_repository.get_by_analysis_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        if analysis.status != AnalysisStatus.IN_PROGRESS:
            raise ValueError(f"Analysis {analysis_id} is not in progress")
        
        # Validate results
        self._validate_analysis_results(results)
        
        # Update analysis with results
        analysis.complete_successfully(results)
        
        # Save updated analysis
        updated_analysis = await self.analysis_repository.update(analysis)
        
        logger.info(f"Analysis {analysis_id} completed successfully")
        return updated_analysis
    
    async def fail_analysis(self, analysis_id: str, error_message: str) -> AnalysisEntity:
        """Mark analysis as failed."""
        
        analysis = await self.analysis_repository.get_by_analysis_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        # Update analysis with error
        analysis.fail_with_error(error_message)
        
        # Save updated analysis
        updated_analysis = await self.analysis_repository.update(analysis)
        
        logger.error(f"Analysis {analysis_id} failed: {error_message}")
        return updated_analysis
    
    async def retry_failed_analysis(self, analysis_id: str) -> AnalysisEntity:
        """Retry a failed analysis."""
        
        analysis = await self.analysis_repository.get_by_analysis_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        if not analysis.can_retry(self._max_retries):
            raise ValueError(f"Analysis {analysis_id} cannot be retried")
        
        # Reset status to pending
        analysis.status = AnalysisStatus.PENDING
        analysis.error_message = None
        analysis.started_at = None
        analysis.completed_at = None
        analysis.updated_at = datetime.utcnow()
        
        # Save updated analysis
        updated_analysis = await self.analysis_repository.update(analysis)
        
        logger.info(f"Analysis {analysis_id} scheduled for retry (attempt {analysis.retry_count + 1})")
        return updated_analysis
    
    async def cancel_analysis(self, analysis_id: str, user_id: int) -> AnalysisEntity:
        """Cancel an analysis (only by owner)."""
        
        analysis = await self.analysis_repository.get_by_analysis_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        if analysis.user_id != user_id:
            raise ValueError(f"User {user_id} is not authorized to cancel analysis {analysis_id}")
        
        if analysis.is_completed():
            raise ValueError(f"Analysis {analysis_id} is already completed")
        
        # Cancel analysis
        analysis.cancel()
        
        # Save updated analysis
        updated_analysis = await self.analysis_repository.update(analysis)
        
        logger.info(f"Analysis {analysis_id} cancelled by user {user_id}")
        return updated_analysis
    
    async def add_content_to_analysis(self, analysis_id: str, content_items: List[ContentItem]) -> AnalysisEntity:
        """Add content items to an analysis."""
        
        analysis = await self.analysis_repository.get_by_analysis_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        if analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot add content to analysis {analysis_id} in status {analysis.status}")
        
        # Validate content limit
        total_content = len(analysis.content_items) + len(content_items)
        if total_content > self._max_content_items:
            raise ValueError(f"Content limit exceeded: {total_content} > {self._max_content_items}")
        
        # Add content items
        for content_item in content_items:
            analysis.add_content_item(content_item)
        
        # Save updated analysis
        updated_analysis = await self.analysis_repository.update(analysis)
        
        logger.info(f"Added {len(content_items)} content items to analysis {analysis_id}")
        return updated_analysis
    
    async def get_user_analyses(self, user_id: int, 
                               platform: Optional[Platform] = None,
                               status: Optional[AnalysisStatus] = None,
                               limit: int = 50, 
                               offset: int = 0) -> List[AnalysisEntity]:
        """Get analyses for a user with filtering."""
        
        return await self.analysis_repository.get_by_user(
            user_id=user_id,
            platform=platform,
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def get_user_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get dashboard data for a user."""
        
        # Get recent analyses
        recent_analyses = await self.analysis_repository.get_recent_analyses(user_id, limit=10)
        
        # Get analysis metrics
        metrics = await self.analysis_repository.get_analysis_metrics(user_id)
        
        # Get counts by platform
        platform_counts = {}
        for platform in Platform:
            count = await self.analysis_repository.get_user_analysis_count(user_id, platform)
            platform_counts[platform.value] = count
        
        # Get pending analyses count
        pending_analyses = await self.analysis_repository.get_by_user(
            user_id=user_id, 
            status=AnalysisStatus.PENDING, 
            limit=100
        )
        
        return {
            'total_analyses': sum(platform_counts.values()),
            'platform_counts': platform_counts,
            'pending_count': len(pending_analyses),
            'recent_analyses': [analysis.to_dict() for analysis in recent_analyses],
            'metrics': metrics.to_dict(),
            'success_rate': metrics.calculate_success_rate()
        }
    
    async def get_analysis_by_id(self, analysis_id: str, user_id: int) -> Optional[AnalysisEntity]:
        """Get analysis by ID with user authorization."""
        
        analysis = await self.analysis_repository.get_by_analysis_id(analysis_id)
        
        if not analysis:
            return None
        
        if analysis.user_id != user_id:
            raise ValueError(f"User {user_id} is not authorized to access analysis {analysis_id}")
        
        return analysis
    
    async def delete_analysis(self, analysis_id: str, user_id: int) -> bool:
        """Delete an analysis (only by owner)."""
        
        analysis = await self.analysis_repository.get_by_analysis_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        if analysis.user_id != user_id:
            raise ValueError(f"User {user_id} is not authorized to delete analysis {analysis_id}")
        
        # Delete from repository
        success = await self.analysis_repository.delete(analysis.id)
        
        if success:
            logger.info(f"Analysis {analysis_id} deleted by user {user_id}")
        else:
            logger.error(f"Failed to delete analysis {analysis_id}")
        
        return success
    
    # Private helper methods
    
    async def _validate_analysis_creation(self, user_id: int, platform: Platform, target_identifier: str):
        """Validate analysis creation business rules."""
        
        # Check if user has too many pending analyses
        pending_analyses = await self.analysis_repository.get_by_user(
            user_id=user_id,
            status=AnalysisStatus.PENDING,
            limit=100
        )
        
        if len(pending_analyses) >= 10:  # Business rule: max 10 pending analyses
            raise ValueError("Too many pending analyses. Please wait for some to complete.")
        
        # Check for duplicate analysis (same platform + target + user)
        existing_analyses = await self.analysis_repository.get_by_user(
            user_id=user_id,
            platform=platform,
            limit=100
        )
        
        for existing in existing_analyses:
            if (existing.target_identifier == target_identifier and 
                existing.status in [AnalysisStatus.PENDING, AnalysisStatus.IN_PROGRESS]):
                raise ValueError(f"Analysis for {target_identifier} on {platform.value} is already in progress")
    
    def _validate_analysis_results(self, results: AnalysisResult):
        """Validate analysis results."""
        
        if not results:
            raise ValueError("Analysis results cannot be empty")
        
        # Validate confidence score
        if not (0.0 <= results.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        # Validate executive summary
        if not results.executive_summary or not results.executive_summary.strip():
            raise ValueError("Executive summary is required")
        
        if len(results.executive_summary) > 5000:
            raise ValueError("Executive summary is too long (max 5000 characters)")
