"""
Interfaz abstracta para reconocedores (faces, plates, etc.).

Cualquier tarea de reconocimiento implementa BaseRecognizer.
NO impone modelo ni librería: solo el contrato recognize() → list[Result].

Patron Strategy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict


class RecognitionResult(BaseModel):
    """Resultado generico de un reconocimiento."""

    label: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None  # x1,y1,x2,y2
    metadata: dict = {}

    model_config = ConfigDict(frozen=True)


class BaseRecognizer(ABC):
    """
    Interfaz para cualquier reconocedor (face, plate, license, animal breed).

    Subclases:
    - FaceRecognizer: identifica personas conocidas
    - PlateOCR: lee placas de vehiculos
    - (futuro) BreedRecognizer, LogoRecognizer, etc.
    """

    def __init__(self, name: str, enabled: bool = True) -> None:
        self._name = name
        self._enabled = enabled
        self._is_loaded = False

    @property
    def name(self) -> str:
        """Nombre del reconocedor."""
        return self._name

    @property
    def enabled(self) -> bool:
        """True si esta activo."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Activa o desactiva el reconocedor."""
        self._enabled = value

    @property
    def is_loaded(self) -> bool:
        """True si los modelos estan cargados en memoria."""
        return self._is_loaded

    @abstractmethod
    def load(self) -> None:
        """Carga los modelos en memoria/GPU."""
        ...

    @abstractmethod
    def unload(self) -> None:
        """Libera los modelos y recursos."""
        ...

    @abstractmethod
    def recognize(self, image_bgr: np.ndarray) -> list[RecognitionResult]:
        """
        Procesa una imagen y retorna resultados.

        Args:
            image_bgr: Imagen BGR (np.ndarray HxWx3).

        Returns:
            Lista de RecognitionResult (puede ser vacia).
        """
        ...
