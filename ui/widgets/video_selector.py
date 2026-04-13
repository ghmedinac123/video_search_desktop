"""
Selector de video con drag and drop + boton explorar.

Responsabilidad UNICA: permitir al usuario seleccionar un video
y mostrar su metadata (duracion, FPS, resolucion).

Hereda de BaseWidget. Emite signal video_selected(Path).

Uso:
    from ui.widgets.video_selector import VideoSelector

    selector = VideoSelector()
    selector.video_selected.connect(lambda p: print(f"Video: {p}"))
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QFileDialog
from PySide6.QtCore import Signal, Qt

from ui.base_widget import BaseWidget
from ui.theme import Theme
from core.frame_extractor import FrameExtractor


class VideoSelector(BaseWidget):
    """Selector de video con drag-drop y explorador de archivos."""

    video_selected = Signal(object)

    SUPPORTED_FORMATS: str = "Videos (*.mp4 *.avi *.mkv *.mov *.wmv *.flv)"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._video_path: Path | None = None
        self._extractor = FrameExtractor()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construye la zona de drop + boton + metadata."""
        c = Theme.colors()

        # Zona de drop
        self._drop_zone = QLabel(
            "Arrastra un video aqui\no haz clic para seleccionar\n\n"
            "MP4, AVI, MKV, MOV"
        )
        self._drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_zone.setMinimumHeight(120)
        self._drop_zone.setStyleSheet(
            f"QLabel {{"
            f"  background-color: {c.bg_tertiary};"
            f"  border: 2px dashed {c.border};"
            f"  border-radius: {Theme.BORDER_RADIUS_LARGE}px;"
            f"  color: {c.text_secondary};"
            f"  font-size: {Theme.FONT_SIZE}px;"
            f"  padding: 20px;"
            f"}}"
        )
        self._drop_zone.setCursor(Qt.CursorShape.PointingHandCursor)
        self._drop_zone.mousePressEvent = lambda e: self._browse()
        self.main_layout.addWidget(self._drop_zone)

        # Habilitar drag and drop
        self.setAcceptDrops(True)

        # Metadata del video (oculta hasta seleccionar)
        self._meta_card = self.create_card()
        self._meta_card.setVisible(False)
        meta_layout = self._meta_card.layout()

        self._file_label = QLabel("")
        self._file_label.setStyleSheet("font-weight: 600;")
        meta_layout.addWidget(self._file_label)

        self._info_label = QLabel("")
        self._info_label.setProperty("class", "secondary")
        meta_layout.addWidget(self._info_label)

        self.main_layout.addWidget(self._meta_card)

    def _browse(self) -> None:
        """Abre dialogo de seleccion de archivo."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar video", "", self.SUPPORTED_FORMATS,
        )
        if path:
            self._load_video(Path(path))

    def _load_video(self, path: Path) -> None:
        """Carga metadata del video y emite signal."""
        try:
            metadata = self._extractor.get_video_metadata(path)
            self._video_path = path

            self._file_label.setText(metadata.file_name)
            self._info_label.setText(
                f"Duracion: {metadata.duration_formatted}  |  "
                f"FPS: {metadata.fps:.0f}  |  "
                f"Resolucion: {metadata.resolution}  |  "
                f"{metadata.file_size_mb:.0f} MB"
            )
            self._meta_card.setVisible(True)

            c = Theme.colors()
            self._drop_zone.setText(f"Video cargado: {metadata.file_name}")
            self._drop_zone.setStyleSheet(
                f"QLabel {{"
                f"  background-color: {c.success}15;"
                f"  border: 2px solid {c.success}40;"
                f"  border-radius: {Theme.BORDER_RADIUS_LARGE}px;"
                f"  color: {c.success};"
                f"  font-size: {Theme.FONT_SIZE}px;"
                f"  padding: 20px;"
                f"}}"
            )

            self.video_selected.emit(path)

        except Exception as e:
            self.show_error("Error", f"No se pudo cargar el video:\n{e}")

    @property
    def video_path(self) -> Path | None:
        """Ruta del video seleccionado, o None."""
        return self._video_path

    # ── Drag and Drop ──

    def dragEnterEvent(self, event) -> None:
        """Acepta drag si es un archivo de video."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        """Procesa el archivo dropeado."""
        urls = event.mimeData().urls()
        if urls:
            path = Path(urls[0].toLocalFile())
            if path.suffix.lower() in (".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"):
                self._load_video(path)
