from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# SQLite DB file lives in the backend directory regardless of the current
# working directory. This avoids split DBs when running tests from repo root.
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BACKEND_DIR / "infinitywindow.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # needed for SQLite + FastAPI
        "timeout": 60.0,  # Wait up to 60 seconds for database lock
    },
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,  # Maintain a small pool of connections
    max_overflow=10,  # Allow overflow connections
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Wait up to 30 seconds for a connection from pool
    echo=False,  # Set to True for SQL query logging
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Enable SQLite WAL (Write-Ahead Logging) mode for better concurrency.
    This allows multiple readers while a writer is active, reducing lock contention.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=60000")  # 60 second timeout
    cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
