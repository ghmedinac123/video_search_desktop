"""
Ventana principal de la aplicación.

Responsabilidad ÚNICA: componer la ventana con sidebar + paneles
+ status bar. NO contiene lógica de negocio.

Uso:
    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
    QStatusBar,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer

from ui.theme import Theme
from ui.base_widget import BaseWidget
from ui.widgets.sidebar import Sidebar
from core.gpu_utils import GPUUtils


class _PlaceholderPanel(BaseWidget):
    """Panel placeholder temporal hasta implementar los reales."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        header = self.create_header(title)
        self.main_layout.addWidget(header)
        desc = self.create_secondary_label(
            f"Panel '{title}' — se implementa en la siguiente subfase."
        )
        self.main_layout.addWidget(desc)
        self.main_layout.addStretch()


class MainWindow(QMainWindow):
    """
    Ventana principal — compone sidebar + paneles + status bar.

    El QStackedWidget central cambia de panel cuando la sidebar
    emite page_changed. Los paneles se reemplazan en fases posteriores.
    """

    WINDOW_TITLE: str = "Video Search Desktop"
    MIN_WIDTH: int = 1100
    MIN_HEIGHT: int = 700

    def __init__(self) -> None:
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self._setup_status_bar()
        self._start_gpu_timer()

    def _setup_window(self) -> None:
        """Configura propiedades de la ventana."""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.resize(1280, 800)
        self.setStyleSheet(Theme.get_stylesheet())

    def _setup_ui(self) -> None:
        """Construye el layout principal: sidebar + contenido."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar izquierda
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._on_page_changed)
        layout.addWidget(self._sidebar)

        # Contenido central (paneles apilados)
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        # Paneles placeholder (se reemplazan en subfases posteriores)
        self._panels: list[QWidget] = [
            _PlaceholderPanel("Modelos"),
            _PlaceholderPanel("Indexar"),
            _PlaceholderPanel("Buscar"),
            _PlaceholderPanel("Estadísticas"),
        ]
        for panel in self._panels:
            self._stack.addWidget(panel)

    def _setup_status_bar(self) -> None:
        """Configura la barra de estado inferior."""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        # GPU info
        self._gpu_label = QLabel("GPU: detectando...")
        self._status_bar.addWidget(self._gpu_label)

        # VRAM
        self._vram_label = QLabel("")
        self._status_bar.addWidget(self._vram_label)

        # Separador
        self._status_bar.addWidget(QLabel("  |  "))

        # ChromaDB
        self._db_label = QLabel("ChromaDB: embebido")
        self._status_bar.addPermanentWidget(self._db_label)

        # Detectar GPU inicial
        gpu_info = GPUUtils.detect_gpu()
        if gpu_info.available:
            self._gpu_label.setText(
                f"GPU: {gpu_info.device_name}"
            )
        else:
            self._gpu_label.setText("GPU: no detectada (modo CPU)")

    def _start_gpu_timer(self) -> None:
        """Inicia timer que actualiza VRAM cada 2 segundos."""
        self._gpu_timer = QTimer(self)
        self._gpu_timer.timeout.connect(self._update_vram)
        self._gpu_timer.start(2000)

    def _update_vram(self) -> None:
        """Actualiza el label de VRAM en la status bar."""
        vram = GPUUtils.get_vram_status()
        if vram.total_gb > 0:
            self._vram_label.setText(
                f"VRAM: {vram.used_gb:.1f}/{vram.total_gb:.0f} GB "
                f"({vram.usage_percent:.0f}%) | "
                f"{vram.temperature_celsius} C"
            )

    def _on_page_changed(self, index: int) -> None:
        """Cambia el panel visible cuando la sidebar emite click."""
        self._stack.setCurrentIndex(index)

    # ── API pública para reemplazar paneles ──

    def set_panel(self, index: int, widget: QWidget) -> None:
        """
        Reemplaza un panel placeholder por el widget real.

        Args:
            index: 0=Modelos, 1=Indexar, 2=Buscar, 3=Stats.
            widget: Widget real que reemplaza al placeholder.
        """
        old = self._stack.widget(index)
        self._stack.removeWidget(old)
        old.deleteLater()
        self._stack.insertWidget(index, widget)
        self._panels[index] = widget
