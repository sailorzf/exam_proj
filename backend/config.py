# backend/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'exam.db'}"
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "dev-secret-do-not-use-in-prod"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8
