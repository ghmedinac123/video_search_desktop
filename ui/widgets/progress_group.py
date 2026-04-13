"""
Grupo de barras de progreso reutilizable.

Responsabilidad UNICA: mostrar N barras de progreso con labels.
Se reutiliza en: indexacion (4 barras) y descarga de modelos.

Hereda de BaseWidget.

Uso:
    from ui.widgets.progress_group import ProgressGroup

    pg = ProgressGroup(bars=["Frames", "YOLO", "CLIP", "VLM"])
    pg.update_bar("Frames", current=50, total=100)
    pg.reset_all()
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QLabel, QProgressBar, QHBoxLayout

from ui.base_widget import BaseWidget
from ui.theme import Theme


class ProgressGroup(BaseWidget):
    """Grupo de barras de progreso con labels — reutilizable."""

    def __init__(
        self,
        bars: list[str],
        parent: QWidget | None = None,
    ) -> None:
        """
        Args:
            bars: Lista de nombres para cada barra (ej: ["Frames", "YOLO"]).
        """
        super().__init__(parent)
        self._bars: dict[str, QProgressBar] = {}
        self._labels: dict[str, QLabel] = {}

        for name in bars:
            self._add_bar(name)

    def _add_bar(self, name: str) -> None:
        """Agrega una barra de progreso con label."""
        row = self.create_horizontal_layout()

        label = QLabel(f"{name}:")
        label.setProperty("class", "secondary")
        label.setFixedWidth(80)
        row.addWidget(label)

        bar = QProgressBar()
        bar.setTextVisible(True)
        bar.setFormat("%v/%m")
        bar.setValue(0)
        bar.setMaximum(100)
        row.addWidget(bar, stretch=1)

        count_label = QLabel("0/0")
        count_label.setProperty("class", "muted")
        count_label.setFixedWidth(70)
        count_label.setAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignRight)
        from PySide6.QtCore import Qt
        count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(count_label)

        self.main_layout.addLayout(row)
        self._bars[name] = bar
        self._labels[name] = count_label

    def update_bar(self, name: str, current: int, total: int) -> None:
        """
        Actualiza una barra especifica.

        Args:
            name: Nombre de la barra (debe coincidir con el constructor).
            current: Valor actual.
            total: Valor maximo.
        """
        if name not in self._bars:
            return

        bar = self._bars[name]
        bar.setMaximum(max(total, 1))
        bar.setValue(current)
        bar.setFormat(f"%v/%m")

        self._labels[name].setText(f"{current:,}/{total:,}")

    def reset_all(self) -> None:
        """Resetea todas las barras a 0."""
        for name in self._bars:
            self._bars[name].setValue(0)
            self._bars[name].setMaximum(100)
            self._labels[name].setText("0/0")
