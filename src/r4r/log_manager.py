#!/usr/bin/env python3
"""
r4r Log Management System
Complete implementation of Render's log management API with TUI interface
"""

import json
import asyncio
import websockets
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from rich.console import Console

console = Console()

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"

@dataclass
class LogEntry:
    """Represents a single log entry from Render"""
    timestamp: str
    level: str
    message: str
    source: str
    service_id: str
    resource_id: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        return cls(
            timestamp=data.get('timestamp', ''),
            level=data.get('level', 'info'),
            message=data.get('message', ''),
            source=data.get('source', ''),
            service_id=data.get('serviceId', ''),
            resource_id=data.get('resourceId'),
            labels=data.get('labels', {})
        )

@dataclass
class LogStream:
    """Represents a log stream configuration"""
    id: str
    name: str
    service_id: str
    filters: Dict[str, Any]
    created_at: str
    updated_at: str
    enabled: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogStream':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            service_id=data.get('serviceId', ''),
            filters=data.get('filters', {}),
            created_at=data.get('createdAt', ''),
            updated_at=data.get('updatedAt', ''),
            enabled=data.get('enabled', True)
        )

@dataclass
class LogStreamOverride:
    """Represents a log stream override configuration"""
    id: str
    stream_id: str
    resource_id: str
    overrides: Dict[str, Any]
    created_at: str
    updated_at: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogStreamOverride':
        return cls(
            id=data.get('id', ''),
            stream_id=data.get('streamId', ''),
            resource_id=data.get('resourceId', ''),
            overrides=data.get('overrides', {}),
            created_at=data.get('createdAt', ''),
            updated_at=data.get('updatedAt', '')
        )

