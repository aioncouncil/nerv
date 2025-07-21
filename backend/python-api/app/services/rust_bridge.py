"""
Rust Bridge Service

Provides Python interface to the Rust geometry engine through
ctypes bindings or subprocess calls, depending on availability.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

import structlog
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.exceptions import GeometryEngineError

logger = structlog.get_logger()
settings = get_settings()


class Point(BaseModel):
    """Geometric point representation."""
    id: str
    x: float
    y: float
    label: Optional[str] = None
    is_constructed: bool = False
    dependencies: List[str] = []


class Line(BaseModel):
    """Geometric line representation."""
    id: str
    point1_id: str
    point2_id: str
    label: Optional[str] = None
    dependencies: List[str] = []


class Circle(BaseModel):
    """Geometric circle representation."""
    id: str
    center_id: str
    radius_point_id: str
    label: Optional[str] = None
    dependencies: List[str] = []


class ConstructionSpace(BaseModel):
    """Complete construction space state."""
    points: Dict[str, Point] = {}
    lines: Dict[str, Line] = {}
    circles: Dict[str, Circle] = {}
    history: List[Dict[str, Any]] = []


class RustGeometryService:
    """Service for interfacing with the Rust geometry engine."""
    
    def __init__(self):
        self.rust_binary_path = self._find_rust_binary()
        self._process_pool: Optional[asyncio.subprocess.Process] = None
        
    def _find_rust_binary(self) -> Optional[Path]:
        """Find the Rust geometry engine binary."""
        
        # Check configured path first
        if settings.rust_lib_path:
            rust_path = Path(settings.rust_lib_path)
            if rust_path.exists():
                return rust_path
                
        # Look for cargo build output
        possible_paths = [
            Path("../rust-core/target/release/nerv-geometry"),
            Path("../rust-core/target/debug/nerv-geometry"), 
            Path("./target/release/nerv-geometry"),
            Path("./target/debug/nerv-geometry"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.resolve()
                
        logger.warning("Rust geometry binary not found, using fallback mode")
        return None
    
    async def health_check(self) -> bool:
        """Check if the Rust geometry engine is available and responsive."""
        if not self.rust_binary_path:
            # Fallback mode - return basic health
            return True
            
        try:
            # Try to execute a simple geometry operation
            result = await self._execute_rust_command({
                "command": "health_check"
            })
            return result.get("status") == "healthy"
        except Exception as e:
            logger.error("Rust engine health check failed", error=str(e))
            return False
    
    async def create_construction_space(self) -> ConstructionSpace:
        """Create a new empty construction space."""
        if not self.rust_binary_path:
            return ConstructionSpace()
            
        try:
            result = await self._execute_rust_command({
                "command": "create_construction_space"
            })
            return ConstructionSpace(**result["construction_space"])
        except Exception as e:
            logger.error("Failed to create construction space", error=str(e))
            return ConstructionSpace()
    
    async def add_point(
        self, 
        construction_space: ConstructionSpace,
        x: float, 
        y: float, 
        label: Optional[str] = None
    ) -> tuple[str, ConstructionSpace]:
        """Add a point to the construction space."""
        
        if not self.rust_binary_path:
            # Fallback: simple Python implementation
            import uuid
            point_id = str(uuid.uuid4())
            point = Point(id=point_id, x=x, y=y, label=label)
            construction_space.points[point_id] = point
            return point_id, construction_space
            
        try:
            result = await self._execute_rust_command({
                "command": "add_point",
                "construction_space": construction_space.dict(),
                "x": x,
                "y": y,
                "label": label
            })
            
            updated_space = ConstructionSpace(**result["construction_space"])
            return result["point_id"], updated_space
            
        except Exception as e:
            raise GeometryEngineError(f"Failed to add point: {str(e)}")
    
    async def construct_line(
        self,
        construction_space: ConstructionSpace,
        point1_id: str,
        point2_id: str,
        label: Optional[str] = None
    ) -> tuple[str, ConstructionSpace]:
        """Construct a line through two points."""
        
        # Validate points exist
        if point1_id not in construction_space.points:
            raise GeometryEngineError(f"Point not found: {point1_id}")
        if point2_id not in construction_space.points:
            raise GeometryEngineError(f"Point not found: {point2_id}")
        if point1_id == point2_id:
            raise GeometryEngineError("Cannot create line with identical points")
            
        if not self.rust_binary_path:
            # Fallback: simple Python implementation
            import uuid
            line_id = str(uuid.uuid4())
            line = Line(
                id=line_id, 
                point1_id=point1_id,
                point2_id=point2_id,
                label=label,
                dependencies=[point1_id, point2_id]
            )
            construction_space.lines[line_id] = line
            return line_id, construction_space
            
        try:
            result = await self._execute_rust_command({
                "command": "construct_line",
                "construction_space": construction_space.dict(),
                "point1_id": point1_id,
                "point2_id": point2_id,
                "label": label
            })
            
            updated_space = ConstructionSpace(**result["construction_space"])
            return result["line_id"], updated_space
            
        except Exception as e:
            raise GeometryEngineError(f"Failed to construct line: {str(e)}")
    
    async def construct_circle(
        self,
        construction_space: ConstructionSpace,
        center_id: str,
        radius_point_id: str,
        label: Optional[str] = None
    ) -> tuple[str, ConstructionSpace]:
        """Construct a circle with center and radius point."""
        
        # Validate points exist
        if center_id not in construction_space.points:
            raise GeometryEngineError(f"Point not found: {center_id}")
        if radius_point_id not in construction_space.points:
            raise GeometryEngineError(f"Point not found: {radius_point_id}")
        if center_id == radius_point_id:
            raise GeometryEngineError("Center and radius point cannot be the same")
            
        if not self.rust_binary_path:
            # Fallback: simple Python implementation
            import uuid
            circle_id = str(uuid.uuid4())
            circle = Circle(
                id=circle_id,
                center_id=center_id,
                radius_point_id=radius_point_id,
                label=label,
                dependencies=[center_id, radius_point_id]
            )
            construction_space.circles[circle_id] = circle
            return circle_id, construction_space
            
        try:
            result = await self._execute_rust_command({
                "command": "construct_circle",
                "construction_space": construction_space.dict(),
                "center_id": center_id,
                "radius_point_id": radius_point_id,
                "label": label
            })
            
            updated_space = ConstructionSpace(**result["construction_space"])
            return result["circle_id"], updated_space
            
        except Exception as e:
            raise GeometryEngineError(f"Failed to construct circle: {str(e)}")
    
    async def find_intersections(
        self,
        construction_space: ConstructionSpace,
        obj1_id: str,
        obj2_id: str
    ) -> tuple[List[Point], ConstructionSpace]:
        """Find intersection points between two geometric objects."""
        
        if not self.rust_binary_path:
            # Fallback: return empty intersections
            return [], construction_space
            
        try:
            result = await self._execute_rust_command({
                "command": "find_intersections",
                "construction_space": construction_space.dict(),
                "obj1_id": obj1_id,
                "obj2_id": obj2_id
            })
            
            intersections = [Point(**point_data) for point_data in result["intersections"]]
            updated_space = ConstructionSpace(**result["construction_space"])
            return intersections, updated_space
            
        except Exception as e:
            raise GeometryEngineError(f"Failed to find intersections: {str(e)}")
    
    async def validate_construction(
        self,
        construction_space: ConstructionSpace,
        step: Dict[str, Any]
    ) -> bool:
        """Validate if a construction step is valid."""
        
        if not self.rust_binary_path:
            # Fallback: basic validation
            step_type = step.get("step_type")
            if step_type == "add_point":
                return True
            elif step_type in ["construct_line", "construct_circle"]:
                # Check if referenced points exist
                dependencies = step.get("dependencies", [])
                return all(dep in construction_space.points for dep in dependencies)
            return True
            
        try:
            result = await self._execute_rust_command({
                "command": "validate_construction",
                "construction_space": construction_space.dict(),
                "step": step
            })
            
            return result["is_valid"]
            
        except Exception as e:
            raise GeometryEngineError(f"Failed to validate construction: {str(e)}")
    
    async def _execute_rust_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command using the Rust geometry engine."""
        
        if not self.rust_binary_path:
            raise GeometryEngineError("Rust geometry engine not available")
            
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                str(self.rust_binary_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send command as JSON
            command_json = json.dumps(command).encode()
            stdout, stderr = await process.communicate(input=command_json)
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise GeometryEngineError(f"Rust command failed: {error_msg}")
                
            # Parse result
            result_text = stdout.decode().strip()
            if not result_text:
                raise GeometryEngineError("Empty response from Rust engine")
                
            return json.loads(result_text)
            
        except json.JSONDecodeError as e:
            raise GeometryEngineError(f"Failed to parse Rust engine response: {str(e)}")
        except Exception as e:
            raise GeometryEngineError(f"Failed to execute Rust command: {str(e)}")
    
    async def close(self):
        """Clean up resources."""
        if self._process_pool:
            self._process_pool.terminate()
            await self._process_pool.wait()
            self._process_pool = None


# Global service instance
_rust_service: Optional[RustGeometryService] = None

def get_rust_service() -> RustGeometryService:
    """Get the global Rust geometry service instance."""
    global _rust_service
    if _rust_service is None:
        _rust_service = RustGeometryService()
    return _rust_service