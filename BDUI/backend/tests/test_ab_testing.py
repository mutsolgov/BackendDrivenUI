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

