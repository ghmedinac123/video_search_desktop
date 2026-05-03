"""
Panel de historial de eventos de seguridad — feed estilo NVR.

Responsabilidad UNICA: mostrar las ultimas N detecciones/alertas
del EventBus con thumbnail, hora, camara y descripcion. Click en
una fila abre el dialogo de detalle.

Componentes:
- _EventRow: una fila reutilizable (single responsibility)
- EventHistoryPanel: contenedor con scroll y suscripcion al bus

Uso:
    panel = EventHistoryPanel()
    main_window.set_panel(panel_index, panel)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
)

from ui.base_widget import BaseWidget
from ui.theme import Theme
from models.event import EventSeverity, EventType, SecurityEvent
from core.events import EventBus


class _EventRow(BaseWidget):
    """
    Una fila clickeable que representa un SecurityEvent.

    Componente reutilizable (instanciado N veces, uno por evento).
    Emite click_row(event_id) cuando el usuario hace click.
    """

    THUMB_W: int = 96
    THUMB_H: int = 64

    clicked_row = Signal(str)

    def __init__(
        self,
        event: SecurityEvent,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._event = event
        self._setup_ui()

    @property
    def event(self) -> SecurityEvent:
        """Evento que representa esta fila."""
        return self._event

    def _setup_ui(self) -> None:
        """Construye la fila."""
        c = Theme.colors()
        self.main_layout.setContentsMargins(8, 6, 8, 6)
        self.main_layout.setSpacing(6)

        # Marco con borde lateral coloreado segun severidad
        side_color = self._severity_color(self._event.severity)

        wrap = QFrame()
        wrap.setStyleSheet(
            f"QFrame {{"
            f"  background-color: {c.bg_tertiary};"
            f"  border-left: 3px solid {side_color};"
            f"  border-radius: 4px;"
            f"  padding: 6px;"
            f"}}"
            f"QFrame:hover {{"
            f"  background-color: {c.card_bg};"
            f"}}"
        )
        wrap.setCursor(Qt.CursorShape.PointingHandCursor)
        wrap.mousePressEvent = self._on_mouse_press

        row = QHBoxLayout(wrap)
        row.setContentsMargins(6, 4, 6, 4)
        row.setSpacing(10)

        # Thumbnail
        thumb = QLabel()
        thumb.setFixedSize(self.THUMB_W, self.THUMB_H)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet("background-color: #111; border-radius: 3px;")
        if self._event.thumbnail_path and self._event.thumbnail_path.exists():
            pixmap = QPixmap(str(self._event.thumbnail_path))
            if not pixmap.isNull():
                thumb.setPixmap(pixmap.scaled(
                    self.THUMB_W, self.THUMB_H,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        else:
            thumb.setText(self._icon_for_type(self._event.event_type))
            thumb.setStyleSheet(
                f"background-color: #111;"
                f"color: {side_color};"
                f"border-radius: 3px;"
                f"font-size: 24px;"
            )
        row.addWidget(thumb)

        # Texto: titulo + meta
        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 0, 0, 0)

        title = QLabel(self._event.title)
        title.setStyleSheet(
            f"font-size: {Theme.FONT_SIZE}px;"
            f"font-weight: 600;"
            f"color: {c.text_primary};"
        )
        col.addWidget(title)

        meta = QLabel(
            f"{self._event.timestamp_formatted}  ·  "
            f"{self._event.camera_id}  ·  "
            f"{self._event.severity.value.upper()}"
        )
        meta.setProperty("class", "muted")
        meta.setStyleSheet(
            f"font-size: {Theme.FONT_SIZE_SMALL}px;"
            f"color: {c.text_muted};"
        )
        col.addWidget(meta)

        if self._event.message:
            msg = QLabel(self._event.message[:120] + (
                "..." if len(self._event.message) > 120 else ""
            ))
            msg.setProperty("class", "secondary")
            msg.setStyleSheet(
                f"font-size: {Theme.FONT_SIZE_SMALL}px;"
                f"color: {c.text_secondary};"
            )
            msg.setWordWrap(True)
            col.addWidget(msg)

        row.addLayout(col, stretch=1)

        self.main_layout.addWidget(wrap)

    def _on_mouse_press(self, event) -> None:
        """Handler de click sobre la fila."""
        self.clicked_row.emit(self._event.event_id)

    @staticmethod
    def _severity_color(severity: EventSeverity) -> str:
        """Color del borde lateral segun severidad."""
        return {
            EventSeverity.INFO: "#1890ff",
            EventSeverity.WARNING: "#faad14",
            EventSeverity.CRITICAL: "#cf1322",
        }.get(severity, "#888")

    @staticmethod
    def _icon_for_type(event_type: EventType) -> str:
        """Emoji icono cuando no hay thumbnail."""
        return {
            EventType.DETECTION: "\U0001f441",
            EventType.TAMPER: "⚠️",
            EventType.CAMERA_CONNECTED: "✅",
            EventType.CAMERA_DISCONNECTED: "❌",
            EventType.SYSTEM: "⚙️",
            EventType.NOTIFICATION_SENT: "\U0001f4e4",
        }.get(event_type, "?")


class _EventDetailDialog(QDialog):
    """Dialogo modal que muestra el detalle completo de un evento."""

    def __init__(
        self,
        event: SecurityEvent,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._event = event
        self.setWindowTitle(f"Evento - {event.event_type.value}")
        self.setMinimumSize(640, 480)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Imagen grande si hay thumbnail
        if self._event.thumbnail_path and self._event.thumbnail_path.exists():
            img = QLabel()
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = QPixmap(str(self._event.thumbnail_path))
            if not pix.isNull():
                img.setPixmap(pix.scaled(
                    600, 400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
            layout.addWidget(img)

        # Metadata
        meta = QLabel(
            f"<b>Camara:</b> {self._event.camera_id}<br>"
            f"<b>Hora:</b> {self._event.timestamp.isoformat()}<br>"
            f"<b>Tipo:</b> {self._event.event_type.value}<br>"
            f"<b>Severidad:</b> {self._event.severity.value}<br>"
            f"<b>Titulo:</b> {self._event.title}"
        )
        meta.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(meta)

        # Descripcion completa
        if self._event.message:
            desc = QTextEdit()
            desc.setPlainText(self._event.message)
            desc.setReadOnly(True)
            desc.setMaximumHeight(120)
            layout.addWidget(desc)

        # Payload JSON
        if self._event.payload:
            import json
            payload_label = QLabel("Payload:")
            payload_label.setStyleSheet("font-weight: 600;")
            layout.addWidget(payload_label)

            payload_view = QTextEdit()
            payload_view.setPlainText(
                json.dumps(self._event.payload, indent=2, default=str)
            )
            payload_view.setReadOnly(True)
            layout.addWidget(payload_view)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class EventHistoryPanel(BaseWidget):
    """
    Panel principal con feed cronologico de eventos.

    Suscriptor del EventBus. Mantiene una lista circular de los
    ultimos MAX_EVENTS y refresca el scroll cuando llegan nuevos.
    """

    MAX_EVENTS: int = 50

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._events: list[SecurityEvent] = []
        self._rows: list[_EventRow] = []
        self._setup_ui()
        EventBus.get_instance().subscribe(self._on_event)

    def _setup_ui(self) -> None:
        """Construye la UI del panel."""
        header = self.create_header("Historial de eventos")
        self.main_layout.addWidget(header)

        desc = self.create_secondary_label(
            f"Ultimas {self.MAX_EVENTS} alertas/detecciones "
            f"de todas las camaras"
        )
        self.main_layout.addWidget(desc)
        self.main_layout.addWidget(self.create_separator())

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        self._scroll_container = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_container)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll_layout.setSpacing(4)
        self._scroll.setWidget(self._scroll_container)

        self.main_layout.addWidget(self._scroll, stretch=1)

        # Mensaje "sin eventos"
        self._empty_label = self.create_muted_label(
            "Aun no hay eventos. Las detecciones de las camaras apareceran aqui."
        )
        self._scroll_layout.addWidget(self._empty_label)

    def _on_event(self, event: SecurityEvent) -> None:
        """Recibe eventos del bus y agrega al feed."""
        # Filtrar eventos no relevantes para el feed (CAMERA_CONNECTED es ruido)
        if event.event_type == EventType.CAMERA_CONNECTED:
            return

        self._events.insert(0, event)
        if len(self._events) > self.MAX_EVENTS:
            self._events = self._events[: self.MAX_EVENTS]

        self._rebuild_rows()

    def _rebuild_rows(self) -> None:
        """Reconstruye las filas del feed."""
        # Limpiar
        for row in self._rows:
            self._scroll_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

        self._empty_label.setVisible(len(self._events) == 0)

        # Crear filas nuevas
        for event in self._events:
            row = _EventRow(event)
            row.clicked_row.connect(self._on_row_clicked)
            self._rows.append(row)
            self._scroll_layout.addWidget(row)

    def _on_row_clicked(self, event_id: str) -> None:
        """Abre el dialogo de detalle del evento."""
        event = next(
            (e for e in self._events if e.event_id == event_id), None
        )
        if event is None:
            return
        dialog = _EventDetailDialog(event, self)
        dialog.exec()

    @property
    def event_count(self) -> int:
        """Cantidad de eventos en el feed."""
        return len(self._events)
