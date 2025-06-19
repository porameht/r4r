# r4r - Super Easy Render CLI

🚀 The simplest and most powerful way to manage your Render deployments with advanced features.

## Features

- **🚀 Complete Service Management**: Deploy, rebuild, and manage all your Render services
- **⚡ One-Off Jobs**: Create and monitor background jobs with real-time status
- **📊 Detailed Information**: Rich service details, deployment history, and logs
- **🔍 Advanced Log Management**: TUI log viewer with real-time streaming, filtering, and log stream management
- **🔐 Secure Authentication**: API key management with user information
- **🎨 Beautiful UI**: Rich terminal interface with progress indicators
- **⚡ Fast**: Built with modern Python tooling (uv, typer, rich)
- **🌐 Network Resilient**: Advanced error handling and retry logic

## Quick Install

```bash
# One-line installation
curl -sSL https://raw.githubusercontent.com/porameht/r4r/main/install.sh | bash

# Or with wget
wget -qO- https://raw.githubusercontent.com/porameht/r4r/main/install.sh | bash
```

## Manual Install

```bash
# Using uv (recommended)
uv tool install r4r

# Using pip
pip install r4r
```

## Quick Start

```bash
# 1. Login with your Render API key
r4r login

# 2. List your services
r4r list

# 3. Deploy a service
r4r deploy myapp

# 4. Deploy with cache clear (rebuild)
r4r deploy myapp --clear
```

## Commands

### Authentication & User Management
| Command | Description | Example |
|---------|-------------|---------|
| `r4r login` | Login with API key | `r4r login --key xxx` |
| `r4r whoami` | Show current user info | `r4r whoami` |
| `r4r logout` | Logout and remove credentials | `r4r logout` |

### Service Management
| Command | Description | Example |
|---------|-------------|---------|
| `r4r list` | List all services | `r4r list --detailed` |
| `r4r info <name>` | Show detailed service info | `r4r info myapp` |
| `r4r deploy <name>` | Deploy service | `r4r deploy myapp` |
| `r4r deploy <name> --clear` | Deploy with cache clear | `r4r deploy myapp -c` |
| `r4r rebuild <name>` | Clear cache + deploy | `r4r rebuild myapp` |

### Deployments & Logs
| Command | Description | Example |
|---------|-------------|---------|
| `r4r deploys <name>` | List recent deployments | `r4r deploys myapp` |
| `r4r logs <name>` | View service logs | `r4r logs myapp --lines 50` |
| `r4r logs <name> --tui` | Interactive TUI log viewer | `r4r logs myapp --tui` |
| `r4r tui` | Launch interactive TUI | `r4r tui --service myapp` |

### Log Stream Management
| Command | Description | Example |
|---------|-------------|---------|
| `r4r log-streams list` | List all log streams | `r4r log-streams list` |
| `r4r log-streams create` | Create new log stream | `r4r log-streams create --name mystream --service srv-123` |
| `r4r log-streams update` | Update log stream | `r4r log-streams update --id stream-123 --level error` |
| `r4r log-streams delete` | Delete log stream | `r4r log-streams delete --id stream-123` |
| `r4r stream-overrides list` | List stream overrides | `r4r stream-overrides list --stream stream-123` |

### One-Off Jobs
| Command | Description | Example |
|---------|-------------|---------|
| `r4r job <name> <command>` | Create and run a job | `r4r job myapp "npm run migrate"` |
| `r4r jobs <name>` | List recent jobs | `r4r jobs myapp` |
| `r4r status <job_id>` | Get job status | `r4r status job-abc123` |

## Options

### Global Options
- `--help`: Show help information
- `--version`: Show version information

### Command-Specific Options
- `--clear, -c`: Clear cache and rebuild
- `--yes, -y`: Skip confirmation prompts
- `--key, -k`: Provide API key directly
- `--detailed, -d`: Show detailed information
- `--lines, -n`: Number of log lines to show
- `--limit, -l`: Limit number of results
- `--wait, -w`: Wait for job completion
- `--follow, -f`: Follow log output (streaming)
- `--type, -t`: Filter by service type
- `--plan, -p`: Specify plan for jobs

## Examples

### Basic Usage
```bash
# Login and check user info
r4r login --key rnd_xxx...
r4r whoami

# List all services with details
r4r list --detailed

# Get detailed info about a service
r4r info myapp

# Deploy with confirmation
r4r deploy myapp

# Deploy and clear cache without confirmation
r4r deploy myapp --clear --yes

# Rebuild (shorthand for --clear)
r4r rebuild myapp
```

### Advanced Features
```bash
# Interactive TUI log viewer (recommended)
r4r tui                              # Launch with service selection
r4r tui --service myapp             # Launch for specific service
r4r logs myapp --tui                # Launch TUI from logs command

# Advanced log viewing
r4r logs myapp --lines 100 --level error
r4r logs myapp --follow --export logs.txt
r4r logs myapp --tui                # Interactive viewer

# Log stream management
r4r log-streams list
r4r log-streams create --name "error-logs" --service myapp --level error
r4r log-streams update --id stream-123 --enabled

# List recent deployments
r4r deploys myapp --limit 5

# Create and run a job
r4r job myapp "rails db:migrate"
r4r job myapp "npm run build" --wait  # Wait for completion

# Monitor jobs
r4r jobs myapp
r4r status job-abc123

# Filter services by type
r4r list --type web_service
r4r list --type background_worker
```

## API Key Setup

### Method 1: Interactive Login
1. Get your API key from [Render Dashboard](https://dashboard.render.com/u/settings#api-keys)
2. Run `r4r login` and paste your key when prompted
3. Verify with `r4r whoami`

### Method 2: Direct Login
```bash
r4r login --key rnd_xxx...
```

### Method 3: Environment Variable
```bash
export RENDER_API_KEY=rnd_xxx...
r4r list  # Will use the environment variable
```

### API Key Retrieval
You can retrieve and manage your API key through multiple methods:
- Via CLI: `r4r login --key your_api_key`
- Via Environment Variable: `export RENDER_API_KEY=your_key`
- Via Interactive Mode: `r4r login` and enter key when prompted
- View current key: `r4r whoami` (shows masked version)

## Development

```bash
# Clone the repo
git clone https://github.com/porameht/r4r.git
cd r4r

# Install in development mode
uv sync
uv run r4r --help

# Run tests
uv run pytest

# Build
uv build
```


## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions:
- Create an issue on [GitHub](https://github.com/porameht/r4r/issues)
- Check the documentation
- Make sure your API key has the correct permissions

---

**Need help?**: Create an issue on GitHub or check your API key permissions