# Better Reel Generator

**Version:** 1.0.0

An advanced, modular Python application for automatically generating beat-synced social media videos (reels, shorts, TikToks) from various sources. This tool downloads videos from YouTube, Instagram, or Pinterest, normalizes them to the perfect format, and creates engaging content synchronized to music beats or vocal changes.

---

## 🎯 What Does This Do?

The Better Reel Generator is an automated video production pipeline that:

1. **Downloads videos** from YouTube, Instagram, or Pinterest
2. **Normalizes videos** to social media formats (9:16 aspect ratio for reels/shorts)
3. **Analyzes audio** to detect beats or vocal changes
4. **Cuts video segments** at precise timestamps synchronized to music
5. **Combines segments** with audio overlay to create engaging, beat-synced content
6. **Overlays images** with animations on background videos
7. **Adds text/logo overlays** with customizable styling

---

## 📁 Project Structure

```
better-reel-gen/
├── main.py                          # Main entry point and CLI interface
├── config.py                        # Configuration constants and settings
├── requirements.txt                 # Python dependencies
│
├── downloaders/                     # Video download modules
│   ├── __init__.py
│   ├── youtube.py                   # YouTube downloader (yt-dlp)
│   ├── instagram.py                 # Instagram downloader (gallery-dl)
│   └── pinterest.py                 # Pinterest downloader (gallery-dl)
│
├── processors/                      # Video/audio processing modules
│   ├── __init__.py
│   ├── normalizer.py                # Video normalization (resolution, fps, codec)
│   ├── combiner.py                  # Video merging and concatenation
│   ├── audio_analyzer.py            # Beat and vocal detection (librosa)
│   ├── video_cutter.py              # Video segmentation and cutting
│   ├── image_overlay.py             # Image overlay with animations
│   └── text_overlay.py              # Text/logo overlay with styling
│
├── utils/                           # Utility modules
│   ├── __init__.py
│   ├── validators.py                # URL, file, and media validation
│   ├── file_manager.py              # File operations and path management
│   └── ffmpeg_helper.py             # FFmpeg wrapper functions
│
├── workflows/                       # Specialized workflow modules
│   ├── __init__.py
│   └── text_overlay_workflow.py     # Text overlay interactive workflow
│
├── downloads/                       # Downloaded videos storage
├── normalized/                      # Normalized videos storage
├── temp/                            # Temporary processing files
└── outputs/                         # Final generated videos
```

---

## 🔧 How It Works

### Architecture Overview

The application follows a **modular pipeline architecture** with five main phases:

```
┌─────────────────┐
│  1. Download    │  ← Download videos from URLs or use local files
└────────┬────────┘
         │
┌────────▼────────┐
│  2. Normalize   │  ← Convert to 9:16 format, fix fps/codec
└────────┬────────┘
         │
┌────────▼────────┐
│  3. Analyze     │  ← Detect beats/vocals in audio
└────────┬────────┘
         │
┌────────▼────────┐
│  4. Cut         │  ← Create video segments at timestamps
└────────┬────────┘
         │
┌────────▼────────┐
│  5. Generate    │  ← Merge segments with audio overlay
└─────────────────┘
```

### Processing Pipeline

1. **Video Source Selection** (`main.py` - Phase 1)
   - Download from YouTube/Instagram/Pinterest URLs
   - Use local video files
   - Combine both downloaded and local videos

2. **Video Processing** (`processors/normalizer.py`, `processors/combiner.py`)
   - Normalize videos to target resolution (1080x1920 for reels)
   - Standardize fps (30fps), codec (H.264), and bitrate
   - Crop/scale videos to fit aspect ratio
   - Merge multiple videos into one

3. **Audio Analysis** (`processors/audio_analyzer.py`)
   - Load audio using librosa
   - Detect beats using onset detection
   - Detect vocal changes using spectral analysis
   - Generate timestamps for cutting points

