import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()
logger = logging.getLogger(__name__)


class TelegramParser:
    """
    Парсер для получения новостей из Telegram каналов.
    Получает массив источников и собирает все сообщения после last_message_date.
    """

    def __init__(self, session_name: str = "user_session"):
        """session_name: str - имя файла сессии (user_session.session)"""
        self.session_name = session_name
        self.API_ID = int(os.getenv("TG_API_ID"))
        self.API_HASH = os.getenv("TG_API_HASH")
        self.PHONE_NUMBER = os.getenv("PHONE_NUMBER")
        self.client: Optional[TelegramClient] = None

    async def _ensure_client(self) -> None:
        """Создаёт и подключает клиента, если он ещё не создан."""
        if self.client is not None:
            return

        self.client = TelegramClient(self.session_name, self.API_ID, self.API_HASH)
        await self.client.connect()

        # Авторизация нужна только если сессии ещё нет / она недействительна
        if await self.client.is_user_authorized():
            logger.info("✅ Уже авторизованы в Telegram")
            return

        logger.info("🔐 Первая авторизация в Telegram.")
        await self.client.send_code_request(self.PHONE_NUMBER)
        code = input("Введите код из Telegram: ").strip()

        try:
            await self.client.sign_in(self.PHONE_NUMBER, code)
            logger.info("✅ Авторизация успешна и сохранена в .session")
        except Exception as auth_error:
            logger.error(f"Ошибка авторизации: {auth_error}")

            if "password" in str(auth_error).lower() or "two-step" in str(auth_error).lower():
                password = input("Введите пароль 2FA: ").strip()
                await self.client.sign_in(password=password)
                logger.info("✅ 2FA авторизация успешна и сохранена в .session")
            else:
                raise

    async def _parse_single_channel(self, source: Dict) -> List[Dict]:
        """Парсит один Telegram канал и собирает новости после last_message_date."""
        results = []

        try:
            channel_username = self._extract_channel_name(source["source_link"])
            last_date = datetime.strptime(source["last_message_date"], "%Y-%m-%d").date()

            logger.info(f"🔍 TG: Парсю канал '{source['source_name']}' ({channel_username})")

            # Получить все сообщения из канала в обратном порядке (новые первыми)
            async for message in self.client.iter_messages(channel_username, reverse=False):
                if not message or not message.text:
                    continue

                # Проверяем, что сообщение новее last_message_date
                message_date = message.date.date()
                if message_date <= last_date:
                    break  # Дальше идут старые сообщения

                results.append(
                    {
                        "source_name": source["source_name"],
                        "source_link": source["source_link"],
                        "contact": source["contact"],
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "message": message.text[:100],
                    }
                )

                logger.info(f"✅ TG: {source['source_name']} – сообщение {message.id} от {message.date}")

        except Exception as e:
            logger.error(f"❌ Ошибка парсинга канала '{source['source_name']}': {e}")

        return results

    async def parse(self, sources: List[Dict]) -> List[Dict]:
        """Парсит список Telegram каналов параллельно и собирает все новости."""
        try:
            await self._ensure_client()
            results = []

            logger.info(f"📊 Начинаю парсинг {len(sources)} TG каналов")

            # Парсим все каналы последовательно (для параллелизма используй asyncio.gather)
            for source in sources:
                channel_results = await self._parse_single_channel(source)
                results.extend(channel_results)

            logger.info(f"✅ TG парсинг завершён. Найдено {len(results)} новых сообщений")
            return results

        except Exception as e:
            logger.error(f"❌ Критическая ошибка TelegramParser: {e}")
            return []

    async def disconnect(self) -> None:
        """Отключает клиента от Telegram."""
        if self.client:
            await self.client.disconnect()
            self.client = None
            logger.info("✅ Отключено от Telegram")

    @staticmethod
    def _extract_channel_name(url: str) -> str:
        """Извлекает имя канала из URL."""
        return url.rstrip("/").split("/")[-1]
