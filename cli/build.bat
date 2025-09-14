@echo off
REM Build script for OpenVibe CLI binary on Windows

echo 🔨 Building OpenVibe CLI binary...

REM Check if we're in the CLI directory
if not exist "pyproject.toml" (
    echo ❌ Please run this script from the cli\ directory
    exit /b 1
)

if not exist "openvibe.spec" (
    echo ❌ Please run this script from the cli\ directory
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    uv venv
)

REM Install dependencies
echo 📦 Installing dependencies...
call .venv\Scripts\activate
uv pip install -e .[build]

REM Clean previous builds
echo 🧹 Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build binary
echo 🚀 Building binary with PyInstaller...
pyinstaller --clean --noconfirm openvibe.spec

REM Test the binary
echo 🧪 Testing binary...
if exist "dist\openvibe.exe" (
    dist\openvibe.exe --version
    dist\openvibe.exe --help >nul
    echo ✅ Binary built successfully: dist\openvibe.exe
    for %%A in (dist\openvibe.exe) do echo 📏 Binary size: %%~zA bytes
) else (
    echo ❌ Binary build failed
    exit /b 1
)

echo 🎉 Build complete! Run 'dist\openvibe.exe' to test.