#!/bin/bash
set -e

# r4r installation script
# Usage: curl -sSL https://raw.githubusercontent.com/porameht/r4r/main/install.sh | bash

echo "🚀 Installing r4r - Render CLI..."

# Get the latest release tag from GitHub API
echo "🔍 Fetching latest version..."
LATEST_TAG=$(curl -s https://api.github.com/repos/porameht/r4r/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' || echo "")

# If no release found, try to get latest tag
if [ -z "$LATEST_TAG" ]; then
    LATEST_TAG=$(curl -s https://api.github.com/repos/porameht/r4r/tags | grep '"name":' | head -1 | sed -E 's/.*"([^"]+)".*/\1/' || echo "")
fi

# If still no tag, fallback to main branch
if [ -z "$LATEST_TAG" ]; then
    echo "⚠️  Could not fetch latest version, installing from main branch..."
    GIT_URL="git+https://github.com/porameht/r4r.git"
else
    echo "✅ Latest version found: $LATEST_TAG"
    GIT_URL="git+https://github.com/porameht/r4r.git@$LATEST_TAG"
fi


# Try pip first (most common)
if command -v pip &> /dev/null; then
    echo "✅ Installing with pip..."
    pip install "$GIT_URL"
    echo "✅ r4r installed successfully!"
elif command -v uv &> /dev/null; then
    echo "✅ Installing with uv..."
    uv tool install "$GIT_URL"
    echo "✅ r4r installed successfully!"
else
    echo "❌ Error: Neither pip nor uv found."
    echo "Please install Python first: https://python.org"
    exit 1
fi

echo ""
echo "🎉 Get started with:"
echo "   r4r auth login"
echo "   r4r services list"
echo ""
echo "📖 For more information, visit: https://github.com/porameht/r4r"