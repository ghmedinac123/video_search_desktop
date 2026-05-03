"""
Worker para captura RTSP en background.

Hereda de BaseWorker. Una instancia por camara.
Conecta StreamCapture con Indexer reutilizando el pipeline existente.
Dibuja las cajas YOLO sobre cada frame de preview para vista NVR.

Uso:
    worker = StreamWorker(capture, indexer)
    worker.status_updated.connect(panel.update_camera_status)
    worker.preview_frame.connect(panel.update_camera_preview)
    worker.start()
"""

from __future__ import annotations

import cv2
import numpy as np

from PySide6.QtCore import Signal

from ui.workers.base_worker import BaseWorker
from core.stream_capture import StreamCapture
from core.indexer import Indexer
from core.logger import logger
from models.camera import CameraStatus
from models.detection import CropData


# Colores BGR por clase (estilo NVR profesional)
_CLASS_COLORS: dict[str, tuple[int, int, int]] = {
    "person":     (0, 255, 0),      # Verde
    "bicycle":    (255, 200, 0),    # Cyan
    "car":        (0, 200, 255),    # Naranja
    "motorcycle": (0, 200, 255),    # Naranja
    "bus":        (0, 200, 255),    # Naranja
    "truck":      (0, 200, 255),    # Naranja
    "bird":       (0, 255, 255),    # Amarillo
    "cat":        (0, 255, 255),    # Amarillo
    "dog":        (0, 255, 255),    # Amarillo
    "backpack":   (255, 0, 200),    # Magenta
    "handbag":    (255, 0, 200),    # Magenta
    "suitcase":   (255, 0, 200),    # Magenta
}
_DEFAULT_COLOR = (255, 255, 255)


class StreamWorker(BaseWorker):
    """
    QThread para captura RTSP de UNA camara.

    Hereda BaseWorker: try/catch + error signal automatico.
    Cachea las ultimas detecciones YOLO y las pinta en cada frame de
    preview hasta que llegue una nueva (cada interval_seconds).
    """

    status_updated = Signal(object)
    detection_count = Signal(str, int)
    preview_frame = Signal(str, object)

    def __init__(
        self,
        capture: StreamCapture,
        indexer: Indexer,
    ) -> None:
        super().__init__()
        self._capture = capture
        self._indexer = indexer
        self._latest_crops: list[CropData] = []

    def execute(self) -> None:
        """
        Ejecuta el loop de captura.

        Frames de preview se emiten via preview_frame con bboxes pintadas.
        Frames AI cada N segundos pasan al Indexer.process_single_frame()
        que REUTILIZA todo el pipeline: YOLO + CLIP + VLM + ChromaDB.
        """
        camera_id = self._capture.camera.camera_id

        def on_frame(frame_data, frame_image, cam_id):
            """Callback: procesa UN frame con el pipeline existente."""
            if self.is_cancelled:
                self._capture.stop()
                return 0

            crops = self._indexer.process_single_frame(
                frame_data=frame_data,
                frame_image=frame_image,
                camera_id=cam_id,
            )
            # Cachear para dibujar bboxes en proximos previews
            self._latest_crops = crops
            self.detection_count.emit(cam_id, len(crops))
            return len(crops)

        def on_status(status):
            """Callback: actualiza UI con estado de la camara."""
            self.status_updated.emit(status)

        def on_preview(frame_image, cam_id):
            """Callback: dibuja bboxes y emite frame para vista NVR."""
            if self.is_cancelled:
                return
            annotated = self._draw_detections(frame_image, self._latest_crops)
            self.preview_frame.emit(cam_id, annotated)

        self._capture.capture_loop(
            on_frame=on_frame,
            on_status=on_status,
            on_preview=on_preview,
        )

    def cancel(self) -> None:
        """Detiene la captura."""
        super().cancel()
        self._capture.stop()

    @property
    def camera_id(self) -> str:
        """ID de la camara de este worker."""
        return self._capture.camera.camera_id

    @staticmethod
    def _draw_detections(
        frame_bgr: np.ndarray,
        crops: list[CropData],
    ) -> np.ndarray:
        """
        Dibuja las cajas YOLO sobre el frame para vista en vivo.

        Estilo: caja semi-transparente + label "person 0.87" arriba.
        Devuelve una nueva imagen, no muta el frame original.
        """
        if not crops:
            return frame_bgr

        annotated = frame_bgr.copy()
        for crop in crops:
            bbox = crop.bbox
            color = _CLASS_COLORS.get(crop.class_name, _DEFAULT_COLOR)

            # Caja
            cv2.rectangle(
                annotated,
                (bbox.x1, bbox.y1),
                (bbox.x2, bbox.y2),
                color,
                thickness=2,
            )

            # Label arriba de la caja
            label = f"{crop.class_name} {crop.confidence:.2f}"
            (lw, lh), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            ly = max(bbox.y1, lh + 4)
            cv2.rectangle(
                annotated,
                (bbox.x1, ly - lh - 4),
                (bbox.x1 + lw + 6, ly),
                color,
                thickness=-1,
            )
            cv2.putText(
                annotated,
                label,
                (bbox.x1 + 3, ly - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

        return annotated
