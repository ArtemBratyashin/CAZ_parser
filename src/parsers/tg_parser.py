import logging
from datetime import date, datetime
from typing import Dict, List, Optional

from telethon import TelegramClient

logger = logging.getLogger(__name__)


class TelegramParser:
    '''
    Парсер для получения новостей из Telegram каналов.
    Получает массив источников и собирает все сообщения после last_message_date.
    '''

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone_number,
        session_name: str = "user_session",
        max_date: Optional[date] = None,
    ):
        '''session_name: str - имя файла сессии (user_session.session)'''
        self._session_name = session_name
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._client: Optional[TelegramClient] = None
        self._max_date = max_date

    async def parse(self, sources: List[Dict]) -> List[Dict]:
        '''Парсит список Telegram каналов и собирает все новости. Для каждого источника новости парсятся отдельно.'''
        try:
            await self._ensure_client()
            results = []

            logger.info(f"📊 Начинаю парсинг {len(sources)} TG каналов")

            for source in sources:
                channel_results = await self._parse_single_channel(source)
                results.extend(channel_results)

            logger.info(f"✅ TG парсинг завершён. Найдено {len(results)} новых сообщений")
            return results

        except Exception as e:
            logger.error(f"❌ Критическая ошибка TelegramParser: {e}")
            return []

    async def _ensure_client(self) -> None:
        '''Создаёт и подключает клиента, если он ещё не создан.'''
        if self._client is not None:
            return

        self._client = TelegramClient(self._session_name, self._api_id, self._api_hash)
        await self._client.connect()

        # Авторизация нужна только если сессии ещё нет / она недействительна
        if await self._client.is_user_authorized():
            logger.info("✅ Уже авторизованы в Telegram")
            return

        logger.info("🔐 Первая авторизация в Telegram.")
        await self._client.send_code_request(self._phone_number)
        code = input("🔐 Введите код из Telegram: ").strip()

        try:
            await self._client.sign_in(self._phone_number, code)
            logger.info("✅ Авторизация успешна и сохранена в .session")
        except Exception as auth_error:
            logger.error(f"Ошибка авторизации: {auth_error}")

            if "password" in str(auth_error).lower() or "two-step" in str(auth_error).lower():
                password = input("🔐 Введите пароль 2FA: ").strip()
                await self._client.sign_in(password=password)
                logger.info("✅ 2FA авторизация успешна и сохранена в .session")
            else:
                raise

    async def _parse_single_channel(self, source: Dict) -> List[Dict]:
        """Парсит один Telegram канал и собирает новости после last_message_date и не позже max_date."""
        results = []

        try:
            channel_username = self._extract_channel_name(source["source_link"])
            last_date = datetime.strptime(source["last_message_date"], "%Y-%m-%d").date()

            max_date = self._max_date

            logger.info(
                "🔍 TG: Парсю канал %r (%s) в диапазоне (%s, %s]",
                source["source_name"],
                channel_username,
                last_date,
                max_date,
            )

            async for message in self._client.iter_messages(channel_username, reverse=False):
                if not message or not message.text:
                    continue

                message_date = message.date.date()

                if message_date <= last_date:
                    break

                if max_date is not None and message_date > max_date:
                    continue

                results.append(
                    {
                        "source_name": source["source_name"],
                        "source_link": source["source_link"],
                        "contact": source["contact"],
                        "date": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "message": message.text[:100],
                    }
                )

                logger.info(
                    "✅ TG: %s – сообщение %s от %s",
                    source["source_name"],
                    message.id,
                    message.date,
                )

        except Exception as e:
            logger.error("❌ Ошибка парсинга канала %r: %s", source["source_name"], e)

        return results

    async def disconnect(self) -> None:
        '''Отключает клиента от Telegram.'''
        if self._client:
            await self._client.disconnect()
            self._client = None
            logger.info("✅ Отключено от Telegram")

    @staticmethod
    def _extract_channel_name(url: str) -> str:
        '''Извлекает имя канала из URL.'''
        return url.rstrip("/").split("/")[-1]
