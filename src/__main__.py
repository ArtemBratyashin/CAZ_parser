import datetime as dt
import logging
from zoneinfo import ZoneInfo

from config import EnvConfig
from parsers.tg_parser import TelegramParser
from text_composer import TextComposer
from writer_bot import WriterBot

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    bot = WriterBot(
        token=EnvConfig().writer_token(),
        chat_id=EnvConfig().chat_id(),
        parser=TelegramParser(
            api_id=EnvConfig().tg_api_id(),
            api_hash=EnvConfig().tg_api_hash(),
            phone_number=EnvConfig().phone_number(),
            session_name="user_session",
        ),
        composer=TextComposer(),
        database='',
        daily_time=dt.time(17, 00, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    bot.run()
