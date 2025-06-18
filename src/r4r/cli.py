#!/usr/bin/env python3
"""
r4r - Render for Render CLI
Super easy Render management with cache clearing and rebuilds
"""

import os
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path
import requests
import time
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
import typer
from typer import Option, Argument
import yaml

app = typer.Typer(
    name="r4r",
    help="🚀 r4r - Super easy Render CLI with cache clearing",
    add_completion=True
)
console = Console()

CONFIG_DIR = Path.home() / ".r4r"
CONFIG_FILE = CONFIG_DIR / "config.yml"
API_BASE_URL = "https://api.render.com/v1"


class RenderAPI:
    """Simple Render API client"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("RENDER_API_KEY") or self._load_api_key()
        if not self.api_key:
            console.print("❌ No API key found. Run 'r4r login' first.", style="red")
            console.print("💡 Get your API key from: https://dashboard.render.com/u/settings#api-keys", style="dim")
            raise typer.Exit(1)
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _load_api_key(self) -> Optional[str]:
        """Load API key from config file"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('api_key')
        return None
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response with error checking"""
        try:
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get('message', str(e))
            except:
                error_msg = str(e)
                
            if response.status_code == 429:
                console.print("⚠️  Rate limit exceeded. Please wait and try again.", style="yellow")
            elif response.status_code == 401:
                console.print("❌ Invalid API key. Run 'r4r login' to authenticate.", style="red")
                console.print("💡 Get your API key from: https://dashboard.render.com/u/settings#api-keys", style="dim")
            elif response.status_code == 403:
                console.print("❌ Access denied. Check your API key permissions.", style="red")
            elif response.status_code == 404:
                console.print("❌ Resource not found.", style="red")
            elif response.status_code >= 500:
                console.print(f"❌ Server error ({response.status_code}). Please try again later.", style="red")
            else:
                console.print(f"❌ Error ({response.status_code}): {error_msg}", style="red")
            raise typer.Exit(1)
        except requests.exceptions.ConnectionError:
            console.print("❌ Connection error. Check your internet connection.", style="red")
            raise typer.Exit(1)
        except requests.exceptions.Timeout:
            console.print("❌ Request timeout. Please try again.", style="red")
            raise typer.Exit(1)
        except requests.exceptions.RequestException as e:
            console.print(f"❌ Request failed: {e}", style="red")
            raise typer.Exit(1)
    
    def list_services(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all services"""
        params = {'limit': limit}
        response = self.session.get(f"{API_BASE_URL}/services", params=params)
        data = self._handle_response(response)
        return data if isinstance(data, list) else []
    
    def find_service(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Find service by name or ID"""
        services = self.list_services()
        return next((s for s in services if s['name'] == name_or_id or s['id'] == name_or_id), None)
    
    def deploy_service(self, service_id: str, clear_cache: bool = False) -> Dict[str, Any]:
        """Deploy a service with optional cache clearing"""
        payload = {"clearCache": clear_cache}
        
        response = self.session.post(
            f"{API_BASE_URL}/services/{service_id}/deploys",
            json=payload
        )
        return self._handle_response(response)
    
    def get_service_details(self, service_id: str) -> Dict[str, Any]:
        """Get detailed service information"""
        response = self.session.get(f"{API_BASE_URL}/services/{service_id}")
        return self._handle_response(response)
    
    def get_service_deployments(self, service_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get service deployment history"""
        params = {'limit': limit}
        response = self.session.get(f"{API_BASE_URL}/services/{service_id}/deploys", params=params)
        return self._handle_response(response)
    
    def create_job(self, service_id: str, command: str, plan_id: str = None) -> Dict[str, Any]:
        """Create a one-off job"""
        payload = {
            "serviceId": service_id,
            "startCommand": command
        }
        if plan_id:
            payload["planId"] = plan_id
            
        response = self.session.post(f"{API_BASE_URL}/jobs", json=payload)
        return self._handle_response(response)
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status"""
        response = self.session.get(f"{API_BASE_URL}/jobs/{job_id}")
        return self._handle_response(response)
    
    def list_jobs(self, service_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List jobs for a service"""
        params = {'limit': limit}
        response = self.session.get(f"{API_BASE_URL}/services/{service_id}/jobs", params=params)
        return self._handle_response(response)
    
    def get_api_key_info(self) -> Dict[str, Any]:
        """Get information about the current API key"""
        response = self.session.get(f"{API_BASE_URL}/owners/me")
        return self._handle_response(response)
    
    def get_service_logs(self, service_id: str, lines: int = 100, follow: bool = False) -> Dict[str, Any]:
        """Get service logs"""
        params = {'lines': lines}
        if follow:
            params['follow'] = 'true'
        response = self.session.get(f"{API_BASE_URL}/services/{service_id}/logs", params=params)
        return self._handle_response(response)
    
    def get_deploy_logs(self, service_id: str, deploy_id: str) -> Dict[str, Any]:
        """Get deployment logs"""
        response = self.session.get(f"{API_BASE_URL}/services/{service_id}/deploys/{deploy_id}/logs")
        return self._handle_response(response)


@app.command("login")
def login(api_key: str = Option(None, "--key", "-k", help="Your Render API key")):
    """Login to Render"""
    if not api_key:
        console.print("🔑 Get your API key from: https://dashboard.render.com/u/settings#api-keys")
        api_key = typer.prompt("Paste your API key", hide_input=True)
    
    try:
        test_api = RenderAPI(api_key)
        services = test_api.list_services()
        owner_info = test_api.get_api_key_info()
        
        CONFIG_DIR.mkdir(exist_ok=True)
        config = {
            'api_key': api_key,
            'owner': owner_info.get('name', 'Unknown'),
            'email': owner_info.get('email', 'Unknown'),
            'login_time': datetime.now().isoformat()
        }
        
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f)
        
        console.print(f"✅ Logged in as {owner_info.get('name', 'Unknown')}! Found {len(services)} services.", style="green")
    except Exception as e:
        console.print(f"❌ Login failed: {e}", style="red")
        raise typer.Exit(1)


