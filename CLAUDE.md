# CLAUDE.md — Contexto del proyecto para Claude

## Qué es este proyecto

App de escritorio Windows para búsqueda visual en videos de cámaras de seguridad
por lenguaje natural. Escribes "mujer con camisa amarilla" y te muestra los frames
exactos con timestamps. 100% local en GPU NVIDIA, sin servidores externos.

## Repo

- **GitHub:** github.com/ghmedinac123/video_search_desktop
- **Estado:** v1.0 completo — 59 archivos, 8,344 líneas
- **Lenguaje:** Python 3.12 (100%)

## Stack

- **GUI:** PySide6 (LGPL, comercial gratis)
- **Detector:** YOLOv11 (n/m/x seleccionable desde UI)
- **Embeddings:** Jina CLIP v2 (multilingüe, imagen↔texto)
- **VLM:** Qwen2.5-VL 7B Q4 (español) o Moondream2 4-bit (inglés) — seleccionable
- **Database:** ChromaDB 1.5.7 embebido (PersistentClient, sin Docker)
- **Tipado:** Pydantic v2 (15 modelos tipados)
- **Logging:** Loguru (centralizado, silencia librerías externas)
- **GPU:** pynvml para monitoreo VRAM/temp en tiempo real

## Arquitectura

```
main.py                    ← Clase Application ensambla core + UI
├── core/                  ← Backend (NO importa nada de ui/)
│   ├── logger.py          ← Loguru centralizado
│   ├── gpu_utils.py       ← GPUUtils estático: detect, vram, temp
│   ├── model_registry.py  ← Catálogo 6 modelos + Factory Method
│   ├── model_manager.py   ← Singleton thread-safe, modelos en GPU
│   ├── database.py        ← ChromaDB embebido, Repository pattern
│   ├── frame_extractor.py ← Video → frames con OpenCV
│   ├── indexer.py         ← Pipeline: frames→detect→embed→describe→store
│   ├── searcher.py        ← Texto → CLIP embed → ChromaDB query
│   ├── detectors/
│   │   ├── base_detector.py    ← ABC
│   │   └── yolo_detector.py    ← Hereda BaseDetector
│   ├── embedders/
│   │   ├── base_embedder.py    ← ABC
│   │   └── clip_embedder.py    ← Hereda BaseEmbedder
│   └── describers/
│       ├── base_describer.py   ← ABC
│       ├── qwen_describer.py   ← Hereda BaseDescriber (español)
│       └── moondream_describer.py ← Hereda BaseDescriber (inglés)
├── models/                ← Pydantic v2 (datos tipados entre capas)
│   ├── settings.py        ← AppSettings lee .env
│   ├── gpu.py             ← GPUInfo, VRAMStatus
│   ├── models_ai.py       ← AIModelInfo, ModelStatus, AIModelType
│   ├── video.py           ← VideoMetadata
│   ├── frame.py           ← FrameData
│   ├── detection.py       ← BoundingBox, CropData
│   ├── search.py          ← SearchQuery, SearchResult, SearchResponse
│   ├── indexing.py        ← IndexStage, IndexProgress, IndexResult
│   └── database.py        ← CollectionStats
└── ui/                    ← PySide6 frontend
    ├── theme.py           ← Dark/light mode, QSS global
    ├── base_widget.py     ← Clase base: TODOS los paneles heredan
    ├── main_window.py     ← QMainWindow + sidebar + stacked panels
    ├── widgets/
    │   ├── sidebar.py, gpu_monitor.py
    │   ├── model_panel.py, model_card.py
    │   ├── video_selector.py, indexing_panel.py, progress_group.py
    │   ├── search_panel.py, result_gallery.py, result_card.py, result_detail.py
    │   └── stats_panel.py
    └── workers/
        ├── base_worker.py      ← Clase base: TODOS los workers heredan
        ├── model_download_worker.py, model_load_worker.py
        ├── index_worker.py, search_worker.py
```

## Principios de código

- **SOLID estricto:** cada clase tiene UNA responsabilidad
- **Polimorfismo:** BaseDetector/BaseEmbedder/BaseDescriber con herencia
- **Singleton:** ModelManager thread-safe (un solo set de modelos en VRAM)
- **Factory:** ModelRegistry.create_detector/embedder/describer()
- **Repository:** Database abstrae ChromaDB
- **Observer:** Signals/Slots PySide6 para workers↔UI
- **Dependency Inversion:** Indexer recibe interfaces por constructor
- **Template Method:** BaseWorker.run() → subclase.execute()
- **0 código duplicado:** BaseWidget y BaseWorker eliminan repetición
- **Tipado fuerte:** Pydantic v2 en TODAS las interfaces entre capas
- **Idempotencia:** download_model() no re-descarga, upsert no duplica

## Regla de dependencia

```
ui/ → core/ → models/    (permitido, fluye hacia abajo)
core/ → ui/               (PROHIBIDO)
models/ → core/           (PROHIBIDO)
```

## Modelos AI seleccionables desde la UI

| Modelo | Tipo | VRAM | Idioma |
|--------|------|------|--------|
| YOLOv11n | Detector | 0.3 GB | N/A |
| YOLOv11m | Detector | 0.5 GB | N/A |
| YOLOv11x | Detector | 1.0 GB | N/A |
| Jina CLIP v2 | Embedder | 3.5 GB | Multilingüe |
| Qwen2.5-VL 7B Q4 | Describer | 5.5 GB | Español |
| Moondream2 4-bit | Describer | 2.5 GB | Inglés |

## Cómo correr

```bash
git clone https://github.com/ghmedinac123/video_search_desktop.git
cd video_search_desktop
copy .env.example .env
pip install uv
uv sync
python main.py
```

Requiere: Windows 10+, Python 3.12+, GPU NVIDIA 8+ GB VRAM, CUDA 12.x

## Datos en runtime (gitignored)

- `data/chromadb/` — Base de datos embeddings
- `output/frames/` — Frames extraídos de videos
- `output/crops/` — Detecciones recortadas
- `logs/` — Logs rotativos (10MB, 7 días)

## Próximos pasos pendientes

- Debug primer run en PC con RTX 5060 Ti
- Conectar botones Descargar/Cargar en ModelPanel con workers
- Splash screen + iconos
- PyInstaller + Inno Setup para generar instalador .exe
- Optimizaciones de rendimiento en pipeline de indexación