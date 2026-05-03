# VIDEO SEARCH DESKTOP — DOCUMENTACIÓN TÉCNICA COMPLETA

## FASE 0: Documentación, Arquitectura e Infraestructura

> **REGLA DE ORO:** No se escribe código hasta que este documento esté aprobado.
> Cada fase se valida con `python -c "import modulo"` antes de avanzar.

---

## ÍNDICE

1. [Visión del Producto](#1-visión-del-producto)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Principios de Ingeniería](#3-principios-de-ingeniería)
4. [Arquitectura del Sistema](#4-arquitectura-del-sistema)
5. [Sistema de Logging](#5-sistema-de-logging)
6. [Modelos Pydantic](#6-modelos-pydantic)
7. [Core Backend — Diseño de Clases](#7-core-backend--diseño-de-clases)
8. [UI Frontend — Diseño de Clases](#8-ui-frontend--diseño-de-clases)
9. [Estructura de Carpetas](#9-estructura-de-carpetas)
10. [Dependencias — pyproject.toml](#10-dependencias--pyprojecttoml)
11. [Configuración — .env](#11-configuración--env)
12. [Plan de Fases Detallado](#12-plan-de-fases-detallado)
13. [Criterios de Aceptación por Fase](#13-criterios-de-aceptación-por-fase)
14. [Empaquetado y Entrega](#14-empaquetado-y-entrega)

---

## 1. VISIÓN DEL PRODUCTO

### 1.1 Qué es

Aplicación de escritorio Windows que permite:

- Indexar videos de cámaras de seguridad (CCTV, NVR, DVR).
- Detectar automáticamente personas, vehículos y objetos en cada frame.
- Describir cada detección con lenguaje natural usando IA (VLM).
- Buscar por lenguaje natural: "mujer con camisa amarilla", "hombre con mochila negra".
- Mostrar galería visual de resultados con timestamps exactos.
- Saltar al momento exacto del video donde aparece la detección.

### 1.2 Para quién

- Operadores de seguridad que necesitan buscar eventos en horas de video.
- Empresas de vigilancia que quieren ofrecer búsqueda inteligente a sus clientes.
- Investigadores forenses que analizan grabaciones de cámaras.

### 1.3 Diferenciador

100% local. Ningún dato sale de la máquina del cliente. Sin servidores externos,
sin APIs de pago, sin conexión permanente a internet. Los modelos de IA corren
en la GPU local del usuario.

---

## 2. STACK TECNOLÓGICO

### 2.1 Lenguaje y Runtime

| Componente       | Tecnología          | Versión   | Justificación                         |
|------------------|---------------------|-----------|---------------------------------------|
| Lenguaje         | Python              | 3.12+     | Ecosistema ML/AI maduro               |
| Gestor paquetes  | uv                  | latest    | Rápido, lockfile determinista         |
| Tipado           | Pydantic v2         | >= 2.9    | Validación, serialización, settings   |
| Runtime types    | typing, typing_ext  | stdlib    | Type hints estrictos                  |

### 2.2 Modelos de IA (GPU Local)

| Modelo              | Función       | VRAM   | Repo / Fuente              |
|----------------------|---------------|--------|-----------------------------|
| YOLOv11m             | Detector      | 0.5 GB | ultralytics CDN             |
| YOLOv11n             | Detector lite | 0.3 GB | ultralytics CDN             |
| YOLOv11x             | Detector HD   | 1.0 GB | ultralytics CDN             |
| Jina CLIP v2         | Embeddings    | 3.5 GB | jinaai/jina-clip-v2         |
| Qwen2.5-VL 7B Q4    | Descriptor    | 5.5 GB | Qwen/Qwen2.5-VL-7B-Instruct|
| Moondream2 4-bit     | Descriptor    | 2.5 GB | moondream/moondream-2b-*    |

**Combinaciones válidas de VRAM:**

| Combinación                    | VRAM Total | GPU mínima        |
|--------------------------------|------------|--------------------|
| YOLOm + CLIP + Moondream      | 6.5 GB     | RTX 3060 (8GB)     |
| YOLOm + CLIP + Qwen Q4        | 9.5 GB     | RTX 4060 Ti (16GB) |
| YOLOx + CLIP + Qwen Q4        | 10.0 GB    | RTX 4060 Ti (16GB) |

### 2.3 Frameworks y Librerías

| Componente         | Librería                | Versión   | Uso                              |
|--------------------|-------------------------|-----------|----------------------------------|
| GUI                | PySide6                 | >= 6.8    | Interfaz de escritorio           |
| Computer Vision    | OpenCV (headless)       | >= 4.10   | Extracción de frames             |
| Detección          | ultralytics             | >= 8.3    | YOLO v11                         |
| Embeddings         | sentence-transformers   | >= 3.3    | Jina CLIP v2                     |
| VLM                | transformers            | >= 4.46   | Qwen2.5-VL / Moondream2         |
| Cuantización       | bitsandbytes            | >= 0.44   | 4-bit para Qwen                 |
| Aceleración        | accelerate              | >= 1.2    | device_map para VLMs             |
| Tensores           | torch                   | >= 2.5    | Backend GPU CUDA 12.x           |
| Tensores visión    | torchvision             | >= 0.20   | Transforms auxiliares            |
| Base de datos      | chromadb                | >= 0.5    | Vector store embebido            |
| Validación         | pydantic                | >= 2.9    | Modelos tipados                  |
| Settings           | pydantic-settings       | >= 2.6    | Config desde .env                |
| Imágenes           | Pillow                  | >= 11.0   | Conversión PIL                   |
| Arrays             | numpy                   | >= 1.26   | Manejo de frames                 |
| Logging            | loguru                  | >= 0.7    | Logger unificado                 |
| Qwen utils         | qwen-vl-utils           | >= 0.0.8  | Procesamiento Qwen VL            |

### 2.4 Infraestructura

| Componente        | Tecnología            | Nota                                |
|-------------------|-----------------------|-------------------------------------|
| Base de datos     | ChromaDB Embebido     | PersistentClient, sin Docker        |
| Almacenamiento    | Sistema de archivos   | ./data/chromadb/, ./output/         |
| Empaquetado       | PyInstaller           | --onedir, sin modelos AI            |
| Instalador        | Inno Setup            | Windows installer profesional       |
| Control versiones | Git                   | .gitignore para data/, output/      |

---

## 3. PRINCIPIOS DE INGENIERÍA

### 3.1 SOLID

| Principio | Aplicación en este proyecto |
|-----------|-----------------------------|
| **S** — Single Responsibility | Cada clase tiene UNA sola razón para cambiar. `Detector` solo detecta. `Embedder` solo genera embeddings. `Database` solo gestiona ChromaDB. |
| **O** — Open/Closed | Las clases base (`BaseDescriber`) están abiertas para extensión (nuevos VLMs) pero cerradas para modificación. Se añade `MistralDescriber` sin tocar `QwenDescriber`. |
| **L** — Liskov Substitution | Cualquier `BaseDescriber` se puede sustituir por `QwenDescriber` o `MoondreamDescriber` sin romper nada. El `ModelManager` no sabe cuál está usando. |
| **I** — Interface Segregation | Workers de UI no dependen de interfaces que no usan. `SearchWorker` no conoce la interfaz de indexación. |
| **D** — Dependency Inversion | `Indexer` depende de abstracciones (`BaseDetector`, `BaseEmbedder`, `BaseDescriber`), no de implementaciones concretas. Se inyectan por constructor. |

### 3.2 Patrones de Diseño

| Patrón | Dónde | Por qué |
|--------|-------|---------|
| **Singleton** (thread-safe) | `ModelManager` | Un solo set de modelos en VRAM |
| **Strategy** | `BaseDescriber` → `QwenDescriber` / `MoondreamDescriber` | Cambiar VLM sin tocar pipeline |
| **Observer** | Signals/Slots de PySide6 | Workers notifican a UI sin acoplamiento |
| **Factory Method** | `ModelRegistry.create_describer()` | Crear VLM correcto según config |
| **Template Method** | `BaseDescriber.describe()` | Flujo común, pasos específicos por subclase |
| **Repository** | `Database` | Abstrae ChromaDB, podría cambiar a FAISS |

### 3.3 Reglas de Código

| Regla | Detalle |
|-------|---------|
| Tipado estricto | Todos los parámetros y retornos tipados. Pydantic para modelos de datos. |
| No código duplicado | Funciones utilitarias en `core/utils.py`. Clases base para polimorfismo. |
| Idempotencia | `download_model()` no re-descarga si ya existe. `create_collection()` no falla si ya existe. |
| Inmutabilidad | Modelos Pydantic con `model_config = ConfigDict(frozen=True)` donde aplique. |
| Docstrings | Todas las clases y métodos públicos con docstring Google style. |
| Logger | `loguru` con configuración centralizada. Silencia ruido de librerías. |
| Errores | Excepciones tipadas (`ModelNotFoundError`, `GPUMemoryError`). Never bare `except:`. |

---

## 4. ARQUITECTURA DEL SISTEMA

### 4.1 Capas

```
┌─────────────────────────────────────────────────────┐
│  CAPA 1: PRESENTACIÓN (ui/)                         │
│  PySide6 Widgets + QSS Theme + Workers (QThread)    │
│  NO contiene lógica de negocio                      │
├─────────────────────────────────────────────────────┤
│  CAPA 2: NEGOCIO (core/)                            │
│  Indexer, Searcher, ModelManager                     │
│  Orquesta los componentes. Pura lógica.             │
├─────────────────────────────────────────────────────┤
│  CAPA 3: COMPONENTES IA (core/)                     │
│  Detector(YOLO), Embedder(CLIP), Describer(VLM)    │
│  Cada uno independiente. Polimórficos.              │
├─────────────────────────────────────────────────────┤
│  CAPA 4: DATOS (core/)                              │
│  Database(ChromaDB), FileManager                    │
│  Persistencia. Podría cambiar sin tocar arriba.     │
├─────────────────────────────────────────────────────┤
│  CAPA 5: INFRAESTRUCTURA (config/, logging/)        │
│  Settings(Pydantic), Logger(Loguru), GPU Utils      │
│  Cross-cutting concerns. Usado por todas las capas. │
└─────────────────────────────────────────────────────┘
```

### 4.2 Regla de Dependencia

Las dependencias solo fluyen HACIA ABAJO:

- `ui/` importa `core/` → PERMITIDO
- `core/` importa `config/` → PERMITIDO
- `core/` importa `ui/` → PROHIBIDO
- `config/` importa `core/` → PROHIBIDO

### 4.3 Flujo de Datos: Indexación

```
Video (.mp4)
    │
    ▼
FrameExtractor.extract(video_path, interval)
    │
    ▼
List[FrameData]  ─── cada frame ───┐
                                    ▼
                        Detector.detect(frame)
                                    │
                                    ▼
                        List[CropData]  ─── cada crop ───┐
                                                          │
                                    ┌─────────────────────┤
                                    ▼                     ▼
                        Embedder.embed_image()   Describer.describe()
                                    │                     │
                                    ▼                     ▼
                              List[float]              str
                                    │                     │
                                    └──────────┬──────────┘
                                               ▼
                                    Database.store(
                                        embedding=emb,
                                        metadata=crop_meta,
                                        description=desc
                                    )
```

### 4.4 Flujo de Datos: Búsqueda

```
Texto consulta ("mujer camisa amarilla")
    │
    ▼
Embedder.embed_text(query)
    │
    ▼
List[float]  (query embedding)
    │
    ▼
Database.search(query_embedding, n_results=30)
    │
    ▼
List[SearchResult]
    │
    ▼
UI: Galería de crops con scores, timestamps, descripciones
```

---

## 5. SISTEMA DE LOGGING

### 5.1 Diseño

Un logger centralizado basado en `loguru` que:

- Se configura UNA VEZ al iniciar la aplicación.
- Es importable desde cualquier módulo con `from core.logger import logger`.
- Silencia el ruido de librerías externas (transformers, torch, ultralytics, chromadb).
- Escribe a consola Y a archivo rotativo.
- Formatea con colores en consola, sin colores en archivo.
- Niveles configurables por entorno (.env).

### 5.2 Configuración de Silenciamiento

```python
# Librerías que generan ruido excesivo — se silencian a WARNING
SILENCED_LOGGERS: list[str] = [
    "transformers",
    "transformers.modeling_utils",
    "transformers.configuration_utils",
    "transformers.tokenization_utils_base",
    "torch",
    "torch.nn.modules",
    "ultralytics",
    "ultralytics.engine",
    "ultralytics.utils",
    "chromadb",
    "chromadb.config",
    "chromadb.segment",
    "sentence_transformers",
    "httpx",
    "httpcore",
    "PIL",
    "urllib3",
    "filelock",
    "huggingface_hub",
    "huggingface_hub.file_download",
    "accelerate",
    "bitsandbytes",
    "numba",
    "onnxruntime",
]
```

### 5.3 Clase LoggerSetup

```
LoggerSetup (core/logger.py)
├── setup_logger(level, log_dir, rotation, retention)
│   ├── Remueve handlers default de loguru
│   ├── Añade handler de consola (con color, formato corto)
│   ├── Añade handler de archivo (sin color, formato completo, rotación)
│   ├── Silencia loggers de librerías externas via logging.getLogger()
│   └── Retorna instancia de logger configurada
├── get_logger() → loguru.Logger
│   └── Retorna el logger singleton ya configurado
└── Constantes:
    ├── LOG_FORMAT_CONSOLE = "{time:HH:mm:ss} | {level.icon} | {module}:{line} | {message}"
    ├── LOG_FORMAT_FILE = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}"
    ├── LOG_ROTATION = "10 MB"
    └── LOG_RETENTION = "7 days"
```

### 5.4 Uso en cualquier módulo

```python
from core.logger import logger

class Detector:
    def detect(self, frame: FrameData) -> list[CropData]:
        logger.info(f"Detectando en frame {frame.index}")
        # ...
        logger.debug(f"Encontradas {len(crops)} detecciones")
        return crops
```

---

## 6. MODELOS PYDANTIC

### 6.1 Jerarquía de Modelos

Todos los modelos de datos son Pydantic v2 `BaseModel` con tipado estricto.
Se usan para transferir datos entre capas SIN acoplar los módulos.

```
models/
├── __init__.py           ← Re-exporta todo
├── settings.py           ← AppSettings (pydantic-settings, lee .env)
├── gpu.py                ← GPUInfo, VRAMStatus
├── models_ai.py          ← AIModelInfo, AIModelType, ModelStatus
├── video.py              ← VideoMetadata
├── frame.py              ← FrameData
├── detection.py          ← CropData, BoundingBox
├── embedding.py          ← EmbeddingResult
├── search.py             ← SearchQuery, SearchResult, SearchResponse
├── indexing.py           ← IndexProgress, IndexResult
└── database.py           ← CollectionStats
```

### 6.2 Detalle de cada Modelo

#### models/settings.py — Configuración Global

```python
class AppSettings(BaseSettings):
    """
    Configuración de toda la aplicación.
    Lee automáticamente desde .env con pydantic-settings.
    """
    # Rutas
    data_dir: Path = Path("./data")
    chromadb_dir: Path = Path("./data/chromadb")
    output_dir: Path = Path("./output")
    frames_dir: Path = Path("./output/frames")
    crops_dir: Path = Path("./output/crops")
    log_dir: Path = Path("./logs")

    # ChromaDB
    collection_name: str = "video_search"

    # Modelos por defecto
    default_detector: str = "yolo11m"
    default_embedder: str = "jina-clip-v2"
    default_describer: str = "qwen2.5-vl-7b-q4"

    # Procesamiento
    frame_interval: int = 2          # Segundos entre frames
    yolo_confidence: float = 0.45    # Confianza mínima YOLO
    min_crop_size: int = 30          # Píxeles mínimos de crop
    crop_padding: int = 10           # Padding alrededor del crop

    # VLM Prompts
    qwen_prompt: str = (
        "Describe esta imagen de cámara de seguridad en UNA oración detallada. "
        "Incluye: tipo de persona u objeto, género, ropa (colores exactos y tipo), "
        "accesorios, acción, dirección de movimiento. Solo la descripción, nada más."
    )
    moondream_prompt: str = (
        "Describe this security camera image in ONE detailed sentence. "
        "Include: person or object type, gender, clothing colors and type, "
        "accessories, action, direction of movement."
    )

    # UI
    web_host: str = "0.0.0.0"
    web_port: int = 7860

    # Logging
    log_level: str = "INFO"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
```

#### models/gpu.py — Información de GPU

```python
class GPUInfo(BaseModel):
    """Información estática de la GPU detectada."""
    available: bool
    device_name: str = "N/A"
    total_vram_gb: float = 0.0
    cuda_version: str = "N/A"
    driver_version: str = "N/A"

class VRAMStatus(BaseModel):
    """Estado dinámico de la VRAM (cambia en tiempo real)."""
    used_gb: float = 0.0
    free_gb: float = 0.0
    total_gb: float = 0.0

    @computed_field
    @property
    def usage_percent(self) -> float:
        if self.total_gb == 0:
            return 0.0
        return round((self.used_gb / self.total_gb) * 100, 1)
```

#### models/models_ai.py — Registro de Modelos AI

```python
class AIModelType(str, Enum):
    """Tipo de modelo AI."""
    DETECTOR = "detector"
    EMBEDDER = "embedder"
    DESCRIBER = "describer"

class ModelStatus(str, Enum):
    """Estado de un modelo."""
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"

class AIModelInfo(BaseModel):
    """Metadatos de un modelo AI disponible."""
    model_id: str                            # Identificador único: "yolo11m"
    display_name: str                        # Nombre legible: "YOLOv11 Medium"
    model_type: AIModelType                  # detector / embedder / describer
    repo_id: str                             # HuggingFace repo o CDN
    estimated_vram_gb: float                 # VRAM estimada en GPU
    estimated_size_gb: float                 # Tamaño descarga en disco
    description: str = ""                    # Descripción corta
    language: str = "multilingual"           # Idioma del modelo
    status: ModelStatus = ModelStatus.NOT_DOWNLOADED
    download_progress: float = 0.0           # 0.0 a 1.0

    model_config = ConfigDict(frozen=False)  # Status cambia dinámicamente
```

#### models/video.py — Metadata de Video

```python
class VideoMetadata(BaseModel):
    """Metadata extraída de un archivo de video."""
    file_path: Path
    file_name: str
    duration_seconds: float
    fps: float
    total_frames: int
    width: int
    height: int
    codec: str = "unknown"
    file_size_mb: float = 0.0

    @computed_field
    @property
    def duration_formatted(self) -> str:
        """Duración formateada como HH:MM:SS."""
        return str(timedelta(seconds=int(self.duration_seconds)))

    @computed_field
    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"
```

#### models/frame.py — Datos de Frame

```python
class FrameData(BaseModel):
    """Un frame extraído de un video, listo para procesamiento."""
    frame_index: int
    timestamp_seconds: float
    frame_path: Path
    video_source: Path
    width: int
    height: int

    # La imagen numpy NO va en el modelo Pydantic.
    # Se pasa por separado para evitar serialización de arrays grandes.

    model_config = ConfigDict(frozen=True)

    @computed_field
    @property
    def timestamp_formatted(self) -> str:
        return str(timedelta(seconds=int(self.timestamp_seconds)))
```

#### models/detection.py — Detecciones YOLO

```python
class BoundingBox(BaseModel):
    """Bounding box de una detección."""
    x1: int
    y1: int
    x2: int
    y2: int

    model_config = ConfigDict(frozen=True)

    @computed_field
    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @computed_field
    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @computed_field
    @property
    def center(self) -> tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)


class CropData(BaseModel):
    """Una detección recortada de un frame."""
    crop_id: str                    # Único: "{video_stem}__f{idx}__d{det}"
    class_name: str                 # Clase YOLO: "person", "car", etc.
    confidence: float               # Confianza YOLO: 0.0 a 1.0
    bbox: BoundingBox
    crop_path: Path
    frame_path: Path
    video_source: Path
    timestamp_seconds: float
    description: str = ""           # Se llena después por VLM

    model_config = ConfigDict(frozen=False)  # description se setea después

    @computed_field
    @property
    def timestamp_formatted(self) -> str:
        return str(timedelta(seconds=int(self.timestamp_seconds)))
```

#### models/search.py — Búsqueda

```python
class SearchQuery(BaseModel):
    """Consulta de búsqueda."""
    text: str
    n_results: int = 30
    min_score: float = 0.0
    class_filter: str | None = None
    video_filter: str | None = None

    model_config = ConfigDict(frozen=True)


class SearchResult(BaseModel):
    """Un resultado individual de búsqueda."""
    crop_id: str
    score: float                     # Similitud coseno: 0.0 a 1.0
    class_name: str
    confidence: float
    timestamp_seconds: float
    video_source: str
    frame_path: str
    crop_path: str
    description: str = ""
    bbox: str = ""                   # Serializado como string desde ChromaDB

    @computed_field
    @property
    def timestamp_formatted(self) -> str:
        return str(timedelta(seconds=int(self.timestamp_seconds)))


class SearchResponse(BaseModel):
    """Respuesta completa de una búsqueda."""
    query: str
    results: list[SearchResult]
    total_results: int
    elapsed_ms: int

    model_config = ConfigDict(frozen=True)
```

#### models/indexing.py — Progreso de Indexación

```python
class IndexStage(str, Enum):
    """Etapa actual del pipeline de indexación."""
    IDLE = "idle"
    EXTRACTING_FRAMES = "extracting_frames"
    DETECTING = "detecting"
    EMBEDDING = "embedding"
    DESCRIBING = "describing"
    STORING = "storing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class IndexProgress(BaseModel):
    """Estado actual del progreso de indexación."""
    stage: IndexStage = IndexStage.IDLE
    frames_total: int = 0
    frames_processed: int = 0
    detections_total: int = 0
    detections_processed: int = 0
    crops_stored: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0
    fps_processing: float = 0.0
    current_frame_path: str = ""
    error_message: str = ""


class IndexResult(BaseModel):
    """Resultado final de una indexación completa."""
    video_source: str
    total_frames: int
    total_detections: int
    total_stored: int
    elapsed_seconds: float
    fps_processing: float
    collection_total: int
```

#### models/database.py — Estadísticas

```python
class CollectionStats(BaseModel):
    """Estadísticas de la colección ChromaDB."""
    collection_name: str
    total_records: int
    indexed_videos: list[str] = []
    class_distribution: dict[str, int] = {}
    disk_usage_mb: float = 0.0
```

---

## 7. CORE BACKEND — DISEÑO DE CLASES

### 7.1 Diagrama de Clases

```
                    ┌─────────────────────┐
                    │    ModelManager      │ ← Singleton
                    │    (Orquestador)     │
                    ├─────────────────────┤
                    │ - _detector          │
                    │ - _embedder          │
                    │ - _describer         │
                    │ - _registry          │
                    ├─────────────────────┤
                    │ + load_detector()    │
                    │ + load_embedder()    │
                    │ + load_describer()   │
                    │ + unload_all()       │
                    │ + get_status()       │
                    └────────┬────────────┘
                             │ usa
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
   │ BaseDetector  │ │ BaseEmbedder │ │  BaseDescriber   │
   │  (ABC)        │ │  (ABC)       │ │  (ABC)           │
   ├──────────────┤ ├──────────────┤ ├──────────────────┤
   │ +detect()     │ │ +embed_img() │ │ +describe()      │
   │ +is_loaded()  │ │ +embed_txt() │ │ +is_loaded()     │
   │ +load()       │ │ +is_loaded() │ │ +load()          │
   │ +unload()     │ │ +load()      │ │ +unload()        │
   └──────┬───────┘ │ +unload()    │ │ +get_model_name()│
          │          └──────┬───────┘ └────┬─────────────┘
          ▼                 ▼              │
   ┌──────────────┐ ┌──────────────┐      ├──────────────┐
   │ YOLODetector │ │ CLIPEmbedder │      ▼              ▼
   │              │ │ (Jina CLIP)  │ ┌──────────┐ ┌────────────┐
   └──────────────┘ └──────────────┘ │  Qwen    │ │ Moondream  │
                                     │ Describer│ │ Describer  │
                                     └──────────┘ └────────────┘

   ┌──────────────┐     ┌──────────────┐
   │ FrameExtract │     │   Database    │
   │    or        │     │ (ChromaDB)   │
   ├──────────────┤     ├──────────────┤
   │ +extract()   │     │ +store()     │
   │ +get_meta()  │     │ +search()    │
   └──────────────┘     │ +get_stats() │
                        │ +reset()     │
   ┌──────────────┐     └──────────────┘
   │   Indexer     │
   │ (Pipeline)    │     ┌──────────────┐
   ├──────────────┤     │   Searcher   │
   │ +index()     │     ├──────────────┤
   │ +pause()     │     │ +search()    │
   │ +resume()    │     └──────────────┘
   │ +cancel()    │
   └──────────────┘

   ┌──────────────┐     ┌──────────────┐
   │  GPUUtils    │     │ModelRegistry │
   │ (Estático)   │     │ (Catálogo)   │
   ├──────────────┤     ├──────────────┤
   │ +detect()    │     │ +get_all()   │
   │ +get_vram()  │     │ +is_down()   │
   │ +clear()     │     │ +download()  │
   └──────────────┘     │ +create()    │
                        └──────────────┘
```

### 7.2 Clases Base Abstractas (ABC)

#### BaseDetector

```python
class BaseDetector(ABC):
    """Clase base para detectores de objetos."""

    @abstractmethod
    def load(self, device: str = "cuda") -> None:
        """Carga el modelo en GPU/CPU."""
        ...

    @abstractmethod
    def unload(self) -> None:
        """Libera el modelo de la memoria."""
        ...

    @abstractmethod
    def detect(self, frame: np.ndarray, confidence: float = 0.45) -> list[CropData]:
        """Detecta objetos en un frame y retorna crops."""
        ...

    @abstractmethod
    def is_loaded(self) -> bool:
        """Retorna True si el modelo está cargado."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo para logging."""
        ...
```

#### BaseEmbedder

```python
class BaseEmbedder(ABC):
    """Clase base para generadores de embeddings."""

    @abstractmethod
    def load(self, device: str = "cuda") -> None: ...

    @abstractmethod
    def unload(self) -> None: ...

    @abstractmethod
    def embed_image(self, image: np.ndarray) -> list[float]:
        """Genera embedding de una imagen (crop)."""
        ...

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Genera embedding de un texto (query)."""
        ...

    @abstractmethod
    def is_loaded(self) -> bool: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...
```

#### BaseDescriber

```python
class BaseDescriber(ABC):
    """Clase base para descriptores visuales (VLM)."""

    @abstractmethod
    def load(self, device: str = "cuda") -> None: ...

    @abstractmethod
    def unload(self) -> None: ...

    @abstractmethod
    def describe(self, image: np.ndarray) -> str:
        """Genera descripción en lenguaje natural de una imagen."""
        ...

    @abstractmethod
    def is_loaded(self) -> bool: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def language(self) -> str:
        """Idioma de las descripciones: 'es' o 'en'."""
        ...
```

### 7.3 ModelRegistry — Factory + Catálogo

```python
class ModelRegistry:
    """
    Catálogo de modelos disponibles + Factory para crear instancias.

    Responsabilidad ÚNICA: saber qué modelos existen, si están
    descargados, descargarlos, y crear la instancia correcta.
    """

    def get_available_models(self) -> list[AIModelInfo]:
        """Retorna todos los modelos registrados."""

    def get_models_by_type(self, model_type: AIModelType) -> list[AIModelInfo]:
        """Filtra por tipo: detector, embedder, describer."""

    def is_downloaded(self, model_id: str) -> bool:
        """Verifica idempotentemente si el modelo ya está en cache."""

    def download_model(self, model_id: str, on_progress: Callable) -> None:
        """Descarga modelo si no existe. Idempotente."""

    def create_detector(self, model_id: str) -> BaseDetector:
        """Factory: crea instancia correcta de detector."""

    def create_embedder(self, model_id: str) -> BaseEmbedder:
        """Factory: crea instancia correcta de embedder."""

    def create_describer(self, model_id: str) -> BaseDescriber:
        """Factory: crea instancia correcta de describer."""
```

### 7.4 ModelManager — Singleton Orquestador

```python
class ModelManager:
    """
    Singleton thread-safe que gestiona los modelos cargados en GPU.

    Responsabilidad ÚNICA: cargar, mantener y descargar modelos de VRAM.
    Delega la creación al ModelRegistry (no sabe cómo crear un YOLO).
    """
    _instance: ClassVar[ModelManager | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    @classmethod
    def get_instance(cls) -> ModelManager: ...

    @property
    def detector(self) -> BaseDetector | None: ...

    @property
    def embedder(self) -> BaseEmbedder | None: ...

    @property
    def describer(self) -> BaseDescriber | None: ...

    def load_detector(self, model_id: str) -> None: ...
    def load_embedder(self, model_id: str) -> None: ...
    def load_describer(self, model_id: str) -> None: ...
    def unload_all(self) -> None: ...

    def is_ready(self) -> bool:
        """True si detector + embedder están cargados (describer opcional)."""

    def get_status(self) -> dict[str, ModelStatus]: ...
```

### 7.5 Indexer — Pipeline Orquestador

```python
class Indexer:
    """
    Pipeline de indexación: Video → Frames → Detections → Embeddings → ChromaDB.

    Responsabilidad ÚNICA: orquestar el pipeline de indexación paso a paso.
    NO ejecuta detección ni embeddings directamente — los delega a los
    componentes que recibe por inyección de dependencias.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        database: Database,
        settings: AppSettings,
    ) -> None: ...

    def index_video(
        self,
        video_path: Path,
        on_progress: Callable[[IndexProgress], None] | None = None,
    ) -> IndexResult:
        """
        Ejecuta el pipeline completo. Thread-safe para uso en QThread.
        Emite progreso a través del callback on_progress.
        """

    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def cancel(self) -> None: ...

    @property
    def is_running(self) -> bool: ...

    @property
    def is_paused(self) -> bool: ...
```

### 7.6 Database — Repository Pattern

```python
class Database:
    """
    Wrapper sobre ChromaDB embebido.

    Responsabilidad ÚNICA: persistir y consultar embeddings + metadata.
    NO sabe nada de YOLO, CLIP, o modelos. Solo datos.
    """

    def __init__(self, chromadb_dir: Path, collection_name: str) -> None:
        """Crea/abre la base de datos embebida. Idempotente."""

    def store(
        self,
        crop_id: str,
        embedding: list[float],
        metadata: dict[str, Any],
        description: str = "",
    ) -> None:
        """Almacena un crop. Upsert idempotente (si ya existe, actualiza)."""

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 30,
    ) -> list[SearchResult]:
        """Busca los crops más similares al embedding de consulta."""

    def get_stats(self) -> CollectionStats: ...
    def get_indexed_videos(self) -> list[str]: ...
    def reset(self) -> None: ...

    @property
    def count(self) -> int: ...
```

---

## 8. UI FRONTEND — DISEÑO DE CLASES

### 8.1 Diagrama

```
MainWindow (QMainWindow)
├── Sidebar (QWidget)
│   ├── Botón Modelos → muestra ModelPanel
│   ├── Botón Indexar → muestra IndexingPanel
│   ├── Botón Buscar → muestra SearchPanel
│   └── Botón Stats  → muestra StatsPanel
├── QStackedWidget (contenido central)
│   ├── ModelPanel (QWidget)
│   │   ├── ModelCardWidget × N (radio + status + progress)
│   │   ├── YOLOConfidenceSlider
│   │   ├── VRAMBar
│   │   └── Botones [Descargar] [Cargar GPU]
│   ├── IndexingPanel (QWidget)
│   │   ├── VideoSelector (drag&drop + browse)
│   │   ├── IntervalSlider
│   │   ├── ProgressBars × 4
│   │   ├── StatsCounters
│   │   └── Botones [Iniciar] [Pausar] [Cancelar]
│   ├── SearchPanel (QWidget)
│   │   ├── SearchBar (QLineEdit)
│   │   ├── ResultGallery (QScrollArea + grid de ResultCard)
│   │   └── ResultDetail (crop + frame + meta + botón video)
│   └── StatsPanel (QWidget)
│       ├── CollectionInfo
│       ├── ClassDistributionChart
│       └── Botón [Limpiar]
└── StatusBar (QStatusBar)
    ├── GPU indicator
    ├── VRAM mini bar
    └── ChromaDB status
```

### 8.2 Workers (QThread)

Toda operación pesada corre en un QThread para no bloquear la UI.
Comunicación por signals/slots (patrón Observer de Qt).

```python
class ModelDownloadWorker(QThread):
    """Descarga modelos en background."""
    progress = Signal(str, float)      # (model_id, 0.0-1.0)
    finished = Signal()
    error = Signal(str)


class ModelLoadWorker(QThread):
    """Carga modelos en GPU en background."""
    model_loaded = Signal(str)         # model_id
    all_loaded = Signal()
    error = Signal(str)


class IndexWorker(QThread):
    """Ejecuta el pipeline de indexación."""
    progress = Signal(IndexProgress)   # Estado completo
    finished = Signal(IndexResult)     # Resultado final
    error = Signal(str)


class SearchWorker(QThread):
    """Ejecuta búsqueda."""
    results = Signal(SearchResponse)   # Resultados
    error = Signal(str)
```

### 8.3 Tema QSS

```python
class Theme:
    """Paleta de colores y QSS centralizado."""

    # Colores base (tema oscuro estilo NVR)
    BG_PRIMARY   = "#0a0e17"     # Fondo principal
    BG_SECONDARY = "#0f1420"     # Paneles, cards
    BG_TERTIARY  = "#161d2e"     # Hover, inputs
    BORDER       = "#243049"     # Bordes normales
    BORDER_FOCUS = "#3b82f6"     # Bordes activos

    # Acentos
    ACCENT       = "#3b82f6"     # Azul primario
    ACCENT_HOVER = "#2563eb"     # Azul hover
    SUCCESS      = "#10b981"     # Verde
    WARNING      = "#f59e0b"     # Amarillo
    ERROR        = "#ef4444"     # Rojo
    INFO         = "#06b6d4"     # Cyan

    # Texto
    TEXT_PRIMARY   = "#e4eaf4"   # Texto principal
    TEXT_SECONDARY = "#7b8ba8"   # Texto secundario
    TEXT_MUTED     = "#4a5568"   # Texto muy tenue

    @staticmethod
    def get_stylesheet() -> str:
        """Retorna el QSS completo de toda la aplicación."""
```

---

## 9. ESTRUCTURA DE CARPETAS

```
video_search_desktop/
│
├── main.py                          ← Punto de entrada
├── pyproject.toml                   ← Dependencias + metadata
├── uv.lock                          ← Lockfile generado por uv
├── .env                             ← Configuración del usuario
├── .env.example                     ← Plantilla de .env
├── .gitignore                       ← Excluye data/, output/, logs/, *.pt
├── README.md                        ← Documentación del proyecto
│
├── core/                            ← BACKEND (sin dependencia a UI)
│   ├── __init__.py
│   ├── logger.py                    ← Logger centralizado (loguru)
│   ├── gpu_utils.py                 ← Detección GPU, VRAM
│   ├── model_registry.py            ← Catálogo + Factory de modelos
│   ├── model_manager.py             ← Singleton: modelos en GPU
│   ├── frame_extractor.py           ← Video → frames (OpenCV)
│   ├── database.py                  ← ChromaDB embebido wrapper
│   ├── indexer.py                   ← Pipeline: video → ChromaDB
│   ├── searcher.py                  ← Búsqueda por texto
│   ├── detectors/                   ← Implementaciones de detectores
│   │   ├── __init__.py
│   │   ├── base.py                  ← BaseDetector (ABC)
│   │   └── yolo_detector.py         ← YOLODetector
│   ├── embedders/                   ← Implementaciones de embedders
│   │   ├── __init__.py
│   │   ├── base.py                  ← BaseEmbedder (ABC)
│   │   └── clip_embedder.py         ← CLIPEmbedder (Jina)
│   └── describers/                  ← Implementaciones de VLMs
│       ├── __init__.py
│       ├── base.py                  ← BaseDescriber (ABC)
│       ├── qwen_describer.py        ← QwenDescriber
│       └── moondream_describer.py   ← MoondreamDescriber
│
├── models/                          ← MODELOS PYDANTIC (datos tipados)
│   ├── __init__.py                  ← Re-exporta todos los modelos
│   ├── settings.py                  ← AppSettings (pydantic-settings)
│   ├── gpu.py                       ← GPUInfo, VRAMStatus
│   ├── models_ai.py                 ← AIModelInfo, AIModelType, ModelStatus
│   ├── video.py                     ← VideoMetadata
│   ├── frame.py                     ← FrameData
│   ├── detection.py                 ← CropData, BoundingBox
│   ├── search.py                    ← SearchQuery, SearchResult, SearchResponse
│   ├── indexing.py                  ← IndexProgress, IndexResult, IndexStage
│   └── database.py                  ← CollectionStats
│
├── ui/                              ← FRONTEND (PySide6)
│   ├── __init__.py
│   ├── main_window.py               ← Ventana principal + sidebar
│   ├── theme.py                     ← QSS + paleta de colores
│   ├── widgets/                     ← Componentes visuales
│   │   ├── __init__.py
│   │   ├── sidebar.py               ← Barra de navegación lateral
│   │   ├── video_selector.py        ← Drag&drop + browse video
│   │   ├── model_panel.py           ← Panel completo de modelos
│   │   ├── model_card.py            ← Card individual de un modelo
│   │   ├── indexing_panel.py        ← Panel de indexación
│   │   ├── search_panel.py          ← Panel de búsqueda
│   │   ├── result_gallery.py        ← Grid de resultados
│   │   ├── result_card.py           ← Card individual de resultado
│   │   ├── result_detail.py         ← Vista detalle de resultado
│   │   ├── stats_panel.py           ← Panel de estadísticas
│   │   ├── gpu_monitor.py           ← Widget barra VRAM
│   │   └── progress_group.py        ← Grupo de barras de progreso
│   └── workers/                     ← QThreads
│       ├── __init__.py
│       ├── model_download_worker.py
│       ├── model_load_worker.py
│       ├── index_worker.py
│       └── search_worker.py
│
├── assets/                          ← Recursos estáticos
│   ├── icon.ico
│   ├── icon.png
│   └── splash.png
│
├── scripts/                         ← Scripts de build
│   ├── build.py                     ← PyInstaller config
│   └── installer.iss                ← Inno Setup script
│
├── data/                            ← GENERADO en runtime (gitignored)
│   └── chromadb/                    ← Base de datos embebida
│
├── output/                          ← GENERADO en runtime (gitignored)
│   ├── frames/                      ← Frames extraídos por video
│   └── crops/                       ← Detecciones recortadas
│
└── logs/                            ← GENERADO en runtime (gitignored)
    └── video_search.log             ← Log rotativo
```

---

## 10. DEPENDENCIAS — pyproject.toml

```toml
[project]
name = "video-search-desktop"
version = "1.0.0"
description = "Búsqueda visual en videos de seguridad por lenguaje natural"
requires-python = ">=3.12"
license = { text = "Proprietary" }
authors = [
    { name = "Tu Nombre", email = "tu@email.com" },
]

dependencies = [
    # ── GUI ──
    "PySide6>=6.8",

    # ── Computer Vision ──
    "opencv-python-headless>=4.10",
    "ultralytics>=8.3",
    "Pillow>=11.0",
    "numpy>=1.26",

    # ── AI / ML ──
    "torch>=2.5",
    "torchvision>=0.20",
    "sentence-transformers>=3.3",
    "transformers>=4.46",
    "bitsandbytes>=0.44",
    "accelerate>=1.2",
    "qwen-vl-utils>=0.0.8",

    # ── Database ──
    "chromadb>=0.5",

    # ── Data Validation ──
    "pydantic>=2.9",
    "pydantic-settings>=2.6",

    # ── Logging ──
    "loguru>=0.7",

    # ── Config ──
    "python-dotenv>=1.0",
]

[project.scripts]
video-search = "main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["core", "models", "ui"]
```

---

## 11. CONFIGURACIÓN — .env

```env
# ═══════════════════════════════════════════
#  VIDEO SEARCH DESKTOP — Configuración
# ═══════════════════════════════════════════

# ── Rutas ──
DATA_DIR=./data
CHROMADB_DIR=./data/chromadb
OUTPUT_DIR=./output
FRAMES_DIR=./output/frames
CROPS_DIR=./output/crops
LOG_DIR=./logs

# ── ChromaDB ──
COLLECTION_NAME=video_search

# ── Modelos por defecto ──
DEFAULT_DETECTOR=yolo11m
DEFAULT_EMBEDDER=jina-clip-v2
DEFAULT_DESCRIBER=qwen2.5-vl-7b-q4

# ── Procesamiento ──
FRAME_INTERVAL=2
YOLO_CONFIDENCE=0.45
MIN_CROP_SIZE=30
CROP_PADDING=10

# ── Logging ──
LOG_LEVEL=INFO
LOG_ROTATION=10 MB
LOG_RETENTION=7 days
```

---

## 12. PLAN DE FASES DETALLADO

### FASE 0 — Documentación e Infraestructura (ESTE DOCUMENTO)

```
Estado: ← ESTAMOS AQUÍ
Objetivo: Documentar TODO. Crear estructura. Verificar que compila.

Entregables:
├── [x] Este documento completo
├── [ ] Estructura de carpetas creada
├── [ ] pyproject.toml configurado
├── [ ] .env + .env.example
├── [ ] .gitignore
├── [ ] models/ — Todos los modelos Pydantic implementados
├── [ ] core/logger.py — Logger configurado
├── [ ] config/ (ahora models/settings.py) — Settings Pydantic
├── [ ] Todos los __init__.py con re-exports
├── [ ] Clases base ABC creadas (sin implementación)
├── [ ] `uv sync` instala todo sin errores
├── [ ] `python -c "from models import *"` funciona
├── [ ] `python -c "from core.logger import logger"` funciona
├── [ ] `python -c "from models.settings import AppSettings; s = AppSettings()"` funciona

Criterio para avanzar a Fase 1:
  Todos los imports funcionan. Todos los modelos Pydantic validan.
  Logger escribe a consola y archivo. Settings lee .env correctamente.
```

### FASE 1 — Core Backend: GPU + Modelos (sin pipeline)

```
Objetivo: ModelRegistry + ModelManager funcionan. Se pueden
          descargar modelos y cargar en GPU desde Python puro.

Archivos:
├── core/gpu_utils.py — Implementado completo
├── core/model_registry.py — Catálogo + descarga + factory
├── core/model_manager.py — Singleton + carga en GPU
├── core/detectors/yolo_detector.py — YOLODetector completo
├── core/embedders/clip_embedder.py — CLIPEmbedder completo
├── core/describers/qwen_describer.py — QwenDescriber completo
├── core/describers/moondream_describer.py — MoondreamDescriber completo
└── core/database.py — ChromaDB embebido wrapper

Verificación:
  python -c "
  from core.model_manager import ModelManager
  mm = ModelManager.get_instance()
  mm.load_detector('yolo11m')
  mm.load_embedder('jina-clip-v2')
  print(mm.get_status())
  mm.unload_all()
  "

  python -c "
  from core.database import Database
  db = Database()
  print(db.count)
  "

Criterio: Modelos cargan en GPU. ChromaDB crea colección.
```

### FASE 2 — Core Backend: Pipeline de Indexación

```
Objetivo: Indexar un video MP4 completo desde Python puro.
          Sin GUI. Solo terminal.

Archivos:
├── core/frame_extractor.py — Implementado
├── core/indexer.py — Pipeline completo con callbacks
└── core/searcher.py — Búsqueda funcional

Verificación:
  python -c "
  from core.model_manager import ModelManager
  from core.database import Database
  from core.indexer import Indexer
  from core.searcher import Searcher
  from models.settings import AppSettings

  settings = AppSettings()
  mm = ModelManager.get_instance()
  mm.load_detector('yolo11m')
  mm.load_embedder('jina-clip-v2')
  mm.load_describer('qwen2.5-vl-7b-q4')

  db = Database(settings.chromadb_dir, settings.collection_name)
  indexer = Indexer(mm, db, settings)
  result = indexer.index_video(Path('test_video.mp4'))
  print(result)

  searcher = Searcher(mm, db)
  response = searcher.search('persona con camisa roja')
  print(response)
  "

Criterio: Video se indexa. Búsqueda retorna resultados con scores.
          ChromaDB tiene datos persistidos.
```

### FASE 3 — UI Base: Ventana + Tema + Navegación

```
Objetivo: Aplicación se abre con ventana estilo NVR.
          Sidebar funcional. 4 paneles placeholder.

Archivos:
├── main.py — Punto de entrada con splash
├── ui/theme.py — QSS completo
├── ui/main_window.py — Ventana principal
├── ui/widgets/sidebar.py — Navegación lateral
├── ui/widgets/gpu_monitor.py — Widget VRAM
└── Placeholders para los 4 paneles

Verificación:
  python main.py
  → Se abre ventana oscura
  → Sidebar navega entre 4 tabs
  → Status bar muestra GPU info
  → VRAM bar se actualiza

Criterio: App se abre, se ve profesional, sidebar navega.
```

### FASE 4 — UI: Panel de Modelos

```
Objetivo: Seleccionar, descargar y cargar modelos desde la interfaz.

Archivos:
├── ui/widgets/model_panel.py
├── ui/widgets/model_card.py
├── ui/workers/model_download_worker.py
└── ui/workers/model_load_worker.py

Verificación:
  → Abro app
  → Tab "Modelos" muestra cards con estado
  → Click "Descargar" → barra progreso → ✓ Descargado
  → Click "Cargar en GPU" → progreso → VRAM sube → ✓ Cargado
  → Selecciono Moondream en vez de Qwen → carga correcta

Criterio: Puedo descargar y cargar cualquier combinación desde la UI.
```

### FASE 5 — UI: Panel de Indexación

```
Objetivo: Cargar video y ver indexación con progreso en tiempo real.

Archivos:
├── ui/widgets/video_selector.py
├── ui/widgets/indexing_panel.py
├── ui/widgets/progress_group.py
└── ui/workers/index_worker.py

Verificación:
  → Arrastro video → se muestra metadata
  → Click "Iniciar" → 4 barras avanzan
  → Counters actualizan en vivo
  → Pausar funciona → Reanudar funciona
  → Cancelar funciona
  → Al terminar: resumen con totales

Criterio: Indexo video completo desde UI. ChromaDB tiene datos.
```

### FASE 6 — UI: Panel de Búsqueda

```
Objetivo: Buscar por texto y ver galería de resultados visuales.

Archivos:
├── ui/widgets/search_panel.py
├── ui/widgets/result_gallery.py
├── ui/widgets/result_card.py
├── ui/widgets/result_detail.py
└── ui/workers/search_worker.py

Verificación:
  → Escribo "mujer camisa amarilla" → Enter
  → Galería muestra crops ordenados por score
  → Cada card: imagen, score, clase, timestamp
  → Click en card → detalle con frame completo + bbox
  → Botón "Abrir video" → salta al segundo correcto

Criterio: Búsqueda end-to-end funcional con resultados visuales.
```

### FASE 7 — UI: Estadísticas + Pulido

```
Objetivo: Panel de stats. Splash screen. Manejo de errores.

Archivos:
├── ui/widgets/stats_panel.py
├── assets/icon.ico, icon.png, splash.png
└── Mejoras generales de UX

Verificación:
  → Tab Stats muestra registros, videos, distribución
  → Splash screen aparece al iniciar
  → Errores muestran diálogos amigables (no crashes)
  → Tooltips en todos los controles

Criterio: App pulida, lista para demo con cliente.
```

### FASE 8 — Empaquetado y Entrega

```
Objetivo: Generar ejecutable y/o instalador para Windows.

Archivos:
├── scripts/build.py
├── scripts/installer.iss
└── README.md completo

Verificación:
  → PyInstaller genera carpeta dist/
  → Ejecutar dist/video_search/main.exe funciona
  → Instalador crea acceso directo, menú inicio
  → Desinstalador funciona
  → En PC limpia: instalar → descargar modelos → indexar → buscar ✓

Criterio: Producto entregable al cliente.
```

---

## 13. CRITERIOS DE ACEPTACIÓN POR FASE

| Fase | Test de Compilación | Test Funcional |
|------|---------------------|----------------|
| 0 | Todos los imports funcionan | Pydantic valida, logger escribe, settings lee .env |
| 1 | core/ importa sin errores | GPU detectada, modelos cargan/descargan en VRAM |
| 2 | Pipeline importa | Video se indexa, búsqueda retorna resultados |
| 3 | ui/ importa, app se abre | Sidebar navega, tema aplicado, status bar funciona |
| 4 | Model panel funciona | Descarga + carga modelos desde UI |
| 5 | Index panel funciona | Indexar video con progreso visual |
| 6 | Search panel funciona | Búsqueda end-to-end con galería |
| 7 | Stats + pulido | Panel stats, splash, errores amigables |
| 8 | .exe funciona | Instalador en PC limpia |

**REGLA: No se pasa a Fase N+1 hasta que todos los tests de Fase N pasen.**

---

## 14. EMPAQUETADO Y ENTREGA

### 14.1 Para Cliente Técnico

```
Entrega: Carpeta zip con código fuente
Requisitos: Python 3.12+, NVIDIA GPU 8GB+, CUDA Toolkit 12.x
Instalación:
  1. pip install uv
  2. uv sync
  3. python main.py
Peso: ~50 KB (código) + dependencias se descargan con uv sync
```

### 14.2 Para Cliente Final (Recomendado)

```
Entrega: VideoSearch_Setup_v1.0.exe (instalador Inno Setup)
Contenido:
  ├── Python 3.12 embebido (~40 MB)
  ├── Todas las dependencias (~400 MB)
  ├── ChromaDB embebido (incluido)
  ├── Modelos AI: se descargan al primer uso (~5-8 GB)
  ├── Acceso directo en escritorio
  ├── Entrada en menú inicio
  └── Desinstalador
Requisitos: Windows 10/11 64-bit, NVIDIA GPU 8GB+ VRAM, Internet (primer uso)
Peso instalador: ~500 MB
Peso total instalado: ~6-9 GB (con modelos)
```

### 14.3 Archivos que NO se versionan (en .gitignore)

```gitignore
# Runtime data
data/
output/
logs/

# Models
*.pt
models_cache/

# Python
__pycache__/
*.pyc
.venv/

# IDE
.vscode/
.idea/

# Build
dist/
build/
*.spec

# OS
.DS_Store
Thumbs.db

# Env (tiene secretos potenciales)
.env
```

---

## 15. FASE 9 — ARQUITECTURA EMPRESARIAL EVENT-DRIVEN (v2.0)

> Esta fase agrega los Tier 1 y Tier 2 del roadmap NVR profesional,
> mas las interfaces (ABCs) listas para implementar Tier 3.

### 15.1 Vision

Pasar de "app local de busqueda en videos" a **plataforma de seguridad
con IA tipo NVR profesional**: visor en vivo con bounding boxes,
historial de eventos, alertas push (Telegram), anti-tamper, exportacion
forense con cadena de custodia, e interfaces extensibles para
reconocimiento facial / OCR / reportes PDF.

### 15.2 Patron de diseno central: Event-Driven

Toda comunicacion entre subsistemas pasa por un **EventBus singleton
Qt-based**. Publishers no conocen subscribers; suscribers no conocen
publishers. Esto desacopla completamente:

```
       ┌───────────────────────────────┐
       │       EventBus singleton      │
       │   (Observer pattern hub)      │
       │   Qt::QueuedConnection        │
       │   thread-safe cross-thread    │
       └─────────┬─────────────────────┘
                 │ publish(SecurityEvent)
   ┌─────────────┼──────────────────┐
   │             │                  │
PUBLISHERS  SUBSCRIBERS-CORE    SUBSCRIBERS-UI
   │             │                  │
Indexer       AlertManager     EventHistoryPanel
StreamCapture (Mediator)       _CameraCard.alert_badge
TamperManager     │
                  │ delega a:
                  ▼
             ┌────────────┐
             │BaseNotifier│ ABC
             ├────────────┤
             │ Telegram   │ implementacion concreta
             │ (futuro:   │
             │  Email,    │
             │  Push,     │
             │  Webhook)  │
             └────────────┘
```

### 15.3 Modelos nuevos

#### models/event.py — SecurityEvent

```python
class EventType(str, Enum):
    DETECTION = "detection"
    CAMERA_CONNECTED = "camera_connected"
    CAMERA_DISCONNECTED = "camera_disconnected"
    TAMPER = "tamper"
    NOTIFICATION_SENT = "notification_sent"
    SYSTEM = "system"

class EventSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class SecurityEvent(BaseModel):
    event_id: str = Field(default_factory=uuid)
    event_type: EventType
    severity: EventSeverity = EventSeverity.INFO
    camera_id: str
    timestamp: datetime
    title: str
    message: str = ""
    thumbnail_path: Path | None = None
    payload: dict[str, Any] = {}  # type-specific data
```

### 15.4 Modulos nuevos en core/

#### core/events/event_bus.py — Singleton

```python
class EventBus(QObject):
    event_published = Signal(object)  # SecurityEvent

    @classmethod
    def get_instance(cls) -> "EventBus": ...
    def publish(self, event: SecurityEvent) -> None: ...
    def subscribe(self, callback) -> None: ...
    def unsubscribe(self, callback) -> None: ...
```

Thread-safe. Cualquier hilo publica; los subscribers reciben en su
propio hilo via QueuedConnection automatica.

#### core/alerts/ — Notificadores polimorficos

| Archivo | Responsabilidad |
|---|---|
| `base_notifier.py` | ABC con template method `handle()` que filtra por severidad y delega a `send()` |
| `telegram_notifier.py` | Implementa `send()` con HTTP POST a Bot API + foto opcional |
| `alert_manager.py` | Singleton suscrito al EventBus que distribuye eventos a notificadores en threads aparte |

Para agregar un canal nuevo:
```python
class EmailNotifier(BaseNotifier):
    def __init__(self): super().__init__("Email", min_severity=EventSeverity.WARNING)
    def send(self, event): ...  # tu integracion SMTP

AlertManager.get_instance().register(EmailNotifier())
```

#### core/tamper/ — Anti-tamper polimorfico

| Archivo | Responsabilidad |
|---|---|
| `base_tamper_detector.py` | ABC `analyze(frame) -> TamperResult` |
| `black_screen_detector.py` | Brillo medio + varianza baja → lente cubierta |
| `scene_change_detector.py` | Distancia Bhattacharyya entre histogramas → camara movida |
| `tamper_manager.py` | Una instancia por camara; itera detectores con cooldown |

Indexer crea un TamperManager por camera_id la primera vez que ve un
frame de esa camara, con detectores BlackScreen + SceneChange por defecto.

#### core/export/ — Exportadores polimorficos

| Archivo | Responsabilidad |
|---|---|
| `base_exporter.py` | ABC `export(events, output_path) -> Path` |
| `evidence_exporter.py` | ZIP forense + manifest.json + chain_of_custody.txt con SHA256 por archivo (validez legal) |
| `pdf_reporter.py` | STUB: cuando se active reportlab, genera PDF ejecutivo |

Estructura del ZIP forense:
```
evidence_2026-05-03.zip
├── manifest.json              ← metadata global + lista eventos
├── chain_of_custody.txt       ← SHA256 de cada archivo + fecha
└── events/
    ├── 0001_a1b2c3d4/
    │   ├── event.json         ← metadata del evento
    │   └── crop_xyz.jpg       ← thumbnail original
    └── 0002_e5f6g7h8/
        ├── event.json
        └── crop_abc.jpg
```

#### core/recognition/ — STUB Tier 3

```python
class BaseRecognizer(ABC):
    def load(self): ...
    def unload(self): ...
    def recognize(self, image_bgr) -> list[RecognitionResult]: ...

class FaceRecognizer(BaseRecognizer):
    """Stub. Activar con: uv add insightface onnxruntime-gpu"""
```

#### core/ocr/ — STUB Tier 3

```python
class BaseOCR(ABC): ...

class PlateOCR(BaseOCR):
    """Stub con regex de placas LATAM: ABC-123, AB1234, 123-ABC"""
    PLATE_PATTERNS: list[re.Pattern]
    @classmethod
    def is_valid_plate(cls, text: str) -> bool: ...
```

### 15.5 Modulos nuevos en ui/widgets/

| Archivo | Responsabilidad |
|---|---|
| `alert_badge.py` | Badge parpadeante reutilizable con `flash(text, color, duration_ms)` y QTimer |
| `event_history_panel.py` | `_EventRow` (fila clickeable con thumbnail) + `_EventDetailDialog` + `EventHistoryPanel` (suscriptor del bus, max 50 eventos) |
| `search_filter_bar.py` | `QComboBox` camaras + checkboxes clases + `QDateEdit` rango + `build_query()` que retorna `SearchQuery` tipado |

### 15.6 Cambios en modulos existentes

#### core/indexer.py
- `process_single_frame()` ahora retorna `list[CropData]` (en lugar de int)
  para que el StreamWorker pueda dibujar bboxes con la info completa
- Llama a `_analyze_tamper()` antes de detectar (CPU-only, no requiere GPU)
- Publica `SecurityEvent.DETECTION` al EventBus al final si hay crops
- Mantiene `dict[camera_id, TamperManager]` con creacion lazy

#### core/stream_capture.py
- `capture_loop()` ahora acepta `on_preview` callback
- Lee frames continuamente (~30fps), emite preview cada 100ms (10fps)
- Procesa AI solo cada `interval_seconds` para no quemar GPU
- Publica `CAMERA_CONNECTED` / `CAMERA_DISCONNECTED` al EventBus

#### core/database.py
- `search()` acepta `class_filter`, `camera_filter`, `date_from`, `date_to`
- Construye `where` clause de ChromaDB con `$and / $in / $gte / $lte`
- Filtros nativos en DB (rapido) en lugar de filtrado en Python (lento)

#### core/searcher.py
- `search_from_query(query: SearchQuery)` lee filtros del modelo tipado
- Convierte `datetime` a timestamp UNIX para la DB

#### models/search.py
```python
class SearchQuery(BaseModel):
    text: str
    n_results: int = 30
    min_score: float = 0.0
    class_filter: list[str] | None = None      # NUEVO: lista, no string
    camera_filter: list[str] | None = None     # NUEVO
    video_filter: str | None = None            # mantenido para compat
    date_from: datetime | None = None          # NUEVO
    date_to: datetime | None = None            # NUEVO
```

#### ui/widgets/camera_panel.py
- `_CameraCard` agrega `AlertBadge` en la fila 1
- Se suscribe al EventBus en `__init__`, filtra por su `camera_id`,
  y ejecuta `alert_badge.flash()` segun severidad/tipo del evento
- Visor en vivo con `update_preview(frame_bgr)` convirtiendo BGR→QPixmap

#### ui/workers/stream_worker.py
- Nuevo `Signal preview_frame(camera_id, ndarray)` para video en vivo
- Cachea `_latest_crops` y dibuja bboxes con `cv2.rectangle` antes de
  emitir cada preview (color por clase)

#### ui/widgets/sidebar.py
- 6 secciones (antes 4): Modelos, Indexar, Buscar, Camaras, **Eventos**, Estadisticas

#### main.py
- Singleton `EventBus.get_instance()` y `AlertManager.get_instance()`
- `_setup_notifiers()` registra `TelegramNotifier()` (auto-disabled sin env)
- `SearchPanel(database=self._db)` para que el filter bar tenga acceso a
  las camaras existentes en la DB

### 15.7 Cumplimiento SOLID — verificado

```python
# Test ejecutado en sesion:
assert issubclass(TelegramNotifier, BaseNotifier)
assert issubclass(BlackScreenDetector, BaseTamperDetector)
assert issubclass(SceneChangeDetector, BaseTamperDetector)
assert issubclass(EvidenceExporter, BaseExporter)
assert issubclass(PdfReporter, BaseExporter)
assert issubclass(FaceRecognizer, BaseRecognizer)
assert issubclass(PlateOCR, BaseOCR)
# Polimorfismo OK: todas las subclases respetan ABCs
```

| Principio | Como se aplica |
|---|---|
| **S**ingle Responsibility | 1 archivo = 1 clase = 1 funcion. EventBus solo enruta, AlertManager solo distribuye, BaseNotifier solo encapsula filtro+envio, etc. |
| **O**pen/Closed | Agregar nuevo notifier/detector/exporter NO toca a su manager. Solo se hereda la ABC y se registra. |
| **L**iskov | Subclases pueden reemplazar a su ABC sin romper el sistema. AlertManager itera sobre `BaseNotifier`, no sobre `TelegramNotifier`. |
| **I**nterface Segregation | ABCs minimas: BaseNotifier solo tiene 1 metodo abstracto (`send`). BaseExporter idem (`export`). |
| **D**ependency Inversion | Indexer, AlertManager, TamperManager dependen de ABCs (interfaces), no de implementaciones concretas. |

### 15.8 Variables de entorno nuevas (.env)

```env
# HuggingFace para descargas mas rapidas (opcional)
HF_TOKEN=hf_xxxxxxxxxx

# Telegram para alertas push (opcional, deshabilitado si vacio)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhi...
TELEGRAM_CHAT_ID=987654321

# Silenciar warnings cosmeticos h264 SEI de camaras Tapo
# (auto-set por settings.setup_model_environment)
OPENCV_LOG_LEVEL=ERROR
OPENCV_FFMPEG_LOGLEVEL=16
```

### 15.9 Roadmap de Tier 3 (interfaces listas)

Para activar **reconocimiento facial**:
```bash
uv add insightface onnxruntime-gpu
```
Luego implementar `FaceRecognizer.load()` y `recognize()` (~50 lineas)
usando `insightface.app.FaceAnalysis(name="buffalo_l")`.

Para activar **OCR de placas**:
```bash
uv add paddleocr paddlepaddle-gpu
```
Luego implementar `PlateOCR.recognize()` con `PaddleOCR.ocr(...)` y
filtrar resultados con `PlateOCR.is_valid_plate()`.

Para activar **reportes PDF**:
```bash
uv add reportlab
```
Luego implementar `PdfReporter.export()` con `reportlab.platypus`
(SimpleDocTemplate, Table, Image).

### 15.10 Roadmap de Tier 4 (futuro)

- Deteccion de comportamiento (loitering, peleas, caidas con YOLO-Pose)
- Heatmap acumulativo de actividad por zona/hora
- Re-identificacion cross-camera (OSNet) — la misma persona en cam01 y cam03
- Multi-tenant + autenticacion (para SaaS)
- ROI zones — polígonos dibujables sobre el frame
- Grid 1/4/9 cámaras simultáneas en pantalla completa
- Anti-tamper avanzado: BlurDetector (lente desenfocada deliberadamente)
