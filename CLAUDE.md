# CLAUDE.md — Contexto del proyecto para Claude

## Que es este proyecto

App de escritorio Windows para busqueda visual en videos de camaras de seguridad
por lenguaje natural. Escribes "mujer con camisa amarilla" y te muestra los frames
exactos con timestamps. 100% local en GPU NVIDIA, sin servidores externos.

Dos modos: v1.0 video grabado + v2.0 camaras RTSP en vivo.

## Repo y estado

- **GitHub:** github.com/ghmedinac123/video_search_desktop
- **Estado:** v2.0 — 63+ archivos Python
- **Python:** 3.12 (fijado en .python-version)
- **Gestor paquetes:** uv (NO pip, NO conda, NO poetry)

## Como correr

```powershell
git clone https://github.com/ghmedinac123/video_search_desktop.git
cd video_search_desktop
copy .env.example .env
uv sync
uv run python main.py
```

IMPORTANTE:
- uv sync crea .venv/ automaticamente, descarga Python 3.12 si no existe
- Siempre usar `uv run` para ejecutar — NO activar venv manualmente
- Para agregar dependencias: `uv add nombre-paquete` (NO pip install)
- Modelos AI se descargan en models_cache/ dentro del proyecto

## Stack

- **GUI:** PySide6 (LGPL, comercial gratis) — dark/light mode
- **Detector:** YOLO26 n/s/m (end-to-end, sin NMS, Ultralytics)
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
│   ├── gpu_utils.py           <- GPUUtils estatico
│   ├── model_registry.py      <- Catalogo 6 modelos + Factory (YOLO26)
│   ├── model_manager.py       <- Singleton thread-safe
│   ├── database.py            <- ChromaDB embebido, Repository
│   ├── frame_extractor.py     <- Video -> frames
│   ├── stream_capture.py      <- Camara RTSP -> frames (v2.0)
│   ├── indexer.py             <- Pipeline + process_single_frame()
│   ├── searcher.py            <- Texto -> CLIP embed -> ChromaDB query
│   ├── detectors/
│   │   ├── base_detector.py   <- ABC
│   │   └── yolo_detector.py   <- Hereda BaseDetector (funciona con YOLO26)
│   ├── embedders/
│   │   ├── base_embedder.py   <- ABC
│   │   └── clip_embedder.py   <- Hereda BaseEmbedder
│   └── describers/
│       ├── base_describer.py  <- ABC
│       ├── qwen_describer.py  <- Hereda BaseDescriber (espanol)
│       └── moondream_describer.py <- Hereda BaseDescriber (ingles)
├── models/                    <- Pydantic v2
│   ├── settings.py            <- AppSettings + setup_model_environment()
│   ├── camera.py              <- CameraConfig + CameraStore (v2.0)
│   └── ... (16 modelos tipados)
└── ui/                        <- PySide6 frontend
    ├── theme.py               <- Dark/light mode
    ├── base_widget.py         <- Clase base TODOS los paneles heredan
    ├── main_window.py         <- QMainWindow + sidebar + stack
    ├── widgets/ (13)          <- Componentes visuales
    └── workers/ (6)           <- QThread workers (heredan BaseWorker)
```

## Regla de dependencia

```
ui/ -> core/ -> models/    (permitido)
core/ -> ui/               (PROHIBIDO)
models/ -> core/           (PROHIBIDO)
```

## Decisiones tecnicas

- Python 3.12 fijado en .python-version
- uv como unico gestor: uv sync + uv run (nunca pip install)
- YOLO26 (end-to-end sin NMS) reemplaza YOLO11
- Modelos en models_cache/ (HF_HOME apunta ahi via setup_model_environment)
- Camaras configurables desde UI, persistidas en data/cameras.json
- MAX_CAMERAS=4 en .env (limite GPU)
- Defaults livianos: yolo26n + moondream2-4bit (6.2 GB VRAM)
- Borrar carpeta = borrar TODO (portable)

## Pendiente

- Debug primer run en PC con RTX 5060 Ti
- Aplicar 5 modificaciones para conectar camaras al pipeline:
  1. core/indexer.py -> agregar process_single_frame()
  2. models/__init__.py -> agregar imports camera
  3. ui/widgets/sidebar.py -> agregar 5to boton Camaras
  4. ui/main_window.py -> agregar 5to panel
  5. main.py -> conectar CameraPanel con StreamWorker
- Test end-to-end: video + camaras + busqueda
- Futuro: reconocimiento facial (InsightFace/Buffalo)
- Futuro: placas vehiculos (PaddleOCR)
- Futuro: alertas Telegram
- Futuro: PyInstaller + Inno Setup
