"""
Video Search Desktop — Punto de entrada principal.

Inicializa logger, settings, configura rutas de modelos,
y arranca la interfaz PySide6 con todos los paneles conectados.

Uso:
    python main.py
"""

from __future__ import annotations

import sys

from models.settings import get_settings

# CRITICO: Configurar rutas de modelos ANTES de importar cualquier modelo AI
settings = get_settings()
settings.ensure_directories()
settings.setup_model_environment()

from PySide6.QtWidgets import QApplication

from core.logger import logger, setup_logger
from core.database import Database
from core.model_manager import ModelManager
from core.indexer import Indexer
from core.searcher import Searcher
from ui.theme import Theme
from ui.main_window import MainWindow
from ui.widgets.model_panel import ModelPanel
from ui.widgets.indexing_panel import IndexingPanel
from ui.widgets.search_panel import SearchPanel
from ui.widgets.stats_panel import StatsPanel
from ui.workers.index_worker import IndexWorker
from ui.workers.search_worker import SearchWorker


class Application:
    """
    Clase principal que ensambla toda la aplicacion.

    Responsabilidad UNICA: conectar core backend con UI frontend.
    Crea las dependencias y las inyecta en los paneles.
    """

    def __init__(self) -> None:
        setup_logger(
            level=settings.log_level,
            log_dir=settings.log_dir,
        )

        logger.info("=" * 50)
        logger.info("VIDEO SEARCH DESKTOP — Iniciando")
        logger.info("=" * 50)
        logger.info(f"Python: {sys.version}")
        logger.info(f"Models cache: {settings.models_cache_dir.resolve()}")
        logger.info(f"ChromaDB: {settings.chromadb_dir.resolve()}")

        # Core backend
        self._mm = ModelManager.get_instance()
        self._db = Database()
        self._indexer = Indexer(self._mm, self._db, settings)
        self._searcher = Searcher(self._mm, self._db)

        # Qt Application
        self._app = QApplication(sys.argv)
        self._app.setStyleSheet(Theme.get_stylesheet())

        # Ventana principal
        self._window = MainWindow()
        self._setup_panels()

    def _setup_panels(self) -> None:
        """Reemplaza placeholders por paneles reales conectados."""

        # Panel 0: Modelos
        self._model_panel = ModelPanel()
        self._window.set_panel(0, self._model_panel)

        # Panel 1: Indexacion
        self._indexing_panel = IndexingPanel()
        self._connect_indexing()
        self._window.set_panel(1, self._indexing_panel)

        # Panel 2: Busqueda
        self._search_panel = SearchPanel()
        self._connect_search()
        self._window.set_panel(2, self._search_panel)

        # Panel 3: Estadisticas
        self._stats_panel = StatsPanel()
        self._stats_panel.set_database(self._db)
        self._window.set_panel(3, self._stats_panel)

    def _connect_indexing(self) -> None:
        """Conecta botones del panel indexacion con el IndexWorker."""
        panel = self._indexing_panel

        def start_indexing():
            video_path = panel.video_selector.video_path
            if video_path is None:
                panel.show_error("Error", "Selecciona un video primero")
                return

            if not self._mm.is_ready():
                panel.show_error(
                    "Error",
                    "Carga detector + embedder en el tab Modelos primero",
                )
                return

            panel.set_running(True)

            self._index_worker = IndexWorker(
                indexer=self._indexer,
                video_path=video_path,
                interval=panel.interval,
            )
            self._index_worker.progress.connect(panel.update_progress)
            self._index_worker.finished.connect(
                lambda result: self._on_index_finished(result)
            )
            self._index_worker.error.connect(
                lambda msg: self._on_index_error(msg)
            )
            self._index_worker.start()

        def pause_indexing():
            if hasattr(self, "_index_worker"):
                self._index_worker.pause()

        def cancel_indexing():
            if hasattr(self, "_index_worker"):
                self._index_worker.cancel()
                panel.set_running(False)

        panel.start_button.clicked.connect(start_indexing)
        panel.pause_button.clicked.connect(pause_indexing)
        panel.cancel_button.clicked.connect(cancel_indexing)

    def _on_index_finished(self, result) -> None:
        """Callback cuando termina la indexacion."""
        self._indexing_panel.set_running(False)
        self._indexing_panel.set_result(
            f"Completado: {result.total_frames} frames, "
            f"{result.total_detections} detecciones, "
            f"{result.total_stored} almacenados en {result.elapsed_seconds:.0f}s"
        )
        self._stats_panel.refresh()
        logger.info("Indexacion completada exitosamente")

    def _on_index_error(self, message: str) -> None:
        """Callback cuando falla la indexacion."""
        self._indexing_panel.set_running(False)
        self._indexing_panel.show_error("Error de indexacion", message)

    def _connect_search(self) -> None:
        """Conecta barra de busqueda con el SearchWorker."""
        panel = self._search_panel

        def do_search():
            query = panel.query_text
            if not query:
                return

            if not self._mm.embedder or not self._mm.embedder.is_loaded():
                panel.show_error(
                    "Error",
                    "Carga el embedder (CLIP) en el tab Modelos primero",
                )
                return

            self._search_worker = SearchWorker(
                searcher=self._searcher,
                query_text=query,
                n_results=30,
            )
            self._search_worker.results.connect(panel.set_results)
            self._search_worker.error.connect(
                lambda msg: panel.show_error("Error de busqueda", msg)
            )
            self._search_worker.start()

        panel.search_button.clicked.connect(do_search)
        panel.search_input.returnPressed.connect(do_search)

    def run(self) -> int:
        """Muestra la ventana y ejecuta el event loop."""
        self._window.show()
        logger.info("Interfaz lista — ventana abierta")
        return self._app.exec()


def main() -> None:
    """Punto de entrada."""
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
