import logging
from datetime import date, datetime
from typing import Dict, List, Optional

from telethon import TelegramClient

logger = logging.getLogger(__name__)

class TelegramParser:
    '''
    Парсер для получения новостей из Telegram каналов через Telethon (UserBot).
    '''

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone_number: str,
        session_name: str = "user_session",
        max_date: Optional[date] = None,
    ):
        self._session_name = session_name
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._client: Optional[TelegramClient] = None
        self._max_date = max_date

    async def parse(self, sources: List[Dict]) -> List[Dict]:
        '''Основной метод: подключается к TG и перебирает список источников.'''
        try:
            await self._ensure_client()
            all_results = []

            logger.info("📊 Начинаю парсинг %d TG каналов", len(sources))

            for source in sources:
                channel_news = await self._parse_single_channel(source)
                all_results.extend(channel_news)

            logger.info("✅ TG парсинг завершён. Найдено новых сообщений: %d", len(all_results))
            return all_results

        except Exception as e:
            logger.error("❌ Критическая ошибка в TelegramParser.parse: %s", e)
            raise e

    async def _ensure_client(self) -> None:
        '''Инициализация клиента и синхронная авторизация при необходимости.'''
        if self._client and self._client.is_connected():
            return

        self._client = TelegramClient(self._session_name, self._api_id, self._api_hash)
        await self._client.connect()

        if not await self._client.is_user_authorized():
            logger.info("🔐 Требуется авторизация в Telegram...")
            await self._client.send_code_request(self._phone_number)
            
            code = input(f"🔐 Введите код из Telegram для номера {self._phone_number}: ").strip()

            try:
                await self._client.sign_in(self._phone_number, code)
            except Exception as e:
                if "password" in str(e).lower():
                    password = input("🔐 Введите пароль 2FA: ").strip()
                    await self._client.sign_in(password=password)
                else:
                    raise e
            logger.info("✅ Авторизация успешно завершена")

    async def _parse_single_channel(self, source: Dict) -> List[Dict]:
        '''Парсинг конкретного канала.'''
        results = []
        try:
            channel_link = source["source_link"]
            source_name = source["source_name"]
            
            last_date_str = source.get("last_message_date")
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()

            logger.info("🔍 Проверяю канал: %s (после %s)", source_name, last_date)

            async for message in self._client.iter_messages(channel_link, limit=50):
                if not message or not message.text:
                    continue

                msg_date = message.date.date()

                if msg_date <= last_date:
                    break

                if self._max_date and msg_date > self._max_date:
                    continue

                results.append({
                    "source_name": source_name,
                    "source_link": channel_link,
                    "contact": source.get("contact"),
                    "date": msg_date.strftime("%Y-%m-%d"),
                    "message": message.text.replace('\n', ' '),
                })

        except Exception as e:
            logger.error("❌ Ошибка при парсинге канала %s: %s", source.get("source_name"), e)
        
        return results

    async def disconnect(self) -> None:
        '''Корректное закрытие сессии.'''
        if self._client:
            await self._client.disconnect()
            logger.info("✅ Сессия Telethon закрыта")