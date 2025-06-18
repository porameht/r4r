#!/bin/bash
# r4r - Super Easy Render CLI Installer using uv

set -e

echo "🚀 Installing r4r (Render CLI)..."

# Check if we have Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.8+ is required. Please install it first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l 2>/dev/null || echo "$PYTHON_VERSION" | awk -F. '{print ($1 < 3 || ($1 == 3 && $2 < 8))}') -eq 1 ]]; then
    echo "❌ Python 3.8+ required. You have $PYTHON_VERSION"
    exit 1
fi

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env 2>/dev/null || true
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install manually: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
fi

# Install r4r using uv
echo "📥 Installing r4r CLI..."
uv tool install r4r

# Check if installation worked
if command -v r4r &> /dev/null; then
    echo "✅ r4r installed successfully!"
else
    echo "⚠️  r4r installed but not in PATH. You may need to:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "   # Add the above line to your shell profile (~/.bashrc, ~/.zshrc, etc.)"
fi

echo ""
echo "🎯 Quick start:"
echo "  1. r4r login"
echo "  2. r4r list"
echo "  3. r4r deploy myapp --clear"
echo ""
echo "📚 All commands:"
echo "  r4r login          # Login with API key"
echo "  r4r list           # List services"
echo "  r4r deploy <name>  # Deploy service"
echo "  r4r deploy <name> --clear  # Deploy with cache clear"
echo "  r4r rebuild <name> # Clear cache + deploy (shorthand)"
echo ""
echo "💡 Get your API key: https://dashboard.render.com/u/settings#api-keys"