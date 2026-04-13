"""
Implementación concreta de describer usando Qwen2.5-VL 7B Q4.

Hereda de BaseDescriber. Genera descripciones en ESPAÑOL de
imágenes de cámaras de seguridad. Usa cuantización 4-bit para
caber en GPUs de 8-16 GB VRAM.

~500ms por crop en GPU. Descripciones detalladas con colores,
ropa, acción, dirección de movimiento.

Uso (via ModelManager, nunca directo):
    describer = QwenDescriber(model_name="Qwen/Qwen2.5-VL-7B-Instruct")
    describer.load(device="cuda")
    desc = describer.describe(crop_bgr)  # → "Mujer joven con camisa..."
    describer.unload()
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from core.describers.base_describer import BaseDescriber
from core.logger import logger
from models.settings import get_settings


class QwenDescriber(BaseDescriber):
    """Descriptor visual basado en Qwen2.5-VL 7B cuantizado a 4-bit."""

    def __init__(self, model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct") -> None:
        """
        Args:
            model_name: Repo HuggingFace del modelo Qwen.
        """
        self._model_name = model_name
        self._model = None
        self._processor = None
        self._device: str = "cpu"

    def load(self, device: str = "cuda") -> None:
        """Carga Qwen2.5-VL con cuantización 4-bit en GPU."""
        import torch
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
        from transformers import BitsAndBytesConfig

        self._device = device

        # Cuantización 4-bit para caber en 16GB VRAM
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )

        self._model = Qwen2VLForConditionalGeneration.from_pretrained(
            self._model_name,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True,
        )

        self._processor = AutoProcessor.from_pretrained(self._model_name)

        logger.info(f"QwenDescriber cargado: {self._model_name} (Q4) en {device}")

    def unload(self) -> None:
        """Libera el modelo de memoria."""
        if self._model is not None:
            del self._model
            self._model = None
        if self._processor is not None:
            del self._processor
            self._processor = None
        logger.debug(f"QwenDescriber descargado: {self._model_name}")

    def describe(self, image: np.ndarray) -> str:
        """
        Genera descripción en español de una imagen.

        Args:
            image: Imagen BGR numpy array (crop de detección).

        Returns:
            Descripción en español (ej: "Mujer joven con camisa amarilla
            caminando hacia la derecha portando una mochila negra").
        """
        if self._model is None or self._processor is None:
            raise RuntimeError("QwenDescriber no está cargado. Llama .load() primero.")

        import torch
        from qwen_vl_utils import process_vision_info

        settings = get_settings()

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": pil_img},
                {"type": "text", "text": settings.qwen_prompt},
            ],
        }]

        text = self._processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self._processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(self._model.device)

        try:
            with torch.no_grad():
                ids = self._model.generate(**inputs, max_new_tokens=150)

            # Solo decodificar tokens nuevos (sin el prompt)
            generated = ids[:, inputs.input_ids.shape[1]:]
            description = self._processor.batch_decode(
                generated, skip_special_tokens=True,
            )[0].strip()

            return description

        except Exception as e:
            logger.warning(f"QwenDescriber error: {e}")
            return ""

    def is_loaded(self) -> bool:
        """True si el modelo está en memoria."""
        return self._model is not None and self._processor is not None

    @property
    def model_name(self) -> str:
        """Nombre para logging y UI."""
        return "Qwen2.5-VL 7B Q4"

    @property
    def language(self) -> str:
        """Idioma de las descripciones."""
        return "es"