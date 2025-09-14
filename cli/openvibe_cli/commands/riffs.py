"""Riffs management commands for OpenVibe CLI."""

import click
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from ..api_client import get_api_client, APIError

console = Console()


@click.group()
def riffs():
    """🎵 Manage riffs within apps.
    
    Riffs are conversation threads within apps where you can chat with AI agents
    and collaborate on specific topics or tasks.
    """
    pass


@riffs.command()
@click.argument('app_slug')
def list(app_slug):
    """List all riffs for an app.
    
    APP_SLUG: The slug of the app to list riffs for
    """
    try:
        api = get_api_client()
        
        # First verify the app exists
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading app...", total=None)
            try:
                app_data = api.get_app(app_slug)
            except APIError as e:
                progress.remove_task(task)
                if e.status_code == 404:
                    console.print(f"❌ App '{app_slug}' not found", style="red")
                    return
                raise
            
            progress.update(task, description="Loading riffs...")
            riffs_data = api.list_riffs(app_slug)
            progress.remove_task(task)
        
        console.print(f"🎵 Riffs for app: {app_data['name']}", style="bold cyan")
        
        if not riffs_data:
            console.print("📭 No riffs found. Create your first riff with:", style="yellow")
            console.print(f"   openvibe riffs create {app_slug} \"My First Riff\"", style="dim")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Slug", style="green")
        table.add_column("Created", style="blue")
        table.add_column("Last Activity", style="yellow")
        table.add_column("Messages", style="white")
        
        for riff in riffs_data:
            created_date = datetime.fromisoformat(riff['created_at'].replace('Z', '+00:00'))
            created_str = created_date.strftime('%Y-%m-%d %H:%M')
            
            last_activity = "Never"
            if riff.get('last_message_at'):
                last_date = datetime.fromisoformat(riff['last_message_at'].replace('Z', '+00:00'))
                last_activity = last_date.strftime('%Y-%m-%d %H:%M')
            
            # Try to get message count (this might not be available in the API)
            message_count = str(riff.get('message_count', '?'))
            
            table.add_row(
                riff['name'],
                riff['slug'],
                created_str,
                last_activity,
                message_count
            )
        
        console.print(table)
        console.print(f"\n💡 Use 'openvibe riffs show {app_slug} <riff-slug>' to view riff details", style="dim")
        console.print(f"💬 Use 'openvibe chat {app_slug} <riff-slug>' to start chatting", style="dim")
        
    except APIError as e:
        console.print(f"❌ Error loading riffs: {e.message}", style="red")
    except Exception as e:
        console.print(f"❌ Unexpected error: {str(e)}", style="red")


@riffs.command()
@click.argument('app_slug')
@click.argument('name')
def create(app_slug, name):
    """Create a new riff in an app.
    
    APP_SLUG: The slug of the app to create the riff in
    NAME: The name of the riff to create
    """
    if not name.strip():
        console.print("❌ Riff name cannot be empty", style="red")
        return
    
    try:
        api = get_api_client()
        
        # First verify the app exists
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Verifying app...", total=None)
                app_data = api.get_app(app_slug)
                progress.remove_task(task)
        except APIError as e:
            if e.status_code == 404:
                console.print(f"❌ App '{app_slug}' not found", style="red")
                return
            raise
        
        # Show what will be created
        slug = api.create_slug(name)
        console.print(f"🎵 Creating riff in app: {app_data['name']}", style="bold")
        console.print(f"   Riff name: {name}")
        console.print(f"   Riff slug: {slug}")
        
        if not Confirm.ask("Continue?", default=True):
            console.print("❌ Cancelled", style="yellow")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Creating riff...", total=None)
            riff_data = api.create_riff(app_slug, name, slug)
            progress.remove_task(task)
        
        console.print("✅ Riff created successfully!", style="green")
        console.print(f"   Name: {riff_data['name']}")
        console.print(f"   Slug: {riff_data['slug']}")
        console.print(f"   Created: {riff_data['created_at']}")
        
        console.print(f"\n💡 Next steps:", style="bold")
        console.print(f"   • View riff: openvibe riffs show {app_slug} {riff_data['slug']}")
        console.print(f"   • Start chatting: openvibe chat {app_slug} {riff_data['slug']}")
        
    except APIError as e:
        console.print(f"❌ Error creating riff: {e.message}", style="red")
    except Exception as e:
        console.print(f"❌ Unexpected error: {str(e)}", style="red")


