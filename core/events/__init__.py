"""
Sistema de eventos del proyecto — patron Observer/PubSub.

Cualquier componente publica eventos al EventBus singleton, y los
suscriptores (UI, notificadores, persistencia) reaccionan sin
acoplarse entre si.
"""

from core.events.event_bus import EventBus

__all__: list[str] = ["EventBus"]
