#!/usr/bin/env python3
"""
r4r CLI Commands
Clean command implementations following KISS and DRY principles
"""

import asyncio
from datetime import datetime
from typing import Optional, Union, Sequence

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .api import RenderService, Service, Project
from .config import APIError, Config, ConfigManager
from .display import (
    confirm_action,
    display_error,
    display_info,
    display_success,
    display_warning,
    handle_service_not_found,
)

console = Console()


def _create_table(
    title: str, columns: Sequence[Union[tuple[str, str], tuple[str, str, int]]]
) -> Table:
    """Create a standardized table"""
    table = Table(title=title)
    for column_data in columns:
        if len(column_data) == 3:
            name, style, width = column_data
            table.add_column(name, style=style, width=width)
        else:
            name, style = column_data
            table.add_column(name, style=style)
    return table


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
                display_info(
                    "Get your API key from: https://dashboard.render.com/u/settings#api-keys"
                )
                raise SystemExit(1)

            config = Config(api_key=api_key)
            self._render_service = RenderService(config)

        return self._render_service

    def login(self, api_key: Optional[str] = None) -> None:
        """Handle login command"""
        if not api_key:
            console.print(
                "🔑 Get your API key from: https://dashboard.render.com/u/settings#api-keys"
            )
            api_key = console.input("Paste your API key: ", password=True)

        try:
            # Test the API key
            config = Config(api_key=api_key)
            test_service = RenderService(config)
            services = test_service.api.list_services()

            # Save config
            config_data = {"api_key": api_key, "login_time": datetime.now().isoformat()}
            self.config_manager.save_config(config_data)

            display_success(f"Logged in successfully! Found {len(services)} services.")

        except APIError as e:
            display_error(f"Login failed: {e.message}")
            raise SystemExit(1)

    def logout(self) -> None:
        """Handle logout command"""
        self.config_manager.clear_config()
        display_success("Logged out successfully!")

    def whoami(self) -> None:
        """Show current user info"""
        config = self.config_manager.load_config()
        if not config.get("api_key"):
            display_error("Not logged in. Run 'r4r login' first.")
            raise SystemExit(1)

        try:
            services = self.render_service.api.list_services()

            panel_content = f"""
🔑 **API Key:** {config.get("api_key", "Unknown")[:8]}...
📅 **Login Time:** {config.get("login_time", "Unknown")}
🚀 **Services:** {len(services)} total
            """
            console.print(
                Panel(panel_content, title="🔐 Current Session", expand=False)
            )
        except APIError as e:
            display_error(f"Failed to get user info: {e.message}")
            raise SystemExit(1)

    def list_services(
        self,
        detailed: bool = False,
        service_type: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> None:
        """Handle list services command"""
        with console.status("Getting all services..."):
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

        # Filter by status if specified
        if status_filter:
            services = [
                s for s in services if s.status.lower() == status_filter.lower()
            ]
            if not services:
                display_warning(f"No services found with status '{status_filter}'")
                return

        # Show available statuses if user wants to see them
        if not status_filter:
            available_statuses = sorted(list(set(s.status for s in services)))
            console.print(
                f"💡 Available statuses: {', '.join(available_statuses)}", style="dim"
            )
            console.print("💡 Use --status <status> to filter by status", style="dim")

        # Create table with proper data
        columns: list[Union[tuple[str, str], tuple[str, str, int]]] = [
            ("Name", "cyan", 20),
            ("Type", "magenta", 12),
            ("Status", "green", 12),
        ]
        if detailed:
            columns.extend(
                [("Region", "yellow", 10), ("Plan", "blue", 10), ("Created", "dim", 12)]
            )
        columns.append(("URL", "blue"))

        table = _create_table(f"Your Render Services ({len(services)})", columns)

        for service in services:
            # Get status display
            status_display = f"{service.status_icon} {service.status.title()}"
            service_type_display = service.type.replace("_", " ").title()

            # Build URL
            url = service.url or "N/A"
            if not url or url == "N/A":
                if service.slug:
                    url = f"https://{service.slug}.onrender.com"
                elif service.name:
                    url = (
                        f"https://{service.name.lower().replace('_', '-')}.onrender.com"
                    )

            row_data = [service.name, service_type_display, status_display]

            if detailed:
                region = service.region or "N/A"
                plan = service.plan or "N/A"
                created = service.created_at[:10] if service.created_at else "N/A"
                row_data.extend([region, plan, created])

            row_data.append(url)
            table.add_row(*row_data)

        console.print(table)

    def deploy_service(
        self, service_name: str, clear_cache: bool = False, yes: bool = False
    ) -> None:
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
            display_info(
                f"Watch progress: https://dashboard.render.com/web/{service.id}"
            )
        except APIError as e:
            display_error(f"Deploy failed: {e.message}")

    def show_service_info(self, service_name: str) -> None:
        """Handle service info command"""
        service = self._find_service(service_name)
        if not service:
            return

        with console.status("Getting service details..."):
            detailed_service = self.render_service.api.get_service_details(service.id)
            deployments = self.render_service.api.list_deploys(service.id, limit=5)

        # Build info panel content
        info = f"""
📛 **Name:** {detailed_service.name}
🆔 **ID:** {detailed_service.id}
🔧 **Type:** {detailed_service.type.replace("_", " ").title()}
📅 **Created:** {detailed_service.formatted_created_at}
🔄 **Auto Deploy:** {"✅" if detailed_service.auto_deploy else "❌"}
        """

        if detailed_service.branch:
            info += f"🌿 **Branch:** {detailed_service.branch}\n"
        if detailed_service.repo_url:
            info += f"📚 **Repository:** {detailed_service.repo_url}\n"
        if detailed_service.region:
            info += f"📍 **Region:** {detailed_service.region}\n"
        if detailed_service.plan:
            info += f"💰 **Plan:** {detailed_service.plan}\n"
        if detailed_service.url:
            info += f"🌐 **URL:** {detailed_service.url}\n"

        console.print(Panel(info, title="📋 Service Information", expand=False))

        # Display recent deployments
        if deployments:
            table = _create_table(
                "🚀 Recent Deployments (Last 5)",
                [
                    ("Status", "green", 12),
                    ("Started", "blue", 20),
                    ("Duration", "yellow", 12),
                    ("Commit", "cyan", 12),
                ],
            )

            for deploy in deployments:
                status_display = f"{deploy.status_icon} {deploy.status.title()}"
                started = (
                    deploy.created_at[:19].replace("T", " ")
                    if deploy.created_at
                    else "N/A"
                )
                commit = deploy.commit_id[:8] if deploy.commit_id else "N/A"

                table.add_row(status_display, started, deploy.duration, commit)

            console.print(table)

    def list_deployments(self, service_name: str, limit: int = 10) -> None:
        """Handle list deployments command"""
        service = self._find_service(service_name)
        if not service:
            return

        with console.status("Getting deployments..."):
            deploys = self.render_service.api.list_deploys(service.id, limit=limit)

        if not deploys:
            display_warning(f"No deployments found for {service.name}")
            return

        table = _create_table(
            f"🚀 Deployments for {service.name} (Last {len(deploys)})",
            [
                ("ID", "cyan", 18),
                ("Status", "green", 12),
                ("Started", "blue", 20),
                ("Duration", "yellow", 12),
                ("Commit", "magenta", 10),
            ],
        )

        for deploy in deploys:
            status_display = f"{deploy.status_icon} {deploy.status.title()}"
            started = (
                deploy.created_at[:19].replace("T", " ") if deploy.created_at else "N/A"
            )
            commit_id = deploy.commit_id[:8] if deploy.commit_id else "N/A"

            table.add_row(
                deploy.id[:16],
                status_display,
                started,
                deploy.duration,
                commit_id,
            )

        console.print(table)

    def create_job(self, service_name: str, command: str, wait: bool = False) -> None:
        """Handle create job command"""
        service = self._find_service(service_name)
        if not service:
            return

        try:
            job = self.render_service.api.create_job(service.id, command)
            display_success(f"Job created! ID: {job.id}")

            if wait:
                self._wait_for_job_completion(job.id)
        except APIError as e:
            display_error(f"Failed to create job: {e.message}")

    def list_jobs(self, service_name: str, limit: int = 10) -> None:
        """Handle list jobs command"""
        service = self._find_service(service_name)
        if not service:
            return

        with console.status("Getting jobs..."):
            jobs = self.render_service.api.list_jobs(service.id, limit=limit)

        if not jobs:
            display_warning(f"No jobs found for {service.name}")
            return

        table = _create_table(
            f"⚙️ Jobs for {service.name} (Last {len(jobs)})",
            [
                ("ID", "cyan", 18),
                ("Command", "green", 30),
                ("Status", "yellow", 12),
                ("Created", "blue", 20),
            ],
        )

        for job in jobs:
            status_display = f"{job.status_icon} {job.status.title()}"
            created = job.created_at[:19].replace("T", " ") if job.created_at else "N/A"
            command_truncated = (
                job.command[:27] + "..." if len(job.command) > 30 else job.command
            )

            table.add_row(
                job.id[:16],
                command_truncated,
                status_display,
                created,
            )

        console.print(table)

    def get_job_status(self, job_id: str) -> None:
        """Handle job status command"""
        try:
            job = self.render_service.api.get_job_status(job_id)

            info = f"""
🆔 **Job ID:** {job.id}
⚙️ **Command:** {job.command}
📊 **Status:** {job.status_icon} {job.status.title()}
📅 **Created:** {job.created_at[:19].replace("T", " ") if job.created_at else "N/A"}
            """

            if job.finished_at:
                info += f"🏁 **Finished:** {job.finished_at[:19].replace('T', ' ')}\n"

            console.print(Panel(info, title="⚙️ Job Status", expand=False))
        except APIError as e:
            display_error(f"Failed to get job status: {e.message}")

    def view_service_events(self, service_name: str, limit: int = 10) -> None:
        """Handle service events command"""
        service = self._find_service(service_name)
        if not service:
            return

        with console.status("Getting events..."):
            events = self.render_service.api.get_service_events(service.id, limit=limit)

        if not events:
            display_warning(f"No events found for {service.name}")
            return

        table = _create_table(
            f"📅 Events for {service.name} (Last {len(events)})",
            [
                ("Type", "cyan", 15),
                ("Description", "green", 40),
                ("Timestamp", "blue", 20),
            ],
        )

        for event in events:
            timestamp = (
                event.timestamp[:19].replace("T", " ") if event.timestamp else "N/A"
            )
            description = (
                event.description[:37] + "..."
                if len(event.description) > 40
                else event.description
            )

            table.add_row(
                event.type.replace("_", " ").title(),
                description,
                timestamp,
            )

        console.print(table)

    def view_logs(
        self, service_name: str, lines: int = 100, stream: bool = False
    ) -> None:
        """Handle logs command"""
        service = self._find_service(service_name)
        if not service:
            return

        try:
            if stream:
                # Use async log streaming
                owner_id = self.render_service.api.get_owner_id()
                if not owner_id:
                    display_warning("Could not get owner ID for log streaming")
                    return

                display_info("Starting log stream... Press Ctrl+C to stop")
                asyncio.run(
                    self.render_service.api.stream_logs_async(
                        service.id, owner_id, lines
                    )
                )
            else:
                # Get static logs
                logs = self.render_service.api.get_service_logs(service.id, lines)
                if logs.get("logs"):
                    for log_line in logs["logs"]:
                        console.print(log_line)
                else:
                    display_warning("No logs found")
        except KeyboardInterrupt:
            display_info("Log streaming stopped")
        except APIError as e:
            display_error(f"Failed to get logs: {e.message}")

    def manage_log_streams(
        self,
        action: str,
        stream_id: Optional[str] = None,
        name: Optional[str] = None,
        service_id: Optional[str] = None,
        level_filter: Optional[str] = None,
        enabled: bool = True,
    ) -> None:
        """Handle log streams management"""
        try:
            if action == "list":
                streams = self.render_service.api.list_log_streams(service_id)
                if not streams:
                    display_warning("No log streams found")
                    return

                table = _create_table(
                    f"📡 Log Streams ({len(streams)})",
                    [
                        ("ID", "cyan", 20),
                        ("Name", "green", 25),
                        ("Service", "blue", 20),
                        ("Filters", "magenta", 30),
                        ("Status", "yellow", 10),
                        ("Created", "dim", 12),
                    ],
                )

                for stream in streams:
                    filters_str = ", ".join(
                        [f"{k}:{v}" for k, v in stream.filters.items()]
                    )
                    status = "✅ Enabled" if stream.enabled else "❌ Disabled"
                    table.add_row(
                        stream.id[:18] + "...",
                        stream.name,
                        stream.service_id[:18] + "...",
                        filters_str[:28] + "..."
                        if len(filters_str) > 28
                        else filters_str,
                        status,
                        stream.created_at[:10],
                    )
                console.print(table)

            elif action == "create":
                if not all([name, service_id]):
                    display_error(
                        "--name and --service are required for creating streams"
                    )
                    return

                filters = {}
                if level_filter:
                    valid_levels = ["debug", "info", "warn", "error", "fatal"]
                    if level_filter.lower() in valid_levels:
                        filters["level"] = level_filter.lower()
                    else:
                        display_warning(f"Invalid log level '{level_filter}'")

                if name is not None and service_id is not None:
                    stream = self.render_service.api.create_log_stream(
                        name=name,
                        service_id=service_id,
                        filters=filters,
                        enabled=enabled,
                    )
                display_success(f"Created log stream: {stream.name} ({stream.id})")

            else:
                display_error(f"Unsupported action: {action}")

        except APIError as e:
            display_error(f"Log stream operation failed: {e.message}")

    def scale_service(self, service_name: str, instances: int) -> None:
        """Handle scale service command"""
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
        """Handle suspend service command"""
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
        """Handle resume service command"""
        service = self._find_service(service_name)
        if not service:
            return

        try:
            self.render_service.api.resume_service(service.id)
            display_success(f"Service {service.name} resumed")
        except APIError as e:
            display_error(f"Failed to resume service: {e.message}")

    def restart_service(self, service_name: str) -> None:
        """Handle restart service command"""
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
            service = self.render_service.api.find_service(name_or_id)

            if not service:
                handle_service_not_found(name_or_id)
                return None

            return service
        except APIError as e:
            display_error(f"Failed to fetch services: {e.message}")
            return None

    def _wait_for_job_completion(self, job_id: str, timeout_minutes: int = 5) -> None:
        """Wait for job to complete"""
        import time

        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Waiting for job to complete...", total=None)

            while time.time() - start_time < timeout_seconds:
                try:
                    job = self.render_service.api.get_job_status(job_id)

                    if job.status in ["succeeded", "failed"]:
                        progress.stop()
                        if job.status == "succeeded":
                            display_success(f"Job {job_id} completed successfully")
                        else:
                            display_error(f"Job {job_id} failed")
                        return

                    time.sleep(5)
                except APIError:
                    time.sleep(5)

            progress.stop()
            display_warning(f"Job timeout after {timeout_minutes} minutes")

    def list_projects(self) -> None:
        """Handle list projects command"""
        with console.status("Getting all projects..."):
            projects = self.render_service.api.list_projects()

        if not projects:
            display_warning("No projects found")
            return

        table = _create_table(
            f"Your Render Projects ({len(projects)})",
            [
                ("Name", "cyan", 25),
                ("Owner", "green", 20),
                ("Type", "magenta", 10),
                ("Environments", "yellow", 12),
                ("Created", "blue", 12),
            ],
        )

        for project in projects:
            owner_display = f"{project.owner.name} ({project.owner.type})"
            env_count = len(project.environment_ids)
            created = project.created_at[:10] if project.created_at else "N/A"

            table.add_row(
                project.name,
                owner_display,
                project.owner.type.title(),
                str(env_count),
                created,
            )

        console.print(table)

    def show_project_info(self, project_name: str) -> None:
        """Handle project info command"""
        project = self._find_project(project_name)
        if not project:
            return

        with console.status("Getting project details..."):
            detailed_project = self.render_service.api.get_project_details(project.id)

        # Build info panel content
        info = f"""
📛 **Name:** {detailed_project.name}
🆔 **ID:** {detailed_project.id}
👤 **Owner:** {detailed_project.owner.name} ({detailed_project.owner.email})
🔐 **Owner Type:** {detailed_project.owner.type.title()}
📅 **Created:** {detailed_project.formatted_created_at}
📝 **Updated:** {detailed_project.formatted_updated_at}
🌍 **Environments:** {len(detailed_project.environment_ids)}
        """

        if detailed_project.owner.two_factor_auth_enabled is not None:
            status = (
                "✅ Enabled"
                if detailed_project.owner.two_factor_auth_enabled
                else "❌ Disabled"
            )
            info += f"🔒 **2FA:** {status}\n"

        console.print(Panel(info, title="📋 Project Information", expand=False))

        # Show environment IDs if any
        if detailed_project.environment_ids:
            env_table = _create_table(
                "🌍 Environment IDs",
                [
                    ("Environment ID", "cyan", 30),
                ],
            )

            for env_id in detailed_project.environment_ids:
                env_table.add_row(env_id)

            console.print(env_table)

    def _find_project(self, name_or_id: str) -> Optional[Project]:
        """Find project by name or ID"""
        try:
            project = self.render_service.api.find_project(name_or_id)

            if not project:
                display_error(f"Project '{name_or_id}' not found")
                display_info("Run 'r4r projects' to see available projects")
                return None

            return project
        except APIError as e:
            display_error(f"Failed to fetch projects: {e.message}")
            return None

    def list_project_services(self, project_name: str, detailed: bool = False) -> None:
        """Handle list services in project command"""
        project = self._find_project(project_name)
        if not project:
            return

        with console.status(f"Getting services in project '{project.name}'..."):
            services = self.render_service.api.list_services_by_project(project.id)

        if not services:
            display_warning(f"No services found in project '{project.name}'")
            display_info("Services might be in different projects or environments")
            return

        # Show project info first
        console.print(f"📋 Project: {project.name} (ID: {project.id})", style="cyan")
        console.print(f"🌍 Environments: {len(project.environment_ids)}", style="dim")

        # Create table for services
        columns: list[Union[tuple[str, str], tuple[str, str, int]]] = [
            ("Name", "cyan", 20),
            ("Type", "magenta", 12),
            ("Status", "green", 12),
        ]
        if detailed:
            columns.extend(
                [("Region", "yellow", 10), ("Plan", "blue", 10), ("Created", "dim", 12)]
            )
        columns.append(("URL", "blue"))

        table = _create_table(
            f"Services in '{project.name}' ({len(services)})", columns
        )

        for service in services:
            # Get status display
            status_display = f"{service.status_icon} {service.status.title()}"
            service_type_display = service.type.replace("_", " ").title()

            # Build URL
            url = service.url or "N/A"
            if not url or url == "N/A":
                if service.slug:
                    url = f"https://{service.slug}.onrender.com"
                elif service.name:
                    url = (
                        f"https://{service.name.lower().replace('_', '-')}.onrender.com"
                    )

            row_data = [service.name, service_type_display, status_display]

            if detailed:
                region = service.region or "N/A"
                plan = service.plan or "N/A"
                created = service.created_at[:10] if service.created_at else "N/A"
                row_data.extend([region, plan, created])

            row_data.append(url)
            table.add_row(*row_data)

        console.print(table)

    def list_environment_services(
        self, environment_id: str, detailed: bool = False
    ) -> None:
        """Handle list services in environment command"""
        with console.status(f"Getting services in environment '{environment_id}'..."):
            services = self.render_service.api.list_services_by_environment(
                environment_id
            )

        if not services:
            display_warning(f"No services found in environment '{environment_id}'")
            return

        # Show environment info first
        console.print(f"🌍 Environment: {environment_id}", style="cyan")

        # Create table for services
        columns: list[Union[tuple[str, str], tuple[str, str, int]]] = [
            ("Name", "cyan", 20),
            ("Type", "magenta", 12),
            ("Status", "green", 12),
        ]
        if detailed:
            columns.extend(
                [("Region", "yellow", 10), ("Plan", "blue", 10), ("Created", "dim", 12)]
            )
        columns.append(("URL", "blue"))

        table = _create_table(f"Services in Environment ({len(services)})", columns)

        for service in services:
            # Get status display
            status_display = f"{service.status_icon} {service.status.title()}"
            service_type_display = service.type.replace("_", " ").title()

            # Build URL
            url = service.url or "N/A"
            if not url or url == "N/A":
                if service.slug:
                    url = f"https://{service.slug}.onrender.com"
                elif service.name:
                    url = (
                        f"https://{service.name.lower().replace('_', '-')}.onrender.com"
                    )

            row_data = [service.name, service_type_display, status_display]

            if detailed:
                region = service.region or "N/A"
                plan = service.plan or "N/A"
                created = service.created_at[:10] if service.created_at else "N/A"
                row_data.extend([region, plan, created])

            row_data.append(url)
            table.add_row(*row_data)

        console.print(table)
