"""Обработчик команды /digest_yesterday."""

import datetime as dt
from typing import Any, Dict, List

from telegram import Update
from telegram.ext import ContextTypes


def _digest_texts(result: Dict[str, Any]) -> List[str]:
    """Нормализует текст дайджеста к списку сообщений."""
    values = result.get("texts")
    if isinstance(values, list):
        return [value for value in values if isinstance(value, str) and value]

    value = result.get("text")
    if isinstance(value, str) and value:
        return [value]

    return []


async def digest_yesterday_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Собирает дайджест за вчера и отправляет по частям."""
    orchestrator = context.application.bot_data.get("orchestrator")
    if orchestrator is None:
        if update.message:
            await update.message.reply_text("Возникла ошибка")
        return

    yesterday = dt.date.today() - dt.timedelta(days=1)
    result = await orchestrator.collect_digest(
        date_from=yesterday,
        date_to=yesterday,
        update_db_dates=False,
    )

    if not update.message:
        return

    errors = result.get("errors") or []
    if errors:
        await update.message.reply_text("Ошибки при парсинге:\n" + "\n".join(errors))

    for text in _digest_texts(result):
        await update.message.reply_text(text)
