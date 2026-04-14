"""
Utilidades de GPU ??? detecci??n, monitoreo VRAM, temperatura.

Clase est??tica que lee informaci??n de la GPU NVIDIA usando
torch.cuda y pynvml. No carga modelos, solo lee sensores.

Uso:
    from core.gpu_utils import GPUUtils

    info = GPUUtils.detect_gpu()          # Info est??tica
    vram = GPUUtils.get_vram_status()     # Estado en tiempo real
    GPUUtils.clear_vram_cache()           # Liberar cache CUDA
"""

from __future__ import annotations

from core.logger import logger
from models.gpu import GPUInfo, VRAMStatus


class GPUUtils:
    """Utilidades est??ticas para monitoreo de GPU NVIDIA."""

    @staticmethod
    def detect_gpu() -> GPUInfo:
        """
        Detecta la GPU disponible y retorna info est??tica.

        Intenta usar torch.cuda primero, luego pynvml para
        driver version. Si no hay GPU, retorna available=False.
        """
        try:
            import torch

            if not torch.cuda.is_available():
                logger.warning("No se detect?? GPU CUDA")
                return GPUInfo(available=False)

            device_name = torch.cuda.get_device_name(0)
            total_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            cuda_version = torch.version.cuda or "N/A"

            # Intentar obtener versi??n del driver con pynvml
            driver_version = GPUUtils._get_driver_version()

            info = GPUInfo(
                available=True,
                device_name=device_name,
                total_vram_gb=round(total_vram, 1),
                cuda_version=cuda_version,
                driver_version=driver_version,
            )

            logger.info(
                f"GPU detectada: {info.device_name} ??? "
                f"{info.total_vram_gb} GB VRAM ??? "
                f"CUDA {info.cuda_version}"
            )
            return info

        except ImportError:
            logger.error("torch no instalado ??? no se puede detectar GPU")
            return GPUInfo(available=False)
        except Exception as e:
            logger.error(f"Error detectando GPU: {e}")
            return GPUInfo(available=False)

    @staticmethod
    def get_vram_status() -> VRAMStatus:
        """
        Lee el estado actual de la VRAM en tiempo real.

        Usa torch.cuda para memoria y pynvml para temperatura
        y utilizaci??n. Se llama cada segundo desde el monitor UI.
        """
        try:
            import torch

            if not torch.cuda.is_available():
                return VRAMStatus()

            used = torch.cuda.memory_allocated(0) / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            free = total - reserved

            # Temperatura y utilizaci??n via pynvml
            temperature, utilization = GPUUtils._get_nvml_stats()

            return VRAMStatus(
                used_gb=round(used, 2),
                free_gb=round(free, 2),
                total_gb=round(total, 1),
                gpu_utilization_percent=utilization,
                temperature_celsius=temperature,
            )

        except ImportError:
            return VRAMStatus()
        except Exception as e:
            logger.debug(f"Error leyendo VRAM: {e}")
            return VRAMStatus()

    @staticmethod
    def clear_vram_cache() -> None:
        """Libera el cache de CUDA para recuperar VRAM."""
        try:
            import torch

            if torch.cuda.is_available():
                before = torch.cuda.memory_allocated(0) / (1024**3)
                torch.cuda.empty_cache()
                after = torch.cuda.memory_allocated(0) / (1024**3)
                freed = before - after
                logger.info(f"VRAM cache liberado: {freed:.2f} GB")
        except Exception as e:
            logger.debug(f"Error limpiando VRAM: {e}")

    @staticmethod
    def get_device() -> str:
        """Retorna 'cuda' si hay GPU disponible, 'cpu' si no."""
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    # ?????? M??todos privados ??????

    @staticmethod
    def _get_driver_version() -> str:
        """Lee versi??n del driver NVIDIA via pynvml."""
        try:
            import pynvml
            pynvml.nvmlInit()
            version = pynvml.nvmlSystemGetDriverVersion()
            pynvml.nvmlShutdown()
            return version
        except Exception:
            return "N/A"

    @staticmethod
    def _get_nvml_stats() -> tuple[int, float]:
        """
        Lee temperatura y utilizaci??n via pynvml.

        Returns:
            Tupla (temperatura_celsius, utilization_percent).
        """
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            temp = pynvml.nvmlDeviceGetTemperature(
                handle, pynvml.NVML_TEMPERATURE_GPU
            )
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            pynvml.nvmlShutdown()
            return temp, float(util.gpu)
        except Exception:
            return 0, 0.0
