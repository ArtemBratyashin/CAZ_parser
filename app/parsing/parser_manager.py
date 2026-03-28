import asyncio
import logging
from datetime import date
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ParserManager:
    '''
    ParserManager - оркестратор для всех парсеров.
    Разделяет источники по типам и запускает соответствующие парсеры.
    '''

    def __init__(self, tg_parser=None, vk_parser=None, web_parser=None) -> None:
        '''Инициализируем менеджер парсеров с опциональными парсерами для Telegram, VK и веб-сайтов.'''
        self._tg = tg_parser
        self._vk = vk_parser
        self._web = web_parser

    async def parse(
        self,
        sources: List[Dict],
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Tuple[List[Dict], List[str]]:
        '''Основной метод для запуска парсеров. Принимает список источников и возвращает список сообщений и ошибок.'''
        tg_sources, vk_sources, web_sources = self._split_sources(sources)
        tasks = self._build_tasks(tg_sources, vk_sources, web_sources, date_from, date_to)

        if not tasks:
            return [], []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        messages: List[Dict] = []
        errors: List[str] = []

        for result in results:
            if isinstance(result, Exception):
                errors.append(f"Parser error: {result}")
            elif isinstance(result, list):
                messages.extend(result)
            else:
                errors.append(f"Unexpected parser result type: {type(result)}")

        return messages, errors

    def _split_sources(self, sources: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        '''Разделяет источники на три категории'''
        tg_sources: List[Dict] = []
        vk_sources: List[Dict] = []
        web_sources: List[Dict] = []

        for source in sources:
            source_type = source.get("source_type")
            source_info = self._source_info(source)

            if source_type == "tg":
                tg_sources.append(source_info)
            elif source_type == "vk":
                vk_sources.append(source_info)
            elif source_type == "web":
                web_sources.append(source_info)
            else:
                logger.warning("Unknown source_type=%r for source_link=%r", source_type, source.get("source_link"))

        return tg_sources, vk_sources, web_sources

    def _source_info(self, source: Dict) -> Dict:
        '''Извлекает и возвращает только нужные поля из источника для парсера'''
        return {
            "source_name": source.get("source_name"),
            "source_link": source.get("source_link"),
            "contact": source.get("contact"),
            "last_message_date": source.get("last_message_date"),
        }

    def _build_tasks(
        self,
        tg_sources: List[Dict],
        vk_sources: List[Dict],
        web_sources: List[Dict],
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> List:
        '''Строит список задач для запуска парсеров'''
        tasks = []

        if tg_sources:
            if self._tg is None:
                logger.warning("TG parser disabled: skipping %s sources", len(tg_sources))
            else:
                tasks.append(self._tg.parse(tg_sources, date_from=date_from, date_to=date_to))

        if vk_sources:
            if self._vk is None:
                logger.warning("VK parser disabled: skipping %s sources", len(vk_sources))
            else:
                tasks.append(self._vk.parse(vk_sources, date_from=date_from, date_to=date_to))

        if web_sources:
            if self._web is None:
                logger.warning("WEB parser disabled: skipping %s sources", len(web_sources))
            else:
                tasks.append(self._web.parse(web_sources, date_from=date_from, date_to=date_to))

        return tasks

    async def disconnect(self) -> None:
        '''Отключает все парсеры, если у них есть метод disconnect'''
        if self._tg is not None and hasattr(self._tg, "disconnect"):
            await self._tg.disconnect()
        if self._vk is not None and hasattr(self._vk, "disconnect"):
            await self._vk.disconnect()
