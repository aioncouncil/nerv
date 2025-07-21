"""
Neo4j Graph Database Models

Defines the graph structure for storing geometric relationships, construction
history, and mathematical proofs in a Neo4j graph database.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


class NodeType(str, Enum):
    """Types of nodes in the geometric graph."""
    POINT = "Point"
    LINE = "Line" 
    CIRCLE = "Circle"
    POLYGON = "Polygon"
    CONSTRUCTION = "Construction"
    THEOREM = "Theorem"
    PROOF = "Proof"
    PLAYER = "Player"
    ELEMENT = "Element"


class RelationshipType(str, Enum):
    """Types of relationships between graph nodes."""
    # Geometric relationships
    LIES_ON = "LIES_ON"           # Point lies on Line/Circle
    CONTAINS = "CONTAINS"         # Line/Circle contains Point
    INTERSECTS = "INTERSECTS"     # Objects intersect
    PARALLEL_TO = "PARALLEL_TO"   # Lines are parallel
    PERPENDICULAR_TO = "PERPENDICULAR_TO"  # Lines are perpendicular
    TANGENT_TO = "TANGENT_TO"     # Line tangent to Circle
    CONCENTRIC = "CONCENTRIC"     # Circles share center
    
    # Construction relationships
    CREATED_BY = "CREATED_BY"     # Object created by Construction
    DEPENDS_ON = "DEPENDS_ON"     # Construction depends on objects
    PART_OF = "PART_OF"           # Step part of Construction
    PRECEDES = "PRECEDES"         # Construction step order
    
    # Proof relationships
    PROVES = "PROVES"             # Proof proves Theorem
    USES = "USES"                 # Proof uses Construction/Theorem
    IMPLIES = "IMPLIES"           # Theorem implies another
    
    # Collection relationships
    OWNS = "OWNS"                 # Player owns Element
    UNLOCKED_BY = "UNLOCKED_BY"   # Element unlocked by Construction
    REQUIRES = "REQUIRES"         # Element requires other elements


class GraphNode(BaseModel):
    """Base class for all graph nodes."""
    node_id: str = Field(..., description="Unique node identifier")
    node_type: NodeType
    properties: Dict[str, Any] = Field(default={}, description="Node properties")
    created_at: datetime = Field(default_factory=datetime.now)
    labels: List[str] = Field(default=[], description="Additional node labels")


class GeometricPoint(GraphNode):
    """Point node in the geometric graph."""
    node_type: NodeType = NodeType.POINT
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    label: Optional[str] = Field(None, description="Point label (A, B, C, etc.)")
    is_constructed: bool = Field(False, description="Created by construction vs given")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update({
            "x": self.x,
            "y": self.y,
            "label": self.label,
            "is_constructed": self.is_constructed
        })


class GeometricLine(GraphNode):
    """Line node in the geometric graph."""
    node_type: NodeType = NodeType.LINE
    point1_id: str = Field(..., description="First point ID")
    point2_id: str = Field(..., description="Second point ID")
    label: Optional[str] = Field(None, description="Line label")
    is_ray: bool = Field(False, description="Is this a ray vs full line")
    is_segment: bool = Field(True, description="Is this a segment vs infinite line")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update({
            "point1_id": self.point1_id,
            "point2_id": self.point2_id,
            "label": self.label,
            "is_ray": self.is_ray,
            "is_segment": self.is_segment
        })


class GeometricCircle(GraphNode):
    """Circle node in the geometric graph."""
    node_type: NodeType = NodeType.CIRCLE
    center_id: str = Field(..., description="Center point ID")
    radius: float = Field(..., description="Circle radius")
    radius_point_id: Optional[str] = Field(None, description="Point defining radius")
    label: Optional[str] = Field(None, description="Circle label")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update({
            "center_id": self.center_id,
            "radius": self.radius,
            "radius_point_id": self.radius_point_id,
            "label": self.label
        })


class Construction(GraphNode):
    """Construction process node."""
    node_type: NodeType = NodeType.CONSTRUCTION
    name: str = Field(..., description="Construction name")
    description: str = Field(..., description="What is being constructed")
    target_theorem: Optional[str] = Field(None, description="Theorem being demonstrated")
    player_id: str = Field(..., description="Player who created construction")
    is_valid: bool = Field(True, description="Is construction geometrically valid")
    difficulty_level: str = Field("beginner", description="Construction difficulty")
    steps_count: int = Field(0, description="Number of construction steps")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update({
            "name": self.name,
            "description": self.description,
            "target_theorem": self.target_theorem,
            "player_id": self.player_id,
            "is_valid": self.is_valid,
            "difficulty_level": self.difficulty_level,
            "steps_count": self.steps_count
        })


class Theorem(GraphNode):
    """Mathematical theorem node."""
    node_type: NodeType = NodeType.THEOREM
    name: str = Field(..., description="Theorem name")
    statement: str = Field(..., description="Theorem statement")
    category: str = Field(..., description="Theorem category (geometry, algebra, etc.)")
    difficulty: str = Field("intermediate", description="Theorem difficulty")
    historical_note: Optional[str] = Field(None, description="Historical context")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update({
            "name": self.name,
            "statement": self.statement,
            "category": self.category,
            "difficulty": self.difficulty,
            "historical_note": self.historical_note
        })


class Player(GraphNode):
    """Player/user node."""
    node_type: NodeType = NodeType.PLAYER
    username: str = Field(..., description="Player username")
    level: int = Field(1, description="Player level")
    experience_points: int = Field(0, description="Total XP")
    constructions_completed: int = Field(0, description="Number of constructions")
    elements_unlocked: int = Field(0, description="Number of elements unlocked")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update({
            "username": self.username,
            "level": self.level,
            "experience_points": self.experience_points,
            "constructions_completed": self.constructions_completed,
            "elements_unlocked": self.elements_unlocked
        })


class Element(GraphNode):
    """Collection element node."""
    node_type: NodeType = NodeType.ELEMENT
    name: str = Field(..., description="Element name")
    description: str = Field(..., description="Element description")
    category: str = Field(..., description="Element category")
    rarity: str = Field(..., description="Element rarity")
    unlock_requirements: List[str] = Field(default=[], description="Required elements")
    discovery_count: int = Field(0, description="Times discovered by players")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.properties.update({
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "rarity": self.rarity,
            "unlock_requirements": self.unlock_requirements,
            "discovery_count": self.discovery_count
        })


class GraphRelationship(BaseModel):
    """Relationship between graph nodes."""
    start_node_id: str = Field(..., description="Source node ID")
    end_node_id: str = Field(..., description="Target node ID")
    relationship_type: RelationshipType
    properties: Dict[str, Any] = Field(default={}, description="Relationship properties")
    created_at: datetime = Field(default_factory=datetime.now)
    strength: Optional[float] = Field(None, description="Relationship strength (0-1)")


class GraphQuery(BaseModel):
    """Query for graph database operations."""
    cypher: str = Field(..., description="Cypher query")
    parameters: Dict[str, Any] = Field(default={}, description="Query parameters")
    return_format: str = Field("records", description="Return format (records, graph, etc.)")


class GraphResult(BaseModel):
    """Result from graph database query."""
    records: List[Dict[str, Any]] = Field(default=[], description="Query result records")
    summary: Dict[str, Any] = Field(default={}, description="Query execution summary")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    execution_time: Optional[float] = Field(None, description="Query execution time in seconds")


# Predefined Cypher queries for common operations
class CypherQueries:
    """Collection of common Cypher queries for geometric operations."""
    
    # Node creation queries
    CREATE_POINT = """
        CREATE (p:Point:GeometricObject {
            node_id: $node_id,
            x: $x,
            y: $y,
            label: $label,
            is_constructed: $is_constructed,
            created_at: datetime()
        })
        RETURN p
    """
    
    CREATE_LINE = """
        CREATE (l:Line:GeometricObject {
            node_id: $node_id,
            point1_id: $point1_id,
            point2_id: $point2_id,
            label: $label,
            is_segment: $is_segment,
            created_at: datetime()
        })
        RETURN l
    """
    
    CREATE_CIRCLE = """
        CREATE (c:Circle:GeometricObject {
            node_id: $node_id,
            center_id: $center_id,
            radius: $radius,
            radius_point_id: $radius_point_id,
            label: $label,
            created_at: datetime()
        })
        RETURN c
    """
    
    # Relationship creation queries
    CREATE_POINT_ON_LINE = """
        MATCH (p:Point {node_id: $point_id}), (l:Line {node_id: $line_id})
        CREATE (p)-[:LIES_ON {created_at: datetime()}]->(l)
        CREATE (l)-[:CONTAINS {created_at: datetime()}]->(p)
    """
    
    CREATE_INTERSECTION = """
        MATCH (obj1:GeometricObject {node_id: $obj1_id}), (obj2:GeometricObject {node_id: $obj2_id})
        CREATE (obj1)-[:INTERSECTS {
            intersection_points: $intersection_points,
            created_at: datetime()
        }]->(obj2)
    """
    
    # Query geometric relationships
    FIND_POINTS_ON_LINE = """
        MATCH (p:Point)-[:LIES_ON]->(l:Line {node_id: $line_id})
        RETURN p.node_id as point_id, p.x as x, p.y as y, p.label as label
        ORDER BY p.created_at
    """
    
    FIND_INTERSECTIONS = """
        MATCH (obj1:GeometricObject {node_id: $obj1_id})-[r:INTERSECTS]-(obj2:GeometricObject)
        RETURN obj2.node_id as other_object_id, 
               r.intersection_points as intersection_points,
               labels(obj2) as object_types
    """
    
    # Construction queries
    FIND_CONSTRUCTION_DEPENDENCIES = """
        MATCH (c:Construction {node_id: $construction_id})-[:DEPENDS_ON]->(obj:GeometricObject)
        RETURN obj.node_id as object_id, labels(obj) as object_types, obj
        ORDER BY obj.created_at
    """
    
    FIND_OBJECTS_IN_CONSTRUCTION = """
        MATCH (obj:GeometricObject)-[:CREATED_BY]->(c:Construction {node_id: $construction_id})
        RETURN obj.node_id as object_id, labels(obj) as object_types, obj
        ORDER BY obj.created_at
    """
    
    # Player and collection queries
    GET_PLAYER_ELEMENTS = """
        MATCH (p:Player {node_id: $player_id})-[:OWNS]->(e:Element)
        RETURN e.node_id as element_id, e.name as name, e.rarity as rarity, e.category as category
        ORDER BY e.rarity, e.name
    """
    
    FIND_UNLOCKABLE_ELEMENTS = """
        MATCH (e:Element)
        WHERE NOT EXISTS {
            MATCH (p:Player {node_id: $player_id})-[:OWNS]->(e)
        }
        WITH e
        MATCH (p:Player {node_id: $player_id})-[:OWNS]->(req:Element)
        WHERE req.node_id IN e.unlock_requirements
        WITH e, count(req) as owned_requirements
        WHERE owned_requirements = size(e.unlock_requirements)
        RETURN e.node_id as element_id, e.name as name, e.rarity as rarity
        ORDER BY 
            CASE e.rarity 
                WHEN 'common' THEN 1 
                WHEN 'uncommon' THEN 2 
                WHEN 'rare' THEN 3 
                WHEN 'legendary' THEN 4 
            END, e.name
    """
    
    # Proof and theorem queries
    FIND_THEOREM_PROOFS = """
        MATCH (t:Theorem {node_id: $theorem_id})<-[:PROVES]-(proof:Proof)
        RETURN proof.node_id as proof_id, proof.method as method, proof.created_at as created_at
        ORDER BY proof.created_at DESC
    """
    
    FIND_RELATED_THEOREMS = """
        MATCH (t1:Theorem {node_id: $theorem_id})
        MATCH (t1)-[:IMPLIES*1..2]-(t2:Theorem)
        WHERE t1 <> t2
        RETURN t2.node_id as theorem_id, t2.name as name, t2.statement as statement
        ORDER BY t2.name
    """


# Graph database schema constraints and indexes
GRAPH_SCHEMA = {
    "constraints": [
        "CREATE CONSTRAINT point_id_unique IF NOT EXISTS FOR (p:Point) REQUIRE p.node_id IS UNIQUE",
        "CREATE CONSTRAINT line_id_unique IF NOT EXISTS FOR (l:Line) REQUIRE l.node_id IS UNIQUE", 
        "CREATE CONSTRAINT circle_id_unique IF NOT EXISTS FOR (c:Circle) REQUIRE c.node_id IS UNIQUE",
        "CREATE CONSTRAINT construction_id_unique IF NOT EXISTS FOR (c:Construction) REQUIRE c.node_id IS UNIQUE",
        "CREATE CONSTRAINT player_id_unique IF NOT EXISTS FOR (p:Player) REQUIRE p.node_id IS UNIQUE",
        "CREATE CONSTRAINT element_id_unique IF NOT EXISTS FOR (e:Element) REQUIRE e.node_id IS UNIQUE",
        "CREATE CONSTRAINT theorem_id_unique IF NOT EXISTS FOR (t:Theorem) REQUIRE t.node_id IS UNIQUE"
    ],
    "indexes": [
        "CREATE INDEX point_coordinates IF NOT EXISTS FOR (p:Point) ON (p.x, p.y)",
        "CREATE INDEX geometric_objects IF NOT EXISTS FOR (obj:GeometricObject) ON obj.created_at",
        "CREATE INDEX player_username IF NOT EXISTS FOR (p:Player) ON p.username",
        "CREATE INDEX element_rarity IF NOT EXISTS FOR (e:Element) ON e.rarity",
        "CREATE INDEX construction_player IF NOT EXISTS FOR (c:Construction) ON c.player_id",
        "CREATE INDEX theorem_category IF NOT EXISTS FOR (t:Theorem) ON t.category"
    ]
}