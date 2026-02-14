import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class TextComposer:
    '''
    Формирует итоговое сообщение из массива новостей.
    Принимает массив словарей с новостями и составляет отформатированное
    сообщение для отправки в Telegram.
    '''

    def __init__(self, message_len: int = 100) -> None:
        '''Инициализируем составитель текста'''
        self._message_len = message_len

    def compose(self, messages: List[Dict]) -> str:
        '''Составляет итоговое сообщение из всех новостей. Для каждой новости форматирует внешний вид и в конце подводит статистику.'''
        try:
            today = datetime.now().strftime("%d.%m.%Y")
            header = f"🎓 СВОДКА НОВОСТЕЙ КАФЕДР ({today})\n\n"

            if not messages:
                text = header + "Сообщений нет.\n\n" + self._format_statistics([])
                logger.info("✅ Сообщение составлено: сообщений нет")
                return text

            sorted_messages = self._sort_by_date(messages)

            text = header
            for msg in sorted_messages:
                text += self._format_message(msg)
                text += "\n"

            text += self._format_statistics(sorted_messages)

            logger.info(f"✅ Сообщение составлено. Размер: {len(text)} символов")
            return text

        except Exception as e:
            logger.error(f"❌ Ошибка при составлении сообщения: {e}")
            return "❌ Ошибка при составлении сообщения"

    def _sort_by_date(self, messages) -> List[Dict]:
        '''Сортирует сообщения по дате, чтобы новые были первыми.'''
        try:
            sorted_list = sorted(
                messages,
                key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"),
                reverse=True,
            )
            logger.info("📊 Сообщения отсортированы по дате")
            return sorted_list
        except Exception as e:
            logger.error(f"⚠️ Ошибка при сортировке: {e}, вернул оригинальный список")
            return messages

    def _format_message(self, msg: Dict) -> str:
        '''Форматирует одну новость в красивый вид (только первые 100 символов).'''
        try:
            message_date = datetime.strptime(msg["date"], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
        except (ValueError, KeyError, TypeError):
            message_date = msg.get("date", "неизвестно")

        raw = (msg.get("message") or "").strip()
        raw = " ".join(raw.split())
        preview = raw[: self._message_len] if raw else "[нет текста]"

        formatted = (
            f"---------\n📚 {msg.get('source_name', '—')}\n"
            f"🔗 Источник: {msg.get('source_link', '—')}\n"
            f"👤 Контакт: {msg.get('contact', '—')}\n"
            f"📅 Дата: {message_date}\n"
            f"📝 Новость: {preview}\n---------\n"
        )
        return formatted

    def _format_statistics(self, messages) -> str:
        '''Формирует статистику по количеству новостей.'''
        total = len(messages)
        return f"---------\n✅ Всего новостей: {total}\n"
