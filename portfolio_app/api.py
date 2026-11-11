from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from portfolio_app.dependencies import get_portfolio_service
from portfolio_app.models.portfolio import PortfolioStatus
from portfolio_app.schemas import (
    CreatePortfolioRequest,
    ErrorResponse,
    PortfolioListResponse,
    PortfolioResponse,
    UpdatePortfolioRequest,
)
from portfolio_app.services.portfolio_service import (
    CreatePortfolio,
    PortfolioService,
    UpdatePortfolio,
)

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])
VALIDATION_RESPONSE = {"model": ErrorResponse, "description": "Request validation failed"}
NOT_FOUND_RESPONSE = {"model": ErrorResponse, "description": "Portfolio does not exist"}
CONFLICT_RESPONSE = {"model": ErrorResponse, "description": "Portfolio identifier already exists"}
INTERNAL_RESPONSE = {"model": ErrorResponse, "description": "Unexpected failure"}


@router.post(
    "",
    response_model=PortfolioResponse,
    status_code=201,
    operation_id="createPortfolio",
    summary="Create a portfolio",
    responses={409: CONFLICT_RESPONSE, 422: VALIDATION_RESPONSE, 500: INTERNAL_RESPONSE},
)
def create_portfolio(
    payload: CreatePortfolioRequest,
    service: PortfolioService = Depends(get_portfolio_service),
) -> JSONResponse:
    portfolio = service.create(CreatePortfolio(**payload.model_dump()))
    response = JSONResponse(
        status_code=201,
        content=PortfolioResponse.model_validate(portfolio).model_dump(mode="json"),
    )
    response.headers["Location"] = f"/api/v1/portfolios/{portfolio.portfolio_id}"
    return response


@router.get(
    "",
    response_model=PortfolioListResponse,
    operation_id="listPortfolios",
    summary="List, filter, and paginate portfolios",
    description=(
        "Results are ordered by created_at descending, then portfolio_id ascending. "
        "Total is calculated after filtering and before pagination."
    ),
    responses={422: VALIDATION_RESPONSE, 500: INTERNAL_RESPONSE},
)
def list_portfolios(
    request: Request,
    status: Optional[PortfolioStatus] = None,
    owner: Optional[str] = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioListResponse:
    unknown = set(request.query_params) - {"status", "owner", "limit", "offset"}
    if unknown:
        parameter = sorted(unknown)[0]
        raise HTTPException(
            status_code=422,
            detail={"field": f"query.{parameter}", "message": "Unsupported query parameter"},
        )
    normalized_owner = owner.strip() if owner is not None else None
    if owner is not None and not normalized_owner:
        raise HTTPException(
            status_code=422,
            detail={"field": "query.owner", "message": "String should have at least 1 character"},
        )
    items, total = service.list(
        status=status,
        owner=normalized_owner,
        limit=limit,
        offset=offset,
    )
    return PortfolioListResponse(
        items=[PortfolioResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    operation_id="getPortfolio",
    summary="Get a portfolio",
    responses={404: NOT_FOUND_RESPONSE, 422: VALIDATION_RESPONSE, 500: INTERNAL_RESPONSE},
)
def get_portfolio(
    portfolio_id: Annotated[str, Path(min_length=1, max_length=64)],
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioResponse:
    return PortfolioResponse.model_validate(service.get(portfolio_id))


@router.patch(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    operation_id="updatePortfolio",
    summary="Update portfolio metadata or status",
    responses={404: NOT_FOUND_RESPONSE, 422: VALIDATION_RESPONSE, 500: INTERNAL_RESPONSE},
)
def update_portfolio(
    portfolio_id: Annotated[str, Path(min_length=1, max_length=64)],
    payload: UpdatePortfolioRequest,
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioResponse:
    command = UpdatePortfolio(
        name=payload.name,
        owner=payload.owner,
        status=payload.status,
    )
    return PortfolioResponse.model_validate(service.update(portfolio_id, command))
