#!/usr/bin/env python3
"""
Better Reel Generator - Main Entry Point
A modular video generator for creating social media content
"""

import sys
import os
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

# Import config
import config

# Import modules
from downloaders import youtube, instagram, pinterest
from processors import normalizer, combiner, audio_analyzer, video_cutter, image_overlay
from utils import validators, file_manager, ffmpeg_helper

# Import workflows
from workflows.text_overlay_workflow import text_overlay_workflow

# Initialize Rich console
console = Console()


# ============================================================================
# MAIN CLI APPLICATION
# ============================================================================

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--version', is_flag=True, help='Show version')
def cli(ctx, version):
    """
    Better Reel Generator - Create awesome social media videos
    
    Run without arguments for interactive mode, or use flags for automation.
    """
    if version:
        console.print(f"[cyan]{config.APP_NAME} v{config.VERSION}[/cyan]")
        return
    
    if ctx.invoked_subcommand is None:
        # No subcommand = interactive mode
        interactive_mode()


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

def interactive_mode():
    """Guided interactive mode with step-by-step prompts"""
    
    # Display welcome banner
    console.print(Panel.fit(
        f"[bold cyan]{config.APP_NAME}[/bold cyan]\n"
        f"[dim]Version {config.VERSION}[/dim]\n\n"
        "[yellow]Create beat-synced videos from any source[/yellow]",
        border_style="cyan"
    ))
    
    # Show main menu
    console.print("\n[bold cyan]What would you like to do?[/bold cyan]")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Description")
    table.add_row("1", "Generate beat-synced reel (standard workflow)")
    table.add_row("2", "Overlay images on video with animations")
    table.add_row("3", "Add text/logo overlay with background box")
    
    console.print(table)
    
    mode_choice = Prompt.ask(
        "\n[cyan]Choose mode[/cyan]",
        choices=["1", "2", "3"],
        default="1"
    )
    
    try:
        if mode_choice == "1":
            # Standard reel generation workflow
            standard_workflow()
        elif mode_choice == "2":
            # Image overlay workflow
            image_overlay_workflow()
        elif mode_choice == "3":
            # Text overlay workflow
            text_overlay_workflow()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Process interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        if config.DEBUG:
            raise


def standard_workflow():
    """Standard beat-synced reel generation workflow"""
    
    # Step 1: Video Source Selection
    console.print("\n[bold cyan]📥 STEP 1: Select Video Source[/bold cyan]")
    video_paths = video_source_phase()
    
    if not video_paths:
        console.print("[red]No videos selected. Exiting.[/red]")
        return
    
    # Step 2: Normalization/Combination Phase
    console.print("\n[bold cyan]🔧 STEP 2: Process Videos[/bold cyan]")
    processed_video = process_videos_phase(video_paths)
    
    if not processed_video:
        console.print("[red]Video processing failed. Exiting.[/red]")
        return
    
    # Step 3: Audio Selection
    console.print("\n[bold cyan]🎵 STEP 3: Select Audio[/bold cyan]")
    audio_path = audio_selection_phase()
    
    if not audio_path:
        console.print("[red]No audio selected. Exiting.[/red]")
        return
    
    # Step 4: Cutting Configuration
    console.print("\n[bold cyan]✂️  STEP 4: Configure Cuts[/bold cyan]")
    cut_config = cutting_configuration_phase(audio_path)
    
    # Step 5: Generate Final Video
    console.print("\n[bold cyan]🎬 STEP 5: Generate Video[/bold cyan]")
    final_video = generate_video_phase(processed_video, audio_path, cut_config)
    
    if final_video:
        console.print(Panel(
            f"[bold green]✅ Success![/bold green]\n\n"
            f"Your video is ready:\n[cyan]{final_video}[/cyan]",
            border_style="green"
        ))
    else:
        console.print("[red]Video generation failed.[/red]")


