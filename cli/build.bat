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
pyinstaller --onefile --name openvibe ^
  --hidden-import=openvibe_cli.main ^
  --hidden-import=openvibe_cli.config ^
  --hidden-import=openvibe_cli.api_client ^
  --hidden-import=openvibe_cli.commands.setup ^
  --hidden-import=openvibe_cli.commands.apps ^
  --hidden-import=openvibe_cli.commands.riffs ^
  --hidden-import=openvibe_cli.commands.chat ^
  --hidden-import=openvibe_cli.commands.integrations ^
  --hidden-import=openvibe_cli.commands.status ^
  --hidden-import=rich.console ^
  --hidden-import=rich.table ^
  --hidden-import=rich.panel ^
  --hidden-import=rich.progress ^
  --hidden-import=prompt_toolkit ^
  --hidden-import=click ^
  --hidden-import=requests ^
  --hidden-import=pydantic ^
  openvibe_cli/main.py

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