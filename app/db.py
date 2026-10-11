import os

from sqlalchemy.ext.asyncio import create_async_engine

# CI/tests might not define DATABASE_URL. Use an in-memory SQLite DB so the app
# can import and the test suite can start without a real database service.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

engine = create_async_engine(DATABASE_URL, pool_size=5)
