"""
Unit tests for the Mergington High School API.

Tests cover the main endpoints:
- GET /activities
- POST /activities/{activity_name}/signup
"""

import pytest
from fastapi import HTTPException


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify we get a dict of activities
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Verify structure of activities
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_structure(self, client):
        """Test that activities have the expected structure."""
        response = client.get("/activities")
        data = response.json()
        
        # Check that known activities exist
        assert "Chess Club" in data or "Programming Class" in data or "Gym Class" in data
        
        # If Chess Club exists, verify its structure
        if "Chess Club" in data:
            chess = data["Chess Club"]
            assert isinstance(chess["description"], str)
            assert isinstance(chess["schedule"], str)
            assert isinstance(chess["max_participants"], int)
            assert chess["max_participants"] > 0


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client, monkeypatch):
        """Test successful signup for an activity."""
        # Mock the activities to control test state
        test_activities = {
            "Test Activity": {
                "description": "Test",
                "schedule": "Monday",
                "max_participants": 10,
                "participants": []
            }
        }
        
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        import app as app_module
        
        monkeypatch.setattr(app_module, "activities", test_activities)
        
        response = client.post(
            "/activities/Test Activity/signup?email=student@test.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@test.edu" in data["message"]
        assert "Test Activity" in data["message"]
        
        # Verify participant was added
        assert "student@test.edu" in test_activities["Test Activity"]["participants"]

    def test_signup_for_nonexistent_activity_returns_404(self, client, monkeypatch):
        """Test signup returns 404 for non-existent activity."""
        test_activities = {
            "Existing Activity": {
                "description": "Test",
                "schedule": "Monday",
                "max_participants": 10,
                "participants": []
            }
        }
        
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        import app as app_module
        
        monkeypatch.setattr(app_module, "activities", test_activities)
        
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@test.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_duplicate_signup_returns_400(self, client, monkeypatch):
        """Test signup returns 400 when student already signed up."""
        test_activities = {
            "Test Activity": {
                "description": "Test",
                "schedule": "Monday",
                "max_participants": 10,
                "participants": ["student@test.edu"]
            }
        }
        
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        import app as app_module
        
        monkeypatch.setattr(app_module, "activities", test_activities)
        
        response = client.post(
            "/activities/Test Activity/signup?email=student@test.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_multiple_students_same_activity(self, client, monkeypatch):
        """Test that multiple students can sign up for the same activity."""
        test_activities = {
            "Test Activity": {
                "description": "Test",
                "schedule": "Monday",
                "max_participants": 10,
                "participants": []
            }
        }
        
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        import app as app_module
        
        monkeypatch.setattr(app_module, "activities", test_activities)
        
        # First student signup
        response1 = client.post(
            "/activities/Test Activity/signup?email=student1@test.edu"
        )
        assert response1.status_code == 200
        
        # Second student signup
        response2 = client.post(
            "/activities/Test Activity/signup?email=student2@test.edu"
        )
        assert response2.status_code == 200
        
        # Verify both are in participants list
        assert len(test_activities["Test Activity"]["participants"]) == 2
        assert "student1@test.edu" in test_activities["Test Activity"]["participants"]
        assert "student2@test.edu" in test_activities["Test Activity"]["participants"]

    def test_signup_with_special_characters_in_email(self, client, monkeypatch):
        """Test signup with email containing special characters (URL encoded)."""
        test_activities = {
            "Test Activity": {
                "description": "Test",
                "schedule": "Monday",
                "max_participants": 10,
                "participants": []
            }
        }
        
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        import app as app_module
        
        monkeypatch.setattr(app_module, "activities", test_activities)
        
        response = client.post(
            "/activities/Test Activity/signup?email=test%2Bstudent@mergington.edu"
        )
        
        assert response.status_code == 200


class TestActivityData:
    """Tests for activity data validation."""

    def test_all_activities_have_required_fields(self, client):
        """Test that all activities have required fields."""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Activity '{activity_name}' missing field '{field}'"

    def test_participants_list_contains_valid_emails(self, client):
        """Test that participants list contains valid email strings."""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation
