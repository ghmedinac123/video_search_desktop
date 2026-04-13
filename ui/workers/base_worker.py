"""
Clase base para TODOS los QThread workers.

Herencia: IndexWorker(BaseWorker), SearchWorker(BaseWorker), etc.
Evita codigo duplicado: try/catch, signal error, cancelacion.

Cada subclase solo implementa execute() con su logica especifica.

Uso:
    from ui.workers.base_worker import BaseWorker

    class MiWorker(BaseWorker):
        resultado = Signal(str)

        def execute(self) -> None:
            # Mi logica aqui
            self.resultado.emit("listo")
"""

from __future__ import annotations

from abc import abstractmethod

from PySide6.QtCore import QThread, Signal

from core.logger import logger


class BaseWorker(QThread):
    """
    Clase base para todos los workers — patron Template Method.

    Provee:
    - Signal error(str) compartido por todos los workers.
    - run() con try/catch automatico que emite error.
    - Propiedad is_cancelled para control de flujo.
    - Cada subclase solo implementa execute().
    """

    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._cancelled = False

    def run(self) -> None:
        """
        Template Method: ejecuta con manejo de errores automatico.

        NO sobreescribir este metodo. Implementar execute() en su lugar.
        """
        self._cancelled = False
        try:
            self.execute()
        except Exception as e:
            logger.error(f"{self.__class__.__name__} error: {e}")
            self.error.emit(str(e))

    @abstractmethod
    def execute(self) -> None:
        """Logica especifica del worker. Implementar en subclase."""
        ...

    def cancel(self) -> None:
        """Solicita cancelacion del worker."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """True si se solicito cancelacion."""
        return self._cancelled
