from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic_core import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import create_engine

import app.middlewares as middlewares
from app.api.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.models.user import User
from app.extypes import GumballException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database connection
    engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "detail": "Internal server error",
        "messages": ({"type": exc.__class__.__name__},)
    })

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={
        "detail": exc.detail
    })

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "detail": "Validation error",
        "messages": [
            {"msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
    })

@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request, exc: PydanticValidationError):
    return JSONResponse(status_code=422, content={
        "detail": "Validation error",
        "messages": [
            {"msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
    })

@app.exception_handler(GumballException)
async def pydantic_validation_exception_handler(request, exc: GumballException):
    return JSONResponse(status_code=422, content={
        "detail": "Gumball exception",
        "message": str(exc)
    })


middlewares.apply_middlewares(app)
# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI.
    """
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get("/api/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    """
    Returns the OpenAPI schema.
    """
    return get_openapi(
        title=f"{settings.PROJECT_NAME} API",
        version="1.0.0",
        description="API documentation",
        routes=app.routes,
    )


@app.get("/", include_in_schema=False)
def root():
    """
    Root endpoint.
    """
    return '"ok"'


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=8, reload=True)
