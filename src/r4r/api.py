#!/usr/bin/env python3
"""
r4r Render API Client
Consolidated API client for all Render operations
"""

import json
import re
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import websockets
from rich.console import Console

from .config import Config, HTTPClient, ServiceType, format_timestamp, get_status_icon

console = Console()


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class LogEntry:
    """Domain entity: Log entry"""

    timestamp: str
    level: str
    message: str
    source: str
    service_id: str
    resource_id: Optional[str] = None
    labels: Optional[Dict[str, str]] = None


@dataclass
class LogStream:
    """Domain entity: Log stream"""

    id: str
    name: str
    service_id: str
    filters: Dict[str, Any]
    created_at: str
    updated_at: str
    enabled: bool = True


@dataclass
class LogStreamOverride:
    """Domain entity: Log stream override"""

    id: str
    stream_id: str
    resource_id: str
    overrides: Dict[str, Any]
    created_at: str
    updated_at: str


@dataclass
class Service:
    """Domain entity: Render service"""

    id: str
    name: str
    type: str
    status: str
    created_at: str
    updated_at: str
    auto_deploy: bool = True
    branch: Optional[str] = None
    repo_url: Optional[str] = None
    slug: Optional[str] = None
    url: Optional[str] = None
    region: Optional[str] = None
    plan: Optional[str] = None

    @classmethod
    def _extract_repo_url(cls, repo_data: Any) -> Optional[str]:
        """Extract repo URL from various repo data formats"""
        if not repo_data:
            return None
        if isinstance(repo_data, str):
            return repo_data
        if isinstance(repo_data, dict):
            return repo_data.get("url")
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Service":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type", ""),
            status=data.get("status", ""),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
            auto_deploy=data.get("autoDeploy") in ["yes", True],
            branch=data.get("branch"),
            repo_url=cls._extract_repo_url(data.get("repo")),
            slug=data.get("slug"),
            url=data.get("url"),
            region=data.get("region"),
            plan=data.get("plan"),
        )

    @property
    def status_icon(self) -> str:
        return get_status_icon(self.status)

    @property
    def formatted_created_at(self) -> str:
        return format_timestamp(self.created_at)


@dataclass
class Deploy:
    """Domain entity: Service deployment"""

    id: str
    service_id: str
    status: str
    created_at: str
    finished_at: Optional[str]
    commit_id: Optional[str]
    commit_message: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Deploy":
        return cls(
            id=data.get("id", ""),
            service_id=data.get("serviceId", ""),
            status=data.get("status", ""),
            created_at=data.get("createdAt", ""),
            finished_at=data.get("finishedAt"),
            commit_id=data.get("commit", {}).get("id") if data.get("commit") else None,
            commit_message=data.get("commit", {}).get("message")
            if data.get("commit")
            else None,
        )

    @property
    def status_icon(self) -> str:
        return get_status_icon(self.status)

    @property
    def duration(self) -> str:
        """Calculate deployment duration"""
        if not self.finished_at or not self.created_at:
            return "N/A"
        try:
            start = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(self.finished_at.replace("Z", "+00:00"))
            return str(end - start).split(".")[0]
        except (ValueError, TypeError):
            return "N/A"


@dataclass
class Event:
    """Domain entity: Service event"""

    id: str
    service_id: str
    type: str
    description: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            id=data.get("id", ""),
            service_id=data.get("serviceId", ""),
            type=data.get("type", ""),
            description=data.get("description", ""),
            timestamp=data.get("timestamp", ""),
            details=data.get("details"),
        )

    @property
    def formatted_timestamp(self) -> str:
        return format_timestamp(self.timestamp)


@dataclass
class Job:
    """Domain entity: Service job"""

    id: str
    service_id: str
    command: str
    status: str
    created_at: str
    finished_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        return cls(
            id=data.get("id", ""),
            service_id=data.get("serviceId", ""),
            command=data.get("startCommand", ""),
            status=data.get("status", ""),
            created_at=data.get("createdAt", ""),
            finished_at=data.get("finishedAt"),
        )

    @property
    def status_icon(self) -> str:
        return get_status_icon(self.status)


@dataclass
class Owner:
    """Domain entity: Project/Service owner"""

    id: str
    name: str
    email: str
    type: str  # "user" or "team"
    two_factor_auth_enabled: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Owner":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            type=data.get("type", ""),
            two_factor_auth_enabled=data.get("twoFactorAuthEnabled"),
        )


