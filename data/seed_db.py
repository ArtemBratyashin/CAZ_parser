import os
import sys
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.models.department import Department
from src.config import EnvConfig

def parse_date(date_value):
    """Безопасно превращает значение из Excel в объект даты."""
    if pd.isna(date_value) or str(date_value).strip() in ["", "-"]:
        return datetime(2026, 1, 1).date()
        
    if isinstance(date_value, datetime):
        return date_value.date()
        
    try:
        return datetime.strptime(str(date_value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return datetime(2026, 1, 1).date()

def seed_database():
    config = EnvConfig()
    engine = create_engine(config.db_dsn())
    Session = sessionmaker(bind=engine)

    file_path = os.path.join(current_dir, 'temp_sources.xlsx')
    
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл {file_path} не найден!")
        return

    df = pd.read_excel(file_path)
    
    with Session() as session:
        count_added = 0
        count_updated = 0
        
        for _, row in df.iterrows():
            name = str(row['Кафедра']).strip()
            last_date = parse_date(row.get('Последняя дата'))
            
            stmt = select(Department).where(Department.name == name)
            existing_dep = session.execute(stmt).scalar_one_or_none()
            
            if existing_dep:
                existing_dep.website_url = str(row['Сайт']).strip() if pd.notna(row['Сайт']) and row['Сайт'] != '-' else None
                existing_dep.vk_url = str(row['Вконтакте']).strip() if pd.notna(row['Вконтакте']) and row['Вконтакте'] != '-' else None
                existing_dep.tg_url = str(row['Телеграмм']).strip() if pd.notna(row['Телеграмм']) and row['Телеграмм'] != '-' else None
                existing_dep.last_news_date = last_date
                count_updated += 1
            else:
                new_dep = Department(
                    name=name,
                    contact=str(row['Контакт']).strip() if pd.notna(row['Контакт']) else None,
                    website_url=str(row['Сайт']).strip() if pd.notna(row['Сайт']) and row['Сайт'] != '-' else None,
                    vk_url=str(row['Вконтакте']).strip() if pd.notna(row['Вконтакте']) and row['Вконтакте'] != '-' else None,
                    tg_url=str(row['Телеграмм']).strip() if pd.notna(row['Телеграмм']) and row['Телеграмм'] != '-' else None,
                    last_news_date=last_date
                )
                session.add(new_dep)
                count_added += 1
        
        session.commit()
        print(f"Синхронизация завершена!")
        print(f"Добавлено: {count_added}, Обновлено: {count_updated}")

if __name__ == "__main__":
    seed_database()