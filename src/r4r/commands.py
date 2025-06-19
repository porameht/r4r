#!/usr/bin/env python3
"""
r4r CLI Commands
Clean command implementations following KISS and DRY principles
"""

import time
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config, ConfigManager, APIError
from .api import RenderService, Service
from .display import (
    create_services_table, create_deploys_table, create_service_info_panel,
    confirm_action, display_error, display_success, display_warning, display_info,
    handle_service_not_found, format_log_entry
)

console = Console()

class RenderCLI:
    """Application Controller: CLI command handlers"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self._render_service = None
    
    @property
    def render_service(self) -> RenderService:
        """Lazy-load render service"""
        if not self._render_service:
            api_key = self.config_manager.get_api_key()
            if not api_key:
                display_error("No API key found. Run 'r4r login' first.")
                display_info("Get your API key from: https://dashboard.render.com/u/settings#api-keys")
                raise SystemExit(1)
            
            config = Config(api_key=api_key)
            self._render_service = RenderService(config)
        
        return self._render_service
    
    def login(self, api_key: Optional[str] = None) -> None:
        """Handle login command"""
        if not api_key:
            console.print("🔑 Get your API key from: https://dashboard.render.com/u/settings#api-keys")
            api_key = console.input("Paste your API key: ", password=True)
        
        try:
            # Test the API key
            config = Config(api_key=api_key)
            test_service = RenderService(config)
            services = test_service.api.list_services()
            
            # Save config
            from datetime import datetime
            config_data = {
                'api_key': api_key,
                'login_time': datetime.now().isoformat()
            }
            self.config_manager.save_config(config_data)
            
            display_success(f"Logged in successfully! Found {len(services)} services.")
            
        except APIError as e:
            display_error(f"Login failed: {e.message}")
            raise SystemExit(1)
    
    def logout(self) -> None:
        """Handle logout command"""
        self.config_manager.clear_config()
        display_success("Logged out successfully!")
    
    def list_services(self, detailed: bool = False, service_type: Optional[str] = None) -> None:
        """Handle list services command"""
        with console.status("Getting services..."):
            services = self.render_service.api.list_services()
        
        if not services:
            display_warning("No services found")
            return
        
        # Filter by type if specified
        if service_type:
            services = [s for s in services if s.type.lower() == service_type.lower()]
            if not services:
                display_warning(f"No services found with type '{service_type}'")
                return
        
        table = create_services_table(services, detailed)
        console.print(table)
    
    def deploy_service(self, service_name: str, clear_cache: bool = False, yes: bool = False) -> None:
        """Handle deploy command"""
        service = self._find_service(service_name)
        if not service:
            return
        
        action = "Deploying with cache clear" if clear_cache else "Deploying"
        console.print(f"🚀 {action}: {service.name}", style="cyan")
        
        if not yes and not confirm_action("Continue?"):
            display_warning("Cancelled")
            return
        
        try:
            deploy = self.render_service.api.trigger_deploy(service.id, clear_cache)
            display_success(f"Deploy started! ID: {deploy.id}")
            display_info(f"Watch progress: https://dashboard.render.com/web/{service.id}")
        except APIError as e:
            display_error(f"Deploy failed: {e.message}")
    
    def show_service_info(self, service_name: str) -> None:
        """Handle service info command"""
        service = self._find_service(service_name)
        if not service:
            return
        
        with console.status("Getting service details..."):
            overview = self.render_service.get_service_overview(service.id)
        
        # Display basic info
        info_panel = create_service_info_panel(service)
        console.print(info_panel)
        
        # Display recent deployments
        if overview['recent_deploys']:
            table = create_deploys_table(overview['recent_deploys'], service.name)
            console.print(table)
    
    def list_deployments(self, service_name: str, limit: int = 10) -> None:
        """Handle list deployments command"""
        service = self._find_service(service_name)
        if not service:
            return
        
        with console.status("Getting deployments..."):
            deploys = self.render_service.api.list_deploys(service.id)[:limit]
        
        if not deploys:
            display_warning(f"No deployments found for {service.name}")
            return
        
        table = create_deploys_table(deploys, service.name)
        console.print(table)
    
    def scale_service(self, service_name: str, instances: int) -> None:
        """Handle scale command"""
        service = self._find_service(service_name)
        if not service:
            return
        
        if not confirm_action(f"Scale {service.name} to {instances} instances?"):
            display_warning("Cancelled")
            return
        
        success = self.render_service.scale_service(service.id, instances)
        if not success:
            raise SystemExit(1)
    
    def suspend_service(self, service_name: str) -> None:
        """Handle suspend command"""
        service = self._find_service(service_name)
        if not service:
            return
        
        if not confirm_action(f"Suspend service {service.name}?"):
            display_warning("Cancelled")
            return
        
        try:
            self.render_service.api.suspend_service(service.id)
            display_success(f"Service {service.name} suspended")
        except APIError as e:
            display_error(f"Failed to suspend service: {e.message}")
    
    def resume_service(self, service_name: str) -> None:
        """Handle resume command"""
        service = self._find_service(service_name)
        if not service:
            return
        
        try:
            self.render_service.api.resume_service(service.id)
            display_success(f"Service {service.name} resumed")
        except APIError as e:
            display_error(f"Failed to resume service: {e.message}")
    
    def restart_service(self, service_name: str) -> None:
        """Handle restart command"""
        service = self._find_service(service_name)
        if not service:
            return
        
        if not confirm_action(f"Restart service {service.name}?"):
            display_warning("Cancelled")
            return
        
        try:
            self.render_service.api.restart_service(service.id)
            display_success(f"Service {service.name} restarted")
        except APIError as e:
            display_error(f"Failed to restart service: {e.message}")
    
    def _find_service(self, name_or_id: str) -> Optional[Service]:
        """Find service by name or ID"""
        try:
            services = self.render_service.api.list_services()
            service = next((s for s in services if s.name == name_or_id or s.id == name_or_id), None)
            
            if not service:
                handle_service_not_found(name_or_id)
                return None
            
            return service
        except APIError as e:
            display_error(f"Failed to fetch services: {e.message}")
            return None