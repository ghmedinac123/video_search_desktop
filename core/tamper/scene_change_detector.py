"""
SceneChangeDetector — detecta movimiento brusco de la camara.

Heuristica: si el histograma del frame difiere mucho del histograma
de referencia (varios frames atras), la camara fue movida.

Implementa BaseTamperDetector. Mantiene estado interno (histograma anterior).
"""

from __future__ import annotations

import cv2
import numpy as np

from core.tamper.base_tamper_detector import (
    BaseTamperDetector,
    TamperResult,
)
from models.event import EventSeverity


class SceneChangeDetector(BaseTamperDetector):
    """Detecta cambio brusco de escena (camara movida o redirigida)."""

    def __init__(
        self,
        change_threshold: float = 0.65,
        enabled: bool = True,
    ) -> None:
        """
        Args:
            change_threshold: distancia minima de Bhattacharyya entre
                histogramas para considerar cambio (0=identico, 1=opuesto).
        """
        super().__init__(name="SceneChange", enabled=enabled)
        self._change_threshold = change_threshold
        self._reference_hist: np.ndarray | None = None
        self._frames_since_ref: int = 0

    def analyze(self, frame_bgr: np.ndarray) -> TamperResult:
        """Compara histograma actual con la referencia."""
        if not self._enabled or frame_bgr is None or frame_bgr.size == 0:
            return TamperResult(triggered=False)

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

        if self._reference_hist is None:
            self._reference_hist = hist
            return TamperResult(triggered=False)

        # Distancia Bhattacharyya: 0 = identico, 1 = opuesto
        distance = float(cv2.compareHist(
            self._reference_hist, hist, cv2.HISTCMP_BHATTACHARYYA
        ))

        self._frames_since_ref += 1

        # Refrescar referencia cada 20 analisis para tolerar drift natural
        if self._frames_since_ref >= 20:
            self._reference_hist = hist
            self._frames_since_ref = 0

        if distance >= self._change_threshold:
            self._reference_hist = hist  # actualizar tras alerta
            self._frames_since_ref = 0
            return TamperResult(
                triggered=True,
                reason="scene_change",
                metric=distance,
                severity=EventSeverity.WARNING,
            )

        return TamperResult(triggered=False, metric=distance)
