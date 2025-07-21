"""
Tests for MAGI AI assistant API endpoints.

Tests the AI assistant functionality including query processing,
proof verification, and educational guidance.
"""

import pytest
from httpx import AsyncClient

from .conftest import assert_api_response_structure, assert_magi_response_valid


class TestMAGIQuery:
    """Test MAGI query endpoint."""
    
    async def test_magi_query_construction_help(self, async_client: AsyncClient, sample_magi_query):
        """Test MAGI query for construction help."""
        response = await async_client.post("/api/v1/magi/query", json=sample_magi_query)
        
        assert response.status_code == 200
        data = response.json()
        
        assert_magi_response_valid(data)
        assert data["response_type"] == "construction_help"
        assert data["magi_system"] in ["casper", "melchior", "balthasar"]
    
    async def test_magi_query_different_types(self, async_client: AsyncClient):
        """Test different types of MAGI queries."""
        query_types = [
            "construction_help",
            "proof_check", 
            "step_explanation",
            "theorem_info",
            "hint_request",
            "error_analysis"
        ]
        
        for query_type in query_types:
            query = {
                "query_type": query_type,
                "content": f"Test query for {query_type}",
                "difficulty_level": "beginner"
            }
            
            response = await async_client.post("/api/v1/magi/query", json=query)
            assert response.status_code == 200
            
            data = response.json()
            assert data["response_type"] == query_type
    
    async def test_magi_query_with_construction_space(self, async_client: AsyncClient, sample_construction_space):
        """Test MAGI query with construction space context."""
        query = {
            "query_type": "construction_help",
            "content": "How can I improve this construction?",
            "construction_space": sample_construction_space,
            "difficulty_level": "intermediate"
        }
        
        response = await async_client.post("/api/v1/magi/query", json=query)
        
        assert response.status_code == 200
        data = response.json()
        assert_magi_response_valid(data)
        
        # Should have contextual suggestions based on construction space
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    async def test_magi_query_preferred_system(self, async_client: AsyncClient):
        """Test MAGI query with preferred system selection."""
        magi_systems = ["casper", "melchior", "balthasar"]
        
        for preferred_magi in magi_systems:
            query = {
                "query_type": "construction_help",
                "content": "Test query",
                "preferred_magi": preferred_magi,
                "difficulty_level": "beginner"
            }
            
            response = await async_client.post("/api/v1/magi/query", json=query)
            assert response.status_code == 200
            
            data = response.json()
            # Should respect preferred MAGI system (or have good reason to override)
            assert data["magi_system"] in magi_systems
    
    async def test_magi_query_validation(self, async_client: AsyncClient):
        """Test MAGI query validation."""
        # Test missing required fields
        invalid_queries = [
            {},  # Empty query
            {"query_type": "construction_help"},  # Missing content
            {"content": "Test"},  # Missing query_type
            {"query_type": "invalid_type", "content": "Test"},  # Invalid query type
        ]
        
        for invalid_query in invalid_queries:
            response = await async_client.post("/api/v1/magi/query", json=invalid_query)
            assert response.status_code == 422  # Validation error
    
    async def test_magi_response_structure(self, async_client: AsyncClient):
        """Test that MAGI responses have consistent structure."""
        query = {
            "query_type": "construction_help",
            "content": "How do I construct a perpendicular bisector?",
            "difficulty_level": "beginner"
        }
        
        response = await async_client.post("/api/v1/magi/query", json=query)
        assert response.status_code == 200
        
        data = response.json()
        
        # Test all required fields exist
        required_fields = [
            "magi_system", "response_type", "content", "suggestions",
            "next_steps", "confidence", "additional_resources", "timestamp"
        ]
        assert_api_response_structure(data, required_fields)
        
        # Test field types
        assert isinstance(data["suggestions"], list)
        assert isinstance(data["next_steps"], list)
        assert isinstance(data["additional_resources"], list)
        assert 0 <= data["confidence"] <= 1


