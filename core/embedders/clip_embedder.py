"""
Implementacion concreta de embedder usando Jina CLIP v2.

Hereda de BaseEmbedder. Genera embeddings tanto de imagenes como
de texto, permitiendo buscar imagenes por descripcion textual.

Uso (via ModelManager, nunca directo):
    embedder = CLIPEmbedder(model_name="jinaai/jina-clip-v2")
    embedder.load(device="cuda")
    img_emb = embedder.embed_image(crop_bgr)
    txt_emb = embedder.embed_text("mujer camisa roja")
    embedder.unload()
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from core.embedders.base_embedder import BaseEmbedder
from core.logger import logger


class CLIPEmbedder(BaseEmbedder):
    """Generador de embeddings multilingue basado en Jina CLIP v2."""

    def __init__(self, model_name: str = "jinaai/jina-clip-v2") -> None:
        """
        Args:
            model_name: Repo HuggingFace del modelo CLIP.
        """
        self._model_name = model_name
        self._model = None
        self._device: str = "cpu"

    def load(self, device: str = "cuda") -> None:
        """Carga el modelo CLIP en GPU/CPU."""
        from sentence_transformers import SentenceTransformer

        self._device = device
        self._model = SentenceTransformer(
            self._model_name,
            trust_remote_code=True,
            device=self._device,
        )

        # Warmup
        self._model.encode("warmup")
        logger.info(f"CLIPEmbedder cargado: {self._model_name} en {device}")

    def unload(self) -> None:
        """Libera el modelo de memoria."""
        if self._model is not None:
            del self._model
            self._model = None
            logger.debug(f"CLIPEmbedder descargado: {self._model_name}")

    def embed_image(self, image: np.ndarray) -> list[float]:
        """
        Genera embedding de una imagen (crop BGR).

        Args:
            image: Imagen BGR numpy array (formato OpenCV).

        Returns:
            Vector de embedding como lista de floats.
        """
        if self._model is None:
            raise RuntimeError("CLIPEmbedder no esta cargado. Llama .load() primero.")

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        embedding = self._model.encode(pil_img)
        return embedding.tolist()

    def embed_text(self, text: str) -> list[float]:
        """
        Genera embedding de un texto (query de busqueda).

        Args:
            text: Texto en lenguaje natural (espanol o ingles).

        Returns:
            Vector de embedding como lista de floats.
        """
        if self._model is None:
            raise RuntimeError("CLIPEmbedder no esta cargado. Llama .load() primero.")

        embedding = self._model.encode(text)
        return embedding.tolist()

    def is_loaded(self) -> bool:
        """True si el modelo esta en memoria."""
        return self._model is not None

    @property
    def model_name(self) -> str:
        """Nombre para logging y UI."""
        return f"Jina CLIP v2 ({self._model_name})"
