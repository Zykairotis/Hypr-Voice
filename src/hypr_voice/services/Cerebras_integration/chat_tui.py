#!/usr/bin/env python3
"""Simple TUI chat client for Cerebras models using Rich."""

import asyncio
import sys
from typing import List, Dict, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from client import CerebrasClient, CerebrasConfig

console = Console()


class ChatTUI:
    def __init__(self):
        self.client: Optional[CerebrasClient] = None
        self.messages: List[Dict[str, str]] = []
        self.current_model: Optional[str] = None
        self.available_models = [
            "gpt-oss-120b",
            "llama-3.3-70b",
            "llama-4-scout-17b-16e-instruct",
            "llama3.1-8b",
            "qwen-3-235b-a22b-instruct-2507",
            "qwen-3-235b-a22b-thinking-2507",
            "qwen-3-32b",
            "qwen-3-coder-480b",
        ]
        self.streaming = True
        self.temperature = 0.7
        self.max_tokens = 16000

    async def initialize(self):
        """Initialize the Cerebras client."""
        try:
            config = CerebrasConfig.from_env()
            self.client = CerebrasClient(config)
            self.current_model = config.model_priority[0] if config.model_priority else "gpt-oss-120b"
            console.print("[bold green]✓ Client initialized[/bold green]")
        except Exception as e:
            console.print(f"[bold red]✗ Failed to initialize: {e}[/bold red]")
            sys.exit(1)

    def show_header(self):
        """Display the chat header."""
        header = Table.grid(expand=True)
        header.add_column(justify="center")
        header.add_row(
            Text("🤖 Cerebras Chat TUI", style="bold cyan", justify="center")
        )
        return Panel(header, style="cyan")

    def show_status(self):
        """Display current status."""
        status = Table.grid(expand=False)
        status.add_column(style="dim")
        status.add_column(style="bold")
        
        status.add_row("Model:", f"[cyan]{self.current_model}[/cyan]")
        status.add_row("Streaming:", f"[{'green' if self.streaming else 'yellow'}]{self.streaming}[/]")
        status.add_row("Temperature:", f"[magenta]{self.temperature}[/magenta]")
        status.add_row("Max Tokens:", f"[blue]{self.max_tokens}[/blue]")
        status.add_row("Messages:", f"[yellow]{len(self.messages)}[/yellow]")
        
        return Panel(status, title="[bold]Status[/bold]", border_style="dim")

    def show_commands(self):
        """Display available commands."""
        commands = Table(show_header=False, expand=True, box=None)
        commands.add_column(style="cyan", width=12)
        commands.add_column(style="dim")
        
        commands.add_row("/model", "Select model")
        commands.add_row("/stream", "Toggle streaming")
        commands.add_row("/temp", "Set temperature")
        commands.add_row("/tokens", "Set max tokens")
        commands.add_row("/reset", "Clear history")
        commands.add_row("/help", "Show commands")
        commands.add_row("/quit", "Exit chat")
        
        return Panel(commands, title="[bold]Commands[/bold]", border_style="dim")

    def select_model(self):
        """Interactive model selection."""
        console.print("\n[bold cyan]Available Models:[/bold cyan]")
        for i, model in enumerate(self.available_models, 1):
            marker = "→" if model == self.current_model else " "
            console.print(f"{marker} {i}. [cyan]{model}[/cyan]")
        
        choice = Prompt.ask(
            "\nSelect model number",
            default=str(self.available_models.index(self.current_model) + 1)
        )
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.available_models):
                self.current_model = self.available_models[idx]
                console.print(f"[green]✓ Model set to {self.current_model}[/green]")
            else:
                console.print("[red]Invalid selection[/red]")
        except ValueError:
            console.print("[red]Invalid input[/red]")

    def handle_command(self, command: str) -> bool:
        """Handle slash commands. Returns False if should quit."""
        if command == "/quit" or command == "/q":
            return False
        
        elif command == "/model" or command == "/m":
            self.select_model()
        
        elif command == "/stream" or command == "/s":
            self.streaming = not self.streaming
            console.print(f"[green]✓ Streaming {'enabled' if self.streaming else 'disabled'}[/green]")
        
        elif command == "/temp" or command == "/t":
            temp = Prompt.ask("Temperature (0.0-2.0)", default=str(self.temperature))
            try:
                self.temperature = max(0.0, min(2.0, float(temp)))
                console.print(f"[green]✓ Temperature set to {self.temperature}[/green]")
            except ValueError:
                console.print("[red]Invalid temperature[/red]")
        
        elif command == "/tokens":
            tokens = Prompt.ask("Max tokens", default=str(self.max_tokens))
            try:
                self.max_tokens = max(1, min(65536, int(tokens)))
                console.print(f"[green]✓ Max tokens set to {self.max_tokens}[/green]")
            except ValueError:
                console.print("[red]Invalid token count[/red]")
        
        elif command == "/reset" or command == "/r":
            self.messages.clear()
            console.print("[green]✓ Conversation reset[/green]")
        
        elif command == "/help" or command == "/h":
            console.print(self.show_commands())
        
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("[dim]Type /help for available commands[/dim]")
        
        return True

    async def send_message(self, user_message: str):
        """Send a message and get response."""
        self.messages.append({"role": "user", "content": user_message})
        
        console.print(Panel(
            Markdown(user_message),
            title="[bold cyan]You[/bold cyan]",
            border_style="cyan"
        ))
        
        if self.streaming:
            await self.stream_response()
        else:
            await self.normal_response()

    async def stream_response(self):
        """Stream response token by token."""
        console.print()
        
        chunks = []
        
        with console.status("[bold green]Generating...[/bold green]") as status:
            async for chunk in self.client.stream_chat(
                self.messages,
                model=self.current_model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            ):
                chunks.append(chunk)
                status.stop()
                console.print(chunk, end="", markup=False)
        
        full_response = "".join(chunks)
        self.messages.append({"role": "assistant", "content": full_response})
        console.print("\n")

    async def normal_response(self):
        """Get complete response at once."""
        with console.status("[bold green]Thinking...[/bold green]"):
            response = await self.client.chat(
                self.messages,
                model=self.current_model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        
        content = response.get("content", "")
        self.messages.append({"role": "assistant", "content": content})
        
        console.print(Panel(
            Markdown(content),
            title="[bold green]Assistant[/bold green]",
            border_style="green"
        ))

    async def run(self):
        """Main chat loop."""
        await self.initialize()
        
        console.clear()
        console.print(self.show_header())
        console.print()
        console.print(self.show_status())
        console.print()
        console.print("[dim]Type your message or /help for commands[/dim]")
        console.print()
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    if not self.handle_command(user_input):
                        break
                    continue
                
                # Send message
                await self.send_message(user_input)
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Use /quit to exit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                console.print(f"\n[bold red]Error: {e}[/bold red]")
        
        # Cleanup
        if self.client:
            await self.client.close()
        
        console.print("\n[bold cyan]👋 Goodbye![/bold cyan]")


async def main():
    """Entry point."""
    chat = ChatTUI()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold cyan]👋 Goodbye![/bold cyan]")

