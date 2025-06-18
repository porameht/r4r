# Advanced Log Management with r4r

r4r now includes comprehensive log management capabilities with an interactive TUI (Text User Interface) for real-time log streaming, filtering, and management.

## 🎯 Quick Start

### Launch Interactive TUI Log Viewer
```bash
# Launch TUI with service selection
r4r tui

# Launch TUI for specific service
r4r tui --service myapp

# Launch TUI from logs command
r4r logs myapp --tui
```

### Basic Log Viewing
```bash
# View recent logs
r4r logs myapp

# View logs with filters
r4r logs myapp --level error --lines 200

# Follow logs in real-time
r4r logs myapp --follow

# Export logs to file
r4r logs myapp --export myapp-logs.txt
```

## 🖥️ TUI Features

The interactive TUI provides a rich interface for log management:

### Main Interface
- **Live Logs Tab**: Real-time log streaming with filtering
- **Log Streams Tab**: Manage log streams and configurations
- **Statistics Tab**: Log analytics and metrics

### Key Features
- ⚡ **Real-time Streaming**: WebSocket-based log streaming
- 🔍 **Advanced Filtering**: Filter by log level, source, and search terms
- 📊 **Statistics**: Log count, filtering metrics, and status
- 💾 **Export Functionality**: Save logs to files
- 🎨 **Syntax Highlighting**: Color-coded logs by level and source
- ⌨️ **Keyboard Shortcuts**: Efficient navigation and control

### Keyboard Shortcuts
- `q` - Quit application
- `r` - Refresh logs and streams
- `c` - Clear log display
- `f` - Toggle follow mode
- `s` - Save/export logs
- `Ctrl+F` - Focus search input

## 📡 Log Stream Management

### Understanding Log Streams
Log streams are configurable filters that allow you to:
- Create custom views of your logs
- Set up persistent filtering rules
- Apply different settings for different resources
- Subscribe to specific types of log events

### Managing Log Streams

#### List All Log Streams
```bash
r4r log-streams list

# Filter by service
r4r log-streams list --service srv-123
```

#### Create Log Stream
```bash
# Create stream with level filter
r4r log-streams create \
  --name "error-logs" \
  --service srv-123 \
  --level error

# Create stream with multiple filters (via API)
r4r log-streams create \
  --name "production-warnings" \
  --service srv-123 \
  --level warn
```

#### Update Log Stream
```bash
# Update stream settings
r4r log-streams update \
  --id stream-456 \
  --name "updated-name" \
  --level info \
  --enabled

# Disable stream
r4r log-streams update \
  --id stream-456 \
  --disabled
```

#### Delete Log Stream
```bash
r4r log-streams delete --id stream-456
```

## 🎛️ Log Stream Overrides

Stream overrides allow you to customize log stream behavior for specific resources.

### Managing Overrides

#### List Overrides
```bash
r4r stream-overrides list --stream stream-123
```

#### Create Override
```bash
r4r stream-overrides create \
  --stream stream-123 \
  --resource resource-456 \
  --overrides '{"level": "debug", "source": "api"}'
```

#### Update Override
```bash
r4r stream-overrides update \
  --stream stream-123 \
  --id override-789 \
  --overrides '{"level": "error", "enabled": true}'
```

#### Delete Override
```bash
r4r stream-overrides delete \
  --stream stream-123 \
  --id override-789
```

## 🔧 Advanced Log API Features

### Supported Log Levels
- `debug` - Detailed debugging information
- `info` - General informational messages
- `warn` - Warning conditions
- `error` - Error conditions
- `fatal` - Critical error conditions

### Log Entry Structure
Each log entry contains:
- **Timestamp**: ISO 8601 formatted timestamp
- **Level**: Log severity level
- **Message**: The actual log message
- **Source**: Component or service that generated the log
- **Service ID**: Associated Render service
- **Resource ID**: Specific resource within the service
- **Labels**: Key-value pairs for additional metadata

