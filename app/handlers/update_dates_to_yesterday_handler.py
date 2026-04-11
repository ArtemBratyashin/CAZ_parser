"""Обработчик команды /update_dates_to_yesterday."""

import datetime as dt

from telegram import Update
from telegram.ext import ContextTypes


async def update_dates_to_yesterday_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ставит вчерашнюю дату источникам в БД."""
    orchestrator = context.application.bot_data.get("orchestrator")
    if orchestrator is None:
        if update.message:
            await update.message.reply_text("Возникла ошибка")
        return

    try:
        updated_rows = orchestrator.update_dates_to_yesterday()
    except Exception:
        if update.message:
            await update.message.reply_text("Возникла ошибка")
        return

    if update.message:
        yesterday = dt.date.today() - dt.timedelta(days=1)
        await update.message.reply_text(
            f"Даты обновлены на {yesterday.strftime('%d.%m.%Y')}. Обновлено записей: {updated_rows}"
        )
