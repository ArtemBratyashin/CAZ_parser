"""Обработчик команды /seed_db."""

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def seed_db_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запускает синхронизацию seed-данных в БД."""
    orchestrator = context.application.bot_data.get("orchestrator")
    if orchestrator is None:
        if update.message:
            await update.message.reply_text("Возникла ошибка")
        return

    try:
        await asyncio.to_thread(orchestrator.run_seed_db)
    except Exception as exc:
        logger.exception("seed_db failed")
        if update.message:
            await update.message.reply_text(f"{"Возникла ошибка"}: {exc}")
        return

    if update.message:
        await update.message.reply_text("Синхронизация источников с БД завершена")
