import datetime as dt

import pytest

from app.bot import DigestBotApp
from app.handlers.basic import info_handler, myid_handler, start_handler
from app.parsing.orchestrator import DigestOrchestrator


pytestmark = pytest.mark.anyio


class _FakeMessage:
    def __init__(self):
        self._replies = []

    async def reply_text(self, text):
        self._replies.append(text)

    def replies(self):
        return list(self._replies)


class _FakeChat:
    def __init__(self, chat_id, chat_type):
        self.id = chat_id
        self.type = chat_type


class _FakeUpdate:
    def __init__(self, message, chat):
        self.message = message
        self.effective_chat = chat


class _FakeBot:
    def __init__(self):
        self._sent = []

    async def send_message(self, chat_id, text, parse_mode=None):
        self._sent.append({"chat_id": chat_id, "text": text, "parse_mode": parse_mode})

    def sent(self):
        return list(self._sent)


class _FakeContext:
    def __init__(self, bot):
        self.bot = bot


class _FakeJob:
    def __init__(self):
        self.next_run_time = None


class _FakeJobQueue:
    def __init__(self):
        self._calls = []

    def run_daily(self, callback, time, name=None, **kwargs):
        self._calls.append({"callback": callback, "time": time, "name": name})
        return _FakeJob()

    def calls(self):
        return list(self._calls)


class _FakeApplication:
    def __init__(self):
        self.job_queue = _FakeJobQueue()


class _FakeOrchestrator:
    def __init__(self, result=None, raise_on_collect=False):
        self._result = result or {"text": "digest", "errors": [], "messages": []}
        self._raise_on_collect = raise_on_collect
        self.collect_calls = []
        self.disconnected = False

    async def collect_digest(self, date_from=None, date_to=None, update_db_dates=False):
        self.collect_calls.append(
            {"date_from": date_from, "date_to": date_to, "update_db_dates": update_db_dates}
        )
        if self._raise_on_collect:
            raise RuntimeError("collect failed")
        return self._result

    async def disconnect(self):
        self.disconnected = True


class _FakeDatabase:
    def __init__(self, sources):
        self._sources = list(sources)
        self.updated_messages = None

    def sources(self):
        return list(self._sources)

    def update_dates(self, messages):
        self.updated_messages = list(messages)


class _FakeParser:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def parse(self, sources, date_from=None, date_to=None):
        self.calls.append({"sources": list(sources), "date_from": date_from, "date_to": date_to})
        return self.response

    async def disconnect(self):
        return None


class _FakeComposer:
    def __init__(self, text="digest"):
        self.text = text
        self.calls = []

    def compose(self, messages):
        self.calls.append(list(messages))
        return self.text


def _build_bot(orchestrator, daily_time=dt.time(hour=17, minute=0)):
    return DigestBotApp(
        token="token",
        chat_id=1001,
        chat_id_errors=1002,
        orchestrator=orchestrator,
        daily_time=daily_time,
    )


async def test_start_handler_replies_greeting():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=1, chat_type="private"))

    await start_handler(update, context=None)

    assert message.replies() == ["Привет!"]


async def test_myid_handler_replies_chat_info():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=555, chat_type="group"))

    await myid_handler(update, context=None)

    assert "555" in message.replies()[0]


async def test_info_handler_replies_commands_list():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=1, chat_type="private"))

    await info_handler(update, context=None)

    reply = message.replies()[0]
    assert "(/start)" in reply
    assert "(/myid)" in reply
    assert "(/info)" in reply
    assert "(/update_dates_to_yesterday)" in reply
    assert "(/digest_today)" in reply
    assert "(/digest_yesterday)" in reply
    assert "(/digest_last_week)" in reply
    assert "(/actual_digest)" in reply


async def test_on_startup_registers_daily_job():
    app = _FakeApplication()
    bot = _build_bot(orchestrator=_FakeOrchestrator(), daily_time=dt.time(hour=8, minute=30))

    await bot._on_startup(app)

    call = app.job_queue.calls()[0]
    assert call["time"] == dt.time(hour=8, minute=30)
    assert call["name"] == "daily_digest"


async def test_send_scheduled_digest_sends_main_and_error_messages():
    fake_bot = _FakeBot()
    context = _FakeContext(bot=fake_bot)
    orchestrator = _FakeOrchestrator(
        result={"text": "digest text", "errors": ["p1"], "messages": []}
    )
    bot = _build_bot(orchestrator=orchestrator)

    await bot._send_scheduled_digest(context)

    sent = fake_bot.sent()
    assert len(sent) == 2
    assert sent[0]["chat_id"] == 1002
    assert sent[1]["chat_id"] == 1001
    assert orchestrator.collect_calls[0]["update_db_dates"] is True


async def test_send_scheduled_digest_handles_exception_and_notifies_error_chat():
    fake_bot = _FakeBot()
    context = _FakeContext(bot=fake_bot)
    bot = _build_bot(orchestrator=_FakeOrchestrator(raise_on_collect=True))

    await bot._send_scheduled_digest(context)

    sent = fake_bot.sent()
    assert len(sent) == 1
    assert sent[0]["chat_id"] == 1002


async def test_on_shutdown_disconnects_orchestrator():
    orchestrator = _FakeOrchestrator()
    bot = _build_bot(orchestrator=orchestrator)

    await bot._on_shutdown(application=None)

    assert orchestrator.disconnected is True


async def test_orchestrator_collect_digest_uses_parser_and_optional_update_flag():
    messages = [{"source_name": "src", "date": "2026-02-10", "message": "m"}]
    parser = _FakeParser((messages, []))
    composer = _FakeComposer(text="digest text")
    database = _FakeDatabase(sources=[{"source_name": "dep", "source_type": "tg"}])

    orchestrator = DigestOrchestrator(database=database, parser_manager=parser, composer=composer)

    result = await orchestrator.collect_digest(
        date_from=dt.date(2026, 2, 1),
        date_to=dt.date(2026, 2, 10),
        update_db_dates=True,
    )

    assert result["text"] == "digest text"
    assert result["messages"] == messages
    assert parser.calls[0]["date_from"] == dt.date(2026, 2, 1)
    assert parser.calls[0]["date_to"] == dt.date(2026, 2, 10)
    assert database.updated_messages == messages
