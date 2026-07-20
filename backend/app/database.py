from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from .config import DATABASE_PATH


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sincronizacion (
                id_tarea_av TEXT PRIMARY KEY,
                id_evento_google TEXT NOT NULL,
                calendar_id TEXT NOT NULL DEFAULT 'primary',
                ultima_modificacion TEXT NOT NULL,
                titulo TEXT NOT NULL,
                estado TEXT NOT NULL,
                event_link TEXT,
                source_type TEXT NOT NULL DEFAULT 'canvas_activity',
                course_name TEXT NOT NULL DEFAULT '',
                source_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_tarea_av TEXT,
                accion TEXT NOT NULL,
                detalle TEXT,
                fecha TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_sync_logs_fecha ON sync_logs(fecha);
            CREATE INDEX IF NOT EXISTS idx_sincronizacion_course ON sincronizacion(course_name);
            """
        )


def get_mapping(id_tarea_av: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM sincronizacion WHERE id_tarea_av = ?",
            (id_tarea_av,),
        ).fetchone()
    return dict(row) if row else None


def save_mapping(
    *,
    id_tarea_av: str,
    id_evento_google: str,
    calendar_id: str,
    ultima_modificacion: str,
    titulo: str,
    estado: str,
    event_link: str | None,
    source_type: str,
    course_name: str,
    source_url: str | None,
) -> None:
    now = utc_now_iso()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO sincronizacion (
                id_tarea_av, id_evento_google, calendar_id,
                ultima_modificacion, titulo, estado, event_link,
                source_type, course_name, source_url, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_tarea_av) DO UPDATE SET
                id_evento_google = excluded.id_evento_google,
                calendar_id = excluded.calendar_id,
                ultima_modificacion = excluded.ultima_modificacion,
                titulo = excluded.titulo,
                estado = excluded.estado,
                event_link = excluded.event_link,
                source_type = excluded.source_type,
                course_name = excluded.course_name,
                source_url = excluded.source_url,
                updated_at = excluded.updated_at
            """,
            (
                id_tarea_av,
                id_evento_google,
                calendar_id,
                ultima_modificacion,
                titulo,
                estado,
                event_link,
                source_type,
                course_name,
                source_url,
                now,
                now,
            ),
        )


def add_log(id_tarea_av: str | None, accion: str, detalle: str = "") -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO sync_logs (id_tarea_av, accion, detalle, fecha) VALUES (?, ?, ?, ?)",
            (id_tarea_av, accion, detalle, utc_now_iso()),
        )


def list_tasks() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM sincronizacion ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_dashboard_stats() -> dict[str, Any]:
    with get_connection() as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS total FROM sincronizacion"
        ).fetchone()["total"]
        grouped = {
            row["accion"]: row["total"]
            for row in connection.execute(
                "SELECT accion, COUNT(*) AS total FROM sync_logs GROUP BY accion"
            ).fetchall()
        }
        last_sync = connection.execute(
            "SELECT MAX(fecha) AS value FROM sync_logs"
        ).fetchone()["value"]
    return {
        "total_tareas": total,
        "insertadas": grouped.get("insertada", 0),
        "actualizadas": grouped.get("actualizada", 0),
        "sin_cambios": grouped.get("sin_cambios", 0),
        "errores": grouped.get("error", 0),
        "ultima_sincronizacion": last_sync,
    }
