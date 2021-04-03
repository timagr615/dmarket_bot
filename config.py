import os
from logger.logger import BaseLogger

DEBUG = False
LOG_FILE = True

logger = BaseLogger(DEBUG, LOG_FILE)

PUBLIC_KEY = "279a15a105ff154598bb823ec51ce62e4e6bbc1476152cfb33cc2007dcbac67d"
SECRET_KEY = "39637fdb289c90803c6b876586341a39ed1b092b62286d4ffafe87ecc2acc354279a15a105ff154598bb823ec51ce62e4e6bbc1476152cfb33cc2007dcbac67d"

proxies = ''

API_URL = "https://api.dmarket.com"
# API_URL_TRADING = 'https://trading.dmarket.com'
API_URL_TRADING = API_URL
GAME = 'a8db'
BAD_ITEMS = ['key', 'pin', 'sticker', 'case', 'operation', 'pass', 'capsule', 'package', 'challengers',
             'patch', 'music', 'kit']


class BaseSettings:
    RPS = 15


class Timers:
    PREV_BASE = 60 * 60 * 4
    ORDERS_BASE = 60 * 10


class PrevParams:
    POPULARITY = 3
    MIN_AVG_PRICE = 4
    MAX_AVG_PRICE = 40


class BuyParams:
    FREQUENCY = True
    MIN_PRICE = 2
    MAX_PRICE = 35

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
