import re

from app.parsing.text_composer import TextComposer


def test_compose_with_empty_messages_returns_header_and_stats():
    result = TextComposer(message_len=100).compose(messages=[])

    assert re.search(r"\(\d{2}\.\d{2}\.\d{4}\)", result)
    assert "0" in result


def test_compose_with_none_messages_is_treated_as_empty():
    result = TextComposer(message_len=100).compose(messages=None)
    assert re.search(r"\(\d{2}\.\d{2}\.\d{4}\)", result)


def test_compose_sorts_messages_descending_by_date():
    messages = [
        {
            "source_name": "SRC_OLD",
            "source_link": "https://example.com/old",
            "contact": "old",
            "date": "2026-02-10",
            "message": "old",
        },
        {
            "source_name": "SRC_NEW",
            "source_link": "https://example.com/new",
            "contact": "new",
            "date": "2026-02-11",
            "message": "new",
        },
    ]

    result = TextComposer(message_len=100).compose(messages=messages)

    pos_new = result.find("SRC_NEW")
    pos_old = result.find("SRC_OLD")
    assert pos_new != -1 and pos_old != -1
    assert pos_new < pos_old


def test_compose_truncates_message_by_configured_limit():
    messages = [
        {
            "source_name": "SRC",
            "source_link": "https://example.com",
            "contact": "c",
            "date": "2026-02-11",
            "message": "a" * 25,
        }
    ]

    result = TextComposer(message_len=10).compose(messages=messages)

    assert "a" * 10 in result
    assert "a" * 11 not in result


def test_compose_uses_placeholder_when_message_text_is_empty():
    messages = [
        {
            "source_name": "SRC",
            "source_link": "https://example.com",
            "contact": "c",
            "date": "2026-02-11",
            "message": "   ",
        }
    ]

    result = TextComposer(message_len=100).compose(messages=messages)

    assert "[" in result and "]" in result


def test_compose_formats_valid_date_to_dd_mm_yyyy():
    messages = [
        {
            "source_name": "SRC",
            "source_link": "https://example.com",
            "contact": "c",
            "date": "2026-02-11",
            "message": "hello",
        }
    ]

    result = TextComposer(message_len=100).compose(messages=messages)

    assert "11.02.2026" in result


def test_compose_keeps_raw_date_when_format_is_invalid():
    messages = [
        {
            "source_name": "SRC",
            "source_link": "https://example.com",
            "contact": "c",
            "date": "2026/02/11",
            "message": "hello",
        }
    ]

    result = TextComposer(message_len=100).compose(messages=messages)

    assert "2026/02/11" in result
