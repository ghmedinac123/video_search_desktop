# FASE 3: UI PySide6 — Dividida en 8 Subfases

## Estado actual del proyecto

### COMPLETADO ✅

| Fase | Archivos | Estado |
|------|----------|--------|
| Fase 0: Infraestructura | pyproject.toml, .env, .gitignore, main.py | ✅ |
| Fase 0: Modelos Pydantic | models/ (10 archivos, 15 clases tipadas) | ✅ |
| Fase 0: Logger | core/logger.py (loguru + silenciamiento) | ✅ |
| Fase 0: ABCs | 3 clases base abstractas (detector, embedder, describer) | ✅ |
| Fase 1: GPU + Modelos | gpu_utils, model_registry, model_manager, database | ✅ |
| Fase 1: Implementaciones | yolo_detector, clip_embedder, qwen_describer, moondream_describer | ✅ |
| Fase 2: Pipeline | frame_extractor, indexer, searcher | ✅ |

**TOTAL CORE: 15 archivos Python, 0 código duplicado, 100% tipado.**

---

### PENDIENTE — Fase 3 UI (este documento)

```
ui/
├── __init__.py                    ← Ya existe (vacío)
├── theme.py                       ← Subfase 3A
├── base_widget.py                 ← Subfase 3A (clase base reutilizable)
├── main_window.py                 ← Subfase 3B
├── widgets/
│   ├── __init__.py                ← Ya existe (vacío)
│   ├── sidebar.py                 ← Subfase 3B
│   ├── gpu_monitor.py             ← Subfase 3C
│   ├── model_panel.py             ← Subfase 3D
│   ├── model_card.py              ← Subfase 3D
│   ├── video_selector.py          ← Subfase 3E
│   ├── indexing_panel.py          ← Subfase 3E
│   ├── progress_group.py          ← Subfase 3E
│   ├── search_panel.py            ← Subfase 3F
│   ├── result_gallery.py          ← Subfase 3F
│   ├── result_card.py             ← Subfase 3F
│   ├── result_detail.py           ← Subfase 3F
│   └── stats_panel.py             ← Subfase 3G
└── workers/
    ├── __init__.py                ← Ya existe (vacío)
    ├── base_worker.py             ← Subfase 3H (clase base reutilizable)
    ├── model_download_worker.py   ← Subfase 3H
    ├── model_load_worker.py       ← Subfase 3H
    ├── index_worker.py            ← Subfase 3H
    └── search_worker.py           ← Subfase 3H
```

**TOTAL UI: 21 archivos nuevos.**

---

## Clases base reutilizables (SRP + herencia)

### BaseWidget — Clase base para TODOS los paneles

Todos los paneles (ModelPanel, IndexingPanel, SearchPanel, StatsPanel)
heredan de BaseWidget. Evita código duplicado: layout, padding,
título, métodos comunes.

```python
# ui/base_widget.py
class BaseWidget(QWidget):
    """
    Clase base para todos los paneles de la app.
    Herencia: ModelPanel(BaseWidget), SearchPanel(BaseWidget), etc.

    Provee:
    - Layout vertical con padding estándar
    - Método create_section_title() para títulos consistentes
    - Método create_card() para cards con estilo NVR
    - Método create_badge() para badges de colores
    - Método create_button() para botones estilizados
    - Método show_error() para mensajes de error
    - Método show_success() para mensajes de éxito
    """
```

### BaseWorker — Clase base para TODOS los QThreads

Todos los workers heredan de BaseWorker. Evita duplicar
señales de error y lógica de try/catch.

```python
# ui/workers/base_worker.py
class BaseWorker(QThread):
    """
    Clase base para todos los workers (QThread).
    Herencia: IndexWorker(BaseWorker), SearchWorker(BaseWorker), etc.

    Provee:
    - Signal error(str) compartido
    - Método run() con try/catch que emite error automáticamente
    - Método abstracto execute() que implementa cada subclase
    - Propiedad is_cancelled para control de flujo
    """
```

---

## Subfases detalladas

### Subfase 3A: Theme + BaseWidget (2 archivos)

