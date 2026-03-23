from datetime import date

import pytest

from app.src.parser_manager import ParserManager


pytestmark = pytest.mark.anyio


class _RecordingParser:
    def __init__(self, payload):
        self.payload = list(payload)
        self.calls = []

    async def parse(self, sources, max_date):
        self.calls.append({"sources": list(sources), "max_date": max_date})
        return list(self.payload)


class _FailingParser:
    async def parse(self, sources, max_date):
        raise RuntimeError("boom")


class _DisconnectingParser:
    def __init__(self):
        self.disconnected = False

    async def parse(self, sources, max_date):
        return []

    async def disconnect(self):
        self.disconnected = True


def _source(source_type, name):
    return {
        "source_name": name,
        "source_link": f"https://example.com/{name}",
        "source_type": source_type,
        "contact": "contact",
        "last_message_date": date(2026, 2, 1),
    }


async def test_parse_returns_empty_list_when_no_sources():
    parser = _RecordingParser(payload=[])
    result = await ParserManager(tg_parser=parser).parse([], max_date=date(2026, 2, 15))
    assert result == []


async def test_parse_skips_disabled_parser_and_returns_empty_list():
    sources = [_source("tg", "tg_one")]
    result = await ParserManager(tg_parser=None).parse(sources, max_date=date(2026, 2, 15))
    assert result == []


async def test_parse_merges_messages_from_all_enabled_parsers():
    tg = _RecordingParser([{"source_name": "tg", "date": "2026-02-12", "message": "t"}])
    vk = _RecordingParser([{"source_name": "vk", "date": "2026-02-11", "message": "v"}])
    web = _RecordingParser([{"source_name": "web", "date": "2026-02-10", "message": "w"}])

    sources = [_source("tg", "tg_one"), _source("vk", "vk_one"), _source("web", "web_one")]
    max_date = date(2026, 2, 15)

    result = await ParserManager(tg_parser=tg, vk_parser=vk, web_parser=web).parse(sources, max_date=max_date)

    assert isinstance(result, tuple)
    messages, errors = result
    assert len(messages) == 3
    assert errors == []

    assert tg.calls[0]["max_date"] == max_date
    assert vk.calls[0]["max_date"] == max_date
    assert web.calls[0]["max_date"] == max_date
    assert len(tg.calls[0]["sources"]) == 1
    assert len(vk.calls[0]["sources"]) == 1
    assert len(web.calls[0]["sources"]) == 1


async def test_parse_keeps_messages_and_collects_errors_from_failing_parsers():
    tg = _RecordingParser([{"source_name": "tg", "date": "2026-02-12", "message": "ok"}])
    vk = _FailingParser()
    sources = [_source("tg", "tg_one"), _source("vk", "vk_one")]

    messages, errors = await ParserManager(tg_parser=tg, vk_parser=vk).parse(sources, max_date=date(2026, 2, 15))

    assert len(messages) == 1
    assert len(errors) == 1
    assert "boom" in errors[0]


async def test_disconnect_calls_disconnect_on_internal_parsers():
    tg = _DisconnectingParser()
    vk = _DisconnectingParser()
    manager = ParserManager(tg_parser=tg, vk_parser=vk)

    await manager.disconnect()

    assert tg.disconnected is True
    assert vk.disconnected is True
