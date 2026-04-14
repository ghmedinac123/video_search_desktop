"""
Implementación concreta de detector usando YOLOv11.

Hereda de BaseDetector. El ModelManager no sabe que esto es YOLO,
solo ve la interfaz BaseDetector con .detect(), .load(), .unload().

Uso (via ModelManager, nunca directo):
    detector = YOLODetector(model_path="yolo11m.pt")
    detector.load(device="cuda")
    crops = detector.detect(frame, confidence=0.45)
    detector.unload()
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from core.detectors.base_detector import BaseDetector
from core.logger import logger
from models.detection import BoundingBox, CropData
from models.settings import get_settings


class YOLODetector(BaseDetector):
    """Detector de objetos basado en Ultralytics YOLOv11."""

    def __init__(self, model_path: str = "yolo11m.pt") -> None:
        """
        Args:
            model_path: Nombre del archivo .pt (se auto-descarga).
        """
        self._model_path = model_path
        self._model = None
        self._device: str = "cpu"

    def load(self, device: str = "cuda") -> None:
        """Carga el modelo YOLO en GPU/CPU."""
        from ultralytics import YOLO

        self._device = device
        self._model = YOLO(self._model_path)

        # Warmup: primera inferencia inicializa CUDA kernels
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        self._model(dummy, device=self._device, verbose=False)

        logger.info(f"YOLODetector cargado: {self._model_path} en {device}")

    def unload(self) -> None:
        """Libera el modelo de memoria."""
        if self._model is not None:
            del self._model
            self._model = None
            logger.debug(f"YOLODetector descargado: {self._model_path}")

    def detect(
        self,
        frame: np.ndarray,
        confidence: float = 0.45,
    ) -> list[CropData]:
        """
        Detecta objetos en un frame y retorna crops recortados.

        Args:
            frame: Imagen BGR numpy array.
            confidence: Confianza mínima YOLO.

        Returns:
            Lista de CropData con cada detección.
        """
        if self._model is None:
            raise RuntimeError("YOLODetector no está cargado. Llama .load() primero.")

        settings = get_settings()
        # Solo detectar personas (clase 0) por defecto
        results = self._model(frame, conf=confidence, verbose=False)
        crops: list[CropData] = []
        h, w = frame.shape[:2]

        for det_idx, box in enumerate(results[0].boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            class_name = results[0].names[cls_id]

            # Clases utiles para seguridad (skip muebles/objetos estaticos)
            SECURITY_CLASSES = {
                0: "person",
                1: "bicycle", 2: "car", 3: "motorcycle",
                5: "bus", 7: "truck",
                14: "bird", 15: "cat", 16: "dog",
                24: "backpack", 25: "umbrella",
                26: "handbag", 27: "tie", 28: "suitcase",
            }
            if cls_id not in SECURITY_CLASSES:
                continue

            # Aplicar padding al crop
            pad = settings.crop_padding
            cx1 = max(0, x1 - pad)
            cy1 = max(0, y1 - pad)
            cx2 = min(w, x2 + pad)
            cy2 = min(h, y2 + pad)

            crop_img = frame[cy1:cy2, cx1:cx2]

            # Filtrar crops demasiado pequeños
            if (crop_img.shape[0] < settings.min_crop_size or
                    crop_img.shape[1] < settings.min_crop_size):
                continue

            crops.append(CropData(
                crop_id="",  # Se asigna después en el Indexer
                class_name=class_name,
                confidence=round(conf, 4),
                bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                crop_path=Path("."),  # Se asigna después en el Indexer
                frame_path=Path("."),  # Se asigna después en el Indexer
                video_source=Path("."),  # Se asigna después en el Indexer
                timestamp_seconds=0.0,  # Se asigna después en el Indexer
            ))

        return crops

    def is_loaded(self) -> bool:
        """True si el modelo está en memoria."""
        return self._model is not None

    @property
    def model_name(self) -> str:
        """Nombre para logging y UI."""
        return f"YOLO ({self._model_path})"