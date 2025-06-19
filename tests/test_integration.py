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
    
    def test_login_list_deploy_flow(self, cli_with_mocked_api):
        """Test login -> list services -> deploy flow"""
        cli, mock_service = cli_with_mocked_api
        
        # 1. Login
        with patch('src.r4r.commands.console.input', return_value="test-key"):
            cli.login(None)
        
        assert cli.config_manager.save_config.called
        
        # 2. List services
        with patch('src.r4r.commands.console.print'):
            cli.list_services()
        
        mock_service.api.list_services.assert_called()
        
        # 3. Deploy service
        mock_deploy = Deploy(
            id="dep-123",
            service_id="srv-123",
            status="build_in_progress",
            created_at="2024-01-01T00:00:00Z",
            finished_at=None,
            commit_id="abc123",
            commit_message="Deploy"
        )
        mock_service.api.trigger_deploy.return_value = mock_deploy
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_success'):
                cli.deploy_service("test-app")
        
        mock_service.api.trigger_deploy.assert_called_with("srv-123", False)
    
    def test_service_lifecycle_flow(self, cli_with_mocked_api):
        """Test service lifecycle: info -> suspend -> resume -> restart"""
        cli, mock_service = cli_with_mocked_api
        
        # Setup service overview
        mock_service.get_service_overview.return_value = {
            'status': {'id': 'srv-123', 'name': 'test-app'},
            'recent_events': [],
            'recent_deploys': []
        }
        
        # 1. Get service info
        with patch('src.r4r.commands.console.print'):
            cli.show_service_info("test-app")
        
        mock_service.get_service_overview.assert_called_with("srv-123")
        
        # 2. Suspend service
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_success'):
                cli.suspend_service("test-app")
        
        mock_service.api.suspend_service.assert_called_with("srv-123")
        
        # 3. Resume service
        with patch('src.r4r.commands.display_success'):
            cli.resume_service("test-app")
        
        mock_service.api.resume_service.assert_called_with("srv-123")
        
        # 4. Restart service
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_success'):
                cli.restart_service("test-app")
        
        mock_service.api.restart_service.assert_called_with("srv-123")
    
    def test_deployment_monitoring_flow(self, cli_with_mocked_api):
        """Test deployment monitoring flow"""
        cli, mock_service = cli_with_mocked_api
        
        # Setup deployments
        deploys = [
            Deploy(
                id=f"dep-{i}",
                service_id="srv-123",
                status="live" if i == 0 else "failed",
                created_at=f"2024-01-0{i+1}T00:00:00Z",
                finished_at=f"2024-01-0{i+1}T00:10:00Z",
                commit_id=f"abc{i}",
                commit_message=f"Deploy {i}"
            )
            for i in range(3)
        ]
        
        mock_service.api.list_deploys.return_value = deploys
        
        # List deployments
        with patch('src.r4r.commands.console.print'):
            cli.list_deployments("test-app", limit=5)
        
        mock_service.api.list_deploys.assert_called()
        
        # Scale service
        mock_service.scale_service.return_value = True
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            cli.scale_service("test-app", 3)
        
        mock_service.scale_service.assert_called_with("srv-123", 3)
    
    def test_error_handling_flow(self, cli_with_mocked_api):
        """Test error handling throughout the flow"""
        cli, mock_service = cli_with_mocked_api
        
        # Service not found
        mock_service.api.list_services.return_value = []
        
        with patch('src.r4r.commands.handle_service_not_found') as mock_not_found:
            cli.deploy_service("non-existent")
            mock_not_found.assert_called_with("non-existent")
        
        # API error during deploy
        from src.r4r.config import APIError
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
        mock_service.api.trigger_deploy.side_effect = APIError("Rate limited", 429)
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_error') as mock_error:
                cli.deploy_service("test-app")
                mock_error.assert_called_with("Deploy failed: Rate limited")