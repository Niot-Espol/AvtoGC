from __future__ import annotations

from dataclasses import dataclass
from secrets import token_urlsafe
from threading import RLock
from typing import Any


@dataclass(slots=True)
class CanvasCredentials:
    base_url: str
    token: str
    profile: dict[str, Any]


class CanvasCredentialStore:
    """Guarda tokens solo en memoria del servidor.

    El navegador recibe únicamente un identificador aleatorio en una cookie de sesión.
    Reiniciar FastAPI elimina todas las conexiones de Canvas.
    """

    def __init__(self) -> None:
        self._items: dict[str, CanvasCredentials] = {}
        self._lock = RLock()

    def create(self, *, base_url: str, token: str, profile: dict[str, Any]) -> str:
        connection_id = token_urlsafe(32)
        with self._lock:
            self._items[connection_id] = CanvasCredentials(
                base_url=base_url,
                token=token,
                profile=profile,
            )
        return connection_id

    def get(self, connection_id: str | None) -> CanvasCredentials | None:
        if not connection_id:
            return None
        with self._lock:
            return self._items.get(connection_id)

    def delete(self, connection_id: str | None) -> None:
        if not connection_id:
            return
        with self._lock:
            self._items.pop(connection_id, None)


canvas_credentials = CanvasCredentialStore()