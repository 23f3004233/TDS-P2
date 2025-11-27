"""Pydantic models for request/response validation."""
from typing import Optional, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class QuizRequest(BaseModel):
    """Incoming quiz request from evaluation system."""
    email: EmailStr
    secret: str
    url: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "secret": "my_secret_string",
                "url": "https://example.com/quiz-834"
            }
        }


class QuizResponse(BaseModel):
    """Response to quiz request."""
    status: str
    message: str
    session_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "processing",
                "message": "Quiz processing started",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class AnswerSubmission(BaseModel):
    """Answer submission to quiz system."""
    email: str
    secret: str
    url: str
    answer: Any  # Can be bool, int, float, str, dict, or base64 string
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "secret": "my_secret_string",
                "url": "https://example.com/quiz-834",
                "answer": 12345
            }
        }


class AnswerResponse(BaseModel):
    """Response from quiz system after answer submission."""
    correct: bool
    reason: Optional[str] = None
    url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "correct": True,
                "url": "https://example.com/quiz-942",
                "reason": None
            }
        }


class QuizTask(BaseModel):
    """Internal representation of a quiz task."""
    url: str
    question: str
    files: Dict[str, str] = Field(default_factory=dict)  # filename: filepath
    submit_url: Optional[str] = None
    raw_html: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/quiz-834",
                "question": "What is the sum of the 'value' column?",
                "files": {"data.csv": "/tmp/data.csv"},
                "submit_url": "https://example.com/submit"
            }
        }


class AnalysisResult(BaseModel):
    """Result from analyzer agent."""
    answer: Any
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    code_executed: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": 12345,
                "confidence": 0.95,
                "reasoning": "Extracted table from PDF page 2 and summed values",
                "code_executed": "import pandas as pd\n..."
            }
        }


class VerificationResult(BaseModel):
    """Result from verifier agent."""
    approved: bool
    feedback: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "feedback": None,
                "confidence": 0.98
            }
        }


# NEW MODELS FOR RESULT TRACKING

class QuizAttempt(BaseModel):
    """Single quiz attempt result."""
    quiz_number: int
    url: str
    question: str
    answer: Any
    correct: bool
    reason: Optional[str] = None
    confidence: float
    timestamp: datetime
    next_url: Optional[str] = None


class SessionResult(BaseModel):
    """Complete session result."""
    session_id: str
    email: str
    status: str  # "processing", "completed", "failed"
    start_time: datetime
    end_time: Optional[datetime] = None
    total_quizzes: int = 0
    correct_answers: int = 0
    attempts: List[QuizAttempt] = Field(default_factory=list)
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "student@example.com",
                "status": "completed",
                "start_time": "2025-11-27T10:00:00",
                "end_time": "2025-11-27T10:02:30",
                "total_quizzes": 3,
                "correct_answers": 2,
                "attempts": []
            }
        }