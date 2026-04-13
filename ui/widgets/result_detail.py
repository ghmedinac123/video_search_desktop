"""
Vista detalle de un resultado de busqueda.

Responsabilidad UNICA: mostrar el frame completo con bounding box,
crop ampliado, metadata, descripcion VLM, y boton para abrir video.

Hereda de BaseWidget.

Uso:
    detail = ResultDetail()
    detail.show_result(search_result)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import Qt

from ui.base_widget import BaseWidget
from ui.theme import Theme
from models.search import SearchResult


class ResultDetail(BaseWidget):
    """Vista detalle de un resultado — frame + crop + metadata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_result: SearchResult | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construye: imagen + metadata + botones."""
        c = Theme.colors()

        # Layout horizontal: imagen izquierda + metadata derecha
        content_row = self.create_horizontal_layout()

        # Frame / Crop image
        self._image_label = QLabel("Selecciona un resultado")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(320, 240)
        self._image_label.setStyleSheet(
            f"background-color: {c.bg_tertiary};"
            f"border-radius: {Theme.BORDER_RADIUS}px;"
            f"color: {c.text_muted};"
        )
        content_row.addWidget(self._image_label, stretch=2)

        # Metadata column
        meta_widget = BaseWidget()
        meta_layout = meta_widget.main_layout
        meta_layout.setContentsMargins(12, 0, 0, 0)

        self._score_label = QLabel("")
        self._class_label = QLabel("")
        self._time_label = QLabel("")
        self._video_label = QLabel("")
        self._desc_label = QLabel("")
        self._desc_label.setWordWrap(True)

        for lbl in (
            self._score_label,
            self._class_label,
            self._time_label,
            self._video_label,
        ):
            lbl.setProperty("class", "secondary")
            meta_layout.addWidget(lbl)

        meta_layout.addWidget(self.create_separator())

        desc_title = QLabel("Descripcion VLM:")
        desc_title.setStyleSheet("font-weight: 600;")
        meta_layout.addWidget(desc_title)
        self._desc_label.setProperty("class", "secondary")
        meta_layout.addWidget(self._desc_label)

        meta_layout.addStretch()

        # Boton abrir video
        self._open_btn = self.create_button("Abrir video en este momento", primary=True)
        self._open_btn.clicked.connect(self._open_video)
        self._open_btn.setEnabled(False)
        meta_layout.addWidget(self._open_btn)

        content_row.addWidget(meta_widget, stretch=1)
        self.main_layout.addLayout(content_row)

    def show_result(self, result: SearchResult) -> None:
        """Muestra el detalle de un resultado."""
        self._current_result = result

        # Cargar imagen (crop o frame)
        self._load_image(result)

        # Metadata
        self._score_label.setText(f"Score: {result.score:.4f}")
        self._class_label.setText(f"Clase: {result.class_name} ({result.confidence:.2f})")
        self._time_label.setText(f"Tiempo: {result.timestamp_formatted}")
        self._video_label.setText(f"Video: {Path(result.video_source).name}")
        self._desc_label.setText(result.description or "Sin descripcion")

        self._open_btn.setEnabled(True)

    def _load_image(self, result: SearchResult) -> None:
        """Carga la imagen del frame con bounding box dibujado."""
        frame_path = Path(result.frame_path)
        crop_path = Path(result.crop_path)

        # Intentar frame completo primero, luego crop
        image_path = frame_path if frame_path.exists() else crop_path

        if image_path.exists():
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                # Dibujar bounding box si tenemos el frame completo
                if frame_path.exists() and result.bbox:
                    pixmap = self._draw_bbox(pixmap, result.bbox)

                scaled = pixmap.scaled(
                    self._image_label.width(),
                    self._image_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._image_label.setPixmap(scaled)
                return

        self._image_label.setText("Imagen no disponible")

    def _draw_bbox(self, pixmap: QPixmap, bbox_str: str) -> QPixmap:
        """Dibuja bounding box sobre el frame."""
        try:
            coords = bbox_str.strip("[]").split(",")
            x1, y1, x2, y2 = [int(c.strip()) for c in coords]

            result_pixmap = pixmap.copy()
            painter = QPainter(result_pixmap)
            pen = QPen(QColor("#3b82f6"), 3)
            painter.setPen(pen)
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
            painter.end()
            return result_pixmap
        except Exception:
            return pixmap

    def _open_video(self) -> None:
        """Abre el video en el segundo exacto con el reproductor del sistema."""
        if self._current_result is None:
            return

        video = self._current_result.video_source
        seconds = int(self._current_result.timestamp_seconds)

        try:
            # Intentar ffplay primero (mas preciso con -ss)
            subprocess.Popen(
                ["ffplay", "-ss", str(seconds), "-autoexit", video],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            try:
                # Fallback: abrir con reproductor del sistema
                import os
                os.startfile(video)
            except Exception as e:
                self.show_error("Error", f"No se pudo abrir el video:\n{e}")

    def clear(self) -> None:
        """Limpia el detalle."""
        self._current_result = None
        self._image_label.clear()
        self._image_label.setText("Selecciona un resultado")
        self._score_label.setText("")
        self._class_label.setText("")
        self._time_label.setText("")
        self._video_label.setText("")
        self._desc_label.setText("")
        self._open_btn.setEnabled(False)
