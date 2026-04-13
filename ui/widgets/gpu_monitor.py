"""
Widget de monitoreo GPU en tiempo real.

Responsabilidad UNICA: mostrar VRAM usada/total, temperatura,
utilizacion, y barra segmentada por modelo. Se actualiza cada segundo.

Hereda de BaseWidget. Reutilizable: se usa en panel Modelos
y en la status bar.

Uso:
    from ui.widgets.gpu_monitor import GPUMonitorWidget

    monitor = GPUMonitorWidget()
    # Se auto-actualiza con QTimer interno
    monitor.stop()   # Detener actualizacion
    monitor.start()  # Reanudar
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
)
from PySide6.QtCore import QTimer

from ui.base_widget import BaseWidget
from ui.theme import Theme
from core.gpu_utils import GPUUtils
from models.gpu import VRAMStatus


class GPUMonitorWidget(BaseWidget):
    """Monitor GPU en tiempo real con barra VRAM y metricas."""

    UPDATE_INTERVAL_MS: int = 1000

    def __init__(self, compact: bool = False, parent: QWidget | None = None) -> None:
        """
        Args:
            compact: True para version mini (solo barra + texto).
            parent: Widget padre.
        """
        super().__init__(parent)
        self._compact = compact
        self._setup_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(self.UPDATE_INTERVAL_MS)
        self._update()

    def _setup_ui(self) -> None:
        """Construye la UI del monitor."""
        if self._compact:
            self._setup_compact()
        else:
            self._setup_full()

    def _setup_compact(self) -> None:
        """Version compacta: una linea con barra + texto."""
        row = self.create_horizontal_layout()
        self._vram_label = QLabel("VRAM: --")
        self._vram_label.setProperty("class", "secondary")
        row.addWidget(self._vram_label)

        self._vram_bar = QProgressBar()
        self._vram_bar.setFixedHeight(8)
        self._vram_bar.setFixedWidth(120)
        self._vram_bar.setTextVisible(False)
        row.addWidget(self._vram_bar)

        self._temp_label = QLabel("")
        self._temp_label.setProperty("class", "muted")
        row.addWidget(self._temp_label)

        row.addStretch()
        self.main_layout.addLayout(row)

    def _setup_full(self) -> None:
        """Version completa: metricas + barra grande + detalles."""
        # Titulo
        title = self.create_section_title("GPU Monitor")
        self.main_layout.addWidget(title)

        # Card contenedora
        card = self.create_card()
        card_layout = card.layout()

        # Fila de metricas
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        self._gpu_name_label = self._create_metric("GPU", "--")
        self._vram_used_label = self._create_metric("VRAM usada", "--")
        self._vram_free_label = self._create_metric("VRAM libre", "--")
        self._util_label = self._create_metric("Uso GPU", "--")
        self._temp_full_label = self._create_metric("Temperatura", "--")

        metrics_row.addWidget(self._gpu_name_label)
        metrics_row.addWidget(self._vram_used_label)
        metrics_row.addWidget(self._vram_free_label)
        metrics_row.addWidget(self._util_label)
        metrics_row.addWidget(self._temp_full_label)

        card_layout.addLayout(metrics_row)

        # Barra VRAM grande
        self._vram_bar_full = QProgressBar()
        self._vram_bar_full.setFixedHeight(16)
        self._vram_bar_full.setTextVisible(True)
        self._vram_bar_full.setFormat("%v / %m GB")
        card_layout.addWidget(self._vram_bar_full)

        self.main_layout.addWidget(card)

        # Detectar GPU una vez
        gpu_info = GPUUtils.detect_gpu()
        if gpu_info.available:
            self._gpu_name_label.findChild(QLabel, "value").setText(gpu_info.device_name)
        else:
            self._gpu_name_label.findChild(QLabel, "value").setText("No detectada")

    def _create_metric(self, label: str, value: str) -> QWidget:
        """Crea un widget metrica reutilizable: label arriba, valor abajo."""
        c = Theme.colors()
        container = QWidget()
        layout = QHBoxLayout(container) if self._compact else __import__(
            "PySide6.QtWidgets", fromlist=["QVBoxLayout"]
        ).QVBoxLayout(container)

        from PySide6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"font-size: {Theme.FONT_SIZE_SMALL}px;"
            f"color: {c.text_muted};"
            f"font-weight: 500;"
            f"letter-spacing: 0.3px;"
        )
        layout.addWidget(lbl)

        val = QLabel(value)
        val.setObjectName("value")
        val.setStyleSheet(
            f"font-size: 18px;"
            f"font-weight: 600;"
            f"color: {c.text_primary};"
        )
        layout.addWidget(val)

        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return container

    def _update(self) -> None:
        """Lee sensores GPU y actualiza la UI."""
        vram = GPUUtils.get_vram_status()

        if self._compact:
            self._update_compact(vram)
        else:
            self._update_full(vram)

    def _update_compact(self, vram: VRAMStatus) -> None:
        """Actualiza version compacta."""
        if vram.total_gb > 0:
            self._vram_label.setText(
                f"VRAM: {vram.used_gb:.1f}/{vram.total_gb:.0f} GB"
            )
            self._vram_bar.setMaximum(int(vram.total_gb * 10))
            self._vram_bar.setValue(int(vram.used_gb * 10))
            self._temp_label.setText(f"{vram.temperature_celsius} C")
        else:
            self._vram_label.setText("VRAM: N/A")

    def _update_full(self, vram: VRAMStatus) -> None:
        """Actualiza version completa."""
        if vram.total_gb > 0:
            self._vram_used_label.findChild(QLabel, "value").setText(
                f"{vram.used_gb:.1f} GB"
            )
            self._vram_free_label.findChild(QLabel, "value").setText(
                f"{vram.free_gb:.1f} GB"
            )
            self._util_label.findChild(QLabel, "value").setText(
                f"{vram.gpu_utilization_percent:.0f}%"
            )
            self._temp_full_label.findChild(QLabel, "value").setText(
                f"{vram.temperature_celsius} C ({vram.temperature_status})"
            )
            self._vram_bar_full.setMaximum(int(vram.total_gb * 10))
            self._vram_bar_full.setValue(int(vram.used_gb * 10))

    def start(self) -> None:
        """Inicia la actualizacion periodica."""
        if not self._timer.isActive():
            self._timer.start(self.UPDATE_INTERVAL_MS)

    def stop(self) -> None:
        """Detiene la actualizacion periodica."""
        self._timer.stop()
