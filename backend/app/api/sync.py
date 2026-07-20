from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..database import get_dashboard_stats, list_tasks
from ..models import CanvasRangeInput
from ..services.canvas_service import CanvasAPIError
from ..services.google_calendar_service import GoogleNotConnectedError
from ..services.sync_service import sync_tasks
from .canvas import get_canvas_client

router = APIRouter(prefix="/api", tags=["Sincronización"])


@router.post("/preview")
def preview(payload: CanvasRangeInput, request: Request) -> dict[str, object]:
    try:
        collected = get_canvas_client(request).collect_tasks(
            start_date=payload.start_date,
            end_date=payload.end_date,
            calendar_id=payload.calendar_id,
            include_completed=payload.include_completed,
        )
    except CanvasAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return {
        "courses": collected["courses"],
        "raw_count": collected["raw_count"],
        "tasks": [task.model_dump(mode="json") for task in collected["tasks"]],
        "skipped": collected["skipped"],
    }


@router.post("/sync")
def synchronize(payload: CanvasRangeInput, request: Request) -> dict[str, object]:
    try:
        collected = get_canvas_client(request).collect_tasks(
            start_date=payload.start_date,
            end_date=payload.end_date,
            calendar_id=payload.calendar_id,
            include_completed=payload.include_completed,
        )
        result = sync_tasks(collected["tasks"])
        result["raw_count"] = collected["raw_count"]
        result["skipped"] = collected["skipped"]
        return result
    except CanvasAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except GoogleNotConnectedError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/tasks")
def synchronized_tasks() -> dict[str, object]:
    return {"items": list_tasks()}


@router.get("/dashboard-stats")
def dashboard_stats() -> dict[str, object]:
    return get_dashboard_stats()
