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
| Python | 3.12 (uv lo descarga automaticamente) |
| GPU | NVIDIA con 8+ GB VRAM (RTX 3060, 4060, 5060, etc.) |
| CUDA | 12.x (viene con el driver NVIDIA) |
| RAM | 16 GB recomendado |
| Disco | ~10 GB (codigo + modelos AI) |
| Internet | Solo la primera vez (descarga modelos) |

---

## Instalacion

### 1. Instalar uv (gestor de paquetes)

uv es un gestor de paquetes ultrarapido escrito en Rust. Reemplaza pip, venv,
pip-tools y pyenv en una sola herramienta. No necesitas tener Python instalado.

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

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
- Instala TODAS las dependencias del `pyproject.toml`
- Genera `uv.lock` con versiones exactas (determinista)

**NO necesitas activar el entorno virtual manualmente.**

### 5. Ejecutar

```powershell
uv run python main.py
```

`uv run` ejecuta el comando dentro del entorno virtual del proyecto
sin necesidad de activarlo. Siempre usa `uv run` para ejecutar.

---

## Comandos utiles

```powershell
# Ejecutar la app
uv run python main.py

# Agregar una dependencia nueva
uv add nombre-paquete

# Actualizar dependencias
uv sync --upgrade

# Ver dependencias instaladas
uv pip list

# Verificar que Python 3.12 esta instalado
uv python list
```

---

## Uso

### 1. Modelos (primer tab)

- Selecciona el detector: YOLO26 Nano/Small/Medium
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
- Configuracion se guarda en `data/cameras.json` (persistente)

### 5. Estadisticas (quinto tab)

- Total de registros indexados (video + camaras unificado)
- Distribucion de clases (person, car, etc.)
- Boton para limpiar la coleccion

---

## Pipeline

### Indexar video grabado (v1.0)

```
Video .mp4 -> Extraer frames cada Ns -> YOLO26 detecta -> CLIP vectoriza
-> VLM describe -> ChromaDB almacena (embedding + metadata + ruta crop)
```

### Camaras en vivo (v2.0)

```
Camara RTSP 24/7 -> StreamCapture lee frame cada Ns
-> YOLO26 detecta: nada = descarta, algo = procesa
-> CLIP vectoriza -> VLM describe -> ChromaDB almacena
-> Todo acumulado en tiempo real -> busqueda instantanea
```

### Busqueda (ambas fuentes)

```
Texto usuario -> CLIP vectoriza texto -> ChromaDB busca similitud
-> Retorna crops mas parecidos con score, timestamp, camara/video
```

---

## Arquitectura

```
video_search_desktop/
├── main.py                  <- Punto de entrada (clase Application)
├── .python-version          <- Fija Python 3.12
├── pyproject.toml           <- Dependencias (uv sync las instala)
├── uv.lock                  <- Lockfile determinista (generado por uv)
├── .venv/                   <- Entorno virtual (creado por uv sync)
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
│   └── ... (16 modelos tipados)
├── ui/                      <- PySide6 (frontend dark/light)
│   ├── theme.py             <- Dark/light mode con toggle
│   ├── base_widget.py       <- Clase base (todos los paneles heredan)
│   ├── main_window.py       <- Ventana principal + sidebar
│   ├── widgets/             <- 13 componentes visuales
│   └── workers/             <- 6 QThread workers
├── data/                    <- Base de datos + config camaras
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

| Modelo | Funcion | VRAM | Velocidad |
|--------|---------|------|-----------|
| YOLO26 Nano | Detectar (ultra rapido) | 0.2 GB | ~2ms |
| YOLO26 Small | Detectar (balance) | 0.4 GB | ~5ms |
| YOLO26 Medium | Detectar (preciso) | 0.6 GB | ~12ms |
| Jina CLIP v2 | Embeddings img+txt | 3.5 GB | ~50ms |
| Qwen2.5-VL 7B Q4 | Describir (espanol) | 5.5 GB | ~500ms |
| Moondream2 4-bit | Describir (rapido) | 2.5 GB | ~130ms |

### Combinaciones de VRAM

| Combo | VRAM | GPU minima |
|-------|------|-----------|
| Nano + CLIP + Moondream (liviano) | 6.2 GB | RTX 3060 8GB |
| Small + CLIP + Qwen (completo) | 9.4 GB | RTX 4060 Ti 16GB |

---

## Configuracion (.env)

```env
MODELS_CACHE_DIR=./models_cache
DEFAULT_DETECTOR=yolo26n
DEFAULT_EMBEDDER=jina-clip-v2
DEFAULT_DESCRIBER=moondream2-4bit
MAX_CAMERAS=4
FRAME_INTERVAL=2
YOLO_CONFIDENCE=0.45
```

Modelos se descargan en `models_cache/` dentro del proyecto.
Borras la carpeta = borras TODO (portable, autocontenido).

---

## Stack

Python 3.12 | uv (gestor paquetes) | PySide6 | PyTorch CUDA |
Ultralytics YOLO26 | Jina CLIP v2 | Transformers | ChromaDB 1.5.7 |
Pydantic v2 | Loguru | pynvml | OpenCV

---

## Licencia

Proprietary — Todos los derechos reservados.
