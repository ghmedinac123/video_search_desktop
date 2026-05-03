"""
TamperManager — orquesta detectores anti-tamper por camara.

Una instancia POR camara. Mantiene un set de BaseTamperDetector
y ejecuta todos sobre cada frame de AI. Si alguno dispara, publica
un SecurityEvent.TAMPER al EventBus.

Para evitar spam: aplica cooldown entre alertas del mismo tipo.

Uso:
    manager = TamperManager(camera_id="tapo01")
    manager.add_detector(BlackScreenDetector())
    manager.add_detector(SceneChangeDetector())
    manager.analyze(frame_bgr)  # llamado cada frame AI desde Indexer
"""

from __future__ import annotations

import time

from core.events import EventBus
from core.logger import logger
from core.tamper.base_tamper_detector import BaseTamperDetector
from models.event import EventType, SecurityEvent


class TamperManager:
    """Gestor de detectores anti-tamper para UNA camara."""

    DEFAULT_COOLDOWN_SECONDS: float = 30.0

    def __init__(
        self,
        camera_id: str,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
    ) -> None:
        self._camera_id = camera_id
        self._cooldown = cooldown_seconds
        self._detectors: list[BaseTamperDetector] = []
        self._last_alert_per_reason: dict[str, float] = {}
        self._bus = EventBus.get_instance()

    @property
    def camera_id(self) -> str:
        """ID de la camara que monitorea."""
        return self._camera_id

    @property
    def detectors(self) -> list[BaseTamperDetector]:
        """Detectores registrados."""
        return list(self._detectors)

    def add_detector(self, detector: BaseTamperDetector) -> None:
        """Agrega un detector al pipeline de esta camara."""
        self._detectors.append(detector)

    def remove_detector(self, name: str) -> None:
        """Elimina un detector por nombre."""
        self._detectors = [d for d in self._detectors if d.name != name]

    def analyze(self, frame_bgr) -> None:
        """
        Analiza el frame con todos los detectores. Publica TAMPER si aplica.

        Args:
            frame_bgr: Imagen BGR (np.ndarray HxWx3).
        """
        now = time.time()
        for detector in self._detectors:
            if not detector.enabled:
                continue
            result = detector.analyze(frame_bgr)
            if not result.triggered:
                continue

            # Cooldown por razon
            last = self._last_alert_per_reason.get(result.reason, 0.0)
            if (now - last) < self._cooldown:
                continue
            self._last_alert_per_reason[result.reason] = now

            self._publish_tamper_event(result, detector)

    def _publish_tamper_event(
        self, result, detector: BaseTamperDetector
    ) -> None:
        """Publica un SecurityEvent.TAMPER al bus."""
        title_map = {
            "black_screen": "Camara cubierta o sin imagen",
            "scene_change": "Cambio brusco de escena",
        }
        title = title_map.get(result.reason, f"Tamper: {result.reason}")

        event = SecurityEvent(
            event_type=EventType.TAMPER,
            severity=result.severity,
            camera_id=self._camera_id,
            title=title,
            message=(
                f"Detector '{detector.name}' disparo con metrica="
                f"{result.metric:.3f}"
            ),
            payload={
                "reason": result.reason,
                "metric": result.metric,
                "detector": detector.name,
            },
        )
        self._bus.publish(event)
        logger.warning(
            f"[Tamper] {self._camera_id} — {title} "
            f"(detector={detector.name}, metric={result.metric:.3f})"
        )
