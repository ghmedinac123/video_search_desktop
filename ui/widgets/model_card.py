"""
Card individual de un modelo AI — componente reutilizable.

Responsabilidad UNICA: mostrar info de UN modelo (nombre, estado,
VRAM, progreso descarga) y emitir signal cuando se selecciona.

Se instancia N veces (1 por modelo del catalogo).
Hereda de BaseWidget.

Uso:
    from ui.widgets.model_card import ModelCard
    card = ModelCard(model_info)
    card.selected.connect(lambda mid: print(f"Seleccionado: {mid}"))
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QRadioButton,
    QLabel,
    QProgressBar,
    QSizePolicy,
)
from PySide6.QtCore import Signal

from ui.base_widget import BaseWidget
from ui.theme import Theme
from models.models_ai import AIModelInfo, ModelStatus


class ModelCard(BaseWidget):
    """Card reutilizable para un modelo AI del catalogo."""

    selected = Signal(str)

    def __init__(self, model_info: AIModelInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._info = model_info
        self._setup_ui()

    @property
    def model_id(self) -> str:
        """ID del modelo que representa esta card."""
        return self._info.model_id

    @property
    def model_info(self) -> AIModelInfo:
        """Info completa del modelo."""
        return self._info

    def _setup_ui(self) -> None:
        """Construye la UI de la card."""
        c = Theme.colors()

        row = self.create_horizontal_layout()

        # Radio button
        self._radio = QRadioButton()
        self._radio.toggled.connect(self._on_toggled)
        row.addWidget(self._radio)

        # Info: nombre + descripcion
        info_col = BaseWidget()
        info_col.main_layout.setContentsMargins(0, 0, 0, 0)
        info_col.main_layout.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_row.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(self._info.display_name)
        name_label.setStyleSheet(
            f"font-size: {Theme.FONT_SIZE}px; font-weight: 600;"
        )
        name_row.addWidget(name_label)

        self._status_badge = self._create_status_badge()
        name_row.addWidget(self._status_badge)
        name_row.addStretch()

        info_col.main_layout.addLayout(name_row)

        desc = QLabel(
            f"{self._info.description} — "
            f"{self._info.estimated_vram_gb} GB VRAM"
        )
        desc.setProperty("class", "secondary")
        desc.setStyleSheet(f"font-size: {Theme.FONT_SIZE_SMALL}px;")
        info_col.main_layout.addWidget(desc)

        row.addWidget(info_col, stretch=1)

        # VRAM badge
        vram_badge = self.create_badge(
            f"{self._info.estimated_vram_gb} GB",
            "warning",
        )
        row.addWidget(vram_badge)

        self.main_layout.addLayout(row)

        # Barra progreso descarga (oculta por defecto)
        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setVisible(False)
        self.main_layout.addWidget(self._progress_bar)

        # Separador
        self.main_layout.addWidget(self.create_separator())

    def _create_status_badge(self) -> QLabel:
        """Crea badge de estado segun ModelStatus."""
        status = self._info.status
        status_map = {
            ModelStatus.NOT_DOWNLOADED: ("No descargado", "error"),
            ModelStatus.DOWNLOADING: ("Descargando...", "warning"),
            ModelStatus.DOWNLOADED: ("Descargado", "success"),
            ModelStatus.LOADING: ("Cargando...", "warning"),
            ModelStatus.LOADED: ("En GPU", "info"),
            ModelStatus.ERROR: ("Error", "error"),
        }
        text, variant = status_map.get(status, ("?", "info"))
        return self.create_badge(text, variant)

    def _on_toggled(self, checked: bool) -> None:
        """Emite signal cuando se selecciona este modelo."""
        if checked:
            self.selected.emit(self._info.model_id)

    # ── API publica ──

    def set_checked(self, checked: bool) -> None:
        """Selecciona o deselecciona el radio button."""
        self._radio.setChecked(checked)

    def is_checked(self) -> bool:
        """True si este modelo esta seleccionado."""
        return self._radio.isChecked()

    def update_status(self, status: ModelStatus) -> None:
        """Actualiza el badge de estado."""
        self._info.status = status
        # Reemplazar badge
        old = self._status_badge
        self._status_badge = self._create_status_badge()
        old.deleteLater()

    def set_download_progress(self, value: float) -> None:
        """Actualiza barra de progreso de descarga (0.0 a 1.0)."""
        self._progress_bar.setVisible(value < 1.0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(int(value * 100))
