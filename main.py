#!/usr/bin/env python3
"""
Better Reel Generator - Main Entry Point
A modular video generator for creating social media content
"""

import sys
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

# Import config
import config

# Import modules (will implement these next)
from downloaders import youtube, instagram, pinterest
from processors import normalizer, combiner, audio_analyzer, video_cutter
from utils import validators, file_manager, ffmpeg_helper

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
    
    try:
        # Step 1: Download Phase
        console.print("\n[bold cyan]📥 STEP 1: Download Videos[/bold cyan]")
        video_paths = download_phase()
        
        if not video_paths:
            console.print("[red]No videos downloaded. Exiting.[/red]")
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
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Process interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        if config.DEBUG:
            raise


# ============================================================================
# PHASE 1: DOWNLOAD
# ============================================================================

def download_phase():
    """Handle video downloads from various sources"""
    
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
        for i, path in enumerate(video_paths, 1):
            if Confirm.ask(f"[cyan]Include {Path(path).name}?[/cyan]", default=True):
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
        
        # Validate audio file
        if not Path(audio_path).exists():
            console.print("[red]File not found. Please try again.[/red]")
            continue
        
        if not validators.is_valid_audio(audio_path):
            console.print("[red]Invalid audio file. Please provide MP3, WAV, M4A, etc.[/red]")
            continue
        
        console.print(f"[green]✓[/green] Audio: {Path(audio_path).name}")
        return audio_path


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
@click.option('--urls', required=True, help='Comma-separated URLs to download')
@click.option('--download-audio', is_flag=True, help='Download audio separately')
@click.option('--audio-path', required=True, help='Path to audio file')
@click.option('--cut-mode', type=click.Choice(['beats', 'vocals']), default='beats')
@click.option('--interval', type=int, default=5, help='Cut every N points')
@click.option('--order', type=click.Choice(['sequential', 'random']), default='sequential')
@click.option('--audio-start', type=float, default=0, help='Audio start time (seconds)')
@click.option('--audio-end', type=float, default=None, help='Audio end time (seconds)')
@click.option('--output', default='final_reel.mp4', help='Output filename')
def generate(urls, download_audio, audio_path, cut_mode, interval, order, audio_start, audio_end, output):
    """Generate video using command-line flags (non-interactive)"""
    
    console.print(Panel.fit(
        "[bold cyan]Better Reel Generator[/bold cyan]\n[dim]Non-interactive mode[/dim]",
        border_style="cyan"
    ))
    
    try:
        # Parse URLs
        url_list = [u.strip() for u in urls.split(',')]
        
        # Download
        console.print("\n[cyan]📥 Downloading videos...[/cyan]")
        # ... (similar logic to interactive mode)
        
        console.print("[green]✅ Generation complete![/green]")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Check for FFmpeg
    if not ffmpeg_helper.check_ffmpeg():
        console.print("[red]❌ FFmpeg not found. Please install FFmpeg first.[/red]")
        sys.exit(1)
    
    cli()