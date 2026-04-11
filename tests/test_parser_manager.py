import asyncio
import random
import uuid
from datetime import date

import pytest

from app.parsing.parser_manager import ParserManager

pytestmark = pytest.mark.anyio


class _FakeParser:
    def __init__(self, payload):
        self.payload = list(payload)
        self.calls = []
        self.disconnected = False

    async def parse(self, sources, date_from=None, date_to=None):
        self.calls.append({"sources": list(sources), "date_from": date_from, "date_to": date_to})
        return list(self.payload)

    async def disconnect(self):
        self.disconnected = True


class _RaisingParser:
    async def parse(self, sources, date_from=None, date_to=None):
        raise RuntimeError(f"ошибка_{uuid.uuid4()}")

    async def disconnect(self):
        return None


class _UnexpectedParser:
    async def parse(self, sources, date_from=None, date_to=None):
        return {"unexpected": "значение"}

    async def disconnect(self):
        return None


def _source(source_type):
    suffix = uuid.uuid4().hex[:6]
    return {
        "source_name": f"источник_{suffix}_ñ",
        "source_link": f"https://example.com/{suffix}",
        "source_type": source_type,
        "contact": f"контакт_{suffix}",
        "last_message_date": date(2026, 2, random.randint(1, 20)),
    }


async def test_parse_returns_empty_result_when_source_list_is_empty():
    manager = ParserManager(tg_parser=_FakeParser(payload=[]))

    messages, errors, stats = await manager.parse([], date_from=None, date_to=date(2026, 2, 28))

    ok = messages == [] and errors == [] and stats["sources_total"] == 0
    assert ok, "Failure: parser manager did not return an empty result for empty sources"


async def test_parse_merges_messages_from_all_enabled_parsers():
    tg_parser = _FakeParser(payload=[{"source_name": "tg_источник", "date": "2026-02-10", "message": "данные"}])
    vk_parser = _FakeParser(payload=[{"source_name": "vk_источник", "date": "2026-02-11", "message": "данные"}])
    web_parser = _FakeParser(payload=[{"source_name": "web_источник", "date": "2026-02-12", "message": "данные"}])
    manager = ParserManager(tg_parser=tg_parser, vk_parser=vk_parser, web_parser=web_parser)
    sources = [_source("tg"), _source("vk"), _source("web")]

    messages, errors, stats = await manager.parse(sources, date_from=date(2026, 2, 1), date_to=date(2026, 2, 28))

    ok = len(messages) == 3 and errors == [] and stats["sources_total"] == 3
    assert ok, "Failure: parser manager did not merge parser outputs correctly"


async def test_parse_cannot_ignore_runtime_errors_from_internal_parser_tasks():
    manager = ParserManager(tg_parser=_FakeParser(payload=[]), vk_parser=_RaisingParser())
    sources = [_source("tg"), _source("vk")]

    messages, errors, stats = await manager.parse(sources, date_from=None, date_to=date(2026, 2, 15))

    ok = len(messages) == 0 and len(errors) == 1 and stats["sources_failed"] == 1
    assert ok, "Failure: parser manager did not collect parser runtime failures"


async def test_parse_cannot_accept_unexpected_result_type_from_parser():
    manager = ParserManager(tg_parser=_UnexpectedParser())
    sources = [_source("tg")]

    messages, errors, stats = await manager.parse(sources, date_from=None, date_to=date(2026, 2, 15))

    ok = messages == [] and len(errors) == 1 and stats["sources_failed"] == 1
    assert ok, "Failure: parser manager did not flag unexpected parser result type"


async def test_parse_dont_include_unknown_source_types_in_workload():
    tg_parser = _FakeParser(payload=[{"source_name": "ok", "date": "2026-02-10", "message": "строка"}])
    manager = ParserManager(tg_parser=tg_parser)
    sources = [_source("unknown"), _source("tg")]

    messages, errors, stats = await manager.parse(sources, date_from=None, date_to=date(2026, 2, 15))

    ok = len(messages) == 1 and errors == [] and stats["sources_without_parser"] == 1
    assert ok, "Failure: parser manager incorrectly processed unknown source type"


async def test_disconnect_calls_every_available_parser_disconnect():
    tg_parser = _FakeParser(payload=[])
    vk_parser = _FakeParser(payload=[])
    manager = ParserManager(tg_parser=tg_parser, vk_parser=vk_parser)

    await manager.disconnect()

    ok = tg_parser.disconnected and vk_parser.disconnected
    assert ok, "Failure: parser manager did not disconnect all child parsers"


async def test_parse_stays_stable_during_concurrent_calls():
    tg_parser = _FakeParser(payload=[{"source_name": "конкурентно", "date": "2026-02-10", "message": "данные"}])
    manager = ParserManager(tg_parser=tg_parser)
    sources = [_source("tg")]

    first, second, third = await asyncio.gather(
        manager.parse(sources, date_from=None, date_to=date(2026, 2, 15)),
        manager.parse(sources, date_from=None, date_to=date(2026, 2, 15)),
        manager.parse(sources, date_from=None, date_to=date(2026, 2, 15)),
    )

    ok = all(len(result[0]) == 1 and result[1] == [] and result[2]["sources_total"] == 1 for result in [first, second, third])
    assert ok, "Failure: parser manager produced inconsistent results under concurrency"
