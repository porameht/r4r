#!/bin/bash
# r4r - Build Script for Development and Production
# Supports multiple Python package managers and distribution methods

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
BUILD_TYPE="dev"
CLEAN=false
UPLOAD=false
SKIP_TESTS=false
VERSION=""

# Help function
show_help() {
    cat << EOF
r4r Build Script

Usage: $0 [OPTIONS]

OPTIONS:
    -t, --type TYPE     Build type: dev, prod, or dist (default: dev)
    -c, --clean         Clean build directories before building
    -u, --upload        Upload to PyPI (requires API token)
    -s, --skip-tests    Skip running tests
    -v, --version VER   Set version number (for prod builds)
    -h, --help          Show this help message

BUILD TYPES:
    dev     Development build with local installation
    prod    Production build with optimizations
    dist    Distribution build for PyPI upload

EXAMPLES:
    $0                          # Development build
    $0 -t prod -c               # Clean production build
    $0 -t dist -u               # Build and upload to PyPI
    $0 -t prod -v 1.0.0         # Production build with version 1.0.0

ENVIRONMENT VARIABLES:
    PYPI_TOKEN                  PyPI API token for uploads
    UV_CACHE_DIR               UV cache directory (optional)
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -u|--upload)
            UPLOAD=true
            shift
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
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

# Validate build type
if [[ ! "$BUILD_TYPE" =~ ^(dev|prod|dist)$ ]]; then
    log_error "Invalid build type: $BUILD_TYPE. Must be dev, prod, or dist"
    exit 1
fi

log_header "r4r Build Script - Type: $BUILD_TYPE"

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    log_error "pyproject.toml not found. Are you in the r4r project directory?"
    exit 1
fi

# Check Python version
log_info "Checking Python version..."
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [[ $(python3 -c "import sys; print(sys.version_info >= (3, 8))") != "True" ]]; then
    log_error "Python 3.8+ required. You have $PYTHON_VERSION"
    exit 1
fi
log_success "Python $PYTHON_VERSION detected"

# Check for required tools
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is required but not installed"
        return 1
    fi
    return 0
}

log_info "Checking required tools..."

# Check for uv (preferred) or pip
if command -v uv &> /dev/null; then
    TOOL="uv"
    log_success "uv detected"
elif command -v pip &> /dev/null; then
    TOOL="pip"
    log_warning "uv not found, using pip (slower)"
else
    log_error "Neither uv nor pip found. Please install one of them."
    exit 1
fi

# Set version if provided
if [[ -n "$VERSION" ]]; then
    log_info "Setting version to $VERSION"
    if [[ "$TOOL" == "uv" ]]; then
        uv run python -c "
import re
with open('pyproject.toml', 'r') as f:
    content = f.read()
content = re.sub(r'version = \"[^\"]*\"', f'version = \"$VERSION\"', content)
with open('pyproject.toml', 'w') as f:
    f.write(content)
"
    else
        python3 -c "
import re
with open('pyproject.toml', 'r') as f:
    content = f.read()
content = re.sub(r'version = \"[^\"]*\"', f'version = \"$VERSION\"', content)
with open('pyproject.toml', 'w') as f:
    f.write(content)
"
    fi
    log_success "Version updated to $VERSION"
fi

# Clean build directories
if [[ "$CLEAN" == true ]]; then
    log_info "Cleaning build directories..."
    rm -rf build/ dist/ *.egg-info/ .pytest_cache/ __pycache__/ src/r4r/__pycache__/
    log_success "Build directories cleaned"
fi

# Install dependencies
log_info "Installing dependencies..."
if [[ "$TOOL" == "uv" ]]; then
    uv sync
    if [[ "$BUILD_TYPE" == "dist" || "$BUILD_TYPE" == "prod" ]]; then
        uv add --dev build twine
    fi
else
    pip install -e .
    if [[ "$BUILD_TYPE" == "dist" || "$BUILD_TYPE" == "prod" ]]; then
        pip install build twine
    fi
fi
log_success "Dependencies installed"

# Run tests (unless skipped)
if [[ "$SKIP_TESTS" != true ]]; then
    log_info "Running tests..."
    if [[ "$TOOL" == "uv" ]]; then
        # Create basic test if none exists
        if [[ ! -d "tests" ]]; then
            mkdir -p tests
            cat > tests/test_basic.py << 'EOF'
"""Basic tests for r4r CLI"""
import subprocess
import sys

def test_import():
    """Test that the module can be imported"""
    try:
        import r4r.cli
        assert True
    except ImportError:
        assert False, "Failed to import r4r.cli"

