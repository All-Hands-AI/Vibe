"""Apps management commands for OpenVibe CLI."""

import click
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from openvibe_cli.backend import get_backend
from openvibe_cli.config import Config

console = Console()


@click.group()
def apps():
    """📱 Manage OpenVibe apps.
    
    Create, list, view, and delete apps. Apps are containers for your riffs
    and provide deployment and management capabilities.
    """
    pass


@apps.command()
def list():
    """List all your apps."""
    try:
        backend = get_backend()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading apps...", total=None)
            apps_data = backend.list_apps()
            progress.remove_task(task)
        
        if not apps_data:
            console.print("📭 No apps found. Create your first app with:", style="yellow")
            console.print("   openvibe apps create \"My First App\"", style="dim")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Slug", style="green")
        table.add_column("Created", style="blue")
        table.add_column("GitHub", style="yellow")
        table.add_column("Status", style="white")
        
        for app in apps_data:
            created_date = datetime.fromisoformat(app['created_at'].replace('Z', '+00:00'))
            created_str = created_date.strftime('%Y-%m-%d')
            
            github_status = "✅ Yes" if app.get('github_url') else "❌ No"
            
            # Simple status - could be enhanced with actual deployment status
            status = "🟢 Active"
            
            table.add_row(
                app['name'],
                app['slug'],
                created_str,
                github_status,
                status
            )
        
        console.print(f"\n📱 Your Apps ({len(apps_data)} total):", style="bold")
        console.print(table)
        console.print(f"\n💡 Use 'openvibe apps show <slug>' to view app details", style="dim")
        
    except Exception as e:
        console.print(f"❌ Error loading apps: {str(e)}", style="red")


@apps.command()
@click.argument('name')
def create(name):
    """Create a new app.
    
    NAME: The name of the app to create
    """
    if not name.strip():
        console.print("❌ App name cannot be empty", style="red")
        return
    
    try:
        backend = get_backend()
        
        # Create slug from name
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = slug[:50]  # Limit length
        
        # Show what will be created
        console.print(f"📱 Creating app:", style="bold")
        console.print(f"   Name: {name}")
        console.print(f"   Slug: {slug}")
        
        if not Confirm.ask("Continue?", default=True):
            console.print("❌ Cancelled", style="yellow")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Creating app...", total=None)
            app_data = backend.create_app(name, slug)
            progress.remove_task(task)
        
        console.print("✅ App created successfully!", style="green")
        console.print(f"   Name: {app_data['name']}")
        console.print(f"   Slug: {app_data['slug']}")
        console.print(f"   Created: {app_data['created_at']}")
        
        if app_data.get('github_repo'):
            console.print(f"   GitHub: {app_data['github_repo']}")
        
        console.print(f"\n💡 Next steps:", style="bold")
        console.print(f"   • View app: openvibe apps show {app_data['slug']}")
        console.print(f"   • Create a riff: openvibe riffs create {app_data['slug']} \"My Riff\"")
        
    except Exception as e:
        console.print(f"❌ Error creating app: {str(e)}", style="red")


