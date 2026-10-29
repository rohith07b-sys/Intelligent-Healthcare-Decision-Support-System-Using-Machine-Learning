import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "local-development-only")
    DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "instance" / "healthcare.db"))
    MODEL_DIR = Path(os.environ.get("MODEL_DIR", BASE_DIR / "artifacts" / "models"))
    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://127.0.0.1:5173")
