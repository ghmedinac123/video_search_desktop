"""
Barra de filtros para el panel de busqueda.

Responsabilidad UNICA: ofrecer al usuario filtros (camara, clase,
rango de fechas) y exponer un metodo build_query() que produce un
SearchQuery tipado para alimentar al Searcher.

Hereda BaseWidget. Componente reutilizable.

Uso:
    bar = SearchFilterBar(database)
    query = bar.build_query(text="persona camisa roja")
"""

from __future__ import annotations

from datetime import datetime, time as dtime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QDate

from ui.base_widget import BaseWidget
from ui.theme import Theme
from models.search import SearchQuery
from core.database import Database


# Clases YOLO relevantes para filtrar (espejo de SECURITY_CLASSES)
_FILTERABLE_CLASSES: list[tuple[str, str]] = [
    ("person", "Persona"),
    ("car", "Auto"),
    ("motorcycle", "Moto"),
    ("bus", "Bus"),
    ("truck", "Camion"),
    ("bicycle", "Bicicleta"),
    ("dog", "Perro"),
    ("cat", "Gato"),
    ("backpack", "Mochila"),
    ("handbag", "Bolso"),
    ("suitcase", "Maleta"),
]


class SearchFilterBar(BaseWidget):
    """
    Fila horizontal con filtros de busqueda.

    Layout: [Camara dropdown] [Clases checkboxes] [Fecha desde] [Fecha hasta]
    [Aplicar/Limpiar]
    """

    filters_changed = Signal()

    def __init__(
        self,
        database: Database,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._database = database
        self._class_checks: dict[str, QCheckBox] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Construye la barra horizontal de filtros."""
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        title = self.create_section_title("Filtros")
        self.main_layout.addWidget(title)

        # Fila 1: camara + fechas
        row1 = self.create_horizontal_layout()

        cam_label = QLabel("Cámara:")
        cam_label.setProperty("class", "secondary")
        row1.addWidget(cam_label)

        self._camera_combo = QComboBox()
        self._camera_combo.addItem("Todas", None)
        self._refresh_camera_options()
        self._camera_combo.currentIndexChanged.connect(
            lambda _: self.filters_changed.emit()
        )
        row1.addWidget(self._camera_combo)

        row1.addSpacing(20)

        from_label = QLabel("Desde:")
        from_label.setProperty("class", "secondary")
        row1.addWidget(from_label)

        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addDays(-7))
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        row1.addWidget(self._date_from)

        to_label = QLabel("Hasta:")
        to_label.setProperty("class", "secondary")
        row1.addWidget(to_label)

        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        row1.addWidget(self._date_to)

        self._date_enabled = QCheckBox("Filtrar por fecha")
        self._date_enabled.setChecked(False)
        row1.addWidget(self._date_enabled)

        row1.addStretch()

        clear_btn = QPushButton("Limpiar filtros")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.reset)
        row1.addWidget(clear_btn)

        self.main_layout.addLayout(row1)

        # Fila 2: clases (checkboxes en rejilla)
        row2_label = QLabel("Clases:")
        row2_label.setProperty("class", "secondary")
        self.main_layout.addWidget(row2_label)

        row2 = self.create_horizontal_layout()
        for class_id, label in _FILTERABLE_CLASSES:
            cb = QCheckBox(label)
            cb.stateChanged.connect(lambda _: self.filters_changed.emit())
            self._class_checks[class_id] = cb
            row2.addWidget(cb)
        row2.addStretch()
        self.main_layout.addLayout(row2)

    def _refresh_camera_options(self) -> None:
        """Carga los camera_id distintos que existen en la DB."""
        try:
            stats = self._database.get_stats()
        except Exception:
            return

        # Obtener camera_ids unicos del peek
        camera_ids: set[str] = set()
        try:
            sample = self._database._collection.peek(
                limit=min(stats.total_records, 5000)
            )
            for meta in (sample.get("metadatas") or []):
                cid = meta.get("camera_id")
                if cid:
                    camera_ids.add(cid)
        except Exception:
            pass

        for cid in sorted(camera_ids):
            self._camera_combo.addItem(cid, cid)

    def refresh(self) -> None:
        """Actualiza la lista de camaras disponibles."""
        current = self._camera_combo.currentData()
        self._camera_combo.clear()
        self._camera_combo.addItem("Todas", None)
        self._refresh_camera_options()
        # Restaurar seleccion si sigue existiendo
        if current is not None:
            idx = self._camera_combo.findData(current)
            if idx >= 0:
                self._camera_combo.setCurrentIndex(idx)

    def reset(self) -> None:
        """Limpia todos los filtros."""
        self._camera_combo.setCurrentIndex(0)
        for cb in self._class_checks.values():
            cb.setChecked(False)
        self._date_from.setDate(QDate.currentDate().addDays(-7))
        self._date_to.setDate(QDate.currentDate())
        self._date_enabled.setChecked(False)
        self.filters_changed.emit()

    def build_query(self, text: str, n_results: int = 30) -> SearchQuery:
        """
        Construye un SearchQuery tipado con los filtros activos.

        Args:
            text: Texto del usuario.
            n_results: Maximo de resultados.

        Returns:
            SearchQuery listo para alimentar al Searcher.
        """
        # Camara seleccionada
        cam_data = self._camera_combo.currentData()
        camera_filter: list[str] | None = (
            [cam_data] if cam_data else None
        )

        # Clases marcadas
        selected_classes = [
            cid for cid, cb in self._class_checks.items() if cb.isChecked()
        ]
        class_filter: list[str] | None = (
            selected_classes if selected_classes else None
        )

        # Fechas si estan habilitadas
        date_from: datetime | None = None
        date_to: datetime | None = None
        if self._date_enabled.isChecked():
            qd_from = self._date_from.date()
            qd_to = self._date_to.date()
            date_from = datetime.combine(
                datetime(qd_from.year(), qd_from.month(), qd_from.day()),
                dtime.min,
            )
            date_to = datetime.combine(
                datetime(qd_to.year(), qd_to.month(), qd_to.day()),
                dtime.max,
            )

        return SearchQuery(
            text=text,
            n_results=n_results,
            class_filter=class_filter,
            camera_filter=camera_filter,
            date_from=date_from,
            date_to=date_to,
        )
