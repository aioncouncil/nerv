"""
Collection API endpoints for Pokédex-style geometric element collection.

Handles element discovery, collection mechanics, and progression tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import structlog

from app.services.rust_bridge import RustGeometryService, ConstructionSpace
from app.core.exceptions import CollectionError

logger = structlog.get_logger()
router = APIRouter()

class CollectionElement(BaseModel):
    """A collectable geometric element."""
    id: str
    name: str
    description: str
    category: str = Field(..., description="Element category (point, line, circle, polygon)")
    rarity: str = Field(..., description="Rarity level (common, uncommon, rare, legendary)")
    unlock_requirements: List[str] = Field(default=[], description="Required elements to unlock")
    construction_template: Optional[Dict[str, Any]] = Field(None, description="Construction template")
    discovery_date: Optional[datetime] = None
    is_unlocked: bool = False
    usage_count: int = 0

class PlayerCollection(BaseModel):
    """Player's collection of geometric elements."""
    player_id: str
    username: str
    total_elements: int = 0
    unique_elements: int = 0
    common_count: int = 0
    uncommon_count: int = 0
    rare_count: int = 0
    legendary_count: int = 0
    elements: Dict[str, CollectionElement] = {}
    achievements: List[str] = []
    current_level: int = 1
    experience_points: int = 0

class ElementUnlockRequest(BaseModel):
    """Request to unlock a new element."""
    player_id: str
    construction_space: ConstructionSpace
    completed_construction: str = Field(..., description="Name of completed construction")

class CollectionStatsResponse(BaseModel):
    """Collection statistics response."""
    collection: PlayerCollection
    available_elements: List[CollectionElement]
    next_unlockable: List[CollectionElement]

# Predefined collection elements
COLLECTION_ELEMENTS = {
    "basic_point": CollectionElement(
        id="basic_point",
        name="Basic Point",
        description="A fundamental point in space - the foundation of all geometry",
        category="point",
        rarity="common",
        unlock_requirements=[],
        is_unlocked=True
    ),
    "line_segment": CollectionElement(
        id="line_segment",
        name="Line Segment",
        description="A straight line connecting two points",
        category="line",
        rarity="common",
        unlock_requirements=["basic_point"],
        construction_template={
            "type": "line_through_points",
            "required_points": 2
        }
    ),
    "circle": CollectionElement(
        id="circle",
        name="Circle",
        description="A perfect round shape with center and radius",
        category="circle", 
        rarity="common",
        unlock_requirements=["basic_point"],
        construction_template={
            "type": "circle_center_radius",
            "required_points": 2
        }
    ),
    "equilateral_triangle": CollectionElement(
        id="equilateral_triangle",
        name="Equilateral Triangle",
        description="A triangle with all sides equal - Euclid's first proposition",
        category="polygon",
        rarity="uncommon",
        unlock_requirements=["line_segment", "circle"],
        construction_template={
            "type": "equilateral_triangle",
            "required_points": 2,
            "steps": ["construct_circles", "find_intersections", "connect_points"]
        }
    ),
    "perpendicular_bisector": CollectionElement(
        id="perpendicular_bisector",
        name="Perpendicular Bisector",
        description="A line that cuts another line in half at a right angle",
        category="line",
        rarity="uncommon",
        unlock_requirements=["line_segment", "circle"],
        construction_template={
            "type": "perpendicular_bisector",
            "required_points": 2,
            "steps": ["construct_circles", "find_intersections", "connect_intersections"]
        }
    ),
    "angle_bisector": CollectionElement(
        id="angle_bisector",
        name="Angle Bisector",
        description="A line that divides an angle into two equal parts",
        category="line",
        rarity="rare",
        unlock_requirements=["perpendicular_bisector", "equilateral_triangle"],
        construction_template={
            "type": "angle_bisector",
            "required_points": 3,
            "steps": ["construct_circles", "find_intersections", "bisect_angle"]
        }
    ),
    "regular_hexagon": CollectionElement(
        id="regular_hexagon",
        name="Regular Hexagon",
        description="A six-sided polygon with all sides and angles equal",
        category="polygon",
        rarity="rare",
        unlock_requirements=["equilateral_triangle", "circle"],
        construction_template={
            "type": "regular_hexagon",
            "required_points": 2,
            "steps": ["construct_circle", "mark_radius_points", "connect_vertices"]
        }
    ),
    "golden_ratio": CollectionElement(
        id="golden_ratio",
        name="Golden Ratio",
        description="The divine proportion φ ≈ 1.618 - nature's perfect ratio",
        category="ratio",
        rarity="legendary",
        unlock_requirements=["regular_hexagon", "angle_bisector"],
        construction_template={
            "type": "golden_ratio_construction",
            "required_points": 2,
            "steps": ["construct_square", "find_midpoint", "construct_arc", "extend_side"]
        }
    )
}

