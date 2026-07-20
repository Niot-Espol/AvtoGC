from __future__ import annotations

import html
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterable
from urllib.parse import urljoin
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from ..config import (
    APP_TIMEZONE,
    CANVAS_REQUEST_TIMEOUT,
    CANVAS_VERIFY_SSL,
    DEFAULT_TASK_DURATION_MINUTES,
)
from ..models import TaskInput


class CanvasAPIError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class CanvasClient:
    def __init__(self, *, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=f"{self.base_url}/",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json+canvas-string-ids",
                "User-Agent": "Proyecto-NIoT-Canvas-Google-Calendar/3.0",
            },
            timeout=CANVAS_REQUEST_TIMEOUT,
            verify=CANVAS_VERIFY_SSL,
            follow_redirects=True,
        )

    @staticmethod
    def _safe_error(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            errors = payload.get("errors")
            if isinstance(errors, list) and errors:
                first = errors[0]
                if isinstance(first, dict):
                    return str(first.get("message") or "Acceso rechazado")
                return str(first)
            if payload.get("message"):
                return str(payload["message"])
        return response.reason_phrase or "Error de Canvas"

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 401:
            raise CanvasAPIError(
                "Canvas rechazó el token. Comprueba que esté completo y siga activo.",
                status_code=401,
            )
        if response.status_code == 403:
            raise CanvasAPIError(
                "El token es válido, pero no tiene permiso para consultar este recurso.",
                status_code=403,
            )
        if response.is_error:
            raise CanvasAPIError(
                f"Canvas respondió {response.status_code}: {self._safe_error(response)}",
                status_code=502,
            )

    def _request_json(
        self,
        path: str,
        params: Iterable[tuple[str, str]] | dict[str, Any] | None = None,
    ) -> Any:
        try:
            with self._client() as client:
                response = client.get(path.lstrip("/"), params=params)
        except httpx.RequestError as exc:
            raise CanvasAPIError(f"No fue posible conectar con Canvas: {exc}") from exc
        self._raise_for_status(response)
        return response.json()

    def _get_paginated(
        self,
        path: str,
        params: Iterable[tuple[str, str]] | dict[str, Any] | None = None,
        max_pages: int = 25,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        next_url: str | None = path.lstrip("/")
        current_params = params
        try:
            with self._client() as client:
                pages = 0
                while next_url and pages < max_pages:
                    response = client.get(next_url, params=current_params)
                    current_params = None
                    pages += 1
                    self._raise_for_status(response)
                    payload = response.json()
                    if not isinstance(payload, list):
                        raise CanvasAPIError("Canvas devolvió un formato inesperado.")
                    items.extend(item for item in payload if isinstance(item, dict))
                    next_link = response.links.get("next")
                    next_url = next_link.get("url") if next_link else None
        except httpx.RequestError as exc:
            raise CanvasAPIError(f"No fue posible conectar con Canvas: {exc}") from exc
        return items

    def get_profile(self) -> dict[str, Any]:
        profile = self._request_json("api/v1/users/self/profile")
        if not isinstance(profile, dict):
            raise CanvasAPIError("Canvas no devolvió un perfil válido.")
        return {
            "id": profile.get("id"),
            "name": profile.get("name") or profile.get("short_name") or "Usuario de Canvas",
            "primary_email": profile.get("primary_email"),
            "time_zone": profile.get("time_zone"),
            "canvas_url": self.base_url,
        }

    def list_courses(self) -> list[dict[str, Any]]:
        params = [
            ("enrollment_state", "active"),
            ("state[]", "available"),
            ("include[]", "term"),
            ("include[]", "course_progress"),
            ("per_page", "100"),
        ]
        courses = self._get_paginated("api/v1/courses", params=params)
        normalized: list[dict[str, Any]] = []
        for course in courses:
            course_id = course.get("id")
            normalized.append(
                {
                    "id": str(course_id),
                    "name": course.get("name")
                    or course.get("course_code")
                    or "Curso sin nombre",
                    "course_code": course.get("course_code"),
                    "workflow_state": course.get("workflow_state"),
                    "start_at": course.get("start_at"),
                    "end_at": course.get("end_at"),
                    "term": (course.get("term") or {}).get("name"),
                    "html_url": urljoin(f"{self.base_url}/", f"courses/{course_id}")
                    if course_id
                    else None,
                }
            )
        return normalized

    def list_planner_items(
        self,
        *,
        start_date: date,
        end_date: date,
        include_completed: bool = False,
    ) -> list[dict[str, Any]]:
        params: list[tuple[str, str]] = [
            ("start_date", start_date.isoformat()),
            ("end_date", (end_date + timedelta(days=1)).isoformat()),
            ("per_page", "100"),
        ]
        if not include_completed:
            params.append(("filter", "incomplete_items"))
        return self._get_paginated("api/v1/planner/items", params=params)

    def list_modules(self, course_id: str) -> list[dict[str, Any]]:
        params = [
            ("include[]", "items"),
            ("include[]", "content_details"),
            ("per_page", "100"),
        ]
        modules = self._get_paginated(
            f"api/v1/courses/{course_id}/modules",
            params=params,
        )
        return [
            {
                "id": str(module.get("id")),
                "name": module.get("name"),
                "state": module.get("state"),
                "unlock_at": module.get("unlock_at"),
                "completed_at": module.get("completed_at"),
                "items_count": module.get("items_count", 0),
                "items": module.get("items") or [],
            }
            for module in modules
        ]

    @staticmethod
    def _parse_datetime(value: Any, timezone_name: str = APP_TIMEZONE) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, date):
            parsed = datetime.combine(value, time(23, 59))
        elif isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return None
            if candidate.endswith("Z"):
                candidate = f"{candidate[:-1]}+00:00"
            try:
                parsed = datetime.fromisoformat(candidate)
            except ValueError:
                try:
                    parsed = datetime.combine(date.fromisoformat(candidate), time(23, 59))
                except ValueError:
                    return None
        else:
            return None
        if parsed.tzinfo is None:
            try:
                parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
            except ZoneInfoNotFoundError:
                parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    @staticmethod
    def _strip_html(value: Any, limit: int = 3500) -> str:
        if not value:
            return ""
        text = re.sub(r"<[^>]+>", " ", str(value))
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:limit]

    @staticmethod
    def _plannable_title(item: dict[str, Any]) -> str:
        plannable = item.get("plannable") or {}
        return str(
            plannable.get("title")
            or plannable.get("name")
            or item.get("title")
            or "Actividad de Canvas"
        )

    def _item_dates(self, item: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
        plannable = item.get("plannable") or {}
        item_type = str(item.get("plannable_type") or "").lower()
        if item_type == "calendar_event":
            start = self._parse_datetime(
                plannable.get("start_at") or item.get("plannable_date")
            )
            end = self._parse_datetime(plannable.get("end_at"))
            if start and not end:
                end = start + timedelta(minutes=DEFAULT_TASK_DURATION_MINUTES)
            return start, end
        due = self._parse_datetime(
            plannable.get("due_at")
            or plannable.get("todo_date")
            or plannable.get("lock_at")
            or item.get("plannable_date")
        )
        if not due:
            return None, None
        return due - timedelta(minutes=DEFAULT_TASK_DURATION_MINUTES), due

    def normalize_planner_item(
        self,
        item: dict[str, Any],
        *,
        course_names: dict[str, str],
        calendar_id: str,
    ) -> TaskInput | None:
        start, end = self._item_dates(item)
        if not start or not end:
            return None
        plannable = item.get("plannable") or {}
        planner_override = item.get("planner_override") or {}
        item_type = str(item.get("plannable_type") or "actividad").lower()
        course_id = str(item.get("course_id") or plannable.get("course_id") or "general")
        course_name = item.get("context_name") or course_names.get(course_id) or "Canvas"
        plannable_id = str(item.get("plannable_id") or plannable.get("id") or "sin-id")
        source_id = f"canvas:{course_id}:{item_type}:{plannable_id}"
        labels = {
            "assignment": "Tarea",
            "sub_assignment": "Subtarea",
            "quiz": "Evaluación",
            "discussion_topic": "Foro",
            "wiki_page": "Lección",
            "announcement": "Anuncio",
            "calendar_event": "Clase/Evento",
            "planner_note": "Nota",
            "assessment_request": "Evaluación por pares",
        }
        type_label = labels.get(item_type, item_type.replace("_", " ").title())
        title = self._plannable_title(item)
        source_url = item.get("html_url") or plannable.get("html_url")
        if source_url and str(source_url).startswith("/"):
            source_url = urljoin(f"{self.base_url}/", str(source_url).lstrip("/"))
        submissions = item.get("submissions") if isinstance(item.get("submissions"), dict) else {}
        status_parts: list[str] = []
        if planner_override.get("marked_complete"):
            status_parts.append("Marcada como completada")
        if submissions.get("missing"):
            status_parts.append("Pendiente/no entregada")
        if submissions.get("late"):
            status_parts.append("Entrega tardía")
        if submissions.get("graded"):
            status_parts.append("Calificada")
        body_text = self._strip_html(
            plannable.get("description")
            or plannable.get("details")
            or plannable.get("message")
            or plannable.get("body")
        )
        description_lines = [
            f"Origen: Canvas — {type_label}",
            f"Curso: {course_name}",
        ]
        if status_parts:
            description_lines.append(f"Estado: {', '.join(status_parts)}")
        if source_url:
            description_lines.append(f"Abrir en Canvas: {source_url}")
        if body_text:
            description_lines.extend(["", body_text])
        modified = self._parse_datetime(
            plannable.get("updated_at")
            or planner_override.get("updated_at")
            or plannable.get("created_at")
            or end
        ) or end
        return TaskInput(
            id_tarea_av=source_id,
            titulo=f"[{course_name}] {type_label}: {title}",
            descripcion="\n".join(description_lines),
            inicio=start,
            fin=end,
            zona_horaria=APP_TIMEZONE,
            ultima_modificacion=modified,
            calendar_id=calendar_id,
            source_type=f"canvas_{item_type}",
            course_name=str(course_name),
            source_url=str(source_url) if source_url else None,
        )

    def collect_tasks(
        self,
        *,
        start_date: date,
        end_date: date,
        calendar_id: str,
        include_completed: bool = False,
    ) -> dict[str, Any]:
        courses = self.list_courses()
        course_names = {str(course["id"]): str(course["name"]) for course in courses}
        raw_items = self.list_planner_items(
            start_date=start_date,
            end_date=end_date,
            include_completed=include_completed,
        )
        tasks: list[TaskInput] = []
        skipped: list[dict[str, Any]] = []
        for item in raw_items:
            task = self.normalize_planner_item(
                item,
                course_names=course_names,
                calendar_id=calendar_id,
            )
            if task:
                tasks.append(task)
            else:
                skipped.append(
                    {
                        "id": item.get("plannable_id"),
                        "type": item.get("plannable_type"),
                        "title": self._plannable_title(item),
                        "reason": "No tiene una fecha utilizable para Google Calendar",
                    }
                )
        tasks.sort(key=lambda task: task.inicio)
        return {
            "courses": courses,
            "raw_count": len(raw_items),
            "tasks": tasks,
            "skipped": skipped,
        }
