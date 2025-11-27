"""Authentication utilities for secret verification."""
from fastapi import HTTPException
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def verify_secret(provided_secret: str, provided_email: str) -> bool:
    """
    Verify that the provided secret matches the configured secret.
    
    Args:
        provided_secret: Secret from request
        provided_email: Email from request
        
    Returns:
        True if secret is valid
        
    Raises:
        HTTPException: If secret is invalid
    """
    if not provided_secret:
        logger.warning(f"Empty secret provided for email: {provided_email}")
        raise HTTPException(status_code=403, detail="Secret is required")
    
    if not settings.quiz_secret:
        logger.error("QUIZ_SECRET not configured in environment")
        raise HTTPException(
            status_code=500, 
            detail="Server configuration error: secret not set"
        )
    
    if provided_secret != settings.quiz_secret:
        logger.warning(
            f"Invalid secret attempt for email: {provided_email}. "
            f"Expected: {settings.quiz_secret[:4]}..., Got: {provided_secret[:4]}..."
        )
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    logger.info(f"Secret verified successfully for email: {provided_email}")
    return True


def verify_email(provided_email: str) -> bool:
    """
    Verify that the provided email matches the configured email.
    
    Args:
        provided_email: Email from request
        
    Returns:
        True if email matches
        
    Raises:
        HTTPException: If email doesn't match
    """
    if provided_email != settings.email:
        logger.warning(
            f"Email mismatch. Expected: {settings.email}, Got: {provided_email}"
        )
        raise HTTPException(
            status_code=403, 
            detail=f"Email mismatch. Expected: {settings.email}"
        )
    
    return True