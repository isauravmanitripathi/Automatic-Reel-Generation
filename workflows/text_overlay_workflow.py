"""
Text Overlay Workflow - Interactive UI for adding text to videos
Handles all user interaction for text overlay feature
"""

import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

import config
from processors import text_overlay
from utils import validators, file_manager, ffmpeg_helper

console = Console()


def text_overlay_workflow():
    """
    Main interactive workflow for text overlay
    
    Guides user through 7 steps:
    1. Select video
    2. Enter text
    3. Choose box color
    4. Choose text color
    5. Choose opacity
    6. Preview settings
    7. Generate video
    """
    
    console.print("\n[bold cyan]📝 TEXT OVERLAY MODE[/bold cyan]")
    console.print("[dim]Add text with colored background box to your video[/dim]\n")
    
    try:
        # Step 1: Select video
        console.print("[bold cyan]STEP 1: Select Video[/bold cyan]")
        video_path = _select_video()
        
        if not video_path:
            console.print("[red]No video selected. Exiting.[/red]")
            return
        
        # Step 2: Enter text
        console.print("\n[bold cyan]STEP 2: Enter Text[/bold cyan]")
        text = _get_text_input()
        
        if not text:
            console.print("[red]No text entered. Exiting.[/red]")
            return
        
        # Step 3: Choose box color
        console.print("\n[bold cyan]STEP 3: Background Box Color[/bold cyan]")
        box_color = _select_box_color()
        
        # Step 4: Choose text color
        console.print("\n[bold cyan]STEP 4: Text Color[/bold cyan]")
        text_color = _select_text_color()
        
        # Step 5: Choose opacity
        console.print("\n[bold cyan]STEP 5: Box Opacity[/bold cyan]")
        opacity = _select_opacity()
        
        # Step 6: Preview and confirm
        console.print("\n[bold cyan]STEP 6: Preview Settings[/bold cyan]")
        if not _preview_and_confirm(video_path, text, box_color, text_color, opacity):
            console.print("[yellow]Cancelled by user[/yellow]")
            return
        
        # Step 7: Generate video
        console.print("\n[bold cyan]🎬 STEP 7: Generate Video[/bold cyan]")
        output_path = _generate_video(video_path, text, box_color, text_color, opacity)
        
        if output_path:
            console.print(Panel(
                f"[bold green]✅ Success![/bold green]\n\n"
                f"Your video with text overlay is ready:\n[cyan]{output_path}[/cyan]",
                border_style="green"
            ))
        else:
            console.print("[red]❌ Video generation failed[/red]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        if config.DEBUG:
            raise


def _select_video() -> str:
    """
    Step 1: Select input video
    
    Prompts user for video path, validates it, and returns resolved path.
    Allows user to retry on invalid input.
    
    Returns:
        Validated video path or empty string if cancelled
    """
    while True:
        path_input = Prompt.ask("\n[cyan]Enter video path[/cyan]")
        
        # Resolve path (handles ~, relative paths, etc.)
        resolved = file_manager.resolve_path(path_input)
        
        if not resolved:
            console.print("[red]Video not found. Please try again.[/red]")
            continue
        
        # Validate video
        is_valid, message = validators.validate_local_video(resolved)
        
        if not is_valid:
            console.print(f"[red]Invalid video: {message}[/red]")
            
            # Ask if user wants to try anyway
            if Confirm.ask("[yellow]Try anyway?[/yellow]", default=False):
                return resolved
            continue
        
        # Show video info
        info = ffmpeg_helper.get_video_info(resolved)
        if info:
            console.print(
                f"[green]✓[/green] Video: {Path(resolved).name} "
                f"({info['width']}x{info['height']}, {info['duration']:.1f}s)"
            )
        else:
            console.print(f"[green]✓[/green] Video: {Path(resolved).name}")
        
        return resolved


def _get_text_input() -> str:
    """
    Step 2: Get text from user
    
    Prompts for text input with validation:
    - Cannot be empty
    - Maximum 100 characters
    - Will be displayed in one line
    
    Returns:
        Validated text string
    """
    console.print("[dim]Enter the text to display (e.g., website link, watermark)[/dim]")
    console.print("[dim]Max 100 characters, will be displayed in one line[/dim]")
    
    while True:
        text = Prompt.ask("\n[cyan]Text to display[/cyan]")
        
        # Check if empty
        if not text or len(text.strip()) == 0:
            console.print("[red]Text cannot be empty. Please try again.[/red]")
            continue
        
        # Check length
        if len(text) > 100:
            console.print("[red]Text too long (max 100 characters). Please shorten it.[/red]")
            continue
        
        # Valid text
        console.print(f"[green]✓[/green] Text: \"{text}\" ({len(text)} characters)")
        return text


def _select_box_color() -> str:
    """
    Step 3: Select background box color
    
    Presents color options:
    1. Black (default)
    2. White
    3. Red
    4. Blue
    5. Green
    6. Yellow
    7. Custom hex code
    
    Returns:
        Color name or hex code
    """
    console.print("[dim]Choose the background box color[/dim]\n")
    
    # Show available colors
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Color")
    table.add_row("1", "Black (default)")
    table.add_row("2", "White")
    table.add_row("3", "Red")
    table.add_row("4", "Blue")
    table.add_row("5", "Green")
    table.add_row("6", "Yellow")
    table.add_row("7", "Custom (hex code)")
    
    console.print(table)
    
    choice = Prompt.ask(
        "\n[cyan]Choose box color[/cyan]",
        choices=["1", "2", "3", "4", "5", "6", "7"],
        default="1"
    )
    
    # Map choices to color names
    color_map = {
        "1": "black",
        "2": "white",
        "3": "red",
        "4": "blue",
        "5": "green",
        "6": "yellow",
    }
    
    if choice == "7":
        # Custom hex code
        hex_code = Prompt.ask("[cyan]Enter hex color code (e.g., FF0000 for red)[/cyan]")
        # Clean up hex code (remove # or 0x if present)
        hex_clean = hex_code.replace('#', '').replace('0x', '').upper()
        color = f"0x{hex_clean}"
        console.print(f"[green]✓[/green] Box color: {color}")
        return color
    else:
        color = color_map[choice]
        console.print(f"[green]✓[/green] Box color: {color}")
        return color


def _select_text_color() -> str:
    """
    Step 4: Select text color
    
    Presents color options:
    1. White (default)
    2. Black
    3. Yellow
    4. Red
    5. Blue
    6. Custom hex code
    
    Returns:
        Color name or hex code
    """
    console.print("[dim]Choose the text color[/dim]\n")
    
    # Show available colors
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Color")
    table.add_row("1", "White (default)")
    table.add_row("2", "Black")
    table.add_row("3", "Yellow")
    table.add_row("4", "Red")
    table.add_row("5", "Blue")
    table.add_row("6", "Custom (hex code)")
    
    console.print(table)
    
    choice = Prompt.ask(
        "\n[cyan]Choose text color[/cyan]",
        choices=["1", "2", "3", "4", "5", "6"],
        default="1"
    )
    
    # Map choices to color names
    color_map = {
        "1": "white",
        "2": "black",
        "3": "yellow",
        "4": "red",
        "5": "blue",
    }
    
    if choice == "6":
        # Custom hex code
        hex_code = Prompt.ask("[cyan]Enter hex color code (e.g., FFFF00 for yellow)[/cyan]")
        # Clean up hex code
        hex_clean = hex_code.replace('#', '').replace('0x', '').upper()
        color = f"0x{hex_clean}"
        console.print(f"[green]✓[/green] Text color: {color}")
        return color
    else:
        color = color_map[choice]
        console.print(f"[green]✓[/green] Text color: {color}")
        return color


def _select_opacity() -> float:
    """
    Step 5: Select box opacity
    
    Prompts for opacity percentage (0-100%)
    Default: 70%
    Converts to 0-1 range for FFmpeg
    
    Returns:
        Opacity value (0.0 - 1.0)
    """
    console.print("[dim]Set the transparency of the background box (0-100%)[/dim]")
    console.print("[dim]70% is recommended for good visibility[/dim]")
    
    opacity_input = Prompt.ask(
        "\n[cyan]Opacity percentage[/cyan]",
        default="70"
    )
    
    try:
        opacity_percent = float(opacity_input)
        
        # Clamp between 0 and 100
        if opacity_percent < 0:
            opacity_percent = 0
        elif opacity_percent > 100:
            opacity_percent = 100
        
        # Convert to 0-1 range
        opacity = opacity_percent / 100.0
        
        console.print(f"[green]✓[/green] Opacity: {opacity_percent}%")
        return opacity
    
    except ValueError:
        console.print("[yellow]Invalid input, using default 70%[/yellow]")
        return 0.7


def _preview_and_confirm(
    video_path: str,
    text: str,
    box_color: str,
    text_color: str,
    opacity: float
) -> bool:
    """
    Step 6: Show preview of settings and get confirmation
    
    Displays:
    - Video info (name, resolution, duration)
    - Text content and length
    - Estimated font size
    - Estimated box dimensions
    - Colors and opacity
    - Position
    
    Args:
        video_path: Video path
        text: Text to display
        box_color: Box color
        text_color: Text color
        opacity: Box opacity
        
    Returns:
        True if user confirms, False if cancelled
    """
    
    # Get video info
    info = ffmpeg_helper.get_video_info(video_path)
    
    # Calculate preview info using text overlay processor
    preview = text_overlay.preview_text_overlay(video_path, text)
    
    if not preview:
        console.print("[yellow]⚠️  Could not generate preview[/yellow]")
        # Ask if user wants to continue anyway
        return Confirm.ask("[cyan]Continue without preview?[/cyan]", default=True)
    
    # Display preview
    console.print("\n[yellow]📊 Settings Preview:[/yellow]")
    console.print(f"  Video: {Path(video_path).name}")
    
    if info:
        console.print(f"  Resolution: {info['width']}x{info['height']}")
        console.print(f"  Duration: {info['duration']:.1f}s")
    
    console.print(f"\n  Text: \"{text}\"")
    console.print(f"  Text length: {preview['text_length']} characters")
    console.print(f"\n  Font size: {preview['font_size']}px (auto-calculated)")
    console.print(f"  Box dimensions: {preview['box_width']}x{preview['box_height']}px")
    console.print(f"\n  Box color: {box_color}")
    console.print(f"  Text color: {text_color}")
    console.print(f"  Opacity: {int(opacity * 100)}%")
    console.print(f"\n  Position: Bottom center ({config.TEXT_OVERLAY_BOTTOM_MARGIN}px from bottom)")
    
    # Get confirmation
    return Confirm.ask("\n[cyan]Proceed with these settings?[/cyan]", default=True)


def _generate_video(
    video_path: str,
    text: str,
    box_color: str,
    text_color: str,
    opacity: float
) -> str:
    """
    Step 7: Generate the video with text overlay
    
    Creates output filename based on input video name.
    Ensures unique output path to avoid overwriting.
    Calls text overlay processor to generate video.
    
    Args:
        video_path: Input video path
        text: Text to display
        box_color: Box color
        text_color: Text color
        opacity: Box opacity
        
    Returns:
        Path to output video or empty string if failed
    """
    
    # Generate output filename
    video_name = Path(video_path).stem
    output_filename = f"{video_name}_text.mp4"
    output_path = str(config.OUTPUTS_DIR / output_filename)
    
    # Ensure unique path (add _1, _2, etc. if file exists)
    output_path = file_manager.ensure_unique_path(output_path)
    
    console.print(f"\n[cyan]Generating video with text overlay...[/cyan]")
    console.print(f"[dim]This may take a moment depending on video length...[/dim]\n")
    
    # Process video
    with console.status("[cyan]Processing...[/cyan]"):
        result = text_overlay.overlay_text_on_video(
            video_path=video_path,
            output_path=output_path,
            text=text,
            box_color=box_color,
            text_color=text_color,
            box_opacity=opacity
        )
    
    return result if result else ""