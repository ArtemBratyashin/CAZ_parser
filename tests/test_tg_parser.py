import random
import string

import pytest

import src.parsers.tg_parser as tp
from src.parsers.tg_parser import TelegramParser


pytestmark = pytest.mark.anyio


def _nonce() -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


class _FakeMessage:
    def __init__(self, msg_id: int, date, text: str) -> None:
        self.id = msg_id
        self.date = date
        self.text = text


class _FakeTelegramClient:
    def __init__(self, session_name: str, api_id: int, api_hash: str) -> None:
        self._connected = False
        self._authorized = True
        self._disconnects = 0
        self._messages_by_channel = {}

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._disconnects += 1

    async def is_user_authorized(self) -> bool:
        return self._authorized

    async def send_code_request(self, phone) -> None:
        raise AssertionError("send_code_request must not be called in unit tests")

    async def sign_in(self, *args, **kwargs):
        raise AssertionError("sign_in must not be called in unit tests")

    def set_messages(self, channel: str, messages) -> None:
        self._messages_by_channel[channel] = list(messages)

    def iter_messages(self, channel_username: str, reverse=False):
        async def _gen():
            for m in self._messages_by_channel.get(channel_username, []):
                yield m

        return _gen()

    def is_connected(self) -> bool:
        return self._connected

    def disconnect_calls(self) -> int:
        return self._disconnects


async def test_extract_channel_name_works_for_tme_link():
    assert TelegramParser._extract_channel_name("https://t.me/theorphys_seminar") == "theorphys_seminar"


async def test_ensure_client_creates_client_and_connects(monkeypatch):
    fake_client = _FakeTelegramClient("s", 1, "h")

    def _factory(session_name, api_id, api_hash):
        return fake_client

    monkeypatch.setattr(tp, "TelegramClient", _factory)

    parser = TelegramParser(api_id=1, api_hash="h", phone_number="+79990000000", session_name="s")
    await parser._ensure_client()

    assert parser._client is fake_client


async def test_parse_single_channel_collects_only_messages_newer_than_last_date(monkeypatch):
    fake_client = _FakeTelegramClient("s", 1, "h")

    from datetime import datetime

    channel = "chan"
    fake_client.set_messages(
        channel,
        [
            _FakeMessage(1, datetime(2026, 2, 15, 10, 0, 0), "новое 1"),
            _FakeMessage(2, datetime(2026, 2, 14, 10, 0, 0), "новое 2"),
            _FakeMessage(3, datetime(2026, 2, 13, 10, 0, 0), "старое"),  # должно остановить цикл (break)
            _FakeMessage(4, datetime(2026, 2, 16, 10, 0, 0), "не должно дойти"),
        ],
    )

    parser = TelegramParser(api_id=1, api_hash="h", phone_number="+79990000000", session_name="s")
    parser._client = fake_client

    source = {
        "source_name": f"имя-{_nonce()}",
        "source_link": f"https://t.me/{channel}",
        "contact": f"контакт-{_nonce()}",
        "last_message_date": "2026-02-13",
    }

    result = await parser._parse_single_channel(source)

    assert len(result) == 2


async def test_parse_returns_empty_list_when_ensure_client_fails(monkeypatch):
    async def _boom():
        raise RuntimeError(_nonce())

    parser = TelegramParser(api_id=1, api_hash="h", phone_number="+79990000000", session_name="s")
    monkeypatch.setattr(parser, "_ensure_client", _boom)

    assert await parser.parse([{"source_link": "https://t.me/x", "source_name": "x", "contact": "c", "last_message_date": "2026-02-01"}]) == []


async def test_disconnect_sets_client_to_none(monkeypatch):
    fake_client = _FakeTelegramClient("s", 1, "h")
    parser = TelegramParser(api_id=1, api_hash="h", phone_number="+79990000000", session_name="s")
    parser._client = fake_client

    await parser.disconnect()

    assert parser._client is None
