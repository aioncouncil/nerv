"""
MAGI AI Assistant API endpoints.

Provides AI-powered assistance for geometric construction, proof checking,
and educational guidance inspired by the MAGI systems from Evangelion.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import structlog

from app.services.rust_bridge import RustGeometryService, ConstructionSpace
from app.core.exceptions import MAGIError

logger = structlog.get_logger()
router = APIRouter()

class MAGISystem(str, Enum):
    """The three MAGI systems, each with different specializations."""
    CASPER = "casper"      # Construction and creative problem solving
    MELCHIOR = "melchior"  # Mathematical analysis and proof verification  
    BALTHASAR = "balthasar" # Educational guidance and step-by-step teaching

class QueryType(str, Enum):
    """Types of queries the MAGI can handle."""
    CONSTRUCTION_HELP = "construction_help"
    PROOF_CHECK = "proof_check"
    STEP_EXPLANATION = "step_explanation"
    THEOREM_INFO = "theorem_info"
    HINT_REQUEST = "hint_request"
    ERROR_ANALYSIS = "error_analysis"
    LEARNING_PATH = "learning_path"

class MAGIQuery(BaseModel):
    """Query to a MAGI system."""
    query_type: QueryType
    content: str = Field(..., description="The question or problem statement")
    construction_space: Optional[ConstructionSpace] = Field(None, description="Current construction context")
    target_theorem: Optional[str] = Field(None, description="Target theorem or construction")
    difficulty_level: str = Field("beginner", description="Student's skill level")
    preferred_magi: Optional[MAGISystem] = Field(None, description="Preferred MAGI system")

class MAGIResponse(BaseModel):
    """Response from a MAGI system."""
    magi_system: MAGISystem
    response_type: QueryType
    content: str
    suggestions: List[str] = Field(default=[], description="Actionable suggestions")
    next_steps: List[str] = Field(default=[], description="Recommended next steps")
    confidence: float = Field(..., description="Confidence in the response (0-1)")
    additional_resources: List[Dict[str, str]] = Field(default=[], description="Additional learning resources")
    timestamp: datetime = Field(default_factory=datetime.now)

class ProofVerificationRequest(BaseModel):
    """Request for proof verification."""
    construction_space: ConstructionSpace
    claimed_theorem: str
    proof_steps: List[str]
    student_explanation: Optional[str] = None

class ProofVerificationResponse(BaseModel):
    """Response from proof verification."""
    is_valid: bool
    verification_details: Dict[str, Any]
    errors_found: List[str] = []
    suggestions: List[str] = []
    missing_steps: List[str] = []
    alternative_approaches: List[str] = []

async def get_rust_service() -> RustGeometryService:
    """Get the Rust geometry service."""
    return RustGeometryService()

@router.post(
    "/query",
    response_model=MAGIResponse,
    summary="Query MAGI System",
    description="Send a query to the MAGI AI system for assistance"
)
async def query_magi(
    query: MAGIQuery,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Query the MAGI system for assistance."""
    try:
        # Route to appropriate MAGI system
        magi_system = _select_magi_system(query)
        
        # Generate response based on query type and MAGI system
        response = await _generate_magi_response(query, magi_system, rust_service)
        
        logger.info(
            "MAGI query processed",
            magi_system=magi_system,
            query_type=query.query_type,
            confidence=response.confidence
        )
        
        return response
        
    except Exception as e:
        logger.error("MAGI query failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MAGI query failed: {str(e)}"
        )

