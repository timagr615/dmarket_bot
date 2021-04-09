from api.dmarketapi import DMarketApi
import datetime
from pydantic import ValidationError
from typing import List
# from db.selectors import SelectSkin
from api.schemas import MarketOffer, Games, Skin
from config import logger, PrevParams, BuyParams, Timers, BAD_ITEMS, GAMES
from config import PUBLIC_KEY, SECRET_KEY
from itertools import groupby
from api.exceptions import UnknownError, TooManyRequests
from time import sleep
from time import time
import requests
import asyncio


class SkinBase:
    def __init__(self, api: DMarketApi):
        self.api = api
        self.repeat = Timers.PREV_BASE
        self.min_price = PrevParams.MIN_AVG_PRICE
        self.max_price = PrevParams.MAX_AVG_PRICE
        self.popularity = PrevParams.POPULARITY
        # self.select_skin = SelectSkin()
        self.min_price_buy = BuyParams.MIN_PRICE
        self.max_price_buy = BuyParams.MAX_PRICE

    @staticmethod
    def check_name(item_name: str):
        for i in BAD_ITEMS:
            if i in item_name.lower():
                if ('Emerald Pinstripe' and 'Monkey Business' and 'Case Hardened') not in item_name:
                    return False
        return True

    async def get_items(self, min_p: int, max_p: int, game: Games) -> List[MarketOffer]:
        market_offers = await self.api.market_offers(price_from=min_p, price_to=max_p, game=game)
        cursor = market_offers.cursor
        while cursor:
            other_offers = await self.api.market_offers(price_from=min_p, price_to=max_p,
                                                        cursor=cursor, game=game)
            market_offers.objects += other_offers.objects
            cursor = other_offers.cursor
        market_offers.objects = sorted(market_offers.objects, key=lambda x: x.title)
        skins = [list(group)[0] for _, group in groupby(market_offers.objects, lambda x: x.title)]
        return [s for s in skins if self.check_name(s.title)]

    async def filter_skins(self, skins: List[MarketOffer], game: Games, min_p: int, max_p: int) -> List[Skin]:
        s = list()
        count = 0
        for i in skins:
            history = await self.api.last_sales(i.title, game=game)
            if len(history.LastSales) == 20:
                prices = [i.Price.Amount for i in history.LastSales]
                avg_price = sum(prices)
                count_prices = len(prices)
                avg_price = avg_price / count_prices
                if min_p <= avg_price <= max_p:
                    try:
                        sk = Skin(title=i.title, game=game, LastSales=history.LastSales,
                                  avg_price=avg_price, update_time=datetime.datetime.now())
                        s.append(sk)
                    except ValidationError as e:
                        logger.error(e.json())
            if count % 500 == 0:
                logger.debug(f'Игра {game}. Проанализировано {count} скинов.')
            count += 1
        return s

    async def update_base(self):
        t0 = time()
        final_skins = list()
        for game in GAMES:
            logger.debug(game)
            skins = await self.get_items(self.min_price, self.max_price, game)
            skins = await self.filter_skins(skins, game, self.min_price, self.max_price)
            logger.debug(f'В игре {game} получено {len(skins)} скинов')
            final_skins += skins
        logger.info(f'Всего проанализировано скинов: {len(final_skins)}')
        logger.info(f'База скинов обновлялась {round((time() - t0)/60, 2)} минут.')

# 10.55
