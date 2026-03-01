import os

from dotenv import load_dotenv


class EnvConfig:
    def __init__(self, env_file: str = None) -> None:
        '''Загружает переменные окружения из указанного файла .env или из системных переменных.'''
        load_dotenv(dotenv_path=env_file)

        self._writer_token = self._get_required("WRITER_TOKEN")
        self._chat_id = int(self._get_required("MY_CHAT_ID"))
        self._db_dsn = os.getenv("DB_DSN")
        self._tg_api_id = self._get_required("TG_API_ID")
        self._tg_api_hash = self._get_required("TG_API_HASH")
        self._phone_number = self._get_required("PHONE_NUMBER")
        self._vk_token = self._get_required("VK_TOKEN")

    def _get_required(self, key: str) -> str:
        '''Получает и проверяет переменную окружения.'''
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Переменная окружения {key} отсутствует!")
        return value

    def writer_token(self) -> str:
        return self._writer_token

    def chat_id(self) -> int:
        return self._chat_id

    def db_dsn(self) -> str:
        return self._db_dsn

    def tg_api_id(self) -> int:
        return self._tg_api_id

    def tg_api_hash(self) -> str:
        return self._tg_api_hash

    def phone_number(self) -> str:
        return self._phone_number

    def vk_token(self) -> str:
        return self._vk_token
