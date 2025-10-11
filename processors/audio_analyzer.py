"""
Audio Analyzer - Detect beats and vocal changes in audio
Uses librosa for audio analysis
"""

import os
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import librosa
from scipy.ndimage import gaussian_filter1d

import config


class AudioAnalyzer:
    """Handler for audio analysis using librosa"""
    
    def __init__(self):
        """Initialize audio analyzer"""
        self.cache_dir = config.TEMP_DIR / "audio_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_beats(
        self,
        audio_path: str,
        hop_length: int = None,
        start_bpm: float = None
    ) -> List[float]:
        """
        Detect beat timestamps in audio
        
        Args:
            audio_path: Path to audio file
            hop_length: Number of samples between frames
            start_bpm: Initial BPM estimate
            
        Returns:
            List of beat timestamps in seconds
        """
        try:
            if not os.path.exists(audio_path):
                if config.DEBUG:
                    print(f"Audio file not found: {audio_path}")
                return []
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Use config defaults if not provided
            if hop_length is None:
                hop_length = config.BEAT_HOP_LENGTH
            
            if start_bpm is None:
                start_bpm = config.BEAT_START_BPM
            
            # Detect beats
            tempo, beat_frames = librosa.beat.beat_track(
                y=y,
                sr=sr,
                hop_length=hop_length,
                start_bpm=start_bpm,
                units='frames'
            )
            
            # Convert frames to time
            beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
            
            # Convert to Python list
            beat_times_list = beat_times.tolist() if hasattr(beat_times, 'tolist') else list(beat_times)
            
            if config.VERBOSE:
                print(f"Detected {len(beat_times_list)} beats")
                print(f"Estimated tempo: {tempo:.2f} BPM")
            
            return beat_times_list
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error detecting beats: {str(e)}")
            return []
    
    def analyze_vocal_changes(
        self,
        audio_path: str,
        threshold: float = None
    ) -> List[float]:
        """
        Detect vocal change points in audio
        
        Args:
            audio_path: Path to audio file
            threshold: Sensitivity threshold (lower = more sensitive)
            
        Returns:
            List of vocal change timestamps in seconds
        """
        try:
            if not os.path.exists(audio_path):
                if config.DEBUG:
                    print(f"Audio file not found: {audio_path}")
                return []
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Use config default if not provided
            if threshold is None:
                threshold = config.VOCAL_THRESHOLD
            
            # Separate harmonic (vocal) and percussive components
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            # Compute mel spectrogram for harmonic part
            mel_spect = librosa.feature.melspectrogram(
                y=y_harmonic,
                sr=sr,
                n_mels=128,
                fmax=8000
            )
            
            # Convert to log scale
            mel_spect_db = librosa.power_to_db(mel_spect, ref=np.max)
            
            # Compute spectral contrast
            contrast = librosa.feature.spectral_contrast(
                S=np.abs(librosa.stft(y_harmonic)),
                sr=sr
            )
            
            # Combine features
            feature_sum = np.mean(contrast, axis=0) + np.mean(mel_spect_db, axis=0)
            
            # Normalize
            feature_sum = librosa.util.normalize(feature_sum)
            
            # Smooth the signal
            feature_smooth = gaussian_filter1d(feature_sum, sigma=3)
            
            # Find peaks (vocal changes)
            peaks = librosa.util.peak_pick(
                feature_smooth,
                pre_max=20,
                post_max=20,
                pre_avg=20,
                post_avg=20,
                delta=threshold,
                wait=1
            )
            
            # Convert frames to time
            vocal_times = librosa.frames_to_time(peaks, sr=sr)
            
            # Convert to Python list
            vocal_times_list = vocal_times.tolist() if hasattr(vocal_times, 'tolist') else list(vocal_times)
            
            # Ensure minimum number of changes
            if len(vocal_times_list) < config.VOCAL_MIN_CHANGES:
                # Fallback to onset detection with different parameters
                onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                peaks = librosa.util.peak_pick(
                    onset_env,
                    pre_max=20,
                    post_max=20,
                    pre_avg=20,
                    post_avg=20,
                    delta=threshold / 2,
                    wait=1
                )
                vocal_times = librosa.frames_to_time(peaks, sr=sr)
                vocal_times_list = vocal_times.tolist() if hasattr(vocal_times, 'tolist') else list(vocal_times)
            
            if config.VERBOSE:
                print(f"Detected {len(vocal_times_list)} vocal changes")
            
            return vocal_times_list
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error detecting vocal changes: {str(e)}")
            return []
    
    def analyze_hybrid(
        self,
        audio_path: str,
        beat_weight: float = 0.7,
        vocal_weight: float = 0.3
    ) -> List[float]:
        """
        Combine beat and vocal detection for hybrid analysis
        
        Args:
            audio_path: Path to audio file
            beat_weight: Weight for beat detection (0-1)
            vocal_weight: Weight for vocal detection (0-1)
            
        Returns:
            List of combined timestamps
        """
        try:
            # Get both beat and vocal times
            beat_times = self.analyze_beats(audio_path)
            vocal_times = self.analyze_vocal_changes(audio_path)
            
            # Combine and sort
            all_times = []
            
            # Add beats with weight
            for beat_time in beat_times:
                all_times.append((beat_time, beat_weight))
            
            # Add vocals with weight
            for vocal_time in vocal_times:
                all_times.append((vocal_time, vocal_weight))
            
            # Sort by time
            all_times.sort(key=lambda x: x[0])
            
            # Merge nearby points (within 0.1 seconds)
            merged_times = []
            last_time = -1.0
            
            for time, weight in all_times:
                if time - last_time > 0.1:
                    merged_times.append(time)
                    last_time = time
            
            return merged_times
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error in hybrid analysis: {str(e)}")
            return []
    
    def get_audio_info(self, audio_path: str) -> Optional[Dict]:
        """
        Get audio file information
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with audio info or None
        """
        try:
            if not os.path.exists(audio_path):
                return None
            
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Get duration
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Estimate tempo
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            
            # Get spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            
            return {
                'duration': duration,
                'sample_rate': sr,
                'tempo': float(tempo),
                'samples': len(y),
                'channels': 1,  # librosa loads as mono by default
                'spectral_centroid_mean': float(np.mean(spectral_centroids)),
                'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
            }
        
        except Exception as e:
            if config.DEBUG:
                print(f"Error getting audio info: {str(e)}")
            return None
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        Get audio duration in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, or 0.0 if error
        """
        try:
            info = self.get_audio_info(audio_path)
            return info['duration'] if info else 0.0
        except Exception:
            return 0.0
    
    def validate_audio(self, audio_path: str) -> bool:
        """
        Check if audio file is valid
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            info = self.get_audio_info(audio_path)
            return info is not None and info['duration'] > 0
        except Exception:
            return False


