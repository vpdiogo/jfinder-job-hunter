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


def test_lists_profiles(client: TestClient) -> None:
    client.post("/profiles", json=profile_payload())

    response = client.get("/profiles")

    assert response.status_code == 200
    assert response.json()[0]["skills"] == ["Python", "FastAPI"]


def test_persists_enriched_profile_fields(client: TestClient) -> None:
    response = client.post(
        "/profiles",
        json={
            **profile_payload(),
            "desired_seniority": "senior",
            "work_modes": ["remote"],
            "locations": ["Brazil"],
            "timezones": ["America/Sao_Paulo"],
            "salary_min": 120000,
            "salary_max": 180000,
            "languages": ["English"],
            "required_technologies": ["Python"],
            "desired_technologies": ["Docker"],
        },
    )

    assert response.status_code == 201
    assert response.json()["work_modes"] == ["remote"]
    assert response.json()["salary_max"] == 180000


def test_rejects_invalid_profile_salary_range(client: TestClient) -> None:
    response = client.post(
        "/profiles",
        json={"salary_min": 200000, "salary_max": 100000},
    )

    assert response.status_code == 422


def test_allows_clearing_an_enriched_profile_field(client: TestClient) -> None:
    profile = client.post(
        "/profiles",
        json={**profile_payload(), "desired_seniority": "senior"},
    ).json()

    response = client.put(
        f"/profiles/{profile['id']}",
        json={"desired_seniority": None},
    )

    assert response.status_code == 200
    assert response.json()["desired_seniority"] is None


def test_rejects_partial_update_that_invalidates_salary_range(client: TestClient) -> None:
    profile = client.post(
        "/profiles",
        json={
            **profile_payload(),
            "salary_min": 100000,
            "salary_max": 180000,
        },
    ).json()

    response = client.put(
        f"/profiles/{profile['id']}",
        json={"salary_min": 200000},
    )

    assert response.status_code == 422
    assert client.get(f"/profiles/{profile['id']}").json()["salary_min"] == 100000


def test_creates_and_updates_a_named_profile(client: TestClient) -> None:
    profile = client.post(
        "/profiles",
        json={**profile_payload(), "name": "Tech Lead — Plataforma"},
    ).json()

    assert profile["name"] == "Tech Lead — Plataforma"

    response = client.put(
        f"/profiles/{profile['id']}",
        json={"name": "DevOps Engineer — Cloud"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "DevOps Engineer — Cloud"


def test_generates_a_name_for_a_legacy_profile_payload(client: TestClient) -> None:
    response = client.post("/profiles", json=profile_payload())

    assert response.status_code == 201
    assert response.json()["name"] == "Perfil 1"
