from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import (
    GOOGLE_CLIENT_SECRET_PATH,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    GOOGLE_TOKEN_PATH,
)
from ..database import add_log, get_mapping, save_mapping
from ..models import TaskInput


class GoogleNotConnectedError(RuntimeError):
    pass


class GoogleCredentialsFileError(RuntimeError):
    pass


def create_oauth_flow(state: str | None = None) -> Flow:
    if not GOOGLE_CLIENT_SECRET_PATH.exists():
        raise GoogleCredentialsFileError(
            "Falta backend/credentials/client_secret.json. Descárgalo desde Google Cloud."
        )
    flow = Flow.from_client_secrets_file(
        str(GOOGLE_CLIENT_SECRET_PATH),
        scopes=GOOGLE_SCOPES,
        state=state,
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow


def save_credentials(credentials: Credentials) -> None:
    GOOGLE_TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")


def load_credentials() -> Credentials:
    if not GOOGLE_TOKEN_PATH.exists():
        raise GoogleNotConnectedError("Primero conecta una cuenta de Google Calendar.")
    credentials = Credentials.from_authorized_user_file(
        str(GOOGLE_TOKEN_PATH),
        GOOGLE_SCOPES,
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleAuthRequest())
        save_credentials(credentials)
    if not credentials.valid:
        raise GoogleNotConnectedError(
            "La autorización de Google ya no es válida. Conecta la cuenta nuevamente."
        )
    return credentials


def get_calendar_service():
    return build(
        "calendar",
        "v3",
        credentials=load_credentials(),
        cache_discovery=False,
    )


def remove_saved_token() -> None:
    if GOOGLE_TOKEN_PATH.exists():
        GOOGLE_TOKEN_PATH.unlink()


def list_google_calendars() -> list[dict[str, object]]:
    result = get_calendar_service().calendarList().list().execute()
    return [
        {
            "id": item.get("id"),
            "summary": item.get("summary"),
            "primary": item.get("primary", False),
            "accessRole": item.get("accessRole"),
            "timeZone": item.get("timeZone"),
        }
        for item in result.get("items", [])
        if item.get("accessRole") in {"owner", "writer"}
    ]


def _aware_datetime(value: datetime, timezone_name: str) -> datetime:
    if value.tzinfo is not None:
        return value
    try:
        return value.replace(tzinfo=ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Zona horaria no válida: {timezone_name}") from exc


def _utc_iso(value: datetime, timezone_name: str) -> str:
    return _aware_datetime(value, timezone_name).astimezone(timezone.utc).isoformat()


def _deterministic_event_id(source_id: str) -> str:
    digest = hashlib.sha256(source_id.encode("utf-8")).hexdigest()
    return f"canvas{digest[:48]}"


def _event_body(task: TaskInput, *, include_id: bool = False) -> dict[str, object]:
    start = _aware_datetime(task.inicio, task.zona_horaria)
    end = _aware_datetime(task.fin, task.zona_horaria)
    body: dict[str, object] = {
        "summary": task.titulo,
        "description": task.descripcion,
        "start": {"dateTime": start.isoformat(), "timeZone": task.zona_horaria},
        "end": {"dateTime": end.isoformat(), "timeZone": task.zona_horaria},
        "extendedProperties": {
            "private": {
                "id_tarea_av": task.id_tarea_av,
                "source_type": task.source_type,
                "course_name": task.course_name[:250],
            }
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 60},
                {"method": "popup", "minutes": 1440},
            ],
        },
    }
    if task.source_url:
        body["source"] = {
            "title": "Abrir actividad en Canvas",
            "url": task.source_url,
        }
    if include_id:
        body["id"] = _deterministic_event_id(task.id_tarea_av)
    return body


def _save(task: TaskInput, event: dict[str, object], modified: str) -> None:
    save_mapping(
        id_tarea_av=task.id_tarea_av,
        id_evento_google=str(event["id"]),
        calendar_id=task.calendar_id,
        ultima_modificacion=modified,
        titulo=task.titulo,
        estado="sincronizada",
        event_link=event.get("htmlLink") if isinstance(event.get("htmlLink"), str) else None,
        source_type=task.source_type,
        course_name=task.course_name,
        source_url=task.source_url,
    )


def sync_task(task: TaskInput, service=None) -> dict[str, object]:
    service = service or get_calendar_service()
    mapping = get_mapping(task.id_tarea_av)
    modification_iso = _utc_iso(task.ultima_modificacion, task.zona_horaria)

    if mapping is None:
        body = _event_body(task, include_id=True)
        try:
            event = service.events().insert(
                calendarId=task.calendar_id,
                body=body,
            ).execute()
            action = "insertada"
            detail = "Evento creado en Google Calendar"
        except HttpError as exc:
            if getattr(exc.resp, "status", None) != 409:
                raise
            event_id = str(body["id"])
            event = service.events().update(
                calendarId=task.calendar_id,
                eventId=event_id,
                body=_event_body(task),
            ).execute()
            action = "actualizada"
            detail = "Se recuperó el evento existente sin crear un duplicado"
        _save(task, event, modification_iso)
        add_log(task.id_tarea_av, action, detail)
        return {
            "id_tarea_av": task.id_tarea_av,
            "titulo": task.titulo,
            "accion": action,
            "event_link": event.get("htmlLink"),
        }

    previous = datetime.fromisoformat(mapping["ultima_modificacion"])
    current = datetime.fromisoformat(modification_iso)
    if current <= previous:
        add_log(task.id_tarea_av, "sin_cambios", "La actividad no cambió en Canvas")
        return {
            "id_tarea_av": task.id_tarea_av,
            "titulo": task.titulo,
            "accion": "sin_cambios",
            "event_link": mapping.get("event_link"),
        }

    calendar_id = mapping.get("calendar_id") or task.calendar_id
    event = service.events().update(
        calendarId=calendar_id,
        eventId=mapping["id_evento_google"],
        body=_event_body(task),
    ).execute()
    _save(task.model_copy(update={"calendar_id": calendar_id}), event, modification_iso)
    add_log(task.id_tarea_av, "actualizada", "Evento actualizado desde Canvas")
    return {
        "id_tarea_av": task.id_tarea_av,
        "titulo": task.titulo,
        "accion": "actualizada",
        "event_link": event.get("htmlLink"),
    }
