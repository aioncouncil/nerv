"""
NERV Geometry Engine - FastAPI Backend

The central API server that orchestrates the geometric engine,
AI assistants, and database operations for the gamified
Euclidean geometry construction system.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn

from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.api.v1.router import api_router
from app.db.session import get_db
from app.services.rust_bridge import RustGeometryService
from app.services.neo4j_service import init_neo4j, close_neo4j, get_neo4j_service

# Configure structured logging
setup_logging()
logger = structlog.get_logger()

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    
    # Startup
    logger.info("Starting NERV Geometry Engine API", version=settings.version)
    
    # Initialize services
    rust_service = RustGeometryService()
    app.state.rust_service = rust_service
    
    # Initialize Neo4j graph database
    neo4j_connected = await init_neo4j()
    if neo4j_connected:
        app.state.neo4j_service = await get_neo4j_service()
        logger.info("Neo4j graph database connected")
    else:
        logger.warning("Neo4j connection failed - graph features disabled")
    
    # Health check endpoints will verify database connections
    logger.info("NERV API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NERV Geometry Engine API")
    
    # Close Neo4j connection
    await close_neo4j()

# Create FastAPI application
app = FastAPI(
    title="NERV Geometry Engine API",
    description="""
    Industrial-grade gamified Euclidean geometry construction system.
    
    ## Features
    
    * **High-Performance Rust Core**: WebAssembly-powered geometric calculations
    * **AI Assistants (MAGI)**: Proof verification and construction guidance  
    * **Graph Database**: Neo4j for geometric relationship storage
    * **Real-time Collaboration**: WebSocket support for shared constructions
    * **Collection System**: Pokédex-style element progression
    
    ## Architecture
    
    - **Backend**: FastAPI + Rust geometric engine + Neo4j graph database
    - **Frontend**: React + TypeScript + Konva.js interactive canvas
    - **AI**: OpenAI/Anthropic integration for mathematical reasoning
    - **Infrastructure**: Docker containers + GitHub Actions CI/CD
    """,
    version=settings.version,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request
    logger.info(
        "Request processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response

# Setup exception handlers
setup_exception_handlers(app)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "nerv-geometry-api",
        "version": settings.version,
        "timestamp": time.time()
    }

@app.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check including dependencies."""
    health_status = {
        "status": "healthy",
        "service": "nerv-geometry-api", 
        "version": settings.version,
        "timestamp": time.time(),
        "dependencies": {}
    }
    
    # Check Rust geometry engine
    try:
        rust_service: RustGeometryService = app.state.rust_service
        rust_status = await rust_service.health_check()
        health_status["dependencies"]["rust_engine"] = {
            "status": "healthy" if rust_status else "unhealthy",
            "details": "Rust geometry calculation engine"
        }
    except Exception as e:
        health_status["dependencies"]["rust_engine"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Neo4j graph database
    try:
        neo4j_service = getattr(app.state, 'neo4j_service', None)
        if neo4j_service:
            neo4j_health = await neo4j_service.health_check()
            health_status["dependencies"]["neo4j"] = neo4j_health
        else:
            health_status["dependencies"]["neo4j"] = {
                "status": "unavailable",
                "details": "Neo4j service not initialized"
            }
    except Exception as e:
        health_status["dependencies"]["neo4j"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # TODO: Add other database health checks when implemented
    # health_status["dependencies"]["postgresql"] = postgres_health 
    # health_status["dependencies"]["redis"] = redis_health
    
    # Determine overall status
    dependency_statuses = [
        dep["status"] for dep in health_status["dependencies"].values()
    ]
    if "unhealthy" in dependency_statuses:
        health_status["status"] = "unhealthy"
    elif "degraded" in dependency_statuses:
        health_status["status"] = "degraded"
        
    return health_status

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "NERV Geometry Engine API",
        "version": settings.version,
        "description": "Industrial-grade gamified Euclidean geometry construction system",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_config=None  # Use our custom logging config
    )