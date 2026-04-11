from app.bot import DigestBotApp


class _FakeOrchestrator:
    async def collect_digest(self, date_from=None, date_to=None, update_db_dates=False):
        return {"texts": ["ok"], "errors": [], "stats": {}}

    async def disconnect(self):
        return None


def _bot():
    return DigestBotApp(
        token="token",
        chat_id=1,
        chat_id_errors=2,
        orchestrator=_FakeOrchestrator(),
        daily_time=None,
    )


def test_error_reports_include_required_source_statistics():
    result = {
        "errors": [],
        "stats": {
            "sources_total": 10,
            "sources_with_news": 3,
            "sources_without_news": 4,
            "sources_failed": 2,
            "sources_without_parser": 1,
        },
    }
    reports = _bot()._error_reports(result)
    message = "\n".join(reports)
    ok = "Найдены новости: 3" in message and "Нет парсера: 1" in message and "Не обработались: 2" in message
    assert ok, "Failure: bot did not include required parsing statistics in error report"


def test_split_text_cannot_return_parts_longer_than_limit():
    parts = _bot()._split_text("x" * 9000, limit=4000)
    ok = len(parts) == 3 and all(len(part) <= 4000 for part in parts)
    assert ok, "Failure: split_text did not enforce the 4000-symbol limit"


def test_digest_texts_returns_text_array_when_result_contains_texts():
    texts = _bot()._digest_texts({"texts": ["первая", "вторая"], "text": "fallback"})
    assert texts == ["первая", "вторая"], "Failure: digest_texts did not preserve ordered text chunks"
