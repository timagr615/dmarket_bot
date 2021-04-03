from itertools import groupby
from api.dmarketapiv2 import DMarketApi
from time import time
from db.selectors import SelectSkin
from config import logger, BuyParams, Timers
from typing import List, Tuple
from api.Item import ItemHistory, ItemOrder
import math
from api.methods import build_target_body_from_offer
from modules.methods import mov_av_5
from config import BAD_ITEMS
from api.Exceptions import TooManyRequests


class OrderAnalytics:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.repeat = Timers.ORDERS_BASE
        self.frequency = BuyParams.FREQUENCY

        self.max_price = BuyParams.MAX_PRICE
        self.min_price = BuyParams.MIN_PRICE
        self.all_sales = BuyParams.ALL_SALES

        self.profit_percent = BuyParams.PROFIT_PERCENT
        self.good_points_percent = BuyParams.GOOD_POINTS_PERCENT
        self.first_sale = BuyParams.FIRST_SALE
        self.last_sale = BuyParams.LAST_SALE
        self.all_sales = BuyParams.ALL_SALES
        self.days_count = BuyParams.DAYS_COUNT
        self.sale_count = BuyParams.SALE_COUNT
        self.max_count_offers = BuyParams.MAX_COUNT_SELL_OFFERS

        self.boost_percent = BuyParams.BOOST_PERCENT
        self.boost_points = BuyParams.BOOST_POINTS

        self.max_threshold = BuyParams.MAX_THRESHOLD
        self.min_threshold = BuyParams.MIN_THRESHOLD

    def popularity_control(self, skins: List[ItemHistory]) -> List[ItemHistory]:
        items = list()
        for skin in skins:
            sales = list()
            first_sale = int(skin.history['LastSales'][-1]['Date'])
            last_sale = int(skin.history['LastSales'][0]['Date'])

            if first_sale > (time() - self.first_sale * 60 * 60 * 24):

                if last_sale > (time() - self.last_sale * 60 * 60 * 24):

                    for sale in skin.history['LastSales']:
                        #print(skin.market_hash_name)
                        if int(sale['Date']) > (time() - self.days_count * 60 * 60 * 24):
                            sales.append(sale)
                    if len(sales) >= self.sale_count:
                        items.append(skin)
        return items

    def boost_control(self, skins: List[ItemHistory]) -> List[ItemHistory]:
        new_skins = list()
        for item in skins:
            mov_av = mov_av_5(item.history['LastSales'])
            delete_points = 0
            try:
                for i in range(len(mov_av[:-4])):
                    if int(item.history['LastSales'][i]['Price']['Amount']) / 100 > \
                            mov_av[i] * (1 + self.boost_percent / 100):
                        item.history['LastSales'].pop(i)
                        delete_points += 1
                if delete_points <= self.boost_points:
                    new_skins.append(item)
            except IndexError:
                pass
        return new_skins

    async def good_skins(self, skins: List[ItemHistory]) -> List[ItemOrder]:
        items = list()
        skins = sorted(skins, key=lambda x: x.market_hash_name)
        names = [i.market_hash_name for i in skins]
        agregated_prices = await self.bot.agregated_prices(names)
        agregated_prices = sorted(agregated_prices, key=lambda x: x['MarketHashName'])

        for skin, agr in zip(skins, agregated_prices):
            # agregated_prices = await self.bot.agregated_prices(skin.market_hash_name)
            best_order = float(agr['Orders']['BestPrice'])
            # print(len(skin.history['LastSales']))
            points_count = math.ceil(len(skin.history['LastSales']) / 100 * self.good_points_percent)
            count = 0
            for i in skin.history['LastSales']:
                price_with_fee = int(i['Price']['Amount']) / 100 * 0.95
                if price_with_fee > best_order * (1 + self.profit_percent / 100):
                    count += 1
            if count >= points_count:
                if int(agr['Offers']['Count']) <= self.max_count_offers:
                    items.append(ItemOrder.new_from_item_history(skin, best_order))
        return items

    async def frequency_skins(self, skins: List[ItemHistory]) -> List[ItemOrder]:
        items = list()
        skins = sorted(skins, key=lambda x: x.market_hash_name)
        names = [i.market_hash_name for i in skins]
        agregated_prices = await self.bot.agregated_prices(names)
        agregated_prices = sorted(agregated_prices, key=lambda x: x['MarketHashName'])
        for skin, agr in zip(skins, agregated_prices):

            best_order = float(agr['Orders']['BestPrice'])
            my_sell_price = best_order * (1 + self.profit_percent / 100)

            count = 0
            points_count = math.ceil(len(skin.history['LastSales']) / 100 * self.good_points_percent)
            for i in skin.history['LastSales']:
                price_with_fee = int(i['Price']['Amount']) / 100 * 0.95
                if price_with_fee > my_sell_price:
                    count += 1
            if count >= points_count:
                if int(agr['Offers']['Count']) <= self.max_count_offers:
                    #if any([my_sell_price <= p for p in offer_prices]):
                    items.append(ItemOrder.new_from_item_history(skin, best_order))
        return items

    async def skins_for_buy(self) -> List[ItemOrder]:
        t = time()
        new_skins = list()
        skins = [i for i in SelectSkin.select_all() if self.min_price < i.avg_price < self.max_price]
        logger.write(f'SKINS {len(skins)}', 'debug')
        if skins:
            skins = self.popularity_control(skins)
            logger.write(f'POP CONTROL {len(skins)}', 'debug')
            skins = self.boost_control(skins)
            logger.write(f'BOOST CONTROL {len(skins)}', 'debug')
            if self.frequency:
                skins = await self.frequency_skins(skins)
            else:
                skins = await self.good_skins(skins)
            logger.write(f'GOOD CONTROL {len(skins)}', 'debug')
            for skin in skins:
                skin.max_price = round(skin.best_order*(1 + self.max_threshold/100), 2)
                skin.min_price = round(skin.best_order*(1 - self.min_threshold/100), 2)
                # logger.write()
                # logger.write(f'{skin.market_hash_name} {skin.best_order} {skin.min_price} {skin.max_price}')
                # SelectSkinOrder.create_skin(skin)
                new_skins.append(skin)
        logger.write(f'База ордеров обновлялась {round(time() - t, 2)} сек.', 'debug')
        return new_skins


