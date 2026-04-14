"""
Implementacion concreta de embedder usando Jina CLIP v2.
Usa el modelo HuggingFace directo para imagenes y sentence-transformers para texto.
"""
from __future__ import annotations

import cv2
import numpy as np
import torch
from PIL import Image

from core.embedders.base_embedder import BaseEmbedder
from core.logger import logger


class CLIPEmbedder(BaseEmbedder):
    """Generador de embeddings multilingue basado en Jina CLIP v2."""

    def __init__(self, model_name: str = "jinaai/jina-clip-v2") -> None:
        self._model_name = model_name
        self._st_model = None
        self._hf_model = None
        self._processor = None
        self._device: str = "cpu"

    def load(self, device: str = "cuda") -> None:
        """Carga CLIP: sentence-transformers para texto, HF directo para imagenes."""
        from sentence_transformers import SentenceTransformer
        from transformers import AutoModel, AutoProcessor

        self._device = device

        # Modelo sentence-transformers para texto
        self._st_model = SentenceTransformer(
            self._model_name,
            trust_remote_code=True,
            device=self._device,
        )

        # Modelo HF directo para imagenes
        self._hf_model = AutoModel.from_pretrained(
            self._model_name,
            trust_remote_code=True,
        ).to(self._device).eval()

        self._processor = AutoProcessor.from_pretrained(
            self._model_name,
            trust_remote_code=True,
        )

        # Warmup texto
        self._st_model.encode("warmup")
        logger.info(f"CLIPEmbedder cargado: {self._model_name} en {device}")

    def unload(self) -> None:
        """Libera el modelo de memoria."""
        if self._st_model is not None:
            del self._st_model
            self._st_model = None
        if self._hf_model is not None:
            del self._hf_model
            self._hf_model = None
        self._processor = None
        logger.debug(f"CLIPEmbedder descargado: {self._model_name}")

    def embed_image(self, image: np.ndarray) -> list[float]:
        """Genera embedding de una imagen usando el modelo HF directo."""
        if self._hf_model is None:
            raise RuntimeError("CLIPEmbedder no esta cargado.")

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        inputs = self._processor(images=pil_img, return_tensors="pt").to(self._device)

        with torch.no_grad():
            outputs = self._hf_model.get_image_features(**inputs)
            embedding = outputs[0].float().cpu().numpy()

        # Normalizar
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.tolist()

    def embed_text(self, text: str) -> list[float]:
        """Genera embedding de texto usando sentence-transformers."""
        if self._st_model is None:
            raise RuntimeError("CLIPEmbedder no esta cargado.")

        embedding = self._st_model.encode(text)
        return embedding.tolist()

    def is_loaded(self) -> bool:
        return self._st_model is not None and self._hf_model is not None

    @property
    def model_name(self) -> str:
        return f"Jina CLIP v2 ({self._model_name})"

    @property
    def language(self) -> str:
        return "multilingual"
