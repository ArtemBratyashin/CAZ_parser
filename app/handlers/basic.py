import datetime as dt

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Привет! Для получения информации о командах отправь /info")


async def myid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if update.message and chat:
        await update.message.reply_text(f"Ваш chat_id: {chat.id}\nТип чата: {chat.type}")


async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Список команд:\n"
            "- Ответ на start (/start)\n"
            "- Получить ID чата (/myid)\n"
            "- Получить информацию о командах (/info)\n"
            "- Обновить даты на вчера (/update_dates_to_yesterday)\n"
            "- Отправить дайджест за сегодня (/digest_today)\n"
            "- Отправить дайджест за вчера (/digest_yesterday)\n"
            "- Отправить дайджест за последнюю неделю (/digest_last_week)\n"
            "- Отправить дайджест всех новых новостей (/actual_digest)"
        )


async def digest_today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orchestrator = context.application.bot_data.get("orchestrator")
    if orchestrator is None:
        if update.message:
            await update.message.reply_text("Возникла ошибка")
        return

    today = dt.date.today()
    result = await orchestrator.collect_digest(
        date_from=today,
        date_to=today,
        update_db_dates=False,
    )

    if update.message:
        if result["errors"]:
            await update.message.reply_text("Ошибки при парсинге:\n" + "\n".join(result["errors"]))
        await update.message.reply_text(result["text"])


async def digest_yesterday_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if update.message:
        if result["errors"]:
            await update.message.reply_text("Ошибки при парсинге:\n" + "\n".join(result["errors"]))
        await update.message.reply_text(result["text"])


def register_basic_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("myid", myid_handler))
    application.add_handler(CommandHandler("info", info_handler))
    application.add_handler(CommandHandler("digest_today", digest_today_handler))
    application.add_handler(CommandHandler("digest_yesterday", digest_yesterday_handler))
