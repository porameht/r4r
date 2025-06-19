#!/usr/bin/env python3
"""
Tests for r4r CLI commands
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.r4r.commands import RenderCLI
from src.r4r.config import Config, APIError
from src.r4r.api import Service, Deploy, Event


class TestRenderCLI:
    """Test suite for RenderCLI commands"""
    
    @pytest.fixture
    def cli(self):
        """Create a RenderCLI instance with mocked dependencies"""
        with patch('src.r4r.commands.ConfigManager') as mock_config_manager:
            mock_config_manager.return_value.get_api_key.return_value = "test-api-key"
            cli = RenderCLI()
            # Mock the render service
            cli._render_service = Mock()
            return cli
    
    @pytest.fixture
    def sample_service(self):
        """Create a sample service for testing"""
        return Service(
            id="srv-123",
            name="test-app",
            type="web_service",
            status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            auto_deploy=True,
            branch="main",
            repo_url="https://github.com/test/repo"
        )
    
    @pytest.fixture
    def sample_deploy(self):
        """Create a sample deployment for testing"""
        return Deploy(
            id="dep-456",
            service_id="srv-123",
            status="live",
            created_at="2024-01-01T00:00:00Z",
            finished_at="2024-01-01T00:10:00Z",
            commit_id="abc123",
            commit_message="Initial deploy"
        )
    
    # Test login command
    def test_login_with_api_key(self, cli):
        """Test login with provided API key"""
        with patch('src.r4r.commands.console.input') as mock_input:
            with patch('src.r4r.commands.RenderService') as mock_service:
                mock_service.return_value.api.list_services.return_value = []
                cli.config_manager.save_config = Mock()
                
                cli.login("test-api-key")
                
                # Verify API key was tested
                mock_service.assert_called_once()
                # Verify config was saved
                cli.config_manager.save_config.assert_called_once()
    
    def test_login_prompt_for_api_key(self, cli):
        """Test login prompting for API key"""
        with patch('src.r4r.commands.console.input', return_value="test-api-key"):
            with patch('src.r4r.commands.RenderService') as mock_service:
                mock_service.return_value.api.list_services.return_value = []
                cli.config_manager.save_config = Mock()
                
                cli.login(None)
                
                # Verify prompted for API key
                mock_service.assert_called_once()
    
    def test_login_invalid_api_key(self, cli):
        """Test login with invalid API key"""
        with patch('src.r4r.commands.RenderService') as mock_service:
            mock_service.side_effect = APIError("Invalid API key", 401)
            
            with pytest.raises(SystemExit):
                cli.login("invalid-key")
    
    # Test logout command
    def test_logout(self, cli):
        """Test logout command"""
        cli.config_manager.clear_config = Mock()
        
        cli.logout()
        
        cli.config_manager.clear_config.assert_called_once()
    
    # Test list services command
    def test_list_services(self, cli, sample_service):
        """Test listing services"""
        cli.render_service.api.list_services.return_value = [sample_service]
        
        with patch('src.r4r.commands.console.print') as mock_print:
            cli.list_services()
            
            # Verify services were fetched
            cli.render_service.api.list_services.assert_called_once()
            # Verify table was printed
            assert mock_print.called
    
    def test_list_services_empty(self, cli):
        """Test listing services when none exist"""
        cli.render_service.api.list_services.return_value = []
        
        with patch('src.r4r.commands.display_warning') as mock_warning:
            cli.list_services()
            
            mock_warning.assert_called_with("No services found")
    
    def test_list_services_filtered_by_type(self, cli, sample_service):
        """Test listing services filtered by type"""
        cli.render_service.api.list_services.return_value = [sample_service]
        
        with patch('src.r4r.commands.console.print'):
            cli.list_services(service_type="web_service")
            
            # Should show the web service
            cli.render_service.api.list_services.assert_called_once()
    
    def test_list_services_filtered_no_match(self, cli, sample_service):
        """Test listing services with no matching type"""
        cli.render_service.api.list_services.return_value = [sample_service]
        
        with patch('src.r4r.commands.display_warning') as mock_warning:
            cli.list_services(service_type="static_site")
            
            mock_warning.assert_called_with("No services found with type 'static_site'")
    
    # Test deploy command
    def test_deploy_service(self, cli, sample_service, sample_deploy):
        """Test deploying a service"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.api.trigger_deploy.return_value = sample_deploy
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_success') as mock_success:
                cli.deploy_service("test-app")
                
                cli.render_service.api.trigger_deploy.assert_called_with("srv-123", False)
                mock_success.assert_called_once()
    
    def test_deploy_service_with_cache_clear(self, cli, sample_service, sample_deploy):
        """Test deploying with cache clear"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.api.trigger_deploy.return_value = sample_deploy
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            cli.deploy_service("test-app", clear_cache=True)
            
            cli.render_service.api.trigger_deploy.assert_called_with("srv-123", True)
    
    def test_deploy_service_cancelled(self, cli, sample_service):
        """Test cancelling deployment"""
        cli._find_service = Mock(return_value=sample_service)
        
        with patch('src.r4r.commands.confirm_action', return_value=False):
            with patch('src.r4r.commands.display_warning') as mock_warning:
                cli.deploy_service("test-app")
                
                mock_warning.assert_called_with("Cancelled")
                cli.render_service.api.trigger_deploy.assert_not_called()
    
    def test_deploy_service_not_found(self, cli):
        """Test deploying non-existent service"""
        cli._find_service = Mock(return_value=None)
        
        cli.deploy_service("non-existent")
        
        cli.render_service.api.trigger_deploy.assert_not_called()
    
    def test_deploy_service_api_error(self, cli, sample_service):
        """Test deploy with API error"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.api.trigger_deploy.side_effect = APIError("Deploy failed", 500)
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_error') as mock_error:
                cli.deploy_service("test-app")
                
                mock_error.assert_called_with("Deploy failed: Deploy failed")
    
    # Test service info command
    def test_show_service_info(self, cli, sample_service, sample_deploy):
        """Test showing service info"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.get_service_overview.return_value = {
            'status': {'id': 'srv-123', 'name': 'test-app'},
            'recent_events': [],
            'recent_deploys': [sample_deploy]
        }
        
        with patch('src.r4r.commands.console.print'):
            cli.show_service_info("test-app")
            
            cli.render_service.get_service_overview.assert_called_with("srv-123")
    
    # Test list deployments command
    def test_list_deployments(self, cli, sample_service, sample_deploy):
        """Test listing deployments"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.api.list_deploys.return_value = [sample_deploy]
        
        with patch('src.r4r.commands.console.print'):
            cli.list_deployments("test-app", limit=5)
            
            cli.render_service.api.list_deploys.assert_called_once()
    
    def test_list_deployments_empty(self, cli, sample_service):
        """Test listing deployments when none exist"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.api.list_deploys.return_value = []
        
        with patch('src.r4r.commands.display_warning') as mock_warning:
            cli.list_deployments("test-app")
            
            mock_warning.assert_called_with("No deployments found for test-app")
    
    # Test scale command
    def test_scale_service(self, cli, sample_service):
        """Test scaling a service"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.scale_service.return_value = True
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            cli.scale_service("test-app", 3)
            
            cli.render_service.scale_service.assert_called_with("srv-123", 3)
    
    def test_scale_service_cancelled(self, cli, sample_service):
        """Test cancelling scale operation"""
        cli._find_service = Mock(return_value=sample_service)
        
        with patch('src.r4r.commands.confirm_action', return_value=False):
            with patch('src.r4r.commands.display_warning') as mock_warning:
                cli.scale_service("test-app", 3)
                
                mock_warning.assert_called_with("Cancelled")
                cli.render_service.scale_service.assert_not_called()
    
    def test_scale_service_failed(self, cli, sample_service):
        """Test scale failure"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.scale_service.return_value = False
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with pytest.raises(SystemExit):
                cli.scale_service("test-app", 3)
    
    # Test suspend command
    def test_suspend_service(self, cli, sample_service):
        """Test suspending a service"""
        cli._find_service = Mock(return_value=sample_service)
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_success') as mock_success:
                cli.suspend_service("test-app")
                
                cli.render_service.api.suspend_service.assert_called_with("srv-123")
                mock_success.assert_called_once()
    
    def test_suspend_service_api_error(self, cli, sample_service):
        """Test suspend with API error"""
        cli._find_service = Mock(return_value=sample_service)
        cli.render_service.api.suspend_service.side_effect = APIError("Cannot suspend", 400)
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_error') as mock_error:
                cli.suspend_service("test-app")
                
                mock_error.assert_called_with("Failed to suspend service: Cannot suspend")
    
    # Test resume command
    def test_resume_service(self, cli, sample_service):
        """Test resuming a service"""
        cli._find_service = Mock(return_value=sample_service)
        
        with patch('src.r4r.commands.display_success') as mock_success:
            cli.resume_service("test-app")
            
            cli.render_service.api.resume_service.assert_called_with("srv-123")
            mock_success.assert_called_once()
    
    # Test restart command
    def test_restart_service(self, cli, sample_service):
        """Test restarting a service"""
        cli._find_service = Mock(return_value=sample_service)
        
        with patch('src.r4r.commands.confirm_action', return_value=True):
            with patch('src.r4r.commands.display_success') as mock_success:
                cli.restart_service("test-app")
                
                cli.render_service.api.restart_service.assert_called_with("srv-123")
                mock_success.assert_called_once()
    
    # Test _find_service helper
    def test_find_service_by_name(self, cli, sample_service):
        """Test finding service by name"""
        cli.render_service.api.list_services.return_value = [sample_service]
        
        result = cli._find_service("test-app")
        
        assert result == sample_service
    
    def test_find_service_by_id(self, cli, sample_service):
        """Test finding service by ID"""
        cli.render_service.api.list_services.return_value = [sample_service]
        
        result = cli._find_service("srv-123")
        
        assert result == sample_service
    
    def test_find_service_not_found(self, cli):
        """Test service not found"""
        cli.render_service.api.list_services.return_value = []
        
        with patch('src.r4r.commands.handle_service_not_found') as mock_not_found:
            result = cli._find_service("non-existent")
            
            assert result is None
            mock_not_found.assert_called_with("non-existent")
    
    def test_find_service_api_error(self, cli):
        """Test find service with API error"""
        cli.render_service.api.list_services.side_effect = APIError("Network error", 500)
        
        with patch('src.r4r.commands.display_error') as mock_error:
            result = cli._find_service("test-app")
            
            assert result is None
            mock_error.assert_called_with("Failed to fetch services: Network error")