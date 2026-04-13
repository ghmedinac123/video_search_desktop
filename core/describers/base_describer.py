    """
Clase base abstracta para descriptores visuales (VLM).

Cualquier VLM (Qwen, Moondream, LLaVA, etc.) hereda de esta clase.
Recibe una imagen y genera una descripción en lenguaje natural.

Uso:
    from core.describers.base import BaseDescriber
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class BaseDescriber(ABC):
    """Interfaz base para descriptores visuales — patrón Strategy."""

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
        Genera descripción en lenguaje natural de una imagen.

        Args:
            image: Imagen BGR como numpy array (OpenCV format).

        Returns:
            Descripción como string (ej: "Mujer joven con camisa
            amarilla caminando hacia la derecha").
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

    @property
    @abstractmethod
    def language(self) -> str:
        """
        Idioma de las descripciones generadas.

        Returns:
            'es' para español (Qwen), 'en' para inglés (Moondream).
        """
        ...