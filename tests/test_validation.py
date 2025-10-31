"""
Tests for data validation and edge cases.
"""
from fastapi.testclient import TestClient
from urllib.parse import quote


class TestDataValidation:
    """Test data validation and edge cases."""
    
    def test_signup_with_special_characters_in_email(self, client: TestClient):
        """Test signup with special characters in email."""
        activity_name = "Chess Club"
        # Email with special characters that should be URL encoded
        email = "test+user@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={quote(email)}")
        
        assert response.status_code == 200
        
        # Verify the student was added with correct email
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_activity_name_with_special_characters(self, client: TestClient):
        """Test with activity names containing special characters."""
        # Use an existing activity name with spaces
        activity_name = "Chess Club"
        email = "test@mergington.edu"
        
        # Test with URL encoding
        encoded_name = quote(activity_name)
        response = client.post(f"/activities/{encoded_name}/signup?email={email}")
        
        assert response.status_code == 200
    
    def test_empty_email_parameter(self, client: TestClient):
        """Test with empty email parameter."""
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email=")
        
        # Should still return 200 but with empty email
        assert response.status_code == 200
        
        # Verify empty email was added (this might be a bug to fix later)
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "" in activities_data[activity_name]["participants"]
    
    def test_missing_email_parameter(self, client: TestClient):
        """Test with missing email parameter."""
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup")
        
        # FastAPI should return 422 for missing required parameter
        assert response.status_code == 422
    
    def test_case_sensitive_activity_names(self, client: TestClient):
        """Test that activity names are case sensitive."""
        email = "case.test@mergington.edu"
        
        # Test with incorrect case
        response = client.post("/activities/chess%20club/signup?email=" + email)
        assert response.status_code == 404
        
        # Test with correct case
        response = client.post("/activities/Chess%20Club/signup?email=" + email)
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_malformed_request_url(self, client: TestClient):
        """Test with malformed request URL."""
        # Test with invalid URL encoding
        response = client.post("/activities/%/signup?email=test@mergington.edu")
        
        # Should handle gracefully
        assert response.status_code in [400, 404, 422]
    
    def test_very_long_activity_name(self, client: TestClient):
        """Test with very long activity name."""
        long_name = "A" * 1000  # Very long activity name
        email = "test@mergington.edu"
        
        response = client.post(f"/activities/{long_name}/signup?email={email}")
        
        assert response.status_code == 404  # Activity doesn't exist
    
    def test_very_long_email(self, client: TestClient):
        """Test with very long email."""
        activity_name = "Chess Club"
        long_email = "a" * 500 + "@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={long_email}")
        
        # Should handle gracefully (though might not be valid email)
        assert response.status_code == 200


class TestDataConsistency:
    """Test data consistency across operations."""
    
    def test_participant_count_consistency(self, client: TestClient):
        """Test that participant counts remain consistent."""
        activity_name = "Chess Club"
        
        # Get initial state
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        initial_count = len(initial_data[activity_name]["participants"])
        
        test_emails = [
            "test1@mergington.edu",
            "test2@mergington.edu", 
            "test3@mergington.edu"
        ]
        
        # Add multiple participants
        for email in test_emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify count increased correctly
        after_signup_response = client.get("/activities")
        after_signup_data = after_signup_response.json()
        after_signup_count = len(after_signup_data[activity_name]["participants"])
        assert after_signup_count == initial_count + len(test_emails)
        
        # Remove participants
        for email in test_emails:
            response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
            assert response.status_code == 200
        
        # Verify count returned to initial state
        final_response = client.get("/activities")
        final_data = final_response.json()
        final_count = len(final_data[activity_name]["participants"])
        assert final_count == initial_count
    
    def test_concurrent_operations_simulation(self, client: TestClient):
        """Simulate concurrent operations to test data consistency."""
        activity_name = "Programming Class"
        base_email = "concurrent.test"
        domain = "@mergington.edu"
        
        # Simulate multiple signups
        emails = [f"{base_email}{i}{domain}" for i in range(5)]
        
        for email in emails:
            signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert signup_response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for email in emails:
            assert email in activities_data[activity_name]["participants"]
        
        # Remove some participants
        emails_to_remove = emails[:3]
        for email in emails_to_remove:
            unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
            assert unregister_response.status_code == 200
        
        # Verify correct participants remain
        final_response = client.get("/activities")
        final_data = final_response.json()
        
        for email in emails_to_remove:
            assert email not in final_data[activity_name]["participants"]
        
        for email in emails[3:]:  # Remaining emails
            assert email in final_data[activity_name]["participants"]