"""
API Middleware & Exception Handling
- Request ID (Correlation ID) generation and tracking
- Reviewer clock override extraction (X-Test-Clock header or query param)
- Structured JSON logging with request context
- Centralized exception handlers ensuring uniform error envelope
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.clock import set_request_clock, parse_clock_string
from app.domain.errors import DomainError

logger = logging.getLogger("kjbn.api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [req:%(request_id)s] %(message)s",
)


class LoggingAndClockMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Correlation ID
        req_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id

        # 2. Reviewer Clock Override (X-Test-Clock header or query param)
        clock_header = request.headers.get("X-Test-Clock")
        if not clock_header and "test_clock" in request.query_params:
            clock_header = request.query_params.get("test_clock")

        if clock_header:
            try:
                override_dt = parse_clock_string(clock_header)
                set_request_clock(override_dt)
            except Exception as e:
                logger.warning(
                    f"Failed to parse X-Test-Clock value '{clock_header}': {e}",
                    extra={"request_id": req_id},
                )
                set_request_clock(None)
        else:
            set_request_clock(None)

        # 3. Time execution and log
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = req_id
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
                extra={"request_id": req_id},
            )
            return response
        finally:
            set_request_clock(None)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        req_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            f"Business rule violation [{exc.code}]: {exc.message} on {request.method} {request.url.path}",
            extra={"request_id": req_id},
        )
        return JSONResponse(
            status_code=exc.status_code,
            headers={"X-Request-ID": req_id},
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": req_id,
                    "details": None,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            f"Validation error on {request.method} {request.url.path}: {exc.errors()}",
            extra={"request_id": req_id},
        )
        # Simplify error details for actionable UI feedback
        details = []
        for err in exc.errors():
            loc = " -> ".join([str(x) for x in err.get("loc", []) if x != "body"])
            msg = err.get("msg", "Invalid field")
            details.append({"field": loc, "issue": msg})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers={"X-Request-ID": req_id},
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed. Please review the highlighted fields.",
                    "request_id": req_id,
                    "details": details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            exc_info=True,
            extra={"request_id": req_id},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers={"X-Request-ID": req_id},
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please contact support with the request ID.",
                    "request_id": req_id,
                    "details": None,
                }
            },
        )
