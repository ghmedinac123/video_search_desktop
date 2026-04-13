"""
Clase base abstracta para generadores de embeddings.

Cualquier embedder (CLIP, SigLIP, etc.) hereda de esta clase.
Genera vectores numéricos tanto de imágenes como de texto,
permitiendo buscar imágenes por descripción textual.

Uso:
    from core.embedders.base import BaseEmbedder
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class BaseEmbedder(ABC):
    """Interfaz base para generadores de embeddings — patrón Strategy."""

    @abstractmethod
    def load(self, device: str = "cuda") -> None:
        """Carga el modelo en GPU/CPU."""
        ...

    @abstractmethod
    def unload(self) -> None:
        """Libera el modelo de la memoria."""
        ...

    @abstractmethod
    def embed_image(self, image: np.ndarray) -> list[float]:
        """
        Genera embedding de una imagen (crop).

        Args:
            image: Imagen BGR como numpy array (OpenCV format).

        Returns:
            Vector de embedding como lista de floats.
        """
        ...

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """
        Genera embedding de un texto (query de búsqueda).

        Args:
            text: Texto en lenguaje natural.

        Returns:
            Vector de embedding como lista de floats.
        """
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Retorna True si el modelo está cargado en memoria."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo para logging y UI."""
        ...