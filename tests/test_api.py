"""
Tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestActivitiesEndpoint:
    """Test the /activities endpoint."""
    
    def test_get_activities_success(self, client: TestClient):
        """Test getting all activities successfully."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Verify each activity has required fields
        for activity_name, activity_details in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
            assert isinstance(activity_details["max_participants"], int)
    
    def test_get_activities_contains_expected_activities(self, client: TestClient):
        """Test that the response contains expected activities."""
        response = client.get("/activities")
        data = response.json()
        
        # Verify some expected activities exist
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in data


class TestSignupEndpoint:
    """Test the /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client: TestClient):
        """Test successful signup for an activity."""
        activity_name = "Chess Club"
        email = "new.student@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify the student was actually added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_duplicate_student(self, client: TestClient):
        """Test signup with a student already registered."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client: TestClient):
        """Test signup for a non-existent activity."""
        activity_name = "Non-existent Activity"
        email = "test@mergington.edu"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_signup_url_encoded_activity_name(self, client: TestClient):
        """Test signup with URL-encoded activity name."""
        activity_name = "Chess Club"
        email = "test.encoded@mergington.edu"
        
        # Use URL encoding for spaces
        encoded_activity = "Chess%20Club"
        response = client.post(f"/activities/{encoded_activity}/signup?email={email}")
        
        assert response.status_code == 200
        
        # Verify the student was added to the correct activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]


class TestUnregisterEndpoint:
    """Test the /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client: TestClient):
        """Test successful unregistration from an activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify the student was actually removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]
    
    def test_unregister_student_not_registered(self, client: TestClient):
        """Test unregistration of a student not registered for the activity."""
        activity_name = "Chess Club"
        email = "notregistered@mergington.edu"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity(self, client: TestClient):
        """Test unregistration from a non-existent activity."""
        activity_name = "Non-existent Activity"
        email = "test@mergington.edu"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_unregister_url_encoded_activity_name(self, client: TestClient):
        """Test unregistration with URL-encoded activity name."""
        activity_name = "Chess Club"
        email = "daniel@mergington.edu"  # Already registered
        
        # Use URL encoding for spaces
        encoded_activity = "Chess%20Club"
        response = client.delete(f"/activities/{encoded_activity}/unregister?email={email}")
        
        assert response.status_code == 200
        
        # Verify the student was removed from the correct activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]


class TestRootEndpoint:
    """Test the root endpoint."""
    
    def test_root_redirect(self, client: TestClient):
        """Test that root endpoint redirects to static/index.html."""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_signup_and_unregister_flow(self, client: TestClient):
        """Test complete signup and unregister flow."""
        activity_name = "Programming Class"
        email = "integration.test@mergington.edu"
        
        # Initial state - verify student is not registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        initial_count = len(activities_data[activity_name]["participants"])
        assert email not in activities_data[activity_name]["participants"]
        
        # Step 1: Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup worked
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
        assert len(activities_data[activity_name]["participants"]) == initial_count + 1
        
        # Step 2: Try to sign up again (should fail)
        duplicate_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert duplicate_response.status_code == 400
        
        # Step 3: Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistration worked
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]
        assert len(activities_data[activity_name]["participants"]) == initial_count
        
        # Step 4: Try to unregister again (should fail)
        duplicate_unregister = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert duplicate_unregister.status_code == 400
    
    def test_multiple_activities_signup(self, client: TestClient):
        """Test signing up for multiple activities."""
        email = "multi.activity@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Sign up for multiple activities
        for activity_name in activities_to_join:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify student is in all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity_name in activities_to_join:
            assert email in activities_data[activity_name]["participants"]
        
        # Unregister from one activity
        unregister_response = client.delete(f"/activities/Chess Club/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify student is removed from only that activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        assert email not in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Programming Class"]["participants"]
        assert email in activities_data["Gym Class"]["participants"]