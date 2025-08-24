"""
Unit tests for analysis domain entities.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from app.core.analysis.entities.analysis import (
    AnalysisEntity, AnalysisResult, AnalysisStatus, AnalysisType,
    Platform, ContentItem, AnalysisMetrics
)


class TestAnalysisEntity:
    """Test AnalysisEntity domain object."""
    
    def test_create_analysis_entity(self):
        """Test creating analysis entity."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        assert analysis.platform == Platform.TWITTER
        assert analysis.target_identifier == "@test_user"
        assert analysis.status == AnalysisStatus.PENDING
        assert analysis.user_id == 1
        assert analysis.analysis_id  # Should be generated automatically
        assert isinstance(analysis.created_at, datetime)
        assert isinstance(analysis.updated_at, datetime)
    
    def test_analysis_id_generation(self):
        """Test automatic analysis ID generation."""
        analysis1 = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test1",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        analysis2 = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test2",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        assert analysis1.analysis_id != analysis2.analysis_id
        assert len(analysis1.analysis_id) == 36  # UUID format
        assert len(analysis2.analysis_id) == 36
    
    def test_invalid_target_identifier(self):
        """Test validation of target identifier."""
        with pytest.raises(ValueError, match="Target identifier cannot be empty"):
            AnalysisEntity(
                id=None,
                analysis_id="",
                platform=Platform.TWITTER,
                target_identifier="",
                analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
                status=AnalysisStatus.PENDING,
                user_id=1
            )
    
    def test_start_processing(self):
        """Test starting analysis processing."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        start_time = datetime.utcnow()
        analysis.start_processing()
        
        assert analysis.status == AnalysisStatus.IN_PROGRESS
        assert analysis.started_at >= start_time
        assert analysis.updated_at >= start_time
    
    def test_complete_successfully(self):
        """Test completing analysis successfully."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.IN_PROGRESS,
            user_id=1
        )
        analysis.start_processing()
        
        results = AnalysisResult(
            executive_summary="Test analysis completed",
            confidence_score=0.85
        )
        
        completion_time = datetime.utcnow()
        analysis.complete_successfully(results)
        
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.results == results
        assert analysis.completed_at >= completion_time
        assert analysis.error_message is None
    
    def test_fail_with_error(self):
        """Test failing analysis with error."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.IN_PROGRESS,
            user_id=1
        )
        
        error_message = "Analysis failed due to API error"
        analysis.fail_with_error(error_message)
        
        assert analysis.status == AnalysisStatus.FAILED
        assert analysis.error_message == error_message
        assert analysis.retry_count == 1
        assert analysis.completed_at is not None
    
    def test_cancel_analysis(self):
        """Test cancelling analysis."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        analysis.cancel()
        
        assert analysis.status == AnalysisStatus.CANCELLED
        assert analysis.completed_at is not None
    
    def test_can_retry(self):
        """Test retry logic."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.FAILED,
            user_id=1,
            retry_count=1
        )
        
        # Should be able to retry
        assert analysis.can_retry(max_retries=3)
        
        # Exceed max retries
        analysis.retry_count = 3
        assert not analysis.can_retry(max_retries=3)
        
        # Different status
        analysis.status = AnalysisStatus.COMPLETED
        assert not analysis.can_retry(max_retries=3)
    
    def test_add_content_item(self):
        """Test adding content items."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        content_item = ContentItem(
            id="tweet_1",
            platform=Platform.TWITTER,
            content_type="tweet",
            text="This is a test tweet",
            author="test_user"
        )
        
        analysis.add_content_item(content_item)
        
        assert len(analysis.content_items) == 1
        assert analysis.content_items[0] == content_item
        assert analysis.get_content_count() == 1
    
    def test_add_content_item_wrong_platform(self):
        """Test adding content item with wrong platform."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        content_item = ContentItem(
            id="review_1",
            platform=Platform.AMAZON,  # Wrong platform
            content_type="review",
            text="This is a test review",
            author="reviewer"
        )
        
        with pytest.raises(ValueError, match="Content platform .* doesn't match analysis platform"):
            analysis.add_content_item(content_item)
    
    def test_processing_duration(self):
        """Test processing duration calculation."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        # No duration when not started
        assert analysis.get_processing_duration() is None
        
        # Start processing
        analysis.start_processing()
        
        # Still no duration when not completed
        assert analysis.get_processing_duration() is None
        
        # Complete analysis
        results = AnalysisResult(executive_summary="Test completed")
        analysis.complete_successfully(results)
        
        # Should have duration now
        duration = analysis.get_processing_duration()
        assert duration is not None
        assert duration >= 0
    
    def test_is_completed(self):
        """Test completion status check."""
        analysis = AnalysisEntity(
            id=None,
            analysis_id="",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            user_id=1
        )
        
        # Not completed when pending
        assert not analysis.is_completed()
        
        # Not completed when in progress
        analysis.status = AnalysisStatus.IN_PROGRESS
        assert not analysis.is_completed()
        
        # Completed when successful
        analysis.status = AnalysisStatus.COMPLETED
        assert analysis.is_completed()
        
        # Completed when failed
        analysis.status = AnalysisStatus.FAILED
        assert analysis.is_completed()
        
        # Completed when cancelled
        analysis.status = AnalysisStatus.CANCELLED
        assert analysis.is_completed()
    
    def test_to_dict(self):
        """Test entity serialization to dictionary."""
        analysis = AnalysisEntity(
            id=1,
            analysis_id="test-123",
            platform=Platform.TWITTER,
            target_identifier="@test_user",
            analysis_type=AnalysisType.COMPREHENSIVE_ANALYSIS,
            status=AnalysisStatus.COMPLETED,
            user_id=1
        )
        
        data = analysis.to_dict()
        
        assert data['id'] == 1
        assert data['analysis_id'] == "test-123"
        assert data['platform'] == "twitter"
        assert data['target_identifier'] == "@test_user"
        assert data['analysis_type'] == "comprehensive_analysis"
        assert data['status'] == "completed"
        assert data['user_id'] == 1
        assert 'created_at' in data
        assert 'updated_at' in data


