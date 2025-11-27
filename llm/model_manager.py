"""Model selection and management logic."""
from typing import Optional, List
from enum import Enum
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaskType(Enum):
    """Types of tasks for model selection."""
    TEXT_ANALYSIS = "text_analysis"
    VISION = "vision"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    WEB_SCRAPING = "web_scraping"
    VERIFICATION = "verification"


class ModelManager:
    """Manages model selection based on task type."""
    
    def __init__(self):
        self.primary_model = settings.primary_model
        self.verifier_model = settings.verifier_model
        self.fallback_models = settings.fallback_models
        
        # Task-specific model preferences
        self.task_models = {
            TaskType.VISION: [
                "openai/gpt-4o",
                "google/gemini-2.0-flash-exp",
                "anthropic/claude-3-5-sonnet"
            ],
            TaskType.CODE_GENERATION: [
                "openai/gpt-4o",
                "anthropic/claude-sonnet-4",
                "google/gemini-2.0-flash-exp"
            ],
            TaskType.DATA_ANALYSIS: [
                "openai/gpt-4o",
                "anthropic/claude-sonnet-4",
                "google/gemini-2.0-flash-exp"
            ],
            TaskType.AUDIO_TRANSCRIPTION: [
                "openai/gpt-4o",
                "google/gemini-2.0-flash-exp"
            ],
            TaskType.TEXT_ANALYSIS: [
                "openai/gpt-4o",
                "anthropic/claude-sonnet-4",
                "google/gemini-2.0-flash-exp"
            ],
            TaskType.WEB_SCRAPING: [
                "openai/gpt-4o",
                "anthropic/claude-sonnet-4"
            ],
            TaskType.VERIFICATION: [
                "anthropic/claude-sonnet-4",
                "openai/gpt-4o"
            ]
        }
    
    def get_model_for_task(
        self, 
        task_type: TaskType, 
        attempt: int = 0
    ) -> str:
        """
        Get the best model for a specific task type.
        
        Args:
            task_type: Type of task
            attempt: Attempt number (for fallback)
            
        Returns:
            Model identifier
        """
        preferred_models = self.task_models.get(task_type, [self.primary_model])
        
        # Try preferred models first
        if attempt < len(preferred_models):
            model = preferred_models[attempt]
            logger.info(f"Selected model for {task_type.value}: {model} (attempt {attempt})")
            return model
        
        # Fall back to general fallback models
        fallback_index = attempt - len(preferred_models)
        if fallback_index < len(self.fallback_models):
            model = self.fallback_models[fallback_index]
            logger.info(f"Using fallback model: {model} (attempt {attempt})")
            return model
        
        # Last resort: use primary model
        logger.warning(f"All models exhausted, using primary: {self.primary_model}")
        return self.primary_model
    
    def get_verifier_model(self) -> str:
        """Get the model for verification tasks."""
        return self.verifier_model
    
    def detect_task_type(
        self, 
        question: str, 
        files: dict
    ) -> TaskType:
        """
        Detect task type based on question and files.
        
        Args:
            question: Question text
            files: Dictionary of files
            
        Returns:
            Detected task type
        """
        question_lower = question.lower()
        
        # Check file types
        has_images = any(
            f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
            for f in files.keys()
        )
        has_audio = any(
            f.endswith(('.mp3', '.wav', '.ogg', '.m4a', '.flac'))
            for f in files.keys()
        )
        has_video = any(
            f.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))
            for f in files.keys()
        )
        has_data = any(
            f.endswith(('.csv', '.xlsx', '.xls', '.json'))
            for f in files.keys()
        )
        has_pdf = any(f.endswith('.pdf') for f in files.keys())
        
        # Detect based on content and files
        if has_images or 'image' in question_lower or 'picture' in question_lower:
            return TaskType.VISION
        
        if has_audio or 'audio' in question_lower or 'transcribe' in question_lower:
            return TaskType.AUDIO_TRANSCRIPTION
        
        if has_video or 'video' in question_lower:
            return TaskType.VISION  # Treat video as vision task
        
        if has_data or 'csv' in question_lower or 'dataframe' in question_lower:
            return TaskType.DATA_ANALYSIS
        
        if 'scrape' in question_lower or 'website' in question_lower or 'html' in question_lower:
            return TaskType.WEB_SCRAPING
        
        if 'code' in question_lower or 'function' in question_lower or 'script' in question_lower:
            return TaskType.CODE_GENERATION
        
        # Default to text analysis
        return TaskType.TEXT_ANALYSIS
    
    def get_model_list(self) -> List[str]:
        """Get list of all available models."""
        all_models = [self.primary_model, self.verifier_model] + self.fallback_models
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in all_models:
            if model not in seen:
                seen.add(model)
                unique_models.append(model)
        return unique_models