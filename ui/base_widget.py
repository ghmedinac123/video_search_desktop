"""
Clase base para TODOS los paneles y widgets de la app.

Herencia: ModelPanel(BaseWidget), SearchPanel(BaseWidget), etc.
Evita código duplicado: todos los paneles comparten métodos de
creación de UI (títulos, cards, badges, botones, separadores).

Uso:
    from ui.base_widget import BaseWidget

    class ModelPanel(BaseWidget):
        def __init__(self):
            super().__init__()
            title = self.create_section_title("Detector")
            card = self.create_card()
            badge = self.create_badge("Descargado", "success")
            btn = self.create_button("Cargar en GPU", primary=True)
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from ui.theme import Theme


class BaseWidget(QWidget):
    """
    Clase base reutilizable para todos los paneles.

    Provee layout vertical con padding + métodos factory para
    crear componentes UI consistentes en toda la app.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            Theme.PADDING, Theme.PADDING,
            Theme.PADDING, Theme.PADDING,
        )
        self._layout.setSpacing(Theme.SPACING)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    @property
    def main_layout(self) -> QVBoxLayout:
        """Layout principal del widget."""
        return self._layout

    # ── Factory methods reutilizables ──

    def create_section_title(self, text: str) -> QLabel:
        """Crea un título de sección estilizado (ej: 'DETECTOR')."""
        label = QLabel(text.upper())
        label.setProperty("class", "title")
        label.setStyleSheet(
            f"font-size: {Theme.FONT_SIZE_TITLE}px; "
            f"font-weight: 600; "
            f"letter-spacing: 0.5px; "
            f"padding: 4px 0;"
        )
        return label

    def create_header(self, text: str) -> QLabel:
        """Crea un encabezado grande (ej: nombre del panel)."""
        label = QLabel(text)
        label.setProperty("class", "header")
        return label

    def create_secondary_label(self, text: str) -> QLabel:
        """Crea un label de texto secundario (gris)."""
        label = QLabel(text)
        label.setProperty("class", "secondary")
        return label

    def create_muted_label(self, text: str) -> QLabel:
        """Crea un label de texto muy tenue."""
        label = QLabel(text)
        label.setProperty("class", "muted")
        return label

    def create_card(self) -> QFrame:
        """Crea un frame con estilo card (fondo + borde + radius)."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setFrameShape(QFrame.Shape.NoFrame)
        c = Theme.colors()
        card.setStyleSheet(
            f"QFrame[class='card'] {{"
            f"  background-color: {c.card_bg};"
            f"  border: 1px solid {c.card_border};"
            f"  border-radius: {Theme.BORDER_RADIUS_LARGE}px;"
            f"  padding: {Theme.PADDING}px;"
            f"}}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            Theme.PADDING, Theme.PADDING,
            Theme.PADDING, Theme.PADDING,
        )
        card_layout.setSpacing(Theme.SPACING)
        return card

    def create_badge(self, text: str, variant: str = "info") -> QLabel:
        """
        Crea un badge/pill con color semántico.

        Args:
            text: Texto del badge.
            variant: "success", "warning", "error", "info", "accent".
        """
        c = Theme.colors()
        color_map = {
            "success": c.success,
            "warning": c.warning,
            "error": c.error,
            "info": c.info,
            "accent": c.accent,
        }
        color = color_map.get(variant, c.info)

        badge = QLabel(text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {color}22;"
            f"color: {color};"
            f"font-size: {Theme.FONT_SIZE_SMALL}px;"
            f"font-weight: 600;"
            f"padding: 2px 10px;"
            f"border-radius: 99px;"
        )
        badge.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        return badge

    def create_button(
        self,
        text: str,
        primary: bool = False,
        danger: bool = False,
    ) -> QPushButton:
        """
        Crea un botón estilizado.

        Args:
            text: Texto del botón.
            primary: True para botón azul principal.
            danger: True para botón rojo de peligro.
        """
        btn = QPushButton(text)
        if primary:
            btn.setProperty("class", "primary")
        elif danger:
            btn.setProperty("class", "danger")
        return btn

    def create_separator(self) -> QFrame:
        """Crea una línea horizontal separadora."""
        sep = QFrame()
        sep.setProperty("class", "separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        return sep

    def create_horizontal_layout(self) -> QHBoxLayout:
        """Crea un layout horizontal con spacing estándar."""
        layout = QHBoxLayout()
        layout.setSpacing(Theme.SPACING)
        layout.setContentsMargins(0, 0, 0, 0)
        return layout

    # ── Diálogos reutilizables ──

    def show_error(self, title: str, message: str) -> None:
        """Muestra un diálogo de error."""
        QMessageBox.critical(self, title, message)

    def show_success(self, title: str, message: str) -> None:
        """Muestra un diálogo de éxito."""
        QMessageBox.information(self, title, message)

    def show_confirm(self, title: str, message: str) -> bool:
        """Muestra un diálogo de confirmación. Retorna True si acepta."""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
