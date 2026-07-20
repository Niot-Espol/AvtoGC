from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..models import CanvasConnectionInput
from ..services.canvas_service import CanvasAPIError, CanvasClient
from ..services.credential_store import canvas_credentials

router = APIRouter(prefix="/api/canvas", tags=["Canvas"])


def get_canvas_client(request: Request) -> CanvasClient:
    connection_id = request.session.get("canvas_connection_id")
    credentials = canvas_credentials.get(connection_id)
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Primero ingresa la URL y el token de Canvas en la aplicación web.",
        )
    return CanvasClient(base_url=credentials.base_url, token=credentials.token)


@router.post("/connect")
def connect_canvas(payload: CanvasConnectionInput, request: Request) -> dict[str, object]:
    token = payload.token.get_secret_value().strip()
    client = CanvasClient(base_url=payload.base_url, token=token)
    try:
        profile = client.get_profile()
    except CanvasAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    previous_id = request.session.get("canvas_connection_id")
    canvas_credentials.delete(previous_id)
    connection_id = canvas_credentials.create(
        base_url=payload.base_url,
        token=token,
        profile=profile,
    )
    request.session["canvas_connection_id"] = connection_id
    return {
        "connected": True,
        "profile": profile,
        "storage": "memory_only",
    }


@router.get("/status")
def canvas_status(request: Request) -> dict[str, object]:
    credentials = canvas_credentials.get(request.session.get("canvas_connection_id"))
    if credentials is None:
        return {"connected": False, "profile": None}
    return {
        "connected": True,
        "profile": credentials.profile,
        "base_url": credentials.base_url,
    }


@router.post("/disconnect")
def disconnect_canvas(request: Request) -> dict[str, bool]:
    connection_id = request.session.pop("canvas_connection_id", None)
    canvas_credentials.delete(connection_id)
    return {"connected": False}


@router.get("/courses")
def courses(request: Request) -> dict[str, object]:
    try:
        return {"items": get_canvas_client(request).list_courses()}
    except CanvasAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/courses/{course_id}/modules")
def modules(course_id: str, request: Request) -> dict[str, object]:
    try:
        return {"items": get_canvas_client(request).list_modules(course_id)}
    except CanvasAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
