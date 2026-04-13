"""
Card individual de un resultado de busqueda — reutilizable.

Responsabilidad UNICA: mostrar thumbnail + score + clase + timestamp
de UN resultado. Se instancia N veces (1 por resultado).

Hereda de BaseWidget. Emite signal clicked(int) con su indice.

Uso:
    card = ResultCard(index=0, result=search_result)
    card.clicked.connect(lambda idx: show_detail(idx))
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtCore import Signal, Qt

from ui.base_widget import BaseWidget
from ui.theme import Theme
from models.search import SearchResult


class ResultCard(BaseWidget):
    """Card reutilizable para un resultado de busqueda."""

    clicked = Signal(int)

    THUMB_WIDTH: int = 200
    THUMB_HEIGHT: int = 150

    def __init__(
        self,
        index: int,
        result: SearchResult,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._index = index
        self._result = result
        self._setup_ui()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    @property
    def result(self) -> SearchResult:
        """El SearchResult que representa esta card."""
        return self._result

    def _setup_ui(self) -> None:
        """Construye: thumbnail + badges."""
        c = Theme.colors()
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(6)

        self.setFixedWidth(self.THUMB_WIDTH + 12)
        self.setStyleSheet(
            f"ResultCard {{"
            f"  background-color: {c.card_bg};"
            f"  border: 1px solid {c.card_border};"
            f"  border-radius: {Theme.BORDER_RADIUS}px;"
            f"}}"
            f"ResultCard:hover {{"
            f"  border-color: {c.accent};"
            f"}}"
        )

        # Thumbnail
        self._thumb = QLabel()
        self._thumb.setFixedSize(self.THUMB_WIDTH, self.THUMB_HEIGHT)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            f"background-color: {c.bg_tertiary};"
            f"border-radius: {Theme.BORDER_RADIUS_SMALL}px;"
        )
        self._load_thumbnail()
        self.main_layout.addWidget(self._thumb)

        # Badges row: score + clase + timestamp
        badges = self.create_horizontal_layout()
        badges.setSpacing(4)

        score_badge = self.create_badge(f"{self._result.score:.3f}", "success")
        class_badge = self.create_badge(self._result.class_name, "error")
        time_badge = self.create_badge(self._result.timestamp_formatted, "warning")

        badges.addWidget(score_badge)
        badges.addWidget(class_badge)
        badges.addWidget(time_badge)
        badges.addStretch()

        self.main_layout.addLayout(badges)

        # Descripcion truncada
        if self._result.description:
            desc_text = self._result.description
            if len(desc_text) > 60:
                desc_text = desc_text[:57] + "..."
            desc = QLabel(desc_text)
            desc.setProperty("class", "muted")
            desc.setWordWrap(True)
            desc.setStyleSheet(f"font-size: {Theme.FONT_SIZE_SMALL}px;")
            self.main_layout.addWidget(desc)

    def _load_thumbnail(self) -> None:
        """Carga la imagen del crop como thumbnail."""
        crop_path = Path(self._result.crop_path)
        if crop_path.exists():
            pixmap = QPixmap(str(crop_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.THUMB_WIDTH,
                    self.THUMB_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._thumb.setPixmap(scaled)
                return
        self._thumb.setText("Sin imagen")

    def mousePressEvent(self, event) -> None:
        """Emite clicked con el indice al hacer click."""
        self.clicked.emit(self._index)
        super().mousePressEvent(event)
