# CLAUDE.md — Contexto del proyecto para Claude

## Que es este proyecto

App de escritorio Windows para busqueda visual en videos de camaras de seguridad
por lenguaje natural. Escribes "mujer con camisa amarilla" y te muestra los frames
exactos con timestamps. 100% local en GPU NVIDIA, sin servidores externos.

Dos modos: v1.0 video grabado (FUNCIONANDO) + v2.0 camaras RTSP en vivo (PENDIENTE conectar).

## Repo y estado

- **GitHub:** github.com/ghmedinac123/video_search_desktop
- **Estado:** v2.0 — 63+ archivos Python, pipeline v1.0 funcionando al 100%
- **Python:** 3.12 (fijado en .python-version como "3.12", NO "3.12.13")
- **Gestor paquetes:** uv (NO pip, NO conda, NO poetry)
- **PC ejecucion:** Ryzen 5 9600X, 32GB DDR5, RTX 5060 Ti 16GB, Win 11 Pro, SSD 932GB

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
- Primera vez: abrir tab Modelos → Descargar → Cargar en GPU → listo

## Stack tecnico (versiones probadas y funcionando)

| Paquete | Version | Nota |
|---------|---------|------|
| Python | 3.12.13 | fijado en .python-version |
| uv | 0.11.3 | gestor de paquetes |
| PyTorch | cu128 (CUDA 12.8) | OBLIGATORIO para RTX 5060 Ti (Blackwell sm_120) |
| PySide6 | 6.11.0 | GUI |
| Ultralytics | 8.4.37 | YOLO26 |
| sentence-transformers | 5.4.0 | NO soporta imagenes, solo texto |
| transformers | 4.x (<5.0) | OBLIGATORIO — 5.x rompe Moondream |
| ChromaDB | 1.5.7 | base vectorial embebida |
| torchao | 0.17.0 | instalado pero NO se usa (4-bit no funciona en Windows) |
| einops | 0.8.2 | dependencia de CLIP |
| timm | 1.0.26 | dependencia de CLIP |

## Modelos AI (los que funcionan)

| Modelo | Repo | VRAM | Funcion | Estado |
|--------|------|------|---------|--------|
| YOLO26 Nano | yolo26n.pt | 0.2 GB | Detectar objetos | ✅ Funciona |
| YOLO26 Small | yolo26s.pt | 0.4 GB | Detectar objetos | ✅ Funciona |
| YOLO26 Medium | yolo26m.pt | 0.6 GB | Detectar objetos | No descargado |
| Jina CLIP v2 | jinaai/jina-clip-v2 | 3.5 GB | Embeddings img+txt | ✅ Funciona |
| Moondream2 fp16 | vikhyatk/moondream2 | 3.5 GB | Describir imagenes | ✅ Funciona |
| Qwen2.5-VL 7B | Qwen/Qwen2.5-VL-7B-Instruct | 5.5 GB | Describir (espanol) | No probado |

### Combo actual en GPU: YOLO26s + CLIP + Moondream fp16 = 7.4 GB de 16 GB

### IMPORTANTE sobre Moondream:
- Se usa `vikhyatk/moondream2` en float16, NO `moondream/moondream-2b-2025-04-14-4bit`
- La version 4-bit requiere torchao con CUDA 12.8 en Windows y NO existe ese build
- El describer carga con `torch_dtype=torch.float16` sin revision, sin torchao
- El model_id en el catalogo sigue diciendo "moondream2-4bit" pero el repo es vikhyatk/moondream2

### IMPORTANTE sobre CLIP:
- sentence-transformers 5.4.0 NO soporta modalidad 'image' con Jina CLIP v2
- clip_embedder.py usa AutoModel directo para imagenes y AutoTokenizer para texto
- NO usa SentenceTransformer para nada (se elimino esa dependencia del embedder)
- Ambos (texto e imagen) usan el MISMO modelo AutoModel para embeddings alineados
- Se agrega .float() antes de .numpy() porque CLIP devuelve BFloat16

## RTX 5060 Ti — Compatibilidad (Blackwell sm_120)

