"""
EvidenceExporter — ZIP forense con cadena de custodia.

Empaqueta:
- frames originales
- crops de detecciones
- manifest.json con metadatos completos
- chain_of_custody.txt con SHA256 de cada archivo + timestamp

El hash SHA256 permite probar que la evidencia no fue alterada
despues del export — util para procesos legales.

Implementa BaseExporter.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path

from core.export.base_exporter import BaseExporter
from core.logger import logger
from models.event import SecurityEvent


class EvidenceExporter(BaseExporter):
    """Exporta eventos a un ZIP forense con cadena de custodia."""

    def __init__(self) -> None:
        super().__init__(name="Evidencia (ZIP forense)", file_extension="zip")

    def export(
        self,
        events: list[SecurityEvent],
        output_path: Path,
    ) -> Path:
        """
        Genera ZIP con frames + crops + manifest + chain of custody.

        Args:
            events: Eventos a exportar (ej: filtrados por fecha o camara).
            output_path: Ruta destino .zip.

        Returns:
            Path al ZIP generado.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        manifest = self._build_manifest(events)
        custody_lines: list[str] = [
            "CADENA DE CUSTODIA - EVIDENCIA EXPORTADA",
            f"Generado: {datetime.now().isoformat()}",
            f"Total eventos: {len(events)}",
            "",
            "Hash SHA256 por archivo (para verificar integridad):",
            "-" * 70,
        ]

        with zipfile.ZipFile(
            output_path, "w", zipfile.ZIP_DEFLATED
        ) as zf:
            # Manifest principal
            manifest_bytes = json.dumps(
                manifest, indent=2, default=str
            ).encode("utf-8")
            zf.writestr("manifest.json", manifest_bytes)
            custody_lines.append(
                f"  manifest.json  →  "
                f"{hashlib.sha256(manifest_bytes).hexdigest()}"
            )

            # Frames + crops
            for i, event in enumerate(events, start=1):
                event_dir = f"events/{i:04d}_{event.event_id[:8]}"
                event_json = json.dumps(
                    event.model_dump(), indent=2, default=str
                ).encode("utf-8")
                zf.writestr(f"{event_dir}/event.json", event_json)
                custody_lines.append(
                    f"  {event_dir}/event.json  →  "
                    f"{hashlib.sha256(event_json).hexdigest()}"
                )

                if event.thumbnail_path and event.thumbnail_path.exists():
                    arc_path = f"{event_dir}/{event.thumbnail_path.name}"
                    zf.write(event.thumbnail_path, arcname=arc_path)
                    custody_lines.append(
                        f"  {arc_path}  →  "
                        f"{self._hash_file(event.thumbnail_path)}"
                    )

            # Cadena de custodia
            custody_text = "\n".join(custody_lines).encode("utf-8")
            zf.writestr("chain_of_custody.txt", custody_text)

        logger.info(
            f"EvidenceExporter: ZIP generado en {output_path} "
            f"({len(events)} eventos)"
        )
        return output_path

    @staticmethod
    def _build_manifest(events: list[SecurityEvent]) -> dict:
        """Construye el JSON de manifest con metadata global."""
        cameras = sorted({e.camera_id for e in events})
        types = sorted({e.event_type.value for e in events})
        severities = sorted({e.severity.value for e in events})

        timestamps = [e.timestamp for e in events]
        time_range = {
            "from": min(timestamps).isoformat() if timestamps else None,
            "to": max(timestamps).isoformat() if timestamps else None,
        }

        return {
            "exporter": "EvidenceExporter v1.0",
            "exported_at": datetime.now().isoformat(),
            "total_events": len(events),
            "cameras": cameras,
            "event_types": types,
            "severities": severities,
            "time_range": time_range,
            "events": [e.model_dump() for e in events],
        }

    @staticmethod
    def _hash_file(path: Path) -> str:
        """SHA256 de un archivo (chunked para no cargar todo en RAM)."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
