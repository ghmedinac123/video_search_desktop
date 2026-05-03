"""
Sistema de reconocimiento (faces, plates, etc.).

Tier 3 — interfaces abstractas listas para implementar:
- BaseRecognizer: ABC generica
- FaceRecognizer (stub): InsightFace/Buffalo cuando se integre

Diseno polimorfico para que TODA tarea de reconocimiento implemente
una sola interfaz uniforme.
"""

from core.recognition.base_recognizer import BaseRecognizer, RecognitionResult
from core.recognition.face_recognizer import FaceRecognizer

__all__: list[str] = [
    "BaseRecognizer",
    "RecognitionResult",
    "FaceRecognizer",
]
