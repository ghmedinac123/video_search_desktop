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

## Arquitectura (event-driven, SOLID)

```
main.py                        <- Clase Application ensambla core + UI
├── core/                      <- Backend (NO importa nada de ui/)
│   ├── logger.py              <- Loguru centralizado
│   ├── gpu_utils.py           <- GPUUtils estatico
│   ├── model_registry.py      <- Catalogo 6 modelos + Factory + SECURITY_CLASSES
│   ├── model_manager.py       <- Singleton thread-safe
│   ├── database.py            <- ChromaDB embebido + filtros where ($and/$in/$gte)
│   ├── frame_extractor.py     <- Video -> frames
│   ├── stream_capture.py      <- RTSP continuo + preview 10fps + AI cada Ns
│   ├── indexer.py             <- Pipeline: detect+embed+describe+store + tamper
│   ├── searcher.py            <- Texto -> CLIP -> DB con filtros multi-criterio
│   ├── detectors/             <- BaseDetector ABC + YOLODetector
│   ├── embedders/             <- BaseEmbedder ABC + CLIPEmbedder
│   ├── describers/            <- BaseDescriber ABC + Moondream/Qwen
│   ├── events/                <- ★ Observer pattern (event-driven core)
│   │   └── event_bus.py       <- Singleton Qt-based EventBus thread-safe
│   ├── alerts/                <- ★ Notificaciones (Strategy + Mediator)
│   │   ├── base_notifier.py   <- ABC + template method handle()
│   │   ├── telegram_notifier.py <- POST a Bot API con foto
│   │   └── alert_manager.py   <- Singleton, distribuye en threads
│   ├── tamper/                <- ★ Anti-tamper (Strategy)
│   │   ├── base_tamper_detector.py <- ABC + TamperResult
│   │   ├── black_screen_detector.py <- brillo + varianza
│   │   ├── scene_change_detector.py <- histograma Bhattacharyya
│   │   └── tamper_manager.py  <- una instancia por camara con cooldown
│   ├── export/                <- ★ Exportadores (Strategy)
│   │   ├── base_exporter.py   <- ABC export(events, path)
│   │   ├── evidence_exporter.py <- ZIP forense + manifest + SHA256
│   │   └── pdf_reporter.py    <- STUB Tier 3 (reportlab)
│   ├── recognition/           <- ★ STUB Tier 3 (faces)
│   │   ├── base_recognizer.py <- ABC RecognitionResult
│   │   └── face_recognizer.py <- placeholder InsightFace/Buffalo
│   └── ocr/                   <- ★ STUB Tier 3 (placas)
│       ├── base_ocr.py        <- ABC OCRResult
│       └── plate_ocr.py       <- placeholder PaddleOCR + regex placas
├── models/                    <- Pydantic v2
│   ├── settings.py            <- AppSettings + setup_model_environment()
│   ├── camera.py              <- CameraConfig + CameraStore
│   ├── event.py               <- ★ SecurityEvent + EventType + EventSeverity
│   └── ... (16+ modelos tipados)
└── ui/                        <- PySide6 frontend
    ├── theme.py
    ├── base_widget.py         <- Clase base TODOS los paneles heredan
    ├── main_window.py         <- QMainWindow + sidebar + stack (6 paneles)
    ├── widgets/
    │   ├── alert_badge.py     <- ★ Badge parpadeante reutilizable
    │   ├── camera_panel.py    <- Cards con preview, bboxes, alert_badge
    │   ├── event_history_panel.py <- ★ Feed cronologico (suscriptor bus)
    │   ├── search_filter_bar.py <- ★ Camaras + clases + fechas
    │   ├── search_panel.py    <- Integra search_filter_bar
    │   └── ...
    └── workers/               <- QThread workers (heredan BaseWorker)
        ├── stream_worker.py   <- Lectura continua RTSP + preview con bboxes
        └── ...
```

★ = nuevos modulos de la arquitectura empresarial event-driven.

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

## Pipeline v1.0 — FUNCIONANDO ✅ (video grabado)

```
Video .mp4 → Extraer frames cada 2s → YOLO26 detecta (filtro SECURITY_CLASSES)
→ CLIP vectoriza imagen → Moondream describe (fp16)
→ ChromaDB almacena (embedding + metadata + ruta crop)
→ Busqueda: texto → CLIP vectoriza → coseno → resultados
```

## Pipeline v2.0 — FUNCIONANDO ✅ (RTSP en vivo, estilo NVR)

```
RTSP continuo (~30fps) → preview UI (10fps con bboxes YOLO) →
cada interval_seconds → AI pipeline (YOLO+CLIP+Moondream) →
process_single_frame() → publica SecurityEvent.DETECTION al EventBus →
[suscriptores: AlertBadge UI, EventHistoryPanel, AlertManager → Telegram]
```

