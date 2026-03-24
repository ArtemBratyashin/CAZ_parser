import logging
from datetime import date, datetime
from typing import Dict, List, Optional

import vk_api

logger = logging.getLogger(__name__)


class VkParser:
    def __init__(
        self, token: str, session_name: str = "vk_session", max_date: Optional[date] = None, api_version: str = "5.199"
    ):
        self._token = token
        self._vk_session: Optional[vk_api.VkApi] = None
        self._vk = None
        self._max_date = max_date
        self._api_version = api_version

    def _ensure_client(self) -> None:
        if self._vk is not None:
            return
        self._vk_session = vk_api.VkApi(token=self._token, api_version=self._api_version)
        self._vk = self._vk_session.get_api()
        logger.info("✅ VK клиент инициализирован")

    async def parse(self, sources: List[Dict], max_date: date) -> List[Dict]:
        """Обертка для совместимости с ParserManager"""
        try:
            self._ensure_client()
            results = []
            logger.info("📊 Парсинг %d VK групп", len(sources))

            for source in sources:
                group_news = await self._parse_single_group(source, max_date=max_date)
                results.extend(group_news)

            return results
        except Exception as e:
            logger.error("❌ Критическая ошибка VK: %s", e)
            return []

    async def _parse_single_group(self, source: Dict, max_date: date) -> List[Dict]:
        """Логика парсинга одной группы (синхронные запросы внутри)"""
        results = []
        try:
            group_id = self._extract_group_identifier(source["source_link"])
            last_date = source.get("last_message_date")

            params = {
                "count": 50,
                "offset": 0,
                "filter": "owner",
            }

            if group_id.isdigit():
                params["owner_id"] = -int(group_id)
            else:
                params["domain"] = group_id

            for _ in range(2):
                response = self._vk.wall.get(**params)
                items = response.get("items", [])
                if not items:
                    break

                stop = False
                for post in items:
                    if post.get("is_pinned"):
                        continue

                    post_dt = datetime.fromtimestamp(post["date"])
                    post_date = post_dt.date()

                    if post_date <= last_date:
                        stop = True
                        break

                    if max_date and post_date > max_date:
                        continue

                    text = (post.get("text") or "").strip()
                    if not text:
                        continue

                    clean_text = " ".join(text.split())

                    results.append(
                        {
                            "source_name": source["source_name"],
                            "source_link": source["source_link"],
                            "contact": source.get("contact"),
                            "date": post_dt.strftime("%Y-%m-%d"),
                            "message": clean_text,
                        }
                    )

                if stop:
                    break
                params["offset"] += params["count"]

        except Exception as e:
            logger.error("❌ Ошибка в группе %s: %s", source.get("source_name"), e)

        return results

    async def disconnect(self) -> None:
        logger.info("✅ Завершение работы VkParser")

    @staticmethod
    def _extract_group_identifier(url: str) -> str:
        last = url.rstrip("/").split("/")[-1]
        if last.startswith("public"):
            return last[6:]
        if last.startswith("club"):
            return last[4:]
        return last
