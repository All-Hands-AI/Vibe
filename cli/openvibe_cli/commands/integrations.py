"""Integration management commands for OpenVibe CLI."""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from openvibe_cli.backend import get_backend
from openvibe_cli.config import Config

console = Console()


@click.group()
def integrations():
    """🔑 Manage API key integrations.
    
    Set up API keys for GitHub, Fly.io, and AI services.
    """
    pass


@integrations.command()
@click.argument('provider', type=click.Choice(['github', 'fly', 'anthropic', 'openai']))
@click.argument('api_key')
def set_key(provider, api_key):
    """Set an API key for a provider.
    
    PROVIDER: The service provider (github, fly, anthropic, openai)
    API_KEY: The API key to set
    """
    try:
        backend = get_backend()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Setting {provider} API key...", total=None)
            success = backend.set_integration_key(provider, api_key)
            progress.remove_task(task)
        
        if success:
            console.print(f"✅ {provider.title()} API key set successfully!", style="green")
        else:
            console.print(f"❌ Failed to set {provider.title()} API key", style="red")
            
    except Exception as e:
        console.print(f"❌ Error setting API key: {str(e)}", style="red")


@integrations.command()
def setup_mock():
    """Set up mock API keys for testing."""
    mock_keys = {
        'github': 'mock_github_token_12345',
        'fly': 'mock_fly_token_12345',
        'anthropic': 'mock_anthropic_key_12345',
        'openai': 'mock_openai_key_12345'
    }
    
    try:
        backend = get_backend()
        
        console.print("🎭 Setting up mock API keys for testing...", style="yellow")
        
        success = backend.setup_mock_keys()
        
        if success:
            console.print("✅ Mock API keys set up successfully!", style="green")
            console.print("\n🎉 Mock setup complete! You can now:", style="green")
            console.print("   • Create apps: openvibe apps create \"My App\"")
            console.print("   • Check status: openvibe status")
        else:
            console.print("❌ Failed to set up mock API keys", style="red")
            
    except Exception as e:
        console.print(f"❌ Error setting up mock keys: {str(e)}", style="red")


@integrations.command()
def status():
    """Check the status of all API key integrations."""
    providers = ['github', 'fly', 'anthropic', 'openai']
    
    backend = get_backend()
    console.print("🔑 API Key Status:", style="bold")
    
    for provider in providers:
        try:
            status_data = backend.get_integration_status(provider)
            
            if status_data.get('valid'):
                console.print(f"   ✅ {provider.title()}: Configured", style="green")
            else:
                console.print(f"   ❌ {provider.title()}: Not configured", style="red")
                
        except Exception:
            console.print(f"   ⚠️ {provider.title()}: Error checking status", style="yellow")