### Real-time Streaming
The TUI uses WebSocket connections for real-time log streaming:
- Automatic reconnection on connection loss
- Efficient bandwidth usage with incremental updates
- Support for multiple resource monitoring
- Graceful handling of large log volumes

## 📊 Log Analytics

### Available Metrics
- Total log count
- Filtered log count
- Logs per minute rate
- Error rate trends
- Most active sources

### Export Formats
- Plain text with timestamps
- JSON structured format
- CSV for spreadsheet analysis

## 🛠️ Integration Examples

### CI/CD Pipeline Monitoring
```bash
# Monitor deployment logs during CI/CD
r4r logs myapp --follow --level info &
PID=$!

# Run your deployment
./deploy.sh

# Stop monitoring
kill $PID
```

### Error Monitoring
```bash
# Create error-only stream for monitoring
r4r log-streams create \
  --name "production-errors" \
  --service srv-production \
  --level error

# Watch errors in TUI
r4r tui --service srv-production
```

### Log Analysis
```bash
# Export logs for analysis
r4r logs myapp \
  --level error \
  --lines 1000 \
  --export error-analysis.txt

# Analyze with external tools
grep "database" error-analysis.txt
```

## 🔍 Troubleshooting

### Common Issues

**TUI Not Loading**
```bash
# Install textual dependency
pip install textual>=0.44.0

# Check Python version (3.8+ required)
python3 --version
```

**WebSocket Connection Errors**
- Check internet connectivity
- Verify API key permissions
- Ensure firewall allows WebSocket connections

**Missing Logs**
- Verify service is running and generating logs
- Check log stream filters
- Confirm resource IDs are correct

### Debug Mode
```bash
# Enable verbose logging
export R4R_DEBUG=1
r4r logs myapp --tui
```

## 🚀 Performance Tips

### Efficient Log Streaming
- Use specific log level filters to reduce data volume
- Limit concurrent streams to 5-10 resources
- Use log streams for persistent filtering instead of CLI flags

### TUI Performance
- Close unused tabs when not needed
- Use search filters to reduce displayed logs
- Clear log display periodically for long-running sessions

### API Usage
- Cache log stream configurations
- Use pagination for large log queries
- Implement exponential backoff for failed requests

## 📚 API Reference

### Log Management API Endpoints

#### List Logs
```
GET /v1/logs
Parameters:
- resourceIds: comma-separated list of resource IDs
- startTime: ISO timestamp for log range start
- endTime: ISO timestamp for log range end
- level: filter by log level
- limit: maximum number of logs to return
```

#### Subscribe to Logs
```
WebSocket: wss://api.render.com/v1/logs/stream
Message Format:
{
  "action": "subscribe",
  "resourceIds": ["resource-123", "resource-456"]
}
```

#### Log Stream CRUD
```
GET    /v1/logStreams              # List streams
POST   /v1/logStreams              # Create stream
GET    /v1/logStreams/{id}         # Get stream
PUT    /v1/logStreams/{id}         # Update stream
DELETE /v1/logStreams/{id}         # Delete stream
```

#### Stream Overrides
```
GET    /v1/logStreams/{id}/overrides           # List overrides
POST   /v1/logStreams/{id}/overrides           # Create override
GET    /v1/logStreams/{id}/overrides/{oid}     # Get override
PUT    /v1/logStreams/{id}/overrides/{oid}     # Update override
DELETE /v1/logStreams/{id}/overrides/{oid}     # Delete override
```

## 🤝 Contributing

We welcome contributions to improve log management features:

1. **Bug Reports**: Report issues with log streaming or TUI
2. **Feature Requests**: Suggest new log analysis features
3. **Performance**: Help optimize log processing and display
4. **Documentation**: Improve this guide and examples

## 📄 License

This log management system is part of r4r and is licensed under MIT License.

---

For more information, visit the [main r4r documentation](README.md) or create an issue on [GitHub](https://github.com/your-username/r4r/issues).