from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from code_migration.api.schemas import ErrorResponse, ErrorDetails
from code_migration.core.security.input_validator import SecurityError

class APIError(Exception):
    """Base API exception that maps to a structured JSON response."""
    def __init__(self, status_code: int, code: str, message: str, details: dict = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details

async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle explicit API errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetails(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump()
    )

async def security_error_handler(request: Request, exc: SecurityError) -> JSONResponse:
    """Map core SecurityErrors to 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=ErrorDetails(code="SECURITY_VIOLATION", message=str(exc))
        ).model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return framework HTTP errors in the same stable envelope."""
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetails(
                code="HTTP_ERROR",
                message=message,
            )
        ).model_dump(),
        headers=getattr(exc, "headers", None),
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for internal server errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetails(
                code="INTERNAL_SERVER_ERROR", 
                message="An unexpected error occurred processing the request."
            )
        ).model_dump()
    )