@riffs.command()
@click.argument('app_slug')
@click.argument('riff_slug')
def show(app_slug, riff_slug):
    """Show detailed information about a riff.
    
    APP_SLUG: The slug of the app
    RIFF_SLUG: The slug of the riff to show
    """
    try:
        api = get_api_client()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Load app and riffs data
            task = progress.add_task("Loading app details...", total=None)
            try:
                app_data = api.get_app(app_slug)
            except APIError as e:
                progress.remove_task(task)
                if e.status_code == 404:
                    console.print(f"❌ App '{app_slug}' not found", style="red")
                    return
                raise
            
            progress.update(task, description="Loading riffs...")
            riffs_data = api.list_riffs(app_slug)
            
            # Find the specific riff
            riff_data = None
            for riff in riffs_data:
                if riff['slug'] == riff_slug:
                    riff_data = riff
                    break
            
            if not riff_data:
                progress.remove_task(task)
                console.print(f"❌ Riff '{riff_slug}' not found in app '{app_slug}'", style="red")
                return
            
            progress.update(task, description="Loading messages...")
            try:
                messages_data = api.list_messages(app_slug, riff_slug)
            except APIError:
                messages_data = []
            
            progress.remove_task(task)
        
        # Create detailed view
        info_text = Text()
        info_text.append(f"🎵 {riff_data['name']}\n\n", style="bold cyan")
        info_text.append(f"App: {app_data['name']} ({app_data['slug']})\n")
        info_text.append(f"Slug: {riff_data['slug']}\n")
        info_text.append(f"Created: {riff_data['created_at']}\n")
        
        if riff_data.get('last_message_at'):
            info_text.append(f"Last Activity: {riff_data['last_message_at']}\n")
        else:
            info_text.append("Last Activity: Never\n", style="dim")
        
        info_text.append(f"Messages: {len(messages_data)}\n")
        
        console.print(Panel(info_text, title="Riff Details", border_style="cyan"))
        
        # Show recent messages if any
        if messages_data:
            console.print(f"\n💬 Recent Messages ({len(messages_data)} total):", style="bold")
            
            # Show last 5 messages
            recent_messages = messages_data[-5:] if len(messages_data) > 5 else messages_data
            
            for msg in recent_messages:
                timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                time_str = timestamp.strftime('%H:%M:%S')
                
                sender = msg.get('sender', 'user')
                sender_style = "green" if sender == 'user' else "blue"
                sender_icon = "👤" if sender == 'user' else "🤖"
                
                console.print(f"  {sender_icon} [{sender_style}]{sender}[/{sender_style}] [{time_str}]")
                
                # Truncate long messages
                content = msg.get('content', '')
                if len(content) > 100:
                    content = content[:97] + "..."
                
                console.print(f"     {content}", style="dim")
            
            if len(messages_data) > 5:
                console.print(f"     ... and {len(messages_data) - 5} more messages", style="dim")
        else:
            console.print("\n📭 No messages yet.", style="yellow")
        
        console.print(f"\n💡 Commands:", style="bold")
        console.print(f"   • Start chatting: openvibe chat {app_slug} {riff_slug}")
        console.print(f"   • List all riffs: openvibe riffs list {app_slug}")
        
    except APIError as e:
        console.print(f"❌ Error loading riff: {e.message}", style="red")
    except Exception as e:
        console.print(f"❌ Unexpected error: {str(e)}", style="red")