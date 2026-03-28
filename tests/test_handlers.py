import datetime as dt

import pytest

from app.handlers.basic import (
    digest_today_handler,
    digest_yesterday_handler,
    info_handler,
    myid_handler,
    register_basic_handlers,
    start_handler,
)


pytestmark = pytest.mark.anyio


class _FakeMessage:
    def __init__(self):
        self._replies = []

    async def reply_text(self, text):
        self._replies.append(text)

    def replies(self):
        return list(self._replies)


class _FakeChat:
    def __init__(self, chat_id=1, chat_type="private"):
        self.id = chat_id
        self.type = chat_type


class _FakeUpdate:
    def __init__(self, message=None, chat=None):
        self.message = message
        self.effective_chat = chat


class _FakeOrchestrator:
    def __init__(self, result=None):
        self.collect_calls = []
        self._result = result or {"text": "digest", "errors": [], "messages": []}

    async def collect_digest(self, date_from=None, date_to=None, update_db_dates=False):
        self.collect_calls.append(
            {"date_from": date_from, "date_to": date_to, "update_db_dates": update_db_dates}
        )
        return self._result


class _FakeContext:
    class _App:
        def __init__(self, orchestrator=None):
            self.bot_data = {}
            if orchestrator is not None:
                self.bot_data["orchestrator"] = orchestrator

    def __init__(self, orchestrator=None):
        self.application = self._App(orchestrator=orchestrator)


class _RecordingApplication:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)


async def test_start_handler_replies_greeting():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat())

    await start_handler(update, context=None)

    assert "Привет" in message.replies()[0]


async def test_start_handler_skips_when_message_is_missing():
    update = _FakeUpdate(message=None, chat=_FakeChat())

    await start_handler(update, context=None)


async def test_myid_handler_replies_chat_data():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=777, chat_type="group"))

    await myid_handler(update, context=None)

    reply = message.replies()[0]
    assert "777" in reply
    assert "group" in reply


async def test_myid_handler_skips_when_chat_is_missing():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=None)

    await myid_handler(update, context=None)

    assert message.replies() == []


async def test_info_handler_contains_all_commands():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat())

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


async def test_digest_today_handler_collects_for_today_without_db_updates():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat())
    orchestrator = _FakeOrchestrator(result={"text": "today digest", "errors": [], "messages": []})
    context = _FakeContext(orchestrator=orchestrator)

    await digest_today_handler(update, context)

    call = orchestrator.collect_calls[0]
    assert call["date_from"] == dt.date.today()
    assert call["date_to"] == dt.date.today()
    assert call["update_db_dates"] is False
    assert message.replies()[-1] == "today digest"


async def test_digest_yesterday_handler_collects_for_yesterday_without_db_updates():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat())
    orchestrator = _FakeOrchestrator(result={"text": "yesterday digest", "errors": [], "messages": []})
    context = _FakeContext(orchestrator=orchestrator)

    await digest_yesterday_handler(update, context)

    call = orchestrator.collect_calls[0]
    yesterday = dt.date.today() - dt.timedelta(days=1)
    assert call["date_from"] == yesterday
    assert call["date_to"] == yesterday
    assert call["update_db_dates"] is False
    assert message.replies()[-1] == "yesterday digest"


async def test_digest_handlers_reply_with_error_when_orchestrator_is_missing():
    message_today = _FakeMessage()
    message_yesterday = _FakeMessage()
    update_today = _FakeUpdate(message=message_today, chat=_FakeChat())
    update_yesterday = _FakeUpdate(message=message_yesterday, chat=_FakeChat())
    context = _FakeContext(orchestrator=None)

    await digest_today_handler(update_today, context)
    await digest_yesterday_handler(update_yesterday, context)

    assert "ошибка" in message_today.replies()[0].lower()
    assert "ошибка" in message_yesterday.replies()[0].lower()


async def test_digest_handler_sends_parser_errors_then_digest_text():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat())
    orchestrator = _FakeOrchestrator(
        result={"text": "digest text", "errors": ["e1", "e2"], "messages": []}
    )
    context = _FakeContext(orchestrator=orchestrator)

    await digest_today_handler(update, context)

    replies = message.replies()
    assert len(replies) == 2
    assert "Ошибки при парсинге" in replies[0]
    assert "e1" in replies[0]
    assert replies[1] == "digest text"


def test_register_basic_handlers_adds_all_commands():
    app = _RecordingApplication()

    register_basic_handlers(app)

    commands = [next(iter(handler.commands)) for handler in app.handlers]
    assert commands == ["start", "myid", "info", "digest_today", "digest_yesterday"]
