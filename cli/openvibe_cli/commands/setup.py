"""Setup command for OpenVibe CLI."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

from openvibe_cli.config import Config

console = Console()


@click.command()
@click.option('--reset', is_flag=True, help='Reset all configuration to defaults')
def setup(reset):
    """🔧 Configure OpenVibe CLI settings and API keys.
    
    This command guides you through setting up your OpenVibe CLI configuration,
    including API keys for GitHub, Fly.io, and AI services.
    """
    if reset:
        if Confirm.ask("Are you sure you want to reset all configuration?"):
            config = Config()
            config.save()
            console.print("✅ Configuration reset to defaults", style="green")
        return
    
    console.print(Panel(
        Text("🔧 OpenVibe CLI Setup\n\nThis will configure your CLI settings and API keys.", 
             justify="center"),
        title="Setup",
        border_style="cyan"
    ))
    
    # Load existing config
    config = Config.load()
    
    # Show current configuration
    console.print("\n📋 Current Configuration:", style="bold")
    config_table = Table(show_header=True, header_style="bold magenta")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    config_table.add_column("Status", style="yellow")
    
    config_table.add_row("User UUID", config.user_uuid[:8] + "...", "✅ Set")
    config_table.add_row("Backend URL", config.backend_url, "✅ Set")
    config_table.add_row("GitHub Token", 
                        "***" + (config.github_token[-4:] if config.github_token else "Not set"),
                        "✅ Set" if config.github_token else "❌ Not set")
    config_table.add_row("Fly.io Token",
                        "***" + (config.fly_token[-4:] if config.fly_token else "Not set"),
                        "✅ Set" if config.fly_token else "❌ Not set")
    config_table.add_row("OpenAI API Key",
                        "***" + (config.openai_api_key[-4:] if config.openai_api_key else "Not set"),
                        "✅ Set" if config.openai_api_key else "❌ Not set")
    config_table.add_row("Anthropic API Key",
                        "***" + (config.anthropic_api_key[-4:] if config.anthropic_api_key else "Not set"),
                        "✅ Set" if config.anthropic_api_key else "❌ Not set")
    
    console.print(config_table)
    
    # Ask if user wants to update settings
    if not Confirm.ask("\nWould you like to update any settings?", default=False):
        console.print("✅ Setup complete!", style="green")
        return
    
    console.print("\n🔑 API Key Configuration:", style="bold")
    console.print("Leave blank to keep current values, or enter new values to update.\n")
    
    # Backend URL
    new_backend_url = Prompt.ask(
        "Backend URL",
        default=config.backend_url,
        show_default=True
    )
    if new_backend_url != config.backend_url:
        config.backend_url = new_backend_url
    
    # GitHub Token
    console.print("\n🐙 GitHub Personal Access Token:")
    console.print("   Required for: Repository management, CI/CD status")
    console.print("   Get one at: https://github.com/settings/tokens")
    console.print("   Permissions needed: repo, workflow")
    
    current_github = "***" + config.github_token[-4:] if config.github_token else "Not set"
    new_github_token = Prompt.ask(
        f"GitHub Token (current: {current_github})",
        password=True,
        default=""
    )
    if new_github_token:
        config.github_token = new_github_token
    
    # Fly.io Token
    console.print("\n🛩️ Fly.io API Token:")
    console.print("   Required for: App deployment and management")
    console.print("   Get one at: https://fly.io/user/personal_access_tokens")
    
    current_fly = "***" + config.fly_token[-4:] if config.fly_token else "Not set"
    new_fly_token = Prompt.ask(
        f"Fly.io Token (current: {current_fly})",
        password=True,
        default=""
    )
    if new_fly_token:
        config.fly_token = new_fly_token
    
    # OpenAI API Key
    console.print("\n🤖 OpenAI API Key:")
    console.print("   Required for: GPT-based AI functionality")
    console.print("   Get one at: https://platform.openai.com/api-keys")
    
    current_openai = "***" + config.openai_api_key[-4:] if config.openai_api_key else "Not set"
    new_openai_key = Prompt.ask(
        f"OpenAI API Key (current: {current_openai})",
        password=True,
        default=""
    )
    if new_openai_key:
        config.openai_api_key = new_openai_key
    
    # Anthropic API Key
    console.print("\n🧠 Anthropic API Key:")
    console.print("   Required for: Claude-based AI functionality")
    console.print("   Get one at: https://console.anthropic.com/")
    
    current_anthropic = "***" + config.anthropic_api_key[-4:] if config.anthropic_api_key else "Not set"
    new_anthropic_key = Prompt.ask(
        f"Anthropic API Key (current: {current_anthropic})",
        password=True,
        default=""
    )
    if new_anthropic_key:
        config.anthropic_api_key = new_anthropic_key
    
    # Save configuration
    config.save()
    
    console.print("\n✅ Configuration saved!", style="green")
    
    # Show setup status
    missing = config.get_missing_setup()
    if missing:
        console.print("\n⚠️ Optional setup items:", style="yellow")
        for key, description in missing.items():
            console.print(f"   • {description}", style="dim")
        console.print("\nYou can run 'openvibe setup' again to configure these later.")
    else:
        console.print("\n🎉 All configuration complete! You're ready to use OpenVibe CLI.", style="green")
    
    console.print(f"\n📁 Configuration saved to: {Config.get_config_path()}", style="dim")