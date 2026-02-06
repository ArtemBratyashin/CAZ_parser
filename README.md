## Разработка

Рекомендуется создать виртуальное окружение для проекта и установить в него зависимости, в том числе
для разработки:

1. Перейдите в папку проекта

2. Создайте виртуальное окружение командой и активируйте его:
    ```console
    foo@bar:~$ python3 -m venv venv
    foo@bar:~$ source ./venv/bin/activate  # На MacOS и Linux
    foo@bar:~$ venv\Scripts\activate  # На Windows
    ```

3. Установите библиотеки
    ```console
    foo@bar:~$ pip install -Ur requirements.txt -r requirements.dev.txt
    ```

## ENV file description

- WRITER_TOKEN = "..." - токен бота для отправки сообщений
- MY_CHAT_ID = "..." - id чата,  который необходимо отпралять сообщение
- TG_API_ID = ... - данные бота парсера
- TG_API_HASH = '...' - данные бота парсера
- PHONE_NUMBER = '...' - данные бота парсера