class TestProofVerification:
    """Test proof verification endpoint."""
    
    async def test_verify_proof_success(self, async_client: AsyncClient, sample_construction_space):
        """Test successful proof verification."""
        proof_request = {
            "construction_space": sample_construction_space,
            "claimed_theorem": "Triangle angle sum equals 180 degrees",
            "proof_steps": [
                "Given triangle ABC with vertices A, B, C",
                "Draw line through C parallel to AB",
                "Angles on the line sum to 180 degrees", 
                "Therefore triangle angles sum to 180 degrees"
            ],
            "student_explanation": "Using parallel line properties"
        }
        
        response = await async_client.post("/api/v1/magi/verify-proof", json=proof_request)
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "is_valid", "verification_details", "errors_found",
            "suggestions", "missing_steps", "alternative_approaches"
        ]
        assert_api_response_structure(data, required_fields)
        
        assert isinstance(data["is_valid"], bool)
        assert isinstance(data["errors_found"], list)
        assert isinstance(data["suggestions"], list)
    
    async def test_verify_proof_invalid(self, async_client: AsyncClient, sample_construction_space):
        """Test proof verification with invalid proof."""
        proof_request = {
            "construction_space": sample_construction_space,
            "claimed_theorem": "All triangles are right triangles",  # False theorem
            "proof_steps": [
                "Given any triangle",
                "Therefore it is a right triangle"  # Invalid logic
            ]
        }
        
        response = await async_client.post("/api/v1/magi/verify-proof", json=proof_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should identify as invalid
        assert data["is_valid"] is False
        assert len(data["errors_found"]) > 0 or len(data["missing_steps"]) > 0
    
    async def test_verify_proof_incomplete(self, async_client: AsyncClient, sample_construction_space):
        """Test proof verification with incomplete proof."""
        proof_request = {
            "construction_space": sample_construction_space,
            "claimed_theorem": "Pythagorean theorem",
            "proof_steps": [
                "Given right triangle"
                # Missing actual proof steps
            ]
        }
        
        response = await async_client.post("/api/v1/magi/verify-proof", json=proof_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should identify missing steps
        assert len(data["missing_steps"]) > 0 or len(data["suggestions"]) > 0


class TestLearningPaths:
    """Test learning path generation endpoint."""
    
    async def test_get_learning_path_triangles(self, async_client: AsyncClient):
        """Test learning path for triangles."""
        response = await async_client.get(
            "/api/v1/magi/learning-path/triangles",
            params={"current_level": "beginner", "include_prerequisites": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["title", "description", "steps", "estimated_time"]
        assert_api_response_structure(data, required_fields)
        
        assert isinstance(data["steps"], list)
        assert len(data["steps"]) > 0
        
        # Each step should have proper structure
        for step in data["steps"]:
            step_fields = ["step", "title", "description", "difficulty"]
            assert_api_response_structure(step, step_fields)
    
    async def test_get_learning_path_circles(self, async_client: AsyncClient):
        """Test learning path for circles."""
        response = await async_client.get(
            "/api/v1/magi/learning-path/circles",
            params={"current_level": "intermediate"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] is not None
        assert isinstance(data["steps"], list)
    
    async def test_get_learning_path_unknown_topic(self, async_client: AsyncClient):
        """Test learning path for unknown topic."""
        response = await async_client.get(
            "/api/v1/magi/learning-path/unknown_topic"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still return a valid structure even for unknown topics
        assert "title" in data
        assert "steps" in data


class TestErrorAnalysis:
    """Test error analysis endpoint."""
    
    async def test_analyze_error_identical_points(self, async_client: AsyncClient, sample_construction_space):
        """Test error analysis for identical points."""
        error_request = {
            "construction_space": sample_construction_space,
            "error_description": "Cannot create line with identical points",
            "attempted_construction": "line_creation"
        }
        
        response = await async_client.post("/api/v1/magi/analyze-error", json=error_request)
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["error_type", "severity", "likely_causes", "suggestions", "corrective_steps"]
        assert_api_response_structure(data, required_fields)
        
        assert data["error_type"] == "identical_points"
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) > 0
    
    async def test_analyze_error_no_intersection(self, async_client: AsyncClient, sample_construction_space):
        """Test error analysis for no intersections found."""
        error_request = {
            "construction_space": sample_construction_space,
            "error_description": "No intersection found between objects",
            "attempted_construction": "intersection_finding"
        }
        
        response = await async_client.post("/api/v1/magi/analyze-error", json=error_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["error_type"] == "no_intersection"
        assert "construction_summary" in data
    
    async def test_analyze_error_construction_failure(self, async_client: AsyncClient, sample_construction_space):
        """Test error analysis for general construction failure."""
        error_request = {
            "construction_space": sample_construction_space,
            "error_description": "Construction failed to complete",
            "attempted_construction": "complex_construction"
        }
        
        response = await async_client.post("/api/v1/magi/analyze-error", json=error_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["corrective_steps"], list)
        assert "context_notes" in data


class TestTheoremInfo:
    """Test theorem information endpoint."""
    
    async def test_get_theorem_pythagorean(self, async_client: AsyncClient):
        """Test getting Pythagorean theorem information."""
        response = await async_client.get(
            "/api/v1/magi/theorem/pythagorean_theorem",
            params={
                "include_proof": True,
                "include_applications": True,
                "difficulty_level": "intermediate"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "theorem" in data
        theorem = data["theorem"]
        
        theorem_fields = ["name", "statement", "difficulty", "category"]
        assert_api_response_structure(theorem, theorem_fields)
        
        assert theorem["name"] == "Pythagorean Theorem"
        assert "learning_resources" in data
    
    async def test_get_theorem_angle_sum(self, async_client: AsyncClient):
        """Test getting triangle angle sum theorem."""
        response = await async_client.get(
            "/api/v1/magi/theorem/sum_of_angles",
            params={"difficulty_level": "beginner"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        theorem = data["theorem"]
        assert theorem["category"] == "triangles"
        assert theorem["difficulty"] == "beginner"
    
    async def test_get_theorem_unknown(self, async_client: AsyncClient):
        """Test getting information for unknown theorem."""
        response = await async_client.get("/api/v1/magi/theorem/unknown_theorem")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still return valid structure for unknown theorems
        assert "theorem" in data
        assert data["theorem"]["name"] is not None


class TestMAGIIntegration:
    """Integration tests for MAGI system."""
    
    async def test_magi_workflow_construction_help(self, async_client: AsyncClient, sample_construction_space):
        """Test complete workflow of getting construction help from MAGI."""
        # 1. Ask for construction help
        query = {
            "query_type": "construction_help",
            "content": "I want to construct a perpendicular bisector",
            "construction_space": sample_construction_space,
            "difficulty_level": "beginner"
        }
        
        help_response = await async_client.post("/api/v1/magi/query", json=query)
        assert help_response.status_code == 200
        help_data = help_response.json()
        
        # 2. Get learning path for related topic
        path_response = await async_client.get("/api/v1/magi/learning-path/lines")
        assert path_response.status_code == 200
        
        # 3. Get theorem information
        theorem_response = await async_client.get("/api/v1/magi/theorem/perpendicular_bisector")
        assert theorem_response.status_code == 200
        
        # All should work together coherently
        assert help_data["confidence"] > 0
        assert len(help_data["suggestions"]) > 0
    
    async def test_magi_error_recovery(self, async_client: AsyncClient, sample_construction_space):
        """Test MAGI system handles errors gracefully."""
        # Send malformed requests that should be handled gracefully
        malformed_requests = [
            {"query_type": "construction_help", "content": ""},  # Empty content
            {"query_type": "construction_help", "content": "a" * 10000},  # Very long content
            {"query_type": "construction_help", "content": None},  # Null content
        ]
        
        for malformed_query in malformed_requests:
            response = await async_client.post("/api/v1/magi/query", json=malformed_query)
            # Should either handle gracefully or return proper error
            assert response.status_code in [200, 422]
    
    async def test_magi_response_consistency(self, async_client: AsyncClient):
        """Test that MAGI responses are consistent across multiple calls."""
        query = {
            "query_type": "construction_help",
            "content": "How do I construct an equilateral triangle?",
            "difficulty_level": "beginner"
        }
        
        # Make multiple identical requests
        responses = []
        for _ in range(3):
            response = await async_client.post("/api/v1/magi/query", json=query)
            assert response.status_code == 200
            responses.append(response.json())
        
        # Responses should have consistent structure
        for response_data in responses:
            assert_magi_response_valid(response_data)
            # Content may vary, but structure should be consistent
            assert response_data["response_type"] == "construction_help"