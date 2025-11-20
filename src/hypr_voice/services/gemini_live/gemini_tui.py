#!/usr/bin/env python3
"""Interactive TUI chat client for Gemini Live with multimodal support using Rich."""

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Union

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Support both relative and absolute imports
try:
    from .gemini_client import GeminiClient, GeminiConfig, LIVE_MODELS, MODEL_MAX_OUTPUT_TOKENS, WEBSOCKET_MODELS
except ImportError:
    from gemini_client import GeminiClient, GeminiConfig, LIVE_MODELS, MODEL_MAX_OUTPUT_TOKENS, WEBSOCKET_MODELS

console = Console()


class GeminiTUI:
    """TUI for Gemini Live API with multimodal support."""

    def __init__(self):
        self.client: Optional[GeminiClient] = None
        self.messages: List[Dict[str, str]] = []
        self.current_model: Optional[str] = None
        self.available_models = LIVE_MODELS
        self.streaming = True
        self.temperature = 0.7
        self.max_tokens = 16384  # Will be updated based on model
        self.system_instruction: Optional[str] = None
        self.current_images: List[Path] = []
        
        # Token tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
    
    def _update_max_tokens_for_model(self):
        """Update max_tokens based on selected model's capabilities."""
        if self.current_model and self.current_model in MODEL_MAX_OUTPUT_TOKENS:
            model_max = MODEL_MAX_OUTPUT_TOKENS[self.current_model]
            # Use reasonable default (not full max to save tokens)
            # For Live models with 1M limit, use 16K as default
            # For others, use their max
            if model_max >= 1000000:
                self.max_tokens = 16384
            elif model_max >= 65536:
                self.max_tokens = 8192
            else:
                self.max_tokens = model_max

    async def initialize(self):
        """Initialize the Gemini client."""
        try:
            config = GeminiConfig.from_env()
            self.client = GeminiClient(config)
            self.current_model = config.model
            self._update_max_tokens_for_model()
            console.print("[bold green]✓ Gemini client initialized[/bold green]")
            console.print(f"[dim]Using model: {self.current_model}[/dim]")
            console.print(f"[dim]Max output tokens: {self.max_tokens}[/dim]")
        except Exception as e:
            console.print(f"[bold red]✗ Failed to initialize: {e}[/bold red]")
            console.print("\n[yellow]Make sure you have set GEMINI_API_KEY or GOOGLE_API_KEY environment variable.[/yellow]")
            sys.exit(1)

    def show_header(self):
        """Display the chat header."""
        header = Table.grid(expand=True)
        header.add_column(justify="center")
        header.add_row(
            Text("🔮 Gemini Live TUI", style="bold magenta", justify="center")
        )
        header.add_row(
            Text("Multimodal AI with Text & Images", style="dim cyan", justify="center")
        )
        return Panel(header, style="magenta")

    def show_status(self):
        """Display current status."""
        status = Table.grid(expand=False)
        status.add_column(style="dim", width=18)
        status.add_column(style="bold")
        
        status.add_row("Model:", f"[cyan]{self.current_model}[/cyan]")
        status.add_row("Streaming:", f"[{'green' if self.streaming else 'yellow'}]{self.streaming}[/]")
        status.add_row("Temperature:", f"[magenta]{self.temperature}[/magenta]")
        status.add_row("Max Tokens:", f"[blue]{self.max_tokens}[/blue]")
        status.add_row("Messages:", f"[yellow]{len(self.messages)}[/yellow]")
        status.add_row("Images Loaded:", f"[green]{len(self.current_images)}[/green]")
        
        if self.total_tokens > 0:
            status.add_row("", "")
            status.add_row("Total Tokens:", f"[bold cyan]{self.total_tokens:,}[/bold cyan]")
            status.add_row("  Prompt:", f"[dim]{self.total_prompt_tokens:,}[/dim]")
            status.add_row("  Completion:", f"[dim]{self.total_completion_tokens:,}[/dim]")
        
        return Panel(status, title="[bold]Status[/bold]", border_style="dim")

    def show_commands(self):
        """Display available commands."""
        commands = Table(show_header=False, expand=True, box=None)
        commands.add_column(style="cyan", width=14)
        commands.add_column(style="dim")
        
        commands.add_row("/model", "Select model")
        commands.add_row("/image", "Add image(s)")
        commands.add_row("/clear-img", "Clear loaded images")
        commands.add_row("/stream", "Toggle streaming")
        commands.add_row("/temp", "Set temperature")
        commands.add_row("/tokens", "Set max tokens")
        commands.add_row("/system", "Set system instruction")
        commands.add_row("/reset", "Clear history")
        commands.add_row("/stats", "Show token stats")
        commands.add_row("/help", "Show commands")
        commands.add_row("/quit", "Exit chat")
        
        return Panel(commands, title="[bold]Commands[/bold]", border_style="dim")

    def select_model(self):
        """Interactive model selection."""
        console.print("\n[bold cyan]Available Models:[/bold cyan]")
        for i, model in enumerate(self.available_models, 1):
            marker = "→" if model == self.current_model else " "
            max_out = MODEL_MAX_OUTPUT_TOKENS.get(model, 8192)
            ws_badge = " [bold magenta]⚡LIVE[/bold magenta]" if model in WEBSOCKET_MODELS else ""
            console.print(f"{marker} {i}. [cyan]{model}[/cyan]{ws_badge} [dim](max: {max_out:,})[/dim]")
        
        choice = Prompt.ask(
            "\nSelect model number",
            default=str(self.available_models.index(self.current_model) + 1) if self.current_model in self.available_models else "1"
        )
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.available_models):
                self.current_model = self.available_models[idx]
                self._update_max_tokens_for_model()
                console.print(f"[green]✓ Model set to {self.current_model}[/green]")
                console.print(f"[dim]Max output tokens updated to: {self.max_tokens:,}[/dim]")
            else:
                console.print("[red]Invalid selection[/red]")
        except ValueError:
            console.print("[red]Invalid input[/red]")

    def add_images(self):
        """Add image files to the current context."""
        console.print("\n[bold cyan]Add Images:[/bold cyan]")
        console.print("[dim]Enter image path(s), separated by commas[/dim]")
        console.print("[dim]Example: /path/to/image1.jpg, /path/to/image2.png[/dim]")
        
        paths_str = Prompt.ask("Image path(s)")
        if not paths_str.strip():
            return
        
        paths = [p.strip() for p in paths_str.split(",")]
        added = []
        
        for path_str in paths:
            path = Path(path_str).expanduser().resolve()
            if path.exists() and path.is_file():
                if path.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]:
                    self.current_images.append(path)
                    added.append(path.name)
                else:
                    console.print(f"[yellow]⚠ Skipping non-image file: {path.name}[/yellow]")
            else:
                console.print(f"[red]✗ File not found: {path_str}[/red]")
        
        if added:
            console.print(f"[green]✓ Added {len(added)} image(s): {', '.join(added)}[/green]")

    def clear_images(self):
        """Clear all loaded images."""
        count = len(self.current_images)
        self.current_images.clear()
        console.print(f"[green]✓ Cleared {count} image(s)[/green]")

    def show_stats(self):
        """Display detailed token statistics."""
        stats = Table(title="Token Usage Statistics", show_header=True, header_style="bold cyan")
        stats.add_column("Metric", style="dim")
        stats.add_column("Value", justify="right", style="bold")
        
        stats.add_row("Total Tokens", f"{self.total_tokens:,}")
        stats.add_row("Prompt Tokens", f"{self.total_prompt_tokens:,}")
        stats.add_row("Completion Tokens", f"{self.total_completion_tokens:,}")
        
        if self.total_tokens > 0:
            avg_msg = self.total_tokens / max(len(self.messages) // 2, 1)
            stats.add_row("Avg Tokens/Message", f"{avg_msg:.1f}")
        
        console.print(stats)

    def handle_command(self, command: str) -> bool:
        """Handle slash commands. Returns False if should quit."""
        if command == "/quit" or command == "/q":
            return False
        
        elif command == "/model" or command == "/m":
            self.select_model()
        
        elif command == "/image" or command == "/img":
            self.add_images()
        
        elif command == "/clear-img" or command == "/ci":
            self.clear_images()
        
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
            model_max = MODEL_MAX_OUTPUT_TOKENS.get(self.current_model, 8192)
            tokens = Prompt.ask(f"Max tokens (1-{model_max:,})", default=str(self.max_tokens))
            try:
                self.max_tokens = max(1, min(model_max, int(tokens)))
                console.print(f"[green]✓ Max tokens set to {self.max_tokens:,}[/green]")
            except ValueError:
                console.print("[red]Invalid token count[/red]")
        
        elif command == "/system":
            instruction = Prompt.ask("System instruction (empty to clear)", default=self.system_instruction or "")
            self.system_instruction = instruction if instruction.strip() else None
            if self.system_instruction:
                console.print(f"[green]✓ System instruction set[/green]")
            else:
                console.print(f"[green]✓ System instruction cleared[/green]")
        
        elif command == "/reset" or command == "/r":
            self.messages.clear()
            self.clear_images()
            console.print("[green]✓ Conversation reset[/green]")
        
        elif command == "/stats":
            self.show_stats()
        
        elif command == "/help" or command == "/h":
            console.print(self.show_commands())
        
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("[dim]Type /help for available commands[/dim]")
        
        return True

    async def send_message(self, user_message: str):
        """Send a message and get response."""
        # Prepare content (text + images)
        content = []
        
        # Add images first
        for img_path in self.current_images:
            content.append(img_path)
        
        # Add text
        content.append(user_message)
        
        # Store in message history
        msg_content = user_message
        if self.current_images:
            msg_content = f"[{len(self.current_images)} image(s)] {user_message}"
        
        self.messages.append({"role": "user", "content": msg_content})
        
        # Display user message
        console.print(Panel(
            Markdown(user_message),
            title=f"[bold cyan]You[/bold cyan] {'🖼️ ' if self.current_images else ''}",
            border_style="cyan"
        ))
        
        if self.streaming:
            await self.stream_response(content)
        else:
            await self.normal_response(content)
        
        # Clear images after sending
        self.current_images.clear()

    async def stream_response(self, content):
        """Stream response token by token with tokens/sec display."""
        console.print()
        
        chunks = []
        start_time = time.time()
        token_count = 0
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Streaming..."),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("", total=None)
                
                async for chunk_data in self.client.stream_content(
                    content,
                    model=self.current_model,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    system_instruction=self.system_instruction,
                ):
                    chunk_text = chunk_data.get("content", "")
                    if chunk_text:
                        chunks.append(chunk_text)
                        progress.stop()
                        console.print(chunk_text, end="", markup=False)
                    
                    # Update token stats from final chunk
                    if chunk_data.get("is_final") and chunk_data.get("usage"):
                        usage = chunk_data["usage"]
                        self.total_prompt_tokens += usage.get("prompt_tokens", 0) or 0
                        self.total_completion_tokens += usage.get("completion_tokens", 0) or 0
                        self.total_tokens += usage.get("total_tokens", 0) or 0
                        token_count = usage.get("completion_tokens", 0) or 0
            
            elapsed = time.time() - start_time
            tokens_per_sec = token_count / elapsed if elapsed > 0 else 0
            
            full_response = "".join(chunks)
            self.messages.append({"role": "assistant", "content": full_response})
            
            # Display stats
            console.print("\n")
            stats_text = f"[dim]Tokens: {token_count} | Speed: {tokens_per_sec:.1f} tok/s | Time: {elapsed:.2f}s[/dim]"
            console.print(stats_text)
            console.print()
            
        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]\n")

    async def normal_response(self, content):
        """Get complete response at once."""
        try:
            with console.status("[bold green]Thinking...[/bold green]"):
                start_time = time.time()
                response = await self.client.generate_content(
                    content,
                    model=self.current_model,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    system_instruction=self.system_instruction,
                )
            
            elapsed = time.time() - start_time
            content_text = response.get("content", "")
            usage = response.get("usage", {})
            
            # Update stats
            self.total_prompt_tokens += usage.get("prompt_tokens", 0) or 0
            self.total_completion_tokens += usage.get("completion_tokens", 0) or 0
            self.total_tokens += usage.get("total_tokens", 0) or 0
            
            token_count = usage.get("completion_tokens", 0) or 0
            tokens_per_sec = token_count / elapsed if elapsed > 0 else 0
            
            self.messages.append({"role": "assistant", "content": content_text})
            
            # Display response
            console.print(Panel(
                Markdown(content_text),
                title="[bold green]Assistant[/bold green]",
                border_style="green",
                subtitle=f"[dim]{token_count} tokens | {tokens_per_sec:.1f} tok/s | {elapsed:.2f}s[/dim]"
            ))
            
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

    async def run(self):
        """Main chat loop."""
        await self.initialize()
        
        console.clear()
        console.print(self.show_header())
        console.print()
        console.print(self.show_status())
        console.print()
        console.print("[dim]Type your message, /image to add images, or /help for commands[/dim]")
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
        
        console.print("\n[bold magenta]👋 Goodbye![/bold magenta]")


async def main():
    """Entry point."""
    chat = GeminiTUI()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold magenta]👋 Goodbye![/bold magenta]")

