"""
Panel de busqueda visual — LA ESTRELLA de la app.

Responsabilidad UNICA: barra de busqueda + galeria + detalle.
Compone: ResultGallery + ResultDetail.
Conecta con Searcher via SearchWorker (nunca bloquea UI).

Hereda de BaseWidget.

Uso:
    from ui.widgets.search_panel import SearchPanel
    panel = SearchPanel()
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QSplitter,
)
from PySide6.QtCore import Qt

from ui.base_widget import BaseWidget
from ui.widgets.result_gallery import ResultGallery
from ui.widgets.result_detail import ResultDetail
from ui.theme import Theme
from models.search import SearchResponse


class SearchPanel(BaseWidget):
    """Panel de busqueda visual con galeria y detalle."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construye: barra busqueda + splitter(galeria + detalle)."""
        # Header
        header = self.create_header("Busqueda visual")
        self.main_layout.addWidget(header)
        desc = self.create_secondary_label(
            "Busca por lenguaje natural: 'mujer con camisa amarilla'"
        )
        self.main_layout.addWidget(desc)

        # Barra de busqueda
        search_row = self.create_horizontal_layout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(
            "Buscar: mujer camisa roja, hombre mochila negra..."
        )
        self._search_input.setClearButtonEnabled(True)
        search_row.addWidget(self._search_input, stretch=1)

        self._search_btn = self.create_button("Buscar", primary=True)
        search_row.addWidget(self._search_btn)

        self.main_layout.addLayout(search_row)

        # Stats de busqueda
        self._stats_label = QLabel("")
        self._stats_label.setProperty("class", "muted")
        self.main_layout.addWidget(self._stats_label)

        # Splitter vertical: galeria arriba, detalle abajo
        self._splitter = QSplitter(Qt.Orientation.Vertical)

        self._gallery = ResultGallery()
        self._splitter.addWidget(self._gallery)

        self._detail = ResultDetail()
        self._splitter.addWidget(self._detail)

        # Proporcion 60% galeria, 40% detalle
        self._splitter.setSizes([400, 250])

        self.main_layout.addWidget(self._splitter, stretch=1)

        # Conectar galeria -> detalle
        self._gallery.result_selected.connect(self._on_result_selected)

    def _on_result_selected(self, index: int) -> None:
        """Muestra detalle cuando se hace click en una card."""
        result = self._gallery.get_result(index)
        if result:
            self._detail.show_result(result)

    # ── API publica ──

    def set_results(self, response: SearchResponse) -> None:
        """Actualiza la galeria con nuevos resultados."""
        self._gallery.set_results(response.results)
        self._stats_label.setText(
            f"{response.total_results} resultados en {response.elapsed_ms}ms"
        )
        self._detail.clear()

    @property
    def search_input(self) -> QLineEdit:
        """Acceso al input de busqueda."""
        return self._search_input

    @property
    def search_button(self):
        """Acceso al boton de busqueda."""
        return self._search_btn

    @property
    def query_text(self) -> str:
        """Texto actual del input de busqueda."""
        return self._search_input.text().strip()
