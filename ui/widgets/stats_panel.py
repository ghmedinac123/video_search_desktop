"""
Panel de estadisticas de la coleccion.

Responsabilidad UNICA: mostrar registros totales, videos indexados,
distribucion de clases, uso de disco, y boton para limpiar.

Hereda de BaseWidget.

Uso:
    from ui.widgets.stats_panel import StatsPanel
    panel = StatsPanel()
    panel.refresh()
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QProgressBar
from PySide6.QtCore import Qt

from ui.base_widget import BaseWidget
from ui.theme import Theme
from core.database import Database
from models.database import CollectionStats


class StatsPanel(BaseWidget):
    """Panel de estadisticas de la coleccion ChromaDB."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db: Database | None = None
        self._setup_ui()

    def set_database(self, database: Database) -> None:
        """Inyecta la base de datos y refresca las estadisticas."""
        self._db = database
        self.refresh()

    def _setup_ui(self) -> None:
        """Construye: metricas + videos + clases + boton limpiar."""
        header = self.create_header("Estadisticas")
        self.main_layout.addWidget(header)
        desc = self.create_secondary_label(
            "Informacion de la coleccion ChromaDB embebida"
        )
        self.main_layout.addWidget(desc)
        self.main_layout.addWidget(self.create_separator())

        # Metricas principales
        metrics_card = self.create_card()
        metrics_layout = metrics_card.layout()

        self._total_label = self._create_stat("Total registros", "0")
        self._videos_label = self._create_stat("Videos indexados", "0")
        self._disk_label = self._create_stat("Uso de disco", "0 MB")

        metrics_row = self.create_horizontal_layout()
        metrics_row.addWidget(self._total_label)
        metrics_row.addWidget(self._videos_label)
        metrics_row.addWidget(self._disk_label)
        metrics_layout.addLayout(metrics_row)

        self.main_layout.addWidget(metrics_card)

        # Distribucion de clases
        classes_title = self.create_section_title("Distribucion de clases")
        self.main_layout.addWidget(classes_title)

        self._classes_card = self.create_card()
        self._classes_layout = self._classes_card.layout()
        self._no_data_label = QLabel("Sin datos — indexa un video primero")
        self._no_data_label.setProperty("class", "muted")
        self._no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._classes_layout.addWidget(self._no_data_label)
        self.main_layout.addWidget(self._classes_card)

        # Videos indexados
        videos_title = self.create_section_title("Videos indexados")
        self.main_layout.addWidget(videos_title)

        self._videos_card = self.create_card()
        self._videos_list_layout = self._videos_card.layout()
        self._no_videos_label = QLabel("Ninguno")
        self._no_videos_label.setProperty("class", "muted")
        self._videos_list_layout.addWidget(self._no_videos_label)
        self.main_layout.addWidget(self._videos_card)

        self.main_layout.addWidget(self.create_separator())

        # Botones
        btn_row = self.create_horizontal_layout()
        self._refresh_btn = self.create_button("Refrescar")
        self._refresh_btn.clicked.connect(self.refresh)
        btn_row.addWidget(self._refresh_btn)

        self._reset_btn = self.create_button("Limpiar coleccion", danger=True)
        self._reset_btn.clicked.connect(self._on_reset)
        btn_row.addWidget(self._reset_btn)
        btn_row.addStretch()
        self.main_layout.addLayout(btn_row)

        self.main_layout.addStretch()

    def _create_stat(self, label: str, value: str) -> QWidget:
        """Crea widget metrica reutilizable: label + valor."""
        c = Theme.colors()
        container = BaseWidget()
        container.main_layout.setContentsMargins(8, 8, 8, 8)
        container.main_layout.setSpacing(2)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"font-size: {Theme.FONT_SIZE_SMALL}px;"
            f"color: {c.text_muted};"
            f"letter-spacing: 0.3px;"
        )
        container.main_layout.addWidget(lbl)

        val = QLabel(value)
        val.setObjectName("value")
        val.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {c.text_primary};"
        )
        container.main_layout.addWidget(val)

        return container

    def refresh(self) -> None:
        """Refresca las estadisticas desde ChromaDB."""
        if self._db is None:
            return

        stats = self._db.get_stats()

        # Metricas
        self._total_label.findChild(QLabel, "value").setText(
            f"{stats.total_records:,}"
        )
        self._videos_label.findChild(QLabel, "value").setText(
            str(len(stats.indexed_videos))
        )
        self._disk_label.findChild(QLabel, "value").setText(
            f"{stats.disk_usage_mb:.1f} MB"
        )

        # Distribucion de clases
        self._refresh_classes(stats)

        # Videos indexados
        self._refresh_videos(stats)

    def _refresh_classes(self, stats: CollectionStats) -> None:
        """Actualiza barras de distribucion de clases."""
        # Limpiar anteriores
        while self._classes_layout.count():
            item = self._classes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not stats.class_distribution:
            label = QLabel("Sin datos")
            label.setProperty("class", "muted")
            self._classes_layout.addWidget(label)
            return

        max_count = max(stats.class_distribution.values()) if stats.class_distribution else 1

        for class_name, count in sorted(
            stats.class_distribution.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            row = QHBoxLayout()
            row.setSpacing(8)

            name = QLabel(class_name)
            name.setFixedWidth(80)
            row.addWidget(name)

            bar = QProgressBar()
            bar.setMaximum(max_count)
            bar.setValue(count)
            bar.setTextVisible(False)
            bar.setFixedHeight(12)
            row.addWidget(bar, stretch=1)

            count_label = QLabel(f"{count:,}")
            count_label.setProperty("class", "secondary")
            count_label.setFixedWidth(50)
            row.addWidget(count_label)

            self._classes_layout.addLayout(row)

    def _refresh_videos(self, stats: CollectionStats) -> None:
        """Actualiza lista de videos indexados."""
        while self._videos_list_layout.count():
            item = self._videos_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not stats.indexed_videos:
            label = QLabel("Ninguno")
            label.setProperty("class", "muted")
            self._videos_list_layout.addWidget(label)
            return

        from pathlib import Path
        for video_path in stats.indexed_videos:
            name = Path(video_path).name
            label = QLabel(f"  {name}")
            label.setProperty("class", "secondary")
            self._videos_list_layout.addWidget(label)

    def _on_reset(self) -> None:
        """Limpia la coleccion con confirmacion."""
        if self._db is None:
            return

        if self.show_confirm(
            "Limpiar coleccion",
            "Esto eliminara TODOS los datos indexados.\n"
            "Esta accion no se puede deshacer.\n\n"
            "Continuar?",
        ):
            self._db.reset()
            self.refresh()
            self.show_success("Listo", "Coleccion limpiada exitosamente")
