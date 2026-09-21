from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.exception import ExceptionType, Severity, Status


class CreateExceptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    portfolio_id: str = Field(min_length=1, max_length=64)
    transaction_id: str = Field(min_length=1, max_length=64)
    type: ExceptionType
    severity: Severity
    description: str = Field(min_length=1, max_length=2000)

    @field_validator("portfolio_id", "transaction_id", "description", mode="before")
    @classmethod
    def trim_strings(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return value.strip()


class UpdateExceptionRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"minProperties": 1},
    )
    severity: Severity = None
    description: str = Field(default=None, min_length=1, max_length=2000)

    @field_validator("description", mode="before")
    @classmethod
    def trim_description(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if isinstance(value, str) else value

    def model_post_init(self, __context: object) -> None:
        if not self.model_fields_set:
            raise ValueError("At least one field must be supplied")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("PATCH fields cannot be null")


class AssignExceptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assignee: str = Field(min_length=1, max_length=100)

    @field_validator("assignee", mode="before")
    @classmethod
    def trim_assignee(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class ResolveExceptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resolution_code: str = Field(min_length=1, max_length=100)
    resolution_notes: str = Field(min_length=1, max_length=2000)

    @field_validator("resolution_code", "resolution_notes", mode="before")
    @classmethod
    def trim_resolution(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class ExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    exception_id: str
    portfolio_id: str
    transaction_id: str
    type: ExceptionType
    severity: Severity
    status: Status
    description: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolution_code: Optional[str]
    resolution_notes: Optional[str]


class ExceptionListResponse(BaseModel):
    items: list[ExceptionResponse]
    total: int
    limit: int
    offset: int


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[list[ErrorDetail]] = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
