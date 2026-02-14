import datetime as dt
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


class WriterBot:
    def __init__(self, token: str, chat_id: int, database, parser, composer, daily_time: dt.time) -> None:
        self._token = token
        self._chat_id = chat_id
        self._database = database
        self._parser = parser
        self._composer = composer
        self._daily_time = daily_time or dt.time(hour=17, minute=0)

    def run(self) -> None:
        application = Application.builder().token(self._token).build()
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("myid", self.my_id))
        application.post_init = self.daily_sender
        application.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            await update.message.reply_text("Привет! Я собираю информацию о кафедрах для КАЯ.")

    async def my_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat = update.effective_chat
        if update.message and chat:
            await update.message.reply_text(f"📱 Ваш chat_id: {chat.id}\nТип чата: {chat.type}")

    async def daily_sender(self, application: Application) -> None:
        '''Ежедневная отправка в daily_time'''
        job = application.job_queue.run_daily(
            self._send_digest,
            time=self._daily_time,
            name="daily_digest",
        )
        logger.info("📅 Daily digest scheduled at %s", self._daily_time.isoformat())
        logger.info("📅 Next_run_time=%s", getattr(job, "next_run_time", None))

    async def _send_digest(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            # sources = self._database.sources()
            sources = [
                {
                    "source_name": "Кафедра теоретической физики",
                    "source_link": "https://t.me/theorphys_seminar",
                    "contact": "Пример",
                    "last_message_date": "2025-09-01",
                },
                {
                    "source_name": "Физический факультет",
                    "source_link": "https://t.me/physics_msu_official",
                    "contact": "Пример",
                    "last_message_date": "2026-02-12",
                },
            ]
            messages_list = await self._parser.parse(sources)
            text = self._composer.compose(messages_list)

            await context.bot.send_message(
                chat_id=self._chat_id,
                text=text,
                parse_mode=None,
            )
            logger.info("✅ Daily digest sent")
        except Exception:
            logger.exception("❌ Failed to send daily digest")
