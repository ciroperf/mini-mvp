import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.cache import _cache_client
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


@pytest.fixture(autouse=True)
def _clear_cache():
    # La cache e' condivisa tra i test (singleton di processo): si riparte sempre vuoti.
    # Funziona sia con il fallback in-memory (test/CI) sia con un vero client Redis.
    if hasattr(_cache_client, "_store"):
        _cache_client._store.clear()
    else:
        asyncio.run(_cache_client.flushdb())
    yield


@pytest.fixture
def query_count():
    count = 0

    def _on_execute(*args, **kwargs):
        nonlocal count
        count += 1

    def _get_count() -> int:
        return count

    event.listen(engine.sync_engine, "before_cursor_execute", _on_execute)
    yield _get_count
    event.remove(engine.sync_engine, "before_cursor_execute", _on_execute)


def _create_note(client: TestClient, title: str = "Title", content: str = "Content") -> dict:
    response = client.post("/notes", json={"title": title, "content": content})
    assert response.status_code == 201
    return response.json()


def test_get_note_second_read_hits_cache(client: TestClient, query_count) -> None:
    created = _create_note(client, "Nota cache", "Contenuto")

    before = query_count()
    first = client.get(f"/notes/{created['id']}")
    assert first.status_code == 200
    after_first = query_count()
    assert after_first > before  # cache miss: ha interrogato Postgres

    second = client.get(f"/notes/{created['id']}")
    assert second.status_code == 200
    assert second.json() == first.json()
    after_second = query_count()
    assert after_second == after_first  # cache hit: nessuna nuova query


def test_list_notes_second_read_hits_cache(client: TestClient, query_count) -> None:
    _create_note(client)

    before = query_count()
    first = client.get("/notes")
    assert first.status_code == 200
    after_first = query_count()
    assert after_first > before

    second = client.get("/notes")
    assert second.status_code == 200
    assert second.json() == first.json()
    after_second = query_count()
    assert after_second == after_first


def test_update_note_invalidates_cache(client: TestClient, query_count) -> None:
    created = _create_note(client, "Vecchio", "Contenuto vecchio")

    cached = client.get(f"/notes/{created['id']}")
    assert cached.json()["title"] == "Vecchio"

    update = client.put(
        f"/notes/{created['id']}",
        json={"title": "Nuovo", "content": "Contenuto nuovo"},
    )
    assert update.status_code == 200

    after_update = query_count()
    response = client.get(f"/notes/{created['id']}")
    assert response.json()["title"] == "Nuovo"
    assert query_count() > after_update  # non e' tornato il valore stantio dalla cache


def test_delete_note_invalidates_cache(client: TestClient) -> None:
    created = _create_note(client)

    client.get(f"/notes/{created['id']}")  # popola la cache

    delete = client.delete(f"/notes/{created['id']}")
    assert delete.status_code == 204

    response = client.get(f"/notes/{created['id']}")
    assert response.status_code == 404
