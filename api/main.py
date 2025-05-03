"""
ProtoNomia API Main
This module defines the FastAPI application for ProtoNomia.
"""
import logging
from typing import Dict, List

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import simulation_router, agent_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ProtoNomia API",
    description="API for the ProtoNomia economic simulation",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(simulation_router, prefix="/simulation", tags=["simulation"])
app.include_router(agent_router, prefix="/agent", tags=["agent"])

# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint for health checks.
    """
    return {
        "app": "ProtoNomia API",
        "status": "online",
        "version": "1.0.0",
    } 