from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Note
from app.schemas import NoteCreate, NoteOut, NoteUpdate

app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/notes", response_model=NoteOut, status_code=201)
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_db)) -> Note:  # noqa: B008
    db_note = Note(title=note.title, content=note.content)
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note


@app.get("/notes", response_model=list[NoteOut])
async def list_notes(db: AsyncSession = Depends(get_db)) -> list[Note]:  # noqa: B008
    result = await db.execute(select(Note).order_by(Note.id))
    return list(result.scalars().all())


@app.get("/notes/{note_id}", response_model=NoteOut)
async def get_note(note_id: int, db: AsyncSession = Depends(get_db)) -> Note:  # noqa: B008
    note = await db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: int, note: NoteUpdate, db: AsyncSession = Depends(get_db)  # noqa: B008
) -> Note:
    db_note = await db.get(Note, note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    db_note.title = note.title
    db_note.content = note.content
    await db.commit()
    await db.refresh(db_note)
    return db_note


@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)) -> None:  # noqa: B008
    db_note = await db.get(Note, note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(db_note)
    await db.commit()