async def get_rust_service() -> RustGeometryService:
    """Get the Rust geometry service."""
    return RustGeometryService()

@router.get(
    "/player/{player_id}",
    response_model=CollectionStatsResponse,
    summary="Get Player Collection",
    description="Get a player's complete element collection and statistics"
)
async def get_player_collection(
    player_id: str,
    include_locked: bool = False
):
    """Get player's collection."""
    try:
        # In a real app, this would load from database
        # For now, create a default collection
        collection = PlayerCollection(
            player_id=player_id,
            username=f"Player_{player_id[:8]}",
            elements={
                "basic_point": COLLECTION_ELEMENTS["basic_point"].copy(deep=True)
            }
        )
        
        # Update stats
        collection.total_elements = len(collection.elements)
        collection.unique_elements = len(collection.elements)
        collection.common_count = sum(1 for e in collection.elements.values() if e.rarity == "common")
        collection.uncommon_count = sum(1 for e in collection.elements.values() if e.rarity == "uncommon")
        collection.rare_count = sum(1 for e in collection.elements.values() if e.rarity == "rare")
        collection.legendary_count = sum(1 for e in collection.elements.values() if e.rarity == "legendary")
        
        # Get available elements
        available = list(COLLECTION_ELEMENTS.values()) if include_locked else [
            e for e in COLLECTION_ELEMENTS.values() if e.is_unlocked or e.id in collection.elements
        ]
        
        # Find next unlockable elements
        owned_ids = set(collection.elements.keys())
        next_unlockable = [
            element for element in COLLECTION_ELEMENTS.values()
            if (element.id not in owned_ids and 
                all(req in owned_ids for req in element.unlock_requirements))
        ]
        
        logger.info(
            "Retrieved player collection",
            player_id=player_id,
            total_elements=collection.total_elements,
            next_unlockable=len(next_unlockable)
        )
        
        return CollectionStatsResponse(
            collection=collection,
            available_elements=available,
            next_unlockable=next_unlockable
        )
        
    except Exception as e:
        logger.error("Failed to get player collection", player_id=player_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve collection: {str(e)}"
        )

