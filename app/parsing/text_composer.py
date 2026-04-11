import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class TextComposer:
    """Собирает итоговый текст дайджеста."""

    def __init__(self, message_len: int = 100, max_message_size: int = 4000) -> None:
        """Сохраняет лимиты превью и размера сообщения."""
        self._message_len = message_len
        self._max_message_size = max_message_size

    def compose(self, messages: List[Dict]) -> List[str]:
        """Формирует массив сообщений для отправки в Telegram."""
        try:
            today = datetime.now().strftime("%d.%m.%Y")
            header = f"🎓 СВОДКА НОВОСТЕЙ КАФЕДР ({today})\n\n"

            parts: List[str] = [header]
            if not messages:
                parts.append("Сообщений нет.\n\n")
                parts.append(self._format_statistics([]))
                result = self._pack_parts(parts)
                logger.info("Сообщение составлено: сообщений нет, частей: %s", len(result))
                return result

            sorted_messages = self._sort_by_date(messages)
            for message in sorted_messages:
                parts.append(self._format_message(message))
                parts.append("\n")
            parts.append(self._format_statistics(sorted_messages))

            result = self._pack_parts(parts)
            logger.info("Сообщение составлено. Частей: %s", len(result))
            return result

        except Exception as exc:
            logger.error("Ошибка при составлении сообщения: %s", exc)
            return ["Ошибка при составлении сообщения"]

    def _sort_by_date(self, messages: List[Dict]) -> List[Dict]:
        """Сортирует новости по убыванию даты."""
        try:
            sorted_list = sorted(
                messages,
                key=lambda item: datetime.strptime(item["date"], "%Y-%m-%d"),
                reverse=True,
            )
            logger.info("Сообщения отсортированы по дате")
            return sorted_list
        except Exception as exc:
            logger.error("Ошибка при сортировке: %s", exc)
            return messages

    def _format_message(self, message: Dict) -> str:
        """Форматирует одну новость в блок."""
        try:
            message_date = datetime.strptime(message["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        except (ValueError, KeyError, TypeError):
            message_date = message.get("date", "неизвестно")

        raw = (message.get("message") or "").strip()
        raw = raw.replace("*", "")
        raw = " ".join(raw.split())
        preview = raw[: self._message_len] if raw else "[нет текста]"

        formatted = (
            f"━━━━━━━━━━━━━\n📚 {message.get('source_name', '—')}\n"
            f"🔗 Источник: {message.get('source_link', '—')}\n"
            f"👤 Контакт: {message.get('contact', '—')}\n"
            f"📅 Дата: {message_date}\n"
            f"📝 Новость: {preview}\n━━━━━━━━━━━━━\n"
        )
        return formatted

    def _format_statistics(self, messages: List[Dict]) -> str:
        """Возвращает статистику по количеству новостей."""
        total = len(messages)
        return f"━━━━━━━━━━━━━\n✅ Всего новостей: {total}\n"

    def _pack_parts(self, parts: List[str]) -> List[str]:
        """Укладывает текстовые части в сообщения до лимита."""
        chunks: List[str] = []
        current = ""

        for part in parts:
            for piece in self._split_long_piece(part):
                if not current:
                    current = piece
                    continue

                if len(current) + len(piece) <= self._max_message_size:
                    current += piece
                else:
                    chunks.append(current.rstrip())
                    current = piece

        if current:
            chunks.append(current.rstrip())

        return [chunk for chunk in chunks if chunk] or [""]

    def _split_long_piece(self, piece: str) -> List[str]:
        """Делит длинный кусок по лимиту."""
        if len(piece) <= self._max_message_size:
            return [piece]

        parts: List[str] = []
        left = piece
        while left:
            if len(left) <= self._max_message_size:
                parts.append(left)
                break

            split_at = left.rfind("\n", 0, self._max_message_size + 1)
            if split_at <= 0:
                split_at = self._max_message_size

            parts.append(left[:split_at])
            left = left[split_at:].lstrip("\n")

        return [part for part in parts if part]
