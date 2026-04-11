"""Обработчик команды /info."""

from telegram import Update
from telegram.ext import ContextTypes


async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет список доступных команд."""
    if update.message:
        await update.message.reply_text(
            "Список команд:\n"
            "- Ответ на start (/start)\n"
            "- Получить ID чата (/myid)\n"
            "- Получить информацию о командах (/info)\n"
            "- Синхронизировать БД из Python-данных (/seed_db)\n"
            "- Обновить даты на вчера (/update_dates_to_yesterday)\n"
            "- Отправить дайджест за сегодня (/digest_today)\n"
            "- Отправить дайджест за вчера (/digest_yesterday)\n"
            "- Отправить дайджест за последнюю неделю (/digest_last_week)\n"
            "- Отправить дайджест всех новых новостей (/actual_digest)"
        )
