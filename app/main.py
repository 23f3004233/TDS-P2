"""Main FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models import QuizRequest, QuizResponse
from app.config import settings
from app.utils.auth import verify_secret, verify_email
from app.utils.logger import get_logger
from agents.orchestrator import OrchestratorAgent

logger = get_logger(__name__)


# Global orchestrator instance
orchestrator = OrchestratorAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    logger.info("=" * 60)
    logger.info("LLM Quiz Solver Starting")
    logger.info(f"Email: {settings.email}")
    logger.info(f"Primary Model: {settings.primary_model}")
    logger.info(f"Verification: {'Enabled' if settings.enable_verification else 'Disabled'}")
    logger.info("=" * 60)
    yield
    logger.info("LLM Quiz Solver Shutting Down")


app = FastAPI(
    title="LLM Quiz Solver",
    description="Automated quiz solver using multiple LLM agents",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "LLM Quiz Solver",
        "status": "running",
        "email": settings.email,
        "github": settings.github_repo
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/quiz", response_model=QuizResponse)
async def handle_quiz(
    request: QuizRequest,
    background_tasks: BackgroundTasks
):
    """
    Main quiz handling endpoint.
    
    Accepts POST requests with quiz URL and credentials.
    Processes quiz in background and returns immediately.
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Received quiz request from: {request.email}")
    logger.info(f"Quiz URL: {request.url}")
    logger.info(f"{'='*60}\n")
    
    try:
        # Verify email
        verify_email(request.email)
        
        # Verify secret
        verify_secret(request.secret, request.email)
        
        # Add quiz processing to background tasks
        background_tasks.add_task(orchestrator.process_quiz, request)
        
        logger.info("Quiz processing started in background")
        
        return QuizResponse(
            status="processing",
            message="Quiz processing started successfully"
        )
        
    except HTTPException as e:
        logger.error(f"Authentication error: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error handling quiz request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(400)
async def bad_request_handler(request, exc):
    """Handle 400 Bad Request errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid JSON payload"}
    )


@app.exception_handler(403)
async def forbidden_handler(request, exc):
    """Handle 403 Forbidden errors."""
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc.detail) if hasattr(exc, 'detail') else "Forbidden"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False
    )