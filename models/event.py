"""
Modelos Pydantic para eventos de seguridad.

Un evento representa CUALQUIER suceso relevante en la plataforma:
- Deteccion AI (persona, vehiculo, etc.)
- Conexion/desconexion de camara
- Tampering detectado (camara cubierta, pantalla negra)
- Notificacion enviada (Telegram)

Patron: enum cerrado de tipos + payload generico para datos
especificos. Permite serializar a JSON y persistir si hace falta.

Uso:
    from models.event import SecurityEvent, EventType, EventSeverity
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Tipos de eventos de seguridad."""

    DETECTION = "detection"
    CAMERA_CONNECTED = "camera_connected"
    CAMERA_DISCONNECTED = "camera_disconnected"
    TAMPER = "tamper"
    NOTIFICATION_SENT = "notification_sent"
    SYSTEM = "system"


class EventSeverity(str, Enum):
    """Nivel de severidad para priorizacion en UI/notificaciones."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SecurityEvent(BaseModel):
    """
    Evento unificado del sistema. Un solo modelo para todos los tipos.

    El campo `payload` lleva datos especificos de cada tipo:
    - DETECTION: {"crop_ids": [...], "classes": [...], "count": N}
    - TAMPER: {"reason": "black_screen", "metric": 0.02}
    - CAMERA_*: {"rtsp_url": "..."}
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    severity: EventSeverity = EventSeverity.INFO
    camera_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    title: str
    message: str = ""
    thumbnail_path: Path | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=False)

    @property
    def timestamp_formatted(self) -> str:
        """Timestamp legible HH:MM:SS."""
        return self.timestamp.strftime("%H:%M:%S")

    @property
    def is_critical(self) -> bool:
        """True si requiere atencion inmediata."""
        return self.severity == EventSeverity.CRITICAL