def image_overlay_workflow():
    """Image overlay workflow"""
    
    console.print("\n[bold cyan]🖼️  IMAGE OVERLAY MODE[/bold cyan]")
    console.print("[dim]Overlay images from a folder onto a background video with animations[/dim]\n")
    
    # Step 1: Select background video
    console.print("[bold cyan]STEP 1: Select Background Video[/bold cyan]")
    
    video_path = None
    while not video_path:
        path_input = Prompt.ask("\n[cyan]Enter background video path[/cyan]")
        
        # Resolve path
        resolved = file_manager.resolve_path(path_input)
        
        if not resolved:
            console.print("[red]Video not found. Please try again.[/red]")
            continue
        
        # Validate video
        is_valid, message = validators.validate_local_video(resolved)
        
        if not is_valid:
            console.print(f"[red]Invalid video: {message}[/red]")
            
            if Confirm.ask("[yellow]Try anyway?[/yellow]", default=False):
                video_path = resolved
            continue
        
        video_path = resolved
        
        # Show video info
        info = ffmpeg_helper.get_video_info(video_path)
        if info:
            console.print(
                f"[green]✓[/green] Video: {Path(video_path).name} "
                f"({info['width']}x{info['height']}, {info['duration']:.1f}s)"
            )
    
    # Step 2: Select images folder
    console.print("\n[bold cyan]STEP 2: Select Images Folder[/bold cyan]")
    
    images_folder = None
    num_images = 0
    
    while not images_folder:
        folder_input = Prompt.ask("\n[cyan]Enter folder path containing images[/cyan]")
        
        # Resolve path
        resolved = file_manager.resolve_path(folder_input)
        
        if not resolved:
            console.print("[red]Folder not found. Please try again.[/red]")
            continue
        
        if not os.path.isdir(resolved):
            console.print("[red]Path is not a folder. Please try again.[/red]")
            continue
        
        # Check for images
        images = image_overlay.get_images_from_folder(resolved)
        
        if not images:
            console.print("[red]No images found in folder. Please try again.[/red]")
            continue
        
        images_folder = resolved
        num_images = len(images)
        
        console.print(f"[green]✓[/green] Found {num_images} images in folder")
        
        # Show first few image names
        console.print("[dim]Images:[/dim]")
        for img in images[:5]:
            console.print(f"  [dim]- {Path(img).name}[/dim]")
        if len(images) > 5:
            console.print(f"  [dim]... and {len(images) - 5} more[/dim]")
    
    # Step 3: Configure timing
    console.print("\n[bold cyan]STEP 3: Configure Timing[/bold cyan]")
    
    video_duration = ffmpeg_helper.get_video_duration(video_path)
    
    # Auto-calculate or manual?
    auto_duration = Confirm.ask(
        f"\n[cyan]Auto-calculate duration per image?[/cyan]\n"
        f"[dim](Video is {video_duration:.1f}s, {num_images} images)[/dim]",
        default=True
    )
    
    duration_per_image = None
    
    if not auto_duration:
        # Manual duration
        default_duration = video_duration / num_images
        duration_input = Prompt.ask(
            f"[cyan]Duration per image (seconds)[/cyan]",
            default=f"{default_duration:.2f}"
        )
        
        try:
            duration_per_image = float(duration_input)
            if duration_per_image <= 0:
                console.print("[yellow]Invalid duration, using auto-calculate[/yellow]")
                duration_per_image = None
        except ValueError:
            console.print("[yellow]Invalid input, using auto-calculate[/yellow]")
            duration_per_image = None
    
    # Delay between images
    use_delay = Confirm.ask(
        "\n[cyan]Add delay between images?[/cyan]",
        default=False
    )
    
    delay_between_images = 0.0
    
    if use_delay:
        delay_input = Prompt.ask(
            "[cyan]Delay duration (seconds)[/cyan]",
            default="0.5"
        )
        
        try:
            delay_between_images = float(delay_input)
            if delay_between_images < 0:
                delay_between_images = 0.0
        except ValueError:
            delay_between_images = 0.0
    
    # Preview timing
    console.print("\n[yellow]📊 Timing Preview:[/yellow]")
    
    preview = image_overlay.preview_image_timing(
        num_images=num_images,
        video_duration=video_duration,
        duration_per_image=duration_per_image,
        delay_between_images=delay_between_images
    )
    
    if preview:
        console.print(f"  Duration per image: [cyan]{preview['duration_per_image']:.2f}s[/cyan]")
        console.print(f"  Delay between images: [cyan]{delay_between_images:.2f}s[/cyan]")
        console.print(f"  Total timeline: [cyan]{preview['total_duration']:.2f}s[/cyan]")
        
        if preview['total_duration'] > video_duration:
            console.print(f"  [yellow]⚠️  Warning: Timeline exceeds video duration (images will be cut off)[/yellow]")
    
    proceed = Confirm.ask("\n[cyan]Proceed with these settings?[/cyan]", default=True)
    
    if not proceed:
        console.print("[yellow]Cancelled by user[/yellow]")
        return
    
    # Step 4: Choose animation style
    console.print("\n[bold cyan]STEP 4: Choose Animation Style[/bold cyan]")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Animation Style")
    table.add_row("1", "Random (mix of all styles)")
    table.add_row("2", "Slide from bottom")
    table.add_row("3", "Slide from top")
    table.add_row("4", "Slide from left")
    table.add_row("5", "Slide from right")
    table.add_row("6", "Fade in/out")
    
    console.print(table)
    
    animation_choice = Prompt.ask(
        "\n[cyan]Choose animation style[/cyan]",
        choices=["1", "2", "3", "4", "5", "6"],
        default="1"
    )
    
    animation_map = {
        "1": "random",
        "2": "slide_bottom",
        "3": "slide_top",
        "4": "slide_left",
        "5": "slide_right",
        "6": "fade"
    }
    
    animation_style = animation_map[animation_choice]
    
    # Step 5: Generate video
    console.print("\n[bold cyan]🎬 STEP 5: Generate Video[/bold cyan]")
    
    output_filename = Prompt.ask(
        "\n[cyan]Output filename[/cyan]",
        default="overlay_video.mp4"
    )
    
    output_path = str(config.OUTPUTS_DIR / output_filename)
    
    # Ensure unique path
    output_path = file_manager.ensure_unique_path(output_path)
    
    console.print(f"\n[cyan]Generating video with image overlays...[/cyan]")
    console.print(f"[dim]This may take a few minutes...[/dim]\n")
    
    with console.status("[cyan]Processing...[/cyan]"):
        result = image_overlay.overlay_images_on_video(
            video_path=video_path,
            images_folder=images_folder,
            output_path=output_path,
            duration_per_image=duration_per_image,
            delay_between_images=delay_between_images,
            animation_style=animation_style
        )
    
    if result:
        console.print(Panel(
            f"[bold green]✅ Success![/bold green]\n\n"
            f"Your video with image overlays is ready:\n[cyan]{result}[/cyan]",
            border_style="green"
        ))
    else:
        console.print("[red]❌ Video generation failed[/red]")


