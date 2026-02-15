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
        """Сохраняет имя Excel-файла в data."""
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
    
    def update_dates(self, messages: List[Dict]) -> None:
        """
        Обновляет 'Последняя дата' в Excel по сообщениям.
        Для каждой кафедры (source_name) берёт максимальную дату из messages и записывает её в строку кафедры.
        """
        updates = self._collect_updates_by_cafedras(messages)
        if not updates:
            return

        path = (self._data_dir / self._filename).resolve()
        df = pd.read_excel(path)
        df.columns = [str(c).strip() for c in df.columns]

        for i, row in df.iterrows():
            cafedra = self._clean_text(row.get("Кафедра"))
            new_date = updates.get(cafedra)
            if not new_date:
                continue
            df.at[i, "Последняя дата"] = new_date

        df.to_excel(path, index=False)


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
            "last_message_date": last_message_date
        }
    
    def _collect_updates_by_cafedras(self, messages: List[Dict]) -> Dict[str, str]:
        """
        Состаляет список обновлений: source_name -> max(date) в формате YYYY-MM-DD.
        """
        updates: Dict[str, str] = {}

        for m in messages:
            name = self._clean_text(m.get("source_name"))
            date_str = self._to_iso_date(m.get("date"))

            if not name or not date_str:
                continue

            prev = updates.get(name)
            if prev is None:
                updates[name] = date_str
                continue

            if self._to_iso_date(date_str) > self._to_iso_date(prev):
                updates[name] = date_str

        return updates

    def _clean_text(self, val) -> str:
        """Преобразует значение ячейки в строку, превращая NaN/None в пустую строку."""
        if pd.isna(val):
            return ""
        return str(val).strip()

    def _clean_link(self, val) -> Optional[str]:
        """Возвращает ссылку или None, если ячейка пустая/NaN/дефис."""
        if pd.isna(val):
            return None 
        s = str(val).strip()
        if not s or s == "-":
            return None
        return s

    def _to_iso_date(self, val) -> str:
        """Нормализует дату к YYYY-MM-DD или иначе возвращает как есть."""
        if pd.isna(val):
            return ""

        if isinstance(val, dt.datetime):
            return val.date().strftime("%Y-%m-%d")
        if isinstance(val, dt.date):
            return val.strftime("%Y-%m-%d")

        s = str(val).strip()
        if not s:
            return ""

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y"):
            try:
                d = dt.datetime.strptime(s, fmt).date()
                return d.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return s