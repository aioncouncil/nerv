"""
Tests for collection API endpoints.

Tests the Pokédex-style element collection system including
element unlocking, achievement tracking, and progression.
"""

import pytest
from httpx import AsyncClient

from .conftest import assert_api_response_structure


class TestPlayerCollection:
    """Test player collection management."""
    
    async def test_get_player_collection_success(self, async_client: AsyncClient):
        """Test getting player collection successfully."""
        player_id = "test_player_123"
        response = await async_client.get(f"/api/v1/collection/player/{player_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["collection", "available_elements", "next_unlockable"]
        assert_api_response_structure(data, required_fields)
        
        # Test collection structure
        collection = data["collection"]
        collection_fields = [
            "player_id", "username", "total_elements", "unique_elements",
            "common_count", "uncommon_count", "rare_count", "legendary_count",
            "elements", "current_level", "experience_points"
        ]
        assert_api_response_structure(collection, collection_fields)
        
        # Test data types
        assert isinstance(collection["total_elements"], int)
        assert isinstance(collection["elements"], dict)
        assert collection["player_id"] == player_id
    
    async def test_get_player_collection_with_locked_elements(self, async_client: AsyncClient):
        """Test getting player collection including locked elements."""
        player_id = "test_player_456"
        response = await async_client.get(
            f"/api/v1/collection/player/{player_id}",
            params={"include_locked": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include more elements when include_locked=True
        assert len(data["available_elements"]) >= len(data["collection"]["elements"])
    
    async def test_get_player_collection_nonexistent(self, async_client: AsyncClient):
        """Test getting collection for nonexistent player."""
        response = await async_client.get("/api/v1/collection/player/nonexistent_player")
        
        # Should create default collection for new players
        assert response.status_code == 200
        data = response.json()
        
        collection = data["collection"]
        assert collection["player_id"] == "nonexistent_player"
        assert collection["total_elements"] >= 0


class TestElementUnlocking:
    """Test element unlocking mechanics."""
    
    async def test_unlock_element_success(self, async_client: AsyncClient, sample_construction_space):
        """Test successful element unlocking."""
        unlock_request = {
            "player_id": "test_player",
            "construction_space": sample_construction_space,
            "completed_construction": "line_segment"
        }
        
        response = await async_client.post("/api/v1/collection/unlock-element", json=unlock_request)
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["success", "unlocked_elements", "experience_gained", "construction_analysis", "message"]
        assert_api_response_structure(data, required_fields)
        
        assert isinstance(data["success"], bool)
        assert isinstance(data["unlocked_elements"], list)
        assert isinstance(data["experience_gained"], int)
        assert data["experience_gained"] >= 0
    
    async def test_unlock_element_equilateral_triangle(self, async_client: AsyncClient):
        """Test unlocking equilateral triangle element."""
        # Create construction space with triangle pattern
        construction_space = {
            "points": {
                "point_a": {"x": 0, "y": 0},
                "point_b": {"x": 100, "y": 0},
                "point_c": {"x": 50, "y": 87}
            },
            "lines": {
                "line_ab": {"point1_id": "point_a", "point2_id": "point_b"},
                "line_bc": {"point1_id": "point_b", "point2_id": "point_c"},
                "line_ca": {"point1_id": "point_c", "point2_id": "point_a"}
            },
            "circles": {
                "circle_a": {"center_id": "point_a", "radius_point_id": "point_b"},
                "circle_b": {"center_id": "point_b", "radius_point_id": "point_a"}
            },
            "history": []
        }
        
        unlock_request = {
            "player_id": "test_player",
            "construction_space": construction_space,
            "completed_construction": "equilateral_triangle"
        }
        
        response = await async_client.post("/api/v1/collection/unlock-element", json=unlock_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should analyze the construction and potentially unlock triangle
        assert "construction_analysis" in data
        analysis = data["construction_analysis"]
        
        analysis_fields = ["point_count", "line_count", "circle_count", "identified_patterns"]
        assert_api_response_structure(analysis, analysis_fields)
        
        # Should identify triangle pattern
        if "equilateral_triangle" in analysis["identified_patterns"]:
            assert data["experience_gained"] > 0
    
    async def test_unlock_element_invalid_construction(self, async_client: AsyncClient):
        """Test element unlocking with invalid construction."""
        unlock_request = {
            "player_id": "test_player",
            "construction_space": {"points": {}, "lines": {}, "circles": {}, "history": []},
            "completed_construction": "invalid_construction"
        }
        
        response = await async_client.post("/api/v1/collection/unlock-element", json=unlock_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not unlock anything for invalid construction
        assert data["success"] is False or len(data["unlocked_elements"]) == 0
    
    async def test_unlock_element_missing_requirements(self, async_client: AsyncClient):
        """Test unlocking element without meeting requirements."""
        # Try to unlock advanced element without prerequisites
        unlock_request = {
            "player_id": "new_player",
            "construction_space": {"points": {}, "lines": {}, "circles": {}, "history": []},
            "completed_construction": "golden_ratio"  # Legendary element
        }
        
        response = await async_client.post("/api/v1/collection/unlock-element", json=unlock_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not unlock legendary element without prerequisites
        legendary_unlocked = any(
            element.get("rarity") == "legendary" 
            for element in data["unlocked_elements"]
        )
        assert not legendary_unlocked


class TestElementListing:
    """Test element listing and filtering."""
    
    async def test_list_all_elements(self, async_client: AsyncClient):
        """Test listing all elements."""
        response = await async_client.get("/api/v1/collection/elements")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["elements", "total_count", "by_category", "by_rarity", "categories", "rarities"]
        assert_api_response_structure(data, required_fields)
        
        assert isinstance(data["elements"], list)
        assert data["total_count"] == len(data["elements"])
        assert isinstance(data["by_category"], dict)
        assert isinstance(data["by_rarity"], dict)
        
        # Should have elements in different rarities
        assert len(data["rarities"]) > 1
        assert "common" in data["by_rarity"]
    
    async def test_list_elements_by_category(self, async_client: AsyncClient):
        """Test listing elements filtered by category."""
        categories = ["point", "line", "circle", "polygon"]
        
        for category in categories:
            response = await async_client.get(
                "/api/v1/collection/elements",
                params={"category": category}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # All returned elements should match the category filter
            for element in data["elements"]:
                assert element["category"] == category
    
    async def test_list_elements_by_rarity(self, async_client: AsyncClient):
        """Test listing elements filtered by rarity."""
        rarities = ["common", "uncommon", "rare", "legendary"]
        
        for rarity in rarities:
            response = await async_client.get(
                "/api/v1/collection/elements",
                params={"rarity": rarity}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # All returned elements should match the rarity filter
            for element in data["elements"]:
                assert element["rarity"] == rarity
    
    async def test_list_elements_unlocked_only(self, async_client: AsyncClient):
        """Test listing only unlocked elements."""
        response = await async_client.get(
            "/api/v1/collection/elements",
            params={"unlocked_only": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned elements should be unlocked
        for element in data["elements"]:
            assert element.get("is_unlocked", False) is True
    
    async def test_list_elements_combined_filters(self, async_client: AsyncClient):
        """Test listing elements with multiple filters."""
        response = await async_client.get(
            "/api/v1/collection/elements",
            params={
                "category": "line",
                "rarity": "common",
                "unlocked_only": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All elements should match all filters
        for element in data["elements"]:
            assert element["category"] == "line"
            assert element["rarity"] == "common"
            assert element.get("is_unlocked", False) is True


class TestAchievements:
    """Test achievement system."""
    
    async def test_check_achievements_first_construction(self, async_client: AsyncClient):
        """Test checking achievements for first construction."""
        construction_space = {
            "points": {"point_a": {"x": 0, "y": 0}},
            "lines": {},
            "circles": {},
            "history": [{"action": "add_point", "id": "point_a"}]
        }
        
        response = await async_client.post(
            "/api/v1/collection/achievements/check",
            json={
                "player_id": "new_player",
                "construction_space": construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["new_achievements", "total_new", "message"]
        assert_api_response_structure(data, required_fields)
        
        assert isinstance(data["new_achievements"], list)
        assert isinstance(data["total_new"], int)
        
        # Should award "first_construction" achievement
        achievement_ids = [ach["id"] for ach in data["new_achievements"]]
        if data["total_new"] > 0:
            assert "first_construction" in achievement_ids
    
    async def test_check_achievements_triangle_master(self, async_client: AsyncClient):
        """Test checking achievements for triangle mastery."""
        # Create construction space with many triangles
        construction_space = {
            "points": {},
            "lines": {},
            "circles": {},
            "history": [
                {"action": "construct_triangle", "description": f"triangle_{i}"}
                for i in range(12)  # More than required for achievement
            ]
        }
        
        response = await async_client.post(
            "/api/v1/collection/achievements/check",
            json={
                "player_id": "advanced_player", 
                "construction_space": construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Might award triangle-related achievements
        for achievement in data["new_achievements"]:
            assert "id" in achievement
            assert "name" in achievement
            assert "description" in achievement
            assert "unlocked_at" in achievement
    
    async def test_check_achievements_no_new(self, async_client: AsyncClient):
        """Test checking achievements when no new achievements earned."""
        empty_construction_space = {
            "points": {},
            "lines": {},
            "circles": {},
            "history": []
        }
        
        response = await async_client.post(
            "/api/v1/collection/achievements/check",
            json={
                "player_id": "test_player",
                "construction_space": empty_construction_space
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_new"] == 0
        assert len(data["new_achievements"]) == 0
        assert "No new achievements" in data["message"]


class TestCollectionIntegration:
    """Integration tests for collection system."""
    
    async def test_complete_progression_workflow(self, async_client: AsyncClient):
        """Test complete progression from new player to advanced collection."""
        player_id = "progression_test_player"
        
        # 1. Get initial collection (should be mostly empty)
        initial_response = await async_client.get(f"/api/v1/collection/player/{player_id}")
        assert initial_response.status_code == 200
        initial_data = initial_response.json()
        initial_count = initial_data["collection"]["total_elements"]
        
        # 2. Try to unlock basic element
        basic_construction = {
            "points": {"p1": {"x": 0, "y": 0}},
            "lines": {"l1": {"point1_id": "p1", "point2_id": "p2"}},
            "circles": {},
            "history": [{"action": "construct_line"}]
        }
        
        unlock_response = await async_client.post(
            "/api/v1/collection/unlock-element",
            json={
                "player_id": player_id,
                "construction_space": basic_construction,
                "completed_construction": "line_segment"
            }
        )
        assert unlock_response.status_code == 200
        
        # 3. Check achievements
        achievement_response = await async_client.post(
            "/api/v1/collection/achievements/check",
            json={
                "player_id": player_id,
                "construction_space": basic_construction
            }
        )
        assert achievement_response.status_code == 200
        
        # 4. Get updated collection
        final_response = await async_client.get(f"/api/v1/collection/player/{player_id}")
        assert final_response.status_code == 200
        final_data = final_response.json()
        
        # Should show progression
        final_count = final_data["collection"]["total_elements"]
        assert final_count >= initial_count
    
    async def test_element_unlock_chain(self, async_client: AsyncClient):
        """Test that element unlocking follows proper dependency chain."""
        player_id = "chain_test_player"
        
        # Get list of all elements
        elements_response = await async_client.get("/api/v1/collection/elements")
        all_elements = elements_response.json()["elements"]
        
        # Find elements with dependencies
        dependent_elements = [
            element for element in all_elements 
            if element.get("unlock_requirements", [])
        ]
        
        assert len(dependent_elements) > 0, "Should have elements with dependencies"
        
        # Try to unlock advanced element without prerequisites
        advanced_element = next(
            (elem for elem in dependent_elements if elem["rarity"] in ["rare", "legendary"]),
            None
        )
        
        if advanced_element:
            unlock_response = await async_client.post(
                "/api/v1/collection/unlock-element",
                json={
                    "player_id": player_id,
                    "construction_space": {"points": {}, "lines": {}, "circles": {}, "history": []},
                    "completed_construction": advanced_element["name"].lower().replace(" ", "_")
                }
            )
            
            assert unlock_response.status_code == 200
            data = unlock_response.json()
            
            # Should not unlock advanced element without prerequisites
            unlocked_names = [elem["name"] for elem in data["unlocked_elements"]]
            assert advanced_element["name"] not in unlocked_names
    
    async def test_collection_statistics_accuracy(self, async_client: AsyncClient):
        """Test that collection statistics are accurate."""
        player_id = "stats_test_player"
        
        # Get player collection
        response = await async_client.get(f"/api/v1/collection/player/{player_id}")
        assert response.status_code == 200
        data = response.json()
        
        collection = data["collection"]
        elements = collection["elements"]
        
        # Verify counts match actual elements
        actual_total = len(elements)
        actual_common = sum(1 for elem in elements.values() if elem.get("rarity") == "common")
        actual_uncommon = sum(1 for elem in elements.values() if elem.get("rarity") == "uncommon")
        actual_rare = sum(1 for elem in elements.values() if elem.get("rarity") == "rare")
        actual_legendary = sum(1 for elem in elements.values() if elem.get("rarity") == "legendary")
        
        assert collection["total_elements"] == actual_total
        assert collection["unique_elements"] == actual_total  # Should be same for unique collection
        assert collection["common_count"] == actual_common
        assert collection["uncommon_count"] == actual_uncommon  
        assert collection["rare_count"] == actual_rare
        assert collection["legendary_count"] == actual_legendary
    
    async def test_error_handling_robustness(self, async_client: AsyncClient):
        """Test that collection endpoints handle errors gracefully."""
        # Test various error conditions
        error_conditions = [
            # Invalid player ID
            ("/api/v1/collection/player/", None),
            # Malformed unlock request
            ("/api/v1/collection/unlock-element", {"invalid": "data"}),
            # Malformed achievement check
            ("/api/v1/collection/achievements/check", {"invalid": "data"}),
        ]
        
        for endpoint, data in error_conditions:
            if data:
                response = await async_client.post(endpoint, json=data)
            else:
                response = await async_client.get(endpoint)
            
            # Should return proper HTTP error codes
            assert response.status_code in [400, 404, 422, 500]