from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text

DB_URL = "sqlite:///./fish_tank.db"
engine = create_engine(DB_URL, echo=False)

def init_db():
    from . import models  # noqa: F401
    # Create tables if missing
    SQLModel.metadata.create_all(engine)
    # Ensure runtime DB compatibility: add new columns if they don't exist (SQLite)
    try:
        with engine.begin() as conn:
            # Check columns in the 'view' table
            info = conn.execute(text("PRAGMA table_info('view')")).mappings().all()
            cols = [row.get('name') for row in info] if info else []
            if 'comprehension' not in cols:
                # Add the comprehension column (nullable integer)
                conn.execute(text('ALTER TABLE "view" ADD COLUMN comprehension INTEGER'))
    except Exception:
        # If anything goes wrong here, ignore and let the app continue; errors will surface when accessing missing data.
        pass

def get_session():
    return Session(engine)
