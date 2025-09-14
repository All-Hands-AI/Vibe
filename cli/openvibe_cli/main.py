"""Main CLI entry point for OpenVibe CLI."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .commands.setup import setup
from .commands.apps import apps
from .commands.riffs import riffs
from .commands.chat import chat
from .commands.integrations import integrations
from .commands.status import status

console = Console()


@click.group()
@click.version_option()
def main():
    """🤙 OpenVibe CLI - Command line interface for OpenVibe.
    
    This CLI provides 1:1 functionality parity with the OpenVibe web frontend,
    allowing you to manage apps, riffs, and chat interactions from the terminal.
    """
    pass


@main.command()
def welcome():
    """Display welcome message and getting started guide."""
    welcome_text = Text()
    welcome_text.append("🤙 Welcome to OpenVibe CLI!\n\n", style="bold cyan")
    welcome_text.append("This command-line interface mirrors the functionality of the OpenVibe web frontend.\n\n")
    welcome_text.append("Getting Started:\n", style="bold")
    welcome_text.append("1. Run 'openvibe setup' to configure your API keys\n")
    welcome_text.append("2. Use 'openvibe apps list' to see your apps\n")
    welcome_text.append("3. Create a new app with 'openvibe apps create \"My App\"'\n")
    welcome_text.append("4. Start chatting with 'openvibe chat <app-slug> <riff-slug>'\n\n")
    welcome_text.append("For help with any command, use --help\n")
    welcome_text.append("Example: openvibe apps --help")
    
    console.print(Panel(welcome_text, title="OpenVibe CLI", border_style="cyan"))


# Register command groups
main.add_command(setup)
main.add_command(apps)
main.add_command(riffs)
main.add_command(chat)
main.add_command(integrations)
main.add_command(status)


if __name__ == "__main__":
    main()