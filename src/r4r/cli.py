#!/usr/bin/env python3
"""
r4r CLI - Professional CLI with domain-based subcommands
Following domain-driven design principles
"""

import typer
from typing import Optional

from .commands import RenderCLI

# Main application
app = typer.Typer(
    name="r4r",
    help="🚀 Render Command Line Interface",
    add_completion=True,
)

# Initialize the command handler
cli_handler = RenderCLI()

# Domain-specific sub-applications
auth_app = typer.Typer(help="🔐 Authentication management")
services_app = typer.Typer(help="🚀 Services management")
deployments_app = typer.Typer(help="📦 Deployments management") 
jobs_app = typer.Typer(help="⚙️  Jobs management")
logs_app = typer.Typer(help="📋 Logs and monitoring")
projects_app = typer.Typer(help="📁 Projects management")

# Add sub-applications to main app
app.add_typer(auth_app, name="auth")
app.add_typer(services_app, name="services") 
app.add_typer(deployments_app, name="deployments")
app.add_typer(jobs_app, name="jobs")
app.add_typer(logs_app, name="logs")
app.add_typer(projects_app, name="projects")

# =============================================================================
# AUTHENTICATION DOMAIN
# =============================================================================

@auth_app.command("login")
def auth_login(api_key: str = typer.Option(None, "--key", "-k", help="Your Render API key")):
    """Login to Render"""
    cli_handler.login(api_key)

@auth_app.command("logout")
def auth_logout():
    """Logout and remove stored credentials"""
    cli_handler.logout()

@auth_app.command("whoami")
def auth_whoami():
    """Show current user info"""
    cli_handler.whoami()

# =============================================================================
# SERVICES DOMAIN  
# =============================================================================

