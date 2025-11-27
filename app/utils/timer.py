"""Timer management for 3-minute quiz constraint."""
import time
from typing import Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QuizTimer:
    """Manages timing for quiz solving with 3-minute hard limit."""
    
    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize timer.
        
        Args:
            timeout: Timeout in seconds (default: from config)
        """
        self.timeout = timeout or settings.quiz_timeout
        self.start_time = time.time()
        self.submission_buffer = 30  # Reserve 30s for submission
        
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def remaining(self) -> float:
        """Get remaining time in seconds."""
        return max(0, self.timeout - self.elapsed())
    
    def is_expired(self) -> bool:
        """Check if timer has expired."""
        return self.elapsed() >= self.timeout
    
    def has_buffer_time(self) -> bool:
        """Check if we still have buffer time for submission."""
        return self.remaining() > self.submission_buffer
    
    def should_continue(self) -> bool:
        """
        Check if we should continue processing.
        Returns False if we need to wrap up for submission.
        """
        remaining = self.remaining()
        
        if remaining <= 0:
            logger.warning("Timer expired! Must submit immediately.")
            return False
        
        if remaining <= self.submission_buffer:
            logger.warning(
                f"Only {remaining:.1f}s remaining. Entering submission phase."
            )
            return False
        
        return True
    
    def log_status(self, context: str = ""):
        """Log current timer status."""
        elapsed = self.elapsed()
        remaining = self.remaining()
        logger.info(
            f"[Timer] {context} - Elapsed: {elapsed:.1f}s, "
            f"Remaining: {remaining:.1f}s, "
            f"Can continue: {self.should_continue()}"
        )
    
    def get_timeout_for_operation(self, percentage: float = 0.3) -> float:
        """
        Get timeout for a specific operation based on remaining time.
        
        Args:
            percentage: Percentage of remaining time to allocate (0-1)
            
        Returns:
            Timeout in seconds for the operation
        """
        available = self.remaining() - self.submission_buffer
        allocated = max(5, available * percentage)  # Minimum 5 seconds
        return min(allocated, 60)  # Maximum 60 seconds per operation