"""FastAPI Application Main Entry Point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import db_manager
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context managing database connection startup and shutdown."""
    setup_logging()
    await db_manager.connect_to_database()
    yield
    await db_manager.close_database_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-Ready Personal AI Coding Agent Backend API",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Register Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Custom Exception Handlers
register_exception_handlers(app)

# Mount API v1 Router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """Root endpoint returning basic agent API metadata."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
    }