class TestContentItem:
    """Test ContentItem domain object."""
    
    def test_create_content_item(self):
        """Test creating content item."""
        item = ContentItem(
            id="tweet_1",
            platform=Platform.TWITTER,
            content_type="tweet",
            text="This is a test tweet",
            author="test_user",
            timestamp=datetime.utcnow()
        )
        
        assert item.id == "tweet_1"
        assert item.platform == Platform.TWITTER
        assert item.content_type == "tweet"
        assert item.text == "This is a test tweet"
        assert item.author == "test_user"
    
    def test_empty_content_validation(self):
        """Test validation of empty content."""
        with pytest.raises(ValueError, match="Content text cannot be empty"):
            ContentItem(
                id="tweet_1",
                platform=Platform.TWITTER,
                content_type="tweet",
                text="",
                author="test_user"
            )
        
        with pytest.raises(ValueError, match="Content text cannot be empty"):
            ContentItem(
                id="tweet_2",
                platform=Platform.TWITTER,
                content_type="tweet",
                text="   ",  # Only whitespace
                author="test_user"
            )
    
    def test_content_length_validation(self):
        """Test validation of content length."""
        long_text = "a" * 10001  # Exceeds limit
        
        with pytest.raises(ValueError, match="Content text too long"):
            ContentItem(
                id="tweet_1",
                platform=Platform.TWITTER,
                content_type="tweet",
                text=long_text,
                author="test_user"
            )


class TestAnalysisResult:
    """Test AnalysisResult domain object."""
    
    def test_create_analysis_result(self):
        """Test creating analysis result."""
        result = AnalysisResult(
            basic_sentiment={'sentiment': 'positive', 'confidence': 0.85},
            executive_summary="Analysis completed successfully",
            confidence_score=0.85
        )
        
        assert result.basic_sentiment['sentiment'] == 'positive'
        assert result.executive_summary == "Analysis completed successfully"
        assert result.confidence_score == 0.85
    
    def test_get_overall_sentiment(self):
        """Test getting overall sentiment."""
        result = AnalysisResult(
            basic_sentiment={'sentiment': 'positive', 'confidence': 0.85}
        )
        
        assert result.get_overall_sentiment() == 'positive'
        
        # Test with empty sentiment
        result_empty = AnalysisResult()
        assert result_empty.get_overall_sentiment() == 'neutral'
    
    def test_get_confidence_score(self):
        """Test getting confidence score."""
        result = AnalysisResult(
            basic_sentiment={'sentiment': 'positive', 'confidence': 0.85}
        )
        
        assert result.get_confidence_score() == 0.85
        
        # Test with no confidence
        result_no_conf = AnalysisResult()
        assert result_no_conf.get_confidence_score() == 0.0


class TestAnalysisMetrics:
    """Test AnalysisMetrics domain object."""
    
    def test_create_analysis_metrics(self):
        """Test creating analysis metrics."""
        metrics = AnalysisMetrics(
            total_content_items=100,
            processed_items=95,
            failed_items=5
        )
        
        assert metrics.total_content_items == 100
        assert metrics.processed_items == 95
        assert metrics.failed_items == 5
    
    def test_calculate_success_rate(self):
        """Test success rate calculation."""
        metrics = AnalysisMetrics(
            total_content_items=100,
            processed_items=85,
            failed_items=15
        )
        
        success_rate = metrics.calculate_success_rate()
        assert success_rate == 85.0
        
        # Test with zero items
        metrics_zero = AnalysisMetrics()
        assert metrics_zero.calculate_success_rate() == 0.0
    
    def test_to_dict(self):
        """Test metrics serialization."""
        metrics = AnalysisMetrics(
            total_content_items=100,
            processed_items=85,
            failed_items=15,
            average_sentiment_score=0.6
        )
        
        data = metrics.to_dict()
        
        assert data['total_content_items'] == 100
        assert data['processed_items'] == 85
        assert data['failed_items'] == 15
        assert data['success_rate'] == 85.0
        assert data['average_sentiment_score'] == 0.6
