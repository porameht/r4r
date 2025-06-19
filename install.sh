#!/bin/bash
set -e

# r4r installation script
# Usage: curl -sSL https://raw.githubusercontent.com/porameht/r4r/main/install.sh | bash

echo "🚀 Installing r4r - Super Easy Render CLI..."

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "✅ Found uv, installing with uv..."
    uv tool install r4r
    echo "✅ r4r installed successfully with uv!"
elif command -v pip &> /dev/null; then
    echo "✅ Found pip, installing with pip..."
    pip install r4r
    echo "✅ r4r installed successfully with pip!"
else
    echo "❌ Error: Neither uv nor pip found. Please install Python and pip first."
    exit 1
fi

echo ""
echo "🎉 Installation complete! Get started with:"
echo "   r4r login"
echo "   r4r list"
echo ""
echo "📖 For more information, visit: https://github.com/porameht/r4r"