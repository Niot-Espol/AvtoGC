from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from googleapiclient.errors import HttpError

from ..config import FRONTEND_URL
from ..services.google_calendar_service import (
    GoogleCredentialsFileError,
    GoogleNotConnectedError,
    create_oauth_flow,
    list_google_calendars,
    load_credentials,
    remove_saved_token,
    save_credentials,
)

router = APIRouter(prefix="/api/google", tags=["Google Calendar"])


@router.get("/login")
def google_login(request: Request):
    try:
        flow = create_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        request.session["oauth_state"] = state
        return RedirectResponse(authorization_url)
    except GoogleCredentialsFileError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/callback")
def google_callback(request: Request):
    state = request.session.get("oauth_state")
    if not state:
        raise HTTPException(status_code=400, detail="Estado OAuth no encontrado.")
    try:
        flow = create_oauth_flow(state=state)
        flow.fetch_token(authorization_response=str(request.url))
        save_credentials(flow.credentials)
        request.session.pop("oauth_state", None)
        return RedirectResponse(f"{FRONTEND_URL}?google=connected")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo completar la conexión con Google: {exc}",
        ) from exc


@router.get("/status")
def google_status() -> dict[str, object]:
    try:
        credentials = load_credentials()
        return {"connected": True, "scopes": credentials.scopes or []}
    except GoogleNotConnectedError:
        return {"connected": False, "scopes": []}


@router.post("/disconnect")
def google_disconnect() -> dict[str, bool]:
    remove_saved_token()
    return {"connected": False}


@router.get("/calendars")
def calendars() -> dict[str, object]:
    try:
        return {"items": list_google_calendars()}
    except GoogleNotConnectedError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except HttpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
