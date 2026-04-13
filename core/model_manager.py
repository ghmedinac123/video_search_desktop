"""
Singleton thread-safe que gestiona los modelos cargados en GPU.

Responsabilidad ÚNICA: cargar, mantener y descargar modelos de VRAM.
Delega la creación al ModelRegistry (no sabe cómo instanciar un YOLO).

El usuario selecciona modelos en la UI → el Manager los carga en GPU.
Cada componente del pipeline accede a los modelos via este Singleton.

Uso:
    from core.model_manager import ModelManager

    mm = ModelManager.get_instance()
    mm.load_detector("yolo11m")
    mm.load_embedder("jina-clip-v2")
    mm.load_describer("qwen2.5-vl-7b-q4")

    # El pipeline usa los modelos cargados:
    crops = mm.detector.detect(frame)
    embedding = mm.embedder.embed_image(crop)
    description = mm.describer.describe(crop)

    mm.unload_all()
"""

from __future__ import annotations

import threading
from typing import ClassVar

from core.detectors.base_detector import BaseDetector
from core.embedders.base_embedder import BaseEmbedder
from core.describers.base_describer import BaseDescriber
from core.gpu_utils import GPUUtils
from core.logger import logger
from core.model_registry import ModelRegistry
from models.models_ai import ModelStatus


class ModelManager:
    """
    Singleton thread-safe — un solo set de modelos en VRAM.

    Flujo:
    1. UI llama load_detector("yolo11m")
    2. Manager pide al Registry: create_detector("yolo11m")
    3. Registry retorna un YOLODetector instanciado
    4. Manager llama detector.load(device) para cargarlo en GPU
    5. Manager guarda la referencia en self._detector
    """

    _instance: ClassVar[ModelManager | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self) -> None:
        """NO usar directamente. Usar ModelManager.get_instance()."""
        self._registry = ModelRegistry()
        self._detector: BaseDetector | None = None
        self._embedder: BaseEmbedder | None = None
        self._describer: BaseDescriber | None = None
        self._device: str = GPUUtils.get_device()

    @classmethod
    def get_instance(cls) -> ModelManager:
        """Retorna la instancia única. Thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.info(
                        f"ModelManager inicializado — device: {cls._instance._device}"
                    )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Destruye el singleton (para tests). Libera VRAM."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.unload_all()
                cls._instance = None

    # ── Propiedades de solo lectura ──

    @property
    def detector(self) -> BaseDetector | None:
        """Detector actualmente cargado, o None."""
        return self._detector

    @property
    def embedder(self) -> BaseEmbedder | None:
        """Embedder actualmente cargado, o None."""
        return self._embedder

    @property
    def describer(self) -> BaseDescriber | None:
        """Describer actualmente cargado, o None."""
        return self._describer

    @property
    def registry(self) -> ModelRegistry:
        """Acceso al catálogo de modelos."""
        return self._registry

    @property
    def device(self) -> str:
        """Device actual: 'cuda' o 'cpu'."""
        return self._device

    # ── Cargar modelos ──

    def load_detector(self, model_id: str) -> None:
        """
        Carga un detector en GPU. Si ya hay uno cargado, lo descarga primero.

        Args:
            model_id: ID del catálogo (ej: "yolo11m").
        """
        if self._detector is not None and self._detector.is_loaded():
            logger.info(f"Descargando detector anterior: {self._detector.model_name}")
            self._detector.unload()

        logger.info(f"Cargando detector: {model_id}")
        self._registry.get_model_info(model_id).status = ModelStatus.LOADING

        self._detector = self._registry.create_detector(model_id)
        self._detector.load(device=self._device)

        self._registry.get_model_info(model_id).status = ModelStatus.LOADED
        logger.info(f"Detector cargado: {self._detector.model_name} en {self._device}")

    def load_embedder(self, model_id: str) -> None:
        """
        Carga un embedder en GPU. Si ya hay uno cargado, lo descarga primero.

        Args:
            model_id: ID del catálogo (ej: "jina-clip-v2").
        """
        if self._embedder is not None and self._embedder.is_loaded():
            logger.info(f"Descargando embedder anterior: {self._embedder.model_name}")
            self._embedder.unload()

        logger.info(f"Cargando embedder: {model_id}")
        self._registry.get_model_info(model_id).status = ModelStatus.LOADING

        self._embedder = self._registry.create_embedder(model_id)
        self._embedder.load(device=self._device)

        self._registry.get_model_info(model_id).status = ModelStatus.LOADED
        logger.info(f"Embedder cargado: {self._embedder.model_name} en {self._device}")

    def load_describer(self, model_id: str) -> None:
        """
        Carga un describer (VLM) en GPU. Si ya hay uno, lo descarga primero.

        Args:
            model_id: ID del catálogo (ej: "qwen2.5-vl-7b-q4" o "moondream2-4bit").
        """
        if self._describer is not None and self._describer.is_loaded():
            logger.info(f"Descargando describer anterior: {self._describer.model_name}")
            self._describer.unload()

        logger.info(f"Cargando describer: {model_id}")
        self._registry.get_model_info(model_id).status = ModelStatus.LOADING

        self._describer = self._registry.create_describer(model_id)
        self._describer.load(device=self._device)

        self._registry.get_model_info(model_id).status = ModelStatus.LOADED
        logger.info(f"Describer cargado: {self._describer.model_name} en {self._device}")

    # ── Descargar modelos ──

    def unload_all(self) -> None:
        """Descarga todos los modelos de VRAM y libera memoria."""
        logger.info("Descargando todos los modelos de VRAM...")

        if self._detector is not None and self._detector.is_loaded():
            self._detector.unload()
            logger.debug(f"Detector descargado: {self._detector.model_name}")
        self._detector = None

        if self._embedder is not None and self._embedder.is_loaded():
            self._embedder.unload()
            logger.debug(f"Embedder descargado: {self._embedder.model_name}")
        self._embedder = None

        if self._describer is not None and self._describer.is_loaded():
            self._describer.unload()
            logger.debug(f"Describer descargado: {self._describer.model_name}")
        self._describer = None

        GPUUtils.clear_vram_cache()
        logger.info("Todos los modelos descargados — VRAM liberada")

    # ── Estado ──

    def is_ready(self) -> bool:
        """
        True si detector + embedder están cargados.
        Describer es opcional (puede funcionar sin descripciones).
        """
        detector_ok = self._detector is not None and self._detector.is_loaded()
        embedder_ok = self._embedder is not None and self._embedder.is_loaded()
        return detector_ok and embedder_ok

    def get_status(self) -> dict[str, str]:
        """Retorna estado de cada componente para la UI."""
        def _status(component: BaseDetector | BaseEmbedder | BaseDescriber | None) -> str:
            if component is None:
                return "not_loaded"
            return "loaded" if component.is_loaded() else "error"

        return {
            "detector": _status(self._detector),
            "embedder": _status(self._embedder),
            "describer": _status(self._describer),
            "device": self._device,
        }

    def get_loaded_models_info(self) -> list[dict[str, str | float]]:
        """Retorna info de modelos cargados para el monitor GPU."""
        loaded: list[dict[str, str | float]] = []

        if self._detector is not None and self._detector.is_loaded():
            loaded.append({
                "name": self._detector.model_name,
                "type": "detector",
            })

        if self._embedder is not None and self._embedder.is_loaded():
            loaded.append({
                "name": self._embedder.model_name,
                "type": "embedder",
            })

        if self._describer is not None and self._describer.is_loaded():
            loaded.append({
                "name": self._describer.model_name,
                "type": "describer",
            })

        return loaded