"""
BlackScreenDetector — detecta cuando la camara esta cubierta.

Heuristica: brillo medio del frame por debajo de threshold + varianza
muy baja → la lente esta tapada o la imagen es completamente negra.

Implementa BaseTamperDetector.
"""

from __future__ import annotations

import cv2
import numpy as np

from core.tamper.base_tamper_detector import (
    BaseTamperDetector,
    TamperResult,
)
from models.event import EventSeverity


class BlackScreenDetector(BaseTamperDetector):
    """Detecta lente tapada midiendo brillo y varianza."""

    def __init__(
        self,
        brightness_threshold: float = 25.0,
        variance_threshold: float = 30.0,
        enabled: bool = True,
    ) -> None:
        """
        Args:
            brightness_threshold: brillo medio (0-255) por debajo del cual
                se considera "negro".
            variance_threshold: varianza por debajo de la cual se considera
                "uniforme" (tapado vs noche real).
        """
        super().__init__(name="BlackScreen", enabled=enabled)
        self._brightness_threshold = brightness_threshold
        self._variance_threshold = variance_threshold

    def analyze(self, frame_bgr: np.ndarray) -> TamperResult:
        """Calcula brillo medio + varianza del frame."""
        if not self._enabled or frame_bgr is None or frame_bgr.size == 0:
            return TamperResult(triggered=False)

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))
        variance = float(np.var(gray))

        if (
            mean_brightness < self._brightness_threshold
            and variance < self._variance_threshold
        ):
            return TamperResult(
                triggered=True,
                reason="black_screen",
                metric=mean_brightness,
                severity=EventSeverity.CRITICAL,
            )
        return TamperResult(triggered=False, metric=mean_brightness)
