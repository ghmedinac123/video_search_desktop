# Video Search Desktop

Aplicacion de escritorio Windows para **buscar personas y objetos en videos de seguridad por lenguaje natural**.

Escribes "mujer con camisa amarilla" y el sistema te muestra las imagenes exactas con timestamps.

**100% local.** Ningun dato sale de tu PC. Los modelos de IA corren en tu GPU.

---

## Funcionalidades

### v1.0 — Video grabado
- Cargar video MP4/AVI/MKV y procesar con IA
- Detectar personas, vehiculos y objetos automaticamente
- Buscar por lenguaje natural con galeria visual de resultados
- Seleccionar modelos AI desde la interfaz

### v2.0 — Camaras RTSP en vivo
- Conectar hasta 4 camaras RTSP desde la UI
- Procesamiento en tiempo real: YOLO detecta, CLIP vectoriza, VLM describe
- Frames sin detecciones se descartan automaticamente
- Busqueda instantanea sobre todo lo procesado (video + camaras)
- Configuracion de camaras persistente en JSON (no hardcoded)

---

## Requisitos

| Componente | Minimo |
|------------|--------|
| OS | Windows 10/11 64-bit |
| Python | 3.12+ |
| GPU | NVIDIA con 8+ GB VRAM (RTX 3060, 4060, 5060, etc.) |
| CUDA | 12.x (viene con el driver NVIDIA) |
| RAM | 16 GB recomendado |
| Disco | ~10 GB (codigo + modelos AI) |
| Internet | Solo la primera vez (descarga modelos) |

---

## Instalacion

```bash
git clone https://github.com/ghmedinac123/video_search_desktop.git
cd video_search_desktop
copy .env.example .env
pip install uv
uv sync
python main.py
```

La primera vez que abras el tab **Modelos** y hagas click en **Descargar**,
se descargaran los modelos AI (~3 GB combo liviano). Despues quedan en
`models_cache/` dentro del proyecto.

---

## Uso

### 1. Modelos (primer tab)

- Selecciona el detector: YOLOv11 Nano/Medium/XL
- Selecciona el descriptor: Qwen (espanol) o Moondream (ingles, rapido)
- Click **Descargar** si no estan descargados
- Click **Cargar en GPU** para cargarlos en VRAM
- El monitor GPU muestra consumo en tiempo real

### 2. Indexar (segundo tab)

- Arrastra un video MP4/AVI/MKV o usa el boton explorar
- Ajusta el intervalo de muestreo (cada cuantos segundos)
- Click **Iniciar** — ves 4 barras de progreso en tiempo real
- Puedes pausar o cancelar

### 3. Buscar (tercer tab)

- Escribe en lenguaje natural: "mujer camisa roja", "hombre mochila"
- Los resultados aparecen como galeria de imagenes con scores
- Click en un resultado para ver el frame completo con bounding box
- Boton para saltar al momento exacto en el video

### 4. Camaras RTSP (cuarto tab)

- Click **+ Agregar camara** — formulario con nombre + URL RTSP + intervalo
- Hasta 4 camaras simultaneas (limite configurable en .env)
- Click **Conectar** en cada camara para iniciar captura en tiempo real
- Stats en vivo: frames capturados, detecciones, FPS por camara
- **Iniciar todas** / **Detener todas** para control global
- Configuracion se guarda en `data/cameras.json` (persistente)

### 5. Estadisticas (quinto tab)

- Total de registros indexados (video + camaras unificado)
- Videos y camaras procesados
- Distribucion de clases (person, car, etc.)
- Boton para limpiar la coleccion

---

## Pipeline

### Indexar video grabado (v1.0)

```
Video .mp4 → Extraer frames cada Ns → YOLO detecta → CLIP vectoriza
→ VLM describe → ChromaDB almacena (embedding + metadata + ruta crop)
```

### Camaras en vivo (v2.0)

```
Camara RTSP 24/7 → StreamCapture lee frame cada Ns
→ YOLO detecta: nada = descarta, algo = procesa
→ CLIP vectoriza → VLM describe → ChromaDB almacena
→ Todo acumulado en tiempo real → busqueda instantanea
```

### Busqueda (ambas fuentes)

```
Texto usuario → CLIP vectoriza texto → ChromaDB busca similitud
→ Retorna crops mas parecidos con score, timestamp, camara/video
```

---

## Arquitectura

