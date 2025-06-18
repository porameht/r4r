# r4r - Development Makefile
# Simple commands for development workflow

.PHONY: help install build test lint format clean dev prod dist upload

# Default target
help:
	@echo "🚀 r4r Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install    Install dependencies and r4r in development mode"
	@echo "  dev        Quick development setup"
	@echo ""
	@echo "Development:"
	@echo "  test       Run tests"
	@echo "  lint       Run linting checks"
	@echo "  format     Format code"
	@echo "  clean      Clean build artifacts"
	@echo ""
	@echo "Building:"
	@echo "  build      Build development version"
	@echo "  prod       Build production version"
	@echo "  dist       Build distribution for PyPI"
	@echo "  upload     Upload to PyPI (requires PYPI_TOKEN)"
	@echo ""
	@echo "Usage:"
	@echo "  make install    # First time setup"
	@echo "  make dev        # Daily development"
	@echo "  make test       # Run tests"
	@echo "  make prod       # Production build"

# Development setup
install:
	@echo "📦 Installing dependencies..."
	uv sync --dev
	@echo "🔧 Installing r4r in development mode..."
	uv tool install --editable .
	@echo "✅ Development setup complete!"

# Quick development setup
dev: install
	@echo "🧪 Running quick tests..."
	@$(MAKE) test
	@echo "🎉 Ready for development!"

# Testing
test:
	@echo "🧪 Running tests..."
	@mkdir -p tests
	@if [ ! -f tests/test_basic.py ]; then \
		echo "Creating basic tests..."; \
		cat > tests/test_basic.py << 'EOF'; \
"""Basic tests for r4r CLI"""; \
import subprocess; \
import sys; \
def test_import():; \
    try:; \
        import r4r.cli; \
        assert True; \
    except ImportError:; \
        assert False, "Failed to import r4r.cli"; \
def test_cli_help():; \
    try:; \
        result = subprocess.run([sys.executable, "-m", "r4r.cli", "--help"], capture_output=True, text=True, timeout=10); \
        assert "r4r - Super easy Render CLI" in result.stdout; \
    except Exception as e:; \
        assert False, f"CLI help test failed: {e}"; \
if __name__ == "__main__":; \
    test_import(); \
    test_cli_help(); \
    print("✅ All tests passed!"); \
EOF; \
	fi
	@if uv run python -c "import pytest" 2>/dev/null; then \
		uv run pytest tests/ -v; \
	else \
		uv run python tests/test_basic.py; \
	fi

# Linting
lint:
	@echo "🔍 Running linting checks..."
	@if uv run python -c "import ruff" 2>/dev/null; then \
		uv run ruff check src/; \
	else \
		echo "⚠️ ruff not installed, skipping lint checks"; \
	fi

# Code formatting
format:
	@echo "🎨 Formatting code..."
	@if uv run python -c "import ruff" 2>/dev/null; then \
		uv run ruff format src/; \
	else \
		echo "⚠️ ruff not installed, skipping code formatting"; \
	fi

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ __pycache__/ src/r4r/__pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleaned!"

# Development build
build: clean
	@echo "🔨 Building development version..."
	@./build.sh -t dev

# Production build
prod: clean test
	@echo "🏭 Building production version..."
	@./build.sh -t prod

# Distribution build
dist: clean test
	@echo "📦 Building distribution..."
	@./build.sh -t dist

# Upload to PyPI
upload: dist
	@echo "🚀 Uploading to PyPI..."
	@if [ -z "$$PYPI_TOKEN" ]; then \
		echo "❌ PYPI_TOKEN environment variable required"; \
		echo "Get your token from: https://pypi.org/manage/account/token/"; \
		exit 1; \
	fi
	@./build.sh -t dist -u

# Quick commands
.PHONY: quick-test quick-build quick-install

# Quick test without full setup
quick-test:
	@echo "⚡ Quick test..."
	@uv run python -c "import r4r.cli; print('✅ Import successful')"
	@uv run python -c "from r4r.cli import app; print('✅ CLI import successful')"

# Quick build check
quick-build:
	@echo "⚡ Quick build check..."
	uv build
	@echo "✅ Build successful"

# Quick install for testing
quick-install:
	@echo "⚡ Quick install..."
	uv tool install --force .

# Show project info
info:
	@echo "📋 Project Information"
	@echo "====================="
	@echo "Name: r4r (Render for Render CLI)"
	@echo "Description: Super easy Render CLI with advanced features"
	@echo ""
	@echo "📂 Structure:"
	@ls -la
	@echo ""
	@echo "🐍 Python version:"
	@python3 --version
	@echo ""
	@echo "📦 UV version:"
	@uv --version 2>/dev/null || echo "uv not installed"
	@echo ""
	@if [ -f pyproject.toml ]; then \
		echo "📋 Project version:"; \
		grep "version = " pyproject.toml | head -1; \
	fi