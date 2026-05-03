"""
Sistema de alertas y notificaciones.

Polimorfismo: cualquier nuevo canal (email, push, webhook) se agrega
implementando BaseNotifier. El AlertManager los orquesta a todos.
"""

from core.alerts.base_notifier import BaseNotifier
from core.alerts.alert_manager import AlertManager
from core.alerts.telegram_notifier import TelegramNotifier

__all__: list[str] = [
    "BaseNotifier",
    "AlertManager",
    "TelegramNotifier",
]
