import logging
from datetime import datetime, date
from typing import Dict, List, Optional

import vk_api

logger = logging.getLogger(__name__)


class VkParser:
    """
    Парсер для получения постов из групп ВКонтакте.
    Получает массив источников и собирает все сообщения после last_message_date
    и не позже max_date.
    """

    def __init__(self, token: str, session_name: str = "vk_session", max_date: Optional[date] = None, api_version: str = "5.199"):
        """Авторизуемся в ВК по токену"""
        self._session_name = session_name
        self._token = token
        self._vk_session: Optional[vk_api.VkApi] = None
        self._vk = None
        self._max_date = max_date
        self._api_version = api_version

    async def parse(self, sources: List[Dict]) -> List[Dict]:
        """Парсит список ВК‑сообществ и собирает новые посты."""
        try:
            self._ensure_client()
            results = []

            logger.info("📊 Начинаю парсинг %d VK групп", len(sources))

            for source in sources:
                group_results = await self._parse_single_group(source)
                results.extend(group_results)

            logger.info("✅ VK парсинг завершён. Найдено %d новых сообщений", len(results))
            return results

        except Exception as e:
            logger.error("❌ Критическая ошибка VkGroupParser: %s", e)
            return []

    def _ensure_client(self) -> None:
        """Инициализация клиента VK по токену."""
        if self._vk is not None:
            return

        self._vk_session = vk_api.VkApi(
            token=self._token,
            api_version=self._api_version,
        )
        self._vk = self._vk_session.get_api()
        logger.info("✅ VK клиент инициализирован по токену")

    async def _parse_single_group(self, source: Dict) -> List[Dict]:
        """Парсит одну VK‑группу и собирает посты после last_message_date и не позже max_date."""
        results = []

        try:
            group_identifier = self._extract_group_identifier(source["source_link"])
            last_date = datetime.strptime(source["last_message_date"], "%Y-%m-%d").date()
            max_date = self._max_date

            logger.info("🔍 VK: Парсю группу %r (%s) в диапазоне (%s, %s]", source["source_name"], group_identifier, last_date, max_date)

            params = {
                "count": 100,
                "offset": 0,
                "filter": "owner",
            }

            if group_identifier.lstrip("-").isdigit():
                params["owner_id"] = -int(group_identifier)
            else:
                params["domain"] = group_identifier

            while True:
                response = self._vk.wall.get(**params)  # [web:26][web:29]

                items = response.get("items", [])
                if not items:
                    break

                stop = False

                for post in items:
                    post_dt = datetime.fromtimestamp(post["date"])
                    post_date = post_dt.date()

                    if post_date <= last_date:
                        stop = True
                        break

                    if max_date is not None and post_date > max_date:
                        continue

                    text = (post.get("text") or "").strip()
                    if not text:
                        continue

                    results.append(
                        {
                            "source_name": source["source_name"],
                            "source_link": source["source_link"],
                            "contact": source.get("contact"),
                            "date": post_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "message": text[:100],
                        }
                    )

                    logger.info(
                        "✅ VK: %s – пост %s от %s",
                        source["source_name"],
                        post.get("id"),
                        post_dt,
                    )

                if stop:
                    break

                params["offset"] += params["count"]

            return results

        except Exception as e:
            logger.error("❌ Ошибка парсинга группы %r: %s", source.get("source_name"), e)
            return results

    async def disconnect(self) -> None:
        """Заглушка для совместимости с TelegramParser"""
        logger.info("✅ Завершение работы VkGroupParser")

    @staticmethod
    def _extract_group_identifier(url: str) -> str:
        """Извлекает идентификатор группы из URL."""
        last = url.rstrip("/").split("/")[-1]

        if last.startswith("public") or last.startswith("club"):
            return last[len("public") :] if last.startswith("public") else last[len("club") :]

        return last
