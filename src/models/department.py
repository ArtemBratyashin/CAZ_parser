from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Date, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    contact: Mapped[Optional[str]] = mapped_column(String(255))
    website_url: Mapped[Optional[str]] = mapped_column(String(255))
    vk_url: Mapped[Optional[str]] = mapped_column(String(255))
    tg_url: Mapped[Optional[str]] = mapped_column(String(255))
    last_news_date: Mapped[Optional[date]] = mapped_column(Date)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Department(name={self.name!r}, last_news={self.last_news_date})>"