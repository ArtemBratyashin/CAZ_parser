import datetime as dt
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


class WriterBot:
    '''
    Данный класс отвечает за бота, отправляющего сообщения.
    На вход бот принимает объекты базы данных, парсера и составителя текста.
    Каждый день в определенное сообщение формируется и отправляется в выбранный чат.
    '''

    def __init__(
        self, token: str, chat_id: int, chat_id_errors: int, database, parser, composer, daily_time: dt.time
    ) -> None:
        '''Инициализируем бота'''
        self._token = token
        self._chat_id = chat_id
        self._chat_id_errors = chat_id_errors
        self._database = database
        self._parser = parser
        self._composer = composer
        self._daily_time = daily_time or dt.time(hour=17, minute=0)

    def run(self) -> None:
        '''Запуск бота'''
        application = (
            Application.builder().token(self._token).post_init(self.daily_sender).post_shutdown(self.shutdown).build()
        )
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("myid", self.my_id))
        application.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        '''Отбивка в ответ на /start'''
        if update.message:
            await update.message.reply_text("Привет! Я собираю информацию о кафедрах для КАЯ.")

    async def my_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        '''Отправляет id чата в ответ на /my_id'''
        chat = update.effective_chat
        if update.message and chat:
            await update.message.reply_text(f"📱 Ваш chat_id: {chat.id}\nТип чата: {chat.type}")

    async def daily_sender(self, application: Application) -> None:
        '''Ежедневная отправка сообщения в daily_time'''
        job = application.job_queue.run_daily(
            self._send_digest,
            time=self._daily_time,
            name="daily_digest",
        )
        logger.info("📅 Daily digest scheduled at %s", self._daily_time.isoformat())
        logger.info("📅 Next_run_time=%s", getattr(job, "next_run_time", None))

    async def _send_digest(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        '''Собирает из базы данных список источников, парсит их через parser_manager, составляет сообщение и отправляет в чат'''
        try:
            sources = self._database.sources()
            messages_list, errors = await self._parser.parse(sources)

            if errors:
                error_report = "⚠️ Проблемы при парсинге источников:\n\n" + "\n".join(errors)
                await context.bot.send_message(chat_id=self._chat_id_errors, text=error_report)
                logger.warning("Отчет об ошибках парсинга отправлен в чат ошибок")

            text = self._composer.compose(messages_list)

            await context.bot.send_message(
                chat_id=self._chat_id,
                text=text,
                parse_mode=None,
            )
            logger.info("✅ Ежедневное сообщение отправлено")
            self._database.update_dates(messages=messages_list)

        except Exception:
            logger.exception("❌ Возникла ошибка при отправке ежедневного сообщения")
            await context.bot.send_message(
                chat_id=self._chat_id_errors, text='⚠️ Ошибка при отправке ежедневного сообщения!'
            )

    async def shutdown(self, application: Application) -> None:
        """Корректное завершение: закрываем внешние async-ресурсы."""
        await self._parser.disconnect()
        logger.info("✅ ParserManager disconnected")
