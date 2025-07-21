"""
API v1 router for the NERV Geometry Engine.

Aggregates all API endpoints under the /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import geometry, construction, collection, magi, graph

api_router = APIRouter()

# Include all endpoint modules
api_router.include_router(
    geometry.router, 
    prefix="/geometry", 
    tags=["geometry"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    construction.router,
    prefix="/construction", 
    tags=["construction"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    collection.router,
    prefix="/collection",
    tags=["collection"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    magi.router,
    prefix="/magi",
    tags=["magi", "ai"],
    responses={404: {"description": "Not found"}}
)

api_router.include_router(
    graph.router,
    prefix="/graph",
    tags=["graph", "neo4j"],
    responses={404: {"description": "Not found"}}
)