@app.command("whoami")
def whoami():
    """Show current user info and API key details"""
    if not CONFIG_FILE.exists():
        console.print("❌ Not logged in. Run 'r4r login' first.", style="red")
        raise typer.Exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)
    
    try:
        api = RenderAPI()
        owner_info = api.get_api_key_info()
        services = api.list_services()
        
        panel_content = f"""
👤 **User:** {owner_info.get('name', 'Unknown')}
📧 **Email:** {owner_info.get('email', 'Unknown')}
🔑 **API Key:** {config.get('api_key', 'Unknown')[:8]}...
📅 **Login Time:** {config.get('login_time', 'Unknown')}
🚀 **Services:** {len(services)} total
        """
        
        console.print(Panel(panel_content, title="🔐 Current Session", expand=False))
        
    except Exception as e:
        console.print(f"❌ Failed to get user info: {e}", style="red")
        raise typer.Exit(1)


@app.command("logout")
def logout():
    """Logout and remove stored credentials"""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        console.print("✅ Logged out successfully!", style="green")
    else:
        console.print("❌ Not logged in.", style="yellow")


@app.command("list")
def list_services(
    detailed: bool = Option(False, "--detailed", "-d", help="Show detailed information"),
    service_type: str = Option(None, "--type", "-t", help="Filter by service type")
):
    """List all your services"""
    api = RenderAPI()
    
    with console.status("Getting services..."):
        services = api.list_services()
    
    if not services:
        console.print("No services found", style="yellow")
        return
    
    # Filter by type if specified
    if service_type:
        services = [s for s in services if s.get('type', '').lower() == service_type.lower()]
        if not services:
            console.print(f"No services found with type '{service_type}'", style="yellow")
            return
    
    table = Table(title=f"Your Render Services ({len(services)})")
    table.add_column("Name", style="cyan", no_wrap=True, width=20)
    table.add_column("Type", style="magenta", width=12)
    table.add_column("Status", style="green", width=12)
    
    if detailed:
        table.add_column("Region", style="yellow", width=10)
        table.add_column("Plan", style="blue", width=10)
        table.add_column("Created", style="dim", width=12)
    
    table.add_column("URL", style="blue", overflow="fold")
    
    for service in services:
        suspended = service.get('suspended', 'unknown')
        status = "🟢 Live" if suspended == "not_suspended" else "🔴 Suspended" if suspended == "suspended" else "❓ Unknown"
        
        # Try different URL sources
        url = 'N/A'
        if service.get('serviceDetails', {}).get('url'):
            url = service['serviceDetails']['url']
        elif service.get('slug'):
            url = f"https://{service['slug']}.onrender.com"
        
        service_type_display = service.get('type', 'unknown').replace('_', ' ').title()
        
        row_data = [service['name'], service_type_display, status]
        
        if detailed:
            region = service.get('serviceDetails', {}).get('region', 'N/A')
            plan = service.get('serviceDetails', {}).get('plan', 'N/A')
            created = service.get('createdAt', '')[:10] if service.get('createdAt') else 'N/A'
            row_data.extend([region, plan, created])
        
        row_data.append(url)
        table.add_row(*row_data)
    
    console.print(table)


