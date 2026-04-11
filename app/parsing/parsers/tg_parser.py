import logging
from datetime import date, datetime
from typing import Dict, List, Optional

from telethon import TelegramClient

logger = logging.getLogger(__name__)


class TelegramParser:
    """Парсит Telegram-каналы через Telethon."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone_number: str,
        session_name: str = "user_session",
    ):
        """Сохраняет параметры клиента Telegram."""
        self._session_name = session_name
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._client: Optional[TelegramClient] = None

    async def parse(
        self,
        sources: List[Dict],
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        """Собирает новости из переданных каналов."""
        await self._ensure_client()
        all_results: List[Dict] = []

        logger.info("Starting TG parsing for %d channels", len(sources))

        for source in sources:
            channel_news = await self._parse_single_channel(source, date_from=date_from, date_to=date_to)
            all_results.extend(channel_news)

        logger.info("TG parsing finished. New messages: %d", len(all_results))
        return all_results

    async def _ensure_client(self) -> None:
        """Создает и авторизует клиент при необходимости."""
        if self._client and self._client.is_connected():
            return

        self._client = TelegramClient(self._session_name, self._api_id, self._api_hash)
        await self._client.connect()

        if not await self._client.is_user_authorized():
            logger.info("Telegram auth required")
            await self._client.send_code_request(self._phone_number)

            code = input(f"Enter Telegram code for {self._phone_number}: ").strip()

            try:
                await self._client.sign_in(self._phone_number, code)
            except Exception as exc:
                if "password" in str(exc).lower():
                    password = input("Enter Telegram 2FA password: ").strip()
                    await self._client.sign_in(password=password)
                else:
                    raise

    async def _parse_single_channel(
        self,
        source: Dict,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        """Парсит один канал в заданном диапазоне."""
        results: List[Dict] = []

        try:
            channel_link = source["source_link"]
            source_name = source["source_name"]

            last_date = self._to_date(source.get("last_message_date"))
            start_date = self._to_date(date_from)
            end_date = self._to_date(date_to)
            lower_bound = start_date if start_date is not None else last_date
            inclusive_start = start_date is not None

            logger.info(
                "TG channel=%s, lower_bound=%s, date_to=%s",
                source_name,
                lower_bound,
                end_date,
            )

            async for message in self._client.iter_messages(channel_link, limit=50):
                if not message or not message.text:
                    continue

                msg_date = message.date.date()

                if end_date and msg_date > end_date:
                    continue

                if lower_bound is not None:
                    if inclusive_start:
                        if msg_date < lower_bound:
                            break
                    else:
                        if msg_date <= lower_bound:
                            break

                results.append(
                    {
                        "source_name": source_name,
                        "source_link": channel_link,
                        "contact": source.get("contact"),
                        "date": msg_date.strftime("%Y-%m-%d"),
                        "message": message.text.replace("\n", " "),
                    }
                )

        except Exception as exc:
            logger.error("TG parsing error for %s: %s", source.get("source_name"), exc)

        return results

    @staticmethod
    def _to_date(value) -> Optional[date]:
        """Преобразует значение к объекту date."""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y"):
                try:
                    return datetime.strptime(text, fmt).date()
                except ValueError:
                    continue
        return None

    async def disconnect(self) -> None:
        """Закрывает Telegram-сессию."""
        if self._client:
            await self._client.disconnect()
            logger.info("Telethon session closed")
