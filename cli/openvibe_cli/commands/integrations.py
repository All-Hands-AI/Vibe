"""Integration management commands for OpenVibe CLI."""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..api_client import get_api_client, APIError
from ..config import Config

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
        api = get_api_client()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Setting {provider} API key...", total=None)
            
            # Make API request to set the key
            response = api._make_request('POST', f'/integrations/{provider}', json={'api_key': api_key})
            data = api._handle_response(response)
            
            progress.remove_task(task)
        
        if data.get('valid'):
            console.print(f"✅ {provider.title()} API key set successfully!", style="green")
        else:
            console.print(f"❌ {provider.title()} API key is invalid", style="red")
            
    except APIError as e:
        console.print(f"❌ Error setting API key: {e.message}", style="red")
    except Exception as e:
        console.print(f"❌ Unexpected error: {str(e)}", style="red")


@integrations.command()
def setup_mock():
    """Set up mock API keys for testing."""
    mock_keys = {
        'github': 'mock_github_token_12345',
        'fly': 'mock_fly_token_12345',
        'anthropic': 'mock_anthropic_key_12345',
        'openai': 'mock_openai_key_12345'
    }
    
    console.print("🎭 Setting up mock API keys for testing...", style="yellow")
    
    for provider, key in mock_keys.items():
        try:
            api = get_api_client()
            response = api._make_request('POST', f'/integrations/{provider}', json={'api_key': key})
            data = api._handle_response(response)
            
            if data.get('valid'):
                console.print(f"✅ Mock {provider} key set", style="green")
            else:
                console.print(f"❌ Failed to set mock {provider} key", style="red")
                
        except Exception as e:
            console.print(f"❌ Error setting mock {provider} key: {str(e)}", style="red")
    
    console.print("\n🎉 Mock API keys setup complete! You can now create apps and test the CLI.", style="green")


@integrations.command()
def status():
    """Check the status of all API key integrations."""
    providers = ['github', 'fly', 'anthropic', 'openai']
    
    console.print("🔑 API Key Status:", style="bold")
    
    for provider in providers:
        try:
            api = get_api_client()
            response = api._make_request('GET', f'/integrations/{provider}')
            data = api._handle_response(response)
            
            if data.get('valid'):
                console.print(f"   ✅ {provider.title()}: Configured", style="green")
            else:
                console.print(f"   ❌ {provider.title()}: Not configured", style="red")
                
        except APIError as e:
            if e.status_code == 404:
                console.print(f"   ❌ {provider.title()}: Not configured", style="red")
            else:
                console.print(f"   ⚠️ {provider.title()}: Error checking status", style="yellow")
        except Exception:
            console.print(f"   ⚠️ {provider.title()}: Error checking status", style="yellow")