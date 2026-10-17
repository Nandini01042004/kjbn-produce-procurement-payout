"""
Main Application Entry Point for KJBN Produce Procurement & Payout
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.middleware import LoggingAndClockMiddleware, register_exception_handlers
from app.api.routes import (
    health,
    farmers,
    crops,
    price_lists,
    deliveries,
    advances,
    payouts,
)

# Auto-create tables if running directly without seed
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KJBN Produce Procurement & Payout API",
    description=(
        "Audit-grade rules engine for farm produce buying centres (Problem 4). "
        "Enforces effective-dated pricing, moisture deductions, frozen delivery breakdowns, "
        "weekly Monday-Sunday payouts, and capped advance recovery."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware for Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID logging and reviewer clock override middleware
app.add_middleware(LoggingAndClockMiddleware)

# Unified exception handlers
register_exception_handlers(app)

# Register API routes under /api
app.include_router(health.router, prefix="/api")
app.include_router(farmers.router, prefix="/api")
app.include_router(crops.router, prefix="/api")
app.include_router(price_lists.router, prefix="/api")
app.include_router(deliveries.router, prefix="/api")
app.include_router(advances.router, prefix="/api")
app.include_router(payouts.router, prefix="/api")


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "KJBN Produce Procurement & Payout Engine",
        "docs": "/docs",
        "health": "/api/health",
    }
