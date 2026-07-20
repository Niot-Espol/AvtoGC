from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .api.canvas import router as canvas_router
from .api.google import router as google_router
from .api.sync import router as sync_router
from .config import FRONTEND_URL, SESSION_SECRET
from .database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AVTOGC - Canvas a Google Calendar",
    version="3.0.0",
    description=(
        "Backend local para conectar una cuenta de Canvas mediante token, consultar "
        "actividades académicas y sincronizarlas con Google Calendar sin duplicados."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(canvas_router)
app.include_router(google_router)
app.include_router(sync_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "AVTOGC API activa",
        "docs": "/docs",
        "version": "3.0.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
