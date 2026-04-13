"""
Clase base abstracta para descriptores visuales (VLM).

Cualquier VLM (Qwen, Moondream, LLaVA, etc.) hereda de esta clase.
Recibe una imagen y genera una descripcion en lenguaje natural.

Uso:
    from core.describers.base_describer import BaseDescriber
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class BaseDescriber(ABC):
    """Interfaz base para descriptores visuales — patron Strategy."""

    @abstractmethod
    def load(self, device: str = "cuda") -> None:
        """Carga el modelo en GPU/CPU."""
        ...

    @abstractmethod
    def unload(self) -> None:
        """Libera el modelo de la memoria."""
        ...

    @abstractmethod
    def describe(self, image: np.ndarray) -> str:
        """
        Genera descripcion en lenguaje natural de una imagen.

        Args:
            image: Imagen BGR como numpy array (OpenCV format).

        Returns:
            Descripcion como string.
        """
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Retorna True si el modelo esta cargado en memoria."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo para logging y UI."""
        ...

    @property
    @abstractmethod
    def language(self) -> str:
        """Idioma de las descripciones: 'es' o 'en'."""
        ...
