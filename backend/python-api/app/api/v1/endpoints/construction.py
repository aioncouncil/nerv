"""
Construction API endpoints for geometric construction operations.

Handles construction validation, step recording, and playback functionality.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import structlog

from app.services.rust_bridge import RustGeometryService, ConstructionSpace
from app.core.exceptions import ConstructionValidationError

logger = structlog.get_logger()
router = APIRouter()

class ConstructionStep(BaseModel):
    """A single construction step."""
    step_number: int = Field(..., description="Step number in sequence")
    step_type: str = Field(..., description="Type of construction step")
    description: str = Field(..., description="Human-readable description")
    dependencies: List[str] = Field(default=[], description="Required object IDs")
    created_objects: List[str] = Field(default=[], description="Object IDs created by this step")
    metadata: Dict[str, Any] = Field(default={}, description="Additional step metadata")

class ConstructionValidationRequest(BaseModel):
    """Request to validate a construction step."""
    construction_space: ConstructionSpace
    step: ConstructionStep

class ConstructionSequence(BaseModel):
    """A sequence of construction steps."""
    name: str = Field(..., description="Name of the construction sequence")
    description: str = Field(..., description="Description of what is being constructed")
    steps: List[ConstructionStep] = Field(..., description="Ordered list of construction steps")
    target_theorem: Optional[str] = Field(None, description="Theorem being demonstrated")

async def get_rust_service() -> RustGeometryService:
    """Get the Rust geometry service."""
    return RustGeometryService()

@router.post(
    "/validate-step",
    summary="Validate Construction Step",
    description="Validate if a construction step is geometrically valid"
)
async def validate_construction_step(
    request: ConstructionValidationRequest,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Validate a single construction step."""
    try:
        # Convert to format expected by Rust engine
        step_data = {
            "step_type": request.step.step_type,
            "dependencies": request.step.dependencies,
            "metadata": request.step.metadata
        }
        
        is_valid = await rust_service.validate_construction(
            request.construction_space,
            step_data
        )
        
        logger.info(
            "Construction step validation",
            step_type=request.step.step_type,
            is_valid=is_valid,
            step_number=request.step.step_number
        )
        
        return {
            "is_valid": is_valid,
            "step": request.step,
            "validation_message": "Step is valid" if is_valid else "Step is invalid",
            "suggestions": _get_validation_suggestions(request.step, request.construction_space) if not is_valid else []
        }
        
    except Exception as e:
        logger.error("Construction step validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation failed: {str(e)}"
        )

