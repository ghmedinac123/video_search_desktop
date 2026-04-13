# CLAUDE.md — Contexto del proyecto para Claude

## Que es este proyecto

App de escritorio Windows para busqueda visual en videos de camaras de seguridad
por lenguaje natural. Escribes "mujer con camisa amarilla" y te muestra los frames
exactos con timestamps. 100% local en GPU NVIDIA, sin servidores externos.

Soporta dos modos:
- v1.0: Video grabado (.mp4) — indexar y luego buscar
- v2.0: Camaras RTSP en vivo — procesa en tiempo real, busqueda instantanea

## Repo

- **GitHub:** github.com/ghmedinac123/video_search_desktop
- **Estado:** v2.0 — 63 archivos Python
- **Lenguaje:** Python 3.12 (100%)

## Stack

- **GUI:** PySide6 (LGPL, comercial gratis) — dark/light mode
- **Detector:** YOLOv11 n/m/x (seleccionable desde UI)
- **Embeddings:** Jina CLIP v2 (multilingue, imagen y texto)
- **VLM:** Qwen2.5-VL 7B Q4 (espanol) o Moondream2 4-bit (ingles)
- **Database:** ChromaDB 1.5.7 embebido (PersistentClient, sin Docker)
- **Tipado:** Pydantic v2 (16 modelos tipados)
- **Logging:** Loguru (centralizado, silencia 30+ librerias)
- **GPU:** pynvml para monitoreo VRAM/temp en tiempo real
- **Streaming:** OpenCV VideoCapture para RTSP

## Arquitectura

```
main.py                        <- Clase Application ensambla core + UI
├── core/                      <- Backend (NO importa nada de ui/)
│   ├── logger.py              <- Loguru centralizado
│   ├── gpu_utils.py           <- GPUUtils estatico: detect, vram, temp
│   ├── model_registry.py      <- Catalogo 6 modelos + Factory Method
│   ├── model_manager.py       <- Singleton thread-safe, modelos en GPU
│   ├── database.py            <- ChromaDB embebido, Repository pattern
│   ├── frame_extractor.py     <- Video -> frames con OpenCV
│   ├── stream_capture.py      <- Camara RTSP -> frames (v2.0)
│   ├── indexer.py             <- Pipeline + process_single_frame()
│   ├── searcher.py            <- Texto -> CLIP embed -> ChromaDB query
│   ├── detectors/
│   │   ├── base_detector.py   <- ABC
│   │   └── yolo_detector.py   <- Hereda BaseDetector
│   ├── embedders/
│   │   ├── base_embedder.py   <- ABC
│   │   └── clip_embedder.py   <- Hereda BaseEmbedder
│   └── describers/
│       ├── base_describer.py  <- ABC
│       ├── qwen_describer.py  <- Hereda BaseDescriber (espanol)
│       └── moondream_describer.py <- Hereda BaseDescriber (ingles)
├── models/                    <- Pydantic v2 (datos tipados entre capas)
│   ├── settings.py            <- AppSettings lee .env + setup_model_environment()
│   ├── camera.py              <- CameraConfig + CameraStatus + CameraStore (v2.0)
│   ├── gpu.py                 <- GPUInfo, VRAMStatus
│   ├── models_ai.py           <- AIModelInfo, ModelStatus, AIModelType
│   ├── video.py               <- VideoMetadata
│   ├── frame.py               <- FrameData
│   ├── detection.py           <- BoundingBox, CropData
│   ├── search.py              <- SearchQuery, SearchResult, SearchResponse
│   ├── indexing.py            <- IndexStage, IndexProgress, IndexResult
│   └── database.py            <- CollectionStats
└── ui/                        <- PySide6 frontend
    ├── theme.py               <- Dark/light mode, QSS global, toggle
    ├── base_widget.py         <- Clase base: TODOS los paneles heredan
    ├── main_window.py         <- QMainWindow + sidebar + stacked panels
    ├── widgets/
    │   ├── sidebar.py         <- 5 botones: Modelos, Indexar, Buscar, Camaras, Stats
    │   ├── gpu_monitor.py     <- VRAM tiempo real cada 1s
    │   ├── model_panel.py     <- Seleccion modelos + VRAM estimada
    │   ├── model_card.py      <- Card reutilizable por modelo (N instancias)
    │   ├── video_selector.py  <- Drag-drop + metadata
    │   ├── indexing_panel.py  <- Progreso 4 barras + pause/cancel
    │   ├── progress_group.py  <- Barras reutilizables
    │   ├── search_panel.py    <- Input + galeria + detalle
    │   ├── result_gallery.py  <- Grid scrollable de ResultCards
    │   ├── result_card.py     <- Card reutilizable por resultado (N instancias)
    │   ├── result_detail.py   <- Frame + bbox + metadata + abrir video
    │   ├── camera_panel.py    <- CRUD camaras + monitoreo en vivo (v2.0)
    │   └── stats_panel.py     <- Estadisticas + limpiar coleccion
    └── workers/
        ├── base_worker.py     <- Clase base: TODOS los workers heredan
        ├── model_download_worker.py
        ├── model_load_worker.py
        ├── index_worker.py
        ├── search_worker.py
        └── stream_worker.py   <- Captura RTSP background (v2.0)
```