Probado con Tapo C200/C236 a `rtsp://USER:PASS@IP:554/stream1`.
Busqueda instantanea (<100ms) sobre eventos en vivo + videos historicos.

## Sistema event-driven (Observer + Strategy + Mediator)

EventBus = QObject singleton thread-safe. Publishers (Indexer,
StreamCapture, TamperManager) publican SecurityEvent. Subscribers (UI,
AlertManager, EventHistoryPanel) reaccionan sin acoplarse.

```python
# Publicar
EventBus.get_instance().publish(SecurityEvent(
    event_type=EventType.DETECTION,
    camera_id="tapo01",
    severity=EventSeverity.WARNING,
    title="Persona detectada",
    payload={"classes": ["person"], "count": 1},
))

# Suscribir
EventBus.get_instance().subscribe(my_callback)
```

### Tipos de evento (models/event.py)
- DETECTION: AI detecto algo (severity=WARNING si person, INFO si vehiculo)
- TAMPER: BlackScreen o SceneChange disparo (severity=CRITICAL/WARNING)
- CAMERA_CONNECTED / CAMERA_DISCONNECTED
- NOTIFICATION_SENT / SYSTEM

### Para agregar un canal de notificacion nuevo
```python
from core.alerts.base_notifier import BaseNotifier

class WhatsAppNotifier(BaseNotifier):
    def __init__(self):
        super().__init__("WhatsApp", min_severity=EventSeverity.CRITICAL)
    def send(self, event: SecurityEvent) -> bool:
        # tu integracion HTTP aqui
        return True

AlertManager.get_instance().register(WhatsAppNotifier())
```

### Para agregar un detector anti-tamper nuevo
```python
from core.tamper.base_tamper_detector import BaseTamperDetector, TamperResult

class BlurDetector(BaseTamperDetector):
    def __init__(self):
        super().__init__("BlurDetector")
    def analyze(self, frame_bgr) -> TamperResult:
        variance = cv2.Laplacian(frame_bgr, cv2.CV_64F).var()
        if variance < 50:
            return TamperResult(triggered=True, reason="lens_blur",
                                metric=variance, severity=EventSeverity.WARNING)
        return TamperResult(triggered=False)

# El TamperManager del Indexer lo agrega al pipeline
```

## Variables de entorno opcionales (.env)

```env
HF_TOKEN=                # Token HuggingFace para descargas mas rapidas
TELEGRAM_BOT_TOKEN=      # Bot creado con @BotFather
TELEGRAM_CHAT_ID=        # Chat ID destino (obtener con @userinfobot)
```

Si TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID faltan, el TelegramNotifier
se auto-deshabilita silenciosamente (log INFO, no error).

## Estado de features por Tier

### Tier 1 — completado ✅
- Bounding boxes en preview en vivo (cv2.rectangle por clase con label)
- Alert badge parpadeante por severidad (verde/naranja/rojo)
- Filtros busqueda multi-criterio (camara, clases YOLO, rango fechas)
- Historial de eventos con thumbnails clickables y dialogo detalle

### Tier 2 — parcialmente completado
- ✅ TelegramNotifier (auto-deshabilita sin token)
- ✅ Anti-tamper: BlackScreenDetector + SceneChangeDetector + cooldown
- ⏳ Grid 1/4/9 camaras simultaneas (refactor UI grande)
- ⏳ ROI zones (canvas drawing + persistencia poligonos)

### Tier 3 — interfaces listas, implementacion pendiente
- ✅ ABC BaseRecognizer + FaceRecognizer stub (`uv add insightface onnxruntime-gpu`)
- ✅ ABC BaseOCR + PlateOCR stub con regex de placas LATAM
- ✅ EvidenceExporter (ZIP forense + manifest.json + chain_of_custody.txt con SHA256)
- ✅ ABC BaseExporter + PdfReporter stub (`uv add reportlab`)
- ⏳ Re-identificacion cross-camera (OSNet o similar)

### Tier 4 — futuro
- Deteccion de comportamiento (loitering, peleas, caidas con YOLO-Pose)
- Heatmap de actividad
- Multi-tenant + autenticacion

## Camaras del usuario

- 1x Tapo C200/C236: `rtsp://USER:PASS@IP:554/stream1` (HD) o `/stream2` (SD)
  — funciona out of the box con RTSP nativo
- 3x Blurams 2K: NO soportan RTSP, solo app propietaria → sirven para grabar .mp4

## Otras mejoras pendientes

- Activar Developer Mode en Windows para symlinks de HuggingFace
- PyInstaller + Inno Setup para instalador .exe
- Tests automatizados (pytest)