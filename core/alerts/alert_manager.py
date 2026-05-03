"""
AlertManager — orquesta TODOS los notificadores registrados.

Suscriptor del EventBus. Recibe cada SecurityEvent y lo distribuye
a cada BaseNotifier registrado. Cada notificador decide si lo maneja
segun su filtro de severidad.

Patron: Mediator + Observer.

Uso:
    manager = AlertManager.get_instance()
    manager.register(TelegramNotifier())
    manager.register(EmailNotifier())  # cuando exista
"""

from __future__ import annotations

import threading

from core.alerts.base_notifier import BaseNotifier
from core.events import EventBus
from core.logger import logger
from models.event import SecurityEvent


class AlertManager:
    """
    Singleton que distribuye eventos a notificadores registrados.

    Notificadores se ejecutan en threads aparte para no bloquear
    el EventBus (Telegram puede tardar varios segundos en HTTP).
    """

    _instance: "AlertManager | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._notifiers: list[BaseNotifier] = []
        self._dispatch_lock = threading.Lock()
        self._bus = EventBus.get_instance()
        self._bus.subscribe(self._on_event)
        logger.info("AlertManager inicializado")

    @classmethod
    def get_instance(cls) -> "AlertManager":
        """Retorna la instancia singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = AlertManager()
        return cls._instance

    def register(self, notifier: BaseNotifier) -> None:
        """Agrega un notificador al pipeline."""
        with self._dispatch_lock:
            self._notifiers.append(notifier)
        logger.info(
            f"AlertManager: notifier '{notifier.name}' registrado "
            f"(enabled={notifier.enabled}, "
            f"min_severity={notifier.min_severity.value})"
        )

    def unregister(self, notifier: BaseNotifier) -> None:
        """Quita un notificador del pipeline."""
        with self._dispatch_lock:
            if notifier in self._notifiers:
                self._notifiers.remove(notifier)

    @property
    def notifiers(self) -> list[BaseNotifier]:
        """Lista de notificadores registrados."""
        return list(self._notifiers)

    def _on_event(self, event: SecurityEvent) -> None:
        """Distribuye el evento a cada notificador en thread separado."""
        with self._dispatch_lock:
            notifiers = list(self._notifiers)

        for notifier in notifiers:
            if not notifier.should_notify(event):
                continue
            # Lanzar en thread separado para no bloquear el bus
            t = threading.Thread(
                target=notifier.handle,
                args=(event,),
                daemon=True,
                name=f"notifier-{notifier.name}",
            )
            t.start()
