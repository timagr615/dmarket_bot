import sys
from loguru import logger
from api.schemas import Games
from credentials import PUBLIC_KEY, SECRET_KEY


logger_config = {
    "handlers": [
        {"sink": sys.stderr, 'colorize': True, 'level': 'DEBUG'},
        # {"sink": "log/debug.log", "serialize": False, 'level': 'DEBUG'},
        {"sink": "log/info.log", "serialize": False, 'level': 'INFO'},
    ],
    "extra": {"user": "someone"}
}
logger.configure(**logger_config)

DEBUG = False
LOG_FILE = True

proxies = ''

API_URL = "https://api.dmarket.com"
API_URL_TRADING = API_URL
GAMES = [Games.CS, Games.DOTA, Games.RUST]

BAD_ITEMS = ['key', 'pin', 'sticker', 'case', 'operation', 'pass', 'capsule', 'package', 'challengers',
             'patch', 'music', 'kit', 'graffiti']


class Timers:
    PREV_BASE = 60 * 60 * 4
    ORDERS_BASE = 60 * 10


class PrevParams:
    POPULARITY = 3
    MIN_AVG_PRICE = 400
    MAX_AVG_PRICE = 3500


class BuyParams:
    FREQUENCY = True
    MIN_PRICE = 200
    MAX_PRICE = 3500

    PROFIT_PERCENT = 6
    GOOD_POINTS_PERCENT = 45

    ALL_SALES = 100
    DAYS_COUNT = 20
    SALE_COUNT = 15
    LAST_SALE = 2  # Последняя продажа не позднее LAST_SALE дней назад
    FIRST_SALE = 15  # Первая покупка не позже FIRST_SALE дней назад

    MAX_COUNT_SELL_OFFERS = 30

    BOOST_PERCENT = 24
    BOOST_POINTS = 3

    MAX_THRESHOLD = 1  # Максимальное повышение цены на MAX_THRESHOLD процентов от текущего ордера
    MIN_THRESHOLD = 3  # Максимальное понижение цены на MIN_THRESHOLD процентов от текущего ордера


class SellParams:
    MIN_PERCENT = 5
    MAX_PERCENT = 12
