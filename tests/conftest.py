"""
Pytest configuration and fixtures.
"""

import pytest
import tempfile
import os
from datetime import datetime

from app.infrastructure.database.models.base import db
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.analysis import Analysis
from config.base import get_config


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    from app.main import create_app
    
    # Use testing configuration
    config = get_config('testing')
    test_app = create_app(config)
    
    with test_app.app_context():
        # Create all database tables
        db.create_all()
        yield test_app
        
        # Clean up
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        # Begin a transaction
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Configure session to use the transaction
        session = db.create_scoped_session(
            options={"bind": connection, "binds": {}}
        )
        db.session = session
        
        yield session
        
        # Rollback transaction and close connection
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        first_name='Test',
        last_name='User',
        role='user',
        status='active'
    )
    user.set_password('testpassword')
    user.verify_email()
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin test user."""
    user = User(
        username='adminuser',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        role='admin',
        status='active'
    )
    user.set_password('adminpassword')
    user.verify_email()
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def premium_user(db_session):
    """Create a premium test user."""
    user = User(
        username='premiumuser',
        email='premium@example.com',
        first_name='Premium',
        last_name='User',
        role='premium',
        status='active',
        analysis_quota=500
    )
    user.set_password('premiumpassword')
    user.verify_email()
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def authenticated_client(client, test_user):
    """Create authenticated client."""
    # Login the test user
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    
    return client


@pytest.fixture
def sample_analysis(db_session, test_user):
    """Create a sample analysis."""
    analysis = Analysis(
        analysis_id='test-analysis-123',
        user_id=test_user.id,
        platform='twitter',
        target_identifier='@test_user',
        analysis_type='comprehensive_analysis',
        status='completed',
        content_count=100,
        results={
            'basic_sentiment': {
                'sentiment': 'positive',
                'confidence': 0.85,
                'score': 0.7
            },
            'executive_summary': 'Test analysis completed successfully'
        }
    )
    
    db_session.add(analysis)
    db_session.commit()
    
    return analysis


@pytest.fixture
def multiple_analyses(db_session, test_user):
    """Create multiple test analyses."""
    analyses = []
    
    platforms = ['twitter', 'instagram', 'amazon', 'tiktok']
    statuses = ['completed', 'pending', 'failed']
    
    for i in range(10):
        analysis = Analysis(
            analysis_id=f'test-analysis-{i}',
            user_id=test_user.id,
            platform=platforms[i % len(platforms)],
            target_identifier=f'@test_target_{i}',
            analysis_type='comprehensive_analysis',
            status=statuses[i % len(statuses)],
            content_count=50 + i * 10,
            created_at=datetime.utcnow()
        )
        
        if analysis.status == 'completed':
            analysis.results = {
                'basic_sentiment': {
                    'sentiment': 'positive' if i % 2 == 0 else 'negative',
                    'confidence': 0.8,
                    'score': 0.6 if i % 2 == 0 else -0.4
                },
                'executive_summary': f'Test analysis {i} completed'
            }
        
        analyses.append(analysis)
        db_session.add(analysis)
    
    db_session.commit()
    return analyses


@pytest.fixture
def api_headers():
    """Create API headers for testing."""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


@pytest.fixture
def auth_headers(test_user):
    """Create authenticated API headers."""
    from app.api.middleware.auth import generate_jwt_token
    
    token = generate_jwt_token(test_user.id)
    
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    from unittest.mock import Mock
    
    mock_service = Mock()
    mock_service.analyze_content_comprehensive.return_value = {
        'basic_sentiment': {
            'sentiment': 'positive',
            'confidence': 0.85,
            'score': 0.7
        },
        'emotions': {
            'joy': 0.6,
            'anger': 0.1,
            'sadness': 0.1
        },
        'executive_summary': 'Mock analysis completed successfully',
        'confidence_score': 0.85
    }
    
    return mock_service


@pytest.fixture
def mock_platform_service():
    """Mock platform service for testing."""
    from unittest.mock import Mock
    
    mock_service = Mock()
    mock_service.scrape_content.return_value = [
        {
            'id': 'content_1',
            'text': 'This is a positive review',
            'author': 'user1',
            'timestamp': datetime.utcnow().isoformat(),
            'engagement_metrics': {'likes': 10, 'shares': 2}
        },
        {
            'id': 'content_2',
            'text': 'This is a negative review',
            'author': 'user2',
            'timestamp': datetime.utcnow().isoformat(),
            'engagement_metrics': {'likes': 3, 'shares': 0}
        }
    ]
    
    return mock_service


@pytest.fixture
def sample_content_items():
    """Sample content items for testing."""
    from app.core.analysis.entities.analysis import ContentItem, Platform
    
    return [
        ContentItem(
            id='item_1',
            platform=Platform.TWITTER,
            content_type='tweet',
            text='Great product! Highly recommend it.',
            author='user1',
            timestamp=datetime.utcnow(),
            engagement_metrics={'likes': 15, 'retweets': 3}
        ),
        ContentItem(
            id='item_2',
            platform=Platform.TWITTER,
            content_type='tweet',
            text='Not impressed with the quality.',
            author='user2',
            timestamp=datetime.utcnow(),
            engagement_metrics={'likes': 2, 'retweets': 0}
        ),
        ContentItem(
            id='item_3',
            platform=Platform.TWITTER,
            content_type='tweet',
            text='Average product, nothing special.',
            author='user3',
            timestamp=datetime.utcnow(),
            engagement_metrics={'likes': 5, 'retweets': 1}
        )
    ]


@pytest.fixture
def temp_file():
    """Create temporary file for testing."""
    fd, path = tempfile.mkstemp()
    yield path
    os.unlink(path)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    from unittest.mock import Mock
    
    redis_mock = Mock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.pipeline.return_value = redis_mock
    redis_mock.execute.return_value = [0, 0, True, True]
    
    return redis_mock


# Utility functions for tests

def login_user(client, email='test@example.com', password='testpassword'):
    """Helper function to login a user in tests."""
    return client.post('/login', data={
        'email': email,
        'password': password,
        'submit': 'Sign In'
    }, follow_redirects=True)


def logout_user(client):
    """Helper function to logout a user in tests."""
    return client.get('/logout', follow_redirects=True)


def create_test_analysis_data():
    """Create test data for analysis creation."""
    return {
        'platform': 'twitter',
        'target_identifier': '@test_user',
        'analysis_type': 'comprehensive_analysis',
        'config': {
            'max_items': 100,
            'include_replies': False
        }
    }


def assert_response_success(response, expected_status=200):
    """Assert that response is successful."""
    assert response.status_code == expected_status
    if response.is_json:
        data = response.get_json()
        assert data.get('status') == 'success'
    return response


def assert_response_error(response, expected_status=400, expected_message=None):
    """Assert that response is an error."""
    assert response.status_code == expected_status
    if response.is_json:
        data = response.get_json()
        assert data.get('status') == 'error'
        if expected_message:
            assert expected_message in data.get('message', '')
    return response


# Test data constants

SAMPLE_PLATFORMS = ['twitter', 'instagram', 'amazon', 'tiktok']
SAMPLE_ANALYSIS_TYPES = ['comprehensive_analysis', 'sentiment_analysis', 'engagement_analysis']
SAMPLE_STATUSES = ['pending', 'in_progress', 'completed', 'failed', 'cancelled']

SAMPLE_SENTIMENT_DATA = {
    'sentiment': 'positive',
    'confidence': 0.85,
    'score': 0.7,
    'distribution': {
        'positive': 0.7,
        'negative': 0.15,
        'neutral': 0.15
    }
}

SAMPLE_ANALYSIS_RESULTS = {
    'basic_sentiment': SAMPLE_SENTIMENT_DATA,
    'emotions': {
        'joy': 0.6,
        'anger': 0.1,
        'sadness': 0.1,
        'fear': 0.05,
        'surprise': 0.1,
        'disgust': 0.05
    },
    'content_quality': {
        'quality_score': 0.8,
        'readability_score': 0.75,
        'engagement_score': 0.85
    },
    'executive_summary': 'Test analysis completed with positive sentiment',
    'confidence_score': 0.85,
    'processing_time_seconds': 12.5
}
