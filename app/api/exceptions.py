from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from app.models.exception import ExceptionType, Severity, Status
from app.schemas.exception import (
    AssignExceptionRequest,
    CreateExceptionRequest,
    ErrorResponse,
    ExceptionListResponse,
    ExceptionResponse,
    ResolveExceptionRequest,
    UpdateExceptionRequest,
)
from app.services.exception_service import ExceptionService

router = APIRouter(prefix="/api/v1/exceptions", tags=["exceptions"])
VALIDATION_RESPONSE = {"model": ErrorResponse, "description": "Validation error"}
NOT_FOUND_RESPONSE = {"model": ErrorResponse, "description": "Exception not found"}
CONFLICT_RESPONSE = {"model": ErrorResponse, "description": "Invalid state transition"}
INTERNAL_RESPONSE = {"model": ErrorResponse, "description": "Unexpected server error"}


def get_service(request: Request) -> ExceptionService:
    return request.app.state.exception_service


@router.post(
    "",
    response_model=ExceptionResponse,
    status_code=201,
    responses={422: VALIDATION_RESPONSE, 500: INTERNAL_RESPONSE},
)
def create_exception(
    payload: CreateExceptionRequest, service: ExceptionService = Depends(get_service)
) -> JSONResponse:
    item = service.create(payload)
    response = JSONResponse(status_code=201, content=ExceptionResponse.model_validate(item).model_dump(mode="json"))
    response.headers["Location"] = f"/api/v1/exceptions/{item.exception_id}"
    return response


@router.get(
    "/{exception_id}",
    response_model=ExceptionResponse,
    responses={
        404: NOT_FOUND_RESPONSE,
        422: VALIDATION_RESPONSE,
        500: INTERNAL_RESPONSE,
    },
)
def get_exception(exception_id: str, service: ExceptionService = Depends(get_service)) -> ExceptionResponse:
    if not service.valid_id(exception_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail={"field": "path.exception_id", "message": "Invalid exception ID format"},
        )
    return ExceptionResponse.model_validate(service.get(exception_id))


@router.get(
    "",
    response_model=ExceptionListResponse,
    responses={422: VALIDATION_RESPONSE, 500: INTERNAL_RESPONSE},
)
def list_exceptions(
    request: Request,
    status: Optional[Status] = None,
    severity: Optional[Severity] = None,
    portfolio_id: Optional[str] = Query(default=None, min_length=1, max_length=64),
    type: Optional[ExceptionType] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ExceptionService = Depends(get_service),
) -> ExceptionListResponse:
    allowed = {"status", "severity", "portfolio_id", "type", "limit", "offset"}
    unknown = set(request.query_params) - allowed
    if unknown:
        from fastapi import HTTPException
        parameter = sorted(unknown)[0]
        raise HTTPException(
            status_code=422,
            detail={
                "field": f"query.{parameter}",
                "message": "Unsupported query parameter",
            },
        )
    items, total = service.list(
        status=status,
        severity=severity,
        portfolio_id=portfolio_id,
        exception_type=type.value if type else None,
        limit=limit,
        offset=offset,
    )
    return ExceptionListResponse(
        items=[ExceptionResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{exception_id}",
    response_model=ExceptionResponse,
    responses={
        404: NOT_FOUND_RESPONSE,
        422: VALIDATION_RESPONSE,
        500: INTERNAL_RESPONSE,
    },
)
def update_exception(
    exception_id: str,
    payload: UpdateExceptionRequest,
    service: ExceptionService = Depends(get_service),
) -> ExceptionResponse:
    if not service.valid_id(exception_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail={"field": "path.exception_id", "message": "Invalid exception ID format"},
        )
    return ExceptionResponse.model_validate(service.update(exception_id, payload))


@router.post(
    "/{exception_id}/assign",
    response_model=ExceptionResponse,
    responses={
        404: NOT_FOUND_RESPONSE,
        409: CONFLICT_RESPONSE,
        422: VALIDATION_RESPONSE,
        500: INTERNAL_RESPONSE,
    },
)
def assign_exception(
    exception_id: str,
    payload: AssignExceptionRequest,
    service: ExceptionService = Depends(get_service),
) -> ExceptionResponse:
    if not service.valid_id(exception_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail={"field": "path.exception_id", "message": "Invalid exception ID format"},
        )
    return ExceptionResponse.model_validate(service.assign(exception_id, payload))


@router.post(
    "/{exception_id}/resolve",
    response_model=ExceptionResponse,
    responses={
        404: NOT_FOUND_RESPONSE,
        409: CONFLICT_RESPONSE,
        422: VALIDATION_RESPONSE,
        500: INTERNAL_RESPONSE,
    },
)
def resolve_exception(
    exception_id: str,
    payload: ResolveExceptionRequest,
    service: ExceptionService = Depends(get_service),
) -> ExceptionResponse:
    if not service.valid_id(exception_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail={"field": "path.exception_id", "message": "Invalid exception ID format"},
        )
    return ExceptionResponse.model_validate(service.resolve(exception_id, payload))


@router.post(
    "/{exception_id}/close",
    response_model=ExceptionResponse,
    responses={
        404: NOT_FOUND_RESPONSE,
        409: CONFLICT_RESPONSE,
        422: VALIDATION_RESPONSE,
        500: INTERNAL_RESPONSE,
    },
)
def close_exception(
    exception_id: str, service: ExceptionService = Depends(get_service)
) -> ExceptionResponse:
    if not service.valid_id(exception_id):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail={"field": "path.exception_id", "message": "Invalid exception ID format"},
        )
    return ExceptionResponse.model_validate(service.close(exception_id))
