"""
Pipeline de indexación: Video → Frames → Detect → Embed → Describe → Store.

Responsabilidad ÚNICA: orquestar el pipeline paso a paso.
NO ejecuta detección ni embeddings directamente — los delega
a los componentes que recibe por inyección de dependencias.

Soporta: pausar, reanudar, cancelar. Emite progreso via callback
para que la UI actualice las barras en tiempo real.

Uso:
    from core.indexer import Indexer

    indexer = Indexer(model_manager=mm, database=db, settings=settings)
    result = indexer.index_video(
        video_path=Path("cam01.mp4"),
        on_progress=lambda p: print(p.stage, p.frames_processed),
    )
"""

from __future__ import annotations

import time
import threading
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from core.database import Database
from core.events import EventBus
from core.frame_extractor import FrameExtractor
from core.logger import logger
from core.model_manager import ModelManager
from core.tamper import (
    BlackScreenDetector,
    SceneChangeDetector,
    TamperManager,
)
from models.detection import BoundingBox, CropData
from models.event import EventSeverity, EventType, SecurityEvent
from models.frame import FrameData
from models.indexing import IndexProgress, IndexResult, IndexStage
from models.settings import AppSettings, get_settings


class Indexer:
    """
    Orquestador del pipeline de indexación.

    Recibe dependencias por constructor (Dependency Inversion).
    NO sabe qué modelo concreto se está usando — solo llama
    las interfaces: detector.detect(), embedder.embed_image(), etc.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        database: Database,
        settings: AppSettings | None = None,
    ) -> None:
        self._mm = model_manager
        self._db = database
        self._settings = settings or get_settings()
        self._frame_extractor = FrameExtractor()

        # Control de flujo
        self._is_running = False
        self._is_paused = False
        self._is_cancelled = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # No pausado inicialmente

        # Lock para serializar acceso a la GPU desde multiples streams RTSP
        self._gpu_lock = threading.Lock()

        # Bus de eventos para publicar detecciones (Observer pattern)
        self._event_bus = EventBus.get_instance()

        # TamperManager por camara (lazy: se crea en el primer frame)
        self._tamper_managers: dict[str, TamperManager] = {}

    def index_video(
        self,
        video_path: Path,
        interval: int | None = None,
        on_progress: Callable[[IndexProgress], None] | None = None,
    ) -> IndexResult:
        """
        Ejecuta el pipeline completo para un video.

        Args:
            video_path: Ruta al video MP4/AVI/MKV.
            interval: Segundos entre frames (override de settings).
            on_progress: Callback que recibe IndexProgress cada frame.

        Returns:
            IndexResult con totales y estadísticas.
        """
        if not self._mm.is_ready():
            raise RuntimeError(
                "ModelManager no está listo. Carga detector + embedder primero."
            )

        self._is_running = True
        self._is_cancelled = False
        self._is_paused = False
        self._pause_event.set()

        interval = interval or self._settings.frame_interval
        t0 = time.time()
        total_detections = 0
        total_stored = 0

        progress = IndexProgress(stage=IndexStage.EXTRACTING_FRAMES)
        self._emit_progress(progress, on_progress)

        # ── Paso 1: Extraer frames ──
        logger.info(f"[Pipeline] Paso 1/4: Extrayendo frames de {video_path.name}")

        def frame_progress(current: int, total: int) -> None:
            progress.frames_processed = current
            progress.frames_total = total
            self._emit_progress(progress, on_progress)

        frames, images = self._frame_extractor.extract(
            video_path=video_path,
            interval=interval,
            on_progress=frame_progress,
        )

        progress.frames_total = len(frames)
        progress.stage = IndexStage.DETECTING

        # Preparar directorio de crops
        crops_dir = self._settings.crops_dir / video_path.stem
        crops_dir.mkdir(parents=True, exist_ok=True)

        # ── Paso 2-4: Procesar cada frame ──
        logger.info(f"[Pipeline] Pasos 2-4: Detect → Embed → Describe → Store")

        for i, (frame_data, frame_image) in enumerate(zip(frames, images)):
            # Verificar cancelación
            if self._is_cancelled:
                logger.warning("[Pipeline] Cancelado por el usuario")
                progress.stage = IndexStage.CANCELLED
                self._emit_progress(progress, on_progress)
                break

            # Esperar si está pausado
            self._pause_event.wait()

            # ── Detectar ──
            progress.stage = IndexStage.DETECTING
            raw_crops = self._mm.detector.detect(
                frame_image,
                confidence=self._settings.yolo_confidence,
            )
            total_detections += len(raw_crops)
            progress.detections_total = total_detections

            for det_idx, crop_data in enumerate(raw_crops):
                if self._is_cancelled:
                    break

                # Completar metadata del crop
                crop_id = (
                    f"{video_path.stem}__"
                    f"f{frame_data.frame_index:06d}__"
                    f"d{det_idx:03d}"
                )
                crop_data.crop_id = crop_id
                crop_data.frame_path = frame_data.frame_path
                crop_data.video_source = video_path.resolve()
                crop_data.timestamp_seconds = frame_data.timestamp_seconds

                # Recortar imagen del crop
                bbox = crop_data.bbox
                pad = self._settings.crop_padding
                h, w = frame_image.shape[:2]
                cx1 = max(0, bbox.x1 - pad)
                cy1 = max(0, bbox.y1 - pad)
                cx2 = min(w, bbox.x2 + pad)
                cy2 = min(h, bbox.y2 + pad)
                crop_image = frame_image[cy1:cy2, cx1:cx2]

                # Guardar crop en disco
                crop_filename = (
                    f"f{frame_data.frame_index:06d}_"
                    f"d{det_idx:03d}_{crop_data.class_name}.jpg"
                )
                crop_path = crops_dir / crop_filename
                cv2.imwrite(str(crop_path), crop_image)
                crop_data.crop_path = crop_path

                # ── Embed ──
                progress.stage = IndexStage.EMBEDDING
                embedding = self._mm.embedder.embed_image(crop_image)

                # ── Describe (opcional) ──
                description = ""
                if self._mm.describer is not None and self._mm.describer.is_loaded():
                    progress.stage = IndexStage.DESCRIBING
                    description = self._mm.describer.describe(crop_image)
                    crop_data.description = description

                # ── Store ──
                progress.stage = IndexStage.STORING
                self._db.store(
                    crop_id=crop_id,
                    embedding=embedding,
                    metadata={
                        "class_name": crop_data.class_name,
                        "confidence": crop_data.confidence,
                        "timestamp_seconds": crop_data.timestamp_seconds,
                        "video_source": str(crop_data.video_source),
                        "frame_path": str(crop_data.frame_path),
                        "crop_path": str(crop_data.crop_path),
                        "bbox": f"[{bbox.x1},{bbox.y1},{bbox.x2},{bbox.y2}]",
                        "description": description,
                    },
                    description=description,
                )
                total_stored += 1
                progress.crops_stored = total_stored
                progress.detections_processed += 1

            # Actualizar progreso por frame
            progress.frames_processed = i + 1
            elapsed = time.time() - t0
            progress.elapsed_seconds = elapsed
            progress.fps_processing = (i + 1) / max(elapsed, 0.001)

            remaining_frames = len(frames) - (i + 1)
            if progress.fps_processing > 0:
                progress.estimated_remaining_seconds = (
                    remaining_frames / progress.fps_processing
                )

            progress.current_frame_path = str(frame_data.frame_path)
            self._emit_progress(progress, on_progress)

            # Liberar imagen para no acumular memoria
            images[i] = None

        # ── Resultado final ──
        elapsed = time.time() - t0
        self._is_running = False

        if not self._is_cancelled:
            progress.stage = IndexStage.COMPLETED
            self._emit_progress(progress, on_progress)

        result = IndexResult(
            video_source=str(video_path),
            total_frames=len(frames),
            total_detections=total_detections,
            total_stored=total_stored,
            elapsed_seconds=round(elapsed, 1),
            fps_processing=round(len(frames) / max(elapsed, 0.001), 1),
            collection_total=self._db.count,
        )

        logger.info(
            f"[Pipeline] Completo: {result.total_frames} frames, "
            f"{result.total_detections} detecciones, "
            f"{result.total_stored} almacenados, "
            f"{result.elapsed_seconds}s"
        )

        return result

    def process_single_frame(
        self,
        frame_data: FrameData,
        frame_image: np.ndarray,
        camera_id: str,
    ) -> list[CropData]:
        """
        Procesa UN frame con el pipeline completo: detect + embed + describe + store.

        Reutilizable tanto para video grabado como para captura RTSP en vivo.
        Llamado por StreamWorker en cada frame capturado.

        Args:
            frame_data: Metadata del frame (frame_index, timestamp, paths).
            frame_image: Imagen BGR (np.ndarray HxWx3).
            camera_id: ID de la fuente — para una camara, su camera_id.

        Returns:
            Lista de CropData almacenados (con bbox, class_name, confidence,
            description). Vacia si no hay detecciones. El UI puede usarlas
            para dibujar las cajas YOLO en el preview en vivo.
        """
        if not self._mm.is_ready():
            return []

        # Anti-tamper PRIMERO (no requiere GPU)
        self._analyze_tamper(camera_id, frame_image)

        with self._gpu_lock:
            # ── Detectar ──
            raw_crops = self._mm.detector.detect(
                frame_image,
                confidence=self._settings.yolo_confidence,
            )

            if not raw_crops:
                return []

            # Preparar directorio de crops por camara
            crops_dir = self._settings.crops_dir / camera_id
            crops_dir.mkdir(parents=True, exist_ok=True)

            stored_crops: list[CropData] = []
            h, w = frame_image.shape[:2]
            pad = self._settings.crop_padding

            for det_idx, crop_data in enumerate(raw_crops):
                # Completar metadata
                crop_id = (
                    f"{camera_id}__"
                    f"f{frame_data.frame_index:06d}__"
                    f"d{det_idx:03d}"
                )
                crop_data.crop_id = crop_id
                crop_data.frame_path = frame_data.frame_path
                crop_data.video_source = frame_data.video_source
                crop_data.timestamp_seconds = frame_data.timestamp_seconds

                # Recortar imagen del crop
                bbox = crop_data.bbox
                cx1 = max(0, bbox.x1 - pad)
                cy1 = max(0, bbox.y1 - pad)
                cx2 = min(w, bbox.x2 + pad)
                cy2 = min(h, bbox.y2 + pad)
                crop_image = frame_image[cy1:cy2, cx1:cx2]

                if crop_image.size == 0:
                    continue

                # Guardar crop en disco
                crop_filename = (
                    f"f{frame_data.frame_index:06d}_"
                    f"d{det_idx:03d}_{crop_data.class_name}.jpg"
                )
                crop_path = crops_dir / crop_filename
                cv2.imwrite(str(crop_path), crop_image)
                crop_data.crop_path = crop_path

                # ── Embed ──
                embedding = self._mm.embedder.embed_image(crop_image)

                # ── Describe (opcional) ──
                description = ""
                if self._mm.describer is not None and self._mm.describer.is_loaded():
                    description = self._mm.describer.describe(crop_image)
                    crop_data.description = description

                # ── Store ──
                self._db.store(
                    crop_id=crop_id,
                    embedding=embedding,
                    metadata={
                        "class_name": crop_data.class_name,
                        "confidence": crop_data.confidence,
                        "timestamp_seconds": crop_data.timestamp_seconds,
                        "video_source": str(crop_data.video_source),
                        "camera_id": camera_id,
                        "frame_path": str(crop_data.frame_path),
                        "crop_path": str(crop_data.crop_path),
                        "bbox": f"[{bbox.x1},{bbox.y1},{bbox.x2},{bbox.y2}]",
                        "description": description,
                    },
                    description=description,
                )
                stored_crops.append(crop_data)

            # Publicar evento de deteccion al bus (UI/Telegram/HistorialPanel)
            if stored_crops:
                self._publish_detection_event(camera_id, stored_crops)

            return stored_crops

    def _analyze_tamper(
        self, camera_id: str, frame_image: np.ndarray
    ) -> None:
        """Ejecuta detectores anti-tamper para esta camara."""
        manager = self._tamper_managers.get(camera_id)
        if manager is None:
            manager = TamperManager(camera_id=camera_id)
            manager.add_detector(BlackScreenDetector())
            manager.add_detector(SceneChangeDetector())
            self._tamper_managers[camera_id] = manager
        manager.analyze(frame_image)

    def _publish_detection_event(
        self, camera_id: str, crops: list[CropData]
    ) -> None:
        """Publica un SecurityEvent.DETECTION al EventBus."""
        classes = sorted({c.class_name for c in crops})
        has_person = "person" in classes

        # Persona = warning, vehiculo/animal = info
        severity = (
            EventSeverity.WARNING if has_person else EventSeverity.INFO
        )

        title = f"{len(crops)} deteccion(es): {', '.join(classes)}"
        first_desc = crops[0].description if crops[0].description else ""

        event = SecurityEvent(
            event_type=EventType.DETECTION,
            severity=severity,
            camera_id=camera_id,
            title=title,
            message=first_desc,
            thumbnail_path=crops[0].crop_path,
            payload={
                "crop_ids": [c.crop_id for c in crops],
                "classes": classes,
                "count": len(crops),
                "max_confidence": max(c.confidence for c in crops),
            },
        )
        self._event_bus.publish(event)

    # ── Control de flujo ──

    def pause(self) -> None:
        """Pausa el pipeline. Reanudable."""
        self._is_paused = True
        self._pause_event.clear()
        logger.info("[Pipeline] Pausado")

    def resume(self) -> None:
        """Reanuda el pipeline después de pausa."""
        self._is_paused = False
        self._pause_event.set()
        logger.info("[Pipeline] Reanudado")

    def cancel(self) -> None:
        """Cancela el pipeline. No reanudable."""
        self._is_cancelled = True
        self._pause_event.set()  # Desbloquear si estaba pausado
        logger.info("[Pipeline] Cancelando...")

    @property
    def is_running(self) -> bool:
        """True si el pipeline está ejecutándose."""
        return self._is_running

    @property
    def is_paused(self) -> bool:
        """True si el pipeline está pausado."""
        return self._is_paused

    # ── Privados ──

    @staticmethod
    def _emit_progress(
        progress: IndexProgress,
        callback: Callable[[IndexProgress], None] | None,
    ) -> None:
        """Emite progreso al callback si existe."""
        if callback is not None:
            callback(progress)