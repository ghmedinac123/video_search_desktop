"""
Badge de alerta parpadeante reutilizable.

Responsabilidad UNICA: mostrar un indicador visual cuando algo
relevante ocurre en la camara (deteccion, tamper, desconexion).

Hereda QLabel y agrega una animacion de parpadeo controlada por timer.
Polimorfismo: la severidad del evento determina el color y duracion.

Uso:
    badge = AlertBadge()
    badge.flash("ALERTA", color="#ff4d4f", duration_ms=3000)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from ui.theme import Theme


class AlertBadge(QLabel):
    """
    Badge que parpadea por N ms cuando se invoca flash().

    Estados internos: invisible (default), parpadeando, persistente.
    """

    BLINK_INTERVAL_MS: int = 500
    DEFAULT_DURATION_MS: int = 3000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color: str = "#ff4d4f"
        self._visible_state: bool = True
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_visibility)
        self._stop_timer = QTimer(self)
        self._stop_timer.setSingleShot(True)
        self._stop_timer.timeout.connect(self.clear_alert)
        self._setup_style()
        self.hide()

    def _setup_style(self) -> None:
        """Aplica estilo base del badge."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._apply_color()

    def _apply_color(self) -> None:
        """Aplica el color actual al badge."""
        self.setStyleSheet(
            f"background-color: {self._color};"
            f"color: white;"
            f"font-size: {Theme.FONT_SIZE_SMALL}px;"
            f"font-weight: 700;"
            f"padding: 3px 12px;"
            f"border-radius: 99px;"
        )

    def flash(
        self,
        text: str,
        color: str = "#ff4d4f",
        duration_ms: int | None = None,
    ) -> None:
        """
        Activa el parpadeo del badge.

        Args:
            text: Texto a mostrar (ej: "ALERTA", "TAMPER").
            color: Color de fondo en hex.
            duration_ms: Duracion del parpadeo. None = DEFAULT_DURATION_MS.
        """
        self.setText(text)
        self._color = color
        self._apply_color()
        self._visible_state = True
        self.show()

        self._blink_timer.start(self.BLINK_INTERVAL_MS)
        self._stop_timer.start(duration_ms or self.DEFAULT_DURATION_MS)

    def _toggle_visibility(self) -> None:
        """Alterna visibilidad para efecto parpadeo."""
        self._visible_state = not self._visible_state
        self.setVisible(self._visible_state)

    def clear_alert(self) -> None:
        """Detiene el parpadeo y oculta el badge."""
        self._blink_timer.stop()
        self._stop_timer.stop()
        self.hide()
