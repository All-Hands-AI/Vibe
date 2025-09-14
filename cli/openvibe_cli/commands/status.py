"""Status and monitoring commands for OpenVibe CLI."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from openvibe_cli.api_client import get_api_client, APIError
from openvibe_cli.config import Config

console = Console()


@click.command()
def status():
    """📊 Show overall system status and health.
    
    Displays configuration status, backend connectivity, and integration status.
    """
    console.print("📊 OpenVibe CLI System Status", style="bold cyan")
    
    # Configuration Status
    config = Config.load()
    
    config_text = Text()
    config_text.append("Configuration:\n", style="bold")
    config_text.append(f"  • User UUID: {config.user_uuid[:8]}...\n")
    config_text.append(f"  • Backend URL: {config.backend_url}\n")
    config_text.append(f"  • Config file: {Config.get_config_path()}\n")
    
    console.print(Panel(config_text, title="Configuration", border_style="blue"))
    
    # Backend Connectivity
    try:
        api = get_api_client()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Checking backend connectivity...", total=None)
            
            # Test basic connectivity
            response = api._make_request('GET', '/api/health')
            health_data = api._handle_response(response)
            
            progress.remove_task(task)
        
        backend_text = Text()
        backend_text.append("Backend Status:\n", style="bold green")
        backend_text.append(f"  • Status: {health_data.get('status', 'unknown')}\n")
        backend_text.append(f"  • Service: {health_data.get('service', 'unknown')}\n")
        backend_text.append(f"  • Timestamp: {health_data.get('timestamp', 'unknown')}\n")
        
        console.print(Panel(backend_text, title="Backend Connectivity", border_style="green"))
        
        # Integration Status
        providers = ['github', 'fly', 'anthropic']
        
        integrations_table = Table(show_header=True, header_style="bold magenta")
        integrations_table.add_column("Provider", style="cyan")
        integrations_table.add_column("Status", style="white")
        integrations_table.add_column("Details", style="dim")
        
        for provider in providers:
            try:
                response = api._make_request('GET', f'/integrations/{provider}')
                data = api._handle_response(response)
                
                if data.get('valid'):
                    status = "✅ Configured"
                    details = "API key is valid"
                else:
                    status = "❌ Not configured"
                    details = "No API key set"
                    
            except APIError as e:
                if e.status_code == 404:
                    status = "❌ Not configured"
                    details = "No API key set"
                else:
                    status = "⚠️ Error"
                    details = f"Status check failed: {e.message}"
            except Exception:
                status = "⚠️ Error"
                details = "Connection error"
            
            integrations_table.add_row(provider.title(), status, details)
        
        console.print("\n🔑 Integration Status:", style="bold")
        console.print(integrations_table)
        
        # Apps Summary
        try:
            apps_data = api.list_apps()
            
            apps_text = Text()
            apps_text.append("Apps Summary:\n", style="bold")
            apps_text.append(f"  • Total apps: {len(apps_data)}\n")
            
            if apps_data:
                apps_text.append("  • Recent apps:\n")
                for app in apps_data[-3:]:  # Show last 3 apps
                    apps_text.append(f"    - {app['name']} ({app['slug']})\n", style="dim")
            
            console.print(Panel(apps_text, title="Apps Overview", border_style="yellow"))
            
        except APIError:
            console.print("⚠️ Could not load apps summary", style="yellow")
        
        console.print("\n✅ System is operational!", style="bold green")
        
    except APIError as e:
        backend_text = Text()
        backend_text.append("Backend Status:\n", style="bold red")
        backend_text.append(f"  • Status: Error\n")
        backend_text.append(f"  • Error: {e.message}\n")
        backend_text.append(f"  • Code: {e.status_code}\n")
        
        console.print(Panel(backend_text, title="Backend Connectivity", border_style="red"))
        console.print("❌ Backend is not accessible", style="bold red")
        
    except Exception as e:
        console.print(f"❌ Unexpected error: {str(e)}", style="red")
    
    console.print(f"\n💡 Commands:", style="bold")
    console.print("   • Check configuration: openvibe setup")
    console.print("   • Set up integrations: openvibe integrations setup-mock")
    console.print("   • List apps: openvibe apps list")
    console.print("   • Get help: openvibe --help")