"""Video processing utilities."""
import os
from typing import List, Optional, Dict, Any
from moviepy.editor import VideoFileClip
import cv2
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VideoProcessor:
    """Processes video files for analysis."""
    
    def __init__(self):
        self.temp_dir = "/tmp/video_processing"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get information about a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            clip = VideoFileClip(video_path)
            
            info = {
                "path": video_path,
                "filename": os.path.basename(video_path),
                "duration_seconds": clip.duration,
                "fps": clip.fps,
                "size": clip.size,
                "width": clip.w,
                "height": clip.h,
                "has_audio": clip.audio is not None,
                "file_size_bytes": os.path.getsize(video_path)
            }
            
            clip.close()
            
            logger.info(
                f"Video info: {info['filename']}, "
                f"Duration: {info['duration_seconds']:.2f}s, "
                f"Size: {info['width']}x{info['height']}"
            )
            return info
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
    
    def extract_frames(
        self, 
        video_path: str, 
        num_frames: int = 10,
        uniform: bool = True
    ) -> List[str]:
        """
        Extract frames from video.
        
        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            uniform: If True, extract uniformly spaced frames
            
        Returns:
            List of extracted frame image paths
        """
        try:
            clip = VideoFileClip(video_path)
            duration = clip.duration
            
            frame_paths = []
            
            if uniform:
                # Extract uniformly spaced frames
                times = [i * duration / (num_frames - 1) for i in range(num_frames)]
            else:
                # Extract first N frames
                times = [i / clip.fps for i in range(num_frames)]
            
            for i, t in enumerate(times):
                if t >= duration:
                    break
                    
                frame = clip.get_frame(t)
                
                frame_path = os.path.join(
                    self.temp_dir,
                    f"{os.path.splitext(os.path.basename(video_path))[0]}_frame_{i}.jpg"
                )
                
                # Convert RGB to BGR for cv2
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(frame_path, frame_bgr)
                
                frame_paths.append(frame_path)
            
            clip.close()
            
            logger.info(f"Extracted {len(frame_paths)} frames from video")
            return frame_paths
            
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            return []
    
    def extract_frame_at_time(self, video_path: str, time_seconds: float) -> Optional[str]:
        """
        Extract a single frame at specific timestamp.
        
        Args:
            video_path: Path to video file
            time_seconds: Time in seconds
            
        Returns:
            Path to extracted frame
        """
        try:
            clip = VideoFileClip(video_path)
            
            if time_seconds >= clip.duration:
                logger.warning(f"Time {time_seconds}s exceeds video duration")
                time_seconds = clip.duration - 0.1
            
            frame = clip.get_frame(time_seconds)
            
            frame_path = os.path.join(
                self.temp_dir,
                f"{os.path.splitext(os.path.basename(video_path))[0]}_at_{time_seconds:.2f}s.jpg"
            )
            
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(frame_path, frame_bgr)
            
            clip.close()
            
            logger.info(f"Extracted frame at {time_seconds}s: {frame_path}")
            return frame_path
            
        except Exception as e:
            logger.error(f"Error extracting frame at time: {e}")
            return None
    
    def create_thumbnail(self, video_path: str, time_seconds: float = 1.0) -> Optional[str]:
        """
        Create a thumbnail from video.
        
        Args:
            video_path: Path to video file
            time_seconds: Time for thumbnail (default: 1 second)
            
        Returns:
            Path to thumbnail image
        """
        return self.extract_frame_at_time(video_path, time_seconds)
    
    def extract_audio(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file
        """
        try:
            clip = VideoFileClip(video_path)
            
            if clip.audio is None:
                logger.warning("Video has no audio")
                clip.close()
                return None
            
            audio_path = os.path.join(
                self.temp_dir,
                f"{os.path.splitext(os.path.basename(video_path))[0]}_audio.wav"
            )
            
            clip.audio.write_audiofile(audio_path, logger=None)
            clip.close()
            
            logger.info(f"Extracted audio: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return None
    
    def get_frame_at_percentage(self, video_path: str, percentage: float) -> Optional[str]:
        """
        Extract frame at a percentage of video duration.
        
        Args:
            video_path: Path to video file
            percentage: Percentage (0-100) of video duration
            
        Returns:
            Path to extracted frame
        """
        try:
            clip = VideoFileClip(video_path)
            time_seconds = (percentage / 100.0) * clip.duration
            clip.close()
            
            return self.extract_frame_at_time(video_path, time_seconds)
            
        except Exception as e:
            logger.error(f"Error extracting frame at percentage: {e}")
            return None