import asyncio
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class ParserManager:
    """
    ParserManager — оркестратор парсинга.
    Принимает на вход общий список источников
    В каждый конкретный парсер передаёт список источников source_type
    Получает от каждого парсера список новостей и склеивает их.
    """

    def __init__(self, tg_parser=None, vk_parser=None, web_parser=None) -> None:
        """
        Все парсеры опциональны — это позволяет "отключать" источники.
        Если, например, tg_parser=None, то TG источники будут пропущены с warning-логом.
        """
        self._tg = tg_parser
        self._vk = vk_parser
        self._web = web_parser

    async def parse(self, sources: List[Dict]) -> List[Dict]:
        """
        Делит источники по типам.
        Создаёт список корутин для включённых парсеров.
        Склеивает результаты в один массив словарей.
        """
        tg_sources, vk_sources, web_sources = self._split_sources(sources)

        tasks = self._build_tasks(tg_sources, vk_sources, web_sources)

        if not tasks:
            return []

        # Запускаем корутины конкурентно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Объединяем результаты
        messages = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Parser failed: %s", result)
                continue
            messages.extend(result)

        return messages

    def _split_sources(self, sources: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Делит входные sources по source_type на 3 списка: tg/vk/web."""
        tg_sources = []
        vk_sources = []
        web_sources = []

        for s in sources:
            st = s.get("source_type")
            source_info = self._source_info(s)

            if st == "tg":
                tg_sources.append(source_info)
            elif st == "vk":
                vk_sources.append(source_info)
            elif st == "web":
                web_sources.append(source_info)
            else:
                logger.warning("Unknown source_type=%r for source_link=%r", st, s.get("source_link"))

        return tg_sources, vk_sources, web_sources

    def _source_info(self, s: Dict) -> Dict:
        """Обрезает входной словарь источника."""
        return {
            "source_name": s.get("source_name"),
            "source_link": s.get("source_link"),
            "contact": s.get("contact"),
            "last_message_date": s.get("last_message_date"),
        }

    def _build_tasks(self, tg_sources: List[Dict], vk_sources: List[Dict], web_sources: List[Dict]) -> List:
        """Создаёт список корутин только для включённых парсеров."""
        tasks = []

        if tg_sources:
            if self._tg is None:
                logger.warning("TG parser disabled: skipping %s sources", len(tg_sources))
            else:
                tasks.append(self._tg.parse(tg_sources))

        if vk_sources:
            if self._vk is None:
                logger.warning("VK parser disabled: skipping %s sources", len(vk_sources))
            else:
                tasks.append(self._vk.parse(vk_sources))

        if web_sources:
            if self._web is None:
                logger.warning("WEB parser disabled: skipping %s sources", len(web_sources))
            else:
                tasks.append(self._web.parse(web_sources))

        return tasks

    async def disconnect(self) -> None:
        """Отключает внутренние парсеры/клиенты (например, Telethon), если они включены."""
        if self._tg is not None and hasattr(self._tg, "disconnect"):
            await self._tg.disconnect()
