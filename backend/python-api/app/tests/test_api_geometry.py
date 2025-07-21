"""
Tests for geometry API endpoints.

Tests the core geometric operations including points, lines, circles,
and intersections through the REST API.
"""

import pytest
from httpx import AsyncClient

from .conftest import assert_api_response_structure, assert_construction_space_valid


class TestGeometryHealth:
    """Test geometry health check endpoint."""
    
    async def test_geometry_health_check_success(self, async_client: AsyncClient):
        """Test successful geometry health check."""
        response = await async_client.get("/api/v1/geometry/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert_api_response_structure(data, ["success", "message", "data"])
        assert data["success"] is True
        assert "engine_available" in data["data"]
    
    async def test_geometry_health_check_handles_failure(self, async_client: AsyncClient, mock_rust_service):
        """Test geometry health check when service is unavailable."""
        # Override mock to simulate failure
        mock_rust_service.health_check.return_value = False
        
        response = await async_client.get("/api/v1/geometry/health")
        
        # Should still return 200 but with failure indication
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestConstructionSpaceEndpoints:
    """Test construction space management endpoints."""
    
    async def test_create_construction_space(self, async_client: AsyncClient):
        """Test creating a new construction space."""
        response = await async_client.post("/api/v1/geometry/construction-space")
        
        assert response.status_code == 200
        data = response.json()
        
        assert_api_response_structure(data, ["construction_space", "operation"])
        assert data["operation"] == "create_construction_space"
        assert_construction_space_valid(data["construction_space"])
    
    async def test_construction_space_summary(self, async_client: AsyncClient):
        """Test getting construction space summary."""
        # Create a construction space first
        create_response = await async_client.post("/api/v1/geometry/construction-space")
        construction_space = create_response.json()["construction_space"]
        
        response = await async_client.get(
            "/api/v1/geometry/construction-space/test_space/summary",
            json=construction_space
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert_api_response_structure(data, ["summary", "operation"])
        summary = data["summary"]
        
        required_summary_keys = [
            "point_count", "line_count", "circle_count", 
            "total_objects", "construction_steps"
        ]
        assert_api_response_structure(summary, required_summary_keys)
        
        # All counts should be non-negative integers
        for key in required_summary_keys:
            assert isinstance(summary[key], int)
            assert summary[key] >= 0


class TestPointOperations:
    """Test point creation and management."""
    
    async def test_add_point_success(self, async_client: AsyncClient, sample_construction_space):
        """Test successful point addition."""
        point_data = {
            "x": 150.0,
            "y": 200.0,
            "label": "D"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/points",
            json={
                "point_data": point_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert_api_response_structure(data, ["construction_space", "operation", "created_id"])
        assert data["operation"] == "add_point"
        assert data["created_id"] is not None
        assert_construction_space_valid(data["construction_space"])
    
    async def test_add_point_validation(self, async_client: AsyncClient, sample_construction_space):
        """Test point addition with invalid data."""
        invalid_point_data = {
            "x": "invalid",  # Should be numeric
            "y": 200.0,
            "label": "D"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/points",
            json={
                "point_data": invalid_point_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_add_point_without_label(self, async_client: AsyncClient, sample_construction_space):
        """Test adding point without optional label."""
        point_data = {
            "x": 75.0,
            "y": 125.0
        }
        
        response = await async_client.post(
            "/api/v1/geometry/points",
            json={
                "point_data": point_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["created_id"] is not None


class TestLineOperations:
    """Test line construction operations."""
    
    async def test_construct_line_success(self, async_client: AsyncClient, sample_construction_space):
        """Test successful line construction."""
        line_data = {
            "point1_id": "point_a",
            "point2_id": "point_b",
            "label": "AB"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/lines",
            json={
                "line_data": line_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert_api_response_structure(data, ["construction_space", "operation", "created_id"])
        assert data["operation"] == "construct_line"
        assert data["created_id"] is not None
    
    async def test_construct_line_invalid_points(self, async_client: AsyncClient, sample_construction_space):
        """Test line construction with non-existent points."""
        line_data = {
            "point1_id": "nonexistent_point1",
            "point2_id": "nonexistent_point2",
            "label": "Invalid"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/lines",
            json={
                "line_data": line_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        # Should handle gracefully - behavior depends on rust service mock
        assert response.status_code in [200, 422]
    
    async def test_construct_line_same_points(self, async_client: AsyncClient, sample_construction_space):
        """Test line construction with identical points."""
        line_data = {
            "point1_id": "point_a",
            "point2_id": "point_a",  # Same point
            "label": "Invalid"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/lines",
            json={
                "line_data": line_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 422]


class TestCircleOperations:
    """Test circle construction operations."""
    
    async def test_construct_circle_success(self, async_client: AsyncClient, sample_construction_space):
        """Test successful circle construction."""
        circle_data = {
            "center_id": "point_a",
            "radius_point_id": "point_b",
            "label": "CircleA"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/circles",
            json={
                "circle_data": circle_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert_api_response_structure(data, ["construction_space", "operation", "created_id"])
        assert data["operation"] == "construct_circle"
        assert data["created_id"] is not None
    
    async def test_construct_circle_same_center_radius(self, async_client: AsyncClient, sample_construction_space):
        """Test circle construction with center and radius point being the same."""
        circle_data = {
            "center_id": "point_a",
            "radius_point_id": "point_a",  # Same as center
            "label": "InvalidCircle"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/circles",
            json={
                "circle_data": circle_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 422]


class TestIntersectionOperations:
    """Test intersection finding operations."""
    
    async def test_find_intersections_success(self, async_client: AsyncClient, sample_construction_space):
        """Test successful intersection finding."""
        intersection_data = {
            "obj1_id": "line_ab",
            "obj2_id": "circle_a"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/intersections",
            json={
                **intersection_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_keys = ["construction_space", "intersections", "intersection_count", "operation"]
        assert_api_response_structure(data, required_keys)
        assert data["operation"] == "find_intersections"
        assert isinstance(data["intersections"], list)
        assert isinstance(data["intersection_count"], int)
        assert data["intersection_count"] >= 0
    
    async def test_find_intersections_no_intersection(self, async_client: AsyncClient, sample_construction_space):
        """Test intersection finding when objects don't intersect."""
        intersection_data = {
            "obj1_id": "line_ab",
            "obj2_id": "line_bc"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/intersections",
            json={
                **intersection_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Even if no intersections, should return valid structure
        assert data["intersection_count"] >= 0
        assert isinstance(data["intersections"], list)
    
    async def test_find_intersections_invalid_objects(self, async_client: AsyncClient, sample_construction_space):
        """Test intersection finding with invalid object IDs."""
        intersection_data = {
            "obj1_id": "nonexistent_obj1",
            "obj2_id": "nonexistent_obj2"
        }
        
        response = await async_client.post(
            "/api/v1/geometry/intersections",
            json={
                **intersection_data,
                "construction_space_data": sample_construction_space
            }
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 422]


class TestGeometryIntegration:
    """Integration tests for multiple geometry operations."""
    
    async def test_complete_triangle_construction(self, async_client: AsyncClient):
        """Test constructing a complete triangle through multiple API calls."""
        # Create construction space
        response = await async_client.post("/api/v1/geometry/construction-space")
        construction_space = response.json()["construction_space"]
        
        # Add three points
        points = [
            {"x": 0, "y": 0, "label": "A"},
            {"x": 100, "y": 0, "label": "B"},
            {"x": 50, "y": 87, "label": "C"}
        ]
        
        for point_data in points:
            response = await async_client.post(
                "/api/v1/geometry/points",
                json={
                    "point_data": point_data,
                    "construction_space_data": construction_space
                }
            )
            assert response.status_code == 200
            construction_space = response.json()["construction_space"]
        
        # Check that all points were added
        summary_response = await async_client.get(
            "/api/v1/geometry/construction-space/test/summary",
            json=construction_space
        )
        summary = summary_response.json()["summary"]
        assert summary["point_count"] >= 3
    
    async def test_error_handling_consistency(self, async_client: AsyncClient):
        """Test that all endpoints handle errors consistently."""
        # Test with completely invalid data
        invalid_requests = [
            ("/api/v1/geometry/points", {"invalid": "data"}),
            ("/api/v1/geometry/lines", {"invalid": "data"}),
            ("/api/v1/geometry/circles", {"invalid": "data"}),
            ("/api/v1/geometry/intersections", {"invalid": "data"})
        ]
        
        for endpoint, data in invalid_requests:
            response = await async_client.post(endpoint, json=data)
            # All should return proper HTTP error codes
            assert response.status_code in [400, 422, 500]
            
            # Response should be JSON
            assert response.headers["content-type"] == "application/json"