@router.post(
    "/verify-proof",
    response_model=ProofVerificationResponse,
    summary="Verify Geometric Proof",
    description="Verify the correctness of a geometric proof"
)
async def verify_proof(
    request: ProofVerificationRequest,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Verify a geometric proof using MELCHIOR (analysis specialist)."""
    try:
        verification = await _verify_geometric_proof(request, rust_service)
        
        logger.info(
            "Proof verification completed",
            theorem=request.claimed_theorem,
            is_valid=verification.is_valid,
            errors_found=len(verification.errors_found)
        )
        
        return verification
        
    except Exception as e:
        logger.error("Proof verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Proof verification failed: {str(e)}"
        )

@router.get(
    "/learning-path/{topic}",
    response_model=Dict[str, Any],
    summary="Get Learning Path",
    description="Get a structured learning path for a geometric topic"
)
async def get_learning_path(
    topic: str,
    current_level: str = "beginner",
    include_prerequisites: bool = True
):
    """Get a learning path for a specific geometric topic."""
    try:
        learning_path = _generate_learning_path(topic, current_level, include_prerequisites)
        
        logger.info(
            "Learning path generated",
            topic=topic,
            level=current_level,
            steps=len(learning_path.get("steps", []))
        )
        
        return learning_path
        
    except Exception as e:
        logger.error("Learning path generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Learning path generation failed: {str(e)}"
        )

@router.post(
    "/analyze-error",
    response_model=Dict[str, Any],
    summary="Analyze Construction Error",
    description="Analyze errors in geometric constructions"
)
async def analyze_error(
    construction_space: ConstructionSpace,
    error_description: str,
    attempted_construction: Optional[str] = None,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Analyze construction errors and provide guidance."""
    try:
        analysis = await _analyze_construction_error(
            construction_space, 
            error_description, 
            attempted_construction,
            rust_service
        )
        
        logger.info(
            "Error analysis completed",
            error_type=analysis.get("error_type"),
            suggestions_count=len(analysis.get("suggestions", []))
        )
        
        return analysis
        
    except Exception as e:
        logger.error("Error analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error analysis failed: {str(e)}"
        )

@router.get(
    "/theorem/{theorem_name}",
    response_model=Dict[str, Any],
    summary="Get Theorem Information",
    description="Get detailed information about a geometric theorem"
)
async def get_theorem_info(
    theorem_name: str,
    include_proof: bool = True,
    include_applications: bool = True,
    difficulty_level: str = "intermediate"
):
    """Get detailed information about a geometric theorem."""
    try:
        theorem_info = _get_theorem_information(
            theorem_name, 
            include_proof, 
            include_applications,
            difficulty_level
        )
        
        logger.info(
            "Theorem information retrieved",
            theorem=theorem_name,
            difficulty=difficulty_level
        )
        
        return theorem_info
        
    except Exception as e:
        logger.error("Theorem info retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Theorem information not found: {str(e)}"
        )

def _select_magi_system(query: MAGIQuery) -> MAGISystem:
    """Select the most appropriate MAGI system for a query."""
    
    if query.preferred_magi:
        return query.preferred_magi
    
    # Route based on query type
    if query.query_type in [QueryType.CONSTRUCTION_HELP, QueryType.HINT_REQUEST]:
        return MAGISystem.CASPER  # Creative problem solving
    elif query.query_type in [QueryType.PROOF_CHECK, QueryType.ERROR_ANALYSIS]:
        return MAGISystem.MELCHIOR  # Mathematical analysis
    elif query.query_type in [QueryType.STEP_EXPLANATION, QueryType.LEARNING_PATH, QueryType.THEOREM_INFO]:
        return MAGISystem.BALTHASAR  # Educational guidance
    
    # Default to CASPER for general queries
    return MAGISystem.CASPER

async def _generate_magi_response(
    query: MAGIQuery, 
    magi_system: MAGISystem, 
    rust_service: RustGeometryService
) -> MAGIResponse:
    """Generate a response from the specified MAGI system."""
    
    # This is a simplified AI response generator
    # In a real system, this would integrate with actual AI/ML models
    
    responses = {
        (MAGISystem.CASPER, QueryType.CONSTRUCTION_HELP): {
            "content": f"CASPER suggests approaching '{query.content}' by breaking it into fundamental steps. Consider starting with the basic elements you have and work systematically toward your goal.",
            "suggestions": [
                "Identify what geometric objects you already have",
                "List what objects you need to create",
                "Find the fundamental constructions that bridge the gap",
                "Use compass and straightedge rules systematically"
            ],
            "confidence": 0.85
        },
        (MAGISystem.MELCHIOR, QueryType.PROOF_CHECK): {
            "content": f"MELCHIOR has analyzed your construction. The logical structure appears sound, but I need to verify each step rigorously.",
            "suggestions": [
                "Ensure each step follows logically from previous steps",
                "Verify that all geometric objects are properly defined",
                "Check that compass and straightedge rules are followed",
                "Confirm the final result matches the intended theorem"
            ],
            "confidence": 0.78
        },
        (MAGISystem.BALTHASAR, QueryType.STEP_EXPLANATION): {
            "content": f"BALTHASAR will guide you through this step by step. '{query.content}' can be understood by examining the underlying geometric principles.",
            "suggestions": [
                "Start with what you already understand about the problem",
                "Connect this to geometric principles you've learned before",
                "Practice similar constructions to build intuition",
                "Ask questions when something isn't clear"
            ],
            "confidence": 0.92
        }
    }
    
    # Get response template or default
    key = (magi_system, query.query_type)
    template = responses.get(key, {
        "content": f"{magi_system.value.upper()} is processing your query about '{query.content}'. This is a complex geometric problem that requires careful analysis.",
        "suggestions": [
            "Break the problem into smaller parts",
            "Use fundamental geometric principles",
            "Work systematically and check each step"
        ],
        "confidence": 0.70
    })
    
    # Add context-specific suggestions if construction space is provided
    next_steps = []
    if query.construction_space:
        if len(query.construction_space.points) == 0:
            next_steps.append("Start by placing some initial points")
        elif len(query.construction_space.lines) == 0:
            next_steps.append("Try constructing lines through your points")
        elif len(query.construction_space.circles) == 0:
            next_steps.append("Consider adding circles to find intersections")
        else:
            next_steps.append("Look for intersections to create new points")
    
    additional_resources = [
        {
            "title": f"Euclid's Elements - Relevant Propositions",
            "url": "https://mathcs.clarku.edu/~djoyce/elements/elements.html",
            "description": "Classical geometric constructions and proofs"
        },
        {
            "title": "Interactive Geometry Software",
            "url": "https://www.geogebra.org/",
            "description": "Practice geometric constructions interactively"
        }
    ]
    
    return MAGIResponse(
        magi_system=magi_system,
        response_type=query.query_type,
        content=template["content"],
        suggestions=template["suggestions"],
        next_steps=next_steps,
        confidence=template["confidence"],
        additional_resources=additional_resources
    )

async def _verify_geometric_proof(
    request: ProofVerificationRequest,
    rust_service: RustGeometryService
) -> ProofVerificationResponse:
    """Verify a geometric proof."""
    
    verification_details = {
        "theorem": request.claimed_theorem,
        "steps_analyzed": len(request.proof_steps),
        "construction_valid": True,  # Simplified for demo
        "logical_flow": "coherent"
    }
    
    errors_found = []
    suggestions = []
    missing_steps = []
    
    # Simplified proof checking logic
    if len(request.proof_steps) < 3:
        errors_found.append("Proof appears incomplete - very few steps provided")
        missing_steps.append("More detailed explanation of each construction step")
    
    if "given" not in " ".join(request.proof_steps).lower():
        missing_steps.append("Clearly state what is given in the problem")
    
    if "therefore" not in " ".join(request.proof_steps).lower():
        missing_steps.append("Include a clear conclusion with 'therefore' or 'hence'")
    
    # Check construction space consistency
    total_objects = (len(request.construction_space.points) + 
                    len(request.construction_space.lines) + 
                    len(request.construction_space.circles))
    
    if total_objects < 3:
        errors_found.append("Construction space seems incomplete for the claimed theorem")
        suggestions.append("Ensure all necessary geometric objects are constructed")
    
    is_valid = len(errors_found) == 0
    
    if not is_valid:
        suggestions.extend([
            "Review each step for logical consistency",
            "Ensure all geometric objects are properly justified",
            "Check that the conclusion follows from the premises"
        ])
    
    alternative_approaches = [
        "Try a coordinate geometry approach",
        "Consider using similar triangles",
        "Explore a proof by contradiction"
    ]
    
    return ProofVerificationResponse(
        is_valid=is_valid,
        verification_details=verification_details,
        errors_found=errors_found,
        suggestions=suggestions,
        missing_steps=missing_steps,
        alternative_approaches=alternative_approaches
    )

def _generate_learning_path(topic: str, level: str, include_prerequisites: bool) -> Dict[str, Any]:
    """Generate a structured learning path for a topic."""
    
    learning_paths = {
        "triangles": {
            "title": "Mastering Triangles",
            "description": "Complete guide to triangle constructions and properties",
            "prerequisites": ["basic_points", "line_construction"] if include_prerequisites else [],
            "steps": [
                {
                    "step": 1,
                    "title": "Basic Triangle Construction",
                    "description": "Learn to construct triangles given three sides",
                    "constructions": ["equilateral_triangle"],
                    "difficulty": "beginner"
                },
                {
                    "step": 2,
                    "title": "Triangle Centers",
                    "description": "Discover centroid, incenter, circumcenter",
                    "constructions": ["perpendicular_bisector", "angle_bisector"],
                    "difficulty": "intermediate"
                },
                {
                    "step": 3,
                    "title": "Special Triangles",
                    "description": "Right triangles and special ratios",
                    "constructions": ["right_triangle", "golden_ratio"],
                    "difficulty": "advanced"
                }
            ],
            "estimated_time": "2-3 weeks",
            "key_theorems": ["Pythagorean Theorem", "Triangle Inequality", "Sum of Angles"]
        },
        "circles": {
            "title": "Circle Geometry Mastery",
            "description": "From basic circles to complex circle theorems",
            "prerequisites": ["basic_points"] if include_prerequisites else [],
            "steps": [
                {
                    "step": 1,
                    "title": "Basic Circle Construction",
                    "description": "Construct circles with compass and straightedge",
                    "constructions": ["circle"],
                    "difficulty": "beginner"
                },
                {
                    "step": 2,
                    "title": "Tangent Lines",
                    "description": "Construct tangent lines to circles",
                    "constructions": ["tangent_to_circle"],
                    "difficulty": "intermediate"
                },
                {
                    "step": 3,
                    "title": "Circle Theorems",
                    "description": "Power of a point and other circle theorems",
                    "constructions": ["inscribed_angle", "power_of_point"],
                    "difficulty": "advanced"
                }
            ],
            "estimated_time": "3-4 weeks",
            "key_theorems": ["Inscribed Angle Theorem", "Power of a Point", "Tangent-Secant Theorem"]
        }
    }
    
    return learning_paths.get(topic.lower(), {
        "title": f"Learning Path for {topic.title()}",
        "description": f"Custom learning path for {topic}",
        "steps": [
            {
                "step": 1,
                "title": f"Introduction to {topic}",
                "description": f"Basic concepts and constructions in {topic}",
                "difficulty": level
            }
        ],
        "estimated_time": "1-2 weeks"
    })

async def _analyze_construction_error(
    construction_space: ConstructionSpace,
    error_description: str,
    attempted_construction: Optional[str],
    rust_service: RustGeometryService
) -> Dict[str, Any]:
    """Analyze construction errors."""
    
    error_analysis = {
        "error_type": "unknown",
        "severity": "medium",
        "likely_causes": [],
        "suggestions": [],
        "corrective_steps": []
    }
    
    # Simple error classification
    error_lower = error_description.lower()
    
    if "point" in error_lower and ("same" in error_lower or "identical" in error_lower):
        error_analysis.update({
            "error_type": "identical_points",
            "severity": "high",
            "likely_causes": ["Trying to create line/circle with identical points"],
            "suggestions": [
                "Ensure points are distinct before creating lines or circles",
                "Check point coordinates to verify they are different",
                "Use the point creation tool to add new distinct points"
            ],
            "corrective_steps": [
                "Create a new point at different coordinates",
                "Verify all points have unique positions",
                "Retry the construction with distinct points"
            ]
        })
    
    elif "intersection" in error_lower and ("none" in error_lower or "no" in error_lower):
        error_analysis.update({
            "error_type": "no_intersection",
            "severity": "medium",
            "likely_causes": ["Geometric objects don't intersect", "Objects are parallel or too far apart"],
            "suggestions": [
                "Check if the objects actually intersect geometrically",
                "Adjust the size or position of circles",
                "Verify the construction logic"
            ],
            "corrective_steps": [
                "Review the geometric relationship between objects",
                "Modify circle radii to ensure intersection",
                "Check for parallel lines that won't intersect"
            ]
        })
    
    elif "construct" in error_lower and "fail" in error_lower:
        error_analysis.update({
            "error_type": "construction_failure",
            "severity": "high",
            "likely_causes": ["Missing prerequisites", "Invalid construction sequence"],
            "suggestions": [
                "Verify all required objects exist before construction",
                "Follow the proper construction sequence",
                "Check that compass and straightedge rules are followed"
            ],
            "corrective_steps": [
                "List all objects needed for the construction",
                "Create missing prerequisite objects first",
                "Retry construction in the correct order"
            ]
        })
    
    # Add context from construction space
    context_notes = []
    if len(construction_space.points) == 0:
        context_notes.append("No points in construction - start by adding basic points")
    if len(construction_space.history) == 0:
        context_notes.append("No construction history - this appears to be a fresh start")
    
    error_analysis["context_notes"] = context_notes
    error_analysis["construction_summary"] = {
        "points": len(construction_space.points),
        "lines": len(construction_space.lines),
        "circles": len(construction_space.circles),
        "steps": len(construction_space.history)
    }
    
    return error_analysis

def _get_theorem_information(
    theorem_name: str,
    include_proof: bool,
    include_applications: bool,
    difficulty_level: str
) -> Dict[str, Any]:
    """Get detailed information about a geometric theorem."""
    
    theorems = {
        "pythagorean_theorem": {
            "name": "Pythagorean Theorem",
            "statement": "In a right triangle, the square of the hypotenuse equals the sum of squares of the other two sides: a² + b² = c²",
            "difficulty": "intermediate",
            "category": "triangles",
            "historical_note": "Named after Pythagoras (~570-495 BCE), though known to earlier civilizations",
            "proof_sketch": "Can be proven using squares on the sides of a right triangle" if include_proof else None,
            "applications": [
                "Distance calculations in coordinate geometry",
                "Right triangle construction",
                "Verification of right angles"
            ] if include_applications else [],
            "related_theorems": ["Law of Cosines", "Distance Formula"],
            "construction_applications": ["right_triangle", "distance_measurement"]
        },
        "sum_of_angles": {
            "name": "Triangle Angle Sum Theorem",
            "statement": "The sum of interior angles in any triangle is 180 degrees",
            "difficulty": "beginner",
            "category": "triangles",
            "historical_note": "Known to ancient Greek mathematicians, appears in Euclid's Elements",
            "proof_sketch": "Can be proven by constructing a line parallel to one side through the opposite vertex" if include_proof else None,
            "applications": [
                "Finding unknown angles in triangles",
                "Proving triangle congruence",
                "Polygon angle calculations"
            ] if include_applications else [],
            "related_theorems": ["Exterior Angle Theorem", "Polygon Angle Sum"],
            "construction_applications": ["angle_measurement", "triangle_construction"]
        }
    }
    
    theorem_key = theorem_name.lower().replace(" ", "_")
    theorem_info = theorems.get(theorem_key)
    
    if not theorem_info:
        # Generate basic info for unknown theorems
        theorem_info = {
            "name": theorem_name.replace("_", " ").title(),
            "statement": f"Information about {theorem_name} is not available in the current knowledge base",
            "difficulty": difficulty_level,
            "category": "general",
            "construction_applications": []
        }
    
    return {
        "theorem": theorem_info,
        "learning_resources": [
            {
                "title": "Euclid's Elements",
                "description": "Classical geometric theorems and proofs",
                "relevance": "foundational"
            },
            {
                "title": "Interactive Geometry",
                "description": "Hands-on exploration of geometric theorems",
                "relevance": "practical"
            }
        ],
        "difficulty_level": difficulty_level,
        "next_topics": ["related_constructions", "advanced_applications"]
    }