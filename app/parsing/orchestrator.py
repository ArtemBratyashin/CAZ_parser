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
        If date_from is None, parser layer uses last_message_date from DB
        as lower bound for each source.
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

    async def disconnect(self) -> None:
        await self._parser.disconnect()
