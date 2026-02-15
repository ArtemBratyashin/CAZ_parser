import datetime as dt
import random
import string

import pytest

from src.writer_bot import WriterBot


pytestmark = pytest.mark.anyio


def _nonce() -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


class _FakeMessage:
    def __init__(self) -> None:
        self._replies = []

    async def reply_text(self, text: str) -> None:
        self._replies.append(text)

    def replies(self):
        return list(self._replies)


class _FakeChat:
    def __init__(self, chat_id: int, chat_type: str) -> None:
        self.id = chat_id
        self.type = chat_type


class _FakeUpdate:
    def __init__(self, message, chat) -> None:
        self.message = message
        self.effective_chat = chat


class _FakeBot:
    def __init__(self) -> None:
        self._sent = []

    async def send_message(self, chat_id: int, text: str, parse_mode=None) -> None:
        self._sent.append({"chat_id": chat_id, "text": text, "parse_mode": parse_mode})

    def sent(self):
        return list(self._sent)


class _FakeContext:
    def __init__(self, bot: _FakeBot) -> None:
        self.bot = bot


class _FakeJob:
    def __init__(self) -> None:
        self.next_run_time = None


class _FakeJobQueue:
    def __init__(self) -> None:
        self._calls = []

    def run_daily(self, callback, time, name=None, **kwargs):
        self._calls.append({"callback": callback, "time": time, "name": name})
        return _FakeJob()

    def calls(self):
        return list(self._calls)


class _FakeApplication:
    def __init__(self) -> None:
        self.job_queue = _FakeJobQueue()


class _FakeParser:
    def __init__(self, result):
        self._result = result
        self._disconnected = False

    async def parse(self, sources):
        return self._result

    async def disconnect(self) -> None:
        self._disconnected = True

    def is_disconnected(self) -> bool:
        return self._disconnected


class _FakeComposer:
    def __init__(self, text: str) -> None:
        self._text = text
        self._last_messages = None

    def compose(self, messages_list):
        self._last_messages = messages_list
        return self._text

    def last_messages(self):
        return self._last_messages
    
class _FakeDatabase:
    def __init__(self, sources):
        self._sources = sources
        self._updated_messages = None

    def sources(self):
        return list(self._sources)

    def update_dates(self, messages):
        self._updated_messages = list(messages)


async def test_start_replies_greeting_when_message_exists():
    msg = _FakeMessage()
    update = _FakeUpdate(message=msg, chat=_FakeChat(chat_id=1, chat_type="private"))
    bot = WriterBot(
        token=_nonce(),
        chat_id=123,
        database=None,
        parser=_FakeParser([]),
        composer=_FakeComposer("x"),
        daily_time=dt.time(hour=17, minute=0),
    )

    await bot.start(update, context=None)

    assert len(msg.replies()) == 1


async def test_my_id_replies_with_chat_id_and_chat_type():
    chat_id = random.randint(10_000, 99_999)
    chat_type = "group"
    msg = _FakeMessage()
    update = _FakeUpdate(message=msg, chat=_FakeChat(chat_id=chat_id, chat_type=chat_type))
    bot = WriterBot(
        token=_nonce(),
        chat_id=chat_id,
        database=None,
        parser=_FakeParser([]),
        composer=_FakeComposer("x"),
        daily_time=dt.time(hour=17, minute=0),
    )

    await bot.my_id(update, context=None)

    assert str(chat_id) in msg.replies()[0]


async def test_daily_sender_schedules_job_with_given_time_and_name():
    t = dt.time(hour=8, minute=30)
    app = _FakeApplication()
    bot = WriterBot(
        token=_nonce(),
        chat_id=1,
        database=None,
        parser=_FakeParser([]),
        composer=_FakeComposer("x"),
        daily_time=t,
    )

    await bot.daily_sender(app)

    call = app.job_queue.calls()[0]
    assert call["time"] == t


async def test_send_digest_sends_composed_text_to_configured_chat():
    fake_bot = _FakeBot()
    context = _FakeContext(bot=fake_bot)

    db_sources = [
        {
            "source_name": f"кафедра-{_nonce()}",
            "source_link": "https://t.me/x",
            "source_type": "tg",
            "contact": "контакт",
            "last_message_date": "2026-02-01",
        }
    ]
    db = _FakeDatabase(sources=db_sources)

    messages = [{"title": f"новость-{_nonce()}"}]
    parser = _FakeParser(result=messages)

    composer_text = f"дайджест-{_nonce()}"
    composer = _FakeComposer(text=composer_text)

    chat_id = random.randint(10_000, 99_999)
    bot = WriterBot(
        token=_nonce(),
        chat_id=chat_id,
        database=db,
        parser=parser,
        composer=composer,
        daily_time=dt.time(hour=17, minute=0),
    )

    await bot._send_digest(context)

    assert fake_bot.sent()[0]["chat_id"] == chat_id




async def test_shutdown_disconnects_parser_when_disconnect_exists():
    parser = _FakeParser(result=[])
    bot = WriterBot(
        token=_nonce(),
        chat_id=1,
        database=None,
        parser=parser,
        composer=_FakeComposer("x"),
        daily_time=dt.time(hour=17, minute=0),
    )

    await bot.shutdown(application=None)

    assert parser.is_disconnected()
