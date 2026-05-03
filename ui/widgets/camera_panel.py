"""
Panel de configuracion y monitoreo de camaras RTSP.

Responsabilidad UNICA: permitir al usuario agregar/editar/eliminar
camaras, ver estado en tiempo real, e iniciar/detener captura.

Hereda de BaseWidget. Las camaras se guardan en data/cameras.json.
NO hardcoded en .env — todo configurable desde la UI.

Uso:
    from ui.widgets.camera_panel import CameraPanel
    panel = CameraPanel()
"""

from __future__ import annotations

import cv2
import numpy as np

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QSpinBox,
    QHBoxLayout,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap

from ui.base_widget import BaseWidget
from ui.theme import Theme
from models.camera import CameraConfig, CameraStatus, CameraStore
from core.logger import logger


class _CameraCard(BaseWidget):
    """
    Card reutilizable para UNA camara. Se instancia N veces.

    Muestra: nombre, URL, estado conexion, detecciones, FPS.
    Botones: editar, eliminar, conectar/desconectar.
    """

    edit_clicked = Signal(str)
    remove_clicked = Signal(str)
    toggle_clicked = Signal(str)

    def __init__(
        self,
        camera: CameraConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._camera = camera
        self._status = CameraStatus(camera_id=camera.camera_id)
        self._connected = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construye la card."""
        c = Theme.colors()

        card = self.create_card()
        card_layout = card.layout()

        # Fila 1: nombre + estado
        row1 = self.create_horizontal_layout()
        name_label = QLabel(f"{self._camera.name}")
        name_label.setStyleSheet(f"font-weight: 600; font-size: {Theme.FONT_SIZE}px;")
        row1.addWidget(name_label)

        self._id_badge = self.create_badge(self._camera.camera_id, "info")
        row1.addWidget(self._id_badge)

        self._status_badge = self.create_badge("Desconectada", "error")
        row1.addWidget(self._status_badge)
        row1.addStretch()
        card_layout.addLayout(row1)

        # Fila 2: URL
        url_label = QLabel(self._camera.rtsp_url)
        url_label.setProperty("class", "muted")
        url_label.setStyleSheet(f"font-size: {Theme.FONT_SIZE_SMALL}px;")
        card_layout.addWidget(url_label)

        # Visor de video en vivo (estilo NVR)
        self._preview_label = QLabel("Sin señal — conecta para ver el video")
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumHeight(270)
        self._preview_label.setMaximumHeight(360)
        self._preview_label.setStyleSheet(
            "background-color: #000;"
            "color: #666;"
            "border-radius: 6px;"
            f"font-size: {Theme.FONT_SIZE_SMALL}px;"
        )
        card_layout.addWidget(self._preview_label)

        # Fila 3: stats en vivo
        row3 = self.create_horizontal_layout()
        self._frames_label = self.create_secondary_label("Frames: 0")
        self._detections_label = self.create_secondary_label("Detecciones: 0")
        self._fps_label = self.create_secondary_label("FPS: --")
        self._time_label = self.create_secondary_label("")
        row3.addWidget(self._frames_label)
        row3.addWidget(self._detections_label)
        row3.addWidget(self._fps_label)
        row3.addWidget(self._time_label)
        row3.addStretch()
        card_layout.addLayout(row3)

        # Fila 4: botones
        row4 = self.create_horizontal_layout()
        self._toggle_btn = self.create_button("Conectar", primary=True)
        self._toggle_btn.clicked.connect(
            lambda: self.toggle_clicked.emit(self._camera.camera_id)
        )
        edit_btn = self.create_button("Editar")
        edit_btn.clicked.connect(
            lambda: self.edit_clicked.emit(self._camera.camera_id)
        )
        remove_btn = self.create_button("Eliminar", danger=True)
        remove_btn.clicked.connect(
            lambda: self.remove_clicked.emit(self._camera.camera_id)
        )
        row4.addWidget(self._toggle_btn)
        row4.addWidget(edit_btn)
        row4.addWidget(remove_btn)
        row4.addStretch()
        card_layout.addLayout(row4)

        self.main_layout.addWidget(card)

    def update_status(self, status: CameraStatus) -> None:
        """Actualiza la card con estado en tiempo real."""
        self._status = status
        self._frames_label.setText(f"Frames: {status.frames_captured:,}")
        self._detections_label.setText(f"Detecciones: {status.detections_total:,}")
        self._fps_label.setText(f"FPS: {status.fps_processing:.1f}")
        self._time_label.setText(status.last_frame_time)

        if status.connected:
            self._status_badge.setText("Conectada")
            self._status_badge.setStyleSheet(
                self.create_badge("", "success").styleSheet()
            )
            self._toggle_btn.setText("Desconectar")
        else:
            self._status_badge.setText("Desconectada")
            self._toggle_btn.setText("Conectar")

    def set_connected(self, connected: bool) -> None:
        """Cambia estado visual de conexion."""
        self._connected = connected
        if connected:
            self._toggle_btn.setText("Desconectar")
        else:
            self._toggle_btn.setText("Conectar")
            self._preview_label.clear()
            self._preview_label.setText("Sin señal — conecta para ver el video")

    def update_preview(self, frame_bgr: np.ndarray) -> None:
        """Actualiza el visor con el frame en vivo (BGR de OpenCV)."""
        if frame_bgr is None or frame_bgr.size == 0:
            return

        # Escalar al ancho del label manteniendo aspecto
        target_w = max(self._preview_label.width(), 480)
        h, w = frame_bgr.shape[:2]
        if w != target_w:
            scale = target_w / w
            new_h = int(h * scale)
            frame_bgr = cv2.resize(
                frame_bgr, (target_w, new_h), interpolation=cv2.INTER_AREA
            )
            h, w = new_h, target_w

        # Limitar altura al maximo del label
        max_h = self._preview_label.maximumHeight()
        if h > max_h:
            scale = max_h / h
            new_w = int(w * scale)
            frame_bgr = cv2.resize(
                frame_bgr, (new_w, max_h), interpolation=cv2.INTER_AREA
            )
            h, w = max_h, new_w

        # BGR -> RGB para Qt
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        bytes_per_line = 3 * w
        qimg = QImage(
            frame_rgb.data, w, h, bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()
        self._preview_label.setPixmap(QPixmap.fromImage(qimg))


class _AddCameraDialog(QDialog):
    """Dialogo modal para agregar/editar una camara."""

    def __init__(
        self,
        parent: QWidget | None = None,
        camera: CameraConfig | None = None,
    ) -> None:
        super().__init__(parent)
        self._camera = camera
        self.setWindowTitle("Agregar camara" if camera is None else "Editar camara")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construye el formulario."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ID
        layout.addWidget(QLabel("ID de la camara (ej: cam01):"))
        self._id_input = QLineEdit()
        self._id_input.setPlaceholderText("cam01")
        if self._camera:
            self._id_input.setText(self._camera.camera_id)
            self._id_input.setEnabled(False)
        layout.addWidget(self._id_input)

        # Nombre
        layout.addWidget(QLabel("Nombre descriptivo:"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Entrada principal")
        if self._camera:
            self._name_input.setText(self._camera.name)
        layout.addWidget(self._name_input)

        # URL RTSP
        layout.addWidget(QLabel("URL RTSP:"))
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText(
            "rtsp://admin:password@192.168.1.100:554/stream1"
        )
        if self._camera:
            self._url_input.setText(self._camera.rtsp_url)
        layout.addWidget(self._url_input)

        # Intervalo
        layout.addWidget(QLabel("Intervalo de captura (segundos):"))
        self._interval_spin = QSpinBox()
        self._interval_spin.setMinimum(1)
        self._interval_spin.setMaximum(30)
        self._interval_spin.setValue(
            self._camera.interval_seconds if self._camera else 2
        )
        layout.addWidget(self._interval_spin)

        # Botones OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_camera_config(self) -> CameraConfig | None:
        """Retorna la config creada, o None si algun campo esta vacio."""
        cam_id = self._id_input.text().strip()
        name = self._name_input.text().strip()
        url = self._url_input.text().strip()

        if not all([cam_id, name, url]):
            return None

        return CameraConfig(
            camera_id=cam_id,
            name=name,
            rtsp_url=url,
            interval_seconds=self._interval_spin.value(),
        )


class CameraPanel(BaseWidget):
    """
    Panel principal de camaras RTSP.

    Hereda BaseWidget. Usa CameraStore para persistir en JSON.
    Usa _CameraCard (reutilizable) para cada camara.
    """

    MAX_CAMERAS: int = 4

    start_capture = Signal(str)
    stop_capture = Signal(str)
    start_all = Signal()
    stop_all = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = CameraStore()
        self._cards: dict[str, _CameraCard] = {}
        self._setup_ui()
        self._load_cameras()

    def _setup_ui(self) -> None:
        """Construye el panel."""
        header = self.create_header("Camaras en vivo")
        self.main_layout.addWidget(header)

        desc = self.create_secondary_label(
            f"Conecta hasta {self.MAX_CAMERAS} camaras RTSP para procesar en tiempo real"
        )
        self.main_layout.addWidget(desc)
        self.main_layout.addWidget(self.create_separator())

        # Scroll area para las cards
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._scroll_container = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_container)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll_layout.setSpacing(8)
        self._scroll.setWidget(self._scroll_container)

        self.main_layout.addWidget(self._scroll, stretch=1)

        # Boton agregar
        self._add_btn = self.create_button("+ Agregar camara")
        self._add_btn.clicked.connect(self._on_add_camera)
        self.main_layout.addWidget(self._add_btn)

        # Botones globales
        btn_row = self.create_horizontal_layout()
        self._start_all_btn = self.create_button("Iniciar todas", primary=True)
        self._start_all_btn.clicked.connect(self.start_all.emit)
        self._stop_all_btn = self.create_button("Detener todas", danger=True)
        self._stop_all_btn.clicked.connect(self.stop_all.emit)
        btn_row.addWidget(self._start_all_btn)
        btn_row.addWidget(self._stop_all_btn)
        btn_row.addStretch()
        self.main_layout.addLayout(btn_row)

    def _load_cameras(self) -> None:
        """Carga camaras guardadas desde JSON y crea cards."""
        cameras = self._store.load()
        for cam in cameras:
            self._add_card(cam)
        self._update_add_button()

    def _add_card(self, camera: CameraConfig) -> None:
        """Agrega una CameraCard al panel."""
        card = _CameraCard(camera)
        card.toggle_clicked.connect(self._on_toggle_camera)
        card.edit_clicked.connect(self._on_edit_camera)
        card.remove_clicked.connect(self._on_remove_camera)
        self._cards[camera.camera_id] = card
        self._scroll_layout.addWidget(card)

    def _update_add_button(self) -> None:
        """Habilita/deshabilita boton agregar segun limite."""
        at_limit = len(self._cards) >= self.MAX_CAMERAS
        self._add_btn.setEnabled(not at_limit)
        if at_limit:
            self._add_btn.setText(f"Limite alcanzado ({self.MAX_CAMERAS} camaras)")
        else:
            self._add_btn.setText("+ Agregar camara")

    def _on_add_camera(self) -> None:
        """Abre dialogo para agregar camara."""
        dialog = _AddCameraDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_camera_config()
            if config:
                if config.camera_id in self._cards:
                    self.show_error("Error", f"Ya existe camara con ID: {config.camera_id}")
                    return
                self._store.add(config)
                self._add_card(config)
                self._update_add_button()
                logger.info(f"Camara agregada: {config.camera_id} — {config.name}")

    def _on_edit_camera(self, camera_id: str) -> None:
        """Abre dialogo para editar camara."""
        cameras = self._store.load()
        camera = next((c for c in cameras if c.camera_id == camera_id), None)
        if camera is None:
            return

        dialog = _AddCameraDialog(self, camera=camera)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_camera_config()
            if config:
                self._store.update(config)
                # Recargar UI
                self._clear_cards()
                self._load_cameras()

    def _on_remove_camera(self, camera_id: str) -> None:
        """Elimina camara con confirmacion."""
        if self.show_confirm("Eliminar camara", f"Eliminar {camera_id}?"):
            self.stop_capture.emit(camera_id)
            self._store.remove(camera_id)
            card = self._cards.pop(camera_id, None)
            if card:
                self._scroll_layout.removeWidget(card)
                card.deleteLater()
            self._update_add_button()
            logger.info(f"Camara eliminada: {camera_id}")

    def _on_toggle_camera(self, camera_id: str) -> None:
        """Conectar o desconectar una camara."""
        card = self._cards.get(camera_id)
        if card and card._connected:
            self.stop_capture.emit(camera_id)
            card.set_connected(False)
        else:
            self.start_capture.emit(camera_id)
            if card:
                card.set_connected(True)

    def _clear_cards(self) -> None:
        """Elimina todas las cards."""
        for card in self._cards.values():
            self._scroll_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    # ── API publica ──

    def update_camera_status(self, status: CameraStatus) -> None:
        """Actualiza el estado visual de una camara desde el worker."""
        card = self._cards.get(status.camera_id)
        if card:
            card.update_status(status)

    def update_camera_preview(self, camera_id: str, frame: np.ndarray) -> None:
        """Actualiza el visor de video en vivo de una camara."""
        card = self._cards.get(camera_id)
        if card:
            card.update_preview(frame)

    def get_cameras(self) -> list[CameraConfig]:
        """Retorna lista de camaras configuradas."""
        return self._store.load()

    def get_camera(self, camera_id: str) -> CameraConfig | None:
        """Retorna config de una camara por ID."""
        cameras = self._store.load()
        return next((c for c in cameras if c.camera_id == camera_id), None)
