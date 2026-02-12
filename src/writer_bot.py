import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from parsers.tg_parser import TelegramParser
from text_composer import TextComposer

load_dotenv()
TOKEN = os.getenv("WRITER_TOKEN")
CHAT_ID = int(os.getenv("MY_CHAT_ID"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обычный обработчик /start"""
    await update.message.reply_text("Привет! Я собираю информацию о кафедрах для КАЯ.")


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает chat_id текущего чата"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    await update.message.reply_text(f"📱 Ваш chat_id: {chat_id}\n" f"  Тип чата: {chat_type}")


async def send_message_on_startup(application: Application) -> None:
    """Отправляет сообщение при запуске бота"""
    #sources = Database(file = file_path).sources()
    #messages = ParserManager(sources = sources).messages_list()
    messages = await TelegramParser().parse([
        {
            "source_name": "Кафедра теоретической физики",
            "source_link": "https://t.me/theorphys_seminar",
            "contact": "Пример",
            "last_message_date": "2025-09-01",
        }
    ])
    ready_text = TextComposer(messages=messages).compose()
    try:
        await application.bot.send_message(chat_id=CHAT_ID, text=ready_text, parse_mode=None)
        logger.info("✅ Сообщение отправлено")
        # Database(file = ссылка на файл).update_time()
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке: {e}")


def run_bot() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", my_id))
    application.post_init = send_message_on_startup
    application.run_polling()


if __name__ == '__main__':
    run_bot()