class RenderLogAPI:
    """Complete Render Log Management API Client"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.render.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
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
            
            console.print(f"❌ API Error ({response.status_code}): {error_msg}", style="red")
            raise Exception(f"API Error: {error_msg}")
    
    # Log Retrieval Methods
    def list_logs(self, 
                  resource_ids: List[str],
                  start_time: Optional[str] = None,
                  end_time: Optional[str] = None,
                  limit: int = 100,
                  level: Optional[LogLevel] = None) -> Dict[str, Any]:
        """
        List logs across multiple resources
        
        Args:
            resource_ids: List of resource IDs to query
            start_time: ISO timestamp for start of log range
            end_time: ISO timestamp for end of log range
            limit: Maximum number of logs to return
            level: Filter by log level
            
        Returns:
            Dict containing logs and pagination info
        """
        params = {
            "resourceIds": ",".join(resource_ids),
            "limit": limit
        }
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if level:
            params["level"] = level.value
            
        response = self.session.get(f"{self.base_url}/logs", params=params)
        return self._handle_response(response)
    
    def subscribe_to_logs(self, resource_ids: List[str]) -> AsyncIterator[LogEntry]:
        """
        Subscribe to real-time log updates via WebSocket
        
        Args:
            resource_ids: List of resource IDs to subscribe to
            
        Yields:
            LogEntry objects as they arrive
        """
        return self._websocket_log_stream(resource_ids)
    
    async def _websocket_log_stream(self, resource_ids: List[str]) -> AsyncIterator[LogEntry]:
        """Internal WebSocket implementation for log streaming using Render's subscribe endpoint"""
        # Use the correct Render API WebSocket endpoint
        ws_url = "wss://api.render.com/v1/logs/subscribe"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                console.print(f"🔗 Connected to Render log stream for {len(resource_ids)} resources", style="green")
                
                # According to Render API, we don't need to send a subscription message
                # The connection itself with the correct auth starts the stream
                # However, we may need to send resource IDs as a message
                
                # Send resource IDs as subscription parameters (if required by implementation)
                subscription_msg = {
                    "resourceIds": resource_ids
                }
                await websocket.send(json.dumps(subscription_msg))
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        # Handle different message types from Render
                        if data.get("type") == "log" or "timestamp" in data:
                            # Create LogEntry from received data
                            log_entry = LogEntry(
                                timestamp=data.get("timestamp", ""),
                                level=data.get("level", "info"),
                                message=data.get("message", ""),
                                source=data.get("source", "unknown"),
                                service_id=data.get("serviceId", ""),
                                resource_id=data.get("resourceId"),
                                labels=data.get("labels", {})
                            )
                            yield log_entry
                        elif data.get("type") == "error":
                            console.print(f"⚠️ Stream error: {data.get('message', 'Unknown error')}", style="yellow")
                        elif data.get("type") == "connection":
                            console.print(f"📡 Connection status: {data.get('status', 'unknown')}", style="dim")
                        
                    except json.JSONDecodeError:
                        # Handle non-JSON messages (might be plain text logs)
                        if message.strip():
                            # Try to parse as plain text log
                            yield LogEntry(
                                timestamp=datetime.now().isoformat(),
                                level="info",
                                message=message.strip(),
                                source="render-stream",
                                service_id=resource_ids[0] if resource_ids else "",
                                resource_id=None,
                                labels={}
                            )
                    except Exception as parse_error:
                        console.print(f"⚠️ Error parsing message: {parse_error}", style="yellow")
                        continue
                        
        except websockets.exceptions.ConnectionClosed:
            console.print("📡 WebSocket connection closed", style="yellow")
        except websockets.exceptions.InvalidURI:
            console.print("❌ Invalid WebSocket URI", style="red")
            raise
        except Exception as e:
            console.print(f"❌ WebSocket connection error: {e}", style="red")
            # Fallback to polling if WebSocket fails
            console.print("🔄 Falling back to polling mode...", style="yellow")
            await self._fallback_polling_stream(resource_ids)
    
    def list_log_label_values(self, 
                             resource_ids: List[str],
                             label_key: str) -> List[str]:
        """
        List possible values for a specific log label
        
        Args:
            resource_ids: List of resource IDs to query
            label_key: The label key to get values for
            
        Returns:
            List of possible label values
        """
        params = {
            "resourceIds": ",".join(resource_ids),
            "labelKey": label_key
        }
        
        response = self.session.get(f"{self.base_url}/logs/labels/values", params=params)
        data = self._handle_response(response)
        return data.get("values", [])
    
    # Log Stream Management Methods
    def list_log_streams(self, service_id: Optional[str] = None) -> List[LogStream]:
        """List all log streams, optionally filtered by service"""
        params = {}
        if service_id:
            params["serviceId"] = service_id
            
        response = self.session.get(f"{self.base_url}/logStreams", params=params)
        data = self._handle_response(response)
        return [LogStream.from_dict(stream) for stream in data.get("logStreams", [])]
    
    def get_log_stream(self, stream_id: str) -> LogStream:
        """Retrieve a specific log stream"""
        response = self.session.get(f"{self.base_url}/logStreams/{stream_id}")
        data = self._handle_response(response)
        return LogStream.from_dict(data)
    
    def create_log_stream(self, 
                         name: str,
                         service_id: str,
                         filters: Dict[str, Any],
                         enabled: bool = True) -> LogStream:
        """Create a new log stream"""
        payload = {
            "name": name,
            "serviceId": service_id,
            "filters": filters,
            "enabled": enabled
        }
        
        response = self.session.post(f"{self.base_url}/logStreams", json=payload)
        data = self._handle_response(response)
        return LogStream.from_dict(data)
    
    def update_log_stream(self, 
                         stream_id: str,
                         name: Optional[str] = None,
                         filters: Optional[Dict[str, Any]] = None,
                         enabled: Optional[bool] = None) -> LogStream:
        """Update an existing log stream"""
        payload = {}
        if name is not None:
            payload["name"] = name
        if filters is not None:
            payload["filters"] = filters
        if enabled is not None:
            payload["enabled"] = enabled
            
        response = self.session.put(f"{self.base_url}/logStreams/{stream_id}", json=payload)
        data = self._handle_response(response)
        return LogStream.from_dict(data)
    
    def delete_log_stream(self, stream_id: str) -> bool:
        """Delete a log stream"""
        response = self.session.delete(f"{self.base_url}/logStreams/{stream_id}")
        self._handle_response(response)
        return True
    
    # Log Stream Override Methods
    def list_log_stream_overrides(self, stream_id: str) -> List[LogStreamOverride]:
        """List all overrides for a log stream"""
        response = self.session.get(f"{self.base_url}/logStreams/{stream_id}/overrides")
        data = self._handle_response(response)
        return [LogStreamOverride.from_dict(override) for override in data.get("overrides", [])]
    
    def get_log_stream_override(self, stream_id: str, override_id: str) -> LogStreamOverride:
        """Retrieve a specific log stream override"""
        response = self.session.get(f"{self.base_url}/logStreams/{stream_id}/overrides/{override_id}")
        data = self._handle_response(response)
        return LogStreamOverride.from_dict(data)
    
    def create_log_stream_override(self,
                                  stream_id: str,
                                  resource_id: str,
                                  overrides: Dict[str, Any]) -> LogStreamOverride:
        """Create a new log stream override"""
        payload = {
            "resourceId": resource_id,
            "overrides": overrides
        }
        
        response = self.session.post(f"{self.base_url}/logStreams/{stream_id}/overrides", json=payload)
        data = self._handle_response(response)
        return LogStreamOverride.from_dict(data)
    
    def update_log_stream_override(self,
                                  stream_id: str,
                                  override_id: str,
                                  overrides: Dict[str, Any]) -> LogStreamOverride:
        """Update an existing log stream override"""
        payload = {"overrides": overrides}
        
        response = self.session.put(f"{self.base_url}/logStreams/{stream_id}/overrides/{override_id}", json=payload)
        data = self._handle_response(response)
        return LogStreamOverride.from_dict(data)
    
    def delete_log_stream_override(self, stream_id: str, override_id: str) -> bool:
        """Delete a log stream override"""
        response = self.session.delete(f"{self.base_url}/logStreams/{stream_id}/overrides/{override_id}")
        self._handle_response(response)
        return True

