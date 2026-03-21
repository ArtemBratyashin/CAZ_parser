import datetime as dt

import pytest

from src.writer_bot import WriterBot


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


class _FakeParser:
    def __init__(self, result):
        self._result = result
        self._calls = []
        self._disconnected = False

    async def parse(self, sources, max_date):
        self._calls.append({"sources": list(sources), "max_date": max_date})
        return self._result

    async def disconnect(self):
        self._disconnected = True

    def calls(self):
        return list(self._calls)

    def is_disconnected(self):
        return self._disconnected


class _RaisingParser:
    async def parse(self, sources, max_date):
        raise RuntimeError("parse failed")

    async def disconnect(self):
        return None


class _FakeComposer:
    def __init__(self, text):
        self._text = text
        self._last_messages = None

    def compose(self, messages_list):
        self._last_messages = messages_list
        return self._text

    def last_messages(self):
        return self._last_messages


class _FakeDatabase:
    def __init__(self, sources):
        self._sources = list(sources)
        self._updated = None

    def sources(self):
        return list(self._sources)

    def update_dates(self, messages):
        self._updated = list(messages)

    def updated_messages(self):
        return self._updated


def _build_bot(database, parser, composer, daily_time=dt.time(hour=17, minute=0)):
    return WriterBot(
        token="token",
        chat_id=1001,
        chat_id_errors=1002,
        database=database,
        parser=parser,
        composer=composer,
        daily_time=daily_time,
    )


async def test_start_replies_when_message_exists():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=1, chat_type="private"))
    bot = _build_bot(database=None, parser=_FakeParser(([], [])), composer=_FakeComposer("digest"))

    await bot.start(update, context=None)

    assert len(message.replies()) == 1


async def test_my_id_replies_with_chat_information():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=555, chat_type="group"))
    bot = _build_bot(database=None, parser=_FakeParser(([], [])), composer=_FakeComposer("digest"))

    await bot.my_id(update, context=None)

    assert "555" in message.replies()[0]


async def test_daily_sender_registers_daily_digest_job():
    schedule_time = dt.time(hour=8, minute=30)
    app = _FakeApplication()
    bot = _build_bot(
        database=None,
        parser=_FakeParser(([], [])),
        composer=_FakeComposer("digest"),
        daily_time=schedule_time,
    )

    await bot.daily_sender(app)

    call = app.job_queue.calls()[0]
    assert call["time"] == schedule_time
    assert call["name"] == "daily_digest"


async def test_send_digest_sends_error_report_and_main_message_and_updates_dates():
    fake_bot = _FakeBot()
    context = _FakeContext(bot=fake_bot)

    db = _FakeDatabase(
        sources=[
            {
                "source_name": "source",
                "source_link": "https://t.me/source",
                "source_type": "tg",
                "contact": "contact",
                "last_message_date": dt.date(2026, 2, 1),
            }
        ]
    )
    messages = [{"source_name": "source", "date": "2026-02-10", "message": "hello"}]
    parser = _FakeParser((messages, ["parser error"]))
    composer = _FakeComposer("digest text")
    bot = _build_bot(database=db, parser=parser, composer=composer)

    await bot._send_digest(context)

    sent = fake_bot.sent()
    assert len(sent) == 2
    assert sent[0]["chat_id"] == 1002
    assert sent[1]["chat_id"] == 1001
    assert db.updated_messages() == messages
    assert parser.calls()[0]["max_date"] == dt.date.today() - dt.timedelta(days=1)
    assert composer.last_messages() == messages


async def test_send_digest_when_parser_fails_notifies_error_chat():
    fake_bot = _FakeBot()
    context = _FakeContext(bot=fake_bot)

    db = _FakeDatabase(sources=[])
    bot = _build_bot(database=db, parser=_RaisingParser(), composer=_FakeComposer("digest text"))

    await bot._send_digest(context)

    sent = fake_bot.sent()
    assert len(sent) == 1
    assert sent[0]["chat_id"] == 1002


async def test_shutdown_disconnects_parser():
    parser = _FakeParser(([], []))
    bot = _build_bot(database=None, parser=parser, composer=_FakeComposer("digest text"))

    await bot.shutdown(application=None)

    assert parser.is_disconnected() is True
