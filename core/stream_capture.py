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

    def read_frame(self) -> tuple[FrameData, np.ndarray] | None:
        """
        Lee UN frame de la camara.

        Retorna tupla (FrameData, imagen BGR) o None si falla.
        """
        if self._cap is None or not self._cap.isOpened():
            return None

        ret, frame = self._cap.read()
        if not ret or frame is None:
            return None

        settings = get_settings()
        now = datetime.now()
        timestamp = now.timestamp()

        # Directorio para frames de esta camara
        cam_frames_dir = settings.frames_dir / self._camera.camera_id
        cam_frames_dir.mkdir(parents=True, exist_ok=True)

        # Guardar frame en disco
        frame_filename = (
            f"{self._camera.camera_id}_"
            f"{now.strftime('%Y%m%d_%H%M%S')}_"
            f"{self._frame_count:06d}.jpg"
        )
        frame_path = cam_frames_dir / frame_filename
        cv2.imwrite(str(frame_path), frame)

        self._frame_count += 1

        frame_data = FrameData(
            frame_index=self._frame_count,
            timestamp_seconds=timestamp,
            frame_path=frame_path,
            video_source=Path(self._camera.rtsp_url),
            width=frame.shape[1],
            height=frame.shape[0],
        )

        # Actualizar status
        self._status.frames_captured = self._frame_count
        self._status.last_frame_time = now.strftime("%H:%M:%S")

        return frame_data, frame

    def capture_loop(
        self,
        on_frame: callable | None = None,
        on_status: callable | None = None,
    ) -> None:
        """
        Loop principal de captura. Llamado por StreamWorker.

        Lee un frame cada N segundos (segun camera.interval_seconds).
        Pasa cada frame al callback on_frame para procesamiento.

        Args:
            on_frame: callback(frame_data, frame_image, camera_id)
            on_status: callback(camera_status) para actualizar UI
        """
        if not self.connect():
            return

        self._running = True
        interval = self._camera.interval_seconds
        t0 = time.time()

        logger.info(
            f"[{self._camera.camera_id}] "
            f"Captura iniciada — intervalo: {interval}s"
        )

        while self._running:
            try:
                result = self.read_frame()

                if result is None:
                    # Intentar reconectar
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

                frame_data, frame_image = result

                # Calcular FPS de procesamiento
                elapsed = time.time() - t0
                if elapsed > 0:
                    self._status.fps_processing = round(
                        self._frame_count / elapsed, 1
                    )

                # Pasar frame al pipeline (callback)
                if on_frame:
                    detections = on_frame(
                        frame_data, frame_image, self._camera.camera_id
                    )
                    self._status.detections_total += detections

                self._status.error_message = ""
                if on_status:
                    on_status(self._status)

                # Esperar intervalo
                time.sleep(interval)

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
