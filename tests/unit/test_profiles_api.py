from fastapi.testclient import TestClient


def profile_payload() -> dict[str, list[str]]:
    return {
        "skills": ["Python", "FastAPI"],
        "target_titles": ["Backend Engineer"],
    }


def test_creates_and_gets_profile(client: TestClient) -> None:
    created = client.post("/profiles", json=profile_payload())

    assert created.status_code == 201
    profile = created.json()
    assert profile["id"] == 1
    assert profile["skills"] == ["Python", "FastAPI"]

    fetched = client.get(f"/profiles/{profile['id']}")

    assert fetched.status_code == 200
    assert fetched.json() == profile


def test_updates_profile(client: TestClient) -> None:
    profile = client.post("/profiles", json=profile_payload()).json()

    response = client.put(
        f"/profiles/{profile['id']}",
        json={"skills": ["Python", "FastAPI", "SQLAlchemy"]},
    )

    assert response.status_code == 200
    assert response.json()["skills"] == ["Python", "FastAPI", "SQLAlchemy"]
    assert response.json()["target_titles"] == ["Backend Engineer"]


def test_returns_not_found_for_unknown_profile(client: TestClient) -> None:
    response = client.get("/profiles/999")

    assert response.status_code == 404


def test_rejects_profile_update_without_changes(client: TestClient) -> None:
    response = client.put("/profiles/1", json={})

    assert response.status_code == 422
