#!/bin/bash
# Build script for OpenVibe CLI binary

set -e

echo "🔨 Building OpenVibe CLI binary..."

# Check if we're in the CLI directory
if [ ! -f "pyproject.toml" ] || [ ! -f "openvibe.spec" ]; then
    echo "❌ Please run this script from the cli/ directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
fi

# Install dependencies
echo "📦 Installing dependencies..."
source .venv/bin/activate
uv pip install -e .[build]

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Build binary
echo "🚀 Building binary with PyInstaller..."
pyinstaller --clean --noconfirm openvibe.spec

# Test the binary
echo "🧪 Testing binary..."
if [ -f "dist/openvibe" ]; then
    ./dist/openvibe --version
    ./dist/openvibe --help > /dev/null
    echo "✅ Binary built successfully: dist/openvibe"
    echo "📏 Binary size: $(du -h dist/openvibe | cut -f1)"
else
    echo "❌ Binary build failed"
    exit 1
fi

echo "🎉 Build complete! Run './dist/openvibe' to test."