4. **Video Cutting** (`processors/video_cutter.py`)
   - Extract segments from video at timestamps
   - Support sequential or random ordering
   - Match total duration to audio length

5. **Final Generation** (`processors/video_cutter.py`)
   - Concatenate video segments
   - Overlay audio track
   - Export final video with proper encoding

---

## 📄 File-by-File Breakdown

### Core Files

#### `main.py` (1211 lines)
**Purpose:** Main entry point and interactive CLI interface

**Key Functions:**
- `cli()` - Click-based CLI group with subcommands
- `interactive_mode()` - Guided step-by-step workflow
- `standard_workflow()` - Beat-synced reel generation
- `image_overlay_workflow()` - Image overlay mode
- `video_source_phase()` - Handle video downloads/selection
- `process_videos_phase()` - Normalize and combine videos
- `audio_selection_phase()` - Get audio file from user
- `cutting_configuration_phase()` - Configure cut settings
- `generate_video_phase()` - Create final video

**Features:**
- Rich console UI with progress bars and tables
- Interactive prompts with validation
- Non-interactive mode via CLI flags
- Error handling with debug mode

#### `config.py` (265 lines)
**Purpose:** Centralized configuration and constants

**Key Settings:**
- **Paths:** `DOWNLOADS_DIR`, `NORMALIZED_DIR`, `TEMP_DIR`, `OUTPUTS_DIR`
- **Video Settings:** Target resolutions, codecs, fps, bitrate
- **Audio Settings:** Codec, bitrate, sample rate
- **Download Settings:** yt-dlp and gallery-dl configuration
- **Audio Analysis:** Beat detection parameters, vocal thresholds
- **Cutting Settings:** Min/max segment duration, ordering modes
- **Overlay Settings:** Animation types, timing, colors
- **File Extensions:** Supported video/audio/image formats
- **URL Patterns:** Regex patterns for platform detection

---

### Downloaders (`downloaders/`)

#### `youtube.py` (322 lines)
**Purpose:** Download videos from YouTube using yt-dlp

**Key Classes:**
- `YouTubeDownloader` - Handler for YouTube downloads

**Key Methods:**
- `download_video()` - Download video with best quality
- `download_audio()` - Download audio only
- `download_both()` - Download video and audio separately
- `get_video_info()` - Get metadata without downloading

**Features:**
- Supports YouTube videos, Shorts, and playlists
- Configurable quality and format selection
- Automatic file detection and validation
- Progress tracking and error handling

#### `instagram.py` (7748 bytes)
**Purpose:** Download videos from Instagram using gallery-dl

**Features:**
- Download Instagram Reels, posts, and IGTV
- Handle authentication if needed
- Extract video metadata

#### `pinterest.py` (8862 bytes)
**Purpose:** Download videos from Pinterest using gallery-dl

**Features:**
- Download Pinterest video pins
- Handle shortened pin.it URLs
- Extract video information

---

### Processors (`processors/`)

#### `normalizer.py` (444 lines)
**Purpose:** Normalize videos to consistent format

**Key Class:** `VideoNormalizer`

**Key Methods:**
- `normalize()` - Main normalization function
- `_build_filter_chain()` - Create FFmpeg filter string
- `_run_ffmpeg_normalize()` - Execute FFmpeg command
- `needs_normalization()` - Check if processing needed

**Features:**
- Convert to target resolution (e.g., 1080x1920)
- Standardize fps (default 30fps)
- Change codec (default H.264)
- Crop modes: center, top, bottom
- Scale and pad to fit aspect ratio
- Batch processing support

#### `combiner.py` (387 lines)
**Purpose:** Merge multiple videos into one

**Key Class:** `VideoCombiner`

**Key Methods:**
- `merge()` - Main merge function
- `_merge_simple_concat()` - Fast concat (same specs)
- `_merge_with_reencoding()` - Reliable merge (different specs)
- `_merge_with_transition()` - Merge with fade/dissolve

