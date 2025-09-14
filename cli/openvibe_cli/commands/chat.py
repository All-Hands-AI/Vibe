"""Interactive chat command for OpenVibe CLI."""

import asyncio
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.shortcuts import input_dialog, message_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Frame
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from openvibe_cli.backend import get_backend

console = Console()


class ChatInterface:
    """Interactive chat interface using prompt-toolkit."""
    
    def __init__(self, app_slug: str, riff_slug: str):
        self.app_slug = app_slug
        self.riff_slug = riff_slug
        self.api = get_api_client()
        self.messages: List[Dict[str, Any]] = []
        self.app_data: Optional[Dict[str, Any]] = None
        self.riff_data: Optional[Dict[str, Any]] = None
        self.running = False
        self.polling_thread: Optional[threading.Thread] = None
        
        # UI components
        self.message_area = TextArea(
            text="Loading messages...",
            read_only=True,
            wrap_lines=True,
            scrollbar=True,
            multiline=True,
        )
        
        self.input_area = TextArea(
            height=3,
            multiline=True,
            wrap_lines=True,
            prompt="💬 Message: ",
        )
        
        self.status_bar = Window(
            content=FormattedTextControl(text="Loading..."),
            height=1,
        )
        
        # Key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()
        
        # Layout
        self.layout = Layout(
            HSplit([
                Frame(
                    self.message_area,
                    title="Chat Messages",
                ),
                Frame(
                    self.input_area,
                    title="Type your message (Ctrl+Enter to send, Ctrl+C to exit)",
                ),
                self.status_bar,
            ])
        )
        
        # Style
        self.style = Style.from_dict({
            'frame.border': '#00aa00',
            'frame.title': '#00aa00 bold',
            'status': '#888888',
            'user-message': '#00aa00',
            'assistant-message': '#0088ff',
            'timestamp': '#888888',
            'error': '#ff0000',
        })
        
        # Application
        self.app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            style=self.style,
            full_screen=True,
        )
    
    def _setup_key_bindings(self):
        """Set up key bindings for the chat interface."""
        
        @self.kb.add('c-c')
        def exit_chat(event):
            """Exit the chat interface."""
            self.running = False
            event.app.exit()
        
        @self.kb.add('c-m')  # Ctrl+Enter
        def send_message(event):
            """Send the current message."""
            message_text = self.input_area.text.strip()
            if message_text:
                self._send_message_async(message_text)
                self.input_area.text = ""
        
        @self.kb.add('c-r')  # Ctrl+R
        def refresh_messages(event):
            """Refresh messages manually."""
            self._fetch_messages()
    
    async def initialize(self) -> bool:
        """Initialize the chat interface by loading app and riff data."""
        try:
            # Load app data
            self.app_data = self.api.get_app(self.app_slug)
            
            # Load riff data
            riffs_data = self.api.list_riffs(self.app_slug)
            for riff in riffs_data:
                if riff['slug'] == self.riff_slug:
                    self.riff_data = riff
                    break
            
            if not self.riff_data:
                console.print(f"❌ Riff '{self.riff_slug}' not found in app '{self.app_slug}'", style="red")
                return False
            
            # Load initial messages
            self._fetch_messages()
            
            return True
            
        except APIError as e:
            if e.status_code == 404:
                console.print(f"❌ App '{self.app_slug}' not found", style="red")
            else:
                console.print(f"❌ Error initializing chat: {e.message}", style="red")
            return False
        except Exception as e:
            console.print(f"❌ Unexpected error: {str(e)}", style="red")
            return False
    
    def _fetch_messages(self):
        """Fetch messages from the API and update the display."""
        try:
            new_messages = self.api.list_messages(self.app_slug, self.riff_slug)
            
            # Only update if messages changed
            if new_messages != self.messages:
                self.messages = new_messages
                self._update_message_display()
                self._update_status_bar()
            
        except APIError as e:
            self._update_status_bar(f"Error loading messages: {e.message}", error=True)
        except Exception as e:
            self._update_status_bar(f"Unexpected error: {str(e)}", error=True)
    
    def _update_message_display(self):
        """Update the message display area."""
        if not self.messages:
            self.message_area.text = "No messages yet. Start the conversation!"
            return
        
        formatted_messages = []
        
        for msg in self.messages:
            timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
            time_str = timestamp.strftime('%H:%M:%S')
            
            sender = msg.get('sender', 'user')
            sender_icon = "👤" if sender == 'user' else "🤖"
            sender_name = "You" if sender == 'user' else "Assistant"
            
            # Format message header
            header = f"[{time_str}] {sender_icon} {sender_name}:"
            
            # Format message content
            content = msg.get('content', '').strip()
            
            # Add message to display
            formatted_messages.append(header)
            formatted_messages.append(content)
            formatted_messages.append("")  # Empty line between messages
        
        self.message_area.text = "\n".join(formatted_messages)
        
        # Scroll to bottom
        self.message_area.buffer.cursor_position = len(self.message_area.text)
    
    def _update_status_bar(self, message: Optional[str] = None, error: bool = False):
        """Update the status bar."""
        if message:
            status_text = message
            style = "class:error" if error else "class:status"
        else:
            app_name = self.app_data['name'] if self.app_data else self.app_slug
            riff_name = self.riff_data['name'] if self.riff_data else self.riff_slug
            message_count = len(self.messages)
            
            status_text = f"💬 {app_name} > {riff_name} | {message_count} messages | Live updates every 2s"
            style = "class:status"
        
        self.status_bar.content = FormattedTextControl(
            text=[(style, status_text)]
        )
    
    def _send_message_async(self, content: str):
        """Send a message asynchronously."""
        def send_message_thread():
            try:
                self._update_status_bar("Sending message...", error=False)
                self.api.send_message(self.app_slug, self.riff_slug, content)
                
                # Immediately fetch messages to update display
                self._fetch_messages()
                
            except APIError as e:
                self._update_status_bar(f"Error sending message: {e.message}", error=True)
                # Reset status after 3 seconds
                threading.Timer(3.0, lambda: self._update_status_bar()).start()
            except Exception as e:
                self._update_status_bar(f"Unexpected error: {str(e)}", error=True)
                threading.Timer(3.0, lambda: self._update_status_bar()).start()
        
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=send_message_thread)
        thread.daemon = True
        thread.start()
    
    def _start_polling(self):
        """Start polling for new messages."""
        def polling_loop():
            while self.running:
                self._fetch_messages()
                time.sleep(2)  # Poll every 2 seconds like the frontend
        
        self.polling_thread = threading.Thread(target=polling_loop)
        self.polling_thread.daemon = True
        self.polling_thread.start()
    
    def run(self):
        """Run the chat interface."""
        self.running = True
        self._start_polling()
        
        try:
            self.app.run()
        finally:
            self.running = False
            if self.polling_thread:
                self.polling_thread.join(timeout=1)


