from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
SESSION_SECRET = os.getenv("SESSION_SECRET", "cambia-esta-clave-en-desarrollo")
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Guayaquil")
CANVAS_REQUEST_TIMEOUT = float(os.getenv("CANVAS_REQUEST_TIMEOUT", "30"))
CANVAS_VERIFY_SSL = os.getenv("CANVAS_VERIFY_SSL", "true").lower() not in {
    "false",
    "0",
    "no",
    "off",
}
DEFAULT_TASK_DURATION_MINUTES = int(
    os.getenv("DEFAULT_TASK_DURATION_MINUTES", "30")
)

DATABASE_PATH = BACKEND_DIR / "data" / "calendar_sync.db"
GOOGLE_CLIENT_SECRET_PATH = BACKEND_DIR / "credentials" / "client_secret.json"
GOOGLE_TOKEN_PATH = BACKEND_DIR / "token.json"
GOOGLE_REDIRECT_URI = f"{BACKEND_URL}/api/google/callback"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]