CRITICO: La RTX 5060 Ti usa arquitectura Blackwell con CUDA capability sm_120.
- PyTorch cu124 NO soporta sm_120 (da warning y no funciona)
- PyTorch cu128 SI soporta sm_120
- torchao cu128 NO tiene builds para Windows (solo Linux)
- pyproject.toml DEBE tener [tool.uv.sources] apuntando a pytorch-cu128

```toml
[tool.uv.sources]
torch = { index = "pytorch-cu128" }
torchvision = { index = "pytorch-cu128" }

[[tool.uv.index]]
name = "pytorch-cu128"
url = "https://download.pytorch.org/whl/cu128"
explicit = true
```

## Bugs encontrados y corregidos (sesion 13/abril/2026)

1. **gpu_utils.py** — `total_mem` no existe en PyTorch nuevo → cambiar a `total_memory`
2. **gpu_utils.py** — Division por `1e9` da 17.1 GB → cambiar a `1024**3` da 15.9 GB
3. **gpu_monitor.py** — `_create_metric()` creaba doble layout con `__import__` hack → reescrito limpio
4. **model_panel.py** — `_on_model_selected` disparaba antes de crear `_vram_estimate_label` → hasattr guard
5. **sidebar.py** — `_toggle_theme` tenia import local que sombreaba Theme → quitado import redundante
6. **pyproject.toml** — BOM de UTF8 de PowerShell → limpiado con TrimStart
7. **pyproject.toml** — Necesita cu128 en [tool.uv.sources], no cu124
8. **.python-version** — Debe decir "3.12", no "3.12.13" (uv no acepta version completa)
9. **model_registry.py** — YOLO se descargaba en raiz del proyecto → fix ruta a models_cache/ultralytics/
10. **model_registry.py** — snapshot_download bajaba todo el repo → ignore_patterns para ONNX/flax
11. **model_registry.py** — create_detector usaba repo_id directo → ahora usa ruta completa models_cache/
12. **moondream_describer.py** — revision="2025-04-14" no existe en repo 4-bit → eliminado revision param
13. **moondream_describer.py** — Cambiado a vikhyatk/moondream2 con torch_dtype=torch.float16
14. **moondream_describer.py** — Parche torchao int4_weight_only ya NO se necesita (se usa fp16)
15. **clip_embedder.py** — sentence-transformers no soporta imagenes → reescrito con AutoModel directo
16. **clip_embedder.py** — BFloat16 error en numpy → agregado .float() antes de .numpy()
17. **yolo_detector.py** — Detectaba muebles/sillas → filtro SECURITY_CLASSES (solo personas, carros, animales, mochilas)
18. **main.py** — Botones Descargar/Cargar no conectados a workers → conectados con callbacks
19. **Dependencias faltantes** — einops, timm, torchao → agregados con `uv add`
20. **transformers 5.x** — Rompe Moondream → pinned a `>=4.46,<5.0`

## Arquitectura

```
main.py                        <- Clase Application ensambla core + UI
├── core/                      <- Backend (NO importa nada de ui/)
│   ├── logger.py              <- Loguru centralizado
│   ├── gpu_utils.py           <- GPUUtils estatico (usa total_memory, 1024**3)
│   ├── model_registry.py      <- Catalogo 6 modelos + Factory + SECURITY_CLASSES
│   ├── model_manager.py       <- Singleton thread-safe
│   ├── database.py            <- ChromaDB embebido, Repository
│   ├── frame_extractor.py     <- Video -> frames
│   ├── stream_capture.py      <- Camara RTSP -> frames (v2.0, NO conectado aun)
│   ├── indexer.py             <- Pipeline: detect+embed+describe+store
│   ├── searcher.py            <- Texto -> CLIP embed -> ChromaDB query coseno
│   ├── detectors/
│   │   ├── base_detector.py   <- ABC
│   │   └── yolo_detector.py   <- SECURITY_CLASSES filter (persona, carro, animal, mochila)
│   ├── embedders/
│   │   ├── base_embedder.py   <- ABC
│   │   └── clip_embedder.py   <- AutoModel directo (NO sentence-transformers)
│   └── describers/
│       ├── base_describer.py  <- ABC
│       ├── qwen_describer.py  <- Hereda BaseDescriber (espanol, NO probado)
│       └── moondream_describer.py <- fp16, vikhyatk/moondream2 (SIN torchao)
├── models/                    <- Pydantic v2
│   ├── settings.py            <- AppSettings + setup_model_environment()
│   ├── camera.py              <- CameraConfig + CameraStore (v2.0)
│   └── ... (16 modelos tipados)
└── ui/                        <- PySide6 frontend
    ├── theme.py               <- Dark/light mode
    ├── base_widget.py         <- Clase base TODOS los paneles heredan
    ├── main_window.py         <- QMainWindow + sidebar + stack
    ├── widgets/ (13)          <- Componentes visuales
    │   ├── camera_panel.py    <- CRUD camaras (EXISTE pero NO conectado)
    │   └── ...
    └── workers/ (6)           <- QThread workers (heredan BaseWorker)
        ├── stream_worker.py   <- Captura RTSP (EXISTE pero NO conectado)
        └── ...
```

