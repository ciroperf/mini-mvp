import asyncio

import pytest
from fastapi.testclient import TestClient

from app.db import engine
from app.main import app
from app.models import Base


@pytest.fixture(scope="module")
def client():
    async def init_db() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_db())

    with TestClient(app) as test_client:
        yield test_client


def _create_note(client: TestClient, title: str = "Title", content: str = "Content") -> dict:
    response = client.post("/notes", json={"title": title, "content": content})
    assert response.status_code == 201
    return response.json()


def test_create_note(client: TestClient) -> None:
    note = _create_note(client, "Spesa", "Latte e pane")
    assert note["title"] == "Spesa"
    assert note["content"] == "Latte e pane"
    assert "id" in note
    assert "created_at" in note


def test_create_then_get_returns_same_content(client: TestClient) -> None:
    created = _create_note(client, "Promemoria", "Chiamare il dentista")

    response = client.get(f"/notes/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_note_not_found(client: TestClient) -> None:
    response = client.get("/notes/0")
    assert response.status_code == 404


def test_list_notes_includes_created_note(client: TestClient) -> None:
    created = _create_note(client)

    response = client.get("/notes")

    assert response.status_code == 200
    ids = [note["id"] for note in response.json()]
    assert created["id"] in ids


def test_update_note(client: TestClient) -> None:
    created = _create_note(client, "Vecchio titolo", "Vecchio contenuto")

    response = client.put(
        f"/notes/{created['id']}",
        json={"title": "Nuovo titolo", "content": "Nuovo contenuto"},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == created["id"]
    assert updated["title"] == "Nuovo titolo"
    assert updated["content"] == "Nuovo contenuto"


def test_update_note_not_found(client: TestClient) -> None:
    response = client.put("/notes/0", json={"title": "x", "content": "y"})
    assert response.status_code == 404


def test_delete_note(client: TestClient) -> None:
    created = _create_note(client)

    response = client.delete(f"/notes/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/notes/{created['id']}")
    assert response.status_code == 404


def test_delete_note_not_found(client: TestClient) -> None:
    response = client.delete("/notes/0")
    assert response.status_code == 404
