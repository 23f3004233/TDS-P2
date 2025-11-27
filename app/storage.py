"""In-memory storage for quiz results."""
from typing import Dict, Optional
from datetime import datetime
from app.models import SessionResult, QuizAttempt

class ResultStorage:
    """Simple in-memory storage for quiz results."""
    
    def __init__(self):
        self._sessions: Dict[str, SessionResult] = {}
    
    def create_session(self, session_id: str, email: str) -> SessionResult:
        """Create a new session."""
        session = SessionResult(
            session_id=session_id,
            email=email,
            status="processing",
            start_time=datetime.now()
        )
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionResult]:
        """Get session by ID."""
        return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs):
        """Update session fields."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
    
    def add_attempt(self, session_id: str, attempt: QuizAttempt):
        """Add a quiz attempt to session."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.attempts.append(attempt)
            session.total_quizzes = len(session.attempts)
            session.correct_answers = sum(1 for a in session.attempts if a.correct)
    
    def complete_session(self, session_id: str, error: Optional[str] = None):
        """Mark session as complete."""
        if session_id in self._sessions:
            self.update_session(
                session_id,
                status="failed" if error else "completed",
                end_time=datetime.now(),
                error=error
            )
    
    def list_sessions(self, email: Optional[str] = None) -> list:
        """List all sessions, optionally filtered by email."""
        sessions = list(self._sessions.values())
        if email:
            sessions = [s for s in sessions if s.email == email]
        return sorted(sessions, key=lambda s: s.start_time, reverse=True)


# Global storage instance
storage = ResultStorage()