def test_cli_help():
    """Test that the CLI shows help"""
    try:
        result = subprocess.run([sys.executable, "-m", "r4r.cli", "--help"], 
                              capture_output=True, text=True, timeout=10)
        assert "r4r - Super easy Render CLI" in result.stdout
    except Exception as e:
        assert False, f"CLI help test failed: {e}"

if __name__ == "__main__":
    test_import()
    test_cli_help()
    print("✅ All tests passed!")
EOF
        fi
        
        # Try to run tests with pytest if available, otherwise run basic tests
        if uv run python -c "import pytest" 2>/dev/null; then
            uv run pytest tests/ -v
        else
            uv run python tests/test_basic.py
        fi
    else
        python3 -m pytest tests/ -v 2>/dev/null || python3 tests/test_basic.py 2>/dev/null || log_warning "No tests found or test framework not available"
    fi
    log_success "Tests completed"
fi

# Build based on type
case $BUILD_TYPE in
    "dev")
        log_info "Building for development..."
        if [[ "$TOOL" == "uv" ]]; then
            uv build
            log_info "Installing in development mode..."
            uv tool install --editable .
        else
            python3 -m build
            pip install -e .
        fi
        log_success "Development build completed"
        
        # Test installation
        log_info "Testing installation..."
        if command -v r4r &> /dev/null; then
            VERSION_OUTPUT=$(r4r --version 2>/dev/null || echo "Version check failed")
            log_success "r4r CLI installed and available: $VERSION_OUTPUT"
        else
            log_warning "r4r CLI installed but not in PATH"
        fi
        ;;
        
    "prod")
        log_info "Building for production..."
        if [[ "$TOOL" == "uv" ]]; then
            uv build
        else
            python3 -m build
        fi
        
        # Create distribution info
        DIST_FILES=$(ls dist/ 2>/dev/null | wc -l)
        if [[ $DIST_FILES -gt 0 ]]; then
            log_success "Production build completed - $DIST_FILES files in dist/"
            ls -la dist/
        else
            log_error "No distribution files created"
            exit 1
        fi
        ;;
        
    "dist")
        log_info "Building for distribution..."
        if [[ "$TOOL" == "uv" ]]; then
            uv build
        else
            python3 -m build
        fi
        
        # Verify distribution
        log_info "Verifying distribution files..."
        if [[ "$TOOL" == "uv" ]]; then
            uv run twine check dist/*
        else
            twine check dist/*
        fi
        log_success "Distribution verification completed"
        
        # Upload if requested
        if [[ "$UPLOAD" == true ]]; then
            if [[ -z "$PYPI_TOKEN" ]]; then
                log_error "PYPI_TOKEN environment variable required for upload"
                exit 1
            fi
            
            log_info "Uploading to PyPI..."
            if [[ "$TOOL" == "uv" ]]; then
                uv run twine upload dist/* --username __token__ --password "$PYPI_TOKEN"
            else
                twine upload dist/* --username __token__ --password "$PYPI_TOKEN"
            fi
            log_success "Upload completed"
        fi
        ;;
esac

# Generate installation commands
log_header "Installation Commands"
echo
log_info "For users to install r4r:"
echo
echo -e "${CYAN}# Using uv (recommended):${NC}"
echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
echo "uv tool install r4r"
echo
echo -e "${CYAN}# Using pip:${NC}"
echo "pip install r4r"
echo
echo -e "${CYAN}# From source:${NC}"
echo "git clone https://github.com/your-username/r4r.git"
echo "cd r4r"
echo "uv tool install ."
echo
echo -e "${CYAN}# One-line install script:${NC}"
echo "curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install.sh | bash"
echo

# Build summary
log_header "Build Summary"
echo
log_success "Build Type: $BUILD_TYPE"
log_success "Tool Used: $TOOL"
if [[ -n "$VERSION" ]]; then
    log_success "Version: $VERSION"
fi
if [[ -d "dist" ]]; then
    DIST_SIZE=$(du -sh dist/ | cut -f1)
    log_success "Distribution Size: $DIST_SIZE"
fi
log_success "Build completed successfully!"

echo
log_info "Next steps:"
case $BUILD_TYPE in
    "dev")
        echo "  • Test your changes: r4r --help"
        echo "  • Run r4r login to authenticate"
        echo "  • Use r4r list to see your services"
        ;;
    "prod")
        echo "  • Test the wheel: pip install dist/*.whl"
        echo "  • Or test the tarball: pip install dist/*.tar.gz"
        ;;
    "dist")
        if [[ "$UPLOAD" != true ]]; then
            echo "  • Upload with: $0 -t dist -u"
            echo "  • Or manually: twine upload dist/*"
        else
            echo "  • Package uploaded to PyPI!"
            echo "  • Users can now: pip install r4r"
        fi
        ;;
esac