@app.command("deploy")
def deploy(
    service: str = Argument(..., help="Service name"),
    clear: bool = Option(False, "--clear", "-c", help="Clear cache and rebuild"),
    yes: bool = Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Deploy a service"""
    api = RenderAPI()
    
    svc = api.find_service(service)
    if not svc:
        console.print(f"❌ Service '{service}' not found", style="red")
        console.print("💡 Run 'r4r list' to see available services", style="dim")
        raise typer.Exit(1)
    
    action = "Deploying with cache clear" if clear else "Deploying"
    console.print(f"🚀 {action}: {svc['name']}", style="cyan")
    
    if not yes:
        if not Confirm.ask("Continue?"):
            console.print("Cancelled", style="yellow")
            return
    
    try:
        deploy_result = api.deploy_service(svc['id'], clear_cache=clear)
        console.print(f"✅ Deploy started! ID: {deploy_result['id']}", style="green")
        console.print(f"🔗 Watch progress: https://dashboard.render.com/web/{svc['id']}", style="dim")
    except Exception as e:
        console.print(f"❌ Deploy failed: {e}", style="red")
        raise typer.Exit(1)


@app.command("rebuild")
def rebuild(
    service: str = Argument(..., help="Service name"),
    yes: bool = Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Rebuild service (clear cache + deploy)"""
    deploy(service, clear=True, yes=yes)


@app.command("info")
def service_info(service: str = Argument(..., help="Service name or ID")):
    """Show detailed service information"""
    api = RenderAPI()
    
    svc = api.find_service(service)
    if not svc:
        console.print(f"❌ Service '{service}' not found", style="red")
        raise typer.Exit(1)
    
    with console.status("Getting service details..."):
        details = api.get_service_details(svc['id'])
        deployments = api.get_service_deployments(svc['id'], limit=5)
    
    # Basic info panel
    basic_info = f"""
📛 **Name:** {details['name']}
🆔 **ID:** {details['id']} 
🔧 **Type:** {details['type'].replace('_', ' ').title()}
📍 **Region:** {details.get('serviceDetails', {}).get('region', 'N/A')}
💰 **Plan:** {details.get('serviceDetails', {}).get('plan', 'N/A')}
🌐 **URL:** {details.get('serviceDetails', {}).get('url', 'N/A')}
📅 **Created:** {details.get('createdAt', 'N/A')[:19] if details.get('createdAt') else 'N/A'}
    """
    
    console.print(Panel(basic_info, title="📋 Service Information", expand=False))
    
    # Recent deployments
    if deployments:
        table = Table(title="🚀 Recent Deployments (Last 5)")
        table.add_column("Status", style="green", width=12)
        table.add_column("Started", style="blue", width=20)
        table.add_column("Duration", style="yellow", width=12)
        table.add_column("Commit", style="cyan", width=12)
        
        for deploy in deployments[:5]:
            status = deploy.get('status', 'unknown')
            status_icon = {
                'live': '🟢 Live',
                'build_in_progress': '🟡 Building',
                'update_in_progress': '🟡 Updating', 
                'build_failed': '🔴 Failed',
                'canceled': '⚪ Canceled'
            }.get(status, f'❓ {status}')
            
            started = deploy.get('createdAt', '')[:19].replace('T', ' ') if deploy.get('createdAt') else 'N/A'
            
            # Calculate duration if finished
            duration = 'N/A'
            if deploy.get('finishedAt') and deploy.get('createdAt'):
                start = datetime.fromisoformat(deploy['createdAt'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(deploy['finishedAt'].replace('Z', '+00:00'))
                duration = str(end - start).split('.')[0]
            
            commit = deploy.get('commit', {}).get('id', 'N/A')[:8] if deploy.get('commit') else 'N/A'
            
            table.add_row(status_icon, started, duration, commit)
        
        console.print(table)


@app.command("logs")
def view_logs(
    service: str = Argument(..., help="Service name or ID"),
    lines: int = Option(100, "--lines", "-n", help="Number of log lines to show"),
    follow: bool = Option(False, "--follow", "-f", help="Follow log output")
):
    """View service logs"""
    api = RenderAPI()
    
    svc = api.find_service(service)
    if not svc:
        console.print(f"❌ Service '{service}' not found", style="red")
        raise typer.Exit(1)
    
    try:
        console.print(f"📜 Fetching logs for {svc['name']}...", style="cyan")
        
        if follow:
            console.print("🔄 Following logs (Ctrl+C to stop)...", style="yellow")
            # For follow mode, we would need WebSocket or polling
            # For now, just show recent logs
            logs_data = api.get_service_logs(svc['id'], lines)
        else:
            logs_data = api.get_service_logs(svc['id'], lines)
        
        # Display logs
        if 'logs' in logs_data and logs_data['logs']:
            console.print(f"\n📄 Recent logs ({len(logs_data['logs'])} entries):", style="green")
            console.print("-" * 80)
            
            for log_entry in logs_data['logs']:
                timestamp = log_entry.get('timestamp', '')
                message = log_entry.get('message', '')
                level = log_entry.get('level', 'INFO')
                
                # Color code by log level
                level_colors = {
                    'ERROR': 'red',
                    'WARN': 'yellow', 
                    'WARNING': 'yellow',
                    'INFO': 'green',
                    'DEBUG': 'dim'
                }
                level_color = level_colors.get(level.upper(), 'white')
                
                console.print(f"[{timestamp}] [{level}] {message}", style=level_color)
        else:
            console.print("⚠️  No logs found or logs not available", style="yellow")
            
    except Exception as e:
        console.print(f"❌ Failed to fetch logs: {e}", style="red")
        raise typer.Exit(1)


@app.command("deploys")
def list_deployments(
    service: str = Argument(..., help="Service name or ID"),
    limit: int = Option(10, "--limit", "-l", help="Number of deployments to show")
):
    """List recent deployments for a service"""
    api = RenderAPI()
    
    svc = api.find_service(service)
    if not svc:
        console.print(f"❌ Service '{service}' not found", style="red")
        raise typer.Exit(1)
    
    with console.status("Getting deployments..."):
        deployments = api.get_service_deployments(svc['id'], limit)
    
    if not deployments:
        console.print(f"No deployments found for {svc['name']}", style="yellow")
        return
    
    table = Table(title=f"🚀 Deployments for {svc['name']} (Last {len(deployments)})")
    table.add_column("ID", style="cyan", width=18)
    table.add_column("Status", style="green", width=12)
    table.add_column("Started", style="blue", width=20) 
    table.add_column("Duration", style="yellow", width=12)
    table.add_column("Commit", style="magenta", width=10)
    table.add_column("Message", style="dim", overflow="fold")
    
    for deploy in deployments:
        status = deploy.get('status', 'unknown')
        status_icon = {
            'live': '🟢 Live',
            'build_in_progress': '🟡 Building',
            'update_in_progress': '🟡 Updating',
            'build_failed': '🔴 Failed',
            'canceled': '⚪ Canceled'
        }.get(status, f'❓ {status}')
        
        started = deploy.get('createdAt', '')[:19].replace('T', ' ') if deploy.get('createdAt') else 'N/A'
        
        # Calculate duration
        duration = 'N/A'
        if deploy.get('finishedAt') and deploy.get('createdAt'):
            start = datetime.fromisoformat(deploy['createdAt'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(deploy['finishedAt'].replace('Z', '+00:00'))
            duration = str(end - start).split('.')[0]
        
        commit_info = deploy.get('commit', {})
        commit_id = commit_info.get('id', 'N/A')[:8] if commit_info.get('id') else 'N/A'
        commit_msg = commit_info.get('message', 'N/A')
        if len(commit_msg) > 40:
            commit_msg = commit_msg[:37] + '...'
            
        table.add_row(
            deploy.get('id', 'N/A')[:16],
            status_icon,
            started,
            duration,
            commit_id,
            commit_msg
        )
    
    console.print(table)


@app.command("job")
def create_job(
    service: str = Argument(..., help="Service name or ID"),
    command: str = Argument(..., help="Command to run"),
    plan: str = Option(None, "--plan", "-p", help="Plan ID for the job"),
    wait: bool = Option(False, "--wait", "-w", help="Wait for job to complete")
):
    """Create and run a one-off job"""
    api = RenderAPI()
    
    svc = api.find_service(service)
    if not svc:
        console.print(f"❌ Service '{service}' not found", style="red")
        raise typer.Exit(1)
    
    console.print(f"🔄 Creating job for {svc['name']}: {command}")
    
    try:
        job = api.create_job(svc['id'], command, plan)
        job_id = job['id']
        
        console.print(f"✅ Job created! ID: {job_id}", style="green")
        
        if wait:
            console.print("⏳ Waiting for job to complete...", style="yellow")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running job...", total=None)
                
                while True:
                    time.sleep(2)
                    status = api.get_job_status(job_id)
                    
                    if status.get('status') in ['succeeded', 'failed', 'canceled']:
                        break
                    
                    progress.update(task, description=f"Status: {status.get('status', 'running')}")
            
            final_status = api.get_job_status(job_id)
            status_icon = {
                'succeeded': '✅ Succeeded',
                'failed': '❌ Failed', 
                'canceled': '⚪ Canceled'
            }.get(final_status.get('status'), f"❓ {final_status.get('status')}")
            
            console.print(f"Job completed: {status_icon}", style="green" if final_status.get('status') == 'succeeded' else "red")
            
    except Exception as e:
        console.print(f"❌ Failed to create job: {e}", style="red")
        raise typer.Exit(1)


@app.command("jobs")
def list_jobs(
    service: str = Argument(..., help="Service name or ID"),
    limit: int = Option(10, "--limit", "-l", help="Number of jobs to show")
):
    """List recent jobs for a service"""
    api = RenderAPI()
    
    svc = api.find_service(service)
    if not svc:
        console.print(f"❌ Service '{service}' not found", style="red")
        raise typer.Exit(1)
    
    with console.status("Getting jobs..."):
        jobs = api.list_jobs(svc['id'], limit)
    
    if not jobs:
        console.print(f"No jobs found for {svc['name']}", style="yellow")
        return
    
    table = Table(title=f"🔧 Jobs for {svc['name']} (Last {len(jobs)})")
    table.add_column("ID", style="cyan", width=20)
    table.add_column("Command", style="blue", width=30)
    table.add_column("Status", style="green", width=12)
    table.add_column("Started", style="yellow", width=20)
    table.add_column("Duration", style="magenta", width=12)
    
    for job in jobs:
        status = job.get('status', 'unknown')
        status_icon = {
            'succeeded': '✅ Success',
            'failed': '❌ Failed',
            'running': '🟡 Running',
            'canceled': '⚪ Canceled'
        }.get(status, f'❓ {status}')
        
        started = job.get('createdAt', '')[:19].replace('T', ' ') if job.get('createdAt') else 'N/A'
        
        # Calculate duration
        duration = 'N/A'
        if job.get('finishedAt') and job.get('startedAt'):
            start = datetime.fromisoformat(job['startedAt'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(job['finishedAt'].replace('Z', '+00:00'))
            duration = str(end - start).split('.')[0]
        elif job.get('startedAt') and status == 'running':
            start = datetime.fromisoformat(job['startedAt'].replace('Z', '+00:00'))
            duration = str(datetime.now(start.tzinfo) - start).split('.')[0]
        
        command = job.get('startCommand', 'N/A')
        if len(command) > 25:
            command = command[:22] + '...'
            
        table.add_row(
            job.get('id', 'N/A')[:18],
            command,
            status_icon,
            started,
            duration
        )
    
    console.print(table)


@app.command("status")
def job_status(job_id: str = Argument(..., help="Job ID")):
    """Get status of a specific job"""
    api = RenderAPI()
    
    try:
        job = api.get_job_status(job_id)
        
        status_info = f"""
🆔 **Job ID:** {job.get('id', 'N/A')}
🔧 **Command:** {job.get('startCommand', 'N/A')}
📊 **Status:** {job.get('status', 'unknown')}
📅 **Created:** {job.get('createdAt', 'N/A')[:19].replace('T', ' ') if job.get('createdAt') else 'N/A'}
⏰ **Started:** {job.get('startedAt', 'N/A')[:19].replace('T', ' ') if job.get('startedAt') else 'N/A'}
🏁 **Finished:** {job.get('finishedAt', 'N/A')[:19].replace('T', ' ') if job.get('finishedAt') else 'N/A'}
        """
        
        console.print(Panel(status_info, title="🔧 Job Status", expand=False))
        
    except Exception as e:
        console.print(f"❌ Failed to get job status: {e}", style="red")
        raise typer.Exit(1)


@app.callback()
def main():
    """r4r - Super easy Render CLI with advanced features"""
    pass


def cli_main():
    """Entry point for CLI"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n👋 Bye!", style="yellow")
        sys.exit(0)
    except typer.Exit as e:
        # Handle typer exits gracefully
        sys.exit(e.exit_code)
    except requests.exceptions.RequestException as e:
        console.print(f"❌ Network error: {e}", style="red")
        console.print("Please check your internet connection and try again.", style="dim")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        console.print("Please report this issue at: https://github.com/your-username/r4r/issues", style="dim")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()