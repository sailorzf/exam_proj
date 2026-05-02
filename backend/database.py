# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL
import bcrypt

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_schema()
    _create_default_admin()


def _migrate_schema():
    """Add new columns/tables if not exists (for existing databases)"""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns("users")]
        for col, col_type in [
            ("is_admin", "BOOLEAN DEFAULT 0"),
            ("name", "VARCHAR"),
            ("gender", "VARCHAR"),
            ("phone", "VARCHAR"),
            ("class_name", "VARCHAR"),
        ]:
            if col not in cols:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                    conn.commit()
    # Create categories table if not exists
    if "categories" not in inspector.get_table_names():
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR NOT NULL UNIQUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
            conn.commit()


def _create_default_admin():
    db = SessionLocal()
    try:
        from models import User
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            pw_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            admin = User(
                username="admin",
                password_hash=pw_hash,
                role="teacher",
                is_admin=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
