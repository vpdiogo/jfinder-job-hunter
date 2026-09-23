from fastapi.testclient import TestClient

RESUME_TEXT = """
Experience
Senior Backend Engineer — Acme

Skills
Python, FastAPI, SQLAlchemy

Languages
English, Portuguese

Education
BSc Computer Science — Example University
"""


def test_extracts_resume_without_changing_profiles(client: TestClient) -> None:
    response = client.post("/profiles/resume-extractions", json={"content": RESUME_TEXT})

    assert response.status_code == 201
    extraction = response.json()
    assert extraction["source_content"] == RESUME_TEXT
    assert extraction["draft"]["skills"] == ["Python", "FastAPI", "SQLAlchemy"]
    assert extraction["draft"]["languages"] == ["English", "Portuguese"]
    assert extraction["confirmed_profile_id"] is None
    assert client.get("/profiles").json() == []


def test_confirms_reviewed_resume_data_into_a_new_profile(client: TestClient) -> None:
    extraction = client.post(
        "/profiles/resume-extractions",
        json={"content": RESUME_TEXT},
    ).json()

    response = client.post(
        f"/profiles/resume-extractions/{extraction['id']}/confirm",
        json={
            "profile": {
                "skills": ["Python", "FastAPI"],
                "target_titles": ["Backend Engineer"],
                "languages": ["English"],
                "work_modes": ["remote"],
            },
            "experiences": ["Senior Backend Engineer — Acme"],
            "education": ["BSc Computer Science — Example University"],
        },
    )

    assert response.status_code == 201
    profile = response.json()
    assert profile["skills"] == ["Python", "FastAPI"]
    assert profile["work_modes"] == ["remote"]

    persisted = client.get(f"/profiles/resume-extractions/{extraction['id']}")
    assert persisted.status_code == 200
    assert persisted.json()["confirmed_profile_id"] == profile["id"]
    assert persisted.json()["confirmed_at"] is not None


def test_rejects_confirming_the_same_extraction_twice(client: TestClient) -> None:
    extraction = client.post(
        "/profiles/resume-extractions",
        json={"content": RESUME_TEXT},
    ).json()
    payload = {"profile": {"skills": ["Python"]}}

    assert (
        client.post(
            f"/profiles/resume-extractions/{extraction['id']}/confirm",
            json=payload,
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/profiles/resume-extractions/{extraction['id']}/confirm",
            json=payload,
        ).status_code
        == 409
    )


def test_confirms_reviewed_resume_data_into_an_existing_profile(client: TestClient) -> None:
    profile = client.post(
        "/profiles",
        json={"skills": ["Java"], "target_titles": ["Developer"]},
    ).json()
    extraction = client.post(
        "/profiles/resume-extractions",
        json={"content": RESUME_TEXT},
    ).json()

    response = client.post(
        f"/profiles/resume-extractions/{extraction['id']}/confirm",
        json={
            "profile_id": profile["id"],
            "profile": {"skills": ["Python"], "target_titles": ["Backend Engineer"]},
        },
    )

    assert response.status_code == 201
    assert response.json()["id"] == profile["id"]
    assert response.json()["skills"] == ["Python"]


def test_confirmation_preserves_unreviewed_existing_profile_fields(
    client: TestClient,
) -> None:
    profile = client.post(
        "/profiles",
        json={
            "name": "DevOps Engineer — Cloud",
            "skills": ["Terraform"],
            "languages": ["Portuguese"],
            "work_modes": ["remote"],
        },
    ).json()
    extraction = client.post(
        "/profiles/resume-extractions",
        json={"content": RESUME_TEXT},
    ).json()

    response = client.post(
        f"/profiles/resume-extractions/{extraction['id']}/confirm",
        json={
            "profile_id": profile["id"],
            "profile": {"skills": ["Python"]},
        },
    )

    assert response.status_code == 201
    assert response.json()["skills"] == ["Python"]
    assert response.json()["languages"] == ["Portuguese"]
    assert response.json()["work_modes"] == ["remote"]
