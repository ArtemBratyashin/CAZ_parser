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


def test_error_reports_return_separate_stats_and_error_blocks_without_split():
    result = {
        "errors": ["first", "second"],
        "stats": {
            "sources_total": 2,
            "sources_with_news": 1,
            "sources_without_news": 0,
            "sources_failed": 1,
            "sources_without_parser": 0,
        },
    }
    reports = _bot()._error_reports(result)
    ok = len(reports) == 2 and reports[0].startswith("Статистика парсинга") and "first" in reports[1]
    assert ok, "Failure: bot error reports must be returned as plain blocks without text splitting"


def test_digest_texts_returns_text_array_when_result_contains_texts():
    texts = _bot()._digest_texts({"texts": ["первая", "вторая"], "text": "fallback"})
    assert texts == ["первая", "вторая"], "Failure: digest_texts did not preserve ordered text chunks"