```
Archivos:
├── ui/theme.py          ← Paleta NVR oscura + QSS global
└── ui/base_widget.py    ← Clase base para todos los paneles

theme.py contiene:
  class Theme:
      - Constantes de colores (BG_PRIMARY, ACCENT, SUCCESS, etc.)
      - get_stylesheet() → str completo QSS para toda la app
      - Estilos para: QPushButton, QLineEdit, QProgressBar,
        QScrollArea, QSlider, QRadioButton, QLabel, QStatusBar

base_widget.py contiene:
  class BaseWidget(QWidget):
      - create_section_title(text) → QLabel estilizado
      - create_card() → QFrame con bordes y fondo NVR
      - create_badge(text, color) → QLabel pill
      - create_button(text, primary=False) → QPushButton
      - create_separator() → QFrame línea horizontal
      - show_error(msg) → QMessageBox
      - show_success(msg) → QMessageBox
```

**Criterio:** Importar Theme y BaseWidget sin errores.

---

### Subfase 3B: Ventana principal + Sidebar (2 archivos)

```
Archivos:
├── ui/main_window.py    ← QMainWindow con layout
└── ui/widgets/sidebar.py ← Navegación lateral con íconos

main_window.py contiene:
  class MainWindow(QMainWindow):
      - Sidebar izquierda (sidebar.py)
      - QStackedWidget central (cambia entre paneles)
      - QStatusBar abajo (GPU + VRAM + ChromaDB)
      - Conecta sidebar clicks → cambia panel visible

sidebar.py contiene:
  class Sidebar(QWidget):
      - Botones verticales: Modelos, Indexar, Buscar, Stats
      - Signal page_changed(int) cuando se hace click
      - Resalta el botón activo
      - Logo/título arriba
```

**Criterio:** App se abre con ventana oscura, sidebar navega entre 4 placeholders.

---

### Subfase 3C: Monitor GPU (1 archivo)

```
Archivo:
└── ui/widgets/gpu_monitor.py

gpu_monitor.py contiene:
  class GPUMonitorWidget(BaseWidget):
      - QTimer cada 1 segundo → llama GPUUtils.get_vram_status()
      - Barra VRAM segmentada (YOLO color, CLIP color, VLM color)
      - Labels: usado/total GB, temperatura, % utilización
      - Se muestra en StatusBar y en panel de Modelos
```

**Criterio:** Widget muestra VRAM en tiempo real actualizándose.

---

### Subfase 3D: Panel de Modelos (2 archivos)

```
Archivos:
├── ui/widgets/model_panel.py   ← Panel completo
└── ui/widgets/model_card.py    ← Card reutilizable por modelo

model_card.py contiene:
  class ModelCard(BaseWidget):
      - Radio button + nombre modelo + badge estado
      - Barra progreso descarga
      - Label VRAM estimada
      - Signal selected(model_id) al hacer click
      - Reutilizable: se instancia N veces (1 por modelo)

model_panel.py contiene:
  class ModelPanel(BaseWidget):
      - 3 secciones: Detectores, Embedders, Describers
      - Cada sección tiene N ModelCards (del catálogo)
      - Slider confianza YOLO
      - Barra VRAM estimada (suma de seleccionados vs GPU)
      - Botones: [Descargar seleccionados] [Cargar en GPU]
      - Conecta con ModelManager via workers
```

**Criterio:** Selecciono modelos, veo VRAM estimada, botones funcionales.

---

### Subfase 3E: Panel de Indexación (3 archivos)

```
Archivos:
├── ui/widgets/video_selector.py  ← Drag&drop + browse
├── ui/widgets/progress_group.py  ← Grupo de barras reutilizable
└── ui/widgets/indexing_panel.py  ← Panel completo

video_selector.py contiene:
  class VideoSelector(BaseWidget):
      - Zona drag&drop (acepta MP4, AVI, MKV, MOV)
      - Botón "Explorar archivos"
      - Preview del primer frame
      - Labels metadata: duración, FPS, resolución
      - Signal video_selected(Path) al cargar video

progress_group.py contiene:
  class ProgressGroup(BaseWidget):
      - N barras QProgressBar con labels
      - Método update_bar(name, value, max)
      - Reutilizable: se usa en indexación y en descarga de modelos

indexing_panel.py contiene:
  class IndexingPanel(BaseWidget):
      - VideoSelector arriba
      - Slider intervalo de muestreo (1-10s)
      - ProgressGroup con 4 barras (frames, YOLO, CLIP, VLM)
      - Counters: frames, detecciones, velocidad, tiempo restante
      - Botones: [Iniciar] [Pausar] [Cancelar]
      - Conecta con Indexer via IndexWorker
```

**Criterio:** Cargo video, veo metadata, indexo con progreso visual.

---

