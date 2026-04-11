"""Обработчик команды /myid."""

from telegram import Update
from telegram.ext import ContextTypes


async def myid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возвращает id и тип чата."""
    chat = update.effective_chat
    if update.message and chat:
        await update.message.reply_text(f"Ваш chat_id: {chat.id}\nТип чата: {chat.type}")