# ============================================================================
# PHASE 1: VIDEO SOURCE SELECTION
# ============================================================================

def video_source_phase():
    """Handle video source selection - download, local, or both"""
    
    console.print("\n[dim]Choose where your videos come from[/dim]")
    
    # Display source options
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Description")
    table.add_row("1", "Download from URLs (YouTube/Instagram/Pinterest)")
    table.add_row("2", "Use local videos from my device")
    table.add_row("3", "Both (download + local videos)")
    
    console.print(table)
    
    choice = Prompt.ask(
        "\n[cyan]Choose source[/cyan]",
        choices=["1", "2", "3"],
        default="1"
    )
    
    all_videos = []
    
    # Option 1: Download only
    if choice == "1":
        all_videos = download_videos_from_urls()
    
    # Option 2: Local only
    elif choice == "2":
        all_videos = select_local_videos()
    
    # Option 3: Both
    elif choice == "3":
        console.print("\n[yellow]First, let's download videos from URLs...[/yellow]")
        downloaded = download_videos_from_urls()
        
        console.print("\n[yellow]Now, let's add local videos...[/yellow]")
        local = select_local_videos()
        
        all_videos = downloaded + local
        
        if downloaded and local:
            console.print(f"\n[green]✓[/green] Total videos: {len(all_videos)} "
                        f"({len(downloaded)} downloaded + {len(local)} local)")
    
    return all_videos


# ============================================================================
# DOWNLOAD FROM URLS
# ============================================================================

def download_videos_from_urls():
    """Download videos from URLs"""
    
    console.print("\n[dim]You can download from YouTube, Instagram, or Pinterest[/dim]")
    
    # Get URLs from user
    urls = []
    while True:
        url = Prompt.ask(
            f"\n[cyan]Enter URL {len(urls) + 1}[/cyan] (or press Enter to finish)",
            default=""
        )
        
        if not url:
            break
        
        # Validate URL
        if not validators.is_valid_url(url):
            console.print("[red]Invalid URL. Please try again.[/red]")
            continue
        
        urls.append(url)
        console.print(f"[green]✓[/green] Added: {url}")
    
    if not urls:
        console.print("[yellow]No URLs provided.[/yellow]")
        return []
    
    # Ask about audio download
    download_audio = Confirm.ask(
        "\n[cyan]Download audio separately?[/cyan]",
        default=False
    )
    
    # Download videos
    downloaded_videos = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for i, url in enumerate(urls, 1):
            task = progress.add_task(
                f"Downloading {i}/{len(urls)}...",
                total=None
            )
            
            try:
                # Detect source and download
                source = validators.detect_source(url)
                
                if source == 'youtube':
                    result = youtube.download(url, download_audio=download_audio)
                elif source == 'instagram':
                    result = instagram.download(url)
                elif source == 'pinterest':
                    result = pinterest.download(url)
                else:
                    console.print(f"[red]Unsupported source: {url}[/red]")
                    continue
                
                if result and result.get('video_path'):
                    downloaded_videos.append(result['video_path'])
                    progress.update(task, completed=True)
                    console.print(f"[green]✓[/green] Downloaded: {Path(result['video_path']).name}")
                else:
                    console.print(f"[red]✗[/red] Failed: {url}")
            
            except Exception as e:
                console.print(f"[red]Error downloading {url}: {str(e)}[/red]")
    
    return downloaded_videos


