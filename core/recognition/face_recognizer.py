"""
FaceRecognizer — STUB Tier 3.

Implementacion pendiente. Cuando se active:
1. uv add insightface onnxruntime-gpu
2. Descargar modelo Buffalo (~500 MB)
3. Llenar load() / recognize() con la integracion real.

La galeria de personas conocidas se persiste en data/known_faces/
con un embedding por persona.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from core.logger import logger
from core.recognition.base_recognizer import (
    BaseRecognizer,
    RecognitionResult,
)


class FaceRecognizer(BaseRecognizer):
    """
    Reconocedor de rostros conocidos vs desconocidos.

    Pendiente integracion con InsightFace/Buffalo.
    """

    def __init__(
        self,
        gallery_dir: Path | None = None,
        similarity_threshold: float = 0.55,
    ) -> None:
        super().__init__(name="FaceRecognizer", enabled=False)
        self._gallery_dir = gallery_dir or Path("data/known_faces")
        self._threshold = similarity_threshold
        self._gallery_embeddings: dict[str, np.ndarray] = {}

    def load(self) -> None:
        """Cargar InsightFace / Buffalo cuando se implemente."""
        logger.info(
            "FaceRecognizer.load(): NO implementado todavia (Tier 3 stub). "
            "Activar con `uv add insightface onnxruntime-gpu`."
        )
        self._is_loaded = False

    def unload(self) -> None:
        """Liberar modelos."""
        self._gallery_embeddings.clear()
        self._is_loaded = False

    def recognize(self, image_bgr: np.ndarray) -> list[RecognitionResult]:
        """Detectar caras + comparar contra galeria. Pendiente impl."""
        if not self._is_loaded or not self._enabled:
            return []
        # TODO: integrar insightface FaceAnalysis y comparar embeddings
        return []
