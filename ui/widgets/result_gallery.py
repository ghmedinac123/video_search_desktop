"""
Galeria scrollable de resultados de busqueda.

Responsabilidad UNICA: mostrar un grid de ResultCards dentro
de un QScrollArea. Lazy loading para no cargar 1000 imagenes.

Emite signal result_selected(int) cuando se hace click en una card.

Uso:
    gallery = ResultGallery()
    gallery.set_results(search_response.results)
    gallery.result_selected.connect(lambda idx: show_detail(idx))
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QScrollArea,
    QGridLayout,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt

from ui.theme import Theme
from ui.widgets.result_card import ResultCard
from models.search import SearchResult


class ResultGallery(QScrollArea):
    """Grid scrollable de ResultCards — galeria visual estilo NVR."""

    result_selected = Signal(int)

    COLUMNS: int = 4

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: list[ResultCard] = []
        self._results: list[SearchResult] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura el scroll area + grid interior."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setSpacing(10)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)

        # Placeholder cuando no hay resultados
        self._empty_label = QLabel("Escribe una busqueda para ver resultados")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setProperty("class", "muted")
        self._empty_label.setMinimumHeight(200)
        self._grid.addWidget(self._empty_label, 0, 0, 1, self.COLUMNS)

    def set_results(self, results: list[SearchResult]) -> None:
        """
        Reemplaza los resultados mostrados en la galeria.

        Args:
            results: Lista de SearchResult ordenados por score.
        """
        self._clear_cards()
        self._results = results

        if not results:
            self._empty_label.setVisible(True)
            self._empty_label.setText("Sin resultados")
            return

        self._empty_label.setVisible(False)

        for i, result in enumerate(results):
            card = ResultCard(index=i, result=result)
            card.clicked.connect(self._on_card_clicked)
            self._cards.append(card)

            row = i // self.COLUMNS
            col = i % self.COLUMNS
            self._grid.addWidget(card, row, col)

    def get_result(self, index: int) -> SearchResult | None:
        """Retorna un resultado por indice."""
        if 0 <= index < len(self._results):
            return self._results[index]
        return None

    def _on_card_clicked(self, index: int) -> None:
        """Propaga click de card al signal de la galeria."""
        self.result_selected.emit(index)

    def _clear_cards(self) -> None:
        """Elimina todas las cards actuales."""
        for card in self._cards:
            self._grid.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        self._results.clear()
