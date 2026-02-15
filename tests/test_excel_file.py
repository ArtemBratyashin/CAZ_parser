import datetime as dt
import random
import string

import pandas as pd
import pytest

import src.excel_file as m
from src.excel_file import ExcelFile


def _nonce() -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


def _df_ok():
    return pd.DataFrame(
        [
            {
                "Кафедра": "ФФ МГУ (официальные ресурсы)",
                "Отделение": "Факультет",
                "Контакт": "A",
                "Сайт": "https://www.phys.msu.ru",
                "Вконтакте": "https://vk.com/ff_mgu",
                "Телеграмм": "https://t.me/physics_msu_official",
                "Последняя дата": "13.02.2026",
            },
            {
                "Кафедра": "Теоретической физики",
                "Отделение": "Экспериментальной и ТА",
                "Контакт": "A",
                "Сайт": "https://theorphys.phys.msu.ru",
                "Вконтакте": "-",
                "Телеграмм": "http://t.me/theorphys_seminar",
                "Последняя дата": "01.09.2025",
            },
        ]
    )


def test_sources_raises_when_required_columns_are_missing(monkeypatch):
    monkeypatch.setattr(m.pd, "read_excel", lambda path: pd.DataFrame([{"Кафедра": "X"}]))

    with pytest.raises(ValueError):
        ExcelFile(filename=f"{_nonce()}.xlsx").sources()


def test_sources_returns_only_existing_links():
    excel = ExcelFile(filename=f"{_nonce()}.xlsx")
    row = {
        "Кафедра": "Кафедра X",
        "Контакт": "Контакт",
        "Сайт": "-",
        "Вконтакте": None,
        "Телеграмм": "https://t.me/x",
        "Последняя дата": "13.02.2026",
    }

    assert len(excel._sources_from_row(row)) == 1


def test_sources_maps_source_types_correctly():
    excel = ExcelFile(filename=f"{_nonce()}.xlsx")
    row = {
        "Кафедра": "Кафедра X",
        "Контакт": "Контакт",
        "Сайт": "https://example.org",
        "Вконтакте": "https://vk.com/x",
        "Телеграмм": "https://t.me/x",
        "Последняя дата": "13.02.2026",
    }

    result = excel._sources_from_row(row)

    assert {r["source_type"] for r in result} == {"web", "vk", "tg"}


def test_sources_normalizes_last_message_date_to_iso():
    excel = ExcelFile(filename=f"{_nonce()}.xlsx")
    row = {
        "Кафедра": "Кафедра X",
        "Контакт": "Контакт",
        "Сайт": "https://example.org",
        "Вконтакте": "-",
        "Телеграмм": "-",
        "Последняя дата": "13.02.2026",
    }

    result = excel._sources_from_row(row)

    assert result[0]["last_message_date"] == "2026-02-13"


def test_update_dates_does_nothing_when_no_updates(monkeypatch):
    df = _df_ok()

    def _read_excel(path):
        return df.copy()

    saved = {"called": False}

    def _to_excel(self, path, index=False):
        saved["called"] = True

    monkeypatch.setattr(m.pd, "read_excel", _read_excel)
    monkeypatch.setattr(pd.DataFrame, "to_excel", _to_excel)

    ExcelFile(filename=f"{_nonce()}.xlsx").update_dates(messages=[])

    assert saved["called"] is False


def test_update_dates_updates_last_date_for_cafedra(monkeypatch):
    df = _df_ok()

    def _read_excel(path):
        return df.copy()

    saved = {"df": None}

    def _to_excel(self, path, index=False):
        saved["df"] = self.copy()

    monkeypatch.setattr(m.pd, "read_excel", _read_excel)
    monkeypatch.setattr(pd.DataFrame, "to_excel", _to_excel)

    messages = [
        {
            "source_name": "Теоретической физики",
            "source_link": "http://t.me/theorphys_seminar",
            "date": "2026-02-15 10:00:00",
        }
    ]

    ExcelFile(filename=f"{_nonce()}.xlsx").update_dates(messages=messages)

    updated = saved["df"].loc[saved["df"]["Кафедра"] == "Теоретической физики", "Последняя дата"].iloc[0]
    assert updated == "2026-02-15"


def test_collect_updates_keeps_max_date_per_cafedra():
    excel = ExcelFile(filename=f"{_nonce()}.xlsx")

    messages = [
        {"source_name": "Кафедра X", "date": "2026-02-01 00:00:00"},
        {"source_name": "Кафедра X", "date": "2026-02-10 00:00:00"},
        {"source_name": "Кафедра X", "date": "2026-02-05 00:00:00"},
    ]

    assert excel._collect_updates_by_cafedras(messages)["Кафедра X"] == "2026-02-10"
