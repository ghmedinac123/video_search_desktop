"""
Captura de frames desde camaras RTSP en tiempo real.

Responsabilidad UNICA: conectar a una camara RTSP, leer frames
a intervalos configurables, y pasarlos al pipeline de indexacion.

UNA instancia por camara. Corre en su propio hilo via StreamWorker.
Reutiliza Indexer.process_single_frame() para el pipeline completo.

Uso:
    from core.stream_capture import StreamCapture

    capture = StreamCapture(camera_config, indexer)
    capture.start()   # Inicia captura en loop
    capture.stop()    # Detiene captura
"""

from __future__ import annotations

import time
import threading
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from core.logger import logger
from models.camera import CameraConfig, CameraStatus
from models.frame import FrameData
from models.settings import get_settings

# Silenciar warnings h264 SEI (propietarios de Tapo, no afectan video)
try:
    cv2.setLogLevel(1)  # 0=silent, 1=fatal, 2=error, 3=warning
except AttributeError:
    pass


class StreamCapture:
    """
    Captura frames de UNA camara RTSP.

    Patron: una instancia por camara. El StreamWorker (QThread)
    llama a start() que corre el loop de captura.
    """

    def __init__(self, camera: CameraConfig) -> None:
        self._camera = camera
        self._cap: cv2.VideoCapture | None = None
        self._running = False
        self._status = CameraStatus(camera_id=camera.camera_id)
        self._frame_count = 0
        self._lock = threading.Lock()

    @property
    def camera(self) -> CameraConfig:
        """Config de la camara."""
        return self._camera

    @property
    def status(self) -> CameraStatus:
        """Estado actual en tiempo real."""
        return self._status

    @property
    def is_running(self) -> bool:
        """True si esta capturando."""
        return self._running

    def connect(self) -> bool:
        """
        Conecta a la camara RTSP.

        Retorna True si la conexion fue exitosa.
        """
        try:
            self._cap = cv2.VideoCapture(self._camera.rtsp_url)

            # Timeout de conexion
            if not self._cap.isOpened():
                self._status.connected = False
                self._status.error_message = "No se pudo conectar a la camara"
                logger.error(
                    f"[{self._camera.camera_id}] "
                    f"No se pudo conectar: {self._camera.rtsp_url}"
                )
                return False

            self._status.connected = True
            self._status.error_message = ""
            logger.info(
                f"[{self._camera.camera_id}] "
                f"Conectado a: {self._camera.name}"
            )
            return True

        except Exception as e:
            self._status.connected = False
            self._status.error_message = str(e)
            logger.error(f"[{self._camera.camera_id}] Error: {e}")
            return False

    def disconnect(self) -> None:
        """Desconecta de la camara y libera recursos."""
        self._running = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._status.connected = False
        logger.info(f"[{self._camera.camera_id}] Desconectado")

    def _save_frame(
        self, frame: np.ndarray, now: datetime
    ) -> FrameData:
        """Guarda un frame a disco e incrementa el contador."""
        settings = get_settings()
        cam_frames_dir = settings.frames_dir / self._camera.camera_id
        cam_frames_dir.mkdir(parents=True, exist_ok=True)

        self._frame_count += 1
        frame_filename = (
            f"{self._camera.camera_id}_"
            f"{now.strftime('%Y%m%d_%H%M%S')}_"
            f"{self._frame_count:06d}.jpg"
        )
        frame_path = cam_frames_dir / frame_filename
        cv2.imwrite(str(frame_path), frame)

        self._status.frames_captured = self._frame_count
        self._status.last_frame_time = now.strftime("%H:%M:%S")

        return FrameData(
            frame_index=self._frame_count,
            timestamp_seconds=now.timestamp(),
            frame_path=frame_path,
            video_source=Path(self._camera.rtsp_url),
            width=frame.shape[1],
            height=frame.shape[0],
        )

    def capture_loop(
        self,
        on_frame: callable | None = None,
        on_status: callable | None = None,
        on_preview: callable | None = None,
    ) -> None:
        """
        Loop principal de captura. Llamado por StreamWorker.

        Lee frames continuamente desde la camara para preview en vivo
        (~10 fps en UI). Procesa con AI solo cada `interval_seconds`.

        Args:
            on_frame: callback(frame_data, frame_image, camera_id) — AI pipeline.
            on_status: callback(camera_status) — actualiza stats en UI.
            on_preview: callback(frame_image, camera_id) — frame en vivo
                        para mostrar el video como un NVR.
        """
        if not self.connect():
            return

        self._running = True
        interval = self._camera.interval_seconds
        preview_interval = 1.0 / 10.0  # ~10 fps de preview en UI
        status_interval = 1.0           # status cada 1 seg

        t0 = time.time()
        last_process = 0.0
        last_preview = 0.0
        last_status = 0.0

        logger.info(
            f"[{self._camera.camera_id}] "
            f"Captura iniciada — intervalo AI: {interval}s, preview: 10 fps"
        )

        while self._running:
            try:
                if self._cap is None or not self._cap.isOpened():
                    self.disconnect()
                    time.sleep(2)
                    if not self.connect():
                        break
                    continue

                ret, frame = self._cap.read()
                if not ret or frame is None:
                    logger.warning(
                        f"[{self._camera.camera_id}] Frame perdido, reconectando..."
                    )
                    self._status.error_message = "Reconectando..."
                    if on_status:
                        on_status(self._status)

                    self.disconnect()
                    time.sleep(2)
                    if not self.connect():
                        break
                    continue

                now = time.time()

                # Preview en vivo a ~10 fps
                if on_preview and (now - last_preview) >= preview_interval:
                    last_preview = now
                    on_preview(frame.copy(), self._camera.camera_id)

                # Procesar con AI cada `interval` segundos
                if on_frame and (now - last_process) >= interval:
                    last_process = now
                    frame_data = self._save_frame(frame, datetime.now())
                    detections = on_frame(
                        frame_data, frame, self._camera.camera_id
                    )
                    self._status.detections_total += detections

                # Actualizar status periodicamente
                if (now - last_status) >= status_interval:
                    last_status = now
                    elapsed = now - t0
                    if elapsed > 0:
                        self._status.fps_processing = round(
                            self._frame_count / elapsed, 2
                        )
                    self._status.error_message = ""
                    if on_status:
                        on_status(self._status)

                # Pequeno sleep para no saturar CPU (max ~30 fps de read)
                time.sleep(0.03)

            except Exception as e:
                logger.error(f"[{self._camera.camera_id}] Error en loop: {e}")
                self._status.error_message = str(e)
                if on_status:
                    on_status(self._status)
                time.sleep(2)

        self.disconnect()

    def stop(self) -> None:
        """Detiene el loop de captura."""
        self._running = False
        logger.info(f"[{self._camera.camera_id}] Deteniendo captura...")
