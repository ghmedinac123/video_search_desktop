"""
Extractor de frames de video usando OpenCV.

Responsabilidad ÚNICA: abrir un video, extraer frames a intervalos
configurables, guardarlos en disco y retornar metadata tipada.

NO detecta, NO genera embeddings, NO describe. Solo extrae frames.

Uso:
    from core.frame_extractor import FrameExtractor

    extractor = FrameExtractor()
    metadata = extractor.get_video_metadata(Path("cam01.mp4"))
    frames, images = extractor.extract(
        video_path=Path("cam01.mp4"),
        interval=2,
        on_progress=lambda current, total: print(f"{current}/{total}"),
    )
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from core.logger import logger
from models.frame import FrameData
from models.settings import get_settings
from models.video import VideoMetadata


class FrameExtractor:
    """Extrae frames de video a intervalos regulares."""

    def get_video_metadata(self, video_path: Path) -> VideoMetadata:
        """
        Lee metadata de un video sin extraer frames.

        Args:
            video_path: Ruta al archivo de video.

        Returns:
            VideoMetadata con duración, FPS, resolución, etc.

        Raises:
            FileNotFoundError: Si el video no existe.
            ValueError: Si OpenCV no puede abrir el video.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video no encontrado: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"No se puede abrir el video: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            codec_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join(
                chr((codec_int >> 8 * i) & 0xFF) for i in range(4)
            )
            duration = total_frames / fps if fps > 0 else 0.0
            file_size = video_path.stat().st_size / (1024 * 1024)

            return VideoMetadata(
                file_path=video_path.resolve(),
                file_name=video_path.name,
                duration_seconds=duration,
                fps=fps,
                total_frames=total_frames,
                width=width,
                height=height,
                codec=codec.strip(),
                file_size_mb=round(file_size, 1),
            )
        finally:
            cap.release()

    def extract(
        self,
        video_path: Path,
        interval: int | None = None,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> tuple[list[FrameData], list[np.ndarray]]:
        """
        Extrae frames de un video a intervalos regulares.

        Args:
            video_path: Ruta al archivo de video.
            interval: Segundos entre frames. Default: lee de settings.
            on_progress: Callback(frames_extraídos, total_estimado).

        Returns:
            Tupla de (lista FrameData metadata, lista numpy images BGR).
            Se retornan por separado porque numpy arrays no van en Pydantic.

        Raises:
            FileNotFoundError: Si el video no existe.
        """
        settings = get_settings()
        interval = interval or settings.frame_interval

        metadata = self.get_video_metadata(video_path)

        # Preparar directorio de salida para este video
        video_frames_dir = settings.frames_dir / video_path.stem
        video_frames_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        fps = metadata.fps
        skip = max(1, int(fps * interval))
        expected_total = int(metadata.duration_seconds / interval)

        logger.info(
            f"Extrayendo frames: {video_path.name} — "
            f"{metadata.duration_formatted} — {fps:.0f} FPS — "
            f"intervalo {interval}s — ~{expected_total} frames"
        )

        frames: list[FrameData] = []
        images: list[np.ndarray] = []
        frame_number = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_number % skip == 0:
                    timestamp = frame_number / fps
                    idx = len(frames)

                    # Guardar frame en disco
                    frame_filename = f"frame_{idx:06d}_t{int(timestamp):06d}.jpg"
                    frame_path = video_frames_dir / frame_filename
                    cv2.imwrite(str(frame_path), frame)

                    # Crear metadata tipada
                    frame_data = FrameData(
                        frame_index=idx,
                        timestamp_seconds=timestamp,
                        frame_path=frame_path,
                        video_source=video_path.resolve(),
                        width=frame.shape[1],
                        height=frame.shape[0],
                    )

                    frames.append(frame_data)
                    images.append(frame)

                    if on_progress:
                        on_progress(len(frames), expected_total)

                frame_number += 1
        finally:
            cap.release()

        logger.info(f"Extracción completa: {len(frames)} frames de {video_path.name}")
        return frames, images