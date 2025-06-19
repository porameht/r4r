#!/usr/bin/env python3
"""
r4r Core Utilities
Common utilities and base classes following clean architecture principles
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from rich.console import Console

console = Console()


class ServiceType(Enum):
    WEB_SERVICE = "web_service"
    BACKGROUND_WORKER = "background_worker"
    STATIC_SITE = "static_site"
    PRIVATE_SERVICE = "private_service"


class ServiceStatus(Enum):
    CREATING = "creating"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BUILD_FAILED = "build_failed"
    DEPLOYING = "deploying"


@dataclass
class Config:
    """Application configuration"""

    api_key: str
    base_url: str = "https://api.render.com/v1"

    @classmethod
    def from_env(cls) -> "Config":
        api_key = os.getenv("RENDER_API_KEY")
        if not api_key:
            raise ValueError("RENDER_API_KEY environment variable required")
        return cls(api_key=api_key)


class APIError(Exception):
    """Custom API error with status code"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class HTTPClient:
    """HTTP client with error handling and retry logic"""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response with standardized error handling"""
        try:
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError:
            error_msg = self._extract_error_message(response)
            raise APIError(error_msg, response.status_code)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")

    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract error message from response"""
        try:
            error_data = response.json()
            return error_data.get("message", f"HTTP {response.status_code}")
        except (ValueError, KeyError):
            return f"HTTP {response.status_code}: {response.reason}"

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """GET request"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        return self._handle_response(response)

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """POST request"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data)
        return self._handle_response(response)

    def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """PUT request"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        response = self.session.put(url, json=data)
        return self._handle_response(response)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request"""
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        response = self.session.delete(url)
        return self._handle_response(response)


def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return timestamp[:19] if timestamp else "N/A"


def truncate_string(text: str, max_length: int) -> str:
    """Truncate string with ellipsis if too long"""
    return text[: max_length - 3] + "..." if len(text) > max_length else text


def get_status_icon(status: str) -> str:
    """Get emoji icon for status"""
    status_icons = {
        "live": "🟢",
        "active": "🟢",
        "suspended": "🔴",
        "build_failed": "🔴",
        "build_in_progress": "🟡",
        "deploying": "🟡",
        "creating": "🟡",
        "succeeded": "✅",
        "failed": "❌",
        "running": "🟡",
        "canceled": "⚪",
    }
    return status_icons.get(status.lower(), "❓")


class ConfigManager:
    """Manage application configuration and credentials"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".r4r"
        self.config_file = self.config_dir / "config.json"

    def save_config(self, config: dict) -> None:
        """Save configuration to file"""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def load_config(self) -> dict:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {}

        with open(self.config_file) as f:
            return json.load(f)

    def get_api_key(self) -> Optional[str]:
        """Get API key from config or environment"""
        # Try environment first
        api_key = os.getenv("RENDER_API_KEY")
        if api_key:
            return api_key

        # Try config file
        config = self.load_config()
        return config.get("api_key")

    def clear_config(self) -> None:
        """Clear stored configuration"""
        if self.config_file.exists():
            self.config_file.unlink()
