"""
Graph Database API endpoints for Neo4j geometric relationships.

Provides endpoints for creating, querying, and analyzing geometric
relationships stored in the Neo4j graph database.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import structlog

from app.services.neo4j_service import get_neo4j_service, Neo4jService
from app.models.graph import (
    GeometricPoint, GeometricLine, GeometricCircle, Construction,
    GraphQuery, GraphResult, NodeType, RelationshipType
)

logger = structlog.get_logger()
router = APIRouter()


class GraphNodeCreate(BaseModel):
    """Request to create a graph node."""
    node_type: NodeType
    properties: Dict[str, Any]
    labels: List[str] = Field(default=[])


class GraphRelationshipCreate(BaseModel):
    """Request to create a graph relationship."""
    start_node_id: str
    end_node_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = Field(default={})


class GraphAnalysisRequest(BaseModel):
    """Request for graph analysis."""
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Dict[str, Any] = Field(default={}, description="Analysis parameters")
    limit: int = Field(default=50, description="Maximum results to return")


@router.get(
    "/health",
    summary="Graph Database Health",
    description="Check Neo4j graph database connection and status"
)
async def graph_health_check(
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Check graph database health."""
    try:
        health = await neo4j_service.health_check()
        return health
    except Exception as e:
        logger.error("Graph health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Graph database health check failed: {str(e)}"
        )


@router.post(
    "/query",
    response_model=GraphResult,
    summary="Execute Graph Query",
    description="Execute a custom Cypher query against the graph database"
)
async def execute_graph_query(
    query: GraphQuery,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Execute a custom graph query."""
    try:
        # Security: Only allow read queries for safety
        if not query.cypher.strip().upper().startswith(('MATCH', 'RETURN', 'WITH', 'OPTIONAL')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only read queries (MATCH, RETURN, WITH, OPTIONAL) are allowed"
            )
        
        result = await neo4j_service.execute_query(query)
        logger.info(
            "Graph query executed",
            records_returned=len(result.records),
            execution_time=result.execution_time
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Graph query execution failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )


@router.post(
    "/points",
    summary="Create Graph Point",
    description="Create a geometric point in the graph database"
)
async def create_graph_point(
    point_data: Dict[str, Any],
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Create a point in the graph database."""
    try:
        point = GeometricPoint(
            node_id=point_data.get("node_id", f"point_{int(datetime.now().timestamp())}"),
            x=point_data["x"],
            y=point_data["y"],
            label=point_data.get("label"),
            is_constructed=point_data.get("is_constructed", False)
        )
        
        result = await neo4j_service.create_point(point)
        logger.info("Graph point created", point_id=point.node_id)
        
        return {
            "success": True,
            "point": point.dict(),
            "graph_result": result.dict()
        }
        
    except Exception as e:
        logger.error("Graph point creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create graph point: {str(e)}"
        )


@router.post(
    "/construction/{construction_id}/relationships",
    summary="Create Construction Relationships",
    description="Create relationships between a construction and its geometric objects"
)
async def create_construction_relationships(
    construction_id: str,
    object_ids: List[str],
    relationship_type: str = "CREATED_BY",
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Create relationships between construction and geometric objects."""
    try:
        await neo4j_service.link_construction_objects(
            construction_id, object_ids, relationship_type
        )
        
        logger.info(
            "Construction relationships created",
            construction_id=construction_id,
            object_count=len(object_ids),
            relationship_type=relationship_type
        )
        
        return {
            "success": True,
            "construction_id": construction_id,
            "objects_linked": len(object_ids),
            "relationship_type": relationship_type
        }
        
    except Exception as e:
        logger.error("Construction relationship creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create construction relationships: {str(e)}"
        )


@router.get(
    "/construction/{construction_id}/graph",
    summary="Get Construction Graph",
    description="Get the complete graph structure for a construction"
)
async def get_construction_graph(
    construction_id: str,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get the complete graph structure for a construction."""
    try:
        graph_data = await neo4j_service.get_construction_graph(construction_id)
        
        if not graph_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Construction {construction_id} not found in graph"
            )
        
        logger.info("Construction graph retrieved", construction_id=construction_id)
        return graph_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Construction graph retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve construction graph: {str(e)}"
        )


