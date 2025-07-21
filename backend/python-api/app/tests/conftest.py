"""
Test configuration and fixtures for NERV API tests.

Provides shared fixtures and configuration for all test modules.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.config import get_settings, TestingSettings
from app.services.rust_bridge import RustGeometryService
from app.services.neo4j_service import Neo4jService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings() -> TestingSettings:
    """Override settings for testing."""
    return TestingSettings()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_rust_service() -> RustGeometryService:
    """Create a mocked Rust geometry service for testing."""
    mock_service = MagicMock(spec=RustGeometryService)
    
    # Mock common methods
    mock_service.health_check = AsyncMock(return_value=True)
    mock_service.create_construction_space = AsyncMock(return_value={
        "points": {},
        "lines": {},
        "circles": {},
        "history": []
    })
    mock_service.add_point = AsyncMock(return_value=(
        "point_test_123",
        {"points": {"point_test_123": {"x": 100, "y": 100}}, "lines": {}, "circles": {}, "history": []}
    ))
    mock_service.construct_line = AsyncMock(return_value=(
        "line_test_123",
        {"points": {}, "lines": {"line_test_123": {"point1_id": "p1", "point2_id": "p2"}}, "circles": {}, "history": []}
    ))
    mock_service.construct_circle = AsyncMock(return_value=(
        "circle_test_123",
        {"points": {}, "lines": {}, "circles": {"circle_test_123": {"center_id": "p1", "radius": 50}}, "history": []}
    ))
    mock_service.find_intersections = AsyncMock(return_value=([], {}))
    mock_service.validate_construction = AsyncMock(return_value=True)
    
    return mock_service


@pytest.fixture
def mock_neo4j_service() -> Neo4jService:
    """Create a mocked Neo4j service for testing."""
    mock_service = MagicMock(spec=Neo4jService)
    
    # Mock common methods
    mock_service.health_check = AsyncMock(return_value={
        "status": "healthy",
        "database": "test",
        "components": []
    })
    mock_service.connect = AsyncMock(return_value=True)
    mock_service.disconnect = AsyncMock()
    mock_service.execute_query = AsyncMock(return_value={
        "records": [],
        "summary": {},
        "execution_time": 0.001
    })
    mock_service.create_point = AsyncMock(return_value={
        "records": [{"p": {"node_id": "test_point", "x": 100, "y": 100}}]
    })
    mock_service.create_construction = AsyncMock(return_value={
        "records": [{"c": {"node_id": "test_construction", "name": "Test"}}]
    })
    
    return mock_service


@pytest.fixture
def sample_construction_space():
    """Sample construction space data for testing."""
    return {
        "points": {
            "point_a": {"x": 0, "y": 0, "label": "A"},
            "point_b": {"x": 100, "y": 0, "label": "B"},
            "point_c": {"x": 50, "y": 87, "label": "C"}
        },
        "lines": {
            "line_ab": {"point1_id": "point_a", "point2_id": "point_b"},
            "line_bc": {"point1_id": "point_b", "point2_id": "point_c"},
            "line_ca": {"point1_id": "point_c", "point2_id": "point_a"}
        },
        "circles": {
            "circle_a": {"center_id": "point_a", "radius_point_id": "point_b", "radius": 100}
        },
        "history": [
            {"action": "add_point", "id": "point_a", "timestamp": 1234567890},
            {"action": "add_point", "id": "point_b", "timestamp": 1234567891},
            {"action": "add_point", "id": "point_c", "timestamp": 1234567892},
            {"action": "construct_line", "id": "line_ab", "timestamp": 1234567893}
        ]
    }


@pytest.fixture
def sample_player_collection():
    """Sample player collection data for testing."""
    return {
        "collection": {
            "player_id": "test_player",
            "username": "TestPlayer",
            "total_elements": 3,
            "unique_elements": 3,
            "common_count": 2,
            "uncommon_count": 1,
            "rare_count": 0,
            "legendary_count": 0,
            "elements": {
                "basic_point": {
                    "id": "basic_point",
                    "name": "Basic Point",
                    "rarity": "common",
                    "is_unlocked": True
                },
                "line_segment": {
                    "id": "line_segment", 
                    "name": "Line Segment",
                    "rarity": "common",
                    "is_unlocked": True
                },
                "equilateral_triangle": {
                    "id": "equilateral_triangle",
                    "name": "Equilateral Triangle", 
                    "rarity": "uncommon",
                    "is_unlocked": True
                }
            },
            "achievements": ["first_construction", "triangle_master"],
            "current_level": 2,
            "experience_points": 150
        },
        "available_elements": [],
        "next_unlockable": []
    }


@pytest.fixture
def sample_magi_query():
    """Sample MAGI query for testing."""
    return {
        "query_type": "construction_help",
        "content": "How do I construct an equilateral triangle?",
        "difficulty_level": "beginner",
        "preferred_magi": "casper"
    }


@pytest.fixture
def sample_construction_sequence():
    """Sample construction sequence for testing."""
    return {
        "name": "Equilateral Triangle",
        "description": "Construct an equilateral triangle on a given line segment",
        "target_theorem": "Euclid's Proposition I.1",
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
            }
        ]
    }


# Test database connection override
@pytest.fixture(autouse=True)
def override_dependencies():
    """Override app dependencies for testing."""
    from app.main import app
    from app.services.rust_bridge import get_rust_service
    from app.services.neo4j_service import get_neo4j_service
    
    # Store original dependencies
    original_rust = app.dependency_overrides.get(get_rust_service)
    original_neo4j = app.dependency_overrides.get(get_neo4j_service)
    
    # Override with mocks
    app.dependency_overrides[get_rust_service] = lambda: mock_rust_service()
    app.dependency_overrides[get_neo4j_service] = lambda: mock_neo4j_service()
    
    yield
    
    # Restore original dependencies
    if original_rust:
        app.dependency_overrides[get_rust_service] = original_rust
    else:
        app.dependency_overrides.pop(get_rust_service, None)
        
    if original_neo4j:
        app.dependency_overrides[get_neo4j_service] = original_neo4j
    else:
        app.dependency_overrides.pop(get_neo4j_service, None)


# Helper functions for tests
def assert_api_response_structure(response_data: dict, expected_keys: list):
    """Assert that API response has expected structure."""
    for key in expected_keys:
        assert key in response_data, f"Missing key '{key}' in response"


def assert_construction_space_valid(construction_space: dict):
    """Assert that construction space has valid structure."""
    required_keys = ["points", "lines", "circles", "history"]
    for key in required_keys:
        assert key in construction_space, f"Missing key '{key}' in construction space"
        assert isinstance(construction_space[key], (dict, list)), f"Invalid type for '{key}'"


def assert_geometric_point_valid(point: dict):
    """Assert that geometric point has valid structure."""
    required_keys = ["x", "y"]
    for key in required_keys:
        assert key in point, f"Missing key '{key}' in point"
        assert isinstance(point[key], (int, float)), f"Invalid type for '{key}'"


def assert_magi_response_valid(response: dict):
    """Assert that MAGI response has valid structure."""
    required_keys = ["magi_system", "response_type", "content", "confidence"]
    for key in required_keys:
        assert key in response, f"Missing key '{key}' in MAGI response"
    
    assert 0 <= response["confidence"] <= 1, "Confidence must be between 0 and 1"
    assert isinstance(response["suggestions"], list), "Suggestions must be a list"