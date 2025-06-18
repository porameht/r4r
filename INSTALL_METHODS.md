# r4r Installation Methods

This document provides comprehensive installation methods for r4r (Render CLI) for different use cases and environments.

## 🚀 Quick Install (Recommended)

The fastest way to get started:

```bash
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install.sh | bash
```

This script:
- Auto-detects your system and Python version
- Installs uv if not present (fastest package manager)
- Falls back to pip if uv installation fails
- Verifies installation and provides setup guidance
- Offers interactive API key setup

## 📦 Installation Methods

### 1. Using uv (Recommended - Fastest)

```bash
# Install uv first (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.cargo/env

# Install r4r
uv tool install r4r
```

**Advantages:**
- ⚡ Fastest installation and dependency resolution
- 🔒 Isolated environments by default
- 🆕 Modern Python package management
- 📦 Better caching and performance

### 2. Using pip (Traditional)

```bash
# Install for current user
pip install r4r --user

# Or system-wide (requires sudo on Linux/macOS)
pip install r4r
```

**Use pip when:**
- uv is not available or compatible
- Working in existing pip-based workflows
- Corporate environments with pip restrictions

### 3. From Source (Development)

```bash
# Clone the repository
git clone https://github.com/your-username/r4r.git
cd r4r

# Install with uv
uv tool install .

# Or with pip
pip install . --user
```

### 4. URL-based Installation (Python)

For environments where you can run Python but don't have git:

```bash
python3 <(curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install-url.py)
```

This Python script:
- Checks system requirements
- Auto-detects available package managers
- Downloads and installs r4r
- Provides comprehensive error handling

## 🛠 Specialized Installation Scripts

### For pip-only environments

Use the dedicated pip installer:

```bash
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install-pip.sh | bash
```

Options:
```bash
# System-wide installation
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install-pip.sh | bash -s -- --system

# Upgrade existing installation
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install-pip.sh | bash -s -- --upgrade

# Verbose output
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install-pip.sh | bash -s -- --verbose
```

### For offline/air-gapped environments

1. Download the distribution files from the [releases page](https://github.com/your-username/r4r/releases)
2. Transfer to target system
3. Install locally:

```bash
# Using uv
uv tool install r4r-*.whl

# Using pip
pip install r4r-*.whl --user
```

## 🐳 Docker Installation

```dockerfile
# Using uv in Docker
FROM python:3.11-slim
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"
RUN uv tool install r4r

# Using pip in Docker
FROM python:3.11-slim
RUN pip install r4r
```

## 📱 Platform-Specific Instructions

### macOS

```bash
# Using Homebrew (if available as a formula)
brew install r4r

# Using MacPorts
port install py311-r4r

# Standard installation
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install.sh | bash
```

### Linux

```bash
# Ubuntu/Debian
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install.sh | bash

# RHEL/CentOS/Fedora
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install.sh | bash

# Arch Linux (if available in AUR)
yay -S r4r

# Alpine Linux
apk add --no-cache python3 py3-pip
pip install r4r
```

### Windows

```powershell
# Using Python
python -m pip install r4r

# Using Windows Subsystem for Linux (WSL)
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install.sh | bash

# Using PowerShell with Python
Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile "get-pip.py"
python get-pip.py
python -m pip install r4r
```

## 🔧 Development Installation

For contributors and developers:

```bash
# Clone and setup development environment
git clone https://github.com/your-username/r4r.git
cd r4r

# Using Makefile (recommended)
make install

# Manual setup with uv
uv sync --dev
uv tool install --editable .

# Manual setup with pip
pip install -e . --user
```

Development commands:
```bash
make dev        # Quick development setup
make test       # Run tests
make build      # Build development version
make prod       # Build production version
make clean      # Clean build artifacts
```

## 🚨 Troubleshooting

### Common Issues

**r4r command not found:**
```bash
# Check if r4r is installed
python3 -c "import r4r; print('✅ r4r installed')"

# Find r4r location
find ~ -name "r4r" -type f 2>/dev/null

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

**Permission denied:**
```bash
# Use user installation
pip install r4r --user

# Or fix permissions (Linux/macOS)
sudo chown -R $USER ~/.local/
```

**Python version too old:**
```bash
# Check Python version
python3 --version

# Install newer Python
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
# Windows: Download from python.org
```

**Network connectivity issues:**
```bash
# Test connectivity
curl -I https://pypi.org

# Use proxy if needed
pip install r4r --proxy http://proxy.company.com:8080
```

### Installation Verification

After installation, verify r4r is working:

```bash
# Check version
r4r --version

# Check help
r4r --help

# Test basic functionality
r4r login --help
```

## 🔄 Updating r4r

### Using uv
```bash
uv tool upgrade r4r
```

### Using pip
```bash
pip install r4r --upgrade --user
```

### Force reinstall
```bash
# With uv
uv tool uninstall r4r
uv tool install r4r

# With pip
pip uninstall r4r
pip install r4r --user
```

## 🗑 Uninstalling r4r

### Using uv
```bash
uv tool uninstall r4r
```

### Using pip
```bash
pip uninstall r4r
```

### Remove configuration
```bash
# Remove config directory
rm -rf ~/.r4r/
```

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, Windows
- **Memory**: 15MB+ available RAM (20MB+ for TUI mode)
- **Storage**: 8MB+ available disk space
- **Network**: Internet connection for installation and API calls
- **Terminal**: Modern terminal with Unicode support (for TUI features)

### TUI Requirements
The interactive TUI log viewer requires:
- **textual**: 0.44.0 or higher (installed automatically)
- **websockets**: 11.0.0 or higher (installed automatically)
- **Modern terminal**: Support for 256 colors and Unicode characters

## 🆘 Getting Help

If you encounter issues:

1. **Check the troubleshooting section above**
2. **Search existing issues**: [GitHub Issues](https://github.com/your-username/r4r/issues)
3. **Create a new issue** with:
   - Your operating system and Python version
   - Installation method attempted
   - Full error message
   - Output of `python3 --version` and `pip --version`

## 📚 Additional Resources

- [Full Documentation](README.md)
- [API Reference](https://docs.render.com/api)
- [Render Dashboard](https://dashboard.render.com/)
- [Get API Key](https://dashboard.render.com/u/settings#api-keys)

---

**Note**: Replace `your-username` with the actual GitHub username/organization in all URLs above.