@router.post(
    "/validate-sequence",
    summary="Validate Construction Sequence", 
    description="Validate an entire sequence of construction steps"
)
async def validate_construction_sequence(
    sequence: ConstructionSequence,
    initial_construction_space: ConstructionSpace,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Validate an entire construction sequence."""
    try:
        current_space = initial_construction_space.copy(deep=True)
        validation_results = []
        
        for i, step in enumerate(sequence.steps):
            # Validate each step in sequence
            step_data = {
                "step_type": step.step_type,
                "dependencies": step.dependencies,
                "metadata": step.metadata
            }
            
            is_valid = await rust_service.validate_construction(current_space, step_data)
            
            validation_result = {
                "step_number": i + 1,
                "step": step,
                "is_valid": is_valid,
                "validation_message": "Step is valid" if is_valid else "Step is invalid"
            }
            
            if not is_valid:
                validation_result["suggestions"] = _get_validation_suggestions(step, current_space)
                
            validation_results.append(validation_result)
            
            # If step is invalid, don't continue validation
            if not is_valid:
                break
                
            # TODO: Actually execute the step to update the construction space
            # This would require implementing step execution in the Rust bridge
        
        overall_valid = all(result["is_valid"] for result in validation_results)
        
        logger.info(
            "Construction sequence validation",
            sequence_name=sequence.name,
            total_steps=len(sequence.steps),
            validated_steps=len(validation_results),
            overall_valid=overall_valid
        )
        
        return {
            "sequence": sequence,
            "overall_valid": overall_valid,
            "validation_results": validation_results,
            "summary": {
                "total_steps": len(sequence.steps),
                "valid_steps": sum(1 for r in validation_results if r["is_valid"]),
                "invalid_steps": sum(1 for r in validation_results if not r["is_valid"])
            }
        }
        
    except Exception as e:
        logger.error("Construction sequence validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Sequence validation failed: {str(e)}"
        )

@router.post(
    "/execute-sequence", 
    summary="Execute Construction Sequence",
    description="Execute a construction sequence step by step"
)
async def execute_construction_sequence(
    sequence: ConstructionSequence,
    initial_construction_space: ConstructionSpace,
    rust_service: RustGeometryService = Depends(get_rust_service)
):
    """Execute a construction sequence step by step."""
    try:
        current_space = initial_construction_space.copy(deep=True)
        execution_results = []
        
        for i, step in enumerate(sequence.steps):
            try:
                # Execute the step based on its type
                result = await _execute_construction_step(step, current_space, rust_service)
                
                execution_results.append({
                    "step_number": i + 1,
                    "step": step,
                    "success": True,
                    "result": result,
                    "message": f"Step {i + 1} executed successfully"
                })
                
                # Update construction space with result
                if "updated_space" in result:
                    current_space = result["updated_space"]
                    
            except Exception as step_error:
                execution_results.append({
                    "step_number": i + 1,
                    "step": step,
                    "success": False,
                    "error": str(step_error),
                    "message": f"Step {i + 1} failed: {str(step_error)}"
                })
                break  # Stop on first failure
        
        success_count = sum(1 for r in execution_results if r["success"])
        
        logger.info(
            "Construction sequence execution",
            sequence_name=sequence.name,
            total_steps=len(sequence.steps),
            successful_steps=success_count,
            overall_success=success_count == len(sequence.steps)
        )
        
        return {
            "sequence": sequence,
            "final_construction_space": current_space,
            "execution_results": execution_results,
            "summary": {
                "total_steps": len(sequence.steps),
                "successful_steps": success_count,
                "failed_steps": len(execution_results) - success_count,
                "overall_success": success_count == len(sequence.steps)
            }
        }
        
    except Exception as e:
        logger.error("Construction sequence execution failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sequence execution failed: {str(e)}"
        )

@router.get(
    "/templates",
    summary="Get Construction Templates",
    description="Get predefined construction templates for common geometric constructions"
)
async def get_construction_templates():
    """Get predefined construction templates."""
    templates = [
        {
            "name": "Equilateral Triangle",
            "description": "Construct an equilateral triangle on a given line segment",
            "difficulty": "beginner",
            "theorem": "Euclid's Proposition I.1",
            "steps": [
                {
                    "step_number": 1,
                    "step_type": "given_points",
                    "description": "Given two points A and B",
                    "dependencies": [],
                    "created_objects": ["point_A", "point_B"]
                },
                {
                    "step_number": 2, 
                    "step_type": "construct_circle",
                    "description": "Construct circle with center A and radius AB",
                    "dependencies": ["point_A", "point_B"],
                    "created_objects": ["circle_A"]
                },
                {
                    "step_number": 3,
                    "step_type": "construct_circle", 
                    "description": "Construct circle with center B and radius BA",
                    "dependencies": ["point_A", "point_B"],
                    "created_objects": ["circle_B"]
                },
                {
                    "step_number": 4,
                    "step_type": "find_intersections",
                    "description": "Find intersection of the two circles",
                    "dependencies": ["circle_A", "circle_B"],
                    "created_objects": ["point_C"]
                },
                {
                    "step_number": 5,
                    "step_type": "construct_line",
                    "description": "Construct line AC",
                    "dependencies": ["point_A", "point_C"],
                    "created_objects": ["line_AC"]
                },
                {
                    "step_number": 6,
                    "step_type": "construct_line",
                    "description": "Construct line BC", 
                    "dependencies": ["point_B", "point_C"],
                    "created_objects": ["line_BC"]
                }
            ]
        },
        {
            "name": "Perpendicular Bisector",
            "description": "Construct the perpendicular bisector of a line segment",
            "difficulty": "beginner",
            "theorem": "Standard construction",
            "steps": [
                {
                    "step_number": 1,
                    "step_type": "given_points",
                    "description": "Given two points A and B",
                    "dependencies": [],
                    "created_objects": ["point_A", "point_B"]
                },
                {
                    "step_number": 2,
                    "step_type": "construct_circle",
                    "description": "Construct circle with center A and radius greater than AB/2",
                    "dependencies": ["point_A", "point_B"],
                    "created_objects": ["circle_A"]
                },
                {
                    "step_number": 3,
                    "step_type": "construct_circle",
                    "description": "Construct circle with center B and same radius",
                    "dependencies": ["point_A", "point_B"],
                    "created_objects": ["circle_B"]
                },
                {
                    "step_number": 4,
                    "step_type": "find_intersections",
                    "description": "Find intersections of the two circles",
                    "dependencies": ["circle_A", "circle_B"],
                    "created_objects": ["point_C", "point_D"]
                },
                {
                    "step_number": 5,
                    "step_type": "construct_line",
                    "description": "Construct line through the intersections",
                    "dependencies": ["point_C", "point_D"],
                    "created_objects": ["line_CD"]
                }
            ]
        }
    ]
    
    return {
        "templates": templates,
        "count": len(templates)
    }

def _get_validation_suggestions(step: ConstructionStep, construction_space: ConstructionSpace) -> List[str]:
    """Get suggestions for fixing invalid construction steps."""
    suggestions = []
    
    # Check if dependencies exist
    for dep_id in step.dependencies:
        if (dep_id not in construction_space.points and 
            dep_id not in construction_space.lines and 
            dep_id not in construction_space.circles):
            suggestions.append(f"Required object '{dep_id}' does not exist in construction space")
    
    # Step-type specific suggestions
    if step.step_type == "construct_line":
        if len(step.dependencies) != 2:
            suggestions.append("Line construction requires exactly 2 point dependencies")
        elif step.dependencies[0] == step.dependencies[1]:
            suggestions.append("Cannot construct line with identical points")
            
    elif step.step_type == "construct_circle":
        if len(step.dependencies) != 2:
            suggestions.append("Circle construction requires exactly 2 point dependencies (center and radius point)")
        elif step.dependencies[0] == step.dependencies[1]:
            suggestions.append("Center and radius point cannot be the same")
    
    return suggestions

async def _execute_construction_step(
    step: ConstructionStep, 
    construction_space: ConstructionSpace,
    rust_service: RustGeometryService
) -> Dict[str, Any]:
    """Execute a single construction step."""
    
    if step.step_type == "add_point":
        # Extract coordinates from metadata
        x = step.metadata.get("x", 0.0)
        y = step.metadata.get("y", 0.0)
        label = step.metadata.get("label")
        
        point_id, updated_space = await rust_service.add_point(
            construction_space, x, y, label
        )
        
        return {
            "created_id": point_id,
            "updated_space": updated_space,
            "type": "point"
        }
        
    elif step.step_type == "construct_line":
        if len(step.dependencies) != 2:
            raise ConstructionValidationError("Line requires exactly 2 points")
            
        line_id, updated_space = await rust_service.construct_line(
            construction_space,
            step.dependencies[0],
            step.dependencies[1],
            step.metadata.get("label")
        )
        
        return {
            "created_id": line_id,
            "updated_space": updated_space,
            "type": "line"
        }
        
    elif step.step_type == "construct_circle":
        if len(step.dependencies) != 2:
            raise ConstructionValidationError("Circle requires exactly 2 points")
            
        circle_id, updated_space = await rust_service.construct_circle(
            construction_space,
            step.dependencies[0],
            step.dependencies[1], 
            step.metadata.get("label")
        )
        
        return {
            "created_id": circle_id,
            "updated_space": updated_space,
            "type": "circle"
        }
        
    elif step.step_type == "find_intersections":
        if len(step.dependencies) != 2:
            raise ConstructionValidationError("Intersection requires exactly 2 geometric objects")
            
        intersections, updated_space = await rust_service.find_intersections(
            construction_space,
            step.dependencies[0],
            step.dependencies[1]
        )
        
        return {
            "intersections": [point.dict() for point in intersections],
            "updated_space": updated_space,
            "type": "intersections"
        }
        
    else:
        raise ConstructionValidationError(f"Unknown step type: {step.step_type}")