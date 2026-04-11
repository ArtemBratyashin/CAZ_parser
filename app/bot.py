import datetime as dt
import logging
from typing import Any, Dict, List

from telegram.ext import Application, ContextTypes

from app.handlers import register_basic_handlers

logger = logging.getLogger(__name__)


class DigestBotApp:
    """Запускает и обслуживает Telegram-бота."""

    def __init__(
        self,
        token: str,
        chat_id: int,
        chat_id_errors: int,
        orchestrator,
        daily_time: dt.time,
    ) -> None:
        """Сохраняет зависимости и параметры запуска."""
        self._token = token
        self._chat_id = chat_id
        self._chat_id_errors = chat_id_errors
        self._orchestrator = orchestrator
        self._daily_time = daily_time or dt.time(hour=17, minute=0)

    def run(self) -> None:
        """Запускает polling и регистрирует обработчики."""
        application = (
            Application.builder()
            .token(self._token)
            .post_init(self._on_startup)
            .post_shutdown(self._on_shutdown)
            .build()
        )
        application.bot_data["orchestrator"] = self._orchestrator
        register_basic_handlers(application)
        application.run_polling()

    async def _on_startup(self, application: Application) -> None:
        """Ставит ежедневную задачу отправки дайджеста."""
        job = application.job_queue.run_daily(
            self._send_digest,
            time=self._daily_time,
            name="daily_digest",
        )
        logger.info("Daily digest scheduled at %s", self._daily_time.isoformat())
        logger.info("Next run time: %s", getattr(job, "next_run_time", None))

    async def _send_digest(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Собирает дайджест и отправляет его в чаты."""
        try:
            result = await self._orchestrator.collect_digest(
                date_from=None,
                date_to=dt.date.today() - dt.timedelta(days=1),
                update_db_dates=True,
            )

            for report in self._error_reports(result):
                await context.bot.send_message(chat_id=self._chat_id_errors, text=report, parse_mode=None)

            for text in self._digest_texts(result):
                await context.bot.send_message(chat_id=self._chat_id, text=text, parse_mode=None)

            logger.info("Scheduled digest sent")

        except Exception:
            logger.exception("Failed to send scheduled digest")
            await context.bot.send_message(
                chat_id=self._chat_id_errors,
                text="Ошибка при отправке дайджеста по расписанию",
            )

    async def _on_shutdown(self, application: Application) -> None:
        """Закрывает внешние ресурсы оркестратора."""
        await self._orchestrator.disconnect()
        logger.info("Orchestrator disconnected")

    def _digest_texts(self, result: Dict[str, Any]) -> List[str]:
        """Нормализует дайджест к списку сообщений."""
        values = result.get("texts")
        if isinstance(values, list):
            return [value for value in values if isinstance(value, str) and value]

        value = result.get("text")
        if isinstance(value, str) and value:
            return [value]

        return []

    def _error_reports(self, result: Dict[str, Any]) -> List[str]:
        """Собирает отчеты для чата ошибок."""
        stats = result.get("stats") or {}
        stat_message = "\n".join(
            [
                "Статистика парсинга по источникам",
                f"Найдены новости: {stats.get('sources_with_news', 0)}",
                f"Нет новостей: {stats.get('sources_without_news', 0)}",
                f"Не обработались: {stats.get('sources_failed', 0)}",
                f"Нет парсера: {stats.get('sources_without_parser', 0)}",
                f"Всего источников: {stats.get('sources_total', 0)}",
            ]
        )

        reports = [stat_message]
        errors = result.get("errors") or []
        if errors:
            error_block = "Проблемы при парсинге источников:\n\n" + "\n".join(errors)
            reports.append(error_block)

        return reports
