"""Small, deterministic pagination API used by the Week 1 exercise."""

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Pagination API")


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
            }
        },
    )


class Product(BaseModel):
    product_id: int
    name: str


class ProductPage(BaseModel):
    items: list[Product]
    total: int
    limit: int
    offset: int


PRODUCTS = [
    Product(product_id=product_id, name=f"Product {product_id}")
    for product_id in range(1, 101)
]


@app.get("/products", response_model=ProductPage)
def list_products(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ProductPage:
    """Return a page of the synthetic products in ascending ID order."""
    return ProductPage(
        items=PRODUCTS[offset : offset + limit],
        total=len(PRODUCTS),
        limit=limit,
        offset=offset,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
