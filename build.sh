#!/bin/bash
set -e

# r4r build script
# Usage: ./build.sh

echo "🔨 Building r4r..."

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "✅ Using uv for build..."
    
    # Clean previous builds
    rm -rf dist/
    
    # Build the package
    uv build
    
    echo "✅ Build complete!"
    echo "📦 Built packages:"
    ls -la dist/
    
elif command -v python &> /dev/null; then
    echo "✅ Using Python build module..."
    
    # Install build if not present
    pip install --quiet build
    
    # Clean previous builds
    rm -rf dist/
    
    # Build the package
    python -m build
    
    echo "✅ Build complete!"
    echo "📦 Built packages:"
    ls -la dist/
    
else
    echo "❌ Error: Neither uv nor python found."
    echo "   Please install Python or uv first."
    exit 1
fi

echo ""
echo "📖 To install locally:"
echo "   uv tool install dist/*.whl"
echo "   # or"
echo "   pip install dist/*.whl"
echo ""
echo "📤 To publish to PyPI:"
echo "   uv publish"
echo "   # or"
echo "   twine upload dist/*"