@apps.command()
@click.argument('slug')
def show(slug):
    """Show detailed information about an app.
    
    SLUG: The slug of the app to show
    """
    try:
        backend = get_backend()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading app details...", total=None)
            app_data = backend.get_app(slug)
            progress.remove_task(task)
        
        if not app_data:
            console.print(f"❌ App '{slug}' not found", style="red")
            return
        
        # Create detailed view
        info_text = Text()
        info_text.append(f"📱 {app_data['name']}\n\n", style="bold cyan")
        info_text.append(f"Slug: {app_data['slug']}\n")
        info_text.append(f"Created: {app_data['created_at']}\n")
        
        if app_data.get('github_repo'):
            info_text.append(f"GitHub: {app_data['github_repo']}\n", style="green")
        else:
            info_text.append("GitHub: Not configured\n", style="dim")
        
        if app_data.get('fly_app_name'):
            info_text.append(f"Fly.io App: {app_data['fly_app_name']}\n", style="blue")
        else:
            info_text.append("Fly.io App: Not deployed\n", style="dim")
        
        console.print(Panel(info_text, title="App Details", border_style="cyan"))
        
        # Load and show riffs
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Loading riffs...", total=None)
                riffs_data = backend.list_riffs(slug)
                progress.remove_task(task)
            
            if riffs_data:
                console.print(f"\n🎵 Riffs ({len(riffs_data)} total):", style="bold")
                riffs_table = Table(show_header=True, header_style="bold magenta")
                riffs_table.add_column("Name", style="cyan")
                riffs_table.add_column("Slug", style="green")
                riffs_table.add_column("Created", style="blue")
                riffs_table.add_column("Last Activity", style="yellow")
                
                for riff in riffs_data:
                    created_date = datetime.fromisoformat(riff['created_at'].replace('Z', '+00:00'))
                    created_str = created_date.strftime('%Y-%m-%d')
                    
                    last_activity = "Never"
                    if riff.get('last_message_at'):
                        last_date = datetime.fromisoformat(riff['last_message_at'].replace('Z', '+00:00'))
                        last_activity = last_date.strftime('%Y-%m-%d')
                    
                    riffs_table.add_row(
                        riff['name'],
                        riff['slug'],
                        created_str,
                        last_activity
                    )
                
                console.print(riffs_table)
            else:
                console.print("\n📭 No riffs found.", style="yellow")
            
            console.print(f"\n💡 Commands:", style="bold")
            console.print(f"   • Create riff: openvibe riffs create {slug} \"Riff Name\"")
            if riffs_data:
                console.print(f"   • Chat with riff: openvibe chat {slug} <riff-slug>")
        
        except Exception:
            console.print("\n⚠️ Could not load riffs for this app", style="yellow")
        
    except Exception as e:
        console.print(f"❌ Error loading app: {str(e)}", style="red")


@apps.command()
@click.argument('slug')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def delete(slug, force):
    """Delete an app and all its data.
    
    SLUG: The slug of the app to delete
    
    ⚠️  WARNING: This will permanently delete:
    • The app from OpenVibe
    • The associated GitHub repository (if any)
    • The associated Fly.io application (if any)
    • All app riffs and data
    
    This action cannot be undone.
    """
    try:
        backend = get_backend()
        
        # First, get app details to show what will be deleted
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading app details...", total=None)
            app_data = backend.get_app(slug)
            progress.remove_task(task)
        
        if not app_data:
            console.print(f"❌ App '{slug}' not found", style="red")
            return
        
        # Show what will be deleted
        console.print(f"🗑️ Delete App: {app_data['name']}", style="bold red")
        console.print("\n⚠️ This will permanently delete:", style="yellow")
        console.print(f"   • The app '{app_data['name']}' from OpenVibe")
        
        if app_data.get('github_url'):
            console.print(f"   • The GitHub repository: {app_data['github_url']}")
        
        if app_data.get('fly_app_name'):
            console.print(f"   • The Fly.io application: {app_data['fly_app_name']}")
        
        console.print("   • All app riffs and data")
        console.print("\n❌ This action cannot be undone.", style="bold red")
        
        if not force:
            if not Confirm.ask(f"\nAre you sure you want to delete '{app_data['name']}'?", default=False):
                console.print("❌ Cancelled", style="yellow")
                return
            
            # Double confirmation for destructive action
            if not Confirm.ask("Type the app name to confirm", default=False):
                console.print("❌ Cancelled", style="yellow")
                return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Deleting app...", total=None)
            success = backend.delete_app(slug)
            progress.remove_task(task)
        
        if success:
            console.print("✅ App deleted successfully!", style="green")
        else:
            console.print("❌ Failed to delete app", style="red")
        
    except Exception as e:
        console.print(f"❌ Error deleting app: {str(e)}", style="red")