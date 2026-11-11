from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from portfolio_app.models.portfolio import PortfolioStatus


def _trim(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


class CreatePortfolioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    portfolio_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    owner: str = Field(min_length=1, max_length=100)

    _trim_strings = field_validator("portfolio_id", "name", "owner", mode="before")(_trim)


class UpdatePortfolioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"minProperties": 1})
    name: str = Field(default=None, min_length=1, max_length=200)  # type: ignore[assignment]
    owner: str = Field(default=None, min_length=1, max_length=100)  # type: ignore[assignment]
    status: PortfolioStatus = None  # type: ignore[assignment]

    _trim_strings = field_validator("name", "owner", mode="before")(_trim)

    def model_post_init(self, __context: object) -> None:
        if not self.model_fields_set:
            raise ValueError("At least one field must be supplied")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("PATCH fields cannot be null")


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    portfolio_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    owner: str = Field(min_length=1, max_length=100)
    status: PortfolioStatus
    created_at: datetime
    updated_at: datetime


class PortfolioListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[PortfolioResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    message: str


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    details: Optional[list[ErrorDetail]] = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error: ErrorBody


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    service: str
    version: str
