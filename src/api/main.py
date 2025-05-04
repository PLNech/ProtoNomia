"""
ProtoNomia API Main
This module defines the FastAPI application for ProtoNomia.
"""
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from src.api.routes import simulation_router, agent_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Create FastAPI app with detailed documentation
description = """
# ProtoNomia Mars Settlement API

ProtoNomia is an economic simulation of a Mars settlement in the year 2993.
This API allows you to create, manage, and monitor simulations with AI-driven agents.

## Features

* 🚀 **Simulation Management**: Create and run simulations with configurable parameters
* 👨‍🚀 **Agent Control**: Add, remove, and modify agents in the simulation 
* 📈 **Real-time Monitoring**: Track the state of the simulation as it progresses
* 🤖 **LLM Integration**: Agents powered by large language models for realistic behavior

## Usage

To get started:
1. Create a new simulation using the `/simulation/start` endpoint
2. Track the simulation state using the `/simulation/detail/{simulation_id}` endpoint
3. Run the simulation day by day with `/simulation/run/{simulation_id}`

For more detailed documentation, see [the full API documentation](https://github.com/yourusername/protonomia/docs/api.md).
"""

tags_metadata = [
    {
        "name": "simulation",
        "description": "Operations for managing simulations",
    },
    {
        "name": "agent",
        "description": "Operations for controlling agents within a simulation",
    },
]

app = FastAPI(
    title="ProtoNomia API",
    description=description,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url=None,  # Disable default docs to use custom UI
    redoc_url=None,  # Disable ReDoc
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


# Custom OpenAPI schema to add extensions
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="ProtoNomia API",
        version="1.0.0",
        description=description,
        routes=app.routes,
        tags=tags_metadata,
    )

    # Add custom extensions or metadata if needed
    openapi_schema["info"]["x-logo"] = {
        "url": "https://img.icons8.com/nolan/64/mars-planet.png"
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Custom Swagger UI with cyberpunk theme
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="ProtoNomia API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://img.icons8.com/nolan/64/mars-planet.png",
        swagger_ui_parameters={
            "syntaxHighlight.theme": "monokai",
            "docExpansion": "none",
            "filter": True,
            "deepLinking": True,
            "defaultModelsExpandDepth": 0,
            "persistAuthorization": True,
        },
    )


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
    Root endpoint for health checks and API documentation access.
    
    Returns:
        dict: Basic information about the API including status and links to documentation
    """
    return {
        "app": "ProtoNomia API",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
    }
