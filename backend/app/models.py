from __future__ import annotations

from datetime import date, datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


class CanvasConnectionInput(BaseModel):
    base_url: str = Field(
        min_length=8,
        max_length=500,
        examples=["https://tu-institucion.instructure.com"],
    )
    token: SecretStr = Field(min_length=20, max_length=1000)

    @field_validator("base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        cleaned = value.strip().rstrip("/")
        if cleaned.endswith("/api/v1"):
            cleaned = cleaned[: -len("/api/v1")]
        parsed = urlparse(cleaned)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Ingresa una URL completa, por ejemplo https://campus.ejemplo.edu")
        if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise ValueError("La dirección de Canvas debe usar HTTPS.")
        return cleaned


class CanvasRangeInput(BaseModel):
    start_date: date
    end_date: date
    calendar_id: str = "primary"
    include_completed: bool = False

    @model_validator(mode="after")
    def validate_range(self) -> "CanvasRangeInput":
        if self.end_date < self.start_date:
            raise ValueError("La fecha final no puede ser anterior a la inicial.")
        if (self.end_date - self.start_date).days > 366:
            raise ValueError("El rango máximo permitido es de 366 días.")
        return self


class TaskInput(BaseModel):
    id_tarea_av: str = Field(min_length=1, max_length=240)
    titulo: str = Field(min_length=1, max_length=500)
    descripcion: str = Field(default="", max_length=12000)
    inicio: datetime
    fin: datetime
    zona_horaria: str = "America/Guayaquil"
    ultima_modificacion: datetime
    calendar_id: str = "primary"
    source_type: str = Field(default="canvas_activity", max_length=80)
    course_name: str = Field(default="", max_length=500)
    source_url: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskInput":
        if self.fin <= self.inicio:
            raise ValueError("La fecha de fin debe ser posterior al inicio.")
        return self