## Regla de dependencia

```
ui/ -> core/ -> models/    (permitido)
core/ -> ui/               (PROHIBIDO)
models/ -> core/           (PROHIBIDO)
```

## models_cache/ — Estructura limpia (~5.6 GB)

```
models_cache/
├── ultralytics/                              (25 MB)
│   ├── yolo26n.pt
│   └── yolo26s.pt
├── huggingface/
│   ├── models--jinaai--jina-clip-v2          (1.7 GB) ← pesos CLIP
│   ├── models--jinaai--jina-clip-implementation       ← codigo CLIP
│   ├── models--jinaai--jina-embeddings-v3    (17 MB)  ← tokenizer CLIP
│   ├── models--jinaai--xlm-roberta-flash...           ← codigo CLIP
│   └── models--vikhyatk--moondream2          (3.8 GB) ← pesos Moondream fp16
└── modules/transformers_modules/                      ← codigo Python modelos
```

## Camaras del usuario

- 3x Blurams 2K (NO soportan RTSP, solo app propietaria — sirven para grabar .mp4)
- 1x camara V380 Pro de AliExpress (pendiente de llegar, SI soporta RTSP con truco ceshi.ini)
  - URL RTSP: rtsp://admin:admin@IP:554/live/ch00_1 (HD) o /live/ch00_0 (SD)
- Recomendacion futura: Tapo C200 ($19 USD) — RTSP nativo sin trucos

## Pipeline v1.0 — FUNCIONANDO ✅

```
Video .mp4 → Extraer frames cada 2s → YOLO26 detecta (filtro SECURITY_CLASSES)
→ CLIP vectoriza imagen (AutoModel.get_image_features) → Moondream describe (fp16)
→ ChromaDB almacena (embedding + metadata + ruta crop)
→ Busqueda: texto → CLIP vectoriza (AutoModel.get_text_features) → coseno → resultados
```

Probado: 21 frames, 2 detecciones personas, 2.6 segundos, busqueda 96ms.

## PENDIENTE — Conectar camaras RTSP v2.0

5 archivos a modificar:
1. **core/indexer.py** → agregar `process_single_frame()` para frames individuales de RTSP
2. **models/__init__.py** → agregar imports de camera
3. **ui/widgets/sidebar.py** → agregar 5to boton "Camaras" en SECTIONS
4. **ui/main_window.py** → agregar 5to panel CameraPanel al stack
5. **main.py** → conectar CameraPanel con StreamWorker y pipeline

Los archivos stream_capture.py, stream_worker.py, camera_panel.py, camera.py YA EXISTEN.
Solo falta ensamblarlos en la app.

## PENDIENTE — Mejoras futuras

- HF_TOKEN en .env para descargas mas rapidas (usuario tiene cuenta: ghmedinac)
- Reconocimiento facial (InsightFace/Buffalo)
- Placas vehiculos (PaddleOCR)
- Alertas Telegram
- Deteccion caidas (YOLO-Pose)
- PyInstaller + Inno Setup para instalador .exe
- Activar Developer Mode en Windows para symlinks de HuggingFace