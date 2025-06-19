#!/usr/bin/env python3
"""
Tests for r4r config module
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

from src.r4r.config import (
    Config, ServiceType, ServiceStatus, APIError, HTTPClient,
    ConfigManager, format_timestamp, truncate_string, get_status_icon
)


class TestEnums:
    """Test enum values"""
    
    def test_service_type_values(self):
        """Test ServiceType enum values"""
        assert ServiceType.WEB_SERVICE.value == "web_service"
        assert ServiceType.BACKGROUND_WORKER.value == "background_worker"
        assert ServiceType.STATIC_SITE.value == "static_site"
        assert ServiceType.PRIVATE_SERVICE.value == "private_service"
    
    def test_service_status_values(self):
        """Test ServiceStatus enum values"""
        assert ServiceStatus.CREATING.value == "creating"
        assert ServiceStatus.ACTIVE.value == "active"
        assert ServiceStatus.SUSPENDED.value == "suspended"
        assert ServiceStatus.BUILD_FAILED.value == "build_failed"
        assert ServiceStatus.DEPLOYING.value == "deploying"


class TestConfig:
    """Test Config dataclass"""
    
    def test_config_creation(self):
        """Test creating Config instance"""
        config = Config(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.render.com/v1"
    
    def test_config_custom_url(self):
        """Test Config with custom base URL"""
        config = Config(api_key="test-key", base_url="https://custom.api.com")
        assert config.base_url == "https://custom.api.com"
    
    def test_config_from_env(self):
        """Test creating Config from environment"""
        with patch('os.getenv', return_value="env-key"):
            config = Config.from_env()
            assert config.api_key == "env-key"
    
    def test_config_from_env_missing(self):
        """Test Config.from_env with missing API key"""
        with patch('os.getenv', return_value=None):
            with pytest.raises(ValueError, match="RENDER_API_KEY"):
                Config.from_env()


class TestAPIError:
    """Test custom APIError exception"""
    
    def test_api_error_creation(self):
        """Test creating APIError"""
        error = APIError("Test error", 404)
        assert str(error) == "Test error"
        assert error.status_code == 404
    
    def test_api_error_without_status(self):
        """Test APIError without status code"""
        error = APIError("Test error")
        assert error.status_code is None


class TestHTTPClient:
    """Test HTTPClient class"""
    
    @pytest.fixture
    def client(self):
        """Create HTTPClient instance"""
        config = Config(api_key="test-key")
        return HTTPClient(config)
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response"""
        response = Mock()
        response.json.return_value = {"result": "success"}
        response.content = b'{"result": "success"}'
        response.raise_for_status = Mock()
        return response
    
    def test_client_initialization(self, client):
        """Test HTTPClient initialization"""
        assert client.config.api_key == "test-key"
        assert "Bearer test-key" in client.session.headers["Authorization"]
        assert client.session.headers["Accept"] == "application/json"
    
    def test_handle_response_success(self, client, mock_response):
        """Test successful response handling"""
        result = client._handle_response(mock_response)
        assert result == {"result": "success"}
    
    def test_handle_response_empty(self, client):
        """Test handling empty response"""
        response = Mock()
        response.content = b''
        response.raise_for_status = Mock()
        
        result = client._handle_response(response)
        assert result == {}
    
    def test_handle_response_http_error(self, client):
        """Test handling HTTP error"""
        response = Mock()
        response.status_code = 404
        response.reason = "Not Found"
        response.json.return_value = {"message": "Service not found"}
        response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        
        with pytest.raises(APIError) as exc_info:
            client._handle_response(response)
        
        assert exc_info.value.status_code == 404
        assert "Service not found" in str(exc_info.value)
    
    def test_handle_response_json_error(self, client):
        """Test handling response with invalid JSON"""
        response = Mock()
        response.status_code = 500
        response.reason = "Internal Server Error"
        response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        
        with pytest.raises(APIError) as exc_info:
            client._handle_response(response)
        
        assert "HTTP 500" in str(exc_info.value)
    
    def test_handle_response_request_exception(self, client):
        """Test handling request exception"""
        response = Mock()
        response.raise_for_status.side_effect = requests.exceptions.ConnectionError("Network error")
        
        with pytest.raises(APIError, match="Request failed"):
            client._handle_response(response)
    
    def test_get_request(self, client, mock_response):
        """Test GET request"""
        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            result = client.get("services")
            
            mock_get.assert_called_with(
                "https://api.render.com/v1/services",
                params=None
            )
            assert result == {"result": "success"}
    
    def test_get_request_with_params(self, client, mock_response):
        """Test GET request with parameters"""
        with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
            result = client.get("services", params={"limit": 10})
            
            mock_get.assert_called_with(
                "https://api.render.com/v1/services",
                params={"limit": 10}
            )
    
    def test_post_request(self, client, mock_response):
        """Test POST request"""
        with patch.object(client.session, 'post', return_value=mock_response) as mock_post:
            data = {"name": "test-service"}
            result = client.post("services", data)
            
            mock_post.assert_called_with(
                "https://api.render.com/v1/services",
                json=data
            )
            assert result == {"result": "success"}
    
    def test_put_request(self, client, mock_response):
        """Test PUT request"""
        with patch.object(client.session, 'put', return_value=mock_response) as mock_put:
            data = {"name": "updated-service"}
            result = client.put("services/123", data)
            
            mock_put.assert_called_with(
                "https://api.render.com/v1/services/123",
                json=data
            )
    
    def test_delete_request(self, client, mock_response):
        """Test DELETE request"""
        with patch.object(client.session, 'delete', return_value=mock_response) as mock_delete:
            result = client.delete("services/123")
            
            mock_delete.assert_called_with(
                "https://api.render.com/v1/services/123"
            )


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_format_timestamp(self):
        """Test timestamp formatting"""
        assert format_timestamp("2024-01-01T12:30:45Z") == "2024-01-01 12:30:45"
        assert format_timestamp("2024-01-01T12:30:45.123Z") == "2024-01-01 12:30:45"
        assert format_timestamp("invalid") == "invalid"
        assert format_timestamp("") == "N/A"  # Empty string returns N/A
    
    def test_truncate_string(self):
        """Test string truncation"""
        assert truncate_string("short", 10) == "short"
        assert truncate_string("this is a long string", 10) == "this is..."
        assert truncate_string("exactly10!", 10) == "exactly10!"
        assert truncate_string("eleven char", 10) == "eleven ..."
    
    def test_get_status_icon(self):
        """Test status icon mapping"""
        assert get_status_icon("live") == "🟢"
        assert get_status_icon("active") == "🟢"
        assert get_status_icon("suspended") == "🔴"
        assert get_status_icon("build_failed") == "🔴"
        assert get_status_icon("deploying") == "🟡"
        assert get_status_icon("succeeded") == "✅"
        assert get_status_icon("failed") == "❌"
        assert get_status_icon("unknown") == "❓"


