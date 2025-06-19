#!/bin/bash
set -e

# r4r pip installation script
# Usage: curl -sSL https://raw.githubusercontent.com/porameht/r4r/main/install-pip.sh | bash

echo "🚀 Installing r4r with pip..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ Error: pip not found. Please install Python and pip first."
    echo "   Visit https://www.python.org/downloads/ to install Python."
    exit 1
fi

# Install r4r
echo "📦 Installing r4r..."
pip install r4r

# Verify installation
if command -v r4r &> /dev/null; then
    echo "✅ r4r installed successfully!"
    echo ""
    echo "🎉 Installation complete! Get started with:"
    echo "   r4r login"
    echo "   r4r list"
    echo ""
    echo "📖 For more information, visit: https://github.com/porameht/r4r"
else
    echo "⚠️  r4r installed but not found in PATH."
    echo "   You may need to add Python's script directory to your PATH."
    echo "   Try running: python -m r4r.cli --help"
fi