**Features:**
- Concatenate multiple videos
- Optional transitions (fade, dissolve)
- Audio synchronization
- Handle different video specifications

#### `audio_analyzer.py` (395 lines)
**Purpose:** Detect beats and vocal changes in audio

**Key Class:** `AudioAnalyzer`

**Key Methods:**
- `analyze_beats()` - Detect beat timestamps using librosa
- `analyze_vocal_changes()` - Detect vocal change points
- `analyze_hybrid()` - Combine beat and vocal detection
- `get_audio_info()` - Extract audio metadata

**Features:**
- Beat detection using onset strength
- Vocal detection using spectral analysis
- Configurable sensitivity and parameters
- BPM estimation
- Audio validation

**Algorithm:**
- Uses librosa's `beat.beat_track()` for beat detection
- Uses MFCC (Mel-frequency cepstral coefficients) for vocal analysis
- Applies Gaussian smoothing for noise reduction

#### `video_cutter.py` (373 lines)
**Purpose:** Extract segments and merge with audio

**Key Class:** `VideoCutter`

**Key Methods:**
- `extract_segment()` - Extract single segment from video
- `create_segments_from_timestamps()` - Create multiple segments
- `merge_segments_with_audio()` - Combine segments with audio
- `cleanup_segments()` - Remove temporary files

**Features:**
- Precise timestamp-based cutting
- Sequential or random segment ordering
- Audio overlay and synchronization
- Automatic duration matching
- Temporary file management

#### `image_overlay.py` (768 lines)
**Purpose:** Overlay images on video with animations

**Key Class:** `ImageOverlayProcessor`

**Key Methods:**
- `process()` - Main overlay function
- `_calculate_timing()` - Calculate image display timing
- `_calculate_image_dimensions()` - Resize images to fit
- `_build_filter_complex()` - Create FFmpeg filter
- `_build_animation_expressions()` - Generate animation math

**Features:**
- Multiple animation styles:
  - Slide from bottom/top/left/right
  - Fade in/out
  - Random (mix of all)
- Automatic image sizing (max 85% of frame)
- Configurable duration per image
- Delay between images
- Maintains aspect ratio

**Technical Details:**
- Uses FFmpeg overlay filter with position expressions
- Implements smooth animations using time-based math
- Handles enable/disable expressions for timing

#### `text_overlay.py` (17797 bytes)
**Purpose:** Add text/logo overlay with background box

**Features:**
- Text overlay with background box
- Configurable colors and opacity
- Font size and positioning
- Logo/watermark support
- Multiple text alignment options

---

### Utils (`utils/`)

#### `validators.py` (874 lines)
**Purpose:** Comprehensive validation for URLs, files, and media

**Key Class:** `Validator`

**Key Methods:**
- `is_valid_url()` - Validate URL format
- `detect_source()` - Identify platform (YouTube/Instagram/Pinterest)
- `is_youtube_url()`, `is_instagram_url()`, `is_pinterest_url()` - Platform checks
- `validate_local_video()` - Comprehensive video file validation
- `validate_local_audio()` - Audio file validation
- `validate_local_image()` - Image file validation
- `is_video_folder()`, `is_image_folder()` - Folder content checks
- `validate_file_size()` - Check file size limits
- `validate_video_duration()` - Check video length

**Features:**
- URL validation and parsing
- Platform detection using regex patterns
- File existence and accessibility checks
- Media format validation
- Duration and size constraints
- Batch validation support

#### `file_manager.py` (19352 bytes)
**Purpose:** File operations and path management

**Key Functions:**
- `resolve_path()` - Resolve relative paths, ~, symlinks
- `find_videos_in_folder()` - Recursively find video files
- `ensure_unique_path()` - Generate unique filenames
- `cleanup_old_files()` - Remove old temporary files
- `get_file_info()` - Get file metadata

**Features:**
- Path resolution and normalization
- Recursive file searching
- Duplicate filename handling
- Automatic cleanup
- Cross-platform compatibility

