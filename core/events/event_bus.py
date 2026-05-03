"""
EventBus — singleton thread-safe para publicar/suscribir eventos.

Patron Observer/PubSub. Disena la app como event-driven:
- Indexer publica DETECTION cuando hay deteccion
- StreamCapture publica CAMERA_CONNECTED/DISCONNECTED
- TamperDetector publica TAMPER
- UI suscribe → muestra alertas
- TelegramNotifier suscribe → envia mensaje
- EventStore suscribe → persiste

Cero acoplamiento: el publisher NO sabe quien escucha.
Basado en QObject + Signal: cross-thread automatico via Qt::QueuedConnection.

Responsabilidad UNICA: enrutar eventos. NO procesa, NO persiste.

Uso:
    from core.events import EventBus
    from models.event import SecurityEvent, EventType

    bus = EventBus.get_instance()
    bus.subscribe(my_callback)
    bus.publish(SecurityEvent(...))
"""

from __future__ import annotations

import threading
from typing import Callable

from PySide6.QtCore import QObject, Signal

from core.logger import logger
from models.event import SecurityEvent


class EventBus(QObject):
    """
    Singleton Qt-based event bus.

    Cualquier hilo puede publicar; los slots se ejecutan en el hilo
    del receptor automaticamente (QueuedConnection cross-thread).
    """

    event_published = Signal(object)

    _instance: "EventBus | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        super().__init__()
        self._subscribers_count: int = 0

    @classmethod
    def get_instance(cls) -> "EventBus":
        """Retorna la instancia singleton, creandola si es necesario."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = EventBus()
                    logger.info("EventBus inicializado")
        return cls._instance

    def publish(self, event: SecurityEvent) -> None:
        """
        Publica un evento a todos los suscriptores.

        Args:
            event: SecurityEvent a propagar.
        """
        logger.debug(
            f"[EventBus] {event.event_type.value} "
            f"({event.severity.value}) [{event.camera_id}] {event.title}"
        )
        self.event_published.emit(event)

    def subscribe(
        self, callback: Callable[[SecurityEvent], None]
    ) -> None:
        """
        Suscribe un callback que recibira CADA evento.

        Para filtrar por tipo, el callback hace `if event.event_type == ...`.

        Args:
            callback: funcion(event: SecurityEvent) -> None.
        """
        self.event_published.connect(callback)
        self._subscribers_count += 1
        logger.debug(
            f"[EventBus] Nuevo suscriptor (total: {self._subscribers_count})"
        )

    def unsubscribe(
        self, callback: Callable[[SecurityEvent], None]
    ) -> None:
        """Desuscribe un callback. Idempotente."""
        try:
            self.event_published.disconnect(callback)
            self._subscribers_count = max(0, self._subscribers_count - 1)
        except (TypeError, RuntimeError):
            pass

    @property
    def subscriber_count(self) -> int:
        """Cantidad de suscriptores activos."""
        return self._subscribers_count
