"""
Worker para captura RTSP en background.

Hereda de BaseWorker. Una instancia por camara.
Conecta StreamCapture con Indexer reutilizando el pipeline existente.

Uso:
    worker = StreamWorker(capture, indexer)
    worker.status_updated.connect(panel.update_camera_status)
    worker.start()
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.workers.base_worker import BaseWorker
from core.stream_capture import StreamCapture
from core.indexer import Indexer
from core.logger import logger
from models.camera import CameraStatus


class StreamWorker(BaseWorker):
    """
    QThread para captura RTSP de UNA camara.

    Hereda BaseWorker: try/catch + error signal automatico.
    Solo implementa execute().
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

    def execute(self) -> None:
        """
        Ejecuta el loop de captura.

        Frames de preview se emiten via preview_frame para video en vivo.
        Frames AI cada N segundos pasan al Indexer.process_single_frame()
        que REUTILIZA todo el pipeline: YOLO + CLIP + VLM + ChromaDB.
        """
        camera_id = self._capture.camera.camera_id

        def on_frame(frame_data, frame_image, cam_id):
            """Callback: procesa UN frame con el pipeline existente."""
            if self.is_cancelled:
                self._capture.stop()
                return 0

            count = self._indexer.process_single_frame(
                frame_data=frame_data,
                frame_image=frame_image,
                camera_id=cam_id,
            )
            self.detection_count.emit(cam_id, count)
            return count

        def on_status(status):
            """Callback: actualiza UI con estado de la camara."""
            self.status_updated.emit(status)

        def on_preview(frame_image, cam_id):
            """Callback: emite frame en vivo para mostrar como NVR."""
            if self.is_cancelled:
                return
            self.preview_frame.emit(cam_id, frame_image)

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
