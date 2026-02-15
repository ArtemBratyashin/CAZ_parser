import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


class ExcelFile:
    '''
    Класс работает с эксель файлом и может:
    1) Получать список ссылок в разбивке по источникам
    2) Обновляет данные по дате последней найденной новости
    '''
    def __init__(self, filename: str, data_dir="data") -> None:
        """Сохраняет имя Excel-файла в data/."""
        self._filename = filename
        self._data_dir = Path(data_dir)

    def sources(self) -> List[Dict]:
        """Читает Excel и возвращает только существующие источники (web/vk/tg) как массив словарей."""
        path = (self._data_dir / self._filename).resolve()
        df = pd.read_excel(path) 

        df.columns = [str(c).strip() for c in df.columns]

        required = ["Кафедра", "Контакт", "Сайт", "Вконтакте", "Телеграмм", "Последняя дата"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"В Excel не хватает колонок: {missing}")

        result: List[Dict] = []
        for row in df.to_dict(orient="records"):
            result.extend(self._sources_from_row(row))
        return result

    def _sources_from_row(self, row: Dict) -> List[Dict]:
        """Преобразует одну строку Excel в 0..3 источника, пропуская отсутствующие ссылки."""
        source_name = self._clean_text(row.get("Кафедра"))
        contact = self._clean_text(row.get("Контакт"))
        last_message_date = self._to_iso_date(row.get("Последняя дата"))

        links = [
            (self._clean_link(row.get("Сайт")), "web"),
            (self._clean_link(row.get("Вконтакте")), "vk"),
            (self._clean_link(row.get("Телеграмм")), "tg"),
        ]

        result: List[Dict] = []
        for link, source_type in links:
            src = self._build_source(source_name, contact, last_message_date, link, source_type)
            if src is not None:
                result.append(src)
        return result

    def _build_source(self,source_name: str, contact: str, last_message_date: str, link: Optional[str], source_type: str) -> Optional[Dict]:
        """Создаёт словарь источника или возвращает None, если ссылки нет."""
        if not link:
            return None

        return {
            "source_name": source_name,
            "source_link": link,
            "source_type": source_type,
            "contact": contact,
            "last_message_date": last_message_date,
        }

    def _clean_text(self, val) -> str:
        """Преобразует значение ячейки в строку, превращая NaN/None в пустую строку."""
        if pd.isna(val):
            return ""  # pd.isna распознаёт NaN/NA [web:654]
        return str(val).strip()

    def _clean_link(self, val) -> Optional[str]:
        """Возвращает ссылку или None, если ячейка пустая/NaN/дефис."""
        if pd.isna(val):
            return None  # [web:654]
        s = str(val).strip()
        if not s or s == "-":
            return None
        return s

    def _to_iso_date(self, val) -> str:
        """Нормализует дату к YYYY-MM-DD (date/datetime или строка DD.MM.YYYY), иначе возвращает как есть."""
        if pd.isna(val):
            return ""  # [web:654]

        if isinstance(val, dt.datetime):
            return val.date().strftime("%Y-%m-%d")
        if isinstance(val, dt.date):
            return val.strftime("%Y-%m-%d")

        s = str(val).strip()
        if not s:
            return ""

        try:
            d = dt.datetime.strptime(s, "%d.%m.%Y").date()
            return d.strftime("%Y-%m-%d")
        except ValueError:
            return s
