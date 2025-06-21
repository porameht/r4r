#!/bin/bash
set -e

# r4r installation script
# Usage: curl -sSL https://raw.githubusercontent.com/porameht/r4r/main/install.sh | bash

echo "🚀 Installing r4r - Render CLI..."

# Try pip first (most common)
if command -v pip &> /dev/null; then
    echo "✅ Installing with pip..."
    pip install git+https://github.com/porameht/r4r.git
    echo "✅ r4r installed successfully!"
elif command -v uv &> /dev/null; then
    echo "✅ Installing with uv..."
    uv tool install git+https://github.com/porameht/r4r.git
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