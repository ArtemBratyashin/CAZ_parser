import datetime as dt
import logging
from typing import Dict, List

from models.department import Department
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class Database:
    '''
    Класс для работы с базой данных. Он использует SQLAlchemy для взаимодействия с базой данных.
    '''

    def __init__(self, dsn: str) -> None:
        '''Принимает DSN (строку подключения) при инициализации.'''
        self.engine = create_engine(dsn)
        self.Session = sessionmaker(bind=self.engine)

    def sources(self) -> List[Dict]:
        '''Возвращает список источников из БД.'''
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
        '''Обновляет даты новостей и время последнего прохода бота.'''
        with self.Session() as session:
            for m in messages:
                name = m.get("source_name")
                raw_date = m.get("date")

                if isinstance(raw_date, str):
                    try:
                        new_date = dt.datetime.strptime(raw_date, "%Y-%m-%d").date()
                    except ValueError:
                        logger.error(f"❌ Неверный формат даты в сообщении: {raw_date}")
                        continue
                elif isinstance(raw_date, dt.date):
                    new_date = raw_date
                else:
                    logger.warning(f"⚠️ Неподдерживаемый тип даты для {name}: {type(raw_date)}")
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
        '''Обновляет last_news_date для всех кафедр на указанную дату. Возвращает количество затронутых строк.'''
        with self.Session() as session:
            stmt = update(Department).values(
                last_news_date=target_date,
                updated_at=dt.datetime.now(dt.timezone.utc),
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount or 0

    def update_dates_to_yesterday(self) -> int:
        '''Обновляет даты новостей для всех кафедр на вчерашнюю дату.'''
        yesterday = dt.date.today() - dt.timedelta(days=1)
        return self.update_dates_to(yesterday)
