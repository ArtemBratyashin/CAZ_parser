import asyncio
import logging
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ParserManager:
    """Маршрутизирует источники по нужным парсерам."""

    def __init__(self, tg_parser=None, vk_parser=None, web_parser=None) -> None:
        """Сохраняет доступные парсеры."""
        self._tg = tg_parser
        self._vk = vk_parser
        self._web = web_parser

    async def parse(
        self,
        sources: List[Dict],
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Tuple[List[Dict], List[str], Dict[str, int]]:
        """Запускает парсеры и возвращает сообщения, ошибки и статистику."""
        tg_sources, vk_sources, web_sources, no_parser_sources = self._split_sources(sources)

        stats = {
            "sources_total": len(sources),
            "sources_with_news": 0,
            "sources_without_news": 0,
            "sources_failed": 0,
            "sources_without_parser": len(no_parser_sources),
        }

        jobs = self._jobs(tg_sources, vk_sources, web_sources, date_from, date_to)
        if not jobs:
            return [], [], stats

        job_results = await asyncio.gather(*jobs)
        messages: List[Dict] = []
        errors: List[str] = []

        for item in job_results:
            source_items = item["sources"]
            source_count = len(source_items)
            error_text = item["error"]
            result = item["result"]

            if error_text is not None:
                stats["sources_failed"] += source_count
                errors.append(error_text)
                continue

            if not isinstance(result, list):
                stats["sources_failed"] += source_count
                errors.append(f"Unexpected parser result type: {type(result)}")
                continue

            messages.extend(result)

            with_news = self._count_sources_with_news(source_items, result)
            stats["sources_with_news"] += with_news
            stats["sources_without_news"] += max(source_count - with_news, 0)

        return messages, errors, stats

    def _split_sources(self, sources: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
        """Делит источники по типам и отделяет неподдерживаемые."""
        tg_sources: List[Dict] = []
        vk_sources: List[Dict] = []
        web_sources: List[Dict] = []
        no_parser_sources: List[Dict] = []

        for source in sources:
            source_type = source.get("source_type")
            source_info = self._source_info(source)

            if source_type == "tg":
                if self._tg is None:
                    no_parser_sources.append(source_info)
                    logger.warning("TG parser disabled: skipping source_link=%r", source.get("source_link"))
                else:
                    tg_sources.append(source_info)
            elif source_type == "vk":
                if self._vk is None:
                    no_parser_sources.append(source_info)
                    logger.warning("VK parser disabled: skipping source_link=%r", source.get("source_link"))
                else:
                    vk_sources.append(source_info)
            elif source_type == "web":
                if self._web is None:
                    no_parser_sources.append(source_info)
                    logger.warning("WEB parser disabled: skipping source_link=%r", source.get("source_link"))
                else:
                    web_sources.append(source_info)
            else:
                no_parser_sources.append(source_info)
                logger.warning("Unknown source_type=%r for source_link=%r", source_type, source.get("source_link"))

        return tg_sources, vk_sources, web_sources, no_parser_sources

    def _jobs(
        self,
        tg_sources: List[Dict],
        vk_sources: List[Dict],
        web_sources: List[Dict],
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> List[Any]:
        """Создает асинхронные задачи запуска парсеров."""
        tasks: List[Any] = []

        if tg_sources and self._tg is not None:
            tasks.append(self._run_parser_job("TG", self._tg, tg_sources, date_from, date_to))
        if vk_sources and self._vk is not None:
            tasks.append(self._run_parser_job("VK", self._vk, vk_sources, date_from, date_to))
        if web_sources and self._web is not None:
            tasks.append(self._run_parser_job("WEB", self._web, web_sources, date_from, date_to))

        return tasks

    async def _run_parser_job(
        self,
        parser_name: str,
        parser: Any,
        source_items: List[Dict],
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> Dict[str, Any]:
        """Запускает один парсер и сохраняет контекст источников."""
        try:
            result = await parser.parse(source_items, date_from=date_from, date_to=date_to)
            return {"sources": source_items, "result": result, "error": None}
        except Exception as exc:
            return {"sources": source_items, "result": None, "error": f"{parser_name} parser error: {exc}"}

    def _source_info(self, source: Dict) -> Dict:
        """Оставляет поля, нужные парсеру."""
        return {
            "source_name": source.get("source_name"),
            "source_link": source.get("source_link"),
            "contact": source.get("contact"),
            "last_message_date": source.get("last_message_date"),
        }

    def _count_sources_with_news(self, source_items: List[Dict], messages: List[Dict]) -> int:
        """Считает, для скольких источников есть хотя бы одна новость."""
        news_keys = {(message.get("source_name"), message.get("source_link")) for message in messages}
        return sum(1 for source in source_items if (source.get("source_name"), source.get("source_link")) in news_keys)

    async def disconnect(self) -> None:
        """Вызывает disconnect у доступных парсеров."""
        if self._tg is not None and hasattr(self._tg, "disconnect"):
            await self._tg.disconnect()
        if self._vk is not None and hasattr(self._vk, "disconnect"):
            await self._vk.disconnect()