# ============================================================================
# SELECT LOCAL VIDEOS
# ============================================================================

def select_local_videos():
    """Allow user to select local video files or folders"""
    
    console.print("\n[dim]You can provide video file paths or folder paths[/dim]")
    console.print("[dim]Tip: Use absolute paths or drag-and-drop files into terminal[/dim]")
    
    video_paths = []
    
    while True:
        # Show current count
        if video_paths:
            console.print(f"\n[green]Current selection: {len(video_paths)} video(s)[/green]")
        
        # Ask for input type
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Description")
        table.add_row("1", "Add a single video file")
        table.add_row("2", "Add all videos from a folder")
        table.add_row("3", "Done (continue with selected videos)")
        
        console.print(table)
        
        choice = Prompt.ask(
            f"\n[cyan]Choose option[/cyan]",
            choices=["1", "2", "3"],
            default="3" if video_paths else "1"
        )
        
        if choice == "3":
            break
        
        elif choice == "1":
            # Single file
            file_path = Prompt.ask("\n[cyan]Enter video file path[/cyan]")
            
            if not file_path:
                continue
            
            # Resolve path (handle ~, relative paths, etc.)
            resolved_path = file_manager.resolve_path(file_path)
            
            if not resolved_path:
                console.print("[red]File not found. Please check the path.[/red]")
                continue
            
            # Validate video file
            is_valid, message = validators.validate_local_video(resolved_path)
            
            if not is_valid:
                console.print(f"[red]Invalid video: {message}[/red]")
                
                # Ask if user wants to try anyway
                if Confirm.ask("[yellow]Try to use this file anyway?[/yellow]", default=False):
                    video_paths.append(resolved_path)
                    console.print(f"[yellow]⚠[/yellow] Added (not validated): {Path(resolved_path).name}")
                continue
            
            video_paths.append(resolved_path)
            
            # Show file info
            info = ffmpeg_helper.get_video_info(resolved_path)
            if info:
                console.print(
                    f"[green]✓[/green] Added: {Path(resolved_path).name} "
                    f"({info['width']}x{info['height']}, {info['duration']:.1f}s)"
                )
            else:
                console.print(f"[green]✓[/green] Added: {Path(resolved_path).name}")
        
        elif choice == "2":
            # Folder of videos
            folder_path = Prompt.ask("\n[cyan]Enter folder path[/cyan]")
            
            if not folder_path:
                continue
            
            # Resolve path
            resolved_path = file_manager.resolve_path(folder_path)
            
            if not resolved_path or not os.path.isdir(resolved_path):
                console.print("[red]Folder not found. Please check the path.[/red]")
                continue
            
            # Check if folder has videos
            has_videos, count = validators.is_video_folder(resolved_path)
            
            if not has_videos:
                console.print("[red]No video files found in this folder.[/red]")
                continue
            
            # Find all videos
            console.print(f"\n[yellow]Found {count} video(s) in folder[/yellow]")
            
            # Ask if recursive search
            recursive = Confirm.ask(
                "[cyan]Search in subfolders too?[/cyan]",
                default=False
            )
            
            found_videos = file_manager.find_videos_in_folder(resolved_path, recursive)
            
            if recursive and len(found_videos) > count:
                console.print(f"[yellow]Found {len(found_videos)} total videos (including subfolders)[/yellow]")
            
            # Ask to select all or individual
            if len(found_videos) <= 10:
                # Few videos - show list and ask individually
                console.print("\n[bold]Select videos to include:[/bold]")
                
                for video in found_videos:
                    # Get video info for display
                    info = ffmpeg_helper.get_video_info(video)
                    display_name = Path(video).name
                    
                    if info:
                        display_info = f"{display_name} ({info['width']}x{info['height']}, {info['duration']:.1f}s)"
                    else:
                        display_info = display_name
                    
                    if Confirm.ask(f"[cyan]Include {display_info}?[/cyan]", default=True):
                        video_paths.append(video)
                        console.print(f"[green]✓[/green] Added")
            else:
                # Many videos - ask to include all or filter
                console.print(f"\n[yellow]Found {len(found_videos)} videos[/yellow]")
                
                include_all = Confirm.ask(
                    "[cyan]Include all videos from this folder?[/cyan]",
                    default=True
                )
                
                if include_all:
                    video_paths.extend(found_videos)
                    console.print(f"[green]✓[/green] Added {len(found_videos)} videos")
                else:
                    # Filter by criteria
                    console.print("\n[yellow]Let's filter the videos...[/yellow]")
                    
                    # Ask for minimum duration
                    min_duration = Prompt.ask(
                        "[cyan]Minimum video duration (seconds)[/cyan]",
                        default="0"
                    )
                    
                    try:
                        min_duration = float(min_duration)
                    except ValueError:
                        min_duration = 0.0
                    
                    # Filter videos
                    filtered_count = 0
                    for video in found_videos:
                        info = ffmpeg_helper.get_video_info(video)
                        if info and info['duration'] >= min_duration:
                            video_paths.append(video)
                            filtered_count += 1
                    
                    console.print(f"[green]✓[/green] Added {filtered_count} videos (duration >= {min_duration}s)")
    
    # Summary
    if video_paths:
        console.print(f"\n[green]✓[/green] Selected {len(video_paths)} local video(s)")
    else:
        console.print("\n[yellow]No local videos selected[/yellow]")
    
    return video_paths


