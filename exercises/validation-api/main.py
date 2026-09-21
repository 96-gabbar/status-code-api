"""Week 1 validation API."""

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StrictInt, field_validator


class UserCreate(BaseModel):
    """Strict request contract for creating a user."""

    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    age: StrictInt = Field(ge=18)
    country: str = Field(min_length=2, max_length=2)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    age: int
    country: str


app = FastAPI(title="Validation API")


def validation_error_response(exc: RequestValidationError) -> JSONResponse:
    """Keep every request-validation failure in one stable envelope."""
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"] if part != "body"),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return validation_error_response(exc)


@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate) -> UserResponse:
    return UserResponse(
        id=f"USR-{uuid4().hex[:12].upper()}",
        name=user.name,
        email=user.email,
        age=user.age,
        country=user.country,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
