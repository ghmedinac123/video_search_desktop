"""
Barra de navegaci?n lateral.

Responsabilidad ?NICA: mostrar botones de navegaci?n y emitir
una se?al cuando el usuario cambia de secci?n.

Uso:
    from ui.widgets.sidebar import Sidebar

    sidebar = Sidebar()
    sidebar.page_changed.connect(stacked_widget.setCurrentIndex)
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from ui.theme import Theme


class _NavButton(QPushButton):
    """
    Bot?n individual de la sidebar. Componente interno reutilizable.

    Cada bot?n tiene un ?cono (emoji), texto, y estado activo/inactivo.
    Se instancia N veces (1 por secci?n).
    """

    def __init__(self, icon: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(f"  {icon}   {text}", parent)
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._apply_style()

    @property
    def active(self) -> bool:
        """True si este bot?n es el seleccionado."""
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        """Activa o desactiva el bot?n visualmente."""
        self._active = value
        self._apply_style()

    def _apply_style(self) -> None:
        """Aplica estilo seg?n estado activo/inactivo."""
        c = Theme.colors()
        if self._active:
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {c.accent}18;"
                f"  color: {c.accent};"
                f"  border: none;"
                f"  border-left: 3px solid {c.accent};"
                f"  border-radius: 0px;"
                f"  text-align: left;"
                f"  padding-left: 12px;"
                f"  font-weight: 600;"
                f"  font-size: {Theme.FONT_SIZE}px;"
                f"}}"
            )
        else:
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: transparent;"
                f"  color: {c.text_secondary};"
                f"  border: none;"
                f"  border-left: 3px solid transparent;"
                f"  border-radius: 0px;"
                f"  text-align: left;"
                f"  padding-left: 12px;"
                f"  font-size: {Theme.FONT_SIZE}px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  background-color: {c.bg_tertiary};"
                f"  color: {c.text_primary};"
                f"}}"
            )


class Sidebar(QWidget):
    """
    Sidebar de navegaci?n con botones verticales.

    Emite page_changed(int) cuando el usuario hace click en un bot?n.
    El ?ndice corresponde a la posici?n en el QStackedWidget.
    """

    page_changed = Signal(int)

    # Definici?n de secciones: (?cono, texto)
    SECTIONS: list[tuple[str, str]] = [
        ("\U0001f9e0", "Modelos"),
        ("\U0001f4e5", "Indexar"),
        ("\U0001f50d", "Buscar"),
        ("\U0001f4f9", "Cámaras"),
        ("\U0001f6a8", "Eventos"),
        ("\U0001f4ca", "Estadísticas"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: list[_NavButton] = []
        self._current_index: int = 0
        self._setup_ui()
        self._set_active(0)

    def _setup_ui(self) -> None:
        """Construye la UI de la sidebar."""
        c = Theme.colors()

        self.setFixedWidth(180)
        self.setStyleSheet(
            f"background-color: {c.bg_secondary};"
            f"border-right: 1px solid {c.border};"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Logo / T?tulo
        title = QLabel("Video Search")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"font-size: 15px;"
            f"font-weight: 700;"
            f"color: {c.accent};"
            f"padding: 20px 0 16px 0;"
            f"background: transparent;"
        )
        layout.addWidget(title)

        # Botones de navegaci?n
        for i, (icon, text) in enumerate(self.SECTIONS):
            btn = _NavButton(icon, text)
            btn.clicked.connect(lambda checked=False, idx=i: self._on_click(idx))
            self._buttons.append(btn)
            layout.addWidget(btn)

        # Spacer para empujar todo arriba
        layout.addStretch()

        # Toggle dark/light abajo
        self._theme_btn = QPushButton("  \u2600   Modo claro")
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: transparent;"
            f"  color: {c.text_muted};"
            f"  border: none;"
            f"  text-align: left;"
            f"  padding: 10px 15px;"
            f"  font-size: {Theme.FONT_SIZE_SMALL}px;"
            f"}}"
            f"QPushButton:hover {{ color: {c.text_primary}; }}"
        )
        self._theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self._theme_btn)

    def _on_click(self, index: int) -> None:
        """Maneja click en un bot?n de navegaci?n."""
        if index == self._current_index:
            return
        self._set_active(index)
        self.page_changed.emit(index)

    def _set_active(self, index: int) -> None:
        """Activa un bot?n y desactiva los dem?s."""
        self._current_index = index
        for i, btn in enumerate(self._buttons):
            btn.active = (i == index)

    def _toggle_theme(self) -> None:
        """Alterna entre dark y light mode."""
        new_mode = Theme.toggle_mode()
        # La ventana principal debe reaplicar el stylesheet
        window = self.window()
        if window:
            window.setStyleSheet(Theme.get_stylesheet())

        # Actualizar texto del bot?n
        if new_mode == "dark":
            self._theme_btn.setText("  \u2600   Modo claro")
        else:
            self._theme_btn.setText("  \U0001f319   Modo oscuro")

        # Re-estilizar botones de la sidebar
        self._setup_ui_colors()

    def _setup_ui_colors(self) -> None:
        """Reaplica colores despu?s de cambio de tema."""
        c = Theme.colors()
        self.setStyleSheet(
            f"background-color: {c.bg_secondary};"
            f"border-right: 1px solid {c.border};"
        )
        for i, btn in enumerate(self._buttons):
            btn.active = (i == self._current_index)
