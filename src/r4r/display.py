#!/usr/bin/env python3
"""
r4r CLI Display Utilities
Simple display utilities for CLI output
"""

from datetime import datetime
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from .api import Deploy, Service
from .config import format_timestamp, truncate_string

console = Console()


def create_services_table(services: List[Service], detailed: bool = False) -> Table:
    """Create a formatted table for services"""
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
        status_display = f"{service.status_icon} {service.status.title()}"
        service_type_display = service.type.replace("_", " ").title()

        # Extract URL
        url = service.url or "N/A"
        if not url or url == "N/A":
            if service.slug:
                url = f"https://{service.slug}.onrender.com"
            elif service.repo_url:
                # Try to construct URL from service name
                url = f"https://{service.name.lower().replace('_', '-')}.onrender.com"

        row_data = [service.name, service_type_display, status_display]

        if detailed:
            region = service.region or "N/A"
            plan = service.plan or "N/A"
            created = service.created_at[:10] if service.created_at else "N/A"
            row_data.extend([region, plan, created])

        row_data.append(url)
        table.add_row(*row_data)

    return table


def create_deploys_table(deploys: List[Deploy], service_name: str) -> Table:
    """Create a formatted table for deployments"""
    table = Table(title=f"🚀 Deployments for {service_name} (Last {len(deploys)})")
    table.add_column("ID", style="cyan", width=18)
    table.add_column("Status", style="green", width=12)
    table.add_column("Started", style="blue", width=20)
    table.add_column("Duration", style="yellow", width=12)
    table.add_column("Commit", style="magenta", width=10)
    table.add_column("Message", style="dim", overflow="fold")

    for deploy in deploys:
        status_display = f"{deploy.status_icon} {deploy.status.title()}"
        started = format_timestamp(deploy.created_at)
        commit_id = deploy.commit_id[:8] if deploy.commit_id else "N/A"
        commit_msg = truncate_string(deploy.commit_message or "N/A", 40)

        table.add_row(
            deploy.id[:16],
            status_display,
            started,
            deploy.duration,
            commit_id,
            commit_msg,
        )

    return table


def create_service_info_panel(service: Service) -> Panel:
    """Create a formatted panel for service information"""
    info = f"""
📛 **Name:** {service.name}
🆔 **ID:** {service.id}
🔧 **Type:** {service.type.replace("_", " ").title()}
📅 **Created:** {service.formatted_created_at}
🔄 **Auto Deploy:** {"✅" if service.auto_deploy else "❌"}
"""

    if service.branch:
        info += f"🌿 **Branch:** {service.branch}\n"

    if service.repo_url:
        info += f"📚 **Repository:** {service.repo_url}\n"

    if service.region:
        info += f"📍 **Region:** {service.region}\n"

    if service.plan:
        info += f"💰 **Plan:** {service.plan}\n"

    if service.url:
        info += f"🌐 **URL:** {service.url}\n"

    return Panel(info, title="📋 Service Information", expand=False)


def confirm_action(message: str, default: bool = False) -> bool:
    """Standardized confirmation prompt"""
    return Confirm.ask(message, default=default)


def display_error(message: str) -> None:
    """Standardized error display"""
    console.print(f"❌ {message}", style="red")


def display_success(message: str) -> None:
    """Standardized success display"""
    console.print(f"✅ {message}", style="green")


def display_warning(message: str) -> None:
    """Standardized warning display"""
    console.print(f"⚠️ {message}", style="yellow")


def display_info(message: str) -> None:
    """Standardized info display"""
    console.print(f"💡 {message}", style="dim")


def handle_service_not_found(service_name: str) -> None:
    """Standardized service not found handling"""
    display_error(f"Service '{service_name}' not found")
    display_info("Run 'r4r list' to see available services")


def format_log_level(level: str) -> str:
    """Format log level with colors"""
    level_colors = {
        "error": "red",
        "warn": "yellow",
        "warning": "yellow",
        "info": "green",
        "debug": "blue",
        "fatal": "bright_red",
    }
    color = level_colors.get(level.lower(), "white")
    return f"[{color}]{level.upper():5}[/{color}]"


def format_log_entry(timestamp: str, level: str, message: str, source: str = "") -> str:
    """Format a log entry for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        time_str = dt.strftime("%H:%M:%S")
    except (ValueError, TypeError):
        time_str = timestamp[:8]

    level_badge = format_log_level(level)
    source_info = f"[dim]{truncate_string(source, 10)}[/dim]" if source else ""

    return f"[dim]{time_str}[/dim] {level_badge} {source_info} {message.strip()}"
