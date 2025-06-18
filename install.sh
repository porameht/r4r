#!/bin/bash
# r4r - Super Easy Render CLI Installer
# Supports uv, pip, and multiple installation methods

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

# Default values
INSTALL_METHOD="auto"
FORCE_REINSTALL=false
SKIP_PATH_CHECK=false
VERBOSE=false

# Help function
show_help() {
    cat << EOF
r4r Installation Script

Usage: $0 [OPTIONS]

OPTIONS:
    -m, --method METHOD     Installation method: auto, uv, pip, or source (default: auto)
    -f, --force            Force reinstall if already installed
    -s, --skip-path        Skip PATH configuration check
    -v, --verbose          Verbose output
    -h, --help             Show this help message

INSTALLATION METHODS:
    auto    Automatically choose the best method (uv preferred)
    uv      Use uv tool (recommended, fastest)
    pip     Use pip (traditional method)
    source  Install from source (development)

EXAMPLES:
    $0                      # Auto-detect best method
    $0 -m uv               # Force uv installation
    $0 -m pip              # Force pip installation
    $0 -f                  # Force reinstall

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--method)
            INSTALL_METHOD="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_REINSTALL=true
            shift
            ;;
        -s|--skip-path)
            SKIP_PATH_CHECK=true
            shift
            ;;
        -v|--verbose)
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

log_header "r4r (Render CLI) Installer"
echo

# Check if already installed and not forcing reinstall
if command -v r4r &> /dev/null && [[ "$FORCE_REINSTALL" != true ]]; then
    CURRENT_VERSION=$(r4r --version 2>/dev/null || echo "unknown")
    log_warning "r4r is already installed: $CURRENT_VERSION"
    echo "Use -f/--force to reinstall or -h/--help for options"
    exit 0
fi

# System requirements check
log_info "Checking system requirements..."

# Check if we have Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3.8+ is required but not found"
    log_info "Please install Python from: https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(python3 -c "import sys; print(sys.version_info >= (3, 8))") != "True" ]]; then
    log_error "Python 3.8+ required. You have $PYTHON_VERSION"
    log_info "Please upgrade Python from: https://www.python.org/downloads/"
    exit 1
fi
log_success "Python $PYTHON_VERSION detected"

# Check internet connectivity
if ! curl -s --head --connect-timeout 5 https://pypi.org > /dev/null; then
    log_error "No internet connection or PyPI is unreachable"
    exit 1
fi
log_success "Internet connectivity verified"

# Determine installation method
if [[ "$INSTALL_METHOD" == "auto" ]]; then
    if command -v uv &> /dev/null; then
        INSTALL_METHOD="uv"
        log_info "Auto-detected: uv (fastest)"
    elif command -v pip &> /dev/null; then
        INSTALL_METHOD="pip"
        log_info "Auto-detected: pip (traditional)"
    else
        log_info "Neither uv nor pip found, will install uv first"
        INSTALL_METHOD="uv"
    fi
else
    log_info "Using specified method: $INSTALL_METHOD"
fi

# Validate installation method
if [[ ! "$INSTALL_METHOD" =~ ^(uv|pip|source)$ ]]; then
    log_error "Invalid installation method: $INSTALL_METHOD"
    log_info "Valid methods: uv, pip, source"
    exit 1
fi

# Installation based on method
case $INSTALL_METHOD in
    "uv")
        # Install uv if not present
        if ! command -v uv &> /dev/null; then
            log_info "Installing uv package manager..."
            if curl -LsSf https://astral.sh/uv/install.sh | sh; then
                # Try different ways to add uv to PATH
                source "$HOME/.cargo/env" 2>/dev/null || true
                export PATH="$HOME/.cargo/bin:$PATH"
                
                # Also try common installation paths
                for uv_path in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv" "/usr/local/bin/uv"; do
                    if [[ -x "$uv_path" ]]; then
                        export PATH="$(dirname "$uv_path"):$PATH"
                        break
                    fi
                done
                
                if ! command -v uv &> /dev/null; then
                    log_error "uv installed but not found in PATH"
                    log_info "Please restart your shell or run: source ~/.cargo/env"
                    exit 1
                fi
                log_success "uv installed successfully"
            else
                log_error "Failed to install uv"
                log_info "Falling back to pip installation..."
                INSTALL_METHOD="pip"
            fi
        else
            log_success "uv already available"
        fi
        
        if [[ "$INSTALL_METHOD" == "uv" ]]; then
            log_info "Installing r4r using uv..."
            if [[ "$VERBOSE" == true ]]; then
                uv tool install r4r --verbose
            else
                uv tool install r4r
            fi
        fi
        ;;
        
    "pip")
        if ! command -v pip &> /dev/null; then
            log_error "pip not found. Please install pip first."
            log_info "On most systems: python3 -m ensurepip --upgrade"
            exit 1
        fi
        
        log_info "Installing r4r using pip..."
        if [[ "$VERBOSE" == true ]]; then
            pip install r4r --user --verbose
        else
            pip install r4r --user
        fi
        ;;
        
    "source")
        log_info "Installing r4r from source..."
        
        # Create temporary directory
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        
        log_info "Downloading source code..."
        if command -v git &> /dev/null; then
            git clone https://github.com/your-username/r4r.git
            cd r4r
        else
            curl -L -o r4r.tar.gz https://github.com/your-username/r4r/archive/main.tar.gz
            tar -xzf r4r.tar.gz
            cd r4r-main
        fi
        
        # Install using available tool
        if command -v uv &> /dev/null; then
            log_info "Using uv for source installation..."
            uv tool install .
        elif command -v pip &> /dev/null; then
            log_info "Using pip for source installation..."
            pip install . --user
        else
            log_error "Neither uv nor pip available for source installation"
            exit 1
        fi
        
        # Cleanup
        cd /
        rm -rf "$TEMP_DIR"
        ;;
