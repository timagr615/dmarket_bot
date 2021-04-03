from api.dmarketapiv2 import DMarketApi
from db.selectors import SelectSkin
from config import logger, PrevParams, BuyParams, Timers, BAD_ITEMS
from config import PUBLIC_KEY, SECRET_KEY
from itertools import groupby
from api.Exceptions import UnknownError, TooManyRequests
from api.Item import ItemHistory
from time import sleep
from time import time
import requests
import asyncio


class SkinBase:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.repeat = Timers.PREV_BASE
        self.min_price = PrevParams.MIN_AVG_PRICE
        self.max_price = PrevParams.MAX_AVG_PRICE
        self.popularity = PrevParams.POPULARITY
        self.select_skin = SelectSkin()
        self.min_price_buy = BuyParams.MIN_PRICE
        self.max_price_buy = BuyParams.MAX_PRICE

    @staticmethod
    def check_name(item_name: str):
        for i in BAD_ITEMS:
            if i in item_name.lower():
                if ('Emerald Pinstripe' and 'Monkey Business' and 'Case Hardened') not in item_name:
                    return False
        return True

    async def update_base(self):
        """Обновляем базу скинов с историей"""
        data = requests.get('https://market.csgo.com/api/v2/prices/class_instance/USD.json').json()['items']
        logger.write('Получена база с сайта')
        it = []
        for item in data:
            try:
                if self.min_price < float(data[item]['avg_price']) < self.max_price:
                    if self.check_name(data[item]['market_hash_name']):
                        it.append(data[item])
            except TypeError:
                pass
        it = sorted(it, key=lambda x: x['market_hash_name'])
        # удаление повторяющихся элементов
        skins = [list(group)[0] for _, group in groupby(it, lambda x: x['market_hash_name'])]
        skins_with_history = []
        count = 0
        # print(len(skins))
        for i in skins:
            count += 1
            #if count % 100 == 0:
                #logger.write(count)
            if not self.select_skin.skin_existence(i):
                try:
                    history = await self.bot.last_sales(i['market_hash_name'])
                    prices = [int(i['Price']['Amount'])/100 for i in history['LastSales']]
                    avg_price = 0
                    for price in prices:
                        avg_price += price
                    count_prices = len(prices)
                    if count_prices != 0:
                        avg_price = avg_price/count_prices
                    else:
                        avg_price = 0
                    if len(history['LastSales']) == 20:
                        params = {
                            'market_hash_name': i['market_hash_name'],
                            'avg_price': round(avg_price, 2),
                            'history': history
                        }
                        # logger.write(f'{params["market_hash_name"]} {params["avg_price"]} {params["history"]}')
                        skins_with_history.append(ItemHistory.new_from_last_sales(params))
                except IndexError:
                    pass
                except Exception as e:
                    logger.write(f'skin base update_base error: {e}', 'error')
                    await asyncio.sleep(3)

        logger.write(f'SKINS WITH HISTORY {len(skins_with_history)}')
        self.select_skin.create_all_skins(skins_with_history)

    async def update_other_items(self):
        """Обновить историю скинов, которые давно не обновлялись"""
        now = time()
        await self.update_base()
        skins_to_update = [skin for skin in self.select_skin.select_update_time(now, self.repeat)
                           if self.min_price_buy < skin.avg_price < self.max_price_buy]
        if not skins_to_update:
            logger.write(f'Нет скинов для обновления.')
        for skin in skins_to_update:
            try:
                history = await self.bot.last_sales(skin.market_hash_name)
                prices = [int(i['Price']['Amount']) / 100 for i in history['LastSales']]
                avg_price = 0
                for price in prices:
                    avg_price += price
                count_prices = len(prices)
                if count_prices != 0:
                    avg_price = avg_price / count_prices
                skin.history = history
                skin.avg_price = round(avg_price, 2)
                skin.update_time = int(time())
                # logger.write(f'{skin.market_hash_name} {skin.avg_price} {skin,history}')
                # self.select_skin.find_by_name(skin)
            except UnknownError:
                pass
            except Exception as e:
                logger.write(f'skin base update_other_items error: {e}', 'error')
                await asyncio.sleep(3)
        self.select_skin.find_by_name(skins_to_update)

        logger.write(f'Первичная база обновлялась {round((time() - now)/60, 2)} мин.')


