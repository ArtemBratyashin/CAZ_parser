import datetime as dt

from data.seed_data import DEPARTMENT_SEED_DATA
from data.seed_db import DEFAULT_LAST_NEWS_DATE, _clean_value, _parse_last_news_date


def test_clean_value_returns_none_for_empty_values():
    assert _clean_value(None) is None
    assert _clean_value("") is None
    assert _clean_value("   ") is None
    assert _clean_value("-") is None


def test_clean_value_strips_text():
    assert _clean_value("  value  ") == "value"


def test_parse_last_news_date_uses_default_for_empty_values():
    assert _parse_last_news_date(None) == DEFAULT_LAST_NEWS_DATE
    assert _parse_last_news_date("") == DEFAULT_LAST_NEWS_DATE
    assert _parse_last_news_date("   ") == DEFAULT_LAST_NEWS_DATE
    assert _parse_last_news_date("-") == DEFAULT_LAST_NEWS_DATE


def test_parse_last_news_date_parses_iso_dates():
    assert _parse_last_news_date("2026-04-09") == dt.date(2026, 4, 9)


def test_parse_last_news_date_accepts_date_objects():
    value = dt.date(2026, 4, 8)
    assert _parse_last_news_date(value) == value


def test_seed_data_is_not_empty():
    assert DEPARTMENT_SEED_DATA
