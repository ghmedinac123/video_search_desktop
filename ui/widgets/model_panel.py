"""
Panel de seleccion y gestion de modelos AI.

Responsabilidad UNICA: permitir al usuario seleccionar, descargar
y cargar modelos en GPU. Muestra VRAM estimada vs disponible.

Hereda de BaseWidget. Usa ModelCard (reutilizable por modelo).
Conecta con ModelManager via workers (nunca bloquea UI).

Uso:
    from ui.widgets.model_panel import ModelPanel
    panel = ModelPanel()
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QSlider,
    QHBoxLayout,
    QButtonGroup,
)
from PySide6.QtCore import Qt

from ui.base_widget import BaseWidget
from ui.widgets.model_card import ModelCard
from ui.widgets.gpu_monitor import GPUMonitorWidget
from ui.theme import Theme
from core.model_manager import ModelManager
from core.gpu_utils import GPUUtils
from models.models_ai import AIModelType


class ModelPanel(BaseWidget):
    """Panel completo de seleccion de modelos AI."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mm = ModelManager.get_instance()
        self._cards: dict[str, ModelCard] = {}
        self._selected: dict[str, str] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construye las 3 secciones + controles + monitor GPU."""
        # Header
        header = self.create_header("Modelos AI")
        self.main_layout.addWidget(header)
        desc = self.create_secondary_label(
            "Selecciona los modelos, descargalos y cargalos en GPU"
        )
        self.main_layout.addWidget(desc)
        self.main_layout.addWidget(self.create_separator())

        # Seccion Detectores
        self._add_model_section("Detector (YOLO)", AIModelType.DETECTOR)

        # Slider confianza YOLO
        self._add_confidence_slider()

        # Seccion Embedders
        self._add_model_section("Embeddings (CLIP)", AIModelType.EMBEDDER)

        # Seccion Describers
        self._add_model_section("Descriptor visual (VLM)", AIModelType.DESCRIBER)

        # Monitor GPU
        self.main_layout.addWidget(self.create_separator())
        self._gpu_monitor = GPUMonitorWidget(compact=False)
        self.main_layout.addWidget(self._gpu_monitor)

        # VRAM estimada
        self._vram_estimate_label = QLabel("")
        self._vram_estimate_label.setProperty("class", "secondary")
        self.main_layout.addWidget(self._vram_estimate_label)
        self._update_vram_estimate()

        # Botones
        btn_row = self.create_horizontal_layout()
        self._download_btn = self.create_button("Descargar seleccionados")
        self._load_btn = self.create_button("Cargar en GPU", primary=True)
        btn_row.addWidget(self._download_btn)
        btn_row.addWidget(self._load_btn)
        btn_row.addStretch()
        self.main_layout.addLayout(btn_row)

        self.main_layout.addStretch()

        # Escanear estado de modelos
        self._mm.registry.scan_downloaded_status()

    def _add_model_section(self, title: str, model_type: AIModelType) -> None:
        """Agrega una seccion con cards de modelos del tipo dado."""
        section_title = self.create_section_title(title)
        self.main_layout.addWidget(section_title)

        card_container = self.create_card()
        card_layout = card_container.layout()

        models = self._mm.registry.get_models_by_type(model_type)
        group = QButtonGroup(self)
        group.setExclusive(True)

        for i, model_info in enumerate(models):
            card = ModelCard(model_info)
            card.selected.connect(self._on_model_selected)
            self._cards[model_info.model_id] = card
            card_layout.addWidget(card)

            # Agregar radio al grupo exclusivo
            group.addButton(card._radio, i)

            # Seleccionar el primero por defecto
            if i == 0:
                card.set_checked(True)
                self._selected[model_type.value] = model_info.model_id

        self.main_layout.addWidget(card_container)

    def _add_confidence_slider(self) -> None:
        """Agrega slider de confianza YOLO."""
        row = self.create_horizontal_layout()

        label = QLabel("Confianza YOLO:")
        label.setProperty("class", "secondary")
        row.addWidget(label)

        self._conf_slider = QSlider(Qt.Orientation.Horizontal)
        self._conf_slider.setMinimum(10)
        self._conf_slider.setMaximum(90)
        self._conf_slider.setValue(45)
        self._conf_slider.setTickInterval(5)
        self._conf_slider.valueChanged.connect(self._on_confidence_changed)
        row.addWidget(self._conf_slider, stretch=1)

        self._conf_label = QLabel("0.45")
        self._conf_label.setFixedWidth(40)
        row.addWidget(self._conf_label)

        self.main_layout.addLayout(row)

    def _on_model_selected(self, model_id: str) -> None:
        """Actualiza seleccion cuando el usuario cambia un radio."""
        info = self._mm.registry.get_model_info(model_id)
        self._selected[info.model_type.value] = model_id
        self._update_vram_estimate()

    def _on_confidence_changed(self, value: int) -> None:
        """Actualiza label de confianza."""
        self._conf_label.setText(f"{value / 100:.2f}")

    def _update_vram_estimate(self) -> None:
        """Calcula y muestra VRAM estimada de la combinacion seleccionada."""
        total_vram = 0.0
        parts = []
        for type_key, model_id in self._selected.items():
            info = self._mm.registry.get_model_info(model_id)
            total_vram += info.estimated_vram_gb
            parts.append(f"{info.display_name}: {info.estimated_vram_gb}")

        gpu_info = GPUUtils.detect_gpu()
        gpu_total = gpu_info.total_vram_gb if gpu_info.available else 0

        fits = total_vram <= gpu_total if gpu_total > 0 else True
        status = "OK" if fits else "EXCEDE VRAM"

        if hasattr(self, '_vram_estimate_label'): self._vram_estimate_label.setText(
            f"VRAM estimada: {total_vram:.1f} GB "
            f"({' + '.join(parts)}) ? {status}"
        )

    @property
    def selected_detector(self) -> str | None:
        """ID del detector seleccionado."""
        return self._selected.get("detector")

    @property
    def selected_embedder(self) -> str | None:
        """ID del embedder seleccionado."""
        return self._selected.get("embedder")

    @property
    def selected_describer(self) -> str | None:
        """ID del describer seleccionado."""
        return self._selected.get("describer")

    @property
    def yolo_confidence(self) -> float:
        """Valor actual del slider de confianza."""
        return self._conf_slider.value() / 100
