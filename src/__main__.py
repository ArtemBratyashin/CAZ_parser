import datetime as dt
import logging
from zoneinfo import ZoneInfo

from config import EnvConfig
from parser_manager import ParserManager
from parsers.tg_parser import TelegramParser
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
            ),
            # vk_parser=VkParser(), необходимо доработать класс для вк парсинга
            # web_parser=WebsiteParser() необходимо доработать класс для парсинга сайтов
        ),
        composer=TextComposer(message_len=200),
        database='',  # необходимо доработать класс для работы с базой данных
        daily_time=dt.time(20, 54, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    bot.run()
