from typing import Optional, Dict, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class IncidentResponseException(Exception):
    """Base application exception."""
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class IncidentNotFoundException(IncidentResponseException):
    def __init__(self, incident_id: str):
        super().__init__(
            code="INCIDENT_NOT_FOUND",
            message=f"Incident with ID '{incident_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ServiceNotFoundException(IncidentResponseException):
    def __init__(self, service_id_or_name: str):
        super().__init__(
            code="SERVICE_NOT_FOUND",
            message=f"Service '{service_id_or_name}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ActionNotFoundException(IncidentResponseException):
    def __init__(self, action_id: str):
        super().__init__(
            code="ACTION_NOT_FOUND",
            message=f"Action with ID '{action_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ActionNotApprovedException(IncidentResponseException):
    def __init__(self, action_id: str, current_status: str, risk_level: str):
        super().__init__(
            code="ACTION_NOT_APPROVED",
            message=f"Action '{action_id}' cannot be executed. Current status: '{current_status}'. Risk level: '{risk_level}' requires human approval.",
            status_code=status.HTTP_403_FORBIDDEN
        )


class ActionNotAllowedException(IncidentResponseException):
    def __init__(self, action_name: str):
        super().__init__(
            code="ACTION_NOT_ALLOWED",
            message=f"Operation '{action_name}' is not in the security allowlist and cannot be executed.",
            status_code=status.HTTP_403_FORBIDDEN
        )


class RecoveryCriteriaNotMetException(IncidentResponseException):
    def __init__(self, reason: str):
        super().__init__(
            code="RECOVERY_CRITERIA_NOT_MET",
            message=f"Incident cannot be resolved: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class LLMIntegrationException(IncidentResponseException):
    def __init__(self, reason: str):
        super().__init__(
            code="LLM_INTEGRATION_ERROR",
            message=f"LLM execution failed: {reason}",
            status_code=status.HTTP_502_BAD_GATEWAY
        )


async def domain_exception_handler(request: Request, exc: IncidentResponseException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"Domain error {exc.code}: {exc.message}",
        extra={"extra_data": {"code": exc.code, "request_id": request_id, "details": exc.details}}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": request_id
            }
        }
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
        exc_info=exc,
        extra={"extra_data": {"request_id": request_id}}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "request_id": request_id
            }
        }
    )