### Subfase 3F: Panel de Búsqueda (4 archivos) ← LA ESTRELLA

```
Archivos:
├── ui/widgets/search_panel.py    ← Panel completo
├── ui/widgets/result_gallery.py  ← Grid scrollable de cards
├── ui/widgets/result_card.py     ← Card individual reutilizable
└── ui/widgets/result_detail.py   ← Vista detalle al hacer click

result_card.py contiene:
  class ResultCard(BaseWidget):
      - Thumbnail del crop (QLabel con pixmap)
      - Badges: score (verde), clase (rojo), timestamp (amarillo)
      - Signal clicked(crop_id) al hacer click
      - Reutilizable: se instancia N veces (1 por resultado)

result_gallery.py contiene:
  class ResultGallery(QScrollArea):
      - Grid responsivo de ResultCards
      - Lazy loading (no cargar 1000 imágenes de golpe)
      - Signal result_selected(SearchResult) al click en card

result_detail.py contiene:
  class ResultDetail(BaseWidget):
      - Frame completo con bounding box dibujado (overlay)
      - Crop ampliado
      - Labels: score, clase, timestamp, video, descripción VLM
      - Botón [Abrir video en este momento ▶]
      - Botón [Copiar frame] [Exportar crop]
      - Navegación ← → entre resultados

search_panel.py contiene:
  class SearchPanel(BaseWidget):
      - Barra de búsqueda (QLineEdit con ícono)
      - Label "N resultados en Xms"
      - QSplitter vertical: arriba ResultGallery, abajo ResultDetail
      - Conecta con Searcher via SearchWorker
```

**Criterio:** Busco "mujer camisa amarilla", galería de crops, click = detalle.

---

### Subfase 3G: Panel de Estadísticas (1 archivo)

```
Archivo:
└── ui/widgets/stats_panel.py

stats_panel.py contiene:
  class StatsPanel(BaseWidget):
      - Total registros en ChromaDB
      - Lista de videos indexados (tabla)
      - Distribución de clases (barras horizontales con QPainter)
      - Uso de disco
      - Botón [Limpiar colección] con confirmación
```

**Criterio:** Tab stats muestra datos de la colección.

---

### Subfase 3H: Workers QThread (5 archivos)

```
Archivos:
├── ui/workers/base_worker.py             ← Clase base
├── ui/workers/model_download_worker.py   ← Descargar modelos
├── ui/workers/model_load_worker.py       ← Cargar en GPU
├── ui/workers/index_worker.py            ← Pipeline indexación
└── ui/workers/search_worker.py           ← Búsqueda

base_worker.py contiene:
  class BaseWorker(QThread):
      error = Signal(str)        # Compartido por todos
      def run(self):             # Try/catch automático
          try:
              self.execute()
          except Exception as e:
              self.error.emit(str(e))

      @abstractmethod
      def execute(self) -> None:  # Cada subclase implementa esto
          ...

model_download_worker.py:
  class ModelDownloadWorker(BaseWorker):
      progress = Signal(str, float)   # (model_id, 0.0-1.0)
      finished = Signal()

model_load_worker.py:
  class ModelLoadWorker(BaseWorker):
      model_loaded = Signal(str)      # model_id
      all_loaded = Signal()

index_worker.py:
  class IndexWorker(BaseWorker):
      progress = Signal(object)       # IndexProgress
      finished = Signal(object)       # IndexResult

search_worker.py:
  class SearchWorker(BaseWorker):
      results = Signal(object)        # SearchResponse
```

**Criterio:** Ninguna operación pesada bloquea la UI.

---

## Resumen: Orden de implementación

| Subfase | Archivos | Depende de |
|---------|----------|------------|
| 3A: Theme + BaseWidget | 2 | Nada (standalone) |
| 3B: Ventana + Sidebar | 2 | 3A |
| 3C: GPU Monitor | 1 | 3A, core/gpu_utils |
| 3D: Panel Modelos | 2 | 3A, 3C, core/model_manager |
| 3E: Panel Indexación | 3 | 3A, core/indexer |
| 3F: Panel Búsqueda | 4 | 3A, core/searcher |
| 3G: Panel Stats | 1 | 3A, core/database |
| 3H: Workers | 5 | 3A (BaseWorker), core/* |
| **TOTAL** | **20** | |

Después de Fase 3:
- Fase 4: Actualizar main.py para arrancar PySide6
- Fase 5: scripts/build.py + scripts/installer.iss
- Fase 6: README.md + subir a GitHub