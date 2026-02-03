import asyncio
import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.parsers.tg_parser import get_last_message_tg

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
    # sources = Database(file = ссылка на файл).sources() -- возвращает массив из словарей с названием, ссылкой, контактом и последней датой
    # messages = ParserManager(sources = sources).messages_list() -- возвращет масси изсловарей с названием, ссылкой, контактом, текстом и датой
    ready_text = await MessageComposer(messages=messages).compose()
    try:
        await application.bot.send_message(chat_id=CHAT_ID, text=ready_text, parse_mode='Markdown')
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
