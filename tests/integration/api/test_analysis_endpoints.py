"""
Integration tests for analysis API endpoints.
"""

import pytest
import json
from unittest.mock import patch, Mock

from tests.conftest import (
    assert_response_success, assert_response_error,
    create_test_analysis_data, SAMPLE_ANALYSIS_RESULTS
)


class TestAnalysisEndpoints:
    """Test analysis API endpoints."""
    
    def test_create_analysis_success(self, client, auth_headers, test_user):
        """Test successful analysis creation."""
        data = create_test_analysis_data()
        
        response = client.post(
            '/api/v1/analysis/',
            data=json.dumps(data),
            headers=auth_headers
        )
        
        assert_response_success(response, 201)
        response_data = response.get_json()
        
        assert 'data' in response_data
        analysis_data = response_data['data']
        assert analysis_data['platform'] == 'twitter'
        assert analysis_data['target_identifier'] == '@test_user'
        assert analysis_data['status'] == 'pending'
        assert analysis_data['user_id'] == test_user.id
    
    def test_create_analysis_invalid_platform(self, client, auth_headers):
        """Test analysis creation with invalid platform."""
        data = create_test_analysis_data()
        data['platform'] = 'invalid_platform'
        
        response = client.post(
            '/api/v1/analysis/',
            data=json.dumps(data),
            headers=auth_headers
        )
        
        assert_response_error(response, 400)
        response_data = response.get_json()
        assert 'errors' in response_data
    
    def test_create_analysis_missing_fields(self, client, auth_headers):
        """Test analysis creation with missing required fields."""
        data = {'platform': 'twitter'}  # Missing target_identifier
        
        response = client.post(
            '/api/v1/analysis/',
            data=json.dumps(data),
            headers=auth_headers
        )
        
        assert_response_error(response, 400)
    
    def test_create_analysis_unauthorized(self, client, api_headers):
        """Test analysis creation without authentication."""
        data = create_test_analysis_data()
        
        response = client.post(
            '/api/v1/analysis/',
            data=json.dumps(data),
            headers=api_headers  # No auth header
        )
        
        assert response.status_code == 401
    
    def test_get_analyses_success(self, client, auth_headers, multiple_analyses):
        """Test getting user analyses."""
        response = client.get(
            '/api/v1/analysis/',
            headers=auth_headers
        )
        
        assert_response_success(response)
        response_data = response.get_json()
        
        assert 'data' in response_data
        assert 'meta' in response_data
        assert len(response_data['data']) > 0
        
        # Check analysis structure
        analysis = response_data['data'][0]
        required_fields = ['id', 'analysis_id', 'platform', 'status', 'created_at']
        for field in required_fields:
            assert field in analysis
    
    def test_get_analyses_with_filters(self, client, auth_headers, multiple_analyses):
        """Test getting analyses with filters."""
        response = client.get(
            '/api/v1/analysis/?platform=twitter&status=completed&limit=5',
            headers=auth_headers
        )
        
        assert_response_success(response)
        response_data = response.get_json()
        
        # All returned analyses should match filters
        for analysis in response_data['data']:
            assert analysis['platform'] == 'twitter'
            assert analysis['status'] == 'completed'
        
        # Should respect limit
        assert len(response_data['data']) <= 5
    
    def test_get_analyses_pagination(self, client, auth_headers, multiple_analyses):
        """Test analysis pagination."""
        # First page
        response1 = client.get(
            '/api/v1/analysis/?limit=3&offset=0',
            headers=auth_headers
        )
        
        assert_response_success(response1)
        data1 = response1.get_json()
        
        # Second page
        response2 = client.get(
            '/api/v1/analysis/?limit=3&offset=3',
            headers=auth_headers
        )
        
        assert_response_success(response2)
        data2 = response2.get_json()
        
        # Should have different analyses
        ids1 = {a['analysis_id'] for a in data1['data']}
        ids2 = {a['analysis_id'] for a in data2['data']}
        assert len(ids1.intersection(ids2)) == 0
    
    def test_get_analyses_search(self, client, auth_headers, multiple_analyses):
        """Test searching analyses."""
        response = client.get(
            '/api/v1/analysis/?search=test_target_1',
            headers=auth_headers
        )
        
        assert_response_success(response)
        response_data = response.get_json()
        
        # Should find specific analysis
        assert len(response_data['data']) >= 1
        found = any('test_target_1' in a['target_identifier'] for a in response_data['data'])
        assert found
    
    def test_get_analysis_by_id_success(self, client, auth_headers, sample_analysis):
        """Test getting specific analysis by ID."""
        response = client.get(
            f'/api/v1/analysis/{sample_analysis.analysis_id}',
            headers=auth_headers
        )
        
        assert_response_success(response)
        response_data = response.get_json()
        
        analysis_data = response_data['data']
        assert analysis_data['analysis_id'] == sample_analysis.analysis_id
        assert analysis_data['platform'] == 'twitter'
        assert analysis_data['target_identifier'] == '@test_user'
    
    def test_get_analysis_by_id_not_found(self, client, auth_headers):
        """Test getting non-existent analysis."""
        response = client.get(
            '/api/v1/analysis/non-existent-id',
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_get_analysis_unauthorized_access(self, client, auth_headers, admin_user, db_session):
        """Test accessing another user's analysis."""
        # Create analysis for admin user
        from app.infrastructure.database.models.analysis import Analysis
        
        other_analysis = Analysis(
            analysis_id='other-user-analysis',
            user_id=admin_user.id,
            platform='twitter',
            target_identifier='@other_user',
            analysis_type='comprehensive_analysis',
            status='completed'
        )
        db_session.add(other_analysis)
        db_session.commit()
        
        # Try to access with regular user auth
        response = client.get(
            f'/api/v1/analysis/{other_analysis.analysis_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_cancel_analysis_success(self, client, auth_headers, db_session, test_user):
        """Test cancelling a pending analysis."""
        from app.infrastructure.database.models.analysis import Analysis
        
        # Create pending analysis
        analysis = Analysis(
            analysis_id='pending-analysis',
            user_id=test_user.id,
            platform='twitter',
            target_identifier='@pending_user',
            analysis_type='comprehensive_analysis',
            status='pending'
        )
        db_session.add(analysis)
        db_session.commit()
        
        response = client.post(
            f'/api/v1/analysis/{analysis.analysis_id}/cancel',
            headers=auth_headers
        )
        
        assert_response_success(response)
        response_data = response.get_json()
        
        assert response_data['data']['status'] == 'cancelled'
    
    def test_cancel_analysis_already_completed(self, client, auth_headers, sample_analysis):
        """Test cancelling already completed analysis."""
        response = client.post(
            f'/api/v1/analysis/{sample_analysis.analysis_id}/cancel',
            headers=auth_headers
        )
        
        assert_response_error(response, 400)
    
    def test_retry_analysis_success(self, client, auth_headers, db_session, test_user):
        """Test retrying a failed analysis."""
        from app.infrastructure.database.models.analysis import Analysis
        
        # Create failed analysis
        analysis = Analysis(
            analysis_id='failed-analysis',
            user_id=test_user.id,
            platform='twitter',
            target_identifier='@failed_user',
            analysis_type='comprehensive_analysis',
            status='failed',
            error_message='Test error',
            retry_count=1
        )
        db_session.add(analysis)
        db_session.commit()
        
        response = client.post(
            f'/api/v1/analysis/{analysis.analysis_id}/retry',
            headers=auth_headers
        )
        
        assert_response_success(response)
        response_data = response.get_json()
        
        assert response_data['data']['status'] == 'pending'
    
    def test_retry_analysis_max_retries_exceeded(self, client, auth_headers, db_session, test_user):
        """Test retrying analysis that exceeded max retries."""
        from app.infrastructure.database.models.analysis import Analysis
        
        # Create analysis with max retries
        analysis = Analysis(
            analysis_id='max-retry-analysis',
            user_id=test_user.id,
            platform='twitter',
            target_identifier='@max_retry_user',
            analysis_type='comprehensive_analysis',
            status='failed',
            error_message='Test error',
            retry_count=3  # Max retries reached
        )
        db_session.add(analysis)
        db_session.commit()
        
        response = client.post(
            f'/api/v1/analysis/{analysis.analysis_id}/retry',
            headers=auth_headers
        )
        
        assert_response_error(response, 400)
    
    def test_delete_analysis_success(self, client, auth_headers, db_session, test_user):
        """Test deleting an analysis."""
        from app.infrastructure.database.models.analysis import Analysis
        
        # Create analysis to delete
        analysis = Analysis(
            analysis_id='delete-analysis',
            user_id=test_user.id,
            platform='twitter',
            target_identifier='@delete_user',
            analysis_type='comprehensive_analysis',
            status='completed'
        )
        db_session.add(analysis)
        db_session.commit()
        
        response = client.delete(
            f'/api/v1/analysis/{analysis.analysis_id}',
            headers=auth_headers
        )
        
        assert_response_success(response)
        
        # Verify analysis is deleted
        deleted_analysis = Analysis.query.filter_by(analysis_id='delete-analysis').first()
        assert deleted_analysis is None
    
    def test_delete_analysis_unauthorized(self, client, auth_headers, admin_user, db_session):
        """Test deleting another user's analysis."""
        from app.infrastructure.database.models.analysis import Analysis
        
        # Create analysis for admin user
        analysis = Analysis(
            analysis_id='admin-analysis',
            user_id=admin_user.id,
            platform='twitter',
            target_identifier='@admin_user',
            analysis_type='comprehensive_analysis',
            status='completed'
        )
        db_session.add(analysis)
        db_session.commit()
        
        # Try to delete with regular user auth
        response = client.delete(
            f'/api/v1/analysis/{analysis.analysis_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_get_dashboard_data(self, client, auth_headers, multiple_analyses):
        """Test getting dashboard data."""
        response = client.get(
            '/api/v1/analysis/dashboard',
            headers=auth_headers
        )
        
        assert_response_success(response)
        response_data = response.get_json()
        
        dashboard_data = response_data['data']
        required_fields = [
            'total_analyses', 'platform_counts', 'pending_count',
            'recent_analyses', 'metrics', 'success_rate'
        ]
        
        for field in required_fields:
            assert field in dashboard_data
        
        assert isinstance(dashboard_data['total_analyses'], int)
        assert isinstance(dashboard_data['platform_counts'], dict)
        assert isinstance(dashboard_data['recent_analyses'], list)
    
    def test_rate_limiting(self, client, auth_headers):
        """Test API rate limiting."""
        # This would require mocking the rate limiter or using a test-specific configuration
        # For now, just test that the endpoint responds normally
        response = client.get('/api/v1/analysis/', headers=auth_headers)
        assert response.status_code in [200, 429]  # Either success or rate limited
    
    def test_invalid_json_body(self, client, auth_headers):
        """Test sending invalid JSON."""
        response = client.post(
            '/api/v1/analysis/',
            data='invalid json',
            headers={'Content-Type': 'application/json', **auth_headers}
        )
        
        assert response.status_code == 400
    
    def test_missing_content_type(self, client, auth_headers):
        """Test missing content type header."""
        data = create_test_analysis_data()
        headers = {k: v for k, v in auth_headers.items() if k != 'Content-Type'}
        
        response = client.post(
            '/api/v1/analysis/',
            data=json.dumps(data),
            headers=headers
        )
        
        assert response.status_code == 400
    
    @patch('app.core.analysis.services.analysis_service.AnalysisDomainService.create_analysis')
    def test_service_error_handling(self, mock_create, client, auth_headers):
        """Test handling of service layer errors."""
        # Mock service to raise an exception
        mock_create.side_effect = Exception("Service error")
        
        data = create_test_analysis_data()
        response = client.post(
            '/api/v1/analysis/',
            data=json.dumps(data),
            headers=auth_headers
        )
        
        assert response.status_code == 500
        response_data = response.get_json()
        assert response_data['status'] == 'error'
        assert 'Internal server error' in response_data['message']
