from fastapi.testclient import TestClient


def create_job(client: TestClient) -> int:
    response = client.post(
        "/jobs/import",
        json={
            "jobs": [
                {
                    "title": "Backend Engineer",
                    "company": "Acme",
                    "url": "https://example.com/jobs/dossier",
                }
            ]
        },
    )
    return response.json()["imported"][0]["id"]


def test_creates_lists_and_updates_job_notes(client: TestClient) -> None:
    job_id = create_job(client)

    created = client.post(f"/jobs/{job_id}/notes", json={"content": "Pesquisar o produto."})

    assert created.status_code == 201
    note = created.json()
    assert note["job_id"] == job_id
    assert note["content"] == "Pesquisar o produto."
    assert note["created_at"]
    assert note["updated_at"]

    listed = client.get(f"/jobs/{job_id}/notes")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [note["id"]]

    updated = client.put(
        f"/jobs/{job_id}/notes/{note['id']}",
        json={"content": "Pesquisar o produto e preparar perguntas."},
    )
    assert updated.status_code == 200
    assert updated.json()["content"] == "Pesquisar o produto e preparar perguntas."


def test_rejects_note_for_unknown_or_different_job(client: TestClient) -> None:
    job_id = create_job(client)
    created = client.post(f"/jobs/{job_id}/notes", json={"content": "Uma nota."}).json()

    assert client.post("/jobs/999/notes", json={"content": "Uma nota."}).status_code == 404
    assert client.put("/jobs/999/notes/1", json={"content": "Outra nota."}).status_code == 404
    assert client.put(
        f"/jobs/{job_id + 1}/notes/{created['id']}",
        json={"content": "Outra nota."},
    ).status_code == 404
