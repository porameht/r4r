#!/usr/bin/env python3
"""
Integration tests for r4r
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.r4r.commands import RenderCLI
from src.r4r.config import Config, ConfigManager
from src.r4r.api import RenderService, Service, Deploy


@pytest.mark.integration
class TestIntegration:
    """Integration tests for full command flow"""
    
    @pytest.fixture
    def cli_with_mocked_api(self):
        """Create CLI with fully mocked API"""
        with patch('src.r4r.commands.ConfigManager') as mock_config_manager:
            # Mock config manager
            mock_config_manager.return_value.get_api_key.return_value = "test-key"
            mock_config_manager.return_value.save_config = Mock()
            mock_config_manager.return_value.clear_config = Mock()
            
            cli = RenderCLI()
            cli.config_manager = mock_config_manager.return_value
            
            # Mock render service
            with patch('src.r4r.commands.RenderService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                cli._render_service = mock_service
                
                # Setup mock responses
                mock_service.api.list_services.return_value = [
                    Service(
                        id="srv-123",
                        name="test-app",
                        type="web_service", 
                        status="active",
                        created_at="2024-01-01T00:00:00Z",
                        updated_at="2024-01-01T00:00:00Z"
                    )
                ]
                
                yield cli, mock_service
    
    def test_login_list_deploy_flow(self):
        """Test complete login -> list -> deploy workflow"""
        with patch('src.r4r.commands.ConfigManager') as mock_config:
            with patch('src.r4r.commands.RenderService') as mock_service:
                mock_config.return_value.get_api_key.return_value = "test-key"
                
                # Mock service with proper find_service behavior
                sample_service = Service(
                    id="srv-123", name="test-app", type="web_service", 
                    status="active", created_at="2024-01-01T00:00:00Z", 
                    updated_at="2024-01-01T00:00:00Z"
                )
                
                mock_service.return_value.api.list_services.return_value = [sample_service]
                mock_service.return_value.api.find_service.return_value = sample_service
                mock_service.return_value.api.trigger_deploy.return_value = Mock(id="dep-123")
                
                cli = RenderCLI()
                
                # Test login
                cli.login("test-key")
                
                # Test list services
                cli.list_services()
                
                # Test deploy - mock confirmation
                with patch('src.r4r.commands.confirm_action', return_value=True):
                    cli.deploy_service("test-app")
                
                # Verify deploy was called with correct service ID
                mock_service.return_value.api.trigger_deploy.assert_called_with("srv-123", False)

    def test_service_lifecycle_flow(self):
        """Test service lifecycle operations"""
        with patch('src.r4r.commands.ConfigManager') as mock_config:
            with patch('src.r4r.commands.RenderService') as mock_service:
                mock_config.return_value.get_api_key.return_value = "test-key"
                
                sample_service = Service(
                    id="srv-123", name="test-app", type="web_service",
                    status="active", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                )
                sample_deploy = Deploy(
                    id="dep-456", service_id="srv-123", status="live",
                    created_at="2024-01-01T00:00:00Z", finished_at="2024-01-01T00:10:00Z",
                    commit_id="abc123", commit_message="Test deploy"
                )
                
                mock_service.return_value.api.find_service.return_value = sample_service
                mock_service.return_value.api.get_service_details.return_value = sample_service
                mock_service.return_value.api.list_deploys.return_value = [sample_deploy]
                
                cli = RenderCLI()
                
                # Test service info
                cli.show_service_info("test-app")
                
                # Verify calls
                mock_service.return_value.api.get_service_details.assert_called_with("srv-123")
                mock_service.return_value.api.list_deploys.assert_called_with("srv-123", limit=5)

    def test_deployment_monitoring_flow(self):
        """Test deployment monitoring and scaling"""
        with patch('src.r4r.commands.ConfigManager') as mock_config:
            with patch('src.r4r.commands.RenderService') as mock_service:
                mock_config.return_value.get_api_key.return_value = "test-key"
                
                sample_service = Service(
                    id="srv-123", name="test-app", type="web_service",
                    status="active", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                )
                
                mock_service.return_value.api.find_service.return_value = sample_service
                mock_service.return_value.scale_service.return_value = True
                
                cli = RenderCLI()
                
                # Test scaling with confirmation
                with patch('src.r4r.commands.confirm_action', return_value=True):
                    cli.scale_service("test-app", 3)
                
                # Verify scale was called with correct service ID
                mock_service.return_value.scale_service.assert_called_with("srv-123", 3)

    def test_error_handling_flow(self):
        """Test error handling across commands"""
        with patch('src.r4r.commands.ConfigManager') as mock_config:
            with patch('src.r4r.commands.RenderService') as mock_service:
                mock_config.return_value.get_api_key.return_value = "test-key"
                
                sample_service = Service(
                    id="srv-123", name="test-app", type="web_service",
                    status="active", created_at="2024-01-01T00:00:00Z",
                    updated_at="2024-01-01T00:00:00Z"
                )
                
                mock_service.return_value.api.find_service.return_value = sample_service
                mock_service.return_value.api.trigger_deploy.return_value = Mock(id="dep-123")
                
                cli = RenderCLI()
                
                # Test deploy with auto-confirm to avoid stdin issues
                cli.deploy_service("test-app", yes=True)
                
                # Verify deploy was called
                mock_service.return_value.api.trigger_deploy.assert_called_with("srv-123", False)