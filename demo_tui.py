#!/usr/bin/env python3
"""
Demo script for r4r TUI Log Management
Shows how to use the new log management features
"""

import os
import sys
from pathlib import Path

# Add src to path for demo
sys.path.insert(0, str(Path(__file__).parent / "src"))

from r4r.log_manager import LogManager, LogLevel, LogEntry
from r4r.tui import launch_log_viewer
from rich.console import Console
from rich.panel import Panel

console = Console()

def demo_log_manager():
    """Demo the LogManager functionality"""
    
    console.print(Panel.fit(
        "🚀 r4r Log Management Demo\n\n"
        "This demo shows how to use the new log management features.\n"
        "Note: You'll need a valid Render API key to see real data.",
        title="Demo"
    ))
    
    # Check for API key
    api_key = os.getenv("RENDER_API_KEY")
    if not api_key:
        console.print("❌ No RENDER_API_KEY environment variable found", style="red")
        console.print("💡 Set your API key: export RENDER_API_KEY=your_key_here", style="dim")
        return
    
    try:
        # Initialize log manager
        console.print("📡 Initializing Log Manager...", style="cyan")
        log_manager = LogManager(api_key)
        
        # Demo: List log streams
        console.print("\n📋 Listing existing log streams...", style="cyan")
        streams = log_manager.api.list_log_streams()
        
        if streams:
            console.print(f"✅ Found {len(streams)} log streams", style="green")
            for stream in streams[:3]:  # Show first 3
                console.print(f"   • {stream.name} ({stream.id[:8]}...)")
        else:
            console.print("ℹ️  No log streams found", style="yellow")
        
        # Demo: Create a sample log stream
        console.print("\n🔧 Creating demo log stream...", style="cyan")
        try:
            # Note: This will fail without a real service ID
            demo_stream = log_manager.api.create_log_stream(
                name="r4r-demo-stream",
                service_id="demo-service",  # This would be a real service ID
                filters={"level": "info"},
                enabled=True
            )
            console.print(f"✅ Created demo stream: {demo_stream.id}", style="green")
        except Exception as e:
            console.print(f"ℹ️  Demo stream creation skipped: {str(e)[:50]}...", style="yellow")
        
        # Demo: Show log levels
        console.print("\n🏷️  Available log levels:", style="cyan")
        for level in LogLevel:
            console.print(f"   • {level.value}")
        
        # Demo: Mock log entries
        console.print("\n📝 Sample log entry format:", style="cyan")
        sample_log = LogEntry(
            timestamp="2024-01-15T10:30:00Z",
            level="info",
            message="Application started successfully",
            source="web-server",
            service_id="srv-example123",
            resource_id="res-web456",
            labels={"environment": "production", "version": "1.2.3"}
        )
        
        console.print(f"   Timestamp: {sample_log.timestamp}")
        console.print(f"   Level: {sample_log.level}")
        console.print(f"   Message: {sample_log.message}")
        console.print(f"   Source: {sample_log.source}")
        console.print(f"   Labels: {sample_log.labels}")
        
        console.print("\n🎯 Demo completed!", style="green")
        console.print("💡 To see the TUI in action, run:", style="dim")
        console.print("   r4r tui --service your-service-name", style="dim")
        
    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")
        console.print("💡 Make sure your API key is valid and you have access to Render services", style="dim")

def demo_tui_features():
    """Demo TUI features (mock data)"""
    
    console.print(Panel.fit(
        "🖥️  TUI Features Demo\n\n"
        "The TUI includes these features:\n"
        "• Real-time log streaming with WebSocket\n"
        "• Advanced filtering by level, source, and search\n"
        "• Log stream management interface\n"
        "• Export and statistics\n"
        "• Keyboard shortcuts for efficiency\n\n"
        "Launch with: r4r tui",
        title="TUI Features"
    ))

def main():
    """Main demo function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "tui":
        demo_tui_features()
    else:
        demo_log_manager()

if __name__ == "__main__":
    main()