# ============================================================================
# PHASE 2: PROCESS VIDEOS
# ============================================================================

def process_videos_phase(video_paths):
    """Normalize and combine videos if multiple"""
    
    if not video_paths:
        return None
    
    # Single video - ask if processing needed
    if len(video_paths) == 1:
        console.print(f"\n[green]✓[/green] Single video: {Path(video_paths[0]).name}")
        
        needs_processing = Confirm.ask(
            "[cyan]Normalize this video? (crop to 9:16, fix fps, etc.)[/cyan]",
            default=True
        )
        
        if needs_processing:
            with console.status("[cyan]Normalizing video...[/cyan]"):
                normalized = normalizer.normalize_video(
                    video_paths[0],
                    target_resolution=config.RESOLUTIONS['reels']
                )
            
            if normalized:
                console.print(f"[green]✓[/green] Normalized: {Path(normalized).name}")
                return normalized
        
        return video_paths[0]
    
    # Multiple videos - normalize and combine
    console.print(f"\n[yellow]Found {len(video_paths)} videos[/yellow]")
    
    # Ask user preference
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Option", style="cyan")
    table.add_column("Description")
    table.add_row("1", "Process all videos (normalize + combine)")
    table.add_row("2", "Select specific videos to process")
    table.add_row("3", "Use first video only")
    
    console.print(table)
    
    choice = Prompt.ask(
        "\n[cyan]Choose an option[/cyan]",
        choices=["1", "2", "3"],
        default="1"
    )
    
    if choice == "3":
        return video_paths[0]
    
    if choice == "2":
        # Let user select videos
        selected = []
        console.print("\n[bold]Select videos to include:[/bold]")
        for i, path in enumerate(video_paths, 1):
            if Confirm.ask(f"[cyan]{i}. Include {Path(path).name}?[/cyan]", default=True):
                selected.append(path)
        video_paths = selected
    
    # Normalize all videos
    console.print("\n[cyan]Normalizing videos...[/cyan]")
    normalized_videos = []
    
    with Progress(console=console) as progress:
        task = progress.add_task(
            "[cyan]Normalizing...",
            total=len(video_paths)
        )
        
        for video in video_paths:
            try:
                normalized = normalizer.normalize_video(
                    video,
                    target_resolution=config.RESOLUTIONS['reels']
                )
                
                if normalized:
                    normalized_videos.append(normalized)
                    console.print(f"[green]✓[/green] {Path(video).name}")
                
                progress.update(task, advance=1)
            
            except Exception as e:
                console.print(f"[red]✗[/red] Failed {Path(video).name}: {str(e)}")
    
    if not normalized_videos:
        console.print("[red]No videos were normalized successfully.[/red]")
        return None
    
    # Combine videos
    console.print("\n[cyan]Combining videos...[/cyan]")
    
    with console.status("[cyan]Merging...[/cyan]"):
        combined = combiner.merge_videos(
            normalized_videos,
            output_path=config.OUTPUTS_DIR / "combined_video.mp4"
        )
    
    if combined:
        console.print(f"[green]✓[/green] Combined: {Path(combined).name}")
        return combined
    
    return None


# ============================================================================
# PHASE 3: AUDIO SELECTION
# ============================================================================

