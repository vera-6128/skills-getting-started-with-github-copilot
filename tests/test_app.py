from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert activities["Basketball Club"]["participants"] == []
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant_to_activity(client):
    email = "student@mergington.edu"

    response = client.post(
        "/activities/Basketball Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Basketball Club"
    }
    assert email in client.get("/activities").json()["Basketball Club"]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_unregister_removes_participant_from_activity(client):
    email = "michael@mergington.edu"

    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }
    assert email not in client.get("/activities").json()["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_status", "expected_detail"),
    [
        (
            "Unknown Club",
            "student@mergington.edu",
            404,
            "Activity not found",
        ),
        (
            "Chess Club",
            "student@mergington.edu",
            404,
            "Student is not signed up for this activity",
        ),
    ],
)
def test_unregister_rejects_invalid_request(
    client, activity_name, email, expected_status, expected_detail
):
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail
