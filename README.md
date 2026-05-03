# Video Search Desktop

Aplicacion de escritorio Windows para **buscar personas y objetos en videos de seguridad por lenguaje natural**.

Escribes "mujer con camisa amarilla" y el sistema te muestra las imagenes exactas con timestamps.

**100% local.** Ningun dato sale de tu PC. Los modelos de IA corren en tu GPU.

---

## Funcionalidades

### v1.0 — Video grabado ✅
- Cargar video MP4/AVI/MKV y procesar con IA
- Detectar personas, vehiculos, animales y objetos relevantes
- Buscar por lenguaje natural con galeria visual de resultados
- Descripciones automaticas de cada deteccion (VLM)
- Seleccionar modelos AI desde la interfaz

### v2.0 — Camaras RTSP en vivo ✅ (estilo NVR)
- Conectar hasta 4 camaras RTSP simultaneas desde la UI
- **Visor en vivo** a ~10 fps con bounding boxes YOLO sobreimpuestas
  (verde=persona, naranja=vehiculo, amarillo=animal, magenta=objetos)
- Procesamiento en tiempo real cada N segundos: YOLO + CLIP + VLM
- **Alert badge parpadeante** cuando detecta persona/vehiculo/tamper
- **Anti-tamper**: alerta si la camara se cubre (lente tapada) o se
  mueve bruscamente (cambio de escena)
- Configuracion de camaras persistente en `data/cameras.json`

### Caracteristicas empresariales (Tier 1+2)
- **Historial de eventos** cronologico con thumbnails clickables
- **Filtros de busqueda** multi-criterio: camara + clases YOLO + rango
  de fechas (queries sub-100ms con ChromaDB)
- **Notificaciones Telegram** con foto + caption (configurable por
  variables de entorno, severidad minima ajustable)
- **Exportacion forense ZIP** con cadena de custodia: manifest.json
  + frames + crops + SHA256 de cada archivo (validez legal)

### Arquitectura event-driven
- **EventBus singleton** Qt-based thread-safe (Observer pattern)
- **AlertManager** distribuye eventos a notificadores (Mediator)
- **TamperManager** orquesta detectores anti-sabotaje (Strategy)
- Interfaces abstractas (ABCs) para extender sin tocar el core:
  `BaseNotifier`, `BaseTamperDetector`, `BaseExporter`,
  `BaseRecognizer`, `BaseOCR`

---

## Requisitos

| Componente | Minimo |
|------------|--------|
| OS | Windows 10/11 64-bit |
| Python | 3.12 (uv lo descarga automaticamente) |
| GPU | NVIDIA con 8+ GB VRAM (RTX 3060, 4060, 5060, etc.) |
| CUDA | 12.x (viene con el driver NVIDIA) |
| RAM | 16 GB recomendado |
| Disco | ~12 GB (codigo + modelos AI + entorno virtual) |
| Internet | Solo la primera vez (descarga modelos ~5.6 GB) |

> **Nota RTX 50xx (Blackwell):** Las GPU RTX 5060/5070/5080/5090 usan arquitectura
> Blackwell (sm_120) que requiere PyTorch con CUDA 12.8. El `pyproject.toml` ya esta
> configurado para descargar la version correcta automaticamente.

---

## Instalacion

### 1. Instalar uv (gestor de paquetes)

uv es un gestor de paquetes ultrarapido escrito en Rust. Reemplaza pip, venv,
pip-tools y pyenv en una sola herramienta. No necesitas tener Python instalado.

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cierra y abre PowerShell despues de instalar.

### 2. Clonar el repositorio

```powershell
git clone https://github.com/ghmedinac123/video_search_desktop.git
cd video_search_desktop
```

### 3. Copiar configuracion

```powershell
copy .env.example .env
```

### 4. Instalar dependencias

```powershell
uv sync
```

Esto automaticamente:
- Descarga Python 3.12 si no lo tienes instalado
- Crea el entorno virtual en `.venv/` dentro del proyecto
- Instala TODAS las dependencias incluyendo PyTorch con CUDA
- Genera `uv.lock` con versiones exactas (determinista)

**NO necesitas activar el entorno virtual manualmente.**

### 5. Ejecutar

```powershell
uv run python main.py
```

### 6. Primer uso

1. Tab **Modelos** → Selecciona YOLO26 Nano + Jina CLIP + Moondream2
2. Click **Descargar seleccionados** (~5.6 GB, una sola vez)
3. Click **Cargar en GPU** (tarda ~15 segundos)
4. Tab **Indexar** → Carga un video MP4 → Click Iniciar
5. Tab **Buscar** → Escribe "persona camisa roja" → Resultados instantaneos

### 7. Camaras RTSP en vivo (NVR)

1. Tab **Cámaras** → "+ Agregar cámara"
2. Llena ID (ej. `tapo01`), nombre, URL RTSP, intervalo
   - Tapo C200/C236: `rtsp://USER:PASS@IP:554/stream1`
   - V380: `rtsp://admin:admin@IP:554/live/ch00_1`
3. Click **Conectar** → ves el video en vivo con cajas YOLO sobreimpuestas
4. Cada deteccion publica un evento al EventBus:
   - El badge "PERSONA DETECTADA" parpadea sobre la card
   - Si Telegram esta configurado, recibes la foto en tu chat
   - Aparece en el tab **Eventos** con thumbnail clickable
5. Tab **Buscar** funciona sobre todo lo que las camaras estan capturando

---

## Comandos utiles

```powershell
# Ejecutar la app
uv run python main.py

# Agregar una dependencia nueva
uv add nombre-paquete

# Actualizar dependencias
uv sync --upgrade

# Limpiar cache de descargas
uv cache clean
```

---

## Uso

### 1. Modelos (primer tab)

- Selecciona el detector: YOLO26 Nano/Small/Medium
- Selecciona el descriptor: Moondream (ingles, rapido)
- Click **Descargar** si no estan descargados
- Click **Cargar en GPU** para cargarlos en VRAM
- El monitor GPU muestra VRAM, temperatura y uso en tiempo real

### 2. Indexar (segundo tab)

- Carga un video MP4/AVI/MKV con el boton explorar
- Ajusta el intervalo de muestreo (cada cuantos segundos)
- Click **Iniciar** — progreso en tiempo real
- Solo indexa objetos relevantes para seguridad (personas, carros, animales, mochilas)
- Muebles y objetos estaticos se ignoran automaticamente

### 3. Buscar (tercer tab)

- Escribe en lenguaje natural en español o ingles:
  - "persona camisa verde"
  - "person with black shirt"
  - "hombre mochila"
  - "car"
- **Filtros de busqueda** (multi-criterio):
  - Dropdown de camaras
  - Checkboxes de clases YOLO (persona, auto, perro, mochila, etc.)
  - Rango de fechas con DatePicker (con checkbox para activar)
- Los resultados aparecen como galeria con scores de similitud
- Click en un resultado para ver el frame completo + descripcion VLM
- Boton para abrir el video en el momento exacto

### 4. Camaras (cuarto tab) — NVR estilo Hikvision/Reolink

- "+ Agregar camara" → formulario con ID, nombre, URL RTSP, intervalo
- Cards con visor en vivo (~10 fps) + bounding boxes YOLO
- Stats en tiempo real: Frames, Detecciones, FPS, hora
- **Alert badge parpadeante** segun severidad:
  - Verde: detecciones (vehiculo, animal, objeto)
  - Rojo: persona detectada
  - Rojo intenso: TAMPER (camara cubierta o movida)
- Botones por camara: Conectar/Desconectar, Editar, Eliminar
- Botones globales: Iniciar todas, Detener todas

### 5. Eventos (quinto tab) — Feed cronologico

- Ultimos 50 eventos de TODAS las camaras
- Cada fila: thumbnail + titulo + camara + hora + severidad
- Click en una fila → dialogo con detalle completo + JSON payload
- Borde lateral coloreado: azul=info, naranja=warning, rojo=critical

### 6. Estadisticas (sexto tab)

- Total de registros indexados
- Distribucion de clases detectadas
- Boton para limpiar la base de datos

---

## Pipeline

### Indexar video grabado (v1.0)

```
Video .mp4 → Extraer frames cada Ns → YOLO26 detecta (filtro seguridad)
→ CLIP vectoriza imagen → Moondream describe en ingles
→ ChromaDB almacena (embedding + metadata + ruta crop)
```

### Busqueda

```
Texto usuario → CLIP vectoriza texto → ChromaDB busca por coseno
→ Retorna crops mas parecidos con score, timestamp, descripcion
```

### Clases detectadas (filtro de seguridad)

| Clase | ID YOLO |
|-------|---------|
| person | 0 |
| bicycle | 1 |
| car | 2 |
| motorcycle | 3 |
| bus | 5 |
| truck | 7 |
| bird | 14 |
| cat | 15 |
| dog | 16 |
| backpack | 24 |
| umbrella | 25 |
| handbag | 26 |
| tie | 27 |
| suitcase | 28 |

Los objetos estaticos (couch, chair, table, TV, potted plant) se ignoran.

---

## Rendimiento (RTX 5060 Ti 16GB)

| Metrica | Valor |
|---------|-------|
| Indexar 21 frames | 2.6 segundos |
| Busqueda por texto | 96 ms |
| VRAM usada (3 modelos) | 7.4 / 16.0 GB |
| Temperatura GPU | 37-52 C |
| Detecciones por frame | Variable (solo objetos relevantes) |

---

## Arquitectura

```
video_search_desktop/
├── main.py                  ← Punto de entrada (clase Application)
├── pyproject.toml           ← Dependencias + PyTorch cu128
├── uv.lock                  ← Lockfile determinista
├── models_cache/            ← Modelos AI (~5.6 GB)
├── core/                    ← Backend (sin dependencia a UI)
│   ├── logger.py            ← Loguru centralizado
│   ├── gpu_utils.py         ← Monitor GPU dinamico
│   ├── database.py          ← ChromaDB 1.5.7 + filtros where
│   ├── model_registry.py    ← Catalogo modelos + Factory
│   ├── model_manager.py     ← Singleton thread-safe
│   ├── frame_extractor.py   ← Video → Frames
│   ├── stream_capture.py    ← RTSP continuo + preview + AI cada Ns
│   ├── indexer.py           ← Pipeline AI + tamper + EventBus publish
│   ├── searcher.py          ← Busqueda con filtros multi-criterio
│   ├── detectors/           ← BaseDetector → YOLODetector
│   ├── embedders/           ← BaseEmbedder → CLIPEmbedder
│   ├── describers/          ← BaseDescriber → Moondream/Qwen
│   ├── events/              ← ★ EventBus singleton (Observer)
│   ├── alerts/              ← ★ BaseNotifier → Telegram (+ AlertManager)
│   ├── tamper/              ← ★ BaseTamperDetector → BlackScreen, SceneChange
│   ├── export/              ← ★ BaseExporter → EvidenceZip + PdfReporter
│   ├── recognition/         ← ★ BaseRecognizer → FaceRecognizer (stub)
│   └── ocr/                 ← ★ BaseOCR → PlateOCR (stub regex placas)
├── models/                  ← Pydantic v2 (17+ modelos tipados)
│   └── event.py             ← ★ SecurityEvent + EventType + EventSeverity
├── ui/                      ← PySide6 (dark/light mode)
│   ├── widgets/             ← 16 componentes visuales
│   │   ├── alert_badge.py        ← ★ Badge parpadeante reutilizable
│   │   ├── event_history_panel.py ← ★ Feed cronologico
│   │   ├── search_filter_bar.py  ← ★ Filtros multi-criterio
│   │   └── ...
│   └── workers/             ← 7 QThread workers (heredan BaseWorker)
├── data/                    ← ChromaDB + cameras.json
├── output/                  ← Frames y crops generados
└── logs/                    ← Logs rotativos
```

★ = nuevos modulos de la arquitectura empresarial event-driven.

### Principios SOLID + Patrones

- **Single Responsibility**: una clase = una funcion clara
- **Open/Closed**: nuevo notifier/detector/exporter sin tocar managers
- **Liskov**: subclases respetan los contratos de las ABC
- **Interface Segregation**: ABCs minimas (1-3 metodos abstractos)
- **Dependency Inversion**: managers reciben ABCs, no implementaciones
- **Polimorfismo**: BaseDetector, BaseEmbedder, BaseDescriber,
  BaseNotifier, BaseTamperDetector, BaseExporter, BaseRecognizer, BaseOCR
- **Singleton**: ModelManager, EventBus, AlertManager
- **Factory**: ModelRegistry instancia segun config
- **Repository**: Database abstrae ChromaDB
- **Observer**: EventBus + Qt Signals/Slots
- **Strategy**: notificadores, detectores tamper, exportadores
- **Mediator**: AlertManager orquesta canales sin acoplarlos
- **Template Method**: BaseWorker.run(), BaseNotifier.handle()

### Modelos AI

| Modelo | Funcion | VRAM | Velocidad |
|--------|---------|------|-----------|
| YOLO26 Nano | Detectar (ultra rapido) | 0.2 GB | ~2ms |
| YOLO26 Small | Detectar (balance) | 0.4 GB | ~5ms |
| YOLO26 Medium | Detectar (preciso) | 0.6 GB | ~12ms |
| Jina CLIP v2 | Embeddings img+txt | 3.5 GB | ~50ms |
| Moondream2 fp16 | Describir (ingles) | 3.5 GB | ~500ms |

### Combinaciones de VRAM

| Combo | VRAM | GPU minima |
|-------|------|-----------|
| Nano + CLIP + Moondream | 7.2 GB | RTX 3060 8GB |
| Small + CLIP + Moondream | 7.4 GB | RTX 3060 8GB |
| Medium + CLIP + Moondream | 7.6 GB | RTX 3060 8GB |

---

## Configuracion (.env)

```env
# Rutas y modelos
MODELS_CACHE_DIR=./models_cache
DEFAULT_DETECTOR=yolo26n
DEFAULT_EMBEDDER=jina-clip-v2
DEFAULT_DESCRIBER=moondream2-4bit
MAX_CAMERAS=4
FRAME_INTERVAL=2
YOLO_CONFIDENCE=0.45

# HuggingFace (opcional, descargas mas rapidas)
HF_TOKEN=

# Telegram para alertas (opcional, deshabilitado si vacio)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Modelos se descargan en `models_cache/` dentro del proyecto.
Borras la carpeta = borras TODO (portable, autocontenido).

---

## Stack

Python 3.12 | uv | PySide6 | PyTorch CUDA 12.8 |
Ultralytics YOLO26 | Jina CLIP v2 | Transformers |
ChromaDB 1.5.7 | Pydantic v2 | Loguru | pynvml | OpenCV

---

## Licencia

Proprietary — Todos los derechos reservados.