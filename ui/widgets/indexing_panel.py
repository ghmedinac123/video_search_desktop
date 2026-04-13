"""
Panel de indexacion de video.

Responsabilidad UNICA: permitir al usuario cargar un video,
configurar intervalo, y ejecutar la indexacion con progreso visual.

Hereda de BaseWidget. Compone: VideoSelector + ProgressGroup.
Conecta con Indexer via IndexWorker (nunca bloquea UI).

Uso:
    from ui.widgets.indexing_panel import IndexingPanel
    panel = IndexingPanel()
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QLabel, QSlider, QHBoxLayout
from PySide6.QtCore import Qt

from ui.base_widget import BaseWidget
from ui.widgets.video_selector import VideoSelector
from ui.widgets.progress_group import ProgressGroup
from ui.theme import Theme
from models.indexing import IndexProgress, IndexStage


class IndexingPanel(BaseWidget):
    """Panel completo de indexacion con progreso en tiempo real."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construye: video selector + slider + progreso + botones."""
        # Header
        header = self.create_header("Indexar video")
        self.main_layout.addWidget(header)
        desc = self.create_secondary_label(
            "Carga un video, ajusta el intervalo y ejecuta el pipeline"
        )
        self.main_layout.addWidget(desc)
        self.main_layout.addWidget(self.create_separator())

        # Video selector (drag and drop)
        self._video_selector = VideoSelector()
        self.main_layout.addWidget(self._video_selector)

        # Slider intervalo de muestreo
        self._add_interval_slider()

        self.main_layout.addWidget(self.create_separator())

        # Barras de progreso
        progress_title = self.create_section_title("Progreso")
        self.main_layout.addWidget(progress_title)

        self._progress = ProgressGroup(
            bars=["Frames", "Detecciones", "Embeddings", "Descripciones"],
        )
        self.main_layout.addWidget(self._progress)

        # Counters
        counters_row = self.create_horizontal_layout()
        self._fps_label = QLabel("Velocidad: --")
        self._fps_label.setProperty("class", "secondary")
        counters_row.addWidget(self._fps_label)

        self._time_label = QLabel("Tiempo restante: --")
        self._time_label.setProperty("class", "secondary")
        counters_row.addWidget(self._time_label)
        counters_row.addStretch()
        self.main_layout.addLayout(counters_row)

        # Botones
        btn_row = self.create_horizontal_layout()
        self._start_btn = self.create_button("Iniciar indexacion", primary=True)
        self._pause_btn = self.create_button("Pausar")
        self._pause_btn.setEnabled(False)
        self._cancel_btn = self.create_button("Cancelar", danger=True)
        self._cancel_btn.setEnabled(False)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._pause_btn)
        btn_row.addWidget(self._cancel_btn)
        btn_row.addStretch()
        self.main_layout.addLayout(btn_row)

        # Resultado
        self._result_label = QLabel("")
        self._result_label.setProperty("class", "secondary")
        self.main_layout.addWidget(self._result_label)

        self.main_layout.addStretch()

    def _add_interval_slider(self) -> None:
        """Agrega slider de intervalo de muestreo."""
        row = self.create_horizontal_layout()

        label = QLabel("Intervalo muestreo:")
        label.setProperty("class", "secondary")
        row.addWidget(label)

        self._interval_slider = QSlider(Qt.Orientation.Horizontal)
        self._interval_slider.setMinimum(1)
        self._interval_slider.setMaximum(10)
        self._interval_slider.setValue(2)
        self._interval_slider.setTickInterval(1)
        self._interval_slider.valueChanged.connect(self._on_interval_changed)
        row.addWidget(self._interval_slider, stretch=1)

        self._interval_label = QLabel("2s")
        self._interval_label.setFixedWidth(30)
        row.addWidget(self._interval_label)

        self.main_layout.addLayout(row)

    def _on_interval_changed(self, value: int) -> None:
        """Actualiza label del slider."""
        self._interval_label.setText(f"{value}s")

    # ── API publica ──

    def update_progress(self, progress: IndexProgress) -> None:
        """Actualiza las barras y counters desde IndexWorker signal."""
        self._progress.update_bar(
            "Frames", progress.frames_processed, progress.frames_total,
        )
        self._progress.update_bar(
            "Detecciones", progress.detections_processed, progress.detections_total,
        )
        self._progress.update_bar(
            "Embeddings", progress.detections_processed, progress.detections_total,
        )
        self._progress.update_bar(
            "Descripciones", progress.crops_stored, progress.detections_total,
        )

        self._fps_label.setText(
            f"Velocidad: {progress.fps_processing:.1f} frames/s"
        )

        remaining = int(progress.estimated_remaining_seconds)
        mins, secs = divmod(remaining, 60)
        self._time_label.setText(f"Tiempo restante: ~{mins}:{secs:02d}")

    def set_running(self, running: bool) -> None:
        """Habilita/deshabilita botones segun estado."""
        self._start_btn.setEnabled(not running)
        self._pause_btn.setEnabled(running)
        self._cancel_btn.setEnabled(running)
        self._video_selector.setEnabled(not running)
        self._interval_slider.setEnabled(not running)

    def set_result(self, text: str) -> None:
        """Muestra mensaje de resultado final."""
        self._result_label.setText(text)

    @property
    def interval(self) -> int:
        """Intervalo de muestreo seleccionado en segundos."""
        return self._interval_slider.value()

    @property
    def start_button(self):
        return self._start_btn

    @property
    def pause_button(self):
        return self._pause_btn

    @property
    def cancel_button(self):
        return self._cancel_btn

    @property
    def video_selector(self) -> VideoSelector:
        return self._video_selector
