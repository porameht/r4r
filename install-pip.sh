#!/bin/bash
# r4r - Pip Installation Script
# Simple installation using pip for systems where uv is not available

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${BLUE}🚀 $1${NC}"
}

# Options
USER_INSTALL=true
UPGRADE=false
VERBOSE=false

# Help function
show_help() {
    cat << EOF
r4r Pip Installation Script

Usage: $0 [OPTIONS]

OPTIONS:
    --system           Install system-wide (requires sudo)
    --upgrade          Upgrade if already installed
    --verbose          Verbose output
    -h, --help         Show this help message

EXAMPLES:
    $0                 # Install for current user
    $0 --system       # System-wide installation
    $0 --upgrade      # Upgrade existing installation

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --system)
            USER_INSTALL=false
            shift
            ;;
        --upgrade)
            UPGRADE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

log_header "r4r (Render CLI) - Pip Installer"
echo

# Check Python version
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_error "Python 3.8+ is required but not found"
    log_info "Please install Python from: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(python3 -c "import sys; print(sys.version_info >= (3, 8))") != "True" ]]; then
    log_error "Python 3.8+ required. You have $PYTHON_VERSION"
    exit 1
fi
log_success "Python $PYTHON_VERSION detected"

# Check pip
log_info "Checking pip..."
if ! command -v pip &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    log_error "pip not found. Installing pip..."
    python3 -m ensurepip --upgrade
    if ! python3 -m pip --version &> /dev/null; then
        log_error "Failed to install pip"
        exit 1
    fi
fi

# Use python3 -m pip for better compatibility
PIP_CMD="python3 -m pip"
PIP_VERSION=$($PIP_CMD --version | awk '{print $2}')
log_success "pip $PIP_VERSION available"

# Check if already installed
if $PIP_CMD list | grep -i "^r4r " &> /dev/null; then
    if [[ "$UPGRADE" == true ]]; then
        log_info "r4r already installed, upgrading..."
    else
        log_warning "r4r is already installed"
        echo "Use --upgrade to upgrade or --help for options"
        exit 0
    fi
fi

# Build installation command
INSTALL_ARGS=()

if [[ "$USER_INSTALL" == true ]]; then
    INSTALL_ARGS+=("--user")
    log_info "Installing for current user..."
else
    log_info "Installing system-wide (may require sudo)..."
fi

if [[ "$UPGRADE" == true ]]; then
    INSTALL_ARGS+=("--upgrade")
fi

if [[ "$VERBOSE" == true ]]; then
    INSTALL_ARGS+=("--verbose")
fi

# Check internet connectivity
log_info "Checking connectivity to PyPI..."
if ! curl -s --head --connect-timeout 5 https://pypi.org > /dev/null; then
    log_error "Cannot reach PyPI. Check your internet connection."
    exit 1
fi
log_success "PyPI is reachable"

# Install r4r
log_info "Installing r4r package..."
if [[ "$USER_INSTALL" == false && $EUID -ne 0 ]]; then
    log_warning "System installation requires root privileges"
    sudo $PIP_CMD install r4r "${INSTALL_ARGS[@]}"
else
    $PIP_CMD install r4r "${INSTALL_ARGS[@]}"
fi

# Verify installation
log_info "Verifying installation..."

# Check if r4r command is available
if command -v r4r &> /dev/null; then
    VERSION_OUTPUT=$(r4r --version 2>/dev/null || echo "version check failed")
    log_success "r4r installed successfully! $VERSION_OUTPUT"
    
    # Test basic functionality
    if r4r --help &> /dev/null; then
        log_success "r4r CLI is working correctly"
    else
        log_warning "r4r installed but may have issues"
    fi
else
    log_warning "r4r installed but not found in PATH"
    
    # Try to find the installation
    if [[ "$USER_INSTALL" == true ]]; then
        USER_BIN=$(python3 -m site --user-base)/bin
        if [[ -x "$USER_BIN/r4r" ]]; then
            log_info "Found r4r at: $USER_BIN/r4r"
            log_info "Add this to your shell profile:"
            echo -e "${YELLOW}export PATH=\"$USER_BIN:\$PATH\"${NC}"
            echo
            log_info "Shell profile locations:"
            echo "  • Bash: ~/.bashrc or ~/.bash_profile"
            echo "  • Zsh: ~/.zshrc"
            echo "  • Fish: ~/.config/fish/config.fish"
        else
            log_error "r4r not found in expected location: $USER_BIN"
        fi
    else
        log_error "r4r not found in system PATH"
        log_info "Try running 'which r4r' to locate the installation"
    fi
fi

# Installation summary
echo
log_header "🎯 Quick Start"
echo -e "${GREEN}1. Get API key:${NC} https://dashboard.render.com/u/settings#api-keys"
echo -e "${GREEN}2. Login:${NC} r4r login"
echo -e "${GREEN}3. List services:${NC} r4r list"
echo -e "${GREEN}4. Deploy:${NC} r4r deploy myapp"
echo

log_header "📚 Key Commands"
cat << 'EOF'

Authentication:
  r4r login                    # Login with API key
  r4r whoami                   # Show user info
  r4r logout                   # Logout

Service Management:
  r4r list --detailed          # List services with details
  r4r info <service>           # Service information
  r4r deploy <service>         # Deploy service
  r4r deploy <service> --clear # Deploy with cache clear
  r4r rebuild <service>        # Rebuild (clear + deploy)

Monitoring:
  r4r logs <service>           # View logs
  r4r deploys <service>        # Deployment history
  r4r job <service> "command"  # Run one-off job
  r4r jobs <service>           # List jobs

EOF

log_success "Installation complete!"
log_info "Run 'r4r --help' for all commands"

# Installation info
echo
log_info "Installation Details:"
echo "  • Method: pip"
echo "  • Python: $PYTHON_VERSION"
echo "  • Pip: $PIP_VERSION"
if [[ "$USER_INSTALL" == true ]]; then
    echo "  • Scope: User installation"
else
    echo "  • Scope: System-wide"
fi

if command -v r4r &> /dev/null; then
    echo "  • Status: ✅ Ready to use"
    echo
    echo -e "${YELLOW}Ready to login? Run: r4r login${NC}"
else
    echo "  • Status: ⚠️  PATH configuration needed"
fi