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


def register_basic_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("myid", myid_handler))
    application.add_handler(CommandHandler("info", info_handler))
