import asyncio
import random
import uuid
from datetime import date, datetime

import pytest

from app.parsing.parsers.tg_parser import TelegramParser

pytestmark = pytest.mark.anyio


class _FakeMessage:
    def __init__(self, dt_value, text):
        self.date = dt_value
        self.text = text


class _FakeTelegramClient:
    def __init__(self):
        self._connected = True
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
        raise AssertionError(f"unexpected auth request for {phone}")

    async def sign_in(self, *args, **kwargs):
        raise AssertionError("unexpected sign in request")

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


class _ParserWithStubEnsure(TelegramParser):
    def __init__(self, fake_client):
        super().__init__(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")
        self._client = fake_client
        self.ensure_calls = 0

    async def _ensure_client(self):
        self.ensure_calls += 1


class _ParserWithFailingEnsure(TelegramParser):
    def __init__(self):
        super().__init__(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")

    async def _ensure_client(self):
        raise RuntimeError(f"сбой_инициализации_{uuid.uuid4().hex[:6]}")


def _source(link):
    return {
        "source_name": f"кафедра_{uuid.uuid4().hex[:6]}_ñ",
        "source_link": link,
        "contact": "контакт",
        "last_message_date": date(2026, 2, random.randint(10, 14)),
    }


async def test_parse_single_channel_uses_last_message_date_when_date_from_is_not_set():
    parser = TelegramParser(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")
    fake_client = _FakeTelegramClient()
    parser._client = fake_client
    channel_link = f"https://t.me/{uuid.uuid4().hex[:8]}"
    fake_client.set_messages(
        channel_link,
        [
            _FakeMessage(datetime(2026, 2, 16, 10, 0, 0), "слишком новая"),
            _FakeMessage(datetime(2026, 2, 15, 10, 0, 0), "новость один"),
            _FakeMessage(datetime(2026, 2, 14, 10, 0, 0), "новость два"),
            _FakeMessage(datetime(2026, 2, 13, 10, 0, 0), "остановка"),
        ],
    )

    source = _source(channel_link)
    source["last_message_date"] = date(2026, 2, 13)
    result = await parser._parse_single_channel(source, date_from=None, date_to=date(2026, 2, 15))

    assert len(result) == 2, "Failure: parser did not respect last_message_date lower bound"


async def test_parse_single_channel_includes_start_date_when_explicit_date_from_is_provided():
    parser = TelegramParser(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")
    fake_client = _FakeTelegramClient()
    parser._client = fake_client
    channel_link = f"https://t.me/{uuid.uuid4().hex[:8]}"
    fake_client.set_messages(
        channel_link,
        [
            _FakeMessage(datetime(2026, 2, 15, 10, 0, 0), "новость один"),
            _FakeMessage(datetime(2026, 2, 14, 10, 0, 0), "новость два"),
            _FakeMessage(datetime(2026, 2, 13, 10, 0, 0), "новость три"),
            _FakeMessage(datetime(2026, 2, 12, 10, 0, 0), "остановка"),
        ],
    )

    result = await parser._parse_single_channel(_source(channel_link), date_from=date(2026, 2, 13), date_to=date(2026, 2, 15))

    ok = [row["date"] for row in result] == ["2026-02-15", "2026-02-14", "2026-02-13"]
    assert ok, "Failure: parser did not include explicit inclusive date_from boundary"


async def test_parse_calls_ensure_client_and_merges_results_for_many_sources():
    fake_client = _FakeTelegramClient()
    channel_one = f"https://t.me/{uuid.uuid4().hex[:8]}"
    channel_two = f"https://t.me/{uuid.uuid4().hex[:8]}"
    fake_client.set_messages(channel_one, [_FakeMessage(datetime(2026, 2, 15, 10, 0, 0), "новость ñ")])
    fake_client.set_messages(channel_two, [_FakeMessage(datetime(2026, 2, 15, 12, 0, 0), "новость ü")])
    parser = _ParserWithStubEnsure(fake_client=fake_client)

    result = await parser.parse([_source(channel_one), _source(channel_two)], date_from=None, date_to=date(2026, 2, 15))

    ok = parser.ensure_calls == 1 and len(result) == 2
    assert ok, "Failure: parse did not initialize client once and merge source results"


async def test_parse_cannot_continue_when_client_initialization_fails():
    parser = _ParserWithFailingEnsure()
    failed = False

    try:
        await parser.parse([_source(f"https://t.me/{uuid.uuid4().hex[:8]}")], date_from=None, date_to=date(2026, 2, 15))
    except RuntimeError:
        failed = True

    assert failed, "Failure: parse did not fail fast when client initialization failed"


async def test_disconnect_calls_underlying_client_disconnect_once():
    parser = TelegramParser(api_id=1, api_hash="hash", phone_number="+79990000000", session_name="session")
    fake_client = _FakeTelegramClient()
    parser._client = fake_client

    await parser.disconnect()

    assert fake_client.disconnect_calls() == 1, "Failure: disconnect did not call underlying client disconnect"


async def test_parse_dont_break_during_concurrent_runs():
    fake_client = _FakeTelegramClient()
    channel = f"https://t.me/{uuid.uuid4().hex[:8]}"
    fake_client.set_messages(channel, [_FakeMessage(datetime(2026, 2, 15, 8, 0, 0), "многопоточный_тест")])
    parser = _ParserWithStubEnsure(fake_client=fake_client)
    source = _source(channel)

    first, second, third = await asyncio.gather(
        parser.parse([source], date_from=None, date_to=date(2026, 2, 15)),
        parser.parse([source], date_from=None, date_to=date(2026, 2, 15)),
        parser.parse([source], date_from=None, date_to=date(2026, 2, 15)),
    )

    ok = len(first) == 1 and len(second) == 1 and len(third) == 1
    assert ok, "Failure: parser produced unstable results during concurrent runs"
