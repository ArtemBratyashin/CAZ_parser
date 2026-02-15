import random
import string

import pytest

from src.config import EnvConfig


def _nonce() -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(12))


def _missing_env_file() -> str:
    return f"missing-{_nonce()}.env"


def test_it_cannot_be_created_without_writer_token(monkeypatch):
    monkeypatch.delenv("WRITER_TOKEN", raising=False)
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")

    with pytest.raises(ValueError):
        EnvConfig(env_file=_missing_env_file())


def test_it_cannot_be_created_without_chat_id(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.delenv("MY_CHAT_ID", raising=False)
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")

    with pytest.raises(ValueError):
        EnvConfig(env_file=_missing_env_file())


def test_it_cannot_be_created_without_tg_api_id(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.delenv("TG_API_ID", raising=False)
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")

    with pytest.raises(ValueError):
        EnvConfig(env_file=_missing_env_file())


def test_it_cannot_be_created_without_tg_api_hash(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.delenv("TG_API_HASH", raising=False)
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")

    with pytest.raises(ValueError):
        EnvConfig(env_file=_missing_env_file())


def test_it_cannot_be_created_without_phone_number(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.delenv("PHONE_NUMBER", raising=False)

    with pytest.raises(ValueError):
        EnvConfig(env_file=_missing_env_file())


def test_it_can_provide_writer_token(monkeypatch):
    token = f"токен-{_nonce()}"
    monkeypatch.setenv("WRITER_TOKEN", token)
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")

    assert EnvConfig(env_file=_missing_env_file()).writer_token() == token


def test_it_can_provide_chat_id_as_int(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    chat_id = random.randint(10_000, 99_999)
    monkeypatch.setenv("MY_CHAT_ID", str(chat_id))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")

    assert EnvConfig(env_file=_missing_env_file()).chat_id() == chat_id


def test_it_can_provide_db_path_from_environment(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")
    db_path = f"данные-{_nonce()}.sqlite3"
    monkeypatch.setenv("DB_PATH", db_path)

    assert EnvConfig(env_file=_missing_env_file()).db_path() == db_path


def test_it_can_use_default_db_path_when_it_is_missing(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")
    monkeypatch.delenv("DB_PATH", raising=False)

    assert EnvConfig(env_file=_missing_env_file()).db_path() == "departments.sqlite3"


def test_it_can_provide_tg_api_id_as_int(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    api_id = random.randint(100_000, 999_999)
    monkeypatch.setenv("TG_API_ID", str(api_id))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")

    assert EnvConfig(env_file=_missing_env_file()).tg_api_id() == api_id


def test_it_can_provide_tg_api_hash(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    api_hash = f"хэш-{_nonce()}"
    monkeypatch.setenv("TG_API_HASH", api_hash)
    monkeypatch.setenv("PHONE_NUMBER", f"+7{random.randint(9000000000, 9999999999)}")

    assert EnvConfig(env_file=_missing_env_file()).tg_api_hash() == api_hash


def test_it_can_provide_phone_number(monkeypatch):
    monkeypatch.setenv("WRITER_TOKEN", f"токен-{_nonce()}")
    monkeypatch.setenv("MY_CHAT_ID", str(random.randint(10_000, 99_999)))
    monkeypatch.setenv("TG_API_ID", str(random.randint(100_000, 999_999)))
    monkeypatch.setenv("TG_API_HASH", f"хэш-{_nonce()}")
    phone = f"+7{random.randint(9000000000, 9999999999)}"
    monkeypatch.setenv("PHONE_NUMBER", phone)

    assert EnvConfig(env_file=_missing_env_file()).phone_number() == phone
