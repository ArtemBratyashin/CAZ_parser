import datetime
import logging
from zoneinfo import ZoneInfo

from app.bot import DigestBotApp
from app.config import Settings
from app.database import Database
from app.parsing.orchestrator import DigestOrchestrator
from app.parsing.parser_manager import ParserManager
from app.parsing.parsers.tg_parser import TelegramParser
from app.parsing.parsers.vk_parser import VkParser
from app.parsing.text_composer import TextComposer

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    settings = Settings()

    tg_parser = TelegramParser(
        api_id=settings.tg_api_id(),
        api_hash=settings.tg_api_hash(),
        phone_number=settings.phone_number(),
        session_name="user_session",
    )
    vk_parser = VkParser(token=settings.vk_token(), session_name="vk_session")

    parser_manager = ParserManager(
        tg_parser=tg_parser,
        vk_parser=vk_parser,
    )

    orchestrator = DigestOrchestrator(
        database=Database(dsn=settings.db_dsn()),
        parser_manager=parser_manager,
        composer=TextComposer(message_len=200),
    )

    bot_app = DigestBotApp(
        token=settings.writer_token(),
        chat_id=settings.chat_id(),
        chat_id_errors=settings.chat_id_errors(),
        orchestrator=orchestrator,
        daily_time=datetime.time(
            settings.sending_hour(),
            settings.sending_minute(),
            tzinfo=ZoneInfo("Europe/Moscow"),
        ),
    )

    bot_app.run()
