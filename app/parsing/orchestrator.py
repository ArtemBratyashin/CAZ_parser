import datetime as dt
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DigestOrchestrator:
    """
    External entrypoint for digest collection pipeline.
    Bot handlers and scheduler should call this class.
    """

    def __init__(self, database, parser_manager, composer) -> None:
        '''Инициируем оркестратор с помощью базы данных, менеджера парсеров и композитора текста'''
        self._database = database
        self._parser = parser_manager
        self._composer = composer

    async def collect_digest(
        self,
        date_from: Optional[dt.date] = None,
        date_to: Optional[dt.date] = None,
        update_db_dates: bool = False,
    ) -> Dict:
        '''
        Собираем дайджест за указанный период.
        Если даты не указаны, то собираем дайджест за вчерашний день.
        Если update_db_dates=True, то обновляем даты в базе данных
        '''
        effective_date_to = date_to or (dt.date.today() - dt.timedelta(days=1))

        sources = self._database.sources()
        messages, errors = await self._parser.parse(
            sources=sources,
            date_from=date_from,
            date_to=effective_date_to,
        )

        text = self._composer.compose(messages)

        if update_db_dates:
            self._database.update_dates(messages=messages)

        return {
            "text": text,
            "messages": messages,
            "errors": errors,
            "date_from": date_from,
            "date_to": effective_date_to,
            "update_db_dates": update_db_dates,
        }

    async def disconnect(self) -> None:
        '''Отключаемся от всех ресурсов, которые использовались в процессе сбора дайджеста'''
        await self._parser.disconnect()
