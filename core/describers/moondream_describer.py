"""
Implementación concreta de describer usando Moondream2 4-bit.

Hereda de BaseDescriber. Genera descripciones en INGLÉS de
imágenes de cámaras de seguridad. Más rápido y ligero que Qwen.

~130ms por crop en GPU. Menos detallado que Qwen pero ocupa
menos VRAM (2.5 GB vs 5.5 GB). Ideal para GPUs de 8 GB.

Uso (via ModelManager, nunca directo):
    describer = MoondreamDescriber(model_name="moondream/moondream-2b-...")
    describer.load(device="cuda")
    desc = describer.describe(crop_bgr)  # → "Young woman wearing yellow..."
    describer.unload()
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from core.describers.base_describer import BaseDescriber
from core.logger import logger
from models.settings import get_settings


class MoondreamDescriber(BaseDescriber):
    """Descriptor visual basado en Moondream2 4-bit."""

    MOONDREAM_REVISION: str = "2025-04-14"

    def __init__(
        self,
        model_name: str = "moondream/moondream-2b-2025-04-14-4bit",
    ) -> None:
        """
        Args:
            model_name: Repo HuggingFace del modelo Moondream.
        """
        self._model_name = model_name
        self._model = None
        self._device: str = "cpu"

    def load(self, device: str = "cuda") -> None:
        """Carga Moondream2 4-bit en GPU."""
        import torch
        from transformers import AutoModelForCausalLM

        self._device = device

        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map={"": self._device},
        )

        # Intentar compilar para mayor velocidad (opcional)
        if hasattr(self._model, "compile"):
            try:
                self._model.compile()
                logger.debug("Moondream compilado con torch.compile")
            except Exception:
                pass

        logger.info(f"MoondreamDescriber cargado: {self._model_name} en {device}")

    def unload(self) -> None:
        """Libera el modelo de memoria."""
        if self._model is not None:
            del self._model
            self._model = None
        logger.debug(f"MoondreamDescriber descargado: {self._model_name}")

    def describe(self, image: np.ndarray) -> str:
        """
        Genera descripción en inglés de una imagen.

        Args:
            image: Imagen BGR numpy array (crop de detección).

        Returns:
            Descripción en inglés (ej: "Young woman wearing a yellow
            shirt walking to the right carrying a black backpack").
        """
        if self._model is None:
            raise RuntimeError("MoondreamDescriber no está cargado. Llama .load() primero.")

        settings = get_settings()

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        try:
            result = self._model.query(
                image=pil_img,
                question=settings.moondream_prompt,
            )
            return result["answer"].strip()

        except Exception as e:
            logger.warning(f"MoondreamDescriber error: {e}")
            return ""

    def is_loaded(self) -> bool:
        """True si el modelo está en memoria."""
        return self._model is not None

    @property
    def model_name(self) -> str:
        """Nombre para logging y UI."""
        return "Moondream2 4-bit"

    @property
    def language(self) -> str:
        """Idioma de las descripciones."""
        return "en"