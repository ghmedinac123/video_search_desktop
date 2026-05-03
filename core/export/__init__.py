"""
Sistema de exportacion de evidencias.

Polimorfismo: cada formato implementa BaseExporter.
- EvidenceExporter: ZIP forense con cadena de custodia (SHA256).
- PdfReporter (stub Tier 3): reporte ejecutivo PDF.
"""

from core.export.base_exporter import BaseExporter
from core.export.evidence_exporter import EvidenceExporter

__all__: list[str] = ["BaseExporter", "EvidenceExporter"]
