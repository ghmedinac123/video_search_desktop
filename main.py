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
from core.stream_capture import StreamCapture
from ui.theme import Theme
from ui.main_window import MainWindow
from ui.widgets.model_panel import ModelPanel
from ui.widgets.indexing_panel import IndexingPanel
from ui.widgets.search_panel import SearchPanel
from ui.widgets.stats_panel import StatsPanel
from ui.widgets.camera_panel import CameraPanel
from ui.workers.index_worker import IndexWorker
from ui.workers.model_download_worker import ModelDownloadWorker
from ui.workers.model_load_worker import ModelLoadWorker
from ui.workers.search_worker import SearchWorker
from ui.workers.stream_worker import StreamWorker


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

        # Workers de streaming RTSP activos: camera_id -> StreamWorker
        self._stream_workers: dict[str, StreamWorker] = {}

        # Ventana principal
        self._window = MainWindow()
        self._setup_panels()
        self._app.aboutToQuit.connect(self._stop_all_streams)

    def _setup_panels(self) -> None:
        """Reemplaza placeholders por paneles reales conectados."""

        # Panel 0: Modelos
        self._model_panel = ModelPanel()
        self._connect_models()
        self._window.set_panel(0, self._model_panel)

        # Panel 1: Indexacion
        self._indexing_panel = IndexingPanel()
        self._connect_indexing()
        self._window.set_panel(1, self._indexing_panel)

        # Panel 2: Busqueda
        self._search_panel = SearchPanel()
        self._connect_search()
        self._window.set_panel(2, self._search_panel)

        # Panel 3: Camaras RTSP
        self._camera_panel = CameraPanel()
        self._connect_cameras()
        self._window.set_panel(3, self._camera_panel)

        # Panel 4: Estadisticas
        self._stats_panel = StatsPanel()
        self._stats_panel.set_database(self._db)
        self._window.set_panel(4, self._stats_panel)

    def _connect_models(self) -> None:
        """Conecta botones Descargar/Cargar del panel Modelos con workers."""
        panel = self._model_panel

        def download_selected():
            """Descarga los modelos seleccionados."""
            selected = []
            if panel.selected_detector:
                selected.append(panel.selected_detector)
            if panel.selected_embedder:
                selected.append(panel.selected_embedder)
            if panel.selected_describer:
                selected.append(panel.selected_describer)

            if not selected:
                panel.show_error("Error", "No hay modelos seleccionados")
                return

            panel._download_btn.setEnabled(False)
            panel._download_btn.setText("Descargando...")

            self._dl_worker = ModelDownloadWorker(
                registry=self._mm.registry,
                model_ids=selected,
            )
            self._dl_worker.progress.connect(
                lambda mid, p: logger.info(f"Descargando {mid}: {p*100:.0f}%")
            )
            self._dl_worker.finished.connect(
                lambda: self._on_download_finished()
            )
            self._dl_worker.error.connect(
                lambda msg: self._on_download_error(msg)
            )
            self._dl_worker.start()

        def load_selected():
            """Carga los modelos seleccionados en GPU."""
            panel._load_btn.setEnabled(False)
            panel._load_btn.setText("Cargando en GPU...")

            self._load_worker = ModelLoadWorker(
                manager=self._mm,
                detector_id=panel.selected_detector,
                embedder_id=panel.selected_embedder,
                describer_id=panel.selected_describer,
            )
            self._load_worker.model_loaded.connect(
                lambda mid: logger.info(f"Modelo cargado en GPU: {mid}")
            )
            self._load_worker.all_loaded.connect(
                lambda: self._on_load_finished()
            )
            self._load_worker.error.connect(
                lambda msg: self._on_load_error(msg)
            )
            self._load_worker.start()

        panel._download_btn.clicked.connect(download_selected)
        panel._load_btn.clicked.connect(load_selected)

    def _on_download_finished(self) -> None:
        """Callback cuando terminan las descargas."""
        self._model_panel._download_btn.setEnabled(True)
        self._model_panel._download_btn.setText("Descargar seleccionados")
        self._mm.registry.scan_downloaded_status()
        self._model_panel.show_success(
            "Descarga completa",
            "Modelos descargados. Ahora haz click en Cargar en GPU.",
        )
        logger.info("Todos los modelos descargados")

    def _on_download_error(self, message: str) -> None:
        """Callback cuando falla una descarga."""
        self._model_panel._download_btn.setEnabled(True)
        self._model_panel._download_btn.setText("Descargar seleccionados")
        self._model_panel.show_error("Error de descarga", message)

    def _on_load_finished(self) -> None:
        """Callback cuando todos los modelos estan en GPU."""
        self._model_panel._load_btn.setEnabled(True)
        self._model_panel._load_btn.setText("Cargar en GPU")
        self._model_panel.show_success(
            "Modelos cargados",
            "Todos los modelos estan en GPU. Puedes indexar y buscar.",
        )
        logger.info("Todos los modelos cargados en GPU")

    def _on_load_error(self, message: str) -> None:
        """Callback cuando falla la carga en GPU."""
        self._model_panel._load_btn.setEnabled(True)
        self._model_panel._load_btn.setText("Cargar en GPU")
        self._model_panel.show_error("Error cargando en GPU", message)

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

    def _connect_cameras(self) -> None:
        """Conecta el panel de camaras con StreamWorker + pipeline."""
        panel = self._camera_panel

        panel.start_capture.connect(self._start_stream)
        panel.stop_capture.connect(self._stop_stream)
        panel.start_all.connect(self._start_all_streams)
        panel.stop_all.connect(self._stop_all_streams)

    def _start_stream(self, camera_id: str) -> None:
        """Inicia captura RTSP para UNA camara."""
        panel = self._camera_panel

        # Verificar modelos cargados
        if not self._mm.is_ready():
            panel.show_error(
                "Modelos no cargados",
                "Carga el detector + embedder en el tab Modelos primero.",
            )
            card = panel._cards.get(camera_id)
            if card:
                card.set_connected(False)
            return

        # Evitar doble inicio
        if camera_id in self._stream_workers:
            logger.warning(f"Stream {camera_id} ya esta activo")
            return

        camera = panel.get_camera(camera_id)
        if camera is None:
            panel.show_error("Error", f"Camara {camera_id} no encontrada")
            return

        capture = StreamCapture(camera)
        worker = StreamWorker(capture=capture, indexer=self._indexer)
        worker.status_updated.connect(panel.update_camera_status)
        worker.error.connect(
            lambda msg, cid=camera_id: self._on_stream_error(cid, msg)
        )
        worker.finished.connect(
            lambda cid=camera_id: self._on_stream_finished(cid)
        )

        self._stream_workers[camera_id] = worker
        worker.start()
        logger.info(f"Stream iniciado: {camera_id} — {camera.name}")

    def _stop_stream(self, camera_id: str) -> None:
        """Detiene captura RTSP para UNA camara."""
        worker = self._stream_workers.get(camera_id)
        if worker is None:
            return
        worker.cancel()
        logger.info(f"Stream detenido: {camera_id}")

    def _start_all_streams(self) -> None:
        """Inicia captura para todas las camaras configuradas."""
        for camera in self._camera_panel.get_cameras():
            if camera.enabled and camera.camera_id not in self._stream_workers:
                card = self._camera_panel._cards.get(camera.camera_id)
                if card:
                    card.set_connected(True)
                self._start_stream(camera.camera_id)

    def _stop_all_streams(self) -> None:
        """Detiene captura de todas las camaras activas."""
        for camera_id in list(self._stream_workers.keys()):
            self._stop_stream(camera_id)
        # Esperar a que terminen para no perder frames en disco
        for worker in list(self._stream_workers.values()):
            worker.wait(3000)

    def _on_stream_error(self, camera_id: str, message: str) -> None:
        """Callback de error en un stream RTSP."""
        logger.error(f"Stream {camera_id} error: {message}")
        self._camera_panel.show_error(
            f"Error en camara {camera_id}", message
        )
        card = self._camera_panel._cards.get(camera_id)
        if card:
            card.set_connected(False)

    def _on_stream_finished(self, camera_id: str) -> None:
        """Callback cuando termina el QThread del stream."""
        self._stream_workers.pop(camera_id, None)
        card = self._camera_panel._cards.get(camera_id)
        if card:
            card.set_connected(False)
        self._stats_panel.refresh()
        logger.info(f"Stream finalizado: {camera_id}")

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
