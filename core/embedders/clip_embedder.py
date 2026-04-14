"""
Jina CLIP v2 - usa AutoModel directo para texto e imagenes (alineados).
"""
from __future__ import annotations
import cv2
import numpy as np
import torch
from PIL import Image
from core.embedders.base_embedder import BaseEmbedder
from core.logger import logger

class CLIPEmbedder(BaseEmbedder):
    def __init__(self, model_name="jinaai/jina-clip-v2"):
        self._model_name = model_name
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._device = "cpu"

    def load(self, device="cuda"):
        from transformers import AutoModel, AutoProcessor, AutoTokenizer
        self._device = device
        self._model = AutoModel.from_pretrained(
            self._model_name, trust_remote_code=True
        ).to(self._device).eval()
        self._processor = AutoProcessor.from_pretrained(
            self._model_name, trust_remote_code=True
        )
        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_name, trust_remote_code=True
        )
        logger.info(f"CLIPEmbedder cargado: {self._model_name} en {device}")

    def unload(self):
        del self._model, self._processor, self._tokenizer
        self._model = self._processor = self._tokenizer = None

    def embed_image(self, image):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        inputs = self._processor(images=pil_img, return_tensors="pt").to(self._device)
        with torch.no_grad():
            emb = self._model.get_image_features(**inputs)[0].float().cpu().numpy()
        norm = np.linalg.norm(emb)
        return (emb / norm).tolist() if norm > 0 else emb.tolist()

    def embed_text(self, text):
        inputs = self._tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self._device)
        with torch.no_grad():
            emb = self._model.get_text_features(**inputs)[0].float().cpu().numpy()
        norm = np.linalg.norm(emb)
        return (emb / norm).tolist() if norm > 0 else emb.tolist()

    def is_loaded(self):
        return self._model is not None

    @property
    def model_name(self):
        return f"Jina CLIP v2 ({self._model_name})"

    @property
    def language(self):
        return "multilingual"
