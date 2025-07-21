"""
Custom exception classes and handlers for the NERV Geometry Engine API.

Provides structured error handling with proper HTTP status codes
and detailed error messages for debugging.
"""

from typing import Any, Dict

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = structlog.get_logger()


class NERVException(Exception):
    """Base exception class for NERV-specific errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class GeometryEngineError(NERVException):
    """Errors related to the Rust geometry engine."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=f"Geometry engine error: {message}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ConstructionValidationError(NERVException):
    """Errors related to geometric construction validation."""
    
    def __init__(self, message: str, construction_data: Dict[str, Any] = None):
        super().__init__(
            message=f"Construction validation failed: {message}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"construction_data": construction_data}
        )


class CollectionError(NERVException):
    """Errors related to element collection operations."""
    
    def __init__(self, message: str, element_id: str = None):
        super().__init__(
            message=f"Collection error: {message}",
            status_code=status.HTTP_409_CONFLICT,
            details={"element_id": element_id}
        )


class DatabaseError(NERVException):
    """Database-related errors."""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"operation": operation}
        )


class MAGIError(NERVException):
    """MAGI AI assistant related errors."""
    
    def __init__(self, message: str, assistant: str = None, model: str = None):
        super().__init__(
            message=f"MAGI system error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"assistant": assistant, "model": model}
        )


class AuthenticationError(NERVException):
    """Authentication and authorization errors."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ProofVerificationError(NERVException):
    """Proof verification specific errors."""
    
    def __init__(self, message: str, proof_step: int = None, theorem: str = None):
        super().__init__(
            message=f"Proof verification failed: {message}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"proof_step": proof_step, "theorem": theorem}
        )


async def nerv_exception_handler(request: Request, exc: NERVException) -> JSONResponse:
    """Handle custom NERV exceptions."""
    
    logger.error(
        "NERV exception occurred",
        exception=exc.__class__.__name__,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
                "status_code": exc.status_code
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    
    logger.warning(
        "Validation error occurred",
        errors=exc.errors(),
        body=exc.body,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": exc.errors(),
                    "invalid_body": exc.body
                },
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    
    logger.error(
        "Unexpected exception occurred",
        exception=exc.__class__.__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        }
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Set up all exception handlers for the FastAPI app."""
    
    # Custom NERV exceptions
    app.add_exception_handler(NERVException, nerv_exception_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, general_exception_handler)