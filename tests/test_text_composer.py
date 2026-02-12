import logging
import re

import pytest

from src.text_composer import TextComposer


def test_compose_empty_messages_shows_no_messages_and_stats():
    result = TextComposer(messages=[]).compose()

    # Заголовок есть, но дату не фиксируем — проверяем шаблон
    assert re.search(r"^🎓 СВОДКА НОВОСТЕЙ КАФЕДР \(\d{2}\.\d{2}\.\d{4}\)\n\n", result)

    assert "Сообщений нет.\n\n" in result


def test_compose_none_messages_treated_as_empty():
    result = TextComposer(messages=None).compose()

    assert "Сообщений нет." in result


def test_compose_sorts_by_date_desc():
    messages = [
        {
            "source_name": "Кафедра A",
            "source_link": "https://t.me/a",
            "contact": "A",
            "date": "2026-02-10 09:00:00",
            "message": "old",
        },
        {
            "source_name": "Кафедра B",
            "source_link": "https://t.me/b",
            "contact": "B",
            "date": "2026-02-11 09:00:00",
            "message": "new",
        },
    ]

    result = TextComposer(messages=messages).compose()

    pos_b = result.find("📚 Кафедра B")
    pos_a = result.find("📚 Кафедра A")
    assert pos_b != -1 and pos_a != -1
    assert pos_b < pos_a  # B (новее) должно быть выше


def test_compose_message_is_cut_to_100_chars():
    long_text = "a" * 150
    messages = [
        {
            "source_name": "Физика",
            "source_link": "https://t.me/physics",
            "contact": "Иван",
            "date": "2026-02-11 09:00:00",
            "message": long_text,
        }
    ]

    result = TextComposer(messages=messages).compose()

    assert ("📝 Новость: " + ("a" * 100)) in result
    assert ("a" * 101) not in result


def test_compose_when_message_empty_puts_placeholder():
    messages = [
        {
            "source_name": "Физика",
            "source_link": "https://t.me/physics",
            "contact": "Иван",
            "date": "2026-02-11 09:00:00",
            "message": "   ",
        }
    ]

    result = TextComposer(messages=messages).compose()

    assert "📝 Новость: [нет текста]" in result


def test_compose_date_is_formatted_dd_mm_yyyy():
    messages = [
        {
            "source_name": "Физика",
            "source_link": "https://t.me/physics",
            "contact": "Иван",
            "date": "2026-02-11 09:00:00",
            "message": "hello",
        }
    ]

    result = TextComposer(messages=messages).compose()

    assert "📅 Дата: 11.02.2026" in result