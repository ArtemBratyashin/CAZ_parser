import datetime
import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo

# from excel_file import ExcelFile
from config import EnvConfig
from database import Database
from parser_manager import ParserManager
from parsers.tg_parser import TelegramParser
from parsers.vk_parser import VkParser
from text_composer import TextComposer
from writer_bot import WriterBot

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    bot = WriterBot(
        token=EnvConfig().writer_token(),
        chat_id=EnvConfig().chat_id(),
        parser=ParserManager(
            tg_parser=TelegramParser(
                api_id=EnvConfig().tg_api_id(),
                api_hash=EnvConfig().tg_api_hash(),
                phone_number=EnvConfig().phone_number(),
                session_name="user_session",
                max_date=date.today() - timedelta(days=1),
            ),
            vk_parser=VkParser(
                token=EnvConfig().vk_token(), session_name="vk_session", max_date=date.today() - timedelta(days=1)
            ),
            # web_parser=WebsiteParser() необходимо доработать класс для парсинга сайтов
        ),
        composer=TextComposer(message_len=200),
        database=Database(
            dsn=EnvConfig().db_dsn()
        ),  # database=ExcelFile(filename='temp_sources.xlsx'), - для работы через эксель файл
        daily_time=datetime.time(21, 42, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    bot.run()