class Orders:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.order_list = OrderAnalytics(self.bot)
        # self.select_order = SelectSkinOrder()

    @staticmethod
    def order_price(max_p, min_p, best):
        if best > max_p:
            order_price = max_p
        elif min_p < best <= max_p:
            order_price = best + 0.01
        else:
            order_price = min_p
        return order_price

    @staticmethod
    def sort_targets(skins: List[ItemOrder], targets: list) -> Tuple[list, list, list]:
        good_targets = [i for i in targets if i['Title'] in [s.market_hash_name for s in skins]]
        bad_targets = [i for i in targets if i['Title'] not in [s.market_hash_name for s in skins]]
        new_skins = [i for i in skins if i.market_hash_name not in [s['Title'] for s in targets]]
        return new_skins, good_targets, bad_targets

    async def delete_targets(self, active: list, inactive: list):
        target_ids_inactive = [i['TargetID'] for i in inactive]
        target_ids = [i['TargetID'] for i in active] + target_ids_inactive
        return await self.bot.delete_target(target_ids)

    async def create_order(self, item: ItemOrder):
        offer, cursor = await self.bot.market_offers(name=item.market_hash_name)
        if offer and offer[0]['title'] == item.market_hash_name:
            target = build_target_body_from_offer(offer, item.best_order)
            target_body = {'Targets': [target]}
            order = await self.bot.create_target(target_body)
            logger.write(order, 'debug')
            return order
        return []

    async def check_offers(self, item: ItemOrder):
        offers = await self.bot.offers_by_title(name=item.market_hash_name, limit=3)
        offers = sorted(offers, key=lambda x: int(x['price']['USD']))
        offer_prices = [int(o['price']['USD']) / 100 for o in offers]
        my_sell_price = item.best_order * (1 + self.order_list.profit_percent / 100)
        if any([my_sell_price <= p for p in offer_prices]):
            return True
        return False

    async def update_orders(self):
        t = time()
        skins = await self.order_list.skins_for_buy()
        '''for skin in skins:
            logger.write(f'{skin.market_hash_name} {skin.best_order} {skin.min_price} {skin.max_price}')'''
        targets = await self.bot.user_targets(limit='1000')
        name_group = [list(j) for _, j in groupby(targets['Items'], key=lambda x: x['Title'])]
        targets_inactive = await self.bot.user_targets(limit='1000', status='TargetStatusInactive')
        new, good, bad = self.sort_targets(skins, targets['Items'])
        for name in name_group:
            if len(name) > 1:
                bad += name[1:]
        await self.delete_targets(bad, targets_inactive['Items'])
        for skin in new:
            # logger.write(f'{skin.market_hash_name} {skin.best_order} {skin.min_price} {skin.max_price}')
            if self.bot.balance > skin.best_order:
                for i in BAD_ITEMS:
                    if i in skin.market_hash_name.lower():
                        continue
                if await self.check_offers(skin):
                    await self.create_order(skin)
        if good:
            for i in good:
                for j in skins:
                    if i["Title"] == j.market_hash_name:
                        if i["Price"]["Amount"] != j.best_order:
                            order_price = self.order_price(j.max_price, j.min_price, j.best_order)
                            j.best_order = order_price
                            if await self.check_offers(j):
                                await self.delete_targets([i], [])
                                await self.create_order(j)

        logger.write(f'Обновление ордеров шло {round(time() - t, 2)} сек.', 'debug')