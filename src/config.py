import os

from dotenv import load_dotenv


class EnvConfig:
    '''
    Данный класс отвечает за конфиг.
    Класс нужен для удобства загрузки и проверки переменных для работы с ботами.
    '''

    def __init__(self, env_file: str = None) -> None:
        '''Загружаем и проверяем переменные'''
        self._env_file = env_file

    def writer_token(self) -> str:
        load_dotenv(dotenv_path=self._env_file)
        writer_token = os.getenv("WRITER_TOKEN")
        if not writer_token:
            raise ValueError("WRITER_TOKEN is missing")
        return writer_token

    def chat_id(self) -> int:
        load_dotenv(dotenv_path=self._env_file)
        chat_id = os.getenv("MY_CHAT_ID")
        if not chat_id:
            raise ValueError("MY_CHAT_ID is missing")
        return int(chat_id)

    def db_dsn(self) -> str:
        load_dotenv(dotenv_path=self._env_file)
        db_path = os.getenv("DB_DSN")
        return db_path

    def tg_api_id(self) -> int:
        load_dotenv(dotenv_path=self._env_file)
        tg_api_id = os.getenv("TG_API_ID")
        if not tg_api_id:
            raise ValueError("TG_API_ID is missing")
        return tg_api_id

    def tg_api_hash(self) -> str:
        load_dotenv(dotenv_path=self._env_file)
        tg_api_hash = os.getenv("TG_API_HASH")
        if not tg_api_hash:
            raise ValueError("TG_API_HASH is missing")
        return tg_api_hash

    def phone_number(self) -> str:
        load_dotenv(dotenv_path=self._env_file)
        phone_number = os.getenv("PHONE_NUMBER")
        if not phone_number:
            raise ValueError("PHONE_NUMBER is missing")
        return phone_number

    def vk_token(self) -> str:
        load_dotenv(dotenv_path=self._env_file)
        vk_token = os.getenv("VK_TOKEN")
        if not vk_token:
            raise ValueError("VK_TOKEN is missing")
        return vk_token
