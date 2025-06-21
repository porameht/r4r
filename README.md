# r4r - Render CLI

CLI tool for managing Render deployments.

## Installation

```bash
# Quick install
curl -sSL https://raw.githubusercontent.com/porameht/r4r/main/install.sh | bash

# Or with uv/pip
uv tool install r4r
pip install r4r
```

## Quick Start

```bash
r4r auth login              # Login with API key
r4r services list           # List services
r4r services deploy <name>  # Deploy service
r4r logs view <name>        # View logs
```

## Commands

### Authentication
- `r4r auth login` - Login with API key
- `r4r auth whoami` - Show current user
- `r4r auth logout` - Logout

### Services
- `r4r services list` - List all services
- `r4r services info <name>` - Show service details
- `r4r services deploy <name>` - Deploy service
- `r4r services scale <name> <count>` - Scale instances
- `r4r services restart <name>` - Restart service

### Logs
- `r4r logs view <name>` - View logs
- `r4r logs stream <name>` - Stream real-time logs
- `r4r logs events <name>` - View events

### Jobs
- `r4r jobs create <name> <cmd>` - Create job
- `r4r jobs list <name>` - List jobs
- `r4r jobs status <id>` - Check job status

### Projects
- `r4r projects list` - List projects
- `r4r projects info <name>` - Project details
- `r4r projects services <name>` - Project services

## API Key Setup

```bash
# Interactive
r4r auth login

# Direct
r4r auth login --key <your-key>

# Environment variable
export RENDER_API_KEY=<your-key>
```

Get your API key from [Render Dashboard](https://dashboard.render.com/u/settings#api-keys)

## Help

```bash
r4r --help              # General help
r4r <command> --help    # Command help
```

## Development

```bash
git clone https://github.com/porameht/r4r.git
cd r4r
uv sync
uv run r4r --help
```

## License

MIT