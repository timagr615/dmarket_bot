# dmarket_bot
Bot for automatic trading on dmarket 




### Для использования:

- git clone https://github.com/timagr615/dmarket_bot.git
- cd dmarket_bot_pro
- Создайте виртуальное окружение, например python3 -m venv venv
Затем активируйте его . venv/bin/activate
- pip install -r requirements.txt
- Создать файл `credentials.py` в корневой директории с следующим содержанием:

```python
PUBLIC_KEY = "your public api key"
SECRET_KEY = "your secret api key"
```
`BOT_TOKEN` - токен бота в телеграме

- Запустить бота можно с помощью файла `main.py`
