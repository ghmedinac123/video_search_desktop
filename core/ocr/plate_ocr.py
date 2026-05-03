"""
PlateOCR — STUB Tier 3.

Implementacion pendiente con PaddleOCR. Cuando se active:
1. uv add paddleocr paddlepaddle-gpu
2. Descargar modelo de placas (~50 MB)
3. Llenar load() / recognize().

Reglas de validacion: solo aceptar resultados que cumplan formato
de placa local (ej: ABC-123 para Colombia, ABC1234 para LATAM).
"""

from __future__ import annotations

import re

import numpy as np

from core.logger import logger
from core.ocr.base_ocr import BaseOCR, OCRResult


class PlateOCR(BaseOCR):
    """Lector OCR especializado en placas vehiculares."""

    # Patrones de placas comunes en Hispanoamerica
    PLATE_PATTERNS: list[re.Pattern] = [
        re.compile(r"^[A-Z]{3}[-\s]?\d{2,4}$"),
        re.compile(r"^[A-Z]{2}\d{4}$"),
        re.compile(r"^\d{3}[-\s]?[A-Z]{3}$"),
    ]

    def __init__(self, language: str = "es") -> None:
        super().__init__(name="PlateOCR", enabled=False)
        self._language = language

    def load(self) -> None:
        """Cargar PaddleOCR cuando se implemente."""
        logger.info(
            "PlateOCR.load(): NO implementado todavia (Tier 3 stub). "
            "Activar con `uv add paddleocr paddlepaddle-gpu`."
        )
        self._is_loaded = False

    def recognize(self, image_bgr: np.ndarray) -> list[OCRResult]:
        """Procesar imagen y retornar placas validas."""
        if not self._is_loaded or not self._enabled:
            return []
        # TODO: PaddleOCR().ocr(...) + filtrar con _is_valid_plate
        return []

    @classmethod
    def is_valid_plate(cls, text: str) -> bool:
        """Valida si el texto cumple un patron de placa conocido."""
        normalized = text.upper().strip()
        return any(p.match(normalized) for p in cls.PLATE_PATTERNS)
