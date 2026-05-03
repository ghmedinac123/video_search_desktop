"""
Interfaz abstracta para detectores anti-tamper.

Cada detector analiza un frame y decide si hay sabotaje.
Ejemplos concretos:
- BlackScreenDetector: pantalla negra (lente cubierta)
- SceneChangeDetector: cambio brusco (camara movida)
- BlurDetector (futuro): lente desenfocada deliberadamente

Patron: Strategy. El TamperManager itera sobre todos.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from models.event import EventSeverity


class TamperResult:
    """Resultado de un detector: triggered + razon + metrica + severidad."""

    def __init__(
        self,
        triggered: bool,
        reason: str = "",
        metric: float = 0.0,
        severity: EventSeverity = EventSeverity.WARNING,
    ) -> None:
        self.triggered = triggered
        self.reason = reason
        self.metric = metric
        self.severity = severity


class BaseTamperDetector(ABC):
    """
    Interfaz para detectores anti-tamper.

    Subclases implementan analyze() retornando TamperResult.
    El nombre se usa para logs y eventos.
    """

    def __init__(self, name: str, enabled: bool = True) -> None:
        self._name = name
        self._enabled = enabled

    @property
    def name(self) -> str:
        """Nombre del detector."""
        return self._name

    @property
    def enabled(self) -> bool:
        """True si el detector esta activo."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Activa o desactiva el detector."""
        self._enabled = value

    @abstractmethod
    def analyze(self, frame_bgr: np.ndarray) -> TamperResult:
        """
        Analiza un frame y retorna si hay tamper.

        Args:
            frame_bgr: Imagen BGR del frame actual.

        Returns:
            TamperResult con triggered=True si detecta sabotaje.
        """
        ...
