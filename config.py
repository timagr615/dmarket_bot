import sys
from loguru import logger

from api.schemas import Games
from credentials import PUBLIC_KEY, SECRET_KEY


logger_config = {
    "handlers": [
        {"sink": sys.stderr, 'colorize': True, 'level': 'INFO'},
        # {"sink": "log/debug.log", "serialize": False, 'level': 'DEBUG'},
        {"sink": "log/info.log", "serialize": False, 'level': 'INFO'},
    ]
}
logger.configure(**logger_config)


API_URL = "https://api.dmarket.com"
API_URL_TRADING = API_URL
# GAMES = [Games.CS, Games.DOTA, Games.RUST]
GAMES = [Games.CS]
DATABASE_NAME = '/skins.db'

BAD_ITEMS = ['key', 'pin', 'sticker', 'case', 'operation', 'pass', 'capsule', 'package', 'challengers',
             'patch', 'music', 'kit', 'graffiti']


class Timers:
    PREV_BASE = 60 * 60 * 5
    ORDERS_BASE = 60 * 10


class PrevParams:
    # POPULARITY = 3
    MIN_AVG_PRICE = 400
    MAX_AVG_PRICE = 3500


class BuyParams:
    FREQUENCY = True
    MIN_PRICE = 300
    MAX_PRICE = 3000

    PROFIT_PERCENT = 7
    GOOD_POINTS_PERCENT = 50

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
    MIN_PERCENT = 4
    MAX_PERCENT = 12