class LogManager:
    """High-level log management interface"""
    
    def __init__(self, api_key: str):
        self.api = RenderLogAPI(api_key)
        self.console = Console()
    
    def get_recent_logs(self, 
                       resource_ids: List[str], 
                       hours: int = 1,
                       level: Optional[LogLevel] = None) -> List[LogEntry]:
        """Get recent logs from the last N hours"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time.replace(hour=end_time.hour - hours)
        
        data = self.api.list_logs(
            resource_ids=resource_ids,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            level=level
        )
        
        return [LogEntry.from_dict(log) for log in data.get("logs", [])]
    
    def stream_logs_sync(self, 
                        resource_ids: List[str],
                        callback: callable) -> None:
        """Stream logs synchronously with a callback function"""
        asyncio.run(self._stream_logs_async(resource_ids, callback))
    
    async def _stream_logs_async(self, 
                                resource_ids: List[str],
                                callback: callable) -> None:
        """Internal async log streaming"""
        try:
            async for log_entry in self.api.subscribe_to_logs(resource_ids):
                callback(log_entry)
        except KeyboardInterrupt:
            self.console.print("\n👋 Log streaming stopped", style="yellow")
        except Exception as e:
            self.console.print(f"❌ Streaming error: {e}", style="red")
    
    def create_stream_for_service(self, 
                                 service_id: str,
                                 name: str,
                                 level_filter: Optional[LogLevel] = None) -> LogStream:
        """Create a log stream for a service with optional level filtering"""
        filters = {}
        if level_filter:
            filters["level"] = level_filter.value
            
        return self.api.create_log_stream(
            name=name,
            service_id=service_id,
            filters=filters
        )
    
    def get_available_log_labels(self, resource_ids: List[str]) -> Dict[str, List[str]]:
        """Get all available log labels and their possible values"""
        # Common log label keys to check
        common_labels = ["level", "source", "component", "environment", "version"]
        
        labels = {}
        for label_key in common_labels:
            try:
                values = self.api.list_log_label_values(resource_ids, label_key)
                if values:
                    labels[label_key] = values
            except:
                continue
                
        return labels