@services_app.command("list")
def services_list(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
    service_type: Optional[str] = typer.Option(None, "--type", help="Filter by service type"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (active, suspended, unknown)")
):
    """List all your services"""
    cli_handler.list_services(detailed, service_type, status)

@services_app.command("info")
def services_info(service: str = typer.Argument(..., help="Service name or ID")):
    """Show detailed service information"""
    cli_handler.show_service_info(service)

@services_app.command("deploy")
def services_deploy(
    service: str = typer.Argument(..., help="Service name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Deploy a service"""
    cli_handler.deploy_service(service, clear_cache=False, yes=yes)

@services_app.command("rebuild")
def services_rebuild(
    service: str = typer.Argument(..., help="Service name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Rebuild service with cache clear"""
    cli_handler.deploy_service(service, clear_cache=True, yes=yes)

@services_app.command("scale")
def services_scale(
    service: str = typer.Argument(..., help="Service name or ID"),
    instances: int = typer.Argument(..., help="Number of instances"),
):
    """Scale a service"""
    cli_handler.scale_service(service, instances)

@services_app.command("suspend")
def services_suspend(service: str = typer.Argument(..., help="Service name or ID")):
    """Suspend a service"""
    cli_handler.suspend_service(service)

@services_app.command("resume")
def services_resume(service: str = typer.Argument(..., help="Service name or ID")):
    """Resume a service"""
    cli_handler.resume_service(service)

@services_app.command("restart")
def services_restart(service: str = typer.Argument(..., help="Service name or ID")):
    """Restart a service"""
    cli_handler.restart_service(service)

# =============================================================================
# DEPLOYMENTS DOMAIN
# =============================================================================

@deployments_app.command("list")
def deployments_list(
    service: str = typer.Argument(..., help="Service name or ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of deployments to show"),
):
    """List deployments for a service"""
    cli_handler.list_deployments(service, limit)

# =============================================================================
# JOBS DOMAIN
# =============================================================================

@jobs_app.command("create")
def jobs_create(
    service: str = typer.Argument(..., help="Service name or ID"),
    command: str = typer.Argument(..., help="Command to run"),
    wait: bool = typer.Option(False, "--wait", "-w", help="Wait for job to complete"),
):
    """Create a one-off job"""
    cli_handler.create_job(service, command, wait)

@jobs_app.command("list")
def jobs_list(
    service: str = typer.Argument(..., help="Service name or ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of jobs to show"),
):
    """List jobs for a service"""
    cli_handler.list_jobs(service, limit)

@jobs_app.command("status")
def jobs_status(job_id: str = typer.Argument(..., help="Job ID")):
    """Get job status"""
    cli_handler.get_job_status(job_id)

# =============================================================================
# LOGS/MONITORING DOMAIN
# =============================================================================

@logs_app.command("view")
def logs_view(
    service: str = typer.Argument(..., help="Service name or ID"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of log lines to show"),
):
    """View service logs"""
    cli_handler.view_logs(service, lines, False)

@logs_app.command("stream")
def logs_stream(
    service: str = typer.Argument(..., help="Service name or ID"),
    lines: int = typer.Option(100, "--lines", "-n", help="Number of log lines to show"),
):
    """Stream real-time logs"""
    cli_handler.view_logs(service, lines, True)

@logs_app.command("events")
def logs_events(
    service: str = typer.Argument(..., help="Service name or ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of events to show"),
):
    """Show service events"""
    cli_handler.view_service_events(service, limit)

@logs_app.command("streams")
def logs_streams(
    action: str = typer.Argument(..., help="Action: list, create"),
    stream_id: Optional[str] = typer.Option(None, "--id", help="Stream ID"),
    name: Optional[str] = typer.Option(None, "--name", help="Stream name"),
    service_id: Optional[str] = typer.Option(None, "--service", help="Service ID"),
    level_filter: Optional[str] = typer.Option(None, "--level", help="Log level filter"),
    enabled: bool = typer.Option(True, "--enabled/--disabled", help="Enable or disable stream"),
):
    """Manage log streams"""
    cli_handler.manage_log_streams(action, stream_id, name, service_id, level_filter, enabled)

# =============================================================================
# PROJECTS DOMAIN
# =============================================================================

@projects_app.command("list")
def projects_list():
    """List all your projects"""
    cli_handler.list_projects()

@projects_app.command("info")
def projects_info(project: str = typer.Argument(..., help="Project name or ID")):
    """Show detailed project information"""
    cli_handler.show_project_info(project)

@projects_app.command("services")
def projects_services(
    project: str = typer.Argument(..., help="Project name or ID"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information")
):
    """List services in a project"""
    cli_handler.list_project_services(project, detailed)

@projects_app.command("environments")
def projects_environments(
    environment_id: str = typer.Argument(..., help="Environment ID"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information")
):
    """List services in an environment"""
    cli_handler.list_environment_services(environment_id, detailed)

# =============================================================================
# BACKWARDS COMPATIBILITY (Legacy commands)
# =============================================================================

@app.command("login", hidden=True)
def legacy_login(api_key: str = typer.Option(None, "--key", "-k", help="Your Render API key")):
    """[DEPRECATED] Use 'r4r auth login' instead"""
    cli_handler.login(api_key)

@app.command("list", hidden=True)
def legacy_list(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed information"),
    service_type: Optional[str] = typer.Option(None, "--type", help="Filter by service type"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status")
):
    """[DEPRECATED] Use 'r4r services list' instead"""
    cli_handler.list_services(detailed, service_type, status)

# =============================================================================
# MAIN CALLBACK
# =============================================================================

@app.callback()
def main():
    """
    🚀 r4r - Professional Render CLI
    
    A domain-organized command-line interface for managing your Render services.
    
    Examples:
      r4r auth login                    # Authenticate
      r4r services list                 # List all services  
      r4r services deploy my-service    # Deploy a service
      r4r projects list                 # List projects
      r4r logs view my-service          # View logs
    """
    pass


def cli_main():
    """Entry point for the CLI application"""
    app()


if __name__ == "__main__":
    cli_main()
