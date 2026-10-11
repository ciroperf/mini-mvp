import json

from fastapi import Depends, FastAPI, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import CACHE_TTL_SECONDS, CacheClient, get_cache
from app.db import get_db
from app.models import Note
from app.observability import metrics_response, observability_middleware, record_cache_result
from app.schemas import NoteCreate, NoteOut, NoteUpdate

app = FastAPI()
app.middleware("http")(observability_middleware)

NOTES_LIST_CACHE_KEY = "notes:list"


def _note_cache_key(note_id: int) -> str:
    return f"notes:{note_id}"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return metrics_response()


@app.post("/notes", response_model=NoteOut, status_code=201)
async def create_note(
    note: NoteCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    cache: CacheClient = Depends(get_cache),  # noqa: B008
) -> Note:
    db_note = Note(title=note.title, content=note.content)
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    await cache.delete(NOTES_LIST_CACHE_KEY)
    return db_note


@app.get("/notes", response_model=list[NoteOut])
async def list_notes(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    cache: CacheClient = Depends(get_cache),  # noqa: B008
) -> list[NoteOut]:
    cached = await cache.get(NOTES_LIST_CACHE_KEY)
    record_cache_result(hit=cached is not None)
    if cached is not None:
        return [NoteOut(**item) for item in json.loads(cached)]

    result = await db.execute(select(Note).order_by(Note.id))
    notes = [NoteOut.model_validate(n) for n in result.scalars().all()]
    await cache.set(
        NOTES_LIST_CACHE_KEY,
        json.dumps([n.model_dump(mode="json") for n in notes]),
        ex=CACHE_TTL_SECONDS,
    )
    return notes


@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    cache: CacheClient = Depends(get_cache),  # noqa: B008
) -> NoteOut:
    cache_key = _note_cache_key(note_id)
    cached = await cache.get(cache_key)
    record_cache_result(hit=cached is not None)
    if cached is not None:
        return NoteOut(**json.loads(cached))

    note = await db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    note_out = NoteOut.model_validate(note)
    await cache.set(cache_key, note_out.model_dump_json(), ex=CACHE_TTL_SECONDS)
    return note_out


@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: int,
    note: NoteUpdate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    cache: CacheClient = Depends(get_cache),  # noqa: B008
) -> Note:
    db_note = await db.get(Note, note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    db_note.title = note.title
    db_note.content = note.content
    await db.commit()
    await db.refresh(db_note)
    await cache.delete(_note_cache_key(note_id), NOTES_LIST_CACHE_KEY)
    return db_note


@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    cache: CacheClient = Depends(get_cache),  # noqa: B008
) -> None:
    db_note = await db.get(Note, note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(db_note)
    await db.commit()
    await cache.delete(_note_cache_key(note_id), NOTES_LIST_CACHE_KEY)
