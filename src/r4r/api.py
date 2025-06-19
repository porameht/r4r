#!/usr/bin/env python3
"""
r4r Render API Client
Monitoring and Core Services Management for Render API
"""

import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Service":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type", ""),
            status=data.get("status", ""),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
            auto_deploy=data.get("autoDeploy", True),
            branch=data.get("branch"),
            repo_url=data.get("repo", {}).get("url"),
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
            commit_id=data.get("commit", {}).get("id"),
            commit_message=data.get("commit", {}).get("message"),
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


class RenderAPI:
    """Infrastructure: Render API Client"""

    def __init__(self, config: Config):
        self.client = HTTPClient(config)

    # Monitoring Methods
    def get_service_events(self, service_id: str) -> List[Event]:
        """Get events for a service"""
        data = self.client.get(f"services/{service_id}/events")
        return [Event.from_dict(event) for event in data.get("events", [])]

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

    # Core Services Management Methods
    def list_services(self) -> List[Service]:
        """List all services"""
        data = self.client.get("services")
        return [Service.from_dict(service) for service in data.get("services", [])]

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
        payload = {
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
    def list_deploys(self, service_id: str) -> List[Deploy]:
        """List deployments for a service"""
        data = self.client.get(f"services/{service_id}/deploys")
        return [Deploy.from_dict(deploy) for deploy in data.get("deploys", [])]

    def trigger_deploy(self, service_id: str, clear_cache: bool = False) -> Deploy:
        """Trigger a new deployment"""
        data = self.client.post(
            f"services/{service_id}/deploys", {"clearCache": clear_cache}
        )
        return Deploy.from_dict(data)

    def rollback_deploy(self, service_id: str, deploy_id: str) -> Deploy:
        """Rollback to a previous deployment"""
        data = self.client.post(
            f"services/{service_id}/rollback", {"deployId": deploy_id}
        )
        return Deploy.from_dict(data)

    # Log Stream Methods (placeholder implementations)
    def list_log_streams(self, service_id: str = None) -> List[LogStream]:
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
