import asyncio
import datetime as dt
import random
import uuid

import pytest

from app.handlers.actual_digest_handler import actual_digest_handler
from app.handlers.digest_last_week_handler import digest_last_week_handler
from app.handlers.digest_today_handler import digest_today_handler
from app.handlers.digest_yesterday_handler import digest_yesterday_handler
from app.handlers.info_handler import info_handler
from app.handlers.myid_handler import myid_handler
from app.handlers.register import register_basic_handlers
from app.handlers.seed_db_handler import seed_db_handler
from app.handlers.start_handler import start_handler
from app.handlers.update_dates_to_yesterday_handler import update_dates_to_yesterday_handler

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
    def __init__(self, message=None, chat=None):
        self.message = message
        self.effective_chat = chat


class _FakeOrchestrator:
    def __init__(self, result):
        self.collect_calls = []
        self.update_dates_result = 0
        self.update_dates_calls = 0
        self.seed_calls = 0
        self.seed_should_fail = False
        self._result = result

    async def collect_digest(self, date_from=None, date_to=None, update_db_dates=False):
        self.collect_calls.append(
            {"date_from": date_from, "date_to": date_to, "update_db_dates": update_db_dates}
        )
        return self._result

    def update_dates_to_yesterday(self):
        self.update_dates_calls += 1
        return self.update_dates_result

    def run_seed_db(self):
        self.seed_calls += 1
        if self.seed_should_fail:
            raise RuntimeError(f"случайная ошибка {uuid.uuid4()}")


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


async def test_start_handler_returns_help_text_when_message_exists():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random.randint(100, 999), chat_type="private"))

    await start_handler(update, context=None)

    ok = bool(message.replies()) and "/info" in message.replies()[0]
    assert ok, "Failure: start handler did not send the expected help text"


async def test_myid_handler_returns_chat_metadata_for_existing_chat():
    random_chat_id = random.randint(10000, 99999)
    random_chat_type = f"group_{uuid.uuid4().hex[:5]}"
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random_chat_id, chat_type=random_chat_type))

    await myid_handler(update, context=None)

    ok = bool(message.replies()) and str(random_chat_id) in message.replies()[0] and random_chat_type in message.replies()[0]
    assert ok, "Failure: myid handler did not return current chat metadata"


async def test_info_handler_returns_the_command_list_for_user():
    message = _FakeMessage()
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random.randint(1, 999), chat_type="private"))

    await info_handler(update, context=None)

    ok = bool(message.replies()) and "/digest_today" in message.replies()[0] and "/actual_digest" in message.replies()[0]
    assert ok, "Failure: info handler did not return the expected command list"


async def test_digest_today_handler_collects_and_sends_the_today_digest():
    digest_text = f"новость_{uuid.uuid4()}_ñ"
    message = _FakeMessage()
    orchestrator = _FakeOrchestrator(result={"text": digest_text, "errors": [], "messages": []})
    context = _FakeContext(orchestrator=orchestrator)
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random.randint(100, 999), chat_type="private"))

    await digest_today_handler(update, context)

    ok = orchestrator.collect_calls[0]["date_from"] == dt.date.today() and message.replies()[-1] == digest_text
    assert ok, "Failure: digest today handler did not call orchestrator for current date"


async def test_digest_yesterday_handler_cannot_work_without_orchestrator():
    message = _FakeMessage()
    context = _FakeContext(orchestrator=None)
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random.randint(10, 99), chat_type="private"))

    await digest_yesterday_handler(update, context)

    ok = len(message.replies()) == 1
    assert ok, "Failure: digest yesterday handler did not report a failure when orchestrator is missing"


async def test_update_dates_to_yesterday_handler_reports_amount_of_updated_rows():
    message = _FakeMessage()
    orchestrator = _FakeOrchestrator(result={"text": "", "errors": [], "messages": []})
    orchestrator.update_dates_result = random.randint(1, 40)
    context = _FakeContext(orchestrator=orchestrator)
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random.randint(1000, 9999), chat_type="private"))

    await update_dates_to_yesterday_handler(update, context)

    ok = orchestrator.update_dates_calls == 1 and str(orchestrator.update_dates_result) in message.replies()[0]
    assert ok, "Failure: update_dates_to_yesterday handler did not report updated rows"


async def test_seed_db_handler_runs_seed_database_in_background_thread():
    message = _FakeMessage()
    orchestrator = _FakeOrchestrator(result={"text": "", "errors": [], "messages": []})
    context = _FakeContext(orchestrator=orchestrator)
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random.randint(300, 500), chat_type="private"))

    await seed_db_handler(update, context)

    ok = orchestrator.seed_calls == 1 and bool(message.replies())
    assert ok, "Failure: seed_db handler did not trigger background synchronization"


async def test_digest_last_week_handler_collects_range_and_returns_message():
    digest_text = f"дайджест_{uuid.uuid4()}_Привет"
    message = _FakeMessage()
    orchestrator = _FakeOrchestrator(result={"text": digest_text, "errors": [], "messages": []})
    context = _FakeContext(orchestrator=orchestrator)
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random.randint(501, 800), chat_type="private"))

    await digest_last_week_handler(update, context)

    ok = orchestrator.collect_calls[0]["date_from"] == dt.date.today() - dt.timedelta(days=7) and message.replies()[-1] == digest_text
    assert ok, "Failure: last week handler did not request the expected date range"


async def test_actual_digest_handler_enables_date_updates_in_database():
    digest_text = f"актуальный_{uuid.uuid4().hex}_данные"
    message = _FakeMessage()
    orchestrator = _FakeOrchestrator(result={"text": digest_text, "errors": [], "messages": []})
    context = _FakeContext(orchestrator=orchestrator)
    update = _FakeUpdate(message=message, chat=_FakeChat(chat_id=random.randint(900, 1200), chat_type="private"))

    await actual_digest_handler(update, context)

    ok = orchestrator.collect_calls[0]["update_db_dates"] is True and message.replies()[-1] == digest_text
    assert ok, "Failure: actual digest handler did not request DB date update"


async def test_handlers_dont_break_when_called_concurrently():
    suffix = uuid.uuid4().hex[:6]
    message_a = _FakeMessage()
    message_b = _FakeMessage()
    orchestrator = _FakeOrchestrator(result={"text": f"конкурентный_{suffix}_тест", "errors": [], "messages": []})
    context = _FakeContext(orchestrator=orchestrator)
    update_a = _FakeUpdate(message=message_a, chat=_FakeChat(chat_id=random.randint(1, 100), chat_type="private"))
    update_b = _FakeUpdate(message=message_b, chat=_FakeChat(chat_id=random.randint(101, 200), chat_type="private"))

    await asyncio.gather(
        digest_today_handler(update_a, context),
        digest_yesterday_handler(update_b, context),
    )

    ok = len(orchestrator.collect_calls) == 2 and len(message_a.replies()) == 1 and len(message_b.replies()) == 1
    assert ok, "Failure: handlers did not survive concurrent execution"


def test_register_basic_handlers_adds_every_command_handler():
    app = _RecordingApplication()

    register_basic_handlers(app)

    commands = {next(iter(handler.commands)) for handler in app.handlers}
    ok = len(commands) == 9 and "start" in commands and "actual_digest" in commands
    assert ok, "Failure: command registration did not include all required handlers"
