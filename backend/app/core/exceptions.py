"""Secure global exception handling to prevent leaking stack traces or internal secrets."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger


class APIException(Exception):
    """Custom API base exception with HTTP status code and message."""

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return safe, sanitized JSON responses."""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)

    if settings.ENVIRONMENT == "development":
        error_detail = str(exc)
    else:
        error_detail = "An internal server error occurred. Please contact the administrator."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": error_detail,
            "path": str(request.url.path),
        },
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom APIException cleanly."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message,
            "path": str(request.url.path),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on FastAPI application instance."""
    app.add_exception_handler(APIException, api_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, global_exception_handler)
