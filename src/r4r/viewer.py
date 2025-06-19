#!/usr/bin/env python3
"""
r4r TUI (Text User Interface) for Log Streaming
Interactive log viewer with real-time streaming capabilities
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Log,
    Pretty,
    Select,
    Static,
    Switch,
    TabPane,
    Tabs,
)

from .api import LogEntry, RenderService


class LogFilterPanel(Static):
    """Panel for configuring log filters"""

    def __init__(self):
        super().__init__()
        self.filters = {"level": None, "source": None, "search": ""}

    def compose(self) -> ComposeResult:
        yield Label("🔍 Log Filters", classes="filter-title")

        with Horizontal():
            yield Label("Level:", classes="filter-label")
            yield Select(
                options=[
                    ("All", None),
                    ("Debug", "debug"),
                    ("Info", "info"),
                    ("Warn", "warn"),
                    ("Error", "error"),
                    ("Fatal", "fatal"),
                ],
                value=None,
                id="level-filter",
            )

        with Horizontal():
            yield Label("Search:", classes="filter-label")
            yield Input(placeholder="Filter messages...", id="search-filter")

        with Horizontal():
            yield Button("Apply Filters", id="apply-filters", variant="primary")
            yield Button("Clear", id="clear-filters", variant="default")


class LogStreamPanel(Static):
    """Panel for managing log streams"""

    def compose(self) -> ComposeResult:
        yield Label("📡 Log Streams", classes="panel-title")

        with Horizontal():
            yield Button("➕ New Stream", id="new-stream", variant="success")
            yield Button("🔄 Refresh", id="refresh-streams", variant="default")

        yield DataTable(id="streams-table", zebra_stripes=True)


class LogViewerApp(App):
    """Main TUI application for log viewing"""

    CSS = """
    .filter-title {
        text-style: bold;
        color: $accent;
        margin: 1;
    }
    
    .panel-title {
        text-style: bold;
        color: $primary;
        margin: 1;
    }
    
    .filter-label {
        width: 8;
        padding: 1;
    }
    
    .log-entry {
        margin: 0 1;
        padding: 0 1;
    }
    
    .log-error {
        background: $error;
        color: $text;
    }
    
    .log-warn {
        background: $warning;
        color: $text;
    }
    
    .log-info {
        background: $surface;
        color: $text;
    }
    
    .log-debug {
        background: $boost;
        color: $text;
    }
    
    .status-bar {
        background: $primary;
        color: $text;
        height: 1;
    }
    
    .sidebar {
        width: 30;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("c", "clear_logs", "Clear"),
        Binding("f", "toggle_follow", "Follow"),
        Binding("s", "save_logs", "Save"),
        Binding("ctrl+f", "focus_search", "Search"),
    ]

    def __init__(self, render_service: RenderService, resource_ids: List[str]):
        super().__init__()
        self.render_service = render_service
        self.resource_ids = resource_ids
        self.following = False
        self.log_count = 0
        self.filtered_count = 0
        self.current_filters: Dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal():
            # Sidebar for filters and controls
            with Vertical(classes="sidebar"):
                yield LogFilterPanel()

                with Collapsible(title="🎛️ Controls", collapsed=False):
                    yield Switch(id="follow-switch", value=False)
                    yield Label("Follow logs")

                    yield Switch(id="auto-scroll", value=True)
                    yield Label("Auto-scroll")

                    with Horizontal():
                        yield Button("📥 Export", id="export-logs", variant="default")
                        yield Button("🗑️ Clear", id="clear-logs", variant="warning")

                yield LogStreamPanel()

            # Main content area
            with Vertical():
                # Tabs for different views
                with Tabs():
                    with TabPane("Live Logs", id="live-logs"):
                        yield Log(
                            id="log-display",
                            highlight=True,
                            auto_scroll=True,
                            max_lines=10000,
                        )

                    with TabPane("Log Streams", id="streams-tab"):
                        yield DataTable(id="streams-detail-table")

                    with TabPane("Statistics", id="stats-tab"):
                        yield Pretty({}, id="stats-display")

        # Status bar
        with Horizontal(classes="status-bar"):
            yield Static(f"📊 Logs: {self.log_count}", id="log-count")
            yield Static(f"🔍 Filtered: {self.filtered_count}", id="filtered-count")
            yield Static("⏸️ Paused", id="follow-status")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted"""
        self.title = "r4r Log Viewer"
        self.sub_title = f"Streaming {len(self.resource_ids)} resources"

        # Setup log display
        log_widget = self.query_one("#log-display", Log)
        log_widget.border_title = "📝 Live Logs"

        # Setup streams table
        self._setup_streams_table()

        # Load initial data
        self._load_recent_logs()
        self._load_log_streams()

    def _setup_streams_table(self) -> None:
        """Setup the log streams data table"""
        table = self.query_one("#streams-table", DataTable)
        table.add_columns("Name", "Service", "Status", "Created")

        detail_table = self.query_one("#streams-detail-table", DataTable)
        detail_table.add_columns(
            "ID", "Name", "Service ID", "Filters", "Enabled", "Created"
        )

    def _load_recent_logs(self) -> None:
        """Load recent logs to populate the display"""
        try:
            recent_logs = self.render_service.get_recent_logs(
                resource_ids=self.resource_ids, hours=1
            )

            log_widget = self.query_one("#log-display", Log)

            for log_entry in recent_logs[-50:]:  # Show last 50 logs
                self._display_log_entry(log_entry, log_widget)

            self.log_count = len(recent_logs)
            self._update_status()

        except Exception as e:
            self._show_error(f"Failed to load recent logs: {e}")

    def _load_log_streams(self) -> None:
        """Load log streams data"""
        try:
            streams = self.render_service.api.list_log_streams()

            # Update main streams table
            table = self.query_one("#streams-table", DataTable)
            table.clear()

            for stream in streams:
                table.add_row(
                    stream.name,
                    stream.service_id[:12] + "...",
                    "✅ Enabled" if stream.enabled else "❌ Disabled",
                    stream.created_at[:10],
                )

            # Update detailed streams table
            detail_table = self.query_one("#streams-detail-table", DataTable)
            detail_table.clear()

            for stream in streams:
                filters_str = ", ".join([f"{k}:{v}" for k, v in stream.filters.items()])
                detail_table.add_row(
                    stream.id[:8] + "...",
                    stream.name,
                    stream.service_id[:12] + "...",
                    filters_str[:30] + "..." if len(filters_str) > 30 else filters_str,
                    "✅" if stream.enabled else "❌",
                    stream.created_at[:10],
                )

        except Exception as e:
            self._show_error(f"Failed to load log streams: {e}")

    def _display_log_entry(self, log_entry: LogEntry, log_widget: Log) -> None:
        """Display a single log entry in the log widget"""
        # Format timestamp
        try:
            dt = datetime.fromisoformat(log_entry.timestamp.replace("Z", "+00:00"))
            timestamp = dt.strftime("%H:%M:%S")
        except (ValueError, TypeError):
            timestamp = log_entry.timestamp[:8]

        # Color based on log level
        level_colors = {
            "error": "red",
            "warn": "yellow",
            "warning": "yellow",
            "info": "green",
            "debug": "blue",
            "fatal": "bright_red",
        }

        level_color = level_colors.get(log_entry.level.lower(), "white")
        level_badge = f"[{level_color}]{log_entry.level.upper():5}[/{level_color}]"

        # Source info
        source = (
            log_entry.source[:10] + "..."
            if len(log_entry.source) > 10
            else log_entry.source
        )
        source_info = f"[dim]{source}[/dim]"

        # Message
        message = log_entry.message.strip()

        # Apply filters
        if self._should_filter_log(log_entry):
            return

        # Format complete log line
        log_line = f"[dim]{timestamp}[/dim] {level_badge} {source_info} {message}"

        log_widget.write(log_line)
        self.filtered_count += 1

    def _should_filter_log(self, log_entry: LogEntry) -> bool:
        """Check if log entry should be filtered out"""
        # Level filter
        if (
            self.current_filters.get("level")
            and log_entry.level != self.current_filters["level"]
        ):
            return True

        # Search filter
        search_term = self.current_filters.get("search", "").lower()
        if search_term and search_term not in log_entry.message.lower():
            return True

        return False

    def _show_error(self, message: str) -> None:
        """Display error message"""
        log_widget = self.query_one("#log-display", Log)
        log_widget.write(f"[red]❌ Error: {message}[/red]")

    def _update_status(self) -> None:
        """Update status bar information"""
        self.query_one("#log-count", Static).update(f"📊 Logs: {self.log_count}")
        self.query_one("#filtered-count", Static).update(
            f"🔍 Filtered: {self.filtered_count}"
        )

        status_text = "▶️ Following" if self.following else "⏸️ Paused"
        self.query_one("#follow-status", Static).update(status_text)

    async def _start_log_streaming(self) -> None:
        """Start real-time log streaming"""
        if self.following:
            return

        self.following = True
        self._update_status()

        log_widget = self.query_one("#log-display", Log)

        try:
            async for log_entry in self.render_service.api.subscribe_to_logs(
                self.resource_ids
            ):
                if not self.following:
                    break

                self._display_log_entry(log_entry, log_widget)
                self.log_count += 1

                # Update status periodically
                if self.log_count % 10 == 0:
                    self._update_status()

        except Exception as e:
            self._show_error(f"Streaming error: {e}")
        finally:
            self.following = False
            self._update_status()

    def _stop_log_streaming(self) -> None:
        """Stop real-time log streaming"""
        self.following = False
        self._update_status()

    # Event handlers
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        if event.button.id == "apply-filters":
            self._apply_filters()
        elif event.button.id == "clear-filters":
            self._clear_filters()
        elif event.button.id == "clear-logs":
            self.action_clear_logs()
        elif event.button.id == "export-logs":
            self._export_logs()
        elif event.button.id == "refresh-streams":
            self._load_log_streams()
        elif event.button.id == "new-stream":
            self._create_new_stream()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggle events"""
        if event.switch.id == "follow-switch":
            if event.value and not self.following:
                asyncio.create_task(self._start_log_streaming())
            elif not event.value and self.following:
                self._stop_log_streaming()
        elif event.switch.id == "auto-scroll":
            log_widget = self.query_one("#log-display", Log)
            log_widget.auto_scroll = event.value

    def _apply_filters(self) -> None:
        """Apply current filter settings"""
        level_select = self.query_one("#level-filter", Select)
        search_input = self.query_one("#search-filter", Input)

        self.current_filters = {
            "level": level_select.value,
            "search": search_input.value,
        }

        # Clear current display and reload with filters
        log_widget = self.query_one("#log-display", Log)
        log_widget.clear()
        self.filtered_count = 0

        self._load_recent_logs()

    def _clear_filters(self) -> None:
        """Clear all filters"""
        self.query_one("#level-filter", Select).value = None
        self.query_one("#search-filter", Input).value = ""
        self.current_filters = {}

        # Reload logs without filters
        log_widget = self.query_one("#log-display", Log)
        log_widget.clear()
        self.filtered_count = 0
        self._load_recent_logs()

    def _export_logs(self) -> None:
        """Export current logs to file"""
        # This would implement log export functionality
        self._show_error("Export functionality not yet implemented")

    def _create_new_stream(self) -> None:
        """Create a new log stream"""
        # This would open a dialog for creating new streams
        self._show_error("Stream creation not yet implemented")

    # Action methods
    async def action_quit(self) -> None:
        """Quit the application"""
        self._stop_log_streaming()
        self.exit()

    def action_refresh(self) -> None:
        """Refresh log data"""
        self._load_recent_logs()
        self._load_log_streams()

    def action_clear_logs(self) -> None:
        """Clear the log display"""
        log_widget = self.query_one("#log-display", Log)
        log_widget.clear()
        self.log_count = 0
        self.filtered_count = 0
        self._update_status()

    def action_toggle_follow(self) -> None:
        """Toggle log following"""
        follow_switch = self.query_one("#follow-switch", Switch)
        follow_switch.value = not follow_switch.value

    def action_save_logs(self) -> None:
        """Save logs to file"""
        self._export_logs()

    def action_focus_search(self) -> None:
        """Focus the search input"""
        self.query_one("#search-filter", Input).focus()


# Helper functions for launching TUI
def launch_log_viewer(render_service: RenderService, resource_ids: List[str]) -> None:
    """Launch the TUI log viewer"""
    app = LogViewerApp(render_service, resource_ids)
    app.run()


def launch_log_viewer_with_service(
    render_service: RenderService, service_id: str
) -> None:
    """Launch log viewer for a specific service"""
    # For now, use service_id as resource_id
    # In a real implementation, you'd fetch the actual resource IDs for the service
    launch_log_viewer(render_service, [service_id])
