"""
Clase base abstracta para detectores de objetos.

Cualquier detector (YOLO, DETR, etc.) hereda de esta clase
e implementa los métodos abstractos. El ModelManager solo
conoce esta interfaz — nunca la implementación concreta.

Uso:
    from core.detectors.base import BaseDetector
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from models.detection import CropData


class BaseDetector(ABC):
    """Interfaz base para detectores de objetos — patrón Strategy."""

    @abstractmethod
    def load(self, device: str = "cuda") -> None:
        """Carga el modelo en GPU/CPU."""
        ...

    @abstractmethod
    def unload(self) -> None:
        """Libera el modelo de la memoria."""
        ...

    @abstractmethod
    def detect(
        self,
        frame: np.ndarray,
        confidence: float = 0.45,
    ) -> list[CropData]:
        """
        Detecta objetos en un frame y retorna crops.

        Args:
            frame: Imagen BGR como numpy array (OpenCV format).
            confidence: Confianza mínima para aceptar detección.

        Returns:
            Lista de CropData con cada detección encontrada.
        """
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Retorna True si el modelo está cargado en memoria."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo para logging y UI."""
        ...