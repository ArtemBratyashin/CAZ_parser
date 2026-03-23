import datetime
import logging
from zoneinfo import ZoneInfo

from database import Database
from app.src.parser_manager import ParserManager
from parsers.tg_parser import TelegramParser
from parsers.vk_parser import VkParser
from app.config import Settings
from app.src.text_composer import TextComposer
from app.src.writer_bot import WriterBot

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    settings = Settings()

    tg_parser = TelegramParser(
        api_id=settings.tg_api_id(),
        api_hash=settings.tg_api_hash(),
        phone_number=settings.phone_number(),
        session_name="user_session",
    )

    vk_parser = VkParser(token=settings.vk_token(), session_name="vk_session")

    bot = WriterBot(
        token=settings.writer_token(),
        chat_id=settings.chat_id(),
        chat_id_errors=settings.chat_id_errors(),
        parser=ParserManager(
            tg_parser=tg_parser,
            vk_parser=vk_parser,
            # web_parser=WebsiteParser() необходимо доработать класс для парсинга сайтов
        ),
        composer=TextComposer(message_len=200),
        database=Database(dsn=settings.db_dsn()),
        daily_time=datetime.time(settings.sending_hour(), settings.sending_minute(), tzinfo=ZoneInfo("Europe/Moscow")),
    )

    bot.run()
