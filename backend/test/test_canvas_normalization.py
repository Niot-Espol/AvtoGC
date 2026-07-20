from datetime import date

from app.services.canvas_service import CanvasClient


def test_assignment_is_normalized():
    client = CanvasClient(base_url="https://canvas.example.edu", token="x" * 30)
    item = {
        "course_id": 12,
        "context_name": "Nutrición Clínica",
        "plannable_id": 44,
        "plannable_type": "assignment",
        "plannable_date": "2026-07-25T21:00:00Z",
        "html_url": "/courses/12/assignments/44",
        "plannable": {
            "id": 44,
            "title": "Caso clínico",
            "due_at": "2026-07-25T21:00:00Z",
            "updated_at": "2026-07-20T10:00:00Z",
        },
    }
    task = client.normalize_planner_item(
        item,
        course_names={"12": "Nutrición Clínica"},
        calendar_id="primary",
    )
    assert task is not None
    assert task.id_tarea_av == "canvas:12:assignment:44"
    assert "Caso clínico" in task.titulo
    assert task.source_url == "https://canvas.example.edu/courses/12/assignments/44"


def test_range_is_collected_from_planner(monkeypatch):
    client = CanvasClient(base_url="https://canvas.example.edu", token="x" * 30)
    monkeypatch.setattr(client, "list_courses", lambda: [{"id": "1", "name": "Curso"}])
    monkeypatch.setattr(
        client,
        "list_planner_items",
        lambda **_: [
            {
                "course_id": 1,
                "plannable_id": 2,
                "plannable_type": "quiz",
                "plannable_date": "2026-08-01T12:00:00Z",
                "plannable": {"id": 2, "title": "Lección 1"},
            }
        ],
    )
    result = client.collect_tasks(
        start_date=date(2026, 7, 20),
        end_date=date(2026, 8, 20),
        calendar_id="primary",
    )
    assert result["raw_count"] == 1
    assert len(result["tasks"]) == 1
