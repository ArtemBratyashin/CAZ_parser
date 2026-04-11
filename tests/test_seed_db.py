import datetime as dt
import random
import uuid

from data.seed_data import DEPARTMENT_SEED_DATA
from data.seed_db import DEFAULT_LAST_NEWS_DATE, _clean_value, _parse_last_news_date


def test_clean_value_cannot_keep_none_input():
    cleaned = _clean_value(None)
    assert cleaned is None, "Failure: clean_value did not return None for None input"


def test_clean_value_dont_keep_blank_text_after_strip():
    noisy = "   \t  \n"
    cleaned = _clean_value(noisy)
    assert cleaned is None, "Failure: clean_value did not collapse blank text to None"


def test_clean_value_returns_trimmed_unicode_text():
    token = f"Пример_{uuid.uuid4().hex[:5]}_ñ"
    cleaned = _clean_value(f"  {token}  ")
    assert cleaned == token, "Failure: clean_value did not return a stripped unicode value"


def test_parse_last_news_date_returns_default_for_empty_marker():
    parsed = _parse_last_news_date("-")
    assert parsed == DEFAULT_LAST_NEWS_DATE, "Failure: parse_last_news_date did not return default date for marker value"


def test_parse_last_news_date_parses_random_iso_string():
    day = random.randint(1, 27)
    value = f"2026-04-{day:02d}"
    parsed = _parse_last_news_date(value)
    assert parsed == dt.date(2026, 4, day), "Failure: parse_last_news_date did not parse valid ISO date"


def test_parse_last_news_date_keeps_existing_date_object():
    value = dt.date(2026, 3, random.randint(1, 28))
    parsed = _parse_last_news_date(value)
    assert parsed == value, "Failure: parse_last_news_date did not preserve date object"


def test_seed_data_contains_non_empty_department_records():
    has_data = len(DEPARTMENT_SEED_DATA) > 0 and any("Ф" in row["name"] for row in DEPARTMENT_SEED_DATA if "name" in row)
    assert has_data, "Failure: seed data list did not contain expected department records"
