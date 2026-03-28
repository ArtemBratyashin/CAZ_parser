from datetime import date, datetime

import pytest

import app.parsing.parsers.tg_parser as tg_module
from app.parsing.parsers.tg_parser import TelegramParser


pytestmark = pytest.mark.anyio


class _FakeMessage:
    def __init__(self, dt_value, text):
        self.date = dt_value
        self.text = text


class _FakeTelegramClient:
    def __init__(self, session_name, api_id, api_hash):
        self._connected = False
        self._authorized = True
        self._disconnect_calls = 0
        self._messages = {}

    async def connect(self):
        self._connected = True

    async def disconnect(self):
        self._disconnect_calls += 1

    async def is_user_authorized(self):
        return self._authorized

    async def send_code_request(self, phone):
        raise AssertionError("unexpected auth call")

    async def sign_in(self, *args, **kwargs):
        raise AssertionError("unexpected auth call")

    def is_connected(self):
        return self._connected

    def set_messages(self, channel_link, messages):
        self._messages[channel_link] = list(messages)

    def iter_messages(self, channel_link, limit=50):
        async def _generator():
            for message in self._messages.get(channel_link, []):
                yield message

        return _generator()

    def disconnect_calls(self):
        return self._disconnect_calls


async def test_ensure_client_creates_and_connects_client(monkeypatch):
    fake_client = _FakeTelegramClient("session", 1, "hash")

    def _factory(session_name, api_id, api_hash):
        return fake_client

    monkeypatch.setattr(tg_module, "TelegramClient", _factory)

    parser = TelegramParser(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")
    await parser._ensure_client()

    assert parser._client is fake_client
    assert fake_client.is_connected() is True


async def test_parse_single_channel_uses_last_message_date_when_date_from_is_none():
    parser = TelegramParser(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")
    fake_client = _FakeTelegramClient("session", 1, "hash")
    parser._client = fake_client

    channel_link = "https://t.me/channel_name"
    fake_client.set_messages(
        channel_link,
        [
            _FakeMessage(datetime(2026, 2, 16, 10, 0, 0), "too new"),
            _FakeMessage(datetime(2026, 2, 15, 10, 0, 0), "new one"),
            _FakeMessage(datetime(2026, 2, 14, 10, 0, 0), "new two"),
            _FakeMessage(datetime(2026, 2, 13, 10, 0, 0), "old stop"),
        ],
    )

    source = {
        "source_name": "department",
        "source_link": channel_link,
        "contact": "contact",
        "last_message_date": date(2026, 2, 13),
    }

    result = await parser._parse_single_channel(source, date_from=None, date_to=date(2026, 2, 15))

    assert len(result) == 2
    assert result[0]["date"] == "2026-02-15"
    assert result[1]["date"] == "2026-02-14"


async def test_parse_single_channel_uses_explicit_date_from_inclusive():
    parser = TelegramParser(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")
    fake_client = _FakeTelegramClient("session", 1, "hash")
    parser._client = fake_client

    channel_link = "https://t.me/channel_name"
    fake_client.set_messages(
        channel_link,
        [
            _FakeMessage(datetime(2026, 2, 15, 10, 0, 0), "new one"),
            _FakeMessage(datetime(2026, 2, 14, 10, 0, 0), "new two"),
            _FakeMessage(datetime(2026, 2, 13, 10, 0, 0), "keep by inclusive"),
            _FakeMessage(datetime(2026, 2, 12, 10, 0, 0), "stop"),
        ],
    )

    source = {
        "source_name": "department",
        "source_link": channel_link,
        "contact": "contact",
        "last_message_date": date(2026, 2, 1),
    }

    result = await parser._parse_single_channel(source, date_from=date(2026, 2, 13), date_to=date(2026, 2, 15))

    assert [row["date"] for row in result] == ["2026-02-15", "2026-02-14", "2026-02-13"]


async def test_parse_reraises_when_client_initialization_fails(monkeypatch):
    parser = TelegramParser(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")

    async def _boom():
        raise RuntimeError("failed to init client")

    monkeypatch.setattr(parser, "_ensure_client", _boom)

    with pytest.raises(RuntimeError, match="failed to init client"):
        await parser.parse(
            [{"source_name": "x", "source_link": "https://t.me/x", "contact": "c", "last_message_date": date(2026, 2, 1)}],
            date_from=None,
            date_to=date(2026, 2, 15),
        )


async def test_disconnect_calls_client_disconnect():
    parser = TelegramParser(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")
    fake_client = _FakeTelegramClient("session", 1, "hash")
    parser._client = fake_client

    await parser.disconnect()

    assert fake_client.disconnect_calls() == 1