class TestConfigManager:
    """Test ConfigManager class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def config_manager(self, temp_dir):
        """Create ConfigManager with temp directory"""
        return ConfigManager(config_dir=temp_dir)
    
    def test_save_and_load_config(self, config_manager):
        """Test saving and loading config"""
        config_data = {
            "api_key": "test-key",
            "user": "test-user"
        }
        
        config_manager.save_config(config_data)
        loaded = config_manager.load_config()
        
        assert loaded == config_data
    
    def test_load_config_not_exists(self, config_manager):
        """Test loading config when file doesn't exist"""
        result = config_manager.load_config()
        assert result == {}
    
    def test_get_api_key_from_env(self, config_manager):
        """Test getting API key from environment"""
        with patch('os.getenv', return_value="env-key"):
            api_key = config_manager.get_api_key()
            assert api_key == "env-key"
    
    def test_get_api_key_from_config(self, config_manager):
        """Test getting API key from config file"""
        config_manager.save_config({"api_key": "config-key"})
        
        with patch('os.getenv', return_value=None):
            api_key = config_manager.get_api_key()
            assert api_key == "config-key"
    
    def test_get_api_key_not_found(self, config_manager):
        """Test getting API key when not found"""
        with patch('os.getenv', return_value=None):
            api_key = config_manager.get_api_key()
            assert api_key is None
    
    def test_clear_config(self, config_manager):
        """Test clearing config"""
        config_manager.save_config({"api_key": "test-key"})
        assert config_manager.config_file.exists()
        
        config_manager.clear_config()
        assert not config_manager.config_file.exists()
    
    def test_clear_config_not_exists(self, config_manager):
        """Test clearing config when file doesn't exist"""
        # Should not raise error
        config_manager.clear_config()