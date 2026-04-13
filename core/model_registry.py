"""
Catálogo de modelos de IA + Factory para crear instancias.

Responsabilidad ÚNICA: saber qué modelos existen, verificar si están
descargados, descargarlos, y crear la instancia concreta correcta.

El ModelManager le pide al Registry: "dame un describer para qwen2.5-vl-7b-q4"
y el Registry retorna un QwenDescriber ya instanciado.

Uso:
    from core.model_registry import ModelRegistry

    registry = ModelRegistry()
    models = registry.get_available_models()
    registry.download_model("yolo11m", on_progress=callback)
    detector = registry.create_detector("yolo11m")
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.logger import logger
from models.models_ai import AIModelInfo, AIModelType, ModelStatus

# ────────────────────────────────────────────────────────
# Catálogo de modelos disponibles.
# Cada entrada define: id, nombre, tipo, repo, VRAM, tamaño.
# Para agregar un modelo nuevo, solo se añade aquí.
# ────────────────────────────────────────────────────────
_MODEL_CATALOG: list[dict] = [
    # ── Detectores (YOLO) ──
    {
        "model_id": "yolo11n",
        "display_name": "YOLOv11 Nano",
        "model_type": AIModelType.DETECTOR,
        "repo_id": "yolo11n.pt",
        "estimated_vram_gb": 0.3,
        "estimated_size_gb": 0.012,
        "description": "Rápido, menor precisión. Ideal para GPUs con poca VRAM.",
        "language": "N/A",
    },
    {
        "model_id": "yolo11m",
        "display_name": "YOLOv11 Medium",
        "model_type": AIModelType.DETECTOR,
        "repo_id": "yolo11m.pt",
        "estimated_vram_gb": 0.5,
        "estimated_size_gb": 0.039,
        "description": "Balance entre velocidad y precisión. Recomendado.",
        "language": "N/A",
    },
    {
        "model_id": "yolo11x",
        "display_name": "YOLOv11 Extra Large",
        "model_type": AIModelType.DETECTOR,
        "repo_id": "yolo11x.pt",
        "estimated_vram_gb": 1.0,
        "estimated_size_gb": 0.110,
        "description": "Máxima precisión. Requiere más VRAM.",
        "language": "N/A",
    },
    # ── Embedders (CLIP) ──
    {
        "model_id": "jina-clip-v2",
        "display_name": "Jina CLIP v2",
        "model_type": AIModelType.EMBEDDER,
        "repo_id": "jinaai/jina-clip-v2",
        "estimated_vram_gb": 3.5,
        "estimated_size_gb": 1.7,
        "description": "Embeddings multilingües imagen↔texto. Requerido para búsqueda.",
        "language": "multilingual",
    },
    # ── Describers (VLM) ──
    {
        "model_id": "qwen2.5-vl-7b-q4",
        "display_name": "Qwen2.5-VL 7B Q4",
        "model_type": AIModelType.DESCRIBER,
        "repo_id": "Qwen/Qwen2.5-VL-7B-Instruct",
        "estimated_vram_gb": 5.5,
        "estimated_size_gb": 4.5,
        "description": "Descripciones en español, detalladas. ~500ms/crop.",
        "language": "es",
    },
    {
        "model_id": "moondream2-4bit",
        "display_name": "Moondream2 4-bit",
        "model_type": AIModelType.DESCRIBER,
        "repo_id": "moondream/moondream-2b-2025-04-14-4bit",
        "estimated_vram_gb": 2.5,
        "estimated_size_gb": 1.2,
        "description": "Descripciones en inglés, rápido. ~130ms/crop.",
        "language": "en",
    },
]


class ModelRegistry:
    """
    Catálogo de modelos + Factory para crear instancias concretas.

    Patrón Factory Method: según el model_id, crea la clase correcta
    (YOLODetector, CLIPEmbedder, QwenDescriber, MoondreamDescriber).
    """

    def __init__(self) -> None:
        """Inicializa el catálogo desde _MODEL_CATALOG."""
        self._models: dict[str, AIModelInfo] = {}

        for entry in _MODEL_CATALOG:
            model = AIModelInfo(**entry)
            self._models[model.model_id] = model

        logger.debug(f"ModelRegistry: {len(self._models)} modelos registrados")

    def get_available_models(self) -> list[AIModelInfo]:
        """Retorna todos los modelos del catálogo."""
        return list(self._models.values())

    def get_models_by_type(self, model_type: AIModelType) -> list[AIModelInfo]:
        """Filtra modelos por tipo: detector, embedder, describer."""
        return [m for m in self._models.values() if m.model_type == model_type]

    def get_model_info(self, model_id: str) -> AIModelInfo:
        """Retorna info de un modelo por su ID. Lanza KeyError si no existe."""
        if model_id not in self._models:
            raise KeyError(f"Modelo no encontrado en catálogo: '{model_id}'")
        return self._models[model_id]

    def is_downloaded(self, model_id: str) -> bool:
        """
        Verifica si un modelo ya está descargado en cache. Idempotente.

        YOLO: busca el .pt en el directorio actual o cache ultralytics.
        HuggingFace: busca en ~/.cache/huggingface/hub/
        """
        info = self.get_model_info(model_id)

        if info.model_type == AIModelType.DETECTOR:
            return self._is_yolo_downloaded(info.repo_id)
        else:
            return self._is_hf_downloaded(info.repo_id)

    def scan_downloaded_status(self) -> None:
        """Escanea todos los modelos y actualiza su status."""
        for model_id, model in self._models.items():
            if self.is_downloaded(model_id):
                model.status = ModelStatus.DOWNLOADED
            else:
                model.status = ModelStatus.NOT_DOWNLOADED

        downloaded = sum(
            1 for m in self._models.values()
            if m.status == ModelStatus.DOWNLOADED
        )
        logger.info(
            f"Modelos escaneados: {downloaded}/{len(self._models)} descargados"
        )

    def download_model(
        self,
        model_id: str,
        on_progress: Callable[[str, float], None] | None = None,
    ) -> None:
        """
        Descarga un modelo si no existe. Idempotente.

        Args:
            model_id: ID del modelo a descargar.
            on_progress: Callback(model_id, progreso 0.0-1.0).
        """
        info = self.get_model_info(model_id)

        if self.is_downloaded(model_id):
            logger.info(f"Modelo '{model_id}' ya descargado, saltando")
            info.status = ModelStatus.DOWNLOADED
            if on_progress:
                on_progress(model_id, 1.0)
            return

        logger.info(f"Descargando modelo: {info.display_name} ({info.repo_id})")
        info.status = ModelStatus.DOWNLOADING

        try:
            if info.model_type == AIModelType.DETECTOR:
                self._download_yolo(info.repo_id)
            else:
                self._download_hf(info.repo_id, model_id, on_progress)

            info.status = ModelStatus.DOWNLOADED
            info.download_progress = 1.0
            logger.info(f"Modelo '{model_id}' descargado exitosamente")

        except Exception as e:
            info.status = ModelStatus.ERROR
            logger.error(f"Error descargando '{model_id}': {e}")
            raise

    # ── Factory Methods ──

    def create_detector(self, model_id: str) -> "BaseDetector":
        """Factory: crea instancia correcta de detector."""
        from core.detectors.yolo_detector import YOLODetector

        info = self.get_model_info(model_id)
        if info.model_type != AIModelType.DETECTOR:
            raise TypeError(f"'{model_id}' no es un detector")

        return YOLODetector(model_path=info.repo_id)

    def create_embedder(self, model_id: str) -> "BaseEmbedder":
        """Factory: crea instancia correcta de embedder."""
        from core.embedders.clip_embedder import CLIPEmbedder

        info = self.get_model_info(model_id)
        if info.model_type != AIModelType.EMBEDDER:
            raise TypeError(f"'{model_id}' no es un embedder")

        return CLIPEmbedder(model_name=info.repo_id)

    def create_describer(self, model_id: str) -> "BaseDescriber":
        """Factory: crea instancia correcta de describer."""
        info = self.get_model_info(model_id)
        if info.model_type != AIModelType.DESCRIBER:
            raise TypeError(f"'{model_id}' no es un describer")

        if model_id == "qwen2.5-vl-7b-q4":
            from core.describers.qwen_describer import QwenDescriber
            return QwenDescriber(model_name=info.repo_id)

        elif model_id == "moondream2-4bit":
            from core.describers.moondream_describer import MoondreamDescriber
            return MoondreamDescriber(model_name=info.repo_id)

        else:
            raise ValueError(f"Describer desconocido: '{model_id}'")

    # ── Métodos privados: verificar descarga ──

    @staticmethod
    def _is_yolo_downloaded(repo_id: str) -> bool:
        """Verifica si un modelo YOLO .pt existe."""
        if Path(repo_id).exists():
            return True
        # Buscar en cache de ultralytics
        home = Path.home()
        ultralytics_cache = home / ".ultralytics" / "models" / repo_id
        if ultralytics_cache.exists():
            return True
        # Buscar en directorio actual de trabajo
        return Path(repo_id).exists()

    @staticmethod
    def _is_hf_downloaded(repo_id: str) -> bool:
        """Verifica si un modelo HuggingFace existe en cache."""
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        # HuggingFace guarda como models--org--name
        folder_name = "models--" + repo_id.replace("/", "--")
        model_dir = hf_cache / folder_name
        if model_dir.exists():
            # Verificar que tenga snapshots (descarga completa)
            snapshots = model_dir / "snapshots"
            if snapshots.exists() and any(snapshots.iterdir()):
                return True
        return False

    # ── Métodos privados: descargar ──

    @staticmethod
    def _download_yolo(repo_id: str) -> None:
        """Descarga modelo YOLO via ultralytics (auto-download)."""
        from ultralytics import YOLO
        # YOLO auto-descarga el .pt al instanciarlo
        _ = YOLO(repo_id)

    @staticmethod
    def _download_hf(
        repo_id: str,
        model_id: str,
        on_progress: Callable[[str, float], None] | None = None,
    ) -> None:
        """Descarga modelo HuggingFace al cache local."""
        from huggingface_hub import snapshot_download

        snapshot_download(
            repo_id=repo_id,
            resume_download=True,
        )
        if on_progress:
            on_progress(model_id, 1.0)