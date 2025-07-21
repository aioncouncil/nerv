"""
Geometry API endpoints for basic geometric operations.

Handles points, lines, circles, and fundamental geometric calculations
through the Rust geometry engine.
"""

from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import structlog

from app.services.rust_bridge import RustGeometryService, ConstructionSpace, Point, Line, Circle
from app.core.exceptions import GeometryEngineError

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models for API requests/responses
class PointCreate(BaseModel):
    """Request model for creating a point."""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")  
    label: Optional[str] = Field(None, description="Optional point label")

class LineCreate(BaseModel):
    """Request model for creating a line."""
    point1_id: str = Field(..., description="ID of first point")
    point2_id: str = Field(..., description="ID of second point")
    label: Optional[str] = Field(None, description="Optional line label")

class CircleCreate(BaseModel):
    """Request model for creating a circle."""
    center_id: str = Field(..., description="ID of center point")
    radius_point_id: str = Field(..., description="ID of radius point")
    label: Optional[str] = Field(None, description="Optional circle label")

class IntersectionRequest(BaseModel):
    """Request model for finding intersections."""
    obj1_id: str = Field(..., description="ID of first geometric object")
    obj2_id: str = Field(..., description="ID of second geometric object")

class GeometryResponse(BaseModel):
    """Response model for geometry operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ConstructionSpaceResponse(BaseModel):
    """Response model for construction space operations."""
    construction_space: ConstructionSpace
    operation: str
    created_id: Optional[str] = None

# Dependency to get Rust service
async def get_rust_service() -> RustGeometryService:
    """Get the Rust geometry service."""
    # In a real app, this would be injected from app state
    return RustGeometryService()

@router.get(
    "/health",
    response_model=GeometryResponse,
    summary="Geometry Engine Health Check",
    description="Check if the Rust geometry engine is available and responsive"
)
async def geometry_health_check(
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Check geometry engine health."""
    try:
        is_healthy = await rust_service.health_check()
        return GeometryResponse(
            success=is_healthy,
            message="Geometry engine is healthy" if is_healthy else "Geometry engine is unhealthy",
            data={"engine_available": is_healthy}
        )
    except Exception as e:
        logger.error("Geometry health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Geometry engine health check failed: {str(e)}"
        )

@router.post(
    "/construction-space",
    response_model=ConstructionSpaceResponse,
    summary="Create Construction Space",
    description="Create a new empty geometric construction space"
)
async def create_construction_space(
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Create a new construction space."""
    try:
        construction_space = await rust_service.create_construction_space()
        
        logger.info("Created new construction space")
        
        return ConstructionSpaceResponse(
            construction_space=construction_space,
            operation="create_construction_space"
        )
    except Exception as e:
        logger.error("Failed to create construction space", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create construction space: {str(e)}"
        )

@router.post(
    "/points",
    response_model=ConstructionSpaceResponse,
    summary="Add Point",
    description="Add a point to the construction space"
)
async def add_point(
    point_data: PointCreate,
    construction_space_data: ConstructionSpace,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Add a point to the construction space."""
    try:
        point_id, updated_space = await rust_service.add_point(
            construction_space_data,
            point_data.x,
            point_data.y,
            point_data.label
        )
        
        logger.info(
            "Added point to construction space",
            point_id=point_id,
            x=point_data.x,
            y=point_data.y,
            label=point_data.label
        )
        
        return ConstructionSpaceResponse(
            construction_space=updated_space,
            operation="add_point",
            created_id=point_id
        )
    except GeometryEngineError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to add point", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add point: {str(e)}"
        )

@router.post(
    "/lines", 
    response_model=ConstructionSpaceResponse,
    summary="Construct Line",
    description="Construct a line through two points"
)
async def construct_line(
    line_data: LineCreate,
    construction_space_data: ConstructionSpace,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Construct a line through two points."""
    try:
        line_id, updated_space = await rust_service.construct_line(
            construction_space_data,
            line_data.point1_id,
            line_data.point2_id,
            line_data.label
        )
        
        logger.info(
            "Constructed line",
            line_id=line_id,
            point1_id=line_data.point1_id,
            point2_id=line_data.point2_id,
            label=line_data.label
        )
        
        return ConstructionSpaceResponse(
            construction_space=updated_space,
            operation="construct_line",
            created_id=line_id
        )
    except GeometryEngineError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to construct line", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to construct line: {str(e)}"
        )

@router.post(
    "/circles",
    response_model=ConstructionSpaceResponse,
    summary="Construct Circle", 
    description="Construct a circle with center and radius point"
)
async def construct_circle(
    circle_data: CircleCreate,
    construction_space_data: ConstructionSpace,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Construct a circle with center and radius point."""
    try:
        circle_id, updated_space = await rust_service.construct_circle(
            construction_space_data,
            circle_data.center_id,
            circle_data.radius_point_id,
            circle_data.label
        )
        
        logger.info(
            "Constructed circle",
            circle_id=circle_id,
            center_id=circle_data.center_id,
            radius_point_id=circle_data.radius_point_id,
            label=circle_data.label
        )
        
        return ConstructionSpaceResponse(
            construction_space=updated_space,
            operation="construct_circle",
            created_id=circle_id
        )
    except GeometryEngineError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to construct circle", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to construct circle: {str(e)}"
        )

@router.post(
    "/intersections",
    response_model=Dict[str, Any],
    summary="Find Intersections",
    description="Find intersection points between two geometric objects"
)
async def find_intersections(
    intersection_data: IntersectionRequest,
    construction_space_data: ConstructionSpace,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Find intersections between two geometric objects."""
    try:
        intersections, updated_space = await rust_service.find_intersections(
            construction_space_data,
            intersection_data.obj1_id,
            intersection_data.obj2_id
        )
        
        logger.info(
            "Found intersections",
            obj1_id=intersection_data.obj1_id,
            obj2_id=intersection_data.obj2_id,
            intersection_count=len(intersections)
        )
        
        return {
            "construction_space": updated_space,
            "intersections": [point.dict() for point in intersections],
            "intersection_count": len(intersections),
            "operation": "find_intersections"
        }
    except GeometryEngineError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to find intersections", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find intersections: {str(e)}"
        )

@router.get(
    "/construction-space/{space_id}/summary",
    response_model=Dict[str, Any],
    summary="Construction Space Summary",
    description="Get summary statistics for a construction space"
)
async def get_construction_summary(
    construction_space_data: ConstructionSpace
):
    """Get construction space summary."""
    try:
        summary = {
            "point_count": len(construction_space_data.points),
            "line_count": len(construction_space_data.lines),
            "circle_count": len(construction_space_data.circles),
            "total_objects": (
                len(construction_space_data.points) + 
                len(construction_space_data.lines) + 
                len(construction_space_data.circles)
            ),
            "construction_steps": len(construction_space_data.history),
            "points": list(construction_space_data.points.keys()),
            "lines": list(construction_space_data.lines.keys()),
            "circles": list(construction_space_data.circles.keys())
        }
        
        return {
            "summary": summary,
            "operation": "get_construction_summary"
        }
    except Exception as e:
        logger.error("Failed to get construction summary", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get construction summary: {str(e)}"
        )