esac

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
    POSSIBLE_PATHS=(
        "$HOME/.local/bin/r4r"
        "$HOME/.cargo/bin/r4r"
        "/usr/local/bin/r4r"
        "$(python3 -m site --user-base)/bin/r4r"
    )
    
    FOUND_PATH=""
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [[ -x "$path" ]]; then
            FOUND_PATH="$path"
            break
        fi
    done
    
    if [[ -n "$FOUND_PATH" ]]; then
        log_info "Found r4r at: $FOUND_PATH"
        DIRNAME=$(dirname "$FOUND_PATH")
        
        if [[ "$SKIP_PATH_CHECK" != true ]]; then
            log_info "To use r4r, add this to your shell profile:"
            echo -e "${YELLOW}export PATH=\"$DIRNAME:\$PATH\"${NC}"
            echo
            log_info "Shell profile locations:"
            echo "  • Bash: ~/.bashrc or ~/.bash_profile"
            echo "  • Zsh: ~/.zshrc"
            echo "  • Fish: ~/.config/fish/config.fish"
            echo
            log_info "Or run this now:"
            echo -e "${CYAN}export PATH=\"$DIRNAME:\$PATH\"${NC}"
        fi
    else
        log_error "Installation completed but r4r not found anywhere"
        log_info "Please check your installation or try a different method"
    fi
fi

# Show usage information
echo
log_header "🎯 Quick Start Guide"
echo -e "${GREEN}1. Get your API key:${NC} https://dashboard.render.com/u/settings#api-keys"
echo -e "${GREEN}2. Login:${NC} r4r login"
echo -e "${GREEN}3. List services:${NC} r4r list"
echo -e "${GREEN}4. Deploy:${NC} r4r deploy myapp"
echo

log_header "📚 Essential Commands"
cat << EOF

${CYAN}Authentication:${NC}
  r4r login              # Login with API key
  r4r whoami             # Show current user info
  r4r logout             # Logout

${CYAN}Service Management:${NC}
  r4r list               # List all services
  r4r list --detailed    # Show detailed service info
  r4r info <name>        # Get service details
  r4r deploy <name>      # Deploy service
  r4r deploy <name> -c   # Deploy with cache clear
  r4r rebuild <name>     # Clear cache + deploy

${CYAN}Logs & Monitoring:${NC}
  r4r logs <name>        # View service logs
  r4r logs <name> -f     # Follow logs (stream)
  r4r deploys <name>     # List recent deployments

${CYAN}One-Off Jobs:${NC}
  r4r job <name> "command"     # Run a job
  r4r job <name> "cmd" --wait  # Run and wait
  r4r jobs <name>              # List recent jobs
  r4r status <job_id>          # Get job status

EOF

log_header "🚀 Installation Complete!"
echo
log_success "r4r is ready to use!"
log_info "Run 'r4r --help' for full command reference"
log_info "Visit https://github.com/your-username/r4r for documentation"
echo

# Installation summary
log_info "Installation Summary:"
echo "  • Method: $INSTALL_METHOD"
echo "  • Python: $PYTHON_VERSION"
if command -v r4r &> /dev/null; then
    echo "  • Status: ✅ Ready to use"
else
    echo "  • Status: ⚠️  Needs PATH configuration"
fi
echo

# Offer to run initial setup
if command -v r4r &> /dev/null; then
    echo -e "${YELLOW}Would you like to set up your API key now? (y/N)${NC}"
    read -r -n 1 response
    echo
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Starting login process..."
        r4r login
    else
        log_info "You can login later with: r4r login"
    fi
fi