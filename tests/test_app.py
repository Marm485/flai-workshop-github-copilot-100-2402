"""
Tests for the Mergington High School Activities API
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


INITIAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities database before each test."""
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_all_activities(self, client):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == len(INITIAL_ACTIVITIES)

    def test_activity_has_required_fields(self, client):
        response = client.get("/activities")
        for activity in response.json().values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity

    def test_known_activity_is_present(self, client):
        response = client.get("/activities")
        assert "Chess Club" in response.json()


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

class TestRoot:
    def test_redirects_to_static(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307, 308)
        assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        response = client.post(
            "/activities/Chess Club/signup?email=new@mergington.edu"
        )
        assert response.status_code == 200
        assert "new@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        client.post("/activities/Chess Club/signup?email=new@mergington.edu")
        data = client.get("/activities").json()
        assert "new@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Unknown Activity/signup?email=new@mergington.edu"
        )
        assert response.status_code == 404

    def test_signup_duplicate_returns_400(self, client):
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        response = client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
        data = client.get("/activities").json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]

    def test_unregister_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Unknown Activity/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_non_participant_returns_404(self, client):
        response = client.delete(
            "/activities/Chess Club/signup?email=nothere@mergington.edu"
        )
        assert response.status_code == 404