@router.get(
    "/construction/{construction_id}/similar",
    summary="Find Similar Constructions",
    description="Find constructions similar to the given one based on graph structure"
)
async def find_similar_constructions(
    construction_id: str,
    limit: int = 10,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Find constructions similar to the given one."""
    try:
        similar = await neo4j_service.find_similar_constructions(construction_id, limit)
        
        logger.info(
            "Similar constructions found",
            construction_id=construction_id,
            similar_count=len(similar)
        )
        
        return {
            "construction_id": construction_id,
            "similar_constructions": similar,
            "count": len(similar)
        }
        
    except Exception as e:
        logger.error("Similar construction search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar constructions: {str(e)}"
        )


@router.post(
    "/analyze",
    summary="Analyze Graph Patterns",
    description="Perform various types of graph analysis on geometric data"
)
async def analyze_graph_patterns(
    analysis_request: GraphAnalysisRequest,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Perform graph pattern analysis."""
    try:
        if analysis_request.analysis_type == "construction_patterns":
            player_id = analysis_request.parameters.get("player_id")
            result = await neo4j_service.analyze_construction_patterns(player_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown analysis type: {analysis_request.analysis_type}"
            )
        
        logger.info(
            "Graph analysis completed",
            analysis_type=analysis_request.analysis_type,
            patterns_found=len(result.get("patterns", []))
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Graph analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph analysis failed: {str(e)}"
        )


@router.get(
    "/objects/{object_id}/relationships",
    summary="Get Object Relationships",
    description="Get all relationships for a geometric object"
)
async def get_object_relationships(
    object_id: str,
    relationship_types: Optional[List[str]] = None,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get all relationships for a geometric object."""
    try:
        # Build dynamic query based on relationship types filter
        relationship_filter = ""
        if relationship_types:
            relationship_filter = f":{':'.join(relationship_types)}"
        
        query = GraphQuery(
            cypher=f"""
                MATCH (obj:GeometricObject {{node_id: $object_id}})-[r{relationship_filter}]-(related)
                RETURN 
                    type(r) as relationship_type,
                    related.node_id as related_id,
                    labels(related) as related_labels,
                    r as relationship_properties,
                    related as related_object
                ORDER BY type(r), related.created_at
            """,
            parameters={"object_id": object_id}
        )
        
        result = await neo4j_service.execute_query(query)
        
        logger.info(
            "Object relationships retrieved",
            object_id=object_id,
            relationships_count=len(result.records)
        )
        
        return {
            "object_id": object_id,
            "relationships": result.records,
            "count": len(result.records)
        }
        
    except Exception as e:
        logger.error("Object relationships retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve object relationships: {str(e)}"
        )


@router.get(
    "/player/{player_id}/graph",
    summary="Get Player Graph",
    description="Get the complete graph of constructions and elements for a player"
)
async def get_player_graph(
    player_id: str,
    include_elements: bool = True,
    include_constructions: bool = True,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get player's complete graph including constructions and elements."""
    try:
        # Build query based on what to include
        optional_clauses = []
        return_clauses = ["p"]
        
        if include_elements:
            optional_clauses.append("OPTIONAL MATCH (p)-[:OWNS]->(e:Element)")
            return_clauses.append("collect(DISTINCT e) as elements")
        
        if include_constructions:
            optional_clauses.append("OPTIONAL MATCH (p)<-[:CREATED_BY]-(c:Construction)")
            optional_clauses.append("OPTIONAL MATCH (c)-[:CREATED_BY|DEPENDS_ON]-(obj:GeometricObject)")
            return_clauses.extend([
                "collect(DISTINCT c) as constructions",
                "collect(DISTINCT obj) as geometric_objects"
            ])
        
        query = GraphQuery(
            cypher=f"""
                MATCH (p:Player {{node_id: $player_id}})
                {chr(10).join(optional_clauses)}
                RETURN {', '.join(return_clauses)}
            """,
            parameters={"player_id": player_id}
        )
        
        result = await neo4j_service.execute_query(query)
        
        if not result.records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Player {player_id} not found in graph"
            )
        
        player_data = result.records[0]
        
        logger.info(
            "Player graph retrieved",
            player_id=player_id,
            elements=len(player_data.get("elements", [])),
            constructions=len(player_data.get("constructions", []))
        )
        
        return {
            "player_id": player_id,
            "player": player_data.get("p", {}),
            "elements": player_data.get("elements", []),
            "constructions": player_data.get("constructions", []),
            "geometric_objects": player_data.get("geometric_objects", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Player graph retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve player graph: {str(e)}"
        )


@router.get(
    "/stats",
    summary="Graph Database Statistics",
    description="Get statistics about the graph database contents"
)
async def get_graph_statistics(
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get graph database statistics."""
    try:
        query = GraphQuery(
            cypher="""
                MATCH (n)
                WITH labels(n) as nodeLabels
                UNWIND nodeLabels as label
                RETURN label, count(*) as count
                ORDER BY count DESC
                
                UNION ALL
                
                MATCH ()-[r]->()
                WITH type(r) as relType
                RETURN relType as label, count(*) as count
                ORDER BY count DESC
            """
        )
        
        result = await neo4j_service.execute_query(query)
        
        # Separate nodes and relationships
        nodes = []
        relationships = []
        
        for record in result.records:
            label = record.get("label", "")
            count = record.get("count", 0)
            
            # Simple heuristic: relationship types are usually ALL_CAPS
            if label and label.isupper():
                relationships.append({"type": label, "count": count})
            else:
                nodes.append({"label": label, "count": count})
        
        logger.info("Graph statistics retrieved")
        
        return {
            "nodes": nodes,
            "relationships": relationships,
            "total_nodes": sum(node["count"] for node in nodes),
            "total_relationships": sum(rel["count"] for rel in relationships),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Graph statistics retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve graph statistics: {str(e)}"
        )


