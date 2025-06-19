#!/usr/bin/env python3
"""
Tests for r4r API module
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.r4r.api import (
    RenderAPI, RenderService, Service, Deploy, Event,
    LogLevel, LogEntry, LogStream, LogStreamOverride
)
from src.r4r.config import Config, APIError


class TestDomainEntities:
    """Test domain entity classes"""
    
    def test_service_creation(self):
        """Test Service entity creation"""
        service = Service(
            id="srv-123",
            name="test-app",
            type="web_service",
            status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z"
        )
        
        assert service.id == "srv-123"
        assert service.name == "test-app"
        assert service.status_icon == "🟢"
        assert "2024-01-01" in service.formatted_created_at
    
    def test_service_from_dict(self):
        """Test Service creation from dictionary"""
        data = {
            'id': 'srv-123',
            'name': 'test-app',
            'type': 'web_service',
            'status': 'active',
            'createdAt': '2024-01-01T00:00:00Z',
            'updatedAt': '2024-01-01T00:00:00Z',
            'autoDeploy': False,
            'branch': 'develop',
            'repo': {'url': 'https://github.com/test/repo'}
        }
        
        service = Service.from_dict(data)
        
        assert service.id == "srv-123"
        assert service.auto_deploy is False
        assert service.branch == "develop"
        assert service.repo_url == "https://github.com/test/repo"
    
    def test_deploy_duration(self):
        """Test Deploy duration calculation"""
        deploy = Deploy(
            id="dep-123",
            service_id="srv-123",
            status="live",
            created_at="2024-01-01T00:00:00Z",
            finished_at="2024-01-01T00:15:30Z",
            commit_id="abc123",
            commit_message="Test deploy"
        )
        
        assert deploy.duration == "0:15:30"
        assert deploy.status_icon == "🟢"
    
    def test_deploy_duration_not_finished(self):
        """Test Deploy duration when not finished"""
        deploy = Deploy(
            id="dep-123",
            service_id="srv-123",
            status="deploying",
            created_at="2024-01-01T00:00:00Z",
            finished_at=None,
            commit_id=None,
            commit_message=None
        )
        
        assert deploy.duration == "N/A"
    
    def test_event_formatted_timestamp(self):
        """Test Event formatted timestamp"""
        event = Event(
            id="evt-123",
            service_id="srv-123",
            type="deploy",
            description="Deployment started",
            timestamp="2024-01-01T12:30:45Z"
        )
        
        assert "2024-01-01" in event.formatted_timestamp
    
    def test_log_level_enum(self):
        """Test LogLevel enum values"""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARN.value == "warn"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.FATAL.value == "fatal"


class TestRenderAPI:
    """Test RenderAPI client"""
    
    @pytest.fixture
    def api(self):
        """Create RenderAPI instance with mocked HTTP client"""
        config = Config(api_key="test-key")
        api = RenderAPI(config)
        api.client = Mock()
        return api
    
    # Test monitoring methods
    def test_get_service_events(self, api):
        """Test getting service events"""
        api.client.get.return_value = {
            'events': [
                {
                    'id': 'evt-123',
                    'serviceId': 'srv-123',
                    'type': 'deploy',
                    'description': 'Deploy started',
                    'timestamp': '2024-01-01T00:00:00Z'
                }
            ]
        }
        
        events = api.get_service_events("srv-123")
        
        assert len(events) == 1
        assert events[0].id == "evt-123"
        api.client.get.assert_called_with("services/srv-123/events")
    
    def test_get_service_status(self, api):
        """Test getting service status"""
        api.client.get.return_value = {
            'id': 'srv-123',
            'name': 'test-app',
            'status': 'active',
            'type': 'web_service',
            'health': 'healthy',
            'updatedAt': '2024-01-01T00:00:00Z'
        }
        
        status = api.get_service_status("srv-123")
        
        assert status['id'] == "srv-123"
        assert status['health'] == "healthy"
        api.client.get.assert_called_with("services/srv-123")
    
    # Test service management methods
    def test_list_services(self, api):
        """Test listing services"""
        api.client.get.return_value = {
            'services': [
                {
                    'id': 'srv-123',
                    'name': 'test-app',
                    'type': 'web_service',
                    'status': 'active'
                }
            ]
        }
        
        services = api.list_services()
        
        assert len(services) == 1
        assert services[0].name == "test-app"
        api.client.get.assert_called_with("services")
    
    def test_create_service(self, api):
        """Test creating a service"""
        from src.r4r.config import ServiceType
        
        api.client.post.return_value = {
            'id': 'srv-new',
            'name': 'new-app',
            'type': 'web_service',
            'status': 'creating'
        }
        
        service = api.create_service(
            name="new-app",
            service_type=ServiceType.WEB_SERVICE,
            repo_url="https://github.com/test/repo",
            branch="main",
            environment_variables={"NODE_ENV": "production"}
        )
        
        assert service.id == "srv-new"
        api.client.post.assert_called_once()
        call_args = api.client.post.call_args
        assert call_args[0][0] == "services"
        assert call_args[0][1]["name"] == "new-app"
        assert call_args[0][1]["envVars"] == {"NODE_ENV": "production"}
    
    def test_suspend_service(self, api):
        """Test suspending a service"""
        api.client.post.return_value = {}
        
        result = api.suspend_service("srv-123")
        
        assert result is True
        api.client.post.assert_called_with("services/srv-123/suspend")
    
    def test_scale_service(self, api):
        """Test scaling a service"""
        api.client.post.return_value = {}
        
        result = api.scale_service("srv-123", 3)
        
        assert result is True
        api.client.post.assert_called_with("services/srv-123/scale", {"numInstances": 3})
    
    # Test deployment methods
    def test_trigger_deploy(self, api):
        """Test triggering a deployment"""
        api.client.post.return_value = {
            'id': 'dep-123',
            'serviceId': 'srv-123',
            'status': 'build_in_progress'
        }
        
        deploy = api.trigger_deploy("srv-123", clear_cache=True)
        
        assert deploy.id == "dep-123"
        api.client.post.assert_called_with("services/srv-123/deploys", {"clearCache": True})
    
    def test_rollback_deploy(self, api):
        """Test rolling back a deployment"""
        api.client.post.return_value = {
            'id': 'dep-rollback',
            'serviceId': 'srv-123',
            'status': 'build_in_progress'
        }
        
        deploy = api.rollback_deploy("srv-123", "dep-previous")
        
        assert deploy.id == "dep-rollback"
        api.client.post.assert_called_with("services/srv-123/rollback", {"deployId": "dep-previous"})


class TestRenderService:
    """Test RenderService high-level operations"""
    
    @pytest.fixture
    def service(self):
        """Create RenderService with mocked API"""
        config = Config(api_key="test-key")
        service = RenderService(config)
        service.api = Mock()
        return service
    
    def test_get_service_overview(self, service):
        """Test getting service overview"""
        service.api.get_service_status.return_value = {'id': 'srv-123', 'status': 'active'}
        service.api.get_service_events.return_value = [Mock() for _ in range(15)]
        service.api.list_deploys.return_value = [Mock() for _ in range(10)]
        
        overview = service.get_service_overview("srv-123")
        
        assert overview['status']['id'] == "srv-123"
        assert len(overview['recent_events']) == 10  # Should limit to 10
        assert len(overview['recent_deploys']) == 5  # Should limit to 5
    
    def test_deploy_and_wait_success(self, service):
        """Test deploy and wait for success"""
        mock_deploy = Mock(id="dep-123", status="build_in_progress")
        service.api.trigger_deploy.return_value = mock_deploy
        
        # Simulate successful deployment
        service.api.list_deploys.side_effect = [
            [Mock(id="dep-123", status="build_in_progress")],
            [Mock(id="dep-123", status="live")]
        ]
        
        with patch('time.sleep'):  # Speed up test
            result = service.deploy_and_wait("srv-123", timeout_minutes=1)
        
        assert result is True
    
    def test_deploy_and_wait_failure(self, service):
        """Test deploy and wait for failure"""
        mock_deploy = Mock(id="dep-123", status="build_in_progress")
        service.api.trigger_deploy.return_value = mock_deploy
        
        # Simulate failed deployment
        service.api.list_deploys.return_value = [
            Mock(id="dep-123", status="failed")
        ]
        
        with patch('time.sleep'):
            result = service.deploy_and_wait("srv-123", timeout_minutes=1)
        
        assert result is False
    
    def test_deploy_and_wait_timeout(self, service):
        """Test deploy and wait timeout"""
        mock_deploy = Mock(id="dep-123", status="build_in_progress")
        service.api.trigger_deploy.return_value = mock_deploy
        
        # Simulate ongoing deployment
        service.api.list_deploys.return_value = [
            Mock(id="dep-123", status="build_in_progress")
        ]
        
        with patch('time.time') as mock_time:
            # Simulate timeout
            mock_time.side_effect = [0, 0, 70, 70]  # Start, first check, timeout
            with patch('time.sleep'):
                result = service.deploy_and_wait("srv-123", timeout_minutes=1)
        
        assert result is False
    
    def test_scale_service_success(self, service):
        """Test successful service scaling"""
        service.api.scale_service.return_value = True
        
        with patch('src.r4r.api.console.print') as mock_print:
            result = service.scale_service("srv-123", 3)
        
        assert result is True
        service.api.scale_service.assert_called_with("srv-123", 3)
        mock_print.assert_called_once()
    
    def test_scale_service_failure(self, service):
        """Test failed service scaling"""
        service.api.scale_service.side_effect = Exception("API error")
        
        with patch('src.r4r.api.console.print') as mock_print:
            result = service.scale_service("srv-123", 3)
        
        assert result is False
        # Should print error message
        assert any("Failed" in str(call) for call in mock_print.call_args_list)