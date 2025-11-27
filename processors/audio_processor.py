"""Audio processing and transcription utilities."""
import os
from typing import Optional, Dict, Any
from pydub import AudioSegment
import speech_recognition as sr
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AudioProcessor:
    """Processes audio files for transcription and analysis."""
    
    def __init__(self):
        self.temp_dir = "/tmp/audio_processing"
        os.makedirs(self.temp_dir, exist_ok=True)
        self.recognizer = sr.Recognizer()
    
    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Get information about an audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            info = {
                "path": audio_path,
                "filename": os.path.basename(audio_path),
                "duration_seconds": len(audio) / 1000.0,
                "channels": audio.channels,
                "sample_width": audio.sample_width,
                "frame_rate": audio.frame_rate,
                "file_size_bytes": os.path.getsize(audio_path)
            }
            
            logger.info(f"Audio info: {info['filename']}, Duration: {info['duration_seconds']:.2f}s")
            return info
            
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return {}
    
    def convert_to_wav(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert audio to WAV format for processing.
        
        Args:
            audio_path: Path to input audio file
            output_path: Path for output WAV (or auto-generate)
            
        Returns:
            Path to WAV file
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            if output_path is None:
                name = os.path.splitext(os.path.basename(audio_path))[0]
                output_path = os.path.join(self.temp_dir, f"{name}.wav")
            
            # Export as WAV with standard parameters
            audio.export(
                output_path,
                format="wav",
                parameters=["-ar", "16000", "-ac", "1"]  # 16kHz mono
            )
            
            logger.info(f"Converted to WAV: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting to WAV: {e}")
            return audio_path
    
    def transcribe_speech_recognition(self, audio_path: str) -> str:
        """
        Transcribe audio using Google Speech Recognition.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            # Convert to WAV if needed
            if not audio_path.endswith('.wav'):
                audio_path = self.convert_to_wav(audio_path)
            
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
                
            # Try Google Speech Recognition
            try:
                text = self.recognizer.recognize_google(audio_data)
                logger.info(f"Transcribed {len(text)} characters")
                return text
            except sr.UnknownValueError:
                logger.warning("Speech recognition could not understand audio")
                return ""
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")
                return ""
                
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    def split_audio_chunks(
        self, 
        audio_path: str, 
        chunk_duration_ms: int = 30000
    ) -> list:
        """
        Split audio into chunks for processing.
        
        Args:
            audio_path: Path to audio file
            chunk_duration_ms: Duration of each chunk in milliseconds
            
        Returns:
            List of chunk file paths
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            chunks = []
            
            for i, chunk_start in enumerate(range(0, len(audio), chunk_duration_ms)):
                chunk = audio[chunk_start:chunk_start + chunk_duration_ms]
                
                chunk_path = os.path.join(
                    self.temp_dir,
                    f"{os.path.splitext(os.path.basename(audio_path))[0]}_chunk_{i}.wav"
                )
                
                chunk.export(chunk_path, format="wav")
                chunks.append(chunk_path)
            
            logger.info(f"Split audio into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting audio: {e}")
            return [audio_path]
    
    def extract_audio_from_video(self, video_path: str) -> Optional[str]:
        """
        Extract audio track from video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file
        """
        try:
            from moviepy.editor import VideoFileClip
            
            video = VideoFileClip(video_path)
            
            if video.audio is None:
                logger.warning("Video has no audio track")
                return None
            
            audio_path = os.path.join(
                self.temp_dir,
                f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.wav"
            )
            
            video.audio.write_audiofile(audio_path, logger=None)
            video.close()
            
            logger.info(f"Extracted audio from video: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio from video: {e}")
            return None
    
    def normalize_audio(self, audio_path: str, target_dBFS: float = -20.0) -> str:
        """
        Normalize audio volume.
        
        Args:
            audio_path: Path to input audio
            target_dBFS: Target volume level in dBFS
            
        Returns:
            Path to normalized audio
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # Calculate change needed
            change_in_dBFS = target_dBFS - audio.dBFS
            
            # Apply normalization
            normalized = audio.apply_gain(change_in_dBFS)
            
            output_path = os.path.join(
                self.temp_dir,
                f"{os.path.splitext(os.path.basename(audio_path))[0]}_normalized.wav"
            )
            
            normalized.export(output_path, format="wav")
            logger.info(f"Normalized audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            return audio_path