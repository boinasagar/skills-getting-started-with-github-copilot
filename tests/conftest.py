"""
Pytest configuration and fixtures for FastAPI testing.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_activities():
    """Sample activities data for testing."""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        }
    }


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test."""
    from src.app import activities
    # Store original activities
    original_activities = activities.copy()
    
    # Reset to original state after test
    yield
    
    # Restore original activities
    activities.clear()
    activities.update(original_activities)