def audio_selection_phase():
    """Get audio file from user"""
    
    console.print("\n[dim]Provide the audio file to sync with video[/dim]")
    
    while True:
        audio_path = Prompt.ask(
            "\n[cyan]Enter audio file path[/cyan]"
        )
        
        # Resolve path
        resolved_path = file_manager.resolve_path(audio_path)
        
        if not resolved_path:
            console.print("[red]File not found. Please try again.[/red]")
            continue
        
        # Validate audio file
        if not validators.is_valid_audio(resolved_path):
            console.print("[red]Invalid audio file. Please provide MP3, WAV, M4A, etc.[/red]")
            continue
        
        # Get audio info
        info = ffmpeg_helper.get_audio_info(resolved_path)
        if info:
            console.print(
                f"[green]✓[/green] Audio: {Path(resolved_path).name} "
                f"({info['duration']:.1f}s, {info['codec']})"
            )
        else:
            console.print(f"[green]✓[/green] Audio: {Path(resolved_path).name}")
        
        return resolved_path


# ============================================================================
# PHASE 4: CUTTING CONFIGURATION
# ============================================================================

def cutting_configuration_phase(audio_path):
    """Configure how to cut the video"""
    
    config_dict = {}
    
    # Cut mode
    console.print("\n[bold]Cut Mode:[/bold]")
    table = Table(show_header=False)
    table.add_column("Option", style="cyan")
    table.add_column("Description")
    table.add_row("1", "Beat Detection (sync to music beats)")
    table.add_row("2", "Vocal Changes (sync to vocals)")
    
    console.print(table)
    
    cut_choice = Prompt.ask(
        "\n[cyan]Choose cut mode[/cyan]",
        choices=["1", "2"],
        default="1"
    )
    
    config_dict['cut_mode'] = 'beats' if cut_choice == "1" else 'vocals'
    
    # Interval
    console.print("\n[bold]Cut Interval:[/bold]")
    config_dict['interval'] = int(Prompt.ask(
        "[cyan]Cut every N points[/cyan] (1 = every beat, 5 = every 5th beat)",
        default="5"
    ))
    
    # Order
    console.print("\n[bold]Segment Order:[/bold]")
    table = Table(show_header=False)
    table.add_column("Option", style="cyan")
    table.add_column("Description")
    table.add_row("1", "Sequential (keep in order)")
    table.add_row("2", "Random (shuffle segments)")
    
    console.print(table)
    
    order_choice = Prompt.ask(
        "\n[cyan]Choose order[/cyan]",
        choices=["1", "2"],
        default="1"
    )
    
    config_dict['order'] = 'sequential' if order_choice == "1" else 'random'
    
    # Audio duration
    console.print("\n[bold]Audio Duration:[/bold]")
    
    # Get audio duration
    audio_duration = ffmpeg_helper.get_audio_duration(audio_path)
    console.print(f"[dim]Total audio duration: {audio_duration:.2f} seconds[/dim]")
    
    use_full = Confirm.ask(
        "\n[cyan]Use full audio?[/cyan]",
        default=True
    )
    
    if use_full:
        config_dict['audio_start'] = 0
        config_dict['audio_end'] = audio_duration
    else:
        config_dict['audio_start'] = float(Prompt.ask(
            "[cyan]Start time (seconds)[/cyan]",
            default="0"
        ))
        
        config_dict['audio_end'] = float(Prompt.ask(
            "[cyan]End time (seconds)[/cyan]",
            default=str(audio_duration)
        ))
    
    return config_dict


# ============================================================================
# PHASE 5: GENERATE VIDEO
# ============================================================================

def generate_video_phase(video_path, audio_path, cut_config):
    """Generate the final video"""
    
    try:
        # Analyze audio
        console.print("\n[cyan]Analyzing audio...[/cyan]")
        
        with console.status("[cyan]Detecting beats/vocals...[/cyan]"):
            if cut_config['cut_mode'] == 'beats':
                cut_points = audio_analyzer.detect_beats(audio_path)
            else:
                cut_points = audio_analyzer.detect_vocal_changes(audio_path)
        
        console.print(f"[green]✓[/green] Found {len(cut_points)} cut points")
        
        # Filter by interval
        filtered_points = cut_points[::cut_config['interval']]
        console.print(f"[green]✓[/green] Using {len(filtered_points)} points (every {cut_config['interval']}th)")
        
        # Cut video
        console.print("\n[cyan]Cutting video segments...[/cyan]")
        
        with console.status("[cyan]Creating segments...[/cyan]"):
            segments = video_cutter.create_segments(
                video_path=video_path,
                cut_points=filtered_points,
                order=cut_config['order'],
                audio_duration=cut_config['audio_end'] - cut_config['audio_start']
            )
        
        console.print(f"[green]✓[/green] Created {len(segments)} segments")
        
        # Merge with audio
        console.print("\n[cyan]Generating final video...[/cyan]")
        
        output_path = config.OUTPUTS_DIR / f"final_reel_{Path(video_path).stem}.mp4"
        
        with console.status("[cyan]Merging segments with audio...[/cyan]"):
            final_video = video_cutter.merge_with_audio(
                segments=segments,
                audio_path=audio_path,
                audio_start=cut_config['audio_start'],
                audio_end=cut_config['audio_end'],
                output_path=str(output_path)
            )
        
        return final_video
    
    except Exception as e:
        console.print(f"[red]Error during generation: {str(e)}[/red]")
        if config.DEBUG:
            raise
        return None


