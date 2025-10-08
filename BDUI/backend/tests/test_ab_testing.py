"""
Tests for A/B testing API endpoints
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta


@pytest.mark.unit
class TestABTestingAPI:
    """Test A/B testing CRUD operations"""
    
    def test_create_ab_test(self, client, created_screen, sample_ab_test_data):
        """Test creating a new A/B test"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        response = client.post("/api/ab-testing/", json=data)
        
        assert response.status_code == status.HTTP_200_OK
        test = response.json()
        assert test["name"] == data["name"]
        assert test["screen_id"] == created_screen["id"]
        assert test["traffic_allocation"] == 0.5
        assert test["is_active"] == False
    
    def test_create_ab_test_duplicate_name(self, client, created_screen, sample_ab_test_data):
        """Test creating A/B test with duplicate name fails"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        client.post("/api/ab-testing/", json=data)
        response = client.post("/api/ab-testing/", json=data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_ab_test_invalid_screen(self, client, sample_ab_test_data):
        """Test creating A/B test with non-existent screen fails"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = 999
        
        response = client.post("/api/ab-testing/", json=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_all_ab_tests(self, client, created_screen, sample_ab_test_data):
        """Test getting all A/B tests"""
        for i in range(3):
            data = sample_ab_test_data.copy()
            data["name"] = f"Test {i}"
            data["screen_id"] = created_screen["id"]
            client.post("/api/ab-testing/", json=data)
        
        response = client.get("/api/ab-testing/")
        
        assert response.status_code == status.HTTP_200_OK
        tests = response.json()
        assert len(tests) >= 3
    
    def test_get_active_ab_tests(self, client, created_screen, sample_ab_test_data):
        """Test filtering A/B tests by active status"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        data["name"] = "Active Test"
        
        response = client.post("/api/ab-testing/", json=data)
        test = response.json()
        
        client.post(f"/api/ab-testing/{test['id']}/activate")
        
        response = client.get("/api/ab-testing/?is_active=true")
        
        assert response.status_code == status.HTTP_200_OK
        tests = response.json()
        assert all(t["is_active"] for t in tests)
    
    def test_get_ab_test_by_id(self, client, created_screen, sample_ab_test_data):
        """Test getting A/B test by ID"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        create_response = client.post("/api/ab-testing/", json=data)
        test = create_response.json()
        
        response = client.get(f"/api/ab-testing/{test['id']}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == test["id"]
    
    def test_update_ab_test(self, client, created_screen, sample_ab_test_data):
        """Test updating an A/B test"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        create_response = client.post("/api/ab-testing/", json=data)
        test = create_response.json()
        
        update_data = {
            "description": "Updated description",
            "traffic_allocation": 0.7
        }
        
        response = client.put(f"/api/ab-testing/{test['id']}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        updated = response.json()
        assert updated["description"] == "Updated description"
        assert updated["traffic_allocation"] == 0.7
    
    def test_activate_ab_test(self, client, created_screen, sample_ab_test_data):
        """Test activating an A/B test"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        create_response = client.post("/api/ab-testing/", json=data)
        test = create_response.json()
        
        response = client.post(f"/api/ab-testing/{test['id']}/activate")
        
        assert response.status_code == status.HTTP_200_OK
        
        get_response = client.get(f"/api/ab-testing/{test['id']}")
        assert get_response.json()["is_active"] == True
    
    def test_deactivate_ab_test(self, client, created_screen, sample_ab_test_data):
        """Test deactivating an A/B test"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        create_response = client.post("/api/ab-testing/", json=data)
        test = create_response.json()
        
        client.post(f"/api/ab-testing/{test['id']}/activate")
        
        response = client.post(f"/api/ab-testing/{test['id']}/deactivate")
        
        assert response.status_code == status.HTTP_200_OK
        
        get_response = client.get(f"/api/ab-testing/{test['id']}")
        assert get_response.json()["is_active"] == False
    
    def test_delete_ab_test(self, client, created_screen, sample_ab_test_data):
        """Test deleting an A/B test"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        create_response = client.post("/api/ab-testing/", json=data)
        test = create_response.json()
        
        response = client.delete(f"/api/ab-testing/{test['id']}")
        
        assert response.status_code == status.HTTP_200_OK
        
        get_response = client.get(f"/api/ab-testing/{test['id']}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_screen_variant_with_active_test(self, client, created_screen, sample_ab_test_data):
        """Test getting variant for a screen with active A/B test"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        create_response = client.post("/api/ab-testing/", json=data)
        test = create_response.json()
        client.post(f"/api/ab-testing/{test['id']}/activate")
        
        response = client.get(
            f"/api/ab-testing/screen/{created_screen['id']}/variant",
            params={"user_id": "test_user_123", "session_id": "test_session_123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        variant = response.json()
        
        assert "variant" in variant
        assert "config" in variant
        assert "test_id" in variant
        assert variant["variant"] in ["control", "variant_a", "variant_b"]
    
    def test_get_screen_variant_without_active_test(self, client, created_screen):
        """Test getting variant for a screen without active A/B test"""
        response = client.get(
            f"/api/ab-testing/screen/{created_screen['id']}/variant",
            params={"user_id": "test_user_123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        variant = response.json()
        
        assert variant["variant"] == "control"
        assert variant["config"] == created_screen["config"]
        assert variant["test_id"] is None
    
    def test_variant_deterministic_for_same_user(self, client, created_screen, sample_ab_test_data):
        """Test that same user always gets same variant"""
        data = sample_ab_test_data.copy()
        data["screen_id"] = created_screen["id"]
        
        create_response = client.post("/api/ab-testing/", json=data)
        test = create_response.json()
        client.post(f"/api/ab-testing/{test['id']}/activate")
        
        user_id = "consistent_user"
        variants = []
        
        for i in range(5):
            response = client.get(
                f"/api/ab-testing/screen/{created_screen['id']}/variant",
                params={"user_id": user_id, "session_id": f"session_{i}"}
            )
            variant = response.json()
            variants.append(variant["variant"])
        
        assert len(set(variants)) == 1

