"""
scraper/telegram_scraper.py
==========================
Extracción de mensajes desde canales públicos de Telegram usando Telethon.

IMPORTANTE:
- Solo funciona con canales PÚBLICOS accesibles legítimamente.
- Requiere credenciales en variables de entorno (ver docs/telegram_data_collection.md).
- NO almacena credenciales en el código.
- Respeta límites de solicitudes.
- NO accede a grupos privados ni elude restricciones.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _load_env_file():
    """Carga variables de .env desde la raíz del proyecto si existe."""
    try:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # No fallar si no se puede leer .env
        pass


_load_env_file()


class TelegramScraperError(Exception):
    """Error genérico del scraper de Telegram."""
    pass


class TelegramAuthError(TelegramScraperError):
    """Falta de credenciales o error de autenticación."""
    pass


class TelegramChannelNotAccessible(TelegramScraperError):
    """Canal no accesible o no público."""
    pass


class TelegramScraper:
    """Scraper para canales públicos de Telegram."""
    
    def __init__(self, api_id: Optional[int] = None, api_hash: Optional[str] = None):
        self.api_id = api_id or os.environ.get('TELEGRAM_API_ID')
        self.api_hash = api_hash or os.environ.get('TELEGRAM_API_HASH')
        self.phone = os.environ.get('TELEGRAM_PHONE')
        self.session_name = os.environ.get('TELEGRAM_SESSION_NAME', 'solar_telegram')
        self.client = None
        
        if not self.api_id or not self.api_hash:
            raise TelegramAuthError(
                "Faltan credenciales. Configura TELEGRAM_API_ID y TELEGRAM_API_HASH "
                "como variables de entorno. Ver docs/telegram_data_collection.md"
            )
        
    async def connect(self):
        """Conecta al cliente de Telegram."""
        try:
            from telethon import TelegramClient
            self.client = TelegramClient(self.session_name, int(self.api_id), self.api_hash)
            await self.client.start(phone=self.phone)
            logger.info("Conectado a Telegram")
        except ImportError:
            raise TelegramScraperError(
                "Telethon no está instalado. Instala con: pip install telethon"
            )
        except Exception as e:
            raise TelegramAuthError(f"Error de autenticación: {e}")
    
    async def disconnect(self):
        """Desconecta del cliente."""
        if self.client:
            await self.client.disconnect()
            logger.info("Desconectado de Telegram")
    
    async def fetch_channel_messages(self, channel_username: str, limit: int = 100) -> list[dict]:
        """Obtiene mensajes de un canal público."""
        if not self.client:
            await self.connect()
        
        try:
            entity = await self.client.get_entity(channel_username)
            messages = []
            async for message in self.client.iter_messages(entity, limit=limit):
                if message.text:
                    msg_data = {
                        'id': message.id,
                        'text': message.text,
                        'date': message.date,
                        'views': getattr(message, 'views', None),
                        'forwards': getattr(message, 'forwards', None),
                        'channel': channel_username,
                        'channel_title': getattr(entity, 'title', channel_username),
                    }
                    messages.append(msg_data)
            logger.info(f"Obtenidos {len(messages)} mensajes de {channel_username}")
            return messages
        except Exception as e:
            raise TelegramChannelNotAccessible(f"No se pudo acceder a {channel_username}: {e}")
    
    async def scrape_channels(self, channels: list[dict], limit_per_channel: int = 100) -> list[dict]:
        """Scrapea múltiples canales públicos."""
        all_messages = []
        try:
            await self.connect()
            for ch in channels:
                username = ch.get('username')
                if not username:
                    continue
                try:
                    msgs = await self.fetch_channel_messages(username, limit_per_channel)
                    all_messages.extend(msgs)
                except Exception as e:
                    logger.error(f"Error scraping {username}: {e}")
                    continue
        finally:
            await self.disconnect()
        
        return all_messages