# ============================================================================
# CLI SUBCOMMANDS (for flag-based usage)
# ============================================================================

@cli.command()
@click.option('--urls', help='Comma-separated URLs to download')
@click.option('--local-videos', help='Comma-separated local video paths')
@click.option('--local-folder', help='Folder containing local videos')
@click.option('--download-audio', is_flag=True, help='Download audio separately')
@click.option('--audio-path', required=True, help='Path to audio file')
@click.option('--cut-mode', type=click.Choice(['beats', 'vocals']), default='beats')
@click.option('--interval', type=int, default=5, help='Cut every N points')
@click.option('--order', type=click.Choice(['sequential', 'random']), default='sequential')
@click.option('--audio-start', type=float, default=0, help='Audio start time (seconds)')
@click.option('--audio-end', type=float, default=None, help='Audio end time (seconds)')
@click.option('--output', default='final_reel.mp4', help='Output filename')
def generate(urls, local_videos, local_folder, download_audio, audio_path, cut_mode, 
            interval, order, audio_start, audio_end, output):
    """Generate video using command-line flags (non-interactive)"""
    
    console.print(Panel.fit(
        "[bold cyan]Better Reel Generator[/bold cyan]\n[dim]Non-interactive mode[/dim]",
        border_style="cyan"
    ))
    
    try:
        all_videos = []
        
        # Download from URLs
        if urls:
            url_list = [u.strip() for u in urls.split(',')]
            console.print(f"\n[cyan]📥 Downloading {len(url_list)} video(s)...[/cyan]")
            
            for url in url_list:
                source = validators.detect_source(url)
                if source == 'youtube':
                    result = youtube.download(url, download_audio=download_audio)
                elif source == 'instagram':
                    result = instagram.download(url)
                elif source == 'pinterest':
                    result = pinterest.download(url)
                else:
                    continue
                
                if result and result.get('video_path'):
                    all_videos.append(result['video_path'])
        
        # Add local videos
        if local_videos:
            video_list = [v.strip() for v in local_videos.split(',')]
            for video in video_list:
                resolved = file_manager.resolve_path(video)
                if resolved and validators.is_valid_video(resolved):
                    all_videos.append(resolved)
        
        # Add videos from folder
        if local_folder:
            resolved_folder = file_manager.resolve_path(local_folder)
            if resolved_folder:
                folder_videos = file_manager.find_videos_in_folder(resolved_folder)
                all_videos.extend(folder_videos)
        
        if not all_videos:
            console.print("[red]No valid videos found.[/red]")
            sys.exit(1)
        
        console.print(f"[green]✓[/green] Found {len(all_videos)} video(s)")
        
        # Process videos - ALWAYS NORMALIZE TO REEL FORMAT
        console.print("\n[cyan]🔧 Processing videos...[/cyan]")
        console.print("[cyan]Normalizing to reel format (1080x1920)...[/cyan]")
        
        if len(all_videos) == 1:
            # Single video - normalize it
            with console.status("[cyan]Normalizing video...[/cyan]"):
                processed = normalizer.normalize_video(
                    all_videos[0],
                    target_resolution=config.RESOLUTIONS['reels'],
                    target_fps=config.TARGET_FPS,
                    crop_mode='center'
                )
            
            if not processed:
                console.print("[red]❌ Video normalization failed[/red]")
                sys.exit(1)
            
            console.print(f"[green]✓[/green] Normalized to 1080x1920")
        else:
            # Multiple videos - normalize all then merge
            normalized = normalizer.batch_normalize(
                all_videos,
                target_resolution=config.RESOLUTIONS['reels'],
                target_fps=config.TARGET_FPS
            )
            
            if not normalized:
                console.print("[red]❌ Video normalization failed[/red]")
                sys.exit(1)
            
            processed = combiner.merge_videos(normalized)
            
            if not processed:
                console.print("[red]❌ Video merging failed[/red]")
                sys.exit(1)
            
            console.print(f"[green]✓[/green] Normalized and combined {len(normalized)} videos")
        
        # Analyze audio
        console.print("\n[cyan]🎵 Analyzing audio...[/cyan]")
        if cut_mode == 'beats':
            cut_points = audio_analyzer.detect_beats(audio_path)
        else:
            cut_points = audio_analyzer.detect_vocal_changes(audio_path)
        
        console.print(f"[green]✓[/green] Found {len(cut_points)} cut points")
        
        filtered_points = cut_points[::interval]
        console.print(f"[green]✓[/green] Using {len(filtered_points)} points (every {interval})")
        
        # Generate video
        console.print("\n[cyan]🎬 Generating video...[/cyan]")
        
        audio_duration = audio_end if audio_end else ffmpeg_helper.get_audio_duration(audio_path)
        
        segments = video_cutter.create_segments(
            video_path=processed,
            cut_points=filtered_points,
            order=order,
            audio_duration=audio_duration - audio_start
        )
        
        console.print(f"[green]✓[/green] Created {len(segments)} segments")
        
        final = video_cutter.merge_with_audio(
            segments=segments,
            audio_path=audio_path,
            audio_start=audio_start,
            audio_end=audio_duration,
            output_path=str(config.OUTPUTS_DIR / output)
        )
        
        if final:
            console.print(f"\n[green]✅ Video saved: {final}[/green]")
        else:
            console.print("[red]❌ Generation failed[/red]")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        if config.DEBUG:
            raise
        sys.exit(1)


