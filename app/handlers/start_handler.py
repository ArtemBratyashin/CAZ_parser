"""Обработчик команды /start."""

from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветствие и подсказку по /info."""
    if update.message:
        await update.message.reply_text("Привет! Для получения информации о командах отправь /info")
