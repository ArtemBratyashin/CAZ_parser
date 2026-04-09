import datetime as dt
import os
import sys
from typing import Any, Dict, Iterable, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config import Settings
from app.models.department import Department
from data.seed_data import DEPARTMENT_SEED_DATA

DEFAULT_LAST_NEWS_DATE = dt.date(2026, 1, 1)


def _clean_value(value: Any) -> Optional[str]:
    """Нормализует строковые поля и превращает пустые/дефис в None."""
    if value is None:
        return None

    text = str(value).strip()
    if text in ("", "-"):
        return None

    return text


def _parse_last_news_date(value: Any) -> dt.date:
    """Преобразует дату новости в date. Пустые значения заполняет дефолтом."""
    if value is None:
        return DEFAULT_LAST_NEWS_DATE

    if isinstance(value, dt.datetime):
        return value.date()

    if isinstance(value, dt.date):
        return value

    text = str(value).strip()
    if text in ("", "-"):
        return DEFAULT_LAST_NEWS_DATE

    try:
        return dt.datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return DEFAULT_LAST_NEWS_DATE


def seed_database(
    seed_data: Optional[Iterable[Dict[str, Any]]] = None,
    dsn: Optional[str] = None,
) -> Dict[str, int]:
    """Синхронизирует таблицу departments из Python-списка данных."""
    dsn_to_use = dsn
    if not dsn_to_use:
        config = Settings()
        dsn_to_use = config.db_dsn()

    if not dsn_to_use:
        raise ValueError("DB_DSN не задан. Невозможно выполнить /seed_db")
    if isinstance(dsn_to_use, str) and ":***@" in dsn_to_use:
        raise ValueError(
            "DB_DSN передан в замаскированном виде (***). "
            "Передайте полный DSN с реальным паролем."
        )

    engine = create_engine(dsn_to_use)
    Session = sessionmaker(bind=engine)

    rows = list(DEPARTMENT_SEED_DATA if seed_data is None else seed_data)

    count_added = 0
    count_updated = 0

    with Session() as session:
        for row in rows:
            name = _clean_value(row.get("name"))
            if name is None:
                continue

            payload = {
                "contact": _clean_value(row.get("contact")),
                "website_url": _clean_value(row.get("website_url")),
                "vk_url": _clean_value(row.get("vk_url")),
                "tg_url": _clean_value(row.get("tg_url")),
                "last_news_date": _parse_last_news_date(row.get("last_news_date")),
            }

            stmt = select(Department).where(Department.name == name)
            existing_dep = session.execute(stmt).scalar_one_or_none()

            if existing_dep is None:
                session.add(Department(name=name, **payload))
                count_added += 1
                continue

            for field, value in payload.items():
                setattr(existing_dep, field, value)
            count_updated += 1

        session.commit()

    result = {
        "added": count_added,
        "updated": count_updated,
        "total": count_added + count_updated,
    }

    print("Синхронизация завершена!")
    print(f"Добавлено: {result['added']}, Обновлено: {result['updated']}")

    return result


if __name__ == "__main__":
    seed_database()