@dataclass
class Project:
    """Domain entity: Render project"""

    id: str
    name: str
    created_at: str
    updated_at: str
    owner: Owner
    environment_ids: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
            owner=Owner.from_dict(data.get("owner", {})),
            environment_ids=data.get("environmentIds", []),
        )

    @property
    def formatted_created_at(self) -> str:
        return format_timestamp(self.created_at)

    @property
    def formatted_updated_at(self) -> str:
        return format_timestamp(self.updated_at)


class RenderAPI:
    """Infrastructure: Consolidated Render API Client"""

    def __init__(self, config: Config):
        self.client = HTTPClient(config)
        self.config = config

    def _extract_items(self, data: Any, key: str) -> List[Dict[str, Any]]:
        """Extract items from nested API response"""
        if isinstance(data, list):
            return [
                item.get(key, item)
                for item in data
                if key in item or "name" in item or "id" in item
            ]
        return data.get(f"{key}s", []) if isinstance(data, dict) else []

    # Service Management Methods
    def list_services(self, limit: Optional[int] = None) -> List[Service]:
        """List all services with pagination support"""
        all_services = []
        cursor = None
        page_limit = 100  # Max per page to get all services efficiently

        while True:
            params = {"limit": page_limit}
            if cursor:
                params["cursor"] = cursor

            data = self.client.get("services", params=params)

            # Handle response format
            if isinstance(data, list):
                services_data = self._extract_items(data, "service")

                for item in data:
                    if "service" in item:
                        service_data = item["service"]
                        # Map status from suspended field
                        if "suspended" in service_data:
                            suspended = service_data["suspended"]
                            if suspended == "not_suspended":
                                service_data["status"] = "active"
                            elif suspended == "suspended":
                                service_data["status"] = "suspended"
                            else:
                                service_data["status"] = "unknown"
                        else:
                            service_data["status"] = "unknown"

                        all_services.append(Service.from_dict(service_data))

                    # Check for next page cursor
                    if "cursor" in item:
                        cursor = item["cursor"]
                    else:
                        cursor = None

                # If we got fewer than page limit, we're done
                if len(data) < page_limit:
                    break

            else:
                # Handle non-paginated response
                services_data = self._extract_items(data, "service")
                for service in services_data:
                    # Map status from suspended field
                    if "suspended" in service:
                        suspended = service["suspended"]
                        if suspended == "not_suspended":
                            service["status"] = "active"
                        elif suspended == "suspended":
                            service["status"] = "suspended"
                        else:
                            service["status"] = "unknown"
                    else:
                        service["status"] = "unknown"

                    all_services.append(Service.from_dict(service))
                break

        # Apply limit if specified
        if limit and len(all_services) > limit:
            all_services = all_services[:limit]

        return all_services

    def find_service(self, name_or_id: str) -> Optional[Service]:
        """Find service by name or ID"""
        services = self.list_services()
        return next(
            (s for s in services if s.name == name_or_id or s.id == name_or_id),
            None,
        )

    def get_service_details(self, service_id: str) -> Service:
        """Get detailed service information"""
        data = self.client.get(f"services/{service_id}")
        return Service.from_dict(data)

    def create_service(
        self,
        name: str,
        service_type: ServiceType,
        repo_url: str,
        branch: str = "main",
        auto_deploy: bool = True,
        environment_variables: Optional[Dict[str, str]] = None,
    ) -> Service:
        """Create a new service"""
        payload: Dict[str, Any] = {
            "name": name,
            "type": service_type.value,
            "repo": repo_url,
            "branch": branch,
            "autoDeploy": auto_deploy,
        }

        if environment_variables:
            payload["envVars"] = environment_variables

        data = self.client.post("services", payload)
        return Service.from_dict(data)

    def update_service(
        self,
        service_id: str,
        name: Optional[str] = None,
        auto_deploy: Optional[bool] = None,
        branch: Optional[str] = None,
    ) -> Service:
        """Update service configuration"""
        payload = {
            k: v
            for k, v in {
                "name": name,
                "autoDeploy": auto_deploy,
                "branch": branch,
            }.items()
            if v is not None
        }

        data = self.client.put(f"services/{service_id}", payload)
        return Service.from_dict(data)

    def suspend_service(self, service_id: str) -> bool:
        """Suspend a service"""
        self.client.post(f"services/{service_id}/suspend")
        return True

    def resume_service(self, service_id: str) -> bool:
        """Resume a suspended service"""
        self.client.post(f"services/{service_id}/resume")
        return True

    def restart_service(self, service_id: str) -> bool:
        """Restart a service"""
        self.client.post(f"services/{service_id}/restart")
        return True

    def scale_service(self, service_id: str, num_instances: int) -> bool:
        """Scale a service to specified number of instances"""
        self.client.post(
            f"services/{service_id}/scale", {"numInstances": num_instances}
        )
        return True

    # Deployment Management Methods
    def list_deploys(self, service_id: str, limit: int = 20) -> List[Deploy]:
        """List deployments for a service"""
        params = {"limit": limit}
        data = self.client.get(f"services/{service_id}/deploys", params=params)
        deploys_data = self._extract_items(data, "deploy")
        return [Deploy.from_dict(deploy) for deploy in deploys_data]

    def trigger_deploy(self, service_id: str, clear_cache: bool = False) -> Deploy:
        """Trigger a new deployment"""
        cache_option = "clear" if clear_cache else "do_not_clear"
        data = self.client.post(
            f"services/{service_id}/deploys", {"clearCache": cache_option}
        )
        return Deploy.from_dict(data)

    def rollback_deploy(self, service_id: str, deploy_id: str) -> Deploy:
        """Rollback to a previous deployment"""
        data = self.client.post(
            f"services/{service_id}/rollback", {"deployId": deploy_id}
        )
        return Deploy.from_dict(data)

    # Job Management Methods
    def create_job(self, service_id: str, command: str) -> Job:
        """Create a one-off job"""
        data = self.client.post(
            f"services/{service_id}/jobs", {"startCommand": command}
        )
        return Job.from_dict(data)

    def list_jobs(self, service_id: str, limit: int = 20) -> List[Job]:
        """List recent jobs for a service"""
        params = {"limit": limit}
        data = self.client.get(f"services/{service_id}/jobs", params=params)
        jobs_data = self._extract_items(data, "job")
        return [Job.from_dict(job) for job in jobs_data]

    def get_job_status(self, job_id: str) -> Job:
        """Get job status"""
        data = self.client.get(f"jobs/{job_id}")
        return Job.from_dict(data)

    # Events and Monitoring Methods
    def get_service_events(self, service_id: str, limit: int = 20) -> List[Event]:
        """Get events for a service"""
        params = {"limit": limit}
        data = self.client.get(f"services/{service_id}/events", params=params)
        events_data = self._extract_items(data, "event")
        return [Event.from_dict(event) for event in events_data]

    def get_event_details(self, event_id: str) -> Event:
        """Get detailed information about a specific event"""
        data = self.client.get(f"events/{event_id}")
        return Event.from_dict(data)

    def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Get current status of a service"""
        data = self.client.get(f"services/{service_id}")
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "status": data.get("status"),
            "type": data.get("type"),
            "health": data.get("health", "unknown"),
            "updated_at": data.get("updatedAt"),
        }

    # Project Management Methods
    def list_projects(self) -> List[Project]:
        """List all projects"""
        data = self.client.get("projects")
        projects_data = self._extract_items(data, "project")
        return [Project.from_dict(project) for project in projects_data]

    def get_project_details(self, project_id: str) -> Project:
        """Get detailed project information"""
        data = self.client.get(f"projects/{project_id}")
        return Project.from_dict(data)

    def find_project(self, name_or_id: str) -> Optional[Project]:
        """Find project by name or ID"""
        projects = self.list_projects()
        return next(
            (p for p in projects if p.name == name_or_id or p.id == name_or_id),
            None,
        )

    def list_services_by_project(self, project_id: str) -> List[Service]:
        """List all services in a specific project"""
        # Get project details to get environment IDs
        project = self.get_project_details(project_id)

        # Get all services
        all_services = self.list_services()

        # Filter services by environment IDs in the project
        project_services = []
        for service in all_services:
            try:
                # Get detailed service info to check environment
                service_details = self.client.get(f"services/{service.id}")
                if service_details.get("environmentId") in project.environment_ids:
                    project_services.append(service)
            except (AttributeError, KeyError, TypeError):
                # Skip if we can't determine environment
                continue

        return project_services

    def list_services_by_environment(self, environment_id: str) -> List[Service]:
        """List all services in a specific environment"""
        all_services = self.list_services()
        env_services = []

        for service in all_services:
            try:
                # Get detailed service info to check environment
                service_details = self.client.get(f"services/{service.id}")
                if service_details.get("environmentId") == environment_id:
                    env_services.append(service)
            except (AttributeError, KeyError, TypeError):
                continue

        return env_services

    # User and Account Methods
    def get_api_key_info(self) -> Dict[str, Any]:
        """Get information about the current API key"""
        return self.client.get("users")

    def get_owner_id(self) -> str:
        """Get the owner/workspace ID for the current user"""
        owners_data = self.client.get("owners")
        if isinstance(owners_data, list) and len(owners_data) > 0:
            owner_item = owners_data[0]
            if isinstance(owner_item, dict):
                owner = owner_item.get("owner", {})
                return owner.get("id", "")
        return ""

    # Logs Methods
    def get_service_logs(self, service_id: str, lines: int = 100) -> Dict[str, Any]:
        """Get service logs"""
        params = {"lines": lines}
        return self.client.get(f"services/{service_id}/logs", params=params)

    async def stream_logs_async(
        self, service_id: str, owner_id: str, lines: int = 100
    ) -> None:
        """Stream logs via WebSocket"""
        params = {
            "ownerId": owner_id,
            "resource": [service_id],
            "limit": lines,
            "direction": "backward",
        }

        ws_url = f"wss://api.render.com/v1/logs/subscribe?{urllib.parse.urlencode(params, doseq=True)}"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        try:
            async with websockets.connect(
                ws_url, additional_headers=headers
            ) as websocket:
                console.print("🔗 Connected to log stream...", style="green")
                async for message in websocket:
                    try:
                        log_data = json.loads(message)
                        self._format_log_message(log_data)
                    except json.JSONDecodeError:
                        # Handle potential bytes message
                        message_str = (
                            message
                            if isinstance(message, str)
                            else message.decode("utf-8")
                        )
                        console.print(f"Raw: {message_str}", style="dim")
        except Exception as e:
            console.print(f"❌ Connection error: {e}", style="red")

    def _format_log_message(self, log_data: Dict[str, Any]) -> None:
        """Format and display a single log message"""
        try:
            # Parse timestamp from log data
            if "timestamp" in log_data:
                timestamp = datetime.fromisoformat(
                    log_data["timestamp"].replace("Z", "+00:00")
                )
                time_str = timestamp.strftime("%H:%M:%S")
            else:
                time_str = datetime.now().strftime("%H:%M:%S")
        except (ValueError, TypeError, AttributeError):
            time_str = datetime.now().strftime("%H:%M:%S")

        message = log_data.get("message", "")

        # Parse labels for metadata
        labels = {
            label["name"]: label["value"]
            for label in log_data.get("labels", [])
            if isinstance(label, dict) and "name" in label
        }

        level = labels.get("level", "info").upper()
        log_type = labels.get("type", "app")

        # Clean message
        clean_message = re.sub(r"\x1b\[[0-9;]*[mK]", "", message)
        clean_message = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", clean_message).strip()

        # Color by level
        colors = {"ERROR": "red", "WARN": "yellow", "INFO": "blue", "DEBUG": "dim"}
        level_color = colors.get(level, "white")

        console.print(
            f"[dim]{time_str}[/dim] [{level_color}]{level}[/{level_color}] [magenta]{log_type}[/magenta] {clean_message}"
        )

    # Log Stream Methods (placeholder implementations)
    def list_log_streams(self, service_id: Optional[str] = None) -> List[LogStream]:
        """List log streams - placeholder implementation"""
        return []

    def create_log_stream(
        self, name: str, service_id: str, filters: Dict[str, Any], enabled: bool = True
    ) -> LogStream:
        """Create log stream - placeholder implementation"""
        return LogStream(
            id="placeholder",
            name=name,
            service_id=service_id,
            filters=filters,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            enabled=enabled,
        )

    def update_log_stream(self, stream_id: str, **kwargs) -> LogStream:
        """Update log stream - placeholder implementation"""
        return LogStream(
            id=stream_id,
            name=kwargs.get("name", "updated"),
            service_id="placeholder",
            filters=kwargs.get("filters", {}),
            created_at="2024-01-01T00:00:00Z",
            updated_at=datetime.now().isoformat(),
            enabled=kwargs.get("enabled", True),
        )

    def delete_log_stream(self, stream_id: str) -> bool:
        """Delete log stream - placeholder implementation"""
        return True

    def list_log_stream_overrides(self, stream_id: str) -> List[LogStreamOverride]:
        """List log stream overrides - placeholder implementation"""
        return []

    def create_log_stream_override(
        self, stream_id: str, resource_id: str, overrides: Dict[str, Any]
    ) -> LogStreamOverride:
        """Create log stream override - placeholder implementation"""
        return LogStreamOverride(
            id="placeholder",
            stream_id=stream_id,
            resource_id=resource_id,
            overrides=overrides,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

    def update_log_stream_override(
        self, stream_id: str, override_id: str, overrides: Dict[str, Any]
    ) -> LogStreamOverride:
        """Update log stream override - placeholder implementation"""
        return LogStreamOverride(
            id=override_id,
            stream_id=stream_id,
            resource_id="placeholder",
            overrides=overrides,
            created_at="2024-01-01T00:00:00Z",
            updated_at=datetime.now().isoformat(),
        )

    def delete_log_stream_override(self, stream_id: str, override_id: str) -> bool:
        """Delete log stream override - placeholder implementation"""
        return True

    async def subscribe_to_logs(self, resource_ids: List[str]):
        """Subscribe to real-time logs - placeholder implementation"""
        # This is a placeholder for real log streaming
        # In a real implementation, this would connect to a WebSocket or SSE stream
        yield  # Make this an async generator
        return


class RenderService:
    """Application Service: High-level business operations"""

    def __init__(self, config: Config):
        self.api = RenderAPI(config)
        self.console = Console()

    def get_service_overview(self, service_id: str) -> Dict[str, Any]:
        """Get comprehensive overview of a service"""
        status = self.api.get_service_status(service_id)
        recent_events = self.api.get_service_events(service_id)[:10]
        recent_deploys = self.api.list_deploys(service_id)[:5]

        return {
            "status": status,
            "recent_events": recent_events,
            "recent_deploys": recent_deploys,
        }

    def deploy_and_wait(self, service_id: str, timeout_minutes: int = 10) -> bool:
        """Deploy service and wait for completion"""
        deploy = self.api.trigger_deploy(service_id)
        console.print(f"🚀 Deployment {deploy.id} started for service {service_id}")

        return self._wait_for_deploy_completion(service_id, deploy.id, timeout_minutes)

    def _wait_for_deploy_completion(
        self, service_id: str, deploy_id: str, timeout_minutes: int
    ) -> bool:
        """Wait for deployment to complete"""
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start_time < timeout_seconds:
            deploys = self.api.list_deploys(service_id)
            current_deploy = next((d for d in deploys if d.id == deploy_id), None)

            if current_deploy and current_deploy.status in ["live", "failed"]:
                success = current_deploy.status == "live"
                status = "completed successfully" if success else "failed"
                style = "green" if success else "red"
                console.print(
                    f"{'✅' if success else '❌'} Deployment {deploy_id} {status}",
                    style=style,
                )
                return success

            time.sleep(10)
            console.print("⏳ Waiting for deployment...", style="dim")

        console.print(
            f"⏰ Deployment timeout after {timeout_minutes} minutes", style="yellow"
        )
        return False

    def scale_service(self, service_id: str, instances: int) -> bool:
        """Scale service with feedback"""
        try:
            self.api.scale_service(service_id, instances)
            console.print(
                f"📈 Scaled service {service_id} to {instances} instances",
                style="green",
            )
            return True
        except Exception as e:
            console.print(f"❌ Failed to scale service: {e}", style="red")
            return False

    def get_recent_logs(self, resource_ids: list, hours: int = 1):
        """Get recent logs for compatibility - simplified implementation"""
        # For now, return empty list as this needs proper log API implementation
        return []

    def stream_logs_sync(self, resource_ids: list, callback):
        """Stream logs synchronously for compatibility"""
        # Simplified implementation - in real use would need proper streaming
        console.print(
            "Log streaming not yet implemented in new architecture", style="yellow"
        )
