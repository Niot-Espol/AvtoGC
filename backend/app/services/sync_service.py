from __future__ import annotations

from typing import Any

from ..database import add_log
from ..models import TaskInput
from .google_calendar_service import get_calendar_service, sync_task


def sync_tasks(tasks: list[TaskInput]) -> dict[str, Any]:
    service = get_calendar_service()
    results: list[dict[str, object]] = []
    counts = {"insertada": 0, "actualizada": 0, "sin_cambios": 0, "error": 0}

    for task in tasks:
        try:
            result = sync_task(task, service=service)
        except Exception as exc:
            add_log(task.id_tarea_av, "error", str(exc))
            result = {
                "id_tarea_av": task.id_tarea_av,
                "titulo": task.titulo,
                "accion": "error",
                "detalle": str(exc),
            }
        action = str(result.get("accion"))
        if action in counts:
            counts[action] += 1
        results.append(result)

    return {"processed": len(tasks), "counts": counts, "results": results}
