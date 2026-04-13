# Video Search Desktop

Aplicacion de escritorio Windows para **buscar personas y objetos en videos de seguridad por lenguaje natural**.

Escribes "mujer con camisa amarilla" y el sistema te muestra las imagenes exactas con timestamps.

**100% local.** Ningun dato sale de tu PC. Los modelos de IA corren en tu GPU.

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

### 1. Clonar el repositorio

```bash
git clone https://github.com/ghmedinac123/video_search_desktop.git
cd video_search_desktop
```

### 2. Instalar uv (gestor de paquetes)

```bash
pip install uv
```

### 3. Instalar dependencias

```bash
uv sync
```

### 4. Copiar configuracion

```bash
copy .env.example .env
```

### 5. Ejecutar

```bash
python main.py
```

La primera vez que abras el tab **Modelos** y hagas click en **Descargar**,
se descargaran los modelos AI (~5-8 GB). Despues quedan en cache.

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

### 4. Estadisticas (cuarto tab)

- Total de registros indexados
- Videos procesados
- Distribucion de clases (person, car, etc.)
- Boton para limpiar la coleccion

---

## Arquitectura

```
video_search_desktop/
├── main.py              <- Punto de entrada
├── core/                <- Backend (sin dependencia a UI)
│   ├── logger.py        <- Loguru centralizado
│   ├── gpu_utils.py     <- Monitor GPU dinamico
│   ├── database.py      <- ChromaDB 1.5.7 embebido
│   ├── model_registry.py <- Catalogo + Factory
│   ├── model_manager.py <- Singleton GPU
│   ├── frame_extractor.py <- Video -> Frames
│   ├── indexer.py       <- Pipeline completo
│   ├── searcher.py      <- Busqueda por texto
│   ├── detectors/       <- BaseDetector -> YOLODetector
│   ├── embedders/       <- BaseEmbedder -> CLIPEmbedder
│   └── describers/      <- BaseDescriber -> Qwen/Moondream
├── models/              <- Pydantic v2 (tipado fuerte)
├── ui/                  <- PySide6 (frontend)
│   ├── theme.py         <- Dark/light mode
│   ├── base_widget.py   <- Clase base para todos los paneles
│   ├── main_window.py   <- Ventana principal
│   ├── widgets/         <- 12 componentes visuales
│   └── workers/         <- 5 QThread workers
├── data/chromadb/       <- Base de datos embebida
├── output/              <- Frames y crops generados
└── logs/                <- Logs rotativos
```

### Principios

- **SOLID**: cada clase tiene una unica responsabilidad
- **Polimorfismo**: BaseDetector/BaseEmbedder/BaseDescriber con herencia
- **Singleton**: ModelManager thread-safe
- **Factory**: ModelRegistry crea instancias segun seleccion del usuario
- **Repository**: Database abstrae ChromaDB
- **Observer**: Signals/Slots de PySide6 para comunicar workers con UI
- **Dependency Inversion**: Indexer recibe interfaces, no implementaciones

### Modelos AI

| Modelo | Funcion | VRAM | Idioma |
|--------|---------|------|--------|
| YOLOv11 n/m/x | Detectar objetos | 0.3-1.0 GB | N/A |
| Jina CLIP v2 | Embeddings img+txt | 3.5 GB | Multilingue |
| Qwen2.5-VL 7B Q4 | Describir (detallado) | 5.5 GB | Espanol |
| Moondream2 4-bit | Describir (rapido) | 2.5 GB | Ingles |

---

## Stack

Python 3.12 | PySide6 | PyTorch CUDA | Ultralytics YOLOv11 | Jina CLIP v2 |
Transformers | ChromaDB 1.5.7 | Pydantic v2 | Loguru | pynvml

---

## Licencia

Proprietary — Todos los derechos reservados.
