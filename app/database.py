import datetime as dt
import logging
from typing import Dict, List

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

from app.models.department import Department

logger = logging.getLogger(__name__)


class Database:
    """Работает с таблицей источников."""

    def __init__(self, dsn: str) -> None:
        """Создает engine и фабрику сессий."""
        self.engine = create_engine(dsn)
        self.Session = sessionmaker(bind=self.engine)

    def sources(self) -> List[Dict]:
        """Возвращает плоский список источников."""
        with self.Session() as session:
            stmt = select(Department)
            departments = session.scalars(stmt).all()

            result: List[Dict] = []
            for dep in departments:
                links = [
                    (dep.website_url, "web"),
                    (dep.vk_url, "vk"),
                    (dep.tg_url, "tg"),
                ]

                for link, s_type in links:
                    if link and str(link).strip() not in ("", "-"):
                        result.append(
                            {
                                "source_name": dep.name,
                                "source_link": link,
                                "source_type": s_type,
                                "contact": dep.contact,
                                "last_message_date": dep.last_news_date,
                            }
                        )
            return result

    def update_dates(self, messages: List[Dict]) -> None:
        """Обновляет last_news_date по сообщениям."""
        with self.Session() as session:
            for message in messages:
                name = message.get("source_name")
                raw_date = message.get("date")

                if isinstance(raw_date, str):
                    try:
                        new_date = dt.datetime.strptime(raw_date, "%Y-%m-%d").date()
                    except ValueError:
                        logger.error("Неверный формат даты в сообщении: %s", raw_date)
                        continue
                elif isinstance(raw_date, dt.date):
                    new_date = raw_date
                else:
                    logger.warning("Неподдерживаемый тип даты для %s: %s", name, type(raw_date))
                    continue

                stmt = (
                    update(Department)
                    .where(Department.name == name)
                    .where((Department.last_news_date == None) | (Department.last_news_date < new_date))
                    .values(last_news_date=new_date, updated_at=dt.datetime.now(dt.timezone.utc))
                )
                session.execute(stmt)
            session.commit()

    def update_dates_to(self, target_date: dt.date) -> int:
        """Ставит одинаковую дату всем кафедрам."""
        with self.Session() as session:
            stmt = update(Department).values(
                last_news_date=target_date,
                updated_at=dt.datetime.now(dt.timezone.utc),
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount or 0

    def update_dates_to_yesterday(self) -> int:
        """Ставит вчерашнюю дату всем кафедрам."""
        yesterday = dt.date.today() - dt.timedelta(days=1)
        return self.update_dates_to(yesterday)
