import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class TextComposer:
    """
    Формирует итоговое сообщение из массива новостей.
    Принимает массив словарей с новостями и составляет красиво отформатированное
    сообщение для отправки в Telegram.
    """

    def __init__(self, messages: List[Dict]):
        """messages: List[Dict] - массив новостей"""
        self.messages = messages

    def compose(self) -> str:
        """Составляет итоговое сообщение из всех новостей."""
        try:
            # Сортируем по дате в убывающем порядке (новые в начале)
            sorted_messages = self._sort_by_date()

            # Формируем заголовок
            today = datetime.now().strftime("%d.%m.%Y")
            text = f"🎓 СВОДКА НОВОСТЕЙ КАФЕДР ({today})\n\n"

            # Добавляем каждую новость
            for msg in sorted_messages:
                text += self._format_message(msg)
                text += "\n"

            # Добавляем статистику
            text += self._format_statistics()

            logger.info(f"✅ Сообщение составлено. Размер: {len(text)} символов")
            return text

        except Exception as e:
            logger.error(f"❌ Ошибка при составлении сообщения: {e}")
            return "❌ Ошибка при составлении сообщения"

    def _sort_by_date(self) -> List[Dict]:
        """Сортирует сообщения по дате в убывающем порядке (новые первыми)."""
        try:
            sorted_list = sorted(
                self.messages,
                key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"),
                reverse=True
            )
            logger.info(f"📊 Сообщения отсортированы по дате")
            return sorted_list
        except Exception as e:
            logger.error(f"⚠️ Ошибка при сортировке: {e}, вернул оригинальный список")
            return self.messages

    def _format_message(self, msg: Dict) -> str:
        """Форматирует одно сообщение в красивый вид."""
        # Извлекаем дату (берём только дату, без времени)
        try:
            message_date = datetime.strptime(msg["date"], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
        except (ValueError, KeyError):
            message_date = msg.get("date", "неизвестно")

        formatted = (
            f"📚 {msg['source_name']}\n"
            f"🔗 Источник: {msg['source_link']}\n"
            f"👤 Контакт: {msg['contact']}\n"
            f"📅 Дата: {message_date}\n"
            f"📝 Новость: {msg['message']}\n"
        )

        return formatted

    def _format_statistics(self) -> str:
        """ Формирует статистику по количеству новостей."""
        total = len(self.messages)
        unique_sources = len(set(msg["source_name"] for msg in self.messages))

        stats = (
            f"---\n"
            f"✅ Всего новостей: {total}\n"
            f"✅ Уникальных кафедр: {unique_sources}\n"
        )

        return stats