#### `ffmpeg_helper.py` (15626 bytes)
**Purpose:** FFmpeg wrapper functions

**Key Functions:**
- `check_ffmpeg()` - Verify FFmpeg installation
- `get_video_info()` - Extract video metadata using ffprobe
- `get_audio_info()` - Extract audio metadata
- `get_video_duration()` - Get video length
- `get_video_resolution()` - Get video dimensions
- `run_ffmpeg_command()` - Execute FFmpeg with error handling

**Features:**
- FFmpeg/ffprobe detection
- Metadata extraction via JSON
- Error handling and logging
- Progress tracking
- Command building utilities

---

### Workflows (`workflows/`)

#### `text_overlay_workflow.py` (13129 bytes)
**Purpose:** Interactive workflow for text/logo overlay

**Features:**
- Step-by-step prompts for text overlay
- Logo/watermark positioning
- Background box customization
- Color and opacity selection
- Preview and confirmation

---

## 🎬 Usage Examples

### Interactive Mode (Recommended)

```bash
# Run the application
python main.py

# Follow the interactive prompts:
# 1. Choose mode (beat-synced reel, image overlay, text overlay)
# 2. Select video source (download URLs or local files)
# 3. Configure processing options
# 4. Generate your video!
```

### Command-Line Mode

**Generate beat-synced reel:**
```bash
python main.py generate \
  --urls "https://youtube.com/watch?v=..." \
  --audio-path "audio.mp3" \
  --cut-mode beats \
  --interval 5 \
  --order random \
  --output "my_reel.mp4"
```

**Overlay images on video:**
```bash
python main.py overlay-images \
  --video "background.mp4" \
  --images-folder "images/" \
  --duration-per-image 2.0 \
  --delay 0.5 \
  --animation slide_bottom \
  --output "overlay_video.mp4"
```

---

## 🔄 Data Flow

### Standard Reel Generation Workflow

```
User Input (URLs/Files)
         │
         ▼
    Downloaders ──────────────┐
         │                    │
         ▼                    ▼
   Local Videos         Downloaded Videos
         │                    │
         └────────┬───────────┘
                  │
                  ▼
            Validators ────► Validation
                  │
                  ▼
             Normalizer ────► 1080x1920, 30fps, H.264
                  │
                  ▼
              Combiner ────► Single video (if multiple)
                  │
                  ▼
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
   Processed Video    Audio File
         │                 │
         │                 ▼
         │         Audio Analyzer ────► Beat/Vocal Timestamps
         │                 │
         └────────┬────────┘
                  │
                  ▼
           Video Cutter ────► Segments at timestamps
                  │
                  ▼
         Merge Segments + Audio
                  │
                  ▼
           Final Video Output
```

---

## 🛠️ Dependencies

### Core Dependencies
- **click** - CLI framework
- **rich** - Beautiful terminal UI
- **ffmpeg-python** - FFmpeg wrapper
- **yt-dlp** - YouTube downloader
- **gallery_dl** - Instagram/Pinterest downloader
- **librosa** - Audio analysis
- **numpy** - Numerical operations
- **scipy** - Scientific computing

### Full List
See `requirements.txt` for complete dependency list with versions.

---

## ⚙️ Configuration

All configuration is centralized in `config.py`:

### Video Settings
- **Target Resolution:** 1080x1920 (9:16 for reels)
- **FPS:** 30
- **Codec:** H.264 (libx264)
- **Bitrate:** 5M
- **CRF:** 23 (quality)

### Audio Settings
- **Codec:** AAC
- **Bitrate:** 192k
- **Sample Rate:** 48000 Hz

### Processing Settings
- **Min Segment Duration:** 0.3s
- **Max Segment Duration:** 5.0s
- **Beat Hop Length:** 512
- **Vocal Threshold:** 0.5

---

## 🎨 Features

