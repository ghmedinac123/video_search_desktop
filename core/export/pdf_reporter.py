"""
PdfReporter — STUB Tier 3.

Genera reportes ejecutivos PDF (resumen diario/semanal).

Implementacion pendiente con reportlab. Cuando se active:
1. uv add reportlab
2. Llenar export() con la composicion del PDF.

Implementa BaseExporter — la UI no necesita saber el formato concreto.
"""

from __future__ import annotations

from pathlib import Path

from core.export.base_exporter import BaseExporter
from core.logger import logger
from models.event import SecurityEvent


class PdfReporter(BaseExporter):
    """Reporte ejecutivo PDF con estadisticas y eventos top."""

    def __init__(self, title: str = "Reporte de Seguridad") -> None:
        super().__init__(name="Reporte PDF", file_extension="pdf")
        self._title = title

    def export(
        self,
        events: list[SecurityEvent],
        output_path: Path,
    ) -> Path:
        """
        Stub: cuando se active reportlab, generar PDF con:
        - Portada (titulo, rango de fechas, total eventos)
        - Estadisticas (eventos por camara, por clase, por hora)
        - Top 10 detecciones criticas con thumbnail
        - Anti-tamper alerts
        """
        logger.warning(
            "PdfReporter NO implementado todavia (Tier 3 stub). "
            "Activar con `uv add reportlab`."
        )
        # Por ahora generamos un .txt placeholder para no romper la UI
        placeholder = output_path.with_suffix(".txt")
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        placeholder.write_text(
            f"{self._title}\n"
            f"Eventos: {len(events)}\n"
            f"(Reporte PDF pendiente — instalar reportlab)\n",
            encoding="utf-8",
        )
        return placeholder
