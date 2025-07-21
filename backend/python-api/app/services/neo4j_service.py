"""
Neo4j Graph Database Service

Provides high-level interface for interacting with the Neo4j graph database
for storing and querying geometric relationships, constructions, and proofs.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import json

from neo4j import AsyncGraphDatabase, AsyncSession, Record
from neo4j.exceptions import ServiceUnavailable, TransientError
import structlog

from app.core.config import get_settings
from app.models.graph import (
    GraphNode, GraphRelationship, GraphQuery, GraphResult,
    GeometricPoint, GeometricLine, GeometricCircle, Construction,
    Player, Element, Theorem, NodeType, RelationshipType,
    CypherQueries, GRAPH_SCHEMA
)

logger = structlog.get_logger()
settings = get_settings()


class Neo4jService:
    """Service for Neo4j graph database operations."""
    
    def __init__(self):
        self.driver = None
        self.uri = settings.neo4j_uri or "bolt://localhost:7687"
        self.user = settings.neo4j_user or "neo4j"
        self.password = settings.neo4j_password or "password"
        self.database = settings.neo4j_database or "neo4j"
        self.connection_pool_size = 50
        self.max_connection_lifetime = 3600  # 1 hour
        
    async def connect(self) -> bool:
        """Initialize connection to Neo4j database."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=self.connection_pool_size,
                max_connection_lifetime=self.max_connection_lifetime,
                encrypted=False  # Use True in production with certificates
            )
            
            # Test connection
            await self.driver.verify_connectivity()
            logger.info("Neo4j connection established", uri=self.uri, database=self.database)
            
            # Initialize schema
            await self._initialize_schema()
            
            return True
            
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e), uri=self.uri)
            return False
    
    async def disconnect(self):
        """Close connection to Neo4j database."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Neo4j database health."""
        try:
            if not self.driver:
                return {"status": "disconnected", "error": "No driver initialized"}
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 as health_check")
                record = await result.single()
                
                if record and record["health_check"] == 1:
                    # Get database info
                    db_info = await session.run(
                        "CALL dbms.components() YIELD name, versions, edition"
                    )
                    components = [dict(record) async for record in db_info]
                    
                    return {
                        "status": "healthy",
                        "database": self.database,
                        "components": components,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {"status": "unhealthy", "error": "Health check query failed"}
                    
        except Exception as e:
            logger.error("Neo4j health check failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}
    
    async def _initialize_schema(self):
        """Initialize database schema with constraints and indexes."""
        try:
            async with self.driver.session(database=self.database) as session:
                # Create constraints
                for constraint_query in GRAPH_SCHEMA["constraints"]:
                    try:
                        await session.run(constraint_query)
                        logger.debug("Created constraint", query=constraint_query)
                    except Exception as e:
                        logger.warning("Constraint creation failed", query=constraint_query, error=str(e))
                
                # Create indexes
                for index_query in GRAPH_SCHEMA["indexes"]:
                    try:
                        await session.run(index_query)
                        logger.debug("Created index", query=index_query)
                    except Exception as e:
                        logger.warning("Index creation failed", query=index_query, error=str(e))
                        
                logger.info("Neo4j schema initialization completed")
                
        except Exception as e:
            logger.error("Schema initialization failed", error=str(e))
    
    async def execute_query(self, query: GraphQuery) -> GraphResult:
        """Execute a Cypher query and return results."""
        start_time = datetime.now()
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query.cypher, query.parameters)
                
                records = []
                async for record in result:
                    # Convert Neo4j record to dictionary
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Handle Neo4j specific types
                        if hasattr(value, '__dict__'):
                            record_dict[key] = dict(value)
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                
                summary = await result.consume()
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(
                    "Neo4j query executed",
                    query_type=query.cypher.split()[0],
                    records_returned=len(records),
                    execution_time=execution_time
                )
                
                return GraphResult(
                    records=records,
                    summary={
                        "query_type": summary.query_type,
                        "counters": dict(summary.counters) if hasattr(summary, 'counters') else {},
                        "result_available_after": summary.result_available_after,
                        "result_consumed_after": summary.result_consumed_after
                    },
                    execution_time=execution_time
                )
                
        except Exception as e:
            logger.error("Neo4j query execution failed", query=query.cypher, error=str(e))
            raise
    
    # Geometric object operations
    
    async def create_point(self, point: GeometricPoint) -> GraphResult:
        """Create a point node in the graph."""
        query = GraphQuery(
            cypher=CypherQueries.CREATE_POINT,
            parameters={
                "node_id": point.node_id,
                "x": point.x,
                "y": point.y,
                "label": point.label,
                "is_constructed": point.is_constructed
            }
        )
        return await self.execute_query(query)
    
    async def create_line(self, line: GeometricLine) -> GraphResult:
        """Create a line node in the graph."""
        query = GraphQuery(
            cypher=CypherQueries.CREATE_LINE,
            parameters={
                "node_id": line.node_id,
                "point1_id": line.point1_id,
                "point2_id": line.point2_id,
                "label": line.label,
                "is_segment": line.is_segment
            }
        )
        result = await self.execute_query(query)
        
        # Create relationships with the points
        await self._create_point_line_relationships(line.node_id, line.point1_id, line.point2_id)
        
        return result
    
    async def create_circle(self, circle: GeometricCircle) -> GraphResult:
        """Create a circle node in the graph."""
        query = GraphQuery(
            cypher=CypherQueries.CREATE_CIRCLE,
            parameters={
                "node_id": circle.node_id,
                "center_id": circle.center_id,
                "radius": circle.radius,
                "radius_point_id": circle.radius_point_id,
                "label": circle.label
            }
        )
        result = await self.execute_query(query)
        
        # Create relationship with center point
        await self._create_circle_center_relationship(circle.node_id, circle.center_id)
        
        return result
    
    async def _create_point_line_relationships(self, line_id: str, point1_id: str, point2_id: str):
        """Create relationships between line and its defining points."""
        for point_id in [point1_id, point2_id]:
            query = GraphQuery(
                cypher=CypherQueries.CREATE_POINT_ON_LINE,
                parameters={"point_id": point_id, "line_id": line_id}
            )
            await self.execute_query(query)
    
    async def _create_circle_center_relationship(self, circle_id: str, center_id: str):
        """Create relationship between circle and its center point."""
        query = GraphQuery(
            cypher="""
                MATCH (c:Circle {node_id: $circle_id}), (p:Point {node_id: $center_id})
                CREATE (c)-[:HAS_CENTER {created_at: datetime()}]->(p)
                CREATE (p)-[:CENTER_OF {created_at: datetime()}]->(c)
            """,
            parameters={"circle_id": circle_id, "center_id": center_id}
        )
        await self.execute_query(query)
    
    async def find_intersections(self, obj1_id: str, obj2_id: str) -> List[Dict[str, Any]]:
        """Find intersection points between two geometric objects."""
        query = GraphQuery(
            cypher=CypherQueries.FIND_INTERSECTIONS,
            parameters={"obj1_id": obj1_id}
        )
        result = await self.execute_query(query)
        
        intersections = []
        for record in result.records:
            if record["other_object_id"] == obj2_id:
                intersections.extend(record.get("intersection_points", []))
        
        return intersections
    
    async def create_intersection_relationship(self, obj1_id: str, obj2_id: str, intersection_points: List[Dict]):
        """Create intersection relationship between two objects."""
        query = GraphQuery(
            cypher=CypherQueries.CREATE_INTERSECTION,
            parameters={
                "obj1_id": obj1_id,
                "obj2_id": obj2_id,
                "intersection_points": intersection_points
            }
        )
        await self.execute_query(query)
    
    # Construction operations
    
    async def create_construction(self, construction: Construction) -> GraphResult:
        """Create a construction node in the graph."""
        query = GraphQuery(
            cypher="""
                CREATE (c:Construction {
                    node_id: $node_id,
                    name: $name,
                    description: $description,
                    target_theorem: $target_theorem,
                    player_id: $player_id,
                    is_valid: $is_valid,
                    difficulty_level: $difficulty_level,
                    steps_count: $steps_count,
                    created_at: datetime()
                })
                RETURN c
            """,
            parameters={
                "node_id": construction.node_id,
                "name": construction.name,
                "description": construction.description,
                "target_theorem": construction.target_theorem,
                "player_id": construction.player_id,
                "is_valid": construction.is_valid,
                "difficulty_level": construction.difficulty_level,
                "steps_count": construction.steps_count
            }
        )
        return await self.execute_query(query)
    
    async def link_construction_objects(self, construction_id: str, object_ids: List[str], relationship_type: str):
        """Link construction with geometric objects it creates or depends on."""
        for object_id in object_ids:
            query = GraphQuery(
                cypher=f"""
                    MATCH (c:Construction {{node_id: $construction_id}}), (obj:GeometricObject {{node_id: $object_id}})
                    CREATE (obj)-[:{relationship_type} {{created_at: datetime()}}]->(c)
                """,
                parameters={"construction_id": construction_id, "object_id": object_id}
            )
            await self.execute_query(query)
    
    async def get_construction_objects(self, construction_id: str) -> List[Dict[str, Any]]:
        """Get all objects created by or used in a construction."""
        query = GraphQuery(
            cypher=CypherQueries.FIND_OBJECTS_IN_CONSTRUCTION,
            parameters={"construction_id": construction_id}
        )
        result = await self.execute_query(query)
        return result.records
    
    # Player and collection operations
    
    async def create_player(self, player: Player) -> GraphResult:
        """Create a player node in the graph."""
        query = GraphQuery(
            cypher="""
                CREATE (p:Player {
                    node_id: $node_id,
                    username: $username,
                    level: $level,
                    experience_points: $experience_points,
                    constructions_completed: $constructions_completed,
                    elements_unlocked: $elements_unlocked,
                    created_at: datetime()
                })
                RETURN p
            """,
            parameters={
                "node_id": player.node_id,
                "username": player.username,
                "level": player.level,
                "experience_points": player.experience_points,
                "constructions_completed": player.constructions_completed,
                "elements_unlocked": player.elements_unlocked
            }
        )
        return await self.execute_query(query)
    
    async def get_player_elements(self, player_id: str) -> List[Dict[str, Any]]:
        """Get all elements owned by a player."""
        query = GraphQuery(
            cypher=CypherQueries.GET_PLAYER_ELEMENTS,
            parameters={"player_id": player_id}
        )
        result = await self.execute_query(query)
        return result.records
    
    async def unlock_element(self, player_id: str, element_id: str) -> GraphResult:
        """Create ownership relationship between player and element."""
        query = GraphQuery(
            cypher="""
                MATCH (p:Player {node_id: $player_id}), (e:Element {node_id: $element_id})
                CREATE (p)-[:OWNS {unlocked_at: datetime()}]->(e)
                SET e.discovery_count = e.discovery_count + 1
                SET p.elements_unlocked = p.elements_unlocked + 1
                RETURN p, e
            """,
            parameters={"player_id": player_id, "element_id": element_id}
        )
        return await self.execute_query(query)
    
    async def find_unlockable_elements(self, player_id: str) -> List[Dict[str, Any]]:
        """Find elements that a player can unlock based on their current collection."""
        query = GraphQuery(
            cypher=CypherQueries.FIND_UNLOCKABLE_ELEMENTS,
            parameters={"player_id": player_id}
        )
        result = await self.execute_query(query)
        return result.records
    
    # Advanced graph analysis
    
    async def find_similar_constructions(self, construction_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find constructions similar to the given one based on structure."""
        query = GraphQuery(
            cypher="""
                MATCH (c1:Construction {node_id: $construction_id})-[:CREATED_BY|DEPENDS_ON]-(obj1:GeometricObject)
                WITH c1, collect(labels(obj1)) as c1_types, count(obj1) as c1_count
                
                MATCH (c2:Construction)-[:CREATED_BY|DEPENDS_ON]-(obj2:GeometricObject)
                WHERE c2 <> c1
                WITH c1, c1_types, c1_count, c2, collect(labels(obj2)) as c2_types, count(obj2) as c2_count
                
                WITH c1, c2, 
                     size(apoc.coll.intersection(c1_types, c2_types)) as common_types,
                     abs(c1_count - c2_count) as count_diff
                WHERE common_types > 0
                
                RETURN c2.node_id as construction_id, 
                       c2.name as name,
                       c2.description as description,
                       common_types,
                       count_diff,
                       (common_types * 1.0 / (size(c1_types) + size(c2_types) - common_types)) as similarity
                ORDER BY similarity DESC, count_diff ASC
                LIMIT $limit
            """,
            parameters={"construction_id": construction_id, "limit": limit}
        )
        result = await self.execute_query(query)
        return result.records
    
    async def analyze_construction_patterns(self, player_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze patterns in constructions to identify common approaches."""
        base_query = """
            MATCH (c:Construction)
            {player_filter}
            MATCH (c)-[:CREATED_BY|DEPENDS_ON]-(obj:GeometricObject)
            
            WITH c, collect(labels(obj)[0]) as object_types, count(obj) as object_count
            
            RETURN 
                object_types,
                count(*) as frequency,
                avg(object_count) as avg_objects,
                collect(c.name)[0..5] as example_constructions
            ORDER BY frequency DESC
            LIMIT 20
        """
        
        player_filter = "WHERE c.player_id = $player_id" if player_id else ""
        cypher = base_query.format(player_filter=player_filter)
        
        query = GraphQuery(
            cypher=cypher,
            parameters={"player_id": player_id} if player_id else {}
        )
        result = await self.execute_query(query)
        
        return {
            "patterns": result.records,
            "total_constructions": len(result.records),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def get_construction_graph(self, construction_id: str) -> Dict[str, Any]:
        """Get the complete graph structure for a construction."""
        query = GraphQuery(
            cypher="""
                MATCH (c:Construction {node_id: $construction_id})
                OPTIONAL MATCH (c)-[r1:CREATED_BY|DEPENDS_ON]-(obj:GeometricObject)
                OPTIONAL MATCH (obj)-[r2:LIES_ON|CONTAINS|INTERSECTS]-(related:GeometricObject)
                
                RETURN c,
                       collect(DISTINCT obj) as objects,
                       collect(DISTINCT r1) as construction_relationships,
                       collect(DISTINCT r2) as geometric_relationships,
                       collect(DISTINCT related) as related_objects
            """,
            parameters={"construction_id": construction_id}
        )
        result = await self.execute_query(query)
        
        if result.records:
            record = result.records[0]
            return {
                "construction": record.get("c", {}),
                "objects": record.get("objects", []),
                "construction_relationships": record.get("construction_relationships", []),
                "geometric_relationships": record.get("geometric_relationships", []),
                "related_objects": record.get("related_objects", [])
            }
        
        return {}


# Global Neo4j service instance
neo4j_service = Neo4jService()


async def get_neo4j_service() -> Neo4jService:
    """Get the Neo4j service instance."""
    return neo4j_service


async def init_neo4j():
    """Initialize Neo4j service."""
    await neo4j_service.connect()


async def close_neo4j():
    """Close Neo4j service."""
    await neo4j_service.disconnect()