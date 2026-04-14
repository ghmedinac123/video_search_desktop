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

### v2.0 — Camaras RTSP en vivo (en desarrollo)
- Conectar hasta 4 camaras RTSP desde la UI
- Procesamiento en tiempo real: YOLO detecta, CLIP vectoriza, VLM describe
- Frames sin detecciones se descartan automaticamente
- Busqueda instantanea sobre todo lo procesado (video + camaras)
- Configuracion de camaras persistente en JSON

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
- Los resultados aparecen como galeria con scores de similitud
- Click en un resultado para ver el frame completo + descripcion VLM
- Boton para abrir el video en el momento exacto

### 4. Estadisticas (cuarto tab)

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
├── .python-version          ← Fija Python 3.12
├── pyproject.toml           ← Dependencias + PyTorch cu128
├── uv.lock                  ← Lockfile determinista
├── .venv/                   ← Entorno virtual (~5.8 GB)
├── models_cache/            ← Modelos AI (~5.6 GB)
├── core/                    ← Backend (sin dependencia a UI)
│   ├── logger.py            ← Loguru centralizado
│   ├── gpu_utils.py         ← Monitor GPU dinamico
│   ├── database.py          ← ChromaDB 1.5.7 embebido
│   ├── model_registry.py    ← Catalogo modelos + Factory
│   ├── model_manager.py     ← Singleton thread-safe
│   ├── frame_extractor.py   ← Video → Frames
│   ├── stream_capture.py    ← Camara RTSP → Frames (v2.0)
│   ├── indexer.py           ← Pipeline: detect+embed+describe+store
│   ├── searcher.py          ← Busqueda por texto natural
│   ├── detectors/           ← BaseDetector → YOLODetector
│   ├── embedders/           ← BaseEmbedder → CLIPEmbedder
│   └── describers/          ← BaseDescriber → Moondream/Qwen
├── models/                  ← Pydantic v2 (16 modelos tipados)
├── ui/                      ← PySide6 (dark/light mode)
│   ├── widgets/             ← 13 componentes visuales
│   └── workers/             ← 6 QThread workers
├── data/                    ← ChromaDB + config camaras
├── output/                  ← Frames y crops generados
└── logs/                    ← Logs rotativos
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

Python 3.12 | uv | PySide6 | PyTorch CUDA 12.8 |
Ultralytics YOLO26 | Jina CLIP v2 | Transformers |
ChromaDB 1.5.7 | Pydantic v2 | Loguru | pynvml | OpenCV

---

## Licencia

Proprietary — Todos los derechos reservados.