## Principios de codigo

- **SOLID estricto:** cada clase tiene UNA responsabilidad
- **Polimorfismo:** BaseDetector/BaseEmbedder/BaseDescriber con herencia
- **Singleton:** ModelManager thread-safe
- **Factory:** ModelRegistry.create_detector/embedder/describer()
- **Repository:** Database abstrae ChromaDB
- **Observer:** Signals/Slots PySide6 para workers y UI
- **Dependency Inversion:** Indexer recibe interfaces por constructor
- **Template Method:** BaseWorker.run() -> subclase.execute()
- **0 codigo duplicado:** BaseWidget y BaseWorker eliminan repeticion
- **Tipado fuerte:** Pydantic v2 en TODAS las interfaces entre capas
- **Idempotencia:** download no re-descarga, upsert no duplica

## Regla de dependencia

```
ui/ -> core/ -> models/    (permitido, fluye hacia abajo)
core/ -> ui/               (PROHIBIDO)
models/ -> core/           (PROHIBIDO)
```

## Datos en runtime (gitignored)

- `models_cache/` — Modelos AI descargados (HF_HOME apunta aqui)
- `data/chromadb/` — Base de datos embeddings
- `data/cameras.json` — Configuracion camaras (creado desde UI)
- `output/frames/` — Frames extraidos (por video y por camara)
- `output/crops/` — Detecciones recortadas
- `logs/` — Logs rotativos (10MB, 7 dias)

## Decisiones tecnicas clave

- Modelos AI en models_cache/ dentro del proyecto (portable, borras carpeta = borras todo)
- setup_model_environment() configura HF_HOME + YOLO_CONFIG_DIR al iniciar
- ChromaDB embebido PersistentClient — sin Docker, sin WSL, Windows nativo
- GPU dinamica — detecta cualquier NVIDIA, no hardcoded
- Camaras configurables desde UI, persistidas en JSON (no en .env)
- MAX_CAMERAS=4 en .env como limite tecnico de la GPU
- StreamCapture: 1 instancia por camara, 1 hilo por camara
- process_single_frame() en Indexer reutiliza pipeline completo
- Defaults livianos: yolo11n + moondream2-4bit (6.3 GB VRAM total)

## Pendiente (hacer en PC con RTX 5060 Ti)

- Debug primer run: uv sync + python main.py
- Aplicar 5 modificaciones para conectar camaras al pipeline:
  1. core/indexer.py -> agregar process_single_frame()
  2. models/__init__.py -> agregar imports camera
  3. ui/widgets/sidebar.py -> agregar 5to boton "Camaras"
  4. ui/main_window.py -> agregar 5to panel
  5. main.py -> conectar CameraPanel con StreamWorker
- Test: descargar modelos, indexar video, buscar por texto
- Test: agregar camara RTSP, conectar, ver detecciones en vivo
- PyInstaller + Inno Setup para instalador .exe
- Splash screen + iconos
