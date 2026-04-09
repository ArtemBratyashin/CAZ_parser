import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DigestOrchestrator:
    """
    External entrypoint for digest collection pipeline.
    Bot handlers and scheduler should call this class.
    """

    def __init__(self, database, parser_manager, composer) -> None:
        self._database = database
        self._parser = parser_manager
        self._composer = composer

    async def collect_digest(
        self,
        date_from: Optional[dt.date] = None,
        date_to: Optional[dt.date] = None,
        update_db_dates: bool = False,
    ) -> Dict:
        """
        Собираем дайджест за указанный период.
        Если даты не указаны, то собираем дайджест за вчерашний день.
        Если update_db_dates=True, то обновляем даты в базе данных.
        """
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

    def update_dates_to_yesterday(self) -> int:
        """Обновляет даты новостей в БД на вчерашнюю дату."""
        return self._database.update_dates_to_yesterday()

    def run_seed_db(self) -> None:
        """Запускает загрузку/синхронизацию источников из Python-данных в БД."""
        project_root = Path(__file__).resolve().parents[2]
        project_root_str = str(project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        from data.seed_db import seed_database

        dsn = self._database.engine.url.render_as_string(hide_password=False)
        seed_database(dsn=dsn)

    async def disconnect(self) -> None:
        """Отключаемся от ресурсов, используемых в процессе сбора дайджеста."""
        await self._parser.disconnect()
