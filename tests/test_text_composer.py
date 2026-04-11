import asyncio
import random
import uuid

import pytest

from app.parsing.text_composer import TextComposer


def _message(date_text, text):
    token = uuid.uuid4().hex[:6]
    return {
        "source_name": f"Источник_{token}_тест",
        "source_link": f"https://example.com/{token}",
        "contact": f"контакт_{token}",
        "date": date_text,
        "message": text,
    }


def test_compose_returns_header_and_empty_state_when_message_list_is_empty():
    texts = TextComposer(message_len=random.randint(40, 120)).compose(messages=[])
    ok = len(texts) == 1 and "Сообщений нет" in texts[0]
    assert ok, "Failure: compose did not return an empty-state message list"


def test_compose_sorts_messages_by_date_in_descending_order():
    composer = TextComposer(message_len=120)
    texts = composer.compose(messages=[_message("2026-02-10", "старый"), _message("2026-02-11", "новый_ñ")])
    text = "\n".join(texts)
    assert text.find("2026-02-11") == -1 and text.find("11.02.2026") < text.find("10.02.2026"), "Failure: compose did not keep descending date order"


def test_compose_truncates_message_text_to_configured_limit():
    limit = random.randint(8, 14)
    source_text = "абвгдежзийклмнопрстуфхцчшщ"
    text = "\n".join(TextComposer(message_len=limit).compose(messages=[_message("2026-02-11", source_text)]))
    assert source_text[:limit] in text and source_text[: limit + 1] not in text, "Failure: compose did not truncate text by configured length"


def test_compose_removes_markdown_asterisks_from_message_body():
    text = "\n".join(TextComposer(message_len=140).compose(messages=[_message("2026-02-11", "Важная **новость** для кафедры")]))
    assert "*" not in text, "Failure: compose did not remove asterisks from message body"


def test_compose_keeps_raw_date_when_date_format_is_invalid():
    raw_date = f"2026/02/{random.randint(10, 20)}"
    text = "\n".join(TextComposer(message_len=100).compose(messages=[_message(raw_date, "текст")]))
    assert raw_date in text, "Failure: compose did not keep raw date for invalid format"


def test_compose_splits_output_into_chunks_not_longer_than_4000_symbols():
    large_text = "ñ" * 12000
    texts = TextComposer(message_len=12000, max_message_size=4000).compose(messages=[_message("2026-02-11", large_text)])
    ok = len(texts) >= 3 and all(len(text) <= 4000 for text in texts)
    assert ok, "Failure: compose did not split digest text into chunks of 4000 symbols"


@pytest.mark.anyio
async def test_compose_dont_produce_inconsistent_text_under_concurrent_calls():
    composer = TextComposer(message_len=100)
    messages = [_message("2026-02-15", "первая_новость_ñ"), _message("2026-02-14", "вторая_новость")]

    first, second, third = await asyncio.gather(
        asyncio.to_thread(composer.compose, messages),
        asyncio.to_thread(composer.compose, messages),
        asyncio.to_thread(composer.compose, messages),
    )

    ok = first == second == third and isinstance(first, list) and "Источник" in "\n".join(first)
    assert ok, "Failure: compose produced inconsistent output under concurrent calls"
