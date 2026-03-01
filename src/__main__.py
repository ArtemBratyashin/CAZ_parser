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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    config = EnvConfig()

    tg_parser = TelegramParser(
        api_id=config.tg_api_id(),
        api_hash=config.tg_api_hash(),
        phone_number=config.phone_number(),
        session_name="user_session",
    )

    vk_parser = VkParser(token=config.vk_token(), session_name="vk_session")

    bot = WriterBot(
        token=config.writer_token(),
        chat_id=config.chat_id(),
        chat_id_errors=config.chat_id_errors(),
        parser=ParserManager(
            tg_parser=tg_parser,
            vk_parser=vk_parser,
            # web_parser=WebsiteParser() необходимо доработать класс для парсинга сайтов
        ),
        composer=TextComposer(message_len=200),
        database=Database(
            dsn=config.db_dsn()
        ),  # database=ExcelFile(filename='temp_sources.xlsx'), - для работы через эксель файл
        daily_time=datetime.time(22, 24, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    bot.run()
