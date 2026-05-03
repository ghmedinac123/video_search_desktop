"""
Sistema anti-tamper para camaras de seguridad.

Detecta sabotaje (camara cubierta, lente bloqueada, cambio de
escena brusco) y publica eventos TAMPER al EventBus.

Polimorfismo: nuevos algoritmos se agregan implementando
BaseTamperDetector. El TamperManager los corre todos sobre cada frame.
"""

from core.tamper.base_tamper_detector import BaseTamperDetector
from core.tamper.black_screen_detector import BlackScreenDetector
from core.tamper.scene_change_detector import SceneChangeDetector
from core.tamper.tamper_manager import TamperManager

__all__: list[str] = [
    "BaseTamperDetector",
    "BlackScreenDetector",
    "SceneChangeDetector",
    "TamperManager",
]
