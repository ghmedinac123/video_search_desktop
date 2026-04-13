"""
Modelos Pydantic para información de GPU y estado de VRAM.

GPUInfo: información estática de la GPU (no cambia después de detectar).
VRAMStatus: estado dinámico que se actualiza cada segundo en el monitor.

Uso:
    from models.gpu import GPUInfo, VRAMStatus
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, computed_field


class GPUInfo(BaseModel):
    """Información estática de la GPU detectada al iniciar."""

    available: bool = False
    device_name: str = "N/A"
    total_vram_gb: float = 0.0
    cuda_version: str = "N/A"
    driver_version: str = "N/A"

    model_config = ConfigDict(frozen=True)


class VRAMStatus(BaseModel):
    """Estado dinámico de la VRAM — se actualiza en tiempo real."""

    used_gb: float = 0.0
    free_gb: float = 0.0
    total_gb: float = 0.0
    gpu_utilization_percent: float = 0.0
    temperature_celsius: int = 0

    @computed_field
    @property
    def usage_percent(self) -> float:
        """Porcentaje de VRAM utilizada."""
        if self.total_gb <= 0:
            return 0.0
        return round((self.used_gb / self.total_gb) * 100, 1)

    @computed_field
    @property
    def temperature_status(self) -> str:
        """Estado legible de la temperatura."""
        if self.temperature_celsius >= 80:
            return "Caliente"
        if self.temperature_celsius >= 65:
            return "Tibio"
        return "Normal"