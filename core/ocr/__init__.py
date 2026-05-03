"""
Sistema de OCR — lectura de texto en imagenes.

Tier 3 — interfaces abstractas listas para implementar.
"""

from core.ocr.base_ocr import BaseOCR, OCRResult
from core.ocr.plate_ocr import PlateOCR

__all__: list[str] = ["BaseOCR", "OCRResult", "PlateOCR"]