@router.post(
    "/unlock-element",
    response_model=Dict[str, Any],
    summary="Unlock Element",
    description="Attempt to unlock a new geometric element through construction"
)
async def unlock_element(
    request: ElementUnlockRequest,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Unlock a new element through successful construction."""
    try:
        # Analyze the construction space to determine what was built
        analysis = await _analyze_construction(request.construction_space, rust_service)
        
        # Check if any elements can be unlocked
        unlocked_elements = []
        experience_gained = 0
        
        for element_id, element in COLLECTION_ELEMENTS.items():
            if (element.name.lower().replace(" ", "_") == request.completed_construction.lower() and
                _can_unlock_element(element, request.construction_space)):
                
                unlocked_element = element.copy(deep=True)
                unlocked_element.discovery_date = datetime.now()
                unlocked_element.is_unlocked = True
                unlocked_elements.append(unlocked_element)
                
                # Calculate experience based on rarity
                rarity_xp = {
                    "common": 10,
                    "uncommon": 25,
                    "rare": 50,
                    "legendary": 100
                }
                experience_gained += rarity_xp.get(element.rarity, 10)
        
        logger.info(
            "Element unlock attempt",
            player_id=request.player_id,
            construction=request.completed_construction,
            unlocked_count=len(unlocked_elements),
            experience_gained=experience_gained
        )
        
        return {
            "success": len(unlocked_elements) > 0,
            "unlocked_elements": [element.dict() for element in unlocked_elements],
            "experience_gained": experience_gained,
            "construction_analysis": analysis,
            "message": f"Unlocked {len(unlocked_elements)} new elements!" if unlocked_elements else "No new elements unlocked"
        }
        
    except Exception as e:
        logger.error("Element unlock failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Element unlock failed: {str(e)}"
        )

@router.get(
    "/elements",
    response_model=Dict[str, Any],
    summary="List All Elements",
    description="Get all available geometric elements in the collection"
)
async def list_elements(
    category: Optional[str] = None,
    rarity: Optional[str] = None,
    unlocked_only: bool = False
):
    """List all collection elements with optional filtering."""
    try:
        elements = list(COLLECTION_ELEMENTS.values())
        
        # Apply filters
        if category:
            elements = [e for e in elements if e.category == category]
        if rarity:
            elements = [e for e in elements if e.rarity == rarity]
        if unlocked_only:
            elements = [e for e in elements if e.is_unlocked]
        
        # Group by category and rarity
        by_category = {}
        by_rarity = {}
        
        for element in elements:
            if element.category not in by_category:
                by_category[element.category] = []
            by_category[element.category].append(element)
            
            if element.rarity not in by_rarity:
                by_rarity[element.rarity] = []
            by_rarity[element.rarity].append(element)
        
        return {
            "elements": [element.dict() for element in elements],
            "total_count": len(elements),
            "by_category": {k: len(v) for k, v in by_category.items()},
            "by_rarity": {k: len(v) for k, v in by_rarity.items()},
            "categories": list(by_category.keys()),
            "rarities": list(by_rarity.keys())
        }
        
    except Exception as e:
        logger.error("Failed to list elements", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list elements: {str(e)}"
        )

@router.post(
    "/achievements/check",
    response_model=Dict[str, Any],
    summary="Check Achievements",
    description="Check and award achievements based on collection progress"
)
async def check_achievements(
    player_id: str,
    construction_space: ConstructionSpace
):
    """Check for new achievements."""
    try:
        achievements = []
        
        # Define achievements
        achievement_checks = [
            {
                "id": "first_construction",
                "name": "First Steps",
                "description": "Complete your first geometric construction",
                "check": lambda: len(construction_space.history) >= 1
            },
            {
                "id": "triangle_master",
                "name": "Triangle Master", 
                "description": "Construct 10 different triangles",
                "check": lambda: len([h for h in construction_space.history if "triangle" in str(h).lower()]) >= 10
            },
            {
                "id": "circle_sage",
                "name": "Circle Sage",
                "description": "Master the art of circles with 25 circle constructions",
                "check": lambda: len(construction_space.circles) >= 25
            },
            {
                "id": "euclid_student",
                "name": "Student of Euclid",
                "description": "Complete all propositions from Book I",
                "check": lambda: False  # Complex check for all Book I propositions
            }
        ]
        
        for achievement in achievement_checks:
            if achievement["check"]():
                achievements.append({
                    "id": achievement["id"],
                    "name": achievement["name"],
                    "description": achievement["description"],
                    "unlocked_at": datetime.now()
                })
        
        logger.info(
            "Achievement check completed",
            player_id=player_id,
            new_achievements=len(achievements)
        )
        
        return {
            "new_achievements": achievements,
            "total_new": len(achievements),
            "message": f"Congratulations! You earned {len(achievements)} new achievements!" if achievements else "No new achievements"
        }
        
    except Exception as e:
        logger.error("Achievement check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Achievement check failed: {str(e)}"
        )

def _can_unlock_element(element: CollectionElement, construction_space: ConstructionSpace) -> bool:
    """Check if an element can be unlocked based on construction space."""
    
    # Check basic requirements
    if not element.unlock_requirements:
        return True
    
    # For demo purposes, simple heuristics based on construction content
    if element.id == "line_segment":
        return len(construction_space.lines) > 0
    elif element.id == "circle":
        return len(construction_space.circles) > 0
    elif element.id == "equilateral_triangle":
        return len(construction_space.lines) >= 3 and len(construction_space.circles) >= 2
    elif element.id == "perpendicular_bisector":
        return len(construction_space.lines) >= 2 and len(construction_space.circles) >= 2
    
    return False

async def _analyze_construction(
    construction_space: ConstructionSpace, 
    rust_service: RustGeometryService
) -> Dict[str, Any]:
    """Analyze a construction space to identify what was built."""
    
    analysis = {
        "point_count": len(construction_space.points),
        "line_count": len(construction_space.lines),
        "circle_count": len(construction_space.circles),
        "construction_steps": len(construction_space.history),
        "identified_patterns": []
    }
    
    # Pattern recognition
    if (analysis["line_count"] == 3 and 
        analysis["circle_count"] >= 2 and 
        analysis["point_count"] >= 3):
        analysis["identified_patterns"].append("equilateral_triangle")
    
    if (analysis["line_count"] >= 2 and 
        analysis["circle_count"] >= 2):
        analysis["identified_patterns"].append("perpendicular_bisector")
    
    if analysis["circle_count"] >= 1:
        analysis["identified_patterns"].append("circle")
    
    if analysis["line_count"] >= 1:
        analysis["identified_patterns"].append("line_segment")
    
    return analysis