```
video_search_desktop/
├── main.py                  <- Punto de entrada (clase Application)
├── models_cache/            <- Modelos AI (se descargan al primer uso)
├── core/                    <- Backend (sin dependencia a UI)
│   ├── logger.py            <- Loguru centralizado
│   ├── gpu_utils.py         <- Monitor GPU dinamico (cualquier NVIDIA)
│   ├── database.py          <- ChromaDB 1.5.7 embebido
│   ├── model_registry.py    <- Catalogo 6 modelos + Factory
│   ├── model_manager.py     <- Singleton thread-safe
│   ├── frame_extractor.py   <- Video -> Frames (OpenCV)
│   ├── stream_capture.py    <- Camara RTSP -> Frames (v2.0)
│   ├── indexer.py           <- Pipeline: detect+embed+describe+store
│   ├── searcher.py          <- Busqueda por texto natural
│   ├── detectors/           <- BaseDetector -> YOLODetector
│   ├── embedders/           <- BaseEmbedder -> CLIPEmbedder
│   └── describers/          <- BaseDescriber -> Qwen/Moondream
├── models/                  <- Pydantic v2 (tipado fuerte)
│   ├── camera.py            <- CameraConfig + CameraStore (v2.0)
│   └── ... (15 modelos tipados)
├── ui/                      <- PySide6 (frontend dark/light)
│   ├── theme.py             <- Dark/light mode con toggle
│   ├── base_widget.py       <- Clase base (todos los paneles heredan)
│   ├── main_window.py       <- Ventana principal + sidebar
│   ├── widgets/             <- 13 componentes visuales
│   │   ├── camera_panel.py  <- CRUD camaras + monitoreo (v2.0)
│   │   └── ...
│   └── workers/             <- 6 QThread workers
│       ├── stream_worker.py <- Captura RTSP background (v2.0)
│       └── ...
├── data/                    <- Base de datos + config camaras
│   ├── chromadb/            <- Embeddings persistidos
│   └── cameras.json         <- Config camaras (creado desde UI)
├── output/                  <- Frames y crops generados
└── logs/                    <- Logs rotativos
```

### Principios

- **SOLID**: cada clase tiene una unica responsabilidad
- **Polimorfismo**: BaseDetector/BaseEmbedder/BaseDescriber con herencia
- **Singleton**: ModelManager thread-safe
- **Factory**: ModelRegistry crea instancias segun seleccion del usuario
- **Repository**: Database abstrae ChromaDB
- **Observer**: Signals/Slots de PySide6 para workers y UI
- **Dependency Inversion**: Indexer recibe interfaces, no implementaciones
- **Template Method**: BaseWorker.run() con execute() abstracto
- **0 codigo duplicado**: BaseWidget y BaseWorker eliminan repeticion

### Modelos AI (seleccionables desde la UI)

| Modelo | Funcion | VRAM | Idioma |
|--------|---------|------|--------|
| YOLOv11 Nano | Detectar (rapido) | 0.3 GB | N/A |
| YOLOv11 Medium | Detectar (balance) | 0.5 GB | N/A |
| YOLOv11 XL | Detectar (preciso) | 1.0 GB | N/A |
| Jina CLIP v2 | Embeddings img+txt | 3.5 GB | Multilingue |
| Qwen2.5-VL 7B Q4 | Describir (detallado) | 5.5 GB | Espanol |
| Moondream2 4-bit | Describir (rapido) | 2.5 GB | Ingles |

### Combinaciones de VRAM

| Combo | VRAM | GPU minima |
|-------|------|-----------|
| Nano + CLIP + Moondream (liviano) | 6.3 GB | RTX 3060 8GB |
| Medium + CLIP + Qwen (completo) | 9.5 GB | RTX 4060 Ti 16GB |

---

## Configuracion (.env)

```env
MODELS_CACHE_DIR=./models_cache    # Modelos DENTRO del proyecto
DEFAULT_DETECTOR=yolo11n           # Modelo por defecto
DEFAULT_DESCRIBER=moondream2-4bit  # VLM por defecto
MAX_CAMERAS=4                      # Limite camaras RTSP
FRAME_INTERVAL=2                   # Segundos entre frames
YOLO_CONFIDENCE=0.45               # Confianza minima deteccion
```

Modelos se descargan en `models_cache/` dentro del proyecto.
Borras la carpeta = borras TODO (portable, autocontenido).

---

## Stack

Python 3.12 | PySide6 | PyTorch CUDA | Ultralytics YOLOv11 | Jina CLIP v2 |
Transformers | ChromaDB 1.5.7 | Pydantic v2 | Loguru | pynvml | OpenCV

---

## Licencia

Proprietary — Todos los derechos reservados.
