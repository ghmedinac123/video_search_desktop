"""
Interfaz abstracta para notificadores externos.

Cualquier canal (Telegram, email, push, webhook, SMS) implementa
BaseNotifier.send(event). El AlertManager los orquesta sin saber
de detalles especificos de cada canal.

Patron: Strategy + Template Method.

Uso:
    class EmailNotifier(BaseNotifier):
        def send(self, event: SecurityEvent) -> bool:
            ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.event import EventSeverity, SecurityEvent


class BaseNotifier(ABC):
    """
    Notificador abstracto. Subclases implementan canales especificos.

    Atributo `min_severity`: solo se envian eventos con severidad >=.
    """

    SEVERITY_RANK: dict[EventSeverity, int] = {
        EventSeverity.INFO: 0,
        EventSeverity.WARNING: 1,
        EventSeverity.CRITICAL: 2,
    }

    def __init__(
        self,
        name: str,
        min_severity: EventSeverity = EventSeverity.WARNING,
        enabled: bool = True,
    ) -> None:
        self._name = name
        self._min_severity = min_severity
        self._enabled = enabled

    @property
    def name(self) -> str:
        """Nombre del canal."""
        return self._name

    @property
    def enabled(self) -> bool:
        """True si el notificador esta activo."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Activa o desactiva el notificador."""
        self._enabled = value

    @property
    def min_severity(self) -> EventSeverity:
        """Severidad minima para enviar."""
        return self._min_severity

    def should_notify(self, event: SecurityEvent) -> bool:
        """
        Determina si este evento debe ser notificado.

        Filtra por enabled y severidad. Subclases pueden extender
        sobreescribiendo este metodo (Liskov-safe).
        """
        if not self._enabled:
            return False
        return (
            self.SEVERITY_RANK[event.severity]
            >= self.SEVERITY_RANK[self._min_severity]
        )

    def handle(self, event: SecurityEvent) -> bool:
        """
        Template method: filtra y delega a send() si aplica.

        Subclases NO sobreescriben este metodo. Implementan send().
        """
        if not self.should_notify(event):
            return False
        try:
            return self.send(event)
        except Exception as e:
            from core.logger import logger
            logger.error(
                f"[{self._name}] Error enviando notificacion: {e}"
            )
            return False

    @abstractmethod
    def send(self, event: SecurityEvent) -> bool:
        """
        Envia el evento por el canal concreto. Debe implementarse.

        Returns:
            True si se envio exitosamente.
        """
        ...