### 1. Multi-Source Video Download
- YouTube (videos, Shorts, playlists)
- Instagram (Reels, posts, IGTV)
- Pinterest (video pins)

### 2. Video Normalization
- Convert any video to social media format
- Automatic cropping and scaling
- FPS and codec standardization

### 3. Beat-Synced Cutting
- Detect beats using librosa
- Detect vocal changes
- Hybrid mode (beats + vocals)
- Configurable interval (every Nth beat)

### 4. Flexible Ordering
- Sequential (maintain order)
- Random (shuffle segments)

### 5. Image Overlay
- Multiple animation styles
- Auto-sizing with padding
- Configurable timing

### 6. Text Overlay
- Custom text with background box
- Logo/watermark support
- Color and opacity control

---

## 🚀 Installation

```bash
# Clone the repository
git clone <repository-url>
cd better-reel-gen

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (required)
# macOS:
brew install ffmpeg

# Linux:
sudo apt install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
```

---

## 📊 Output

Generated videos are saved in the `outputs/` directory with the following characteristics:

- **Format:** MP4
- **Resolution:** 1080x1920 (9:16)
- **Video Codec:** H.264
- **Audio Codec:** AAC
- **FPS:** 30
- **Optimized for:** Instagram Reels, TikTok, YouTube Shorts

---

## 🐛 Debugging

Enable debug mode:
```bash
export DEBUG=true
python main.py
```

Enable verbose logging:
```bash
export VERBOSE=true
python main.py
```

---

## 📝 Notes

- **FFmpeg Required:** This application requires FFmpeg to be installed on your system
- **Storage:** Downloaded and processed videos can take significant disk space
- **Processing Time:** Video generation can take several minutes depending on video length and complexity
- **Auto Cleanup:** Temporary files are automatically cleaned up (configurable in `config.py`)

---

## 🎯 Use Cases

1. **Social Media Content Creation**
   - Create engaging reels synchronized to trending audio
   - Generate TikTok videos with beat-synced cuts
   - Produce YouTube Shorts from existing content

2. **Video Compilation**
   - Combine multiple video clips into one
   - Create montages with music overlay
   - Generate highlight reels

3. **Image Slideshows**
   - Create video slideshows with animations
   - Add product images to promotional videos
   - Generate photo montages with music

4. **Branding**
   - Add watermarks and logos to videos
   - Create branded content with text overlays
   - Generate consistent social media content

---

## 🏗️ Architecture Principles

1. **Modularity:** Each component (downloader, processor, utility) is independent
2. **Separation of Concerns:** Clear boundaries between downloading, processing, and generation
3. **Configuration-Driven:** All settings centralized in `config.py`
4. **Error Handling:** Comprehensive validation and error messages
5. **User Experience:** Rich CLI with progress bars and interactive prompts
6. **Flexibility:** Support for both interactive and non-interactive modes

---

## 📚 Technical Details

### Audio Analysis Algorithm
- Uses **librosa** for audio processing
- **Beat Detection:** Onset strength envelope analysis
- **Vocal Detection:** MFCC-based spectral analysis
- **Smoothing:** Gaussian filter for noise reduction

### Video Processing Pipeline
- **FFmpeg** for all video operations
- **Filter Complex:** Advanced FFmpeg filters for overlays
- **Concatenation:** Demuxer-based for speed, re-encoding for compatibility

### File Management
- **Automatic Cleanup:** Old files removed after 7 days
- **Unique Naming:** Prevents file overwrites
- **Path Resolution:** Handles relative paths, ~, symlinks

---

## 🎓 Learning Resources

To understand the codebase better:
1. Start with `main.py` to see the overall flow
2. Review `config.py` to understand settings
3. Explore individual processors to see how each step works
4. Check `utils/` for helper functions
5. Run in interactive mode to see the workflow in action

---

**Created by:** Better Reel Generator Team  
**License:** See LICENSE file  
**Version:** 1.0.0
