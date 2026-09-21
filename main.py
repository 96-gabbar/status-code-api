"""Day 1 status-code exercise.

Implement the eight endpoint contracts from day-1.md here.
Keep this learning application independent from the flagship service.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field


app = FastAPI(title="HTTP Status Code Exercise")


def reset_example_state() -> None:
    app.state.items = {1: {"item_id": 1, "name": "Example item"}}
    app.state.next_item_id = 2
    app.state.closed_item_status = "closed"


reset_example_state()


class CreateItemRequest(BaseModel):
    name: str


class CommandRequest(BaseModel):
    command: str


class UserRequest(BaseModel):
    age: int = Field(ge=18)


def error_body(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        error = detail["error"]
        code = str(error.get("code", "HTTP_ERROR"))
        message = str(error.get("message", "An error occurred"))
    elif isinstance(detail, str):
        code = "HTTP_ERROR"
        message = detail or "An error occurred"
    else:
        code = "HTTP_ERROR"
        message = "An error occurred"

    return JSONResponse(status_code=exc.status_code, content=error_body(code, message))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body("VALIDATION_ERROR", "Validation error"),
    )


@app.exception_handler(Exception)
async def internal_exception_handler(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "An unexpected error occurred"),
    )


@app.get("/examples/item")
def get_existing_item() -> dict[str, Any]:
    item = app.state.items.get(1)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail=error_body("ITEM_NOT_FOUND", "Item not found"),
        )
    return item


@app.get("/examples/items/{item_id:int}")
def get_item(item_id: int) -> dict[str, Any]:
    item = app.state.items.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail=error_body("ITEM_NOT_FOUND", "Item not found"),
        )
    return item


@app.post("/examples/items")
def create_item(payload: CreateItemRequest) -> JSONResponse:
    item_id = app.state.next_item_id
    item = {"item_id": item_id, "name": payload.name}
    app.state.items[item_id] = item
    app.state.next_item_id += 1

    response = JSONResponse(status_code=201, content=item)
    response.headers["Location"] = f"/examples/items/{item_id}"
    return response


@app.put("/examples/items/{item_id:int}")
def replace_item(item_id: int, payload: CreateItemRequest) -> dict[str, Any]:
    if item_id not in app.state.items:
        raise HTTPException(
            status_code=404,
            detail=error_body("ITEM_NOT_FOUND", "Item not found"),
        )

    item = {"item_id": item_id, "name": payload.name}
    app.state.items[item_id] = item
    return item


@app.delete("/examples/items/{item_id:int}")
def delete_item(item_id: int) -> Response:
    item = app.state.items.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail=error_body("ITEM_NOT_FOUND", "Item not found"),
        )
    app.state.items.pop(item_id, None)
    return Response(status_code=204)


@app.post("/examples/commands")
def unsupported_command(payload: CommandRequest) -> None:
    if payload.command != "SUPPORTED":
        raise HTTPException(
            status_code=400,
            detail=error_body("UNSUPPORTED_COMMAND", "Unsupported command"),
        )


@app.post("/examples/closed-item/resolve")
def resolve_closed_item() -> None:
    if app.state.closed_item_status == "closed":
        raise HTTPException(
            status_code=409,
            detail=error_body("INVALID_STATE_TRANSITION", "Item is already closed"),
        )


@app.post("/examples/users")
def create_user(payload: UserRequest) -> dict[str, int]:
    return {"age": payload.age}


@app.get("/examples/internal-error")
def unexpected_failure() -> None:
    raise RuntimeError("stack trace details should stay internal")
