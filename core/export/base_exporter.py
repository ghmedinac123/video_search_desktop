"""
Interfaz abstracta para exportadores.

Cada formato (ZIP, PDF, CSV) implementa BaseExporter.export(events, path).

Patron Strategy. La UI no sabe el formato concreto, solo invoca export().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from models.event import SecurityEvent


class BaseExporter(ABC):
    """Exportador abstracto. Subclases implementan export()."""

    def __init__(self, name: str, file_extension: str) -> None:
        self._name = name
        self._file_extension = file_extension

    @property
    def name(self) -> str:
        """Nombre legible del exportador."""
        return self._name

    @property
    def file_extension(self) -> str:
        """Extension de archivo (sin punto): zip, pdf, csv."""
        return self._file_extension

    @abstractmethod
    def export(
        self,
        events: list[SecurityEvent],
        output_path: Path,
    ) -> Path:
        """
        Exporta una lista de eventos a un archivo en el formato concreto.

        Args:
            events: Eventos a exportar.
            output_path: Ruta del archivo de salida.

        Returns:
            Path al archivo generado.
        """
        ...
