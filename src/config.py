import os

from dotenv import load_dotenv


class EnvConfig:
    def __init__(self, env_file: str = None) -> None:
        load_dotenv(env_file)

        writer_token = os.getenv("WRITER_TOKEN")
        chat_id = os.getenv("MY_CHAT_ID")
        tg_api_id = os.getenv("TG_API_ID")
        tg_api_hash = os.getenv("TG_API_HASH")
        phone_number = os.getenv("PHONE_NUMBER")
        db_path = os.getenv("DB_PATH", "departments.sqlite3")

        if not writer_token:
            raise ValueError("WRITER_TOKEN is missing")
        if not chat_id:
            raise ValueError("MY_CHAT_ID is missing")
        if not tg_api_id:
            raise ValueError("TG_API_ID is missing")
        if not tg_api_hash:
            raise ValueError("TG_API_HASH is missing")
        if not phone_number:
            raise ValueError("PHONE_NUMBER is missing")

        self._writer_token = writer_token
        self._chat_id = int(chat_id)
        self._db_path = db_path
        self._tg_api_id = int(tg_api_id)
        self._tg_api_hash = tg_api_hash
        self._phone_number = phone_number

    def writer_token(self) -> str:
        return self._writer_token

    def chat_id(self) -> int:
        return self._chat_id

    def db_path(self) -> str:
        return self._db_path

    def tg_api_id(self) -> int:
        return self._tg_api_id

    def tg_api_hash(self) -> str:
        return self._tg_api_hash

    def phone_number(self) -> str:
        return self._phone_number
