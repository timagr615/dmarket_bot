# dmarket_bot
Bot for automatic trading on dmarket 




### Для использования:

- git clone https://github.com/timagr615/dmarket_bot.git
- cd dmarket_bot
- Создайте виртуальное окружение, например python3 -m venv venv
- Затем активируйте virtualenv . venv/bin/activate
- pip install -r requirements.txt
- Создать файл `credentials.py` в корневой директории с следующим содержанием:

```python
PUBLIC_KEY = "your public api key"
SECRET_KEY = "your secret api key"
```

- Запустить бота можно с помощью файла `main.py`

## Возможности
- Мультиигровая торговля. Поддержка всех игр, доступных на dmarket
- Автоматический анализ базы скинов для каждой игры
- Выставление ордеров, отобранных по 15-ти различным параметрам. Борьба ордеров за первое место.
- Автоматическое выставление скинов на продажу после покупки. Корректировка цен в соответствии с настройками и борьба за 1 место.
## Параметры
Все параметры бота находятся в файле `config.py` в корневой директории бота.
### Подробное описание параметров:
- `logger_config`
```python
logger_config = {
    "handlers": [
        {"sink": sys.stderr, 'colorize': True, 'level': 'INFO'},
        # {"sink": "log/debug.log", "serialize": False, 'level': 'DEBUG'},
        {"sink": "log/info.log", "serialize": False, 'level': 'INFO'},
    ]
}
logger.configure(**logger_config)
```
`"sink": sys.stderr` -  выводлогов в консоль
`"sink": "log/info.log"` - вывод логов в файл
`'level': 'INFO'` - уровень логов. Возможные уровни: `TRACE
DEBUG
INFO
SUCCESS 
WARNING
ERROR 
CRITICAL`
