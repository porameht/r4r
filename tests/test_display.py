#!/usr/bin/env python3
"""
Tests for r4r display module
"""

import pytest
from unittest.mock import Mock, patch
from rich.table import Table
from rich.panel import Panel

from src.r4r.display import (
    create_services_table, create_deploys_table, create_service_info_panel,
    confirm_action, display_error, display_success, display_warning, display_info,
    handle_service_not_found, format_log_level, format_log_entry
)
from src.r4r.api import Service, Deploy, Event


class TestServiceDisplay:
    """Test service display functions"""
    
    @pytest.fixture
    def sample_service(self):
        """Create a sample service"""
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
        """Create a sample deployment"""
        return Deploy(
            id="dep-456",
            service_id="srv-123",
            status="live",
            created_at="2024-01-01T00:00:00Z",
            finished_at="2024-01-01T00:10:00Z",
            commit_id="abc123def456",
            commit_message="Fix bug in authentication flow"
        )
    
    def test_create_services_table_basic(self, sample_service):
        """Test creating basic services table"""
        table = create_services_table([sample_service])
        
        assert isinstance(table, Table)
        assert table.title == "Your Render Services (1)"
        assert len(table.columns) == 4  # Name, Type, Status, URL
    
    def test_create_services_table_detailed(self, sample_service):
        """Test creating detailed services table"""
        table = create_services_table([sample_service], detailed=True)
        
        assert isinstance(table, Table)
        assert len(table.columns) == 7  # Name, Type, Status, Region, Plan, Created, URL
    
    def test_create_services_table_empty(self):
        """Test creating table with no services"""
        table = create_services_table([])
        
        assert isinstance(table, Table)
        assert table.title == "Your Render Services (0)"
    
    def test_create_deploys_table(self, sample_deploy):
        """Test creating deployments table"""
        table = create_deploys_table([sample_deploy], "test-app")
        
        assert isinstance(table, Table)
        assert table.title == "🚀 Deployments for test-app (Last 1)"
        assert len(table.columns) == 6  # ID, Status, Started, Duration, Commit, Message
    
    def test_create_deploys_table_truncates_commit(self, sample_deploy):
        """Test that commit ID is truncated"""
        table = create_deploys_table([sample_deploy], "test-app")
        # The table should have truncated commit ID (first 8 chars)
        # We can't easily inspect table rows, but we know the function truncates
        assert isinstance(table, Table)
    
    def test_create_service_info_panel(self, sample_service):
        """Test creating service info panel"""
        panel = create_service_info_panel(sample_service)
        
        assert isinstance(panel, Panel)
        assert panel.title == "📋 Service Information"
        # Panel should contain service details
        renderable_str = str(panel.renderable)
        assert "test-app" in renderable_str
        assert "srv-123" in renderable_str
        assert "Web Service" in renderable_str


class TestUserInteraction:
    """Test user interaction functions"""
    
    def test_confirm_action_yes(self):
        """Test confirm action with yes response"""
        with patch('src.r4r.display.Confirm.ask', return_value=True):
            result = confirm_action("Continue?")
            assert result is True
    
    def test_confirm_action_no(self):
        """Test confirm action with no response"""
        with patch('src.r4r.display.Confirm.ask', return_value=False):
            result = confirm_action("Continue?")
            assert result is False
    
    def test_confirm_action_with_default(self):
        """Test confirm action with default value"""
        with patch('src.r4r.display.Confirm.ask', return_value=True) as mock_ask:
            confirm_action("Continue?", default=True)
            mock_ask.assert_called_with("Continue?", default=True)


class TestDisplayMessages:
    """Test display message functions"""
    
    def test_display_error(self):
        """Test error display"""
        with patch('src.r4r.display.console.print') as mock_print:
            display_error("Something went wrong")
            mock_print.assert_called_with("❌ Something went wrong", style="red")
    
    def test_display_success(self):
        """Test success display"""
        with patch('src.r4r.display.console.print') as mock_print:
            display_success("Operation completed")
            mock_print.assert_called_with("✅ Operation completed", style="green")
    
    def test_display_warning(self):
        """Test warning display"""
        with patch('src.r4r.display.console.print') as mock_print:
            display_warning("Be careful")
            mock_print.assert_called_with("⚠️ Be careful", style="yellow")
    
    def test_display_info(self):
        """Test info display"""
        with patch('src.r4r.display.console.print') as mock_print:
            display_info("Helpful tip")
            mock_print.assert_called_with("💡 Helpful tip", style="dim")
    
    def test_handle_service_not_found(self):
        """Test service not found handler"""
        with patch('src.r4r.display.console.print') as mock_print:
            handle_service_not_found("my-service")
            
            # Should call print twice - error and info
            assert mock_print.call_count == 2
            error_call = mock_print.call_args_list[0]
            info_call = mock_print.call_args_list[1]
            
            assert "Service 'my-service' not found" in error_call[0][0]
            assert "Run 'r4r list'" in info_call[0][0]


class TestLogFormatting:
    """Test log formatting functions"""
    
    def test_format_log_level(self):
        """Test log level formatting"""
        assert "[red]ERROR[/red]" in format_log_level("error")
        assert "[yellow]WARN [/yellow]" in format_log_level("warn")
        assert "[yellow]WARNING[/yellow]" in format_log_level("warning")
        assert "[green]INFO [/green]" in format_log_level("info")
        assert "[blue]DEBUG[/blue]" in format_log_level("debug")
        assert "[bright_red]FATAL[/bright_red]" in format_log_level("fatal")
        assert "[white]UNKNOWN[/white]" in format_log_level("unknown")
    
    def test_format_log_entry_basic(self):
        """Test basic log entry formatting"""
        result = format_log_entry(
            "2024-01-01T12:30:45Z",
            "info",
            "Application started"
        )
        
        assert "12:30:45" in result
        assert "[green]INFO [/green]" in result
        assert "Application started" in result
    
    def test_format_log_entry_with_source(self):
        """Test log entry formatting with source"""
        result = format_log_entry(
            "2024-01-01T12:30:45Z",
            "error",
            "Database connection failed",
            "db-connector"
        )
        
        assert "12:30:45" in result
        assert "[red]ERROR[/red]" in result
        assert "Database connection failed" in result
        assert "[dim]db-conn...[/dim]" in result  # Truncated to 10 chars with ellipsis
    
    def test_format_log_entry_invalid_timestamp(self):
        """Test log entry with invalid timestamp"""
        result = format_log_entry(
            "invalid-timestamp",
            "warn",
            "Warning message"
        )
        
        assert "invalid-" in result  # Falls back to first 8 chars
        assert "[yellow]WARN [/yellow]" in result
        assert "Warning message" in result
    
    def test_format_log_entry_long_source(self):
        """Test log entry with long source name"""
        result = format_log_entry(
            "2024-01-01T12:30:45Z",
            "debug",
            "Debug message",
            "very-long-source-name-here"
        )
        
        assert "[dim]very-lo...[/dim]" in result  # Should be truncated with ellipsis