from datetime import date, datetime

import pytest

from src.parsers.vk_parser import VkParser


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


def _source(link):
    return {
        "source_name": "department",
        "source_link": link,
        "contact": "contact",
        "last_message_date": date(2026, 2, 13),
    }


def test_extract_group_identifier_handles_public_club_and_domain():
    assert VkParser._extract_group_identifier("https://vk.com/public12345") == "12345"
    assert VkParser._extract_group_identifier("https://vk.com/club54321/") == "54321"
    assert VkParser._extract_group_identifier("https://vk.com/some_domain") == "some_domain"


async def test_parse_single_group_collects_relevant_posts_and_stops_on_old_date():
    parser = VkParser(token="token")
    parser._vk = _FakeVkApi(
        pages=[
            [
                {"is_pinned": 1, "date": _timestamp(2026, 2, 17), "text": "skip pinned"},
                {"date": _timestamp(2026, 2, 16), "text": "too new"},
                {"date": _timestamp(2026, 2, 15), "text": "  keep\nthis  "},
                {"date": _timestamp(2026, 2, 13), "text": "old stop"},
            ],
            [{"date": _timestamp(2026, 2, 12), "text": "must not be fetched"}],
        ]
    )

    result = await parser._parse_single_group(_source("https://vk.com/public123"), max_date=date(2026, 2, 15))

    assert len(result) == 1
    assert result[0]["date"] == "2026-02-15"
    assert result[0]["message"] == "keep this"
    assert len(parser._vk.wall.calls) == 1
    assert parser._vk.wall.calls[0]["owner_id"] == -123


async def test_parse_returns_empty_list_when_client_init_fails(monkeypatch):
    parser = VkParser(token="token")

    def _boom():
        raise RuntimeError("vk init failed")

    monkeypatch.setattr(parser, "_ensure_client", _boom)

    result = await parser.parse([_source("https://vk.com/test")], max_date=date(2026, 2, 15))
    assert result == []


async def test_parse_initializes_client_and_merges_messages(monkeypatch):
    parser = VkParser(token="token")
    state = {"initialized": False}

    def _fake_ensure():
        state["initialized"] = True

    async def _fake_parse_single_group(source, max_date):
        return [{"source_name": source["source_name"], "date": "2026-02-12", "message": "ok"}]

    monkeypatch.setattr(parser, "_ensure_client", _fake_ensure)
    monkeypatch.setattr(parser, "_parse_single_group", _fake_parse_single_group)

    result = await parser.parse([_source("https://vk.com/a"), _source("https://vk.com/b")], max_date=date(2026, 2, 15))

    assert state["initialized"] is True
    assert len(result) == 2


async def test_disconnect_is_noop_and_does_not_fail():
    parser = VkParser(token="token")
    await parser.disconnect()
