"""
Interfaz abstracta para OCR.

Cualquier motor (PaddleOCR, EasyOCR, Tesseract) implementa BaseOCR.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from pydantic import BaseModel, ConfigDict


class OCRResult(BaseModel):
    """Resultado de un OCR: texto + confianza + bbox opcional."""

    text: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None

    model_config = ConfigDict(frozen=True)


class BaseOCR(ABC):
    """Motor OCR abstracto. Subclases implementan recognize()."""

    def __init__(self, name: str, enabled: bool = True) -> None:
        self._name = name
        self._enabled = enabled
        self._is_loaded = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @abstractmethod
    def load(self) -> None:
        """Carga el modelo OCR."""
        ...

    @abstractmethod
    def recognize(self, image_bgr: np.ndarray) -> list[OCRResult]:
        """Procesa imagen y retorna textos detectados."""
        ...