def detect_beats(audio_path: str, hop_length: int = None) -> List[float]:
    """
    Main function to detect beats in audio
    
    Args:
        audio_path: Path to audio file
        hop_length: Number of samples between frames
        
    Returns:
        List of beat timestamps in seconds
    """
    analyzer = AudioAnalyzer()
    return analyzer.analyze_beats(audio_path, hop_length=hop_length)


def detect_vocal_changes(audio_path: str, threshold: float = None) -> List[float]:
    """
    Main function to detect vocal changes in audio
    
    Args:
        audio_path: Path to audio file
        threshold: Sensitivity threshold
        
    Returns:
        List of vocal change timestamps in seconds
    """
    analyzer = AudioAnalyzer()
    return analyzer.analyze_vocal_changes(audio_path, threshold=threshold)


def analyze_audio(
    audio_path: str,
    mode: str = 'beats',
    **kwargs
) -> List[float]:
    """
    Analyze audio with specified mode
    
    Args:
        audio_path: Path to audio file
        mode: Analysis mode ('beats', 'vocals', 'hybrid')
        **kwargs: Additional arguments for specific analyzers
        
    Returns:
        List of timestamps in seconds
    """
    analyzer = AudioAnalyzer()
    
    if mode == 'beats':
        return analyzer.analyze_beats(audio_path, **kwargs)
    elif mode == 'vocals':
        return analyzer.analyze_vocal_changes(audio_path, **kwargs)
    elif mode == 'hybrid':
        return analyzer.analyze_hybrid(audio_path, **kwargs)
    else:
        if config.DEBUG:
            print(f"Unknown analysis mode: {mode}")
        return []


def get_audio_duration(audio_path: str) -> float:
    """
    Get audio file duration
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    analyzer = AudioAnalyzer()
    return analyzer.get_audio_duration(audio_path)


def get_audio_info(audio_path: str) -> Optional[Dict]:
    """
    Get detailed audio file information
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dict with audio info or None
    """
    analyzer = AudioAnalyzer()
    return analyzer.get_audio_info(audio_path)