from app.models import Base, Note


def test_note_table_columns() -> None:
    assert "notes" in Base.metadata.tables
    columns = Note.__table__.columns.keys()
    assert columns == ["id", "title", "content", "created_at"]
