import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Test Activity": {
            "description": "A test activity",
            "schedule": "Mondays at 3:00 PM",
            "max_participants": 5,
            "participants": ["existing@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {
        "Test Activity": {
            "description": "A test activity",
            "schedule": "Mondays at 3:00 PM",
            "max_participants": 5,
            "participants": ["existing@example.com"],
        }
    }


def test_signup_adds_student_to_activity(client):
    email = "new@example.com"

    response = client.post(
        "/activities/Test%20Activity/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Test Activity"}
    assert app_module.activities["Test Activity"]["participants"] == [
        "existing@example.com",
        email,
    ]


def test_signup_rejects_duplicate_student(client):
    response = client.post(
        "/activities/Test%20Activity/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_student_from_activity(client):
    email = "existing@example.com"

    response = client.delete(
        "/activities/Test%20Activity/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Test Activity"
    }
    assert app_module.activities["Test Activity"]["participants"] == []


def test_unregister_returns_not_found_for_nonparticipant(client):
    response = client.delete(
        "/activities/Test%20Activity/signup",
        params={"email": "not-signed-up@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}