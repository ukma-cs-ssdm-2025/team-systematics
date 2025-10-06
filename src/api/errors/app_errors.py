from enum import Enum
from typing import Optional, Any, Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    FORBIDDEN = "FORBIDDEN"
    UNAUTHORIZED = "UNAUTHORIZED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class ErrorBody(JSONResponse):
    pass

class AppError(Exception):
    status_code: int = 400
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    message: str = "Application error"
    details: Optional[Dict[str, Any]] = None

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content={
            "error": {"code": self.code, "message": self.message, "details": self.details}
        })

class NotFoundError(AppError):
    status_code = 404
    code = ErrorCode.NOT_FOUND
    message = "Resource not found"

class ConflictError(AppError):
    status_code = 409
    code = ErrorCode.CONFLICT
    message = "State conflict"

class ForbiddenError(AppError):
    status_code = 403
    code = ErrorCode.FORBIDDEN
    message = "Forbidden"

class UnauthorizedError(AppError):
    status_code = 401
    code = ErrorCode.UNAUTHORIZED
    message = "Unauthorized"

def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return exc.to_response()

    @app.exception_handler(StarletteHTTPException)
    async def starlette_exc_handler(_: Request, exc: StarletteHTTPException):
        # Map to our envelope but keep original status
        code = ErrorCode.INTERNAL_ERROR
        if exc.status_code == 404:
            code = ErrorCode.NOT_FOUND
        elif exc.status_code == 403:
            code = ErrorCode.FORBIDDEN
        elif exc.status_code == 401:
            code = ErrorCode.UNAUTHORIZED
        return JSONResponse(status_code=exc.status_code, content={
            "error": {"code": code, "message": str(exc.detail), "details": None}
        })

    @app.exception_handler(RequestValidationError)
    async def validation_exc_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=400, content={
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Input validation failed",
                "details": {"errors": exc.errors()},
            }
        })