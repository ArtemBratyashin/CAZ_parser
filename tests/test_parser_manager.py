import random
import string

import pytest

from src.parser_manager import ParserManager


pytestmark = pytest.mark.anyio


def _nonce() -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


class _GoodParser:
    def __init__(self, tag: str) -> None:
        self._tag = tag

    async def parse(self, sources):
        return [
            {
                "source_name": f"источник-{self._tag}-{_nonce()}",
                "source_link": f"https://example.com/{self._tag}/{_nonce()}",
                "contact": f"контакт-{_nonce()}",
                "date": "2026-02-15 12:34:56",
                "message": f"сообщение-{self._tag}-{_nonce()}",
            }
        ]


class _FailingParser:
    async def parse(self, sources):
        raise RuntimeError(_nonce())


class _DisconnectingParser:
    def __init__(self) -> None:
        self._disconnected = False

    async def parse(self, sources):
        return []

    async def disconnect(self) -> None:
        self._disconnected = True

    def is_disconnected(self) -> bool:
        return self._disconnected


async def test_it_returns_empty_list_when_no_sources_are_given():
    assert await ParserManager(tg_parser=_GoodParser("tg")).parse([]) == []


async def test_it_skips_disabled_parser_when_sources_are_of_that_type():
    sources = [
        {
            "source_name": f"имя-{_nonce()}",
            "source_link": f"https://t.me/{_nonce()}",
            "source_type": "tg",
            "contact": f"контакт-{_nonce()}",
            "last_message_date": "2026-02-01",
        }
    ]

    assert await ParserManager(tg_parser=None).parse(sources) == []


async def test_it_merges_messages_from_multiple_parsers():
    sources = [
        {
            "source_name": f"tg-{_nonce()}",
            "source_link": f"https://t.me/{_nonce()}",
            "source_type": "tg",
            "contact": "не-ASCII контакт",
            "last_message_date": "2026-02-01",
        },
        {
            "source_name": f"vk-{_nonce()}",
            "source_link": f"https://vk.com/{_nonce()}",
            "source_type": "vk",
            "contact": "не-ASCII контакт",
            "last_message_date": "2026-02-01",
        },
        {
            "source_name": f"web-{_nonce()}",
            "source_link": f"https://example.org/{_nonce()}",
            "source_type": "web",
            "contact": "не-ASCII контакт",
            "last_message_date": "2026-02-01",
        },
    ]

    result = await ParserManager(
        tg_parser=_GoodParser("tg"),
        vk_parser=_GoodParser("vk"),
        web_parser=_GoodParser("web"),
    ).parse(sources)

    assert len(result) == 3


async def test_it_ignores_failing_parser_and_returns_messages_from_others():
    sources = [
        {
            "source_name": f"tg-{_nonce()}",
            "source_link": f"https://t.me/{_nonce()}",
            "source_type": "tg",
            "contact": f"контакт-{_nonce()}",
            "last_message_date": "2026-02-01",
        },
        {
            "source_name": f"vk-{_nonce()}",
            "source_link": f"https://vk.com/{_nonce()}",
            "source_type": "vk",
            "contact": f"контакт-{_nonce()}",
            "last_message_date": "2026-02-01",
        },
    ]

    result = await ParserManager(
        tg_parser=_GoodParser("tg"),
        vk_parser=_FailingParser(),
    ).parse(sources)

    assert len(result) == 1


async def test_it_can_disconnect_internal_tg_parser():
    tg = _DisconnectingParser()
    await ParserManager(tg_parser=tg).disconnect()

    assert tg.is_disconnected()
