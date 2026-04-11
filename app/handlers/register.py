"""Регистрация команд Telegram-бота."""

from telegram.ext import Application, CommandHandler

from app.handlers.actual_digest_handler import actual_digest_handler
from app.handlers.digest_last_week_handler import digest_last_week_handler
from app.handlers.digest_today_handler import digest_today_handler
from app.handlers.digest_yesterday_handler import digest_yesterday_handler
from app.handlers.info_handler import info_handler
from app.handlers.myid_handler import myid_handler
from app.handlers.seed_db_handler import seed_db_handler
from app.handlers.start_handler import start_handler
from app.handlers.update_dates_to_yesterday_handler import update_dates_to_yesterday_handler


def register_basic_handlers(application: Application) -> None:
    """Регистрирует все пользовательские команды."""
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("myid", myid_handler))
    application.add_handler(CommandHandler("info", info_handler))
    application.add_handler(CommandHandler("seed_db", seed_db_handler))
    application.add_handler(CommandHandler("update_dates_to_yesterday", update_dates_to_yesterday_handler))
    application.add_handler(CommandHandler("digest_today", digest_today_handler))
    application.add_handler(CommandHandler("digest_yesterday", digest_yesterday_handler))
    application.add_handler(CommandHandler("digest_last_week", digest_last_week_handler))
    application.add_handler(CommandHandler("actual_digest", actual_digest_handler))
