import datetime as dt
import logging

from telegram.ext import Application, ContextTypes

from app.handlers import register_basic_handlers

logger = logging.getLogger(__name__)


class DigestBotApp:
    """
    Telegram bot runtime: handlers + scheduled digest delivery.
    """

    def __init__(
        self,
        token: str,
        chat_id: int,
        chat_id_errors: int,
        orchestrator,
        daily_time: dt.time,
    ) -> None:
        self._token = token
        self._chat_id = chat_id
        self._chat_id_errors = chat_id_errors
        self._orchestrator = orchestrator
        self._daily_time = daily_time or dt.time(hour=17, minute=0)

    def run(self) -> None:
        application = (
            Application.builder()
            .token(self._token)
            .post_init(self._on_startup)
            .post_shutdown(self._on_shutdown)
            .build()
        )
        register_basic_handlers(application)
        application.run_polling()

    async def _on_startup(self, application: Application) -> None:
        job = application.job_queue.run_daily(
            self._send_digest,
            time=self._daily_time,
            name="daily_digest",
        )
        logger.info("Daily digest scheduled at %s", self._daily_time.isoformat())
        logger.info("Next run time: %s", getattr(job, "next_run_time", None))

    async def _send_digest(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            result = await self._orchestrator.collect_digest(
                date_from=None,
                date_to=dt.date.today() - dt.timedelta(days=1),
                update_db_dates=True,
            )

            if result["errors"]:
                await context.bot.send_message(
                    chat_id=self._chat_id_errors,
                    text="Проблемы при парсинге источников:\n\n" + "\n".join(result["errors"]),
                )

            await context.bot.send_message(chat_id=self._chat_id, text=result["text"], parse_mode=None)
            logger.info("Scheduled digest sent")

        except Exception:
            logger.exception("Failed to send scheduled digest")
            await context.bot.send_message(
                chat_id=self._chat_id_errors,
                text="Ошибка при отправке дайджеста по расписанию",
            )

    async def _on_shutdown(self, application: Application) -> None:
        await self._orchestrator.disconnect()
        logger.info("Orchestrator disconnected")