@click.command()
@click.argument('app_slug')
@click.argument('riff_slug')
@click.option('--simple', is_flag=True, help='Use simple line-by-line chat instead of full-screen interface')
def chat(app_slug, riff_slug, simple):
    """💬 Start an interactive chat session with a riff.
    
    APP_SLUG: The slug of the app
    RIFF_SLUG: The slug of the riff to chat with
    
    Controls:
    • Ctrl+Enter: Send message
    • Ctrl+R: Refresh messages
    • Ctrl+C: Exit chat
    """
    if simple:
        _run_simple_chat(app_slug, riff_slug)
    else:
        _run_full_screen_chat(app_slug, riff_slug)


def _run_full_screen_chat(app_slug: str, riff_slug: str):
    """Run the full-screen chat interface."""
    chat_interface = ChatInterface(app_slug, riff_slug)
    
    # Initialize the chat interface
    console.print("🔄 Initializing chat...", style="yellow")
    
    # Run initialization in a way that works with the current event loop
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an existing event loop, we need to handle this differently
            success = asyncio.run_coroutine_threadsafe(chat_interface.initialize(), loop).result()
        else:
            success = asyncio.run(chat_interface.initialize())
    except RuntimeError:
        # Fallback to sync initialization
        success = True
        try:
            chat_interface.app_data = chat_interface.api.get_app(app_slug)
            riffs_data = chat_interface.api.list_riffs(app_slug)
            for riff in riffs_data:
                if riff['slug'] == riff_slug:
                    chat_interface.riff_data = riff
                    break
            if not chat_interface.riff_data:
                console.print(f"❌ Riff '{riff_slug}' not found in app '{app_slug}'", style="red")
                return
            chat_interface._fetch_messages()
        except APIError as e:
            console.print(f"❌ Error initializing chat: {e.message}", style="red")
            return
        except Exception as e:
            console.print(f"❌ Unexpected error: {str(e)}", style="red")
            return
    
    if not success:
        return
    
    console.print("✅ Chat initialized! Starting interface...", style="green")
    console.print("💡 Use Ctrl+Enter to send messages, Ctrl+C to exit", style="dim")
    
    try:
        chat_interface.run()
    except KeyboardInterrupt:
        console.print("\n👋 Chat session ended", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Error in chat interface: {str(e)}", style="red")


def _run_simple_chat(app_slug: str, riff_slug: str):
    """Run a simple line-by-line chat interface."""
    try:
        api = get_api_client()
        
        # Initialize
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing chat...", total=None)
            
            app_data = api.get_app(app_slug)
            riffs_data = api.list_riffs(app_slug)
            
            riff_data = None
            for riff in riffs_data:
                if riff['slug'] == riff_slug:
                    riff_data = riff
                    break
            
            if not riff_data:
                progress.remove_task(task)
                console.print(f"❌ Riff '{riff_slug}' not found in app '{app_slug}'", style="red")
                return
            
            messages = api.list_messages(app_slug, riff_slug)
            progress.remove_task(task)
        
        console.print(f"💬 Chat: {app_data['name']} > {riff_data['name']}", style="bold cyan")
        console.print("Type 'exit' or 'quit' to end the chat session\n")
        
        # Display existing messages
        if messages:
            console.print("📜 Message History:", style="bold")
            for msg in messages[-10:]:  # Show last 10 messages
                timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                time_str = timestamp.strftime('%H:%M')
                
                sender = msg.get('sender', 'user')
                sender_icon = "👤" if sender == 'user' else "🤖"
                sender_name = "You" if sender == 'user' else "Assistant"
                
                console.print(f"[{time_str}] {sender_icon} {sender_name}: {msg.get('content', '')}")
            
            if len(messages) > 10:
                console.print(f"... and {len(messages) - 10} more messages")
            console.print()
        
        # Chat loop
        session = PromptSession()
        
        while True:
            try:
                user_input = session.prompt("💬 You: ")
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("👋 Goodbye!", style="yellow")
                    break
                
                if not user_input.strip():
                    continue
                
                # Send message
                console.print("📤 Sending...", style="dim")
                api.send_message(app_slug, riff_slug, user_input)
                
                # Wait a moment and fetch new messages
                time.sleep(1)
                new_messages = api.list_messages(app_slug, riff_slug)
                
                # Show new messages since last check
                for msg in new_messages[len(messages):]:
                    timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                    time_str = timestamp.strftime('%H:%M')
                    
                    sender = msg.get('sender', 'user')
                    if sender != 'user':  # Don't show user's own message again
                        sender_icon = "🤖"
                        sender_name = "Assistant"
                        console.print(f"[{time_str}] {sender_icon} {sender_name}: {msg.get('content', '')}")
                
                messages = new_messages
                
            except KeyboardInterrupt:
                console.print("\n👋 Chat session ended", style="yellow")
                break
            except EOFError:
                console.print("\n👋 Chat session ended", style="yellow")
                break
            except APIError as e:
                console.print(f"❌ Error: {e.message}", style="red")
            except Exception as e:
                console.print(f"❌ Unexpected error: {str(e)}", style="red")
    
    except APIError as e:
        if e.status_code == 404:
            console.print(f"❌ App '{app_slug}' not found", style="red")
        else:
            console.print(f"❌ Error: {e.message}", style="red")
    except Exception as e:
        console.print(f"❌ Unexpected error: {str(e)}", style="red")