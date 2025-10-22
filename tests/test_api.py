"""
Test cases for the High School Management System API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Test cases for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Test cases for the activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Check that we have the expected activities
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Soccer Team",
            "Basketball Team", "Art Club", "Drama Society", "Debate Club", "Math Olympiad"
        ]
        
        for activity_name in expected_activities:
            assert activity_name in data
            
        # Verify structure of activity data
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        
    def test_get_activities_has_correct_initial_participants(self, client, reset_activities):
        """Test that activities have the correct initial participants."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have 2 participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        
        # Programming Class should have 2 participants
        assert len(data["Programming Class"]["participants"]) == 2
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
        assert "sophia@mergington.edu" in data["Programming Class"]["participants"]
        
        # Soccer Team should have no participants initially
        assert len(data["Soccer Team"]["participants"]) == 0


class TestSignupEndpoint:
    """Test cases for the activity signup endpoint."""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        email = "newstudent@mergington.edu"
        activity = "Soccer Team"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist."""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test that duplicate signup is rejected."""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_with_special_characters_in_activity_name(self, client, reset_activities):
        """Test signup with URL encoding for activity names."""
        email = "student@mergington.edu"
        activity = "Math Olympiad"  # Contains space
        
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
    
    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signup with special characters in email."""
        from urllib.parse import quote
        
        email = "test+student@mergington.edu"
        activity = "Art Club"
        
        # Properly encode the email for URL
        encoded_email = quote(email)
        response = client.post(f"/activities/{activity}/signup?email={encoded_email}")
        assert response.status_code == 200
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client, reset_activities):
        """Test that the same student can sign up for multiple different activities."""
        email = "multisport@mergington.edu"
        activities_to_join = ["Soccer Team", "Basketball Team", "Drama Society"]
        
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify the participant was added to all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity in activities_to_join:
            assert email in activities_data[activity]["participants"]
    
    def test_signup_maintains_activity_capacity_constraints(self, client, reset_activities):
        """Test that signup works within activity capacity constraints."""
        # Get an activity with available spots
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        activity = "Soccer Team"
        max_participants = activities_data[activity]["max_participants"]
        current_participants = len(activities_data[activity]["participants"])
        available_spots = max_participants - current_participants
        
        # Sign up students up to the limit
        for i in range(available_spots):
            email = f"student{i}@mergington.edu"
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all participants were added
        final_response = client.get("/activities")
        final_data = final_response.json()
        assert len(final_data[activity]["participants"]) == max_participants


class TestAPIIntegration:
    """Integration tests for the complete API workflow."""
    
    def test_complete_signup_workflow(self, client, reset_activities):
        """Test a complete workflow: get activities, then sign up."""
        # Step 1: Get all activities
        activities_response = client.get("/activities")
        assert activities_response.status_code == 200
        activities_data = activities_response.json()
        
        # Step 2: Choose an activity with available spots
        activity_name = "Debate Club"
        activity_data = activities_data[activity_name]
        initial_participants = len(activity_data["participants"])
        
        # Step 3: Sign up for the activity
        email = "debater@mergington.edu"
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Step 4: Verify the change is reflected in activities
        updated_response = client.get("/activities")
        updated_data = updated_response.json()
        
        assert len(updated_data[activity_name]["participants"]) == initial_participants + 1
        assert email in updated_data[activity_name]["participants"]