@cli.command()
@click.option('--video', required=True, help='Background video path')
@click.option('--images-folder', required=True, help='Folder containing images')
@click.option('--duration-per-image', type=float, help='Duration each image shows (auto if not set)')
@click.option('--delay', type=float, default=0.0, help='Delay between images in seconds')
@click.option('--animation', default='random', 
              type=click.Choice(['random', 'slide_bottom', 'slide_top', 'slide_left', 'slide_right', 'fade']),
              help='Animation style')
@click.option('--output', default='overlay_video.mp4', help='Output filename')
def overlay_images(video, images_folder, duration_per_image, delay, animation, output):
    """Overlay images from folder onto background video with animations"""
    
    console.print(Panel.fit(
        "[bold cyan]Image Overlay Mode[/bold cyan]\n[dim]Non-interactive mode[/dim]",
        border_style="cyan"
    ))
    
    try:
        # Validate inputs
        is_valid, message = image_overlay.validate_overlay_inputs(
            video_path=video,
            images_folder=images_folder,
            duration_per_image=duration_per_image
        )
        
        if not is_valid:
            console.print(f"[red]❌ Validation failed: {message}[/red]")
            sys.exit(1)
        
        console.print(f"[green]✓[/green] {message}")
        
        # Get images count
        images = image_overlay.get_images_from_folder(images_folder)
        console.print(f"[cyan]Found {len(images)} images[/cyan]")
        
        # Preview timing
        video_duration = ffmpeg_helper.get_video_duration(video)
        preview = image_overlay.preview_image_timing(
            num_images=len(images),
            video_duration=video_duration,
            duration_per_image=duration_per_image,
            delay_between_images=delay
        )
        
        if preview:
            console.print(f"[dim]Duration per image: {preview['duration_per_image']:.2f}s[/dim]")
            console.print(f"[dim]Total timeline: {preview['total_duration']:.2f}s[/dim]")
        
        # Generate output path
        output_path = str(config.OUTPUTS_DIR / output)
        output_path = file_manager.ensure_unique_path(output_path)
        
        console.print(f"\n[cyan]🎬 Generating video with image overlays...[/cyan]")
        console.print(f"[dim]This may take a few minutes...[/dim]\n")
        
        # Process
        with console.status("[cyan]Processing...[/cyan]"):
            result = image_overlay.overlay_images_on_video(
                video_path=video,
                images_folder=images_folder,
                output_path=output_path,
                duration_per_image=duration_per_image,
                delay_between_images=delay,
                animation_style=animation
            )
        
        if result:
            console.print(f"\n[green]✅ Video saved: {result}[/green]")
        else:
            console.print("[red]❌ Generation failed[/red]")
            sys.exit(1)
    
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        if config.DEBUG:
            raise
        sys.exit(1)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Check for FFmpeg
    if not ffmpeg_helper.check_ffmpeg():
        console.print("[red]❌ FFmpeg not found. Please install FFmpeg first.[/red]")
        console.print("[yellow]Install: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)[/yellow]")
        sys.exit(1)
    
    cli()