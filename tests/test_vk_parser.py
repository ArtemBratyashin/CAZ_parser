import asyncio
import random
import uuid
from datetime import date, datetime

import pytest

from app.parsing.parsers.vk_parser import VkParser

pytestmark = pytest.mark.anyio


def _timestamp(yyyy, mm, dd, hh=10, minute=0, sec=0):
    return int(datetime(yyyy, mm, dd, hh, minute, sec).timestamp())


class _FakeWall:
    def __init__(self, pages):
        self._pages = list(pages)
        self.calls = []

    def get(self, **params):
        self.calls.append(params)
        if self._pages:
            return {"items": self._pages.pop(0)}
        return {"items": []}


class _FakeVkApi:
    def __init__(self, pages):
        self.wall = _FakeWall(pages)


class _ParserWithFailingEnsure(VkParser):
    def __init__(self):
        super().__init__(token="token")

    def _ensure_client(self) -> None:
        raise RuntimeError(f"ошибка_{uuid.uuid4().hex[:6]}")


class _ParserWithStubMethods(VkParser):
    def __init__(self):
        super().__init__(token="token")
        self.ensure_calls = 0

    def _ensure_client(self) -> None:
        self.ensure_calls += 1

    async def _parse_single_group(self, source, date_from=None, date_to=None):
        return [{"source_name": source["source_name"], "date": "2026-02-12", "message": "строка_ñ"}]


def _source(link):
    return {
        "source_name": f"кафедра_{uuid.uuid4().hex[:5]}_ñ",
        "source_link": link,
        "contact": "контакт",
        "last_message_date": date(2026, 2, random.randint(10, 14)),
    }


def test_extract_group_identifier_returns_numeric_value_for_public_url():
    value = VkParser._extract_group_identifier("https://vk.com/public12345")
    assert value == "12345", "Failure: extractor did not parse numeric id from public url"


def test_extract_group_identifier_returns_numeric_value_for_club_url():
    value = VkParser._extract_group_identifier("https://vk.com/club54321/")
    assert value == "54321", "Failure: extractor did not parse numeric id from club url"


def test_extract_group_identifier_returns_domain_for_custom_url():
    value = VkParser._extract_group_identifier(f"https://vk.com/{uuid.uuid4().hex[:6]}")
    assert value.isdigit() is False, "Failure: extractor did not keep custom vk domain value"


async def test_parse_single_group_uses_last_message_date_when_date_from_is_none():
    parser = VkParser(token="token")
    parser._vk = _FakeVkApi(
        pages=[
            [
                {"is_pinned": 1, "date": _timestamp(2026, 2, 17), "text": "пропуск"},
                {"date": _timestamp(2026, 2, 16), "text": "слишком новая"},
                {"date": _timestamp(2026, 2, 15), "text": "  оставить\nэту  "},
                {"date": _timestamp(2026, 2, 13), "text": "остановка"},
            ]
        ]
    )

    source = _source("https://vk.com/public123")
    source["last_message_date"] = date(2026, 2, 14)
    result = await parser._parse_single_group(source, date_from=None, date_to=date(2026, 2, 15))

    ok = len(result) == 1 and result[0]["date"] == "2026-02-15" and result[0]["message"] == "оставить эту"
    assert ok, "Failure: vk parser did not respect last_message_date lower bound"


async def test_parse_single_group_includes_start_boundary_when_date_from_is_explicit():
    parser = VkParser(token="token")
    parser._vk = _FakeVkApi(
        pages=[
            [
                {"date": _timestamp(2026, 2, 15), "text": "d15"},
                {"date": _timestamp(2026, 2, 14), "text": "d14"},
                {"date": _timestamp(2026, 2, 13), "text": "d13"},
                {"date": _timestamp(2026, 2, 12), "text": "d12"},
            ]
        ]
    )

    result = await parser._parse_single_group(
        _source("https://vk.com/public123"),
        date_from=date(2026, 2, 13),
        date_to=date(2026, 2, 15),
    )

    ok = [row["date"] for row in result] == ["2026-02-15", "2026-02-14", "2026-02-13"]
    assert ok, "Failure: vk parser did not include explicit inclusive date_from"


async def test_parse_cannot_continue_when_client_initialization_fails():
    parser = _ParserWithFailingEnsure()
    failed = False
    try:
        await parser.parse([_source("https://vk.com/public123")], date_from=None, date_to=date(2026, 2, 15))
    except RuntimeError:
        failed = True
    assert failed, "Failure: vk parser did not stop after client initialization failure"


async def test_parse_merges_messages_for_all_requested_groups():
    parser = _ParserWithStubMethods()
    result = await parser.parse(
        [_source("https://vk.com/public111"), _source("https://vk.com/public222")],
        date_from=None,
        date_to=None,
    )
    assert parser.ensure_calls == 1 and len(result) == 2, "Failure: vk parser did not merge messages from many groups"


async def test_disconnect_dont_fail_when_called():
    parser = VkParser(token="token")
    await parser.disconnect()
    assert True, "Failure: vk parser disconnect raised an unexpected exception"


async def test_parse_produces_stable_results_during_concurrent_calls():
    parser = _ParserWithStubMethods()
    sources = [_source("https://vk.com/public333")]
    first, second, third = await asyncio.gather(
        parser.parse(sources, date_from=None, date_to=None),
        parser.parse(sources, date_from=None, date_to=None),
        parser.parse(sources, date_from=None, date_to=None),
    )
    ok = len(first) == 1 and len(second) == 1 and len(third) == 1
    assert ok, "Failure: vk parser produced unstable output during concurrent calls"
