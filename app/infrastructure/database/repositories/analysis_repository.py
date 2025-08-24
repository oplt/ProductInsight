"""
SQLAlchemy implementation of AnalysisRepositoryInterface.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.analysis.repositories.analysis_repository import AnalysisRepositoryInterface
from app.core.analysis.entities.analysis import (
    AnalysisEntity, AnalysisStatus, Platform, AnalysisType, 
    AnalysisResult, ContentItem, AnalysisMetrics
)
from ..models.analysis import Analysis, AnalysisMetricsSnapshot
from ..models.base import db


logger = logging.getLogger(__name__)


class SQLAlchemyAnalysisRepository(AnalysisRepositoryInterface):
    """SQLAlchemy implementation of analysis repository."""
    
    async def create(self, analysis: AnalysisEntity) -> AnalysisEntity:
        """Create a new analysis."""
        try:
            # Convert domain entity to database model
            db_analysis = Analysis(
                analysis_id=analysis.analysis_id,
                user_id=analysis.user_id,
                platform=analysis.platform.value,
                target_identifier=analysis.target_identifier,
                analysis_type=analysis.analysis_type.value,
                status=analysis.status.value,
                config=analysis.config,
                metadata={
                    'created_from': 'domain_service',
                    'version': '2.0'
                }
            )
            
            db.session.add(db_analysis)
            db.session.commit()
            
            # Convert back to domain entity
            return self._to_domain_entity(db_analysis)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create analysis: {str(e)}")
            raise
    
    async def get_by_id(self, analysis_id: int) -> Optional[AnalysisEntity]:
        """Get analysis by database ID."""
        try:
            db_analysis = Analysis.query.get(analysis_id)
            if db_analysis:
                return self._to_domain_entity(db_analysis)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get analysis by ID {analysis_id}: {str(e)}")
            raise
    
    async def get_by_analysis_id(self, analysis_id: str) -> Optional[AnalysisEntity]:
        """Get analysis by analysis UUID."""
        try:
            db_analysis = Analysis.get_by_analysis_id(analysis_id)
            if db_analysis:
                return self._to_domain_entity(db_analysis)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get analysis by analysis_id {analysis_id}: {str(e)}")
            raise
    
    async def get_by_user(self, user_id: int, platform: Optional[Platform] = None, 
                         status: Optional[AnalysisStatus] = None, 
                         limit: int = 50, offset: int = 0) -> List[AnalysisEntity]:
        """Get analyses by user with optional filtering."""
        try:
            platform_str = platform.value if platform else None
            status_str = status.value if status else None
            
            db_analyses = Analysis.get_by_user(
                user_id=user_id,
                platform=platform_str,
                status=status_str,
                limit=limit,
                offset=offset
            )
            
            return [self._to_domain_entity(db_analysis) for db_analysis in db_analyses]
            
        except Exception as e:
            logger.error(f"Failed to get analyses for user {user_id}: {str(e)}")
            raise
    
    async def update(self, analysis: AnalysisEntity) -> AnalysisEntity:
        """Update an existing analysis."""
        try:
            db_analysis = Analysis.get_by_analysis_id(analysis.analysis_id)
            if not db_analysis:
                raise ValueError(f"Analysis not found: {analysis.analysis_id}")
            
            # Update fields from domain entity
            db_analysis.status = analysis.status.value
            db_analysis.started_at = analysis.started_at
            db_analysis.completed_at = analysis.completed_at
            db_analysis.error_message = analysis.error_message
            db_analysis.retry_count = analysis.retry_count
            db_analysis.config = analysis.config
            db_analysis.updated_at = analysis.updated_at
            
            # Update results if available
            if analysis.results:
                db_analysis.results = self._serialize_analysis_result(analysis.results)
            
            # Update content items if available
            if analysis.content_items:
                db_analysis.raw_data = [self._serialize_content_item(item) for item in analysis.content_items]
                db_analysis.content_count = len(analysis.content_items)
            
            db.session.commit()
            
            return self._to_domain_entity(db_analysis)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update analysis {analysis.analysis_id}: {str(e)}")
            raise
    
    async def delete(self, analysis_id: int) -> bool:
        """Delete an analysis by ID."""
        try:
            db_analysis = Analysis.query.get(analysis_id)
            if not db_analysis:
                return False
            
            db.session.delete(db_analysis)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete analysis {analysis_id}: {str(e)}")
            raise
    
    async def get_pending_analyses(self, limit: int = 10) -> List[AnalysisEntity]:
        """Get pending analyses for processing."""
        try:
            db_analyses = Analysis.get_pending_analyses(limit=limit)
            return [self._to_domain_entity(db_analysis) for db_analysis in db_analyses]
            
        except Exception as e:
            logger.error(f"Failed to get pending analyses: {str(e)}")
            raise
    
    async def get_user_analysis_count(self, user_id: int, platform: Optional[Platform] = None) -> int:
        """Get count of analyses for a user."""
        try:
            platform_str = platform.value if platform else None
            return Analysis.count_by_user(user_id=user_id, platform=platform_str)
            
        except Exception as e:
            logger.error(f"Failed to get analysis count for user {user_id}: {str(e)}")
            raise
    
    async def get_recent_analyses(self, user_id: int, limit: int = 10) -> List[AnalysisEntity]:
        """Get recent analyses for a user."""
        try:
            db_analyses = Analysis.get_recent_by_user(user_id=user_id, limit=limit)
            return [self._to_domain_entity(db_analysis) for db_analysis in db_analyses]
            
        except Exception as e:
            logger.error(f"Failed to get recent analyses for user {user_id}: {str(e)}")
            raise
    
    async def get_analysis_metrics(self, user_id: int, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> AnalysisMetrics:
        """Get analysis metrics for a user within a date range."""
        try:
            # Set default date range (last 30 days)
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Query analyses within date range
            query = Analysis.query.filter(
                Analysis.user_id == user_id,
                Analysis.created_at >= start_date,
                Analysis.created_at <= end_date
            )
            
            analyses = query.all()
            
            # Calculate metrics
            metrics = AnalysisMetrics()
            metrics.total_content_items = sum(a.content_count for a in analyses)
            metrics.processed_items = len([a for a in analyses if a.status == 'completed'])
            metrics.failed_items = len([a for a in analyses if a.status == 'failed'])
            
            # Sentiment distribution
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            sentiment_scores = []
            
            for analysis in analyses:
                if analysis.results and 'basic_sentiment' in analysis.results:
                    sentiment_data = analysis.results['basic_sentiment']
                    sentiment = sentiment_data.get('sentiment', 'neutral')
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                    
                    score = sentiment_data.get('score', 0.0)
                    if score:
                        sentiment_scores.append(score)
            
            metrics.sentiment_distribution = sentiment_counts
            metrics.average_sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            
            # Processing stats
            processing_times = [a.processing_time_seconds for a in analyses if a.processing_time_seconds]
            metrics.processing_stats = {
                'average_time': sum(processing_times) / len(processing_times) if processing_times else 0.0,
                'total_time': sum(processing_times),
                'fastest': min(processing_times) if processing_times else 0.0,
                'slowest': max(processing_times) if processing_times else 0.0
            }
            
            # Platform distribution
            platform_counts = {}
            for analysis in analyses:
                platform = analysis.platform
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            metrics.engagement_stats = {
                'platform_distribution': platform_counts,
                'total_analyses': len(analyses)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get analysis metrics for user {user_id}: {str(e)}")
            raise
    
    async def get_platform_analyses(self, user_id: int, platform: Platform, 
                                   limit: int = 50, offset: int = 0) -> List[AnalysisEntity]:
        """Get analyses for a specific platform."""
        return await self.get_by_user(user_id=user_id, platform=platform, limit=limit, offset=offset)
    
    async def search_analyses(self, user_id: int, query: str, 
                             limit: int = 50, offset: int = 0) -> List[AnalysisEntity]:
        """Search analyses by target identifier or content."""
        try:
            db_analyses = Analysis.search_by_user(
                user_id=user_id,
                search_term=query,
                limit=limit,
                offset=offset
            )
            
            return [self._to_domain_entity(db_analysis) for db_analysis in db_analyses]
            
        except Exception as e:
            logger.error(f"Failed to search analyses for user {user_id}: {str(e)}")
            raise
    
    async def get_failed_analyses(self, max_retries: int = 3) -> List[AnalysisEntity]:
        """Get failed analyses that can be retried."""
        try:
            db_analyses = Analysis.get_failed_analyses(max_retries=max_retries)
            return [self._to_domain_entity(db_analysis) for db_analysis in db_analyses]
            
        except Exception as e:
            logger.error(f"Failed to get failed analyses: {str(e)}")
            raise
    
    # Private helper methods
    
    def _to_domain_entity(self, db_analysis: Analysis) -> AnalysisEntity:
        """Convert database model to domain entity."""
        # Deserialize content items
        content_items = []
        if db_analysis.raw_data:
            for item_data in db_analysis.raw_data:
                content_item = self._deserialize_content_item(item_data)
                if content_item:
                    content_items.append(content_item)
        
        # Deserialize results
        results = None
        if db_analysis.results:
            results = self._deserialize_analysis_result(db_analysis.results)
        
        return AnalysisEntity(
            id=db_analysis.id,
            analysis_id=db_analysis.analysis_id,
            platform=Platform(db_analysis.platform),
            target_identifier=db_analysis.target_identifier,
            analysis_type=AnalysisType(db_analysis.analysis_type),
            status=AnalysisStatus(db_analysis.status),
            user_id=db_analysis.user_id,
            content_items=content_items,
            results=results,
            created_at=db_analysis.created_at,
            updated_at=db_analysis.updated_at,
            started_at=db_analysis.started_at,
            completed_at=db_analysis.completed_at,
            config=db_analysis.config or {},
            error_message=db_analysis.error_message,
            retry_count=db_analysis.retry_count
        )
    
    def _serialize_content_item(self, content_item: ContentItem) -> Dict[str, Any]:
        """Serialize content item for database storage."""
        return {
            'id': content_item.id,
            'platform': content_item.platform.value,
            'content_type': content_item.content_type,
            'text': content_item.text,
            'author': content_item.author,
            'timestamp': content_item.timestamp.isoformat() if content_item.timestamp else None,
            'metadata': content_item.metadata,
            'engagement_metrics': content_item.engagement_metrics
        }
    
    def _deserialize_content_item(self, data: Dict[str, Any]) -> Optional[ContentItem]:
        """Deserialize content item from database storage."""
        try:
            timestamp = None
            if data.get('timestamp'):
                timestamp = datetime.fromisoformat(data['timestamp'])
            
            return ContentItem(
                id=data['id'],
                platform=Platform(data['platform']),
                content_type=data['content_type'],
                text=data['text'],
                author=data.get('author'),
                timestamp=timestamp,
                metadata=data.get('metadata', {}),
                engagement_metrics=data.get('engagement_metrics', {})
            )
        except Exception as e:
            logger.warning(f"Failed to deserialize content item: {str(e)}")
            return None
    
    def _serialize_analysis_result(self, result: AnalysisResult) -> Dict[str, Any]:
        """Serialize analysis result for database storage."""
        return {
            'basic_sentiment': result.basic_sentiment,
            'emotions': result.emotions,
            'intents': result.intents,
            'aspect_sentiment': result.aspect_sentiment,
            'content_quality': result.content_quality,
            'opportunities_risks': result.opportunities_risks,
            'recommendations': result.recommendations,
            'engagement_metrics': result.engagement_metrics,
            'executive_summary': result.executive_summary,
            'llm_enhanced_insights': result.llm_enhanced_insights,
            'confidence_score': result.confidence_score,
            'processing_time_seconds': result.processing_time_seconds
        }
    
    def _deserialize_analysis_result(self, data: Dict[str, Any]) -> AnalysisResult:
        """Deserialize analysis result from database storage."""
        return AnalysisResult(
            basic_sentiment=data.get('basic_sentiment', {}),
            emotions=data.get('emotions', {}),
            intents=data.get('intents', {}),
            aspect_sentiment=data.get('aspect_sentiment', {}),
            content_quality=data.get('content_quality', {}),
            opportunities_risks=data.get('opportunities_risks', {}),
            recommendations=data.get('recommendations', []),
            engagement_metrics=data.get('engagement_metrics', {}),
            executive_summary=data.get('executive_summary', ''),
            llm_enhanced_insights=data.get('llm_enhanced_insights', ''),
            confidence_score=data.get('confidence_score', 0.0),
            processing_time_seconds=data.get('processing_time_seconds', 0.0)
        )
