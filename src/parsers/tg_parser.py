# src/parsers/telegram_parser.py

import os
import logging
from typing import Optional, Dict

from dotenv import load_dotenv
from telethon import TelegramClient

from .base_parser import BaseParser

load_dotenv()
logger = logging.getLogger(__name__)


class TelegramParser(BaseParser):
    """Парсер Telegram‑каналов на Telethon, с сохранением сессии."""

    def __init__(self, session_name: str = "user_session"):
        """
        Args:
            session_name: имя файла сессии (user_session.session)
        """
        self.session_name = session_name
        self.api_id = int(os.getenv("TG_API_ID"))
        self.api_hash = os.getenv("TG_API_HASH")
        self.phone_number = os.getenv("PHONE_NUMBER")
        self.client: Optional[TelegramClient] = None

    async def _ensure_client(self) -> None:
        """Создаёт и подключает клиента, если он ещё не создан."""
        if self.client is None:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.connect()

            # Авторизация нужна только если сессии ещё нет / она недействительна
            if not await self.client.is_user_authorized():
                logger.info("🔐 Первая авторизация в Telegram (дальше сессия сохранится).")
                await self.client.send_code_request(self.phone_number)
                code = input("Введите код из Telegram: ").strip()
                await self.client.sign_in(self.phone_number, code)
                logger.info("✅ Авторизация успешно выполнена и сохранена в .session")

    async def parse(self, source: Dict) -> Optional[Dict]:
        """
        Получает последнее сообщение из Telegram‑канала.

        source: {
            "name": "Кафедра физики",
            "url": "https://t.me/theorphys_seminar",
            "channel": "telegram",
            ...
        }
        """
        try:
            await self._ensure_client()

            channel_username = source["url"].rstrip("/").split("/")[-1]

            async for message in self.client.iter_messages(channel_username, limit=1):
                if message and message.text:
                    return {
                        "title": source["name"],
                        "text": message.text[:100],
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "link": f"https://t.me/{channel_username}/{message.id}",
                    }

            logger.warning(f"⚠️ В канале {channel_username} нет сообщений.")
            return None

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга {source.get('name', channel_username)}: {e}")
            return None

    async def disconnect(self) -> None:
        """Отключает клиента (вызывается один раз при завершении программы)."""
        if self.client:
            await self.client.disconnect()
            self.client = None
            logger.info("✅ Отключено от Telegram")
