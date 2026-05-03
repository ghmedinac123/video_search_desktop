"""
TelegramNotifier — envia eventos al chat configurado por bot HTTP.

Implementa BaseNotifier. Lee TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID
desde .env. Si falta el token, queda deshabilitado silenciosamente.

Usa requests para POST a la API de Telegram.

Uso:
    notifier = TelegramNotifier()  # lee de env vars
    AlertManager.get_instance().register(notifier)
"""

from __future__ import annotations

import os
from pathlib import Path

from core.alerts.base_notifier import BaseNotifier
from core.logger import logger
from models.event import EventSeverity, SecurityEvent


class TelegramNotifier(BaseNotifier):
    """
    Notificador via Telegram Bot API (HTTP).

    Las credenciales vienen de variables de entorno:
        TELEGRAM_BOT_TOKEN: token del bot creado con BotFather
        TELEGRAM_CHAT_ID: ID del chat o grupo destino

    Si alguna falta, el notifier queda enabled=False.
    """

    API_BASE: str = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        min_severity: EventSeverity = EventSeverity.WARNING,
    ) -> None:
        super().__init__(
            name="Telegram",
            min_severity=min_severity,
            enabled=True,
        )
        self._bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

        if not self._bot_token or not self._chat_id:
            logger.info(
                "TelegramNotifier deshabilitado (faltan TELEGRAM_BOT_TOKEN "
                "o TELEGRAM_CHAT_ID en .env)"
            )
            self._enabled = False

    def send(self, event: SecurityEvent) -> bool:
        """Envia mensaje + foto opcional al chat de Telegram."""
        try:
            import requests
        except ImportError:
            logger.warning(
                "TelegramNotifier requiere `requests`. "
                "Ejecuta: uv add requests"
            )
            return False

        text = self._format_message(event)

        if event.thumbnail_path and event.thumbnail_path.exists():
            return self._send_photo(text, event.thumbnail_path, requests)
        return self._send_text(text, requests)

    def _send_text(self, text: str, requests_module) -> bool:
        """Envia mensaje de texto plano."""
        url = self.API_BASE.format(token=self._bot_token) + "/sendMessage"
        try:
            resp = requests_module.post(
                url,
                data={
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                return True
            logger.warning(
                f"Telegram sendMessage fallo: {resp.status_code} {resp.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Telegram sendMessage exception: {e}")
            return False

    def _send_photo(
        self, caption: str, photo_path: Path, requests_module
    ) -> bool:
        """Envia foto + caption."""
        url = self.API_BASE.format(token=self._bot_token) + "/sendPhoto"
        try:
            with open(photo_path, "rb") as f:
                resp = requests_module.post(
                    url,
                    data={
                        "chat_id": self._chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                    },
                    files={"photo": f},
                    timeout=15,
                )
            if resp.status_code == 200:
                return True
            logger.warning(
                f"Telegram sendPhoto fallo: {resp.status_code} {resp.text}"
            )
            return False
        except Exception as e:
            logger.error(f"Telegram sendPhoto exception: {e}")
            return False

    @staticmethod
    def _format_message(event: SecurityEvent) -> str:
        """Construye mensaje HTML con la info del evento."""
        sev_emoji = {
            EventSeverity.INFO: "ℹ️",
            EventSeverity.WARNING: "⚠️",
            EventSeverity.CRITICAL: "🚨",
        }.get(event.severity, "•")

        lines = [
            f"{sev_emoji} <b>{event.title}</b>",
            f"📷 <i>{event.camera_id}</i>",
            f"🕐 {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if event.message:
            lines.append("")
            lines.append(event.message[:300])
        return "\n".join(lines)
