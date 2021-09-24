from itertools import groupby
from api.dmarketapi import DMarketApi
from time import time
from db.crud import SelectSkin
from config import logger, BuyParams, Timers, GAMES
from typing import List, Tuple
from api.schemas import SkinHistory, SkinOrder, Target, CreateTarget, \
    CreateTargets, LastPrice, TargetAttributes, CumulativePrice
import math
# from api.methods import build_target_body_from_offer
from modules.methods import mov_av_5
from config import BAD_ITEMS
from api.exceptions import TooManyRequests


class OrderAnalytics:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.repeat = Timers.ORDERS_BASE
        self.frequency = BuyParams.FREQUENCY

        self.max_price = BuyParams.MAX_PRICE
        self.min_price = BuyParams.MIN_PRICE
        self.all_sales = BuyParams.ALL_SALES

        self.avg_price_count = BuyParams.AVG_PRICE_COUNT
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

    def popularity_control(self, skins: List[SkinHistory]) -> List[SkinHistory]:
        items = list()
        for skin in skins:
            sales = list()
            first_sale = int(skin.LastSales[-1].Date.timestamp())
            last_sale = int(skin.LastSales[0].Date.timestamp())
            if first_sale < (time() - self.first_sale * 60 * 60 * 24):
                if last_sale > (time() - self.last_sale * 60 * 60 * 24):
                    for sale in skin.LastSales:

                        if int(sale.Date.timestamp()) > (time() - self.days_count * 60 * 60 * 24):
                            sales.append(sale)
                    if len(sales) >= self.sale_count:
                        items.append(skin)
        return items

    def boost_control(self, skins: List[SkinHistory]) -> List[SkinHistory]:
        new_skins = list()
        for item in skins:
            mov_av = mov_av_5(item.LastSales)
            delete_points = 0
            try:
                for i in range(len(mov_av[:-4])):
                    if item.LastSales[i].Price.Amount > \
                            mov_av[i] * (1 + self.boost_percent / 100):
                        item.LastSales.pop(i)
                        delete_points += 1
                if delete_points <= self.boost_points:
                    new_skins.append(item)
            except IndexError:
                pass
        return new_skins

    async def good_skins(self, skins: List[SkinHistory]) -> List[SkinOrder]:
        items = list()
        skins = sorted(skins, key=lambda x: x.title)
        names = [i.title for i in skins]
        agregated_prices = await self.bot.agregated_prices(names)
        agregated_prices = sorted(agregated_prices, key=lambda x: x.MarketHashName)

        for skin, agr in zip(skins, agregated_prices):
            best_order = agr.Orders.BestPrice*100
            points_count = math.ceil(len(skin.LastSales) / 100 * self.good_points_percent)
            count = 0
            for i in skin.LastSales:
                price_with_fee = i.Price.Amount * (1 - self.bot.SELL_FEE/100)  # Надо ли делить на 100?
                if price_with_fee > best_order * (1 + self.profit_percent / 100):
                    count += 1
            if count >= points_count:
                if agr.Offers.Count <= self.max_count_offers:
                    items.append(SkinOrder(title=skin.title, bestOrder=int(best_order), game=skin.game))
        return items

    async def frequency_skins(self, skins: List[SkinHistory]) -> List[SkinOrder]:
        items = list()
        skins = sorted(skins, key=lambda x: x.title)
        names = [i.title for i in skins]
        agregated_prices = await self.bot.agregated_prices(names)
        agregated_prices = sorted(agregated_prices, key=lambda x: x.MarketHashName)
        for skin, agr in zip(skins, agregated_prices):

            best_order = agr.Orders.BestPrice*100
            my_sell_price = best_order * (1 + self.profit_percent / 100)

            count = 0
            points_count = math.ceil(len(skin.LastSales) / 100 * self.good_points_percent)
            for i in skin.LastSales:
                price_with_fee = i.Price.Amount * (1 - self.bot.SELL_FEE/100)
                if price_with_fee > my_sell_price:
                    count += 1
            if count >= points_count:
                if agr.Offers.Count <= self.max_count_offers:
                    items.append(SkinOrder(title=skin.title, bestOrder=int(best_order), game=skin.game))
        return items

    @staticmethod
    def first_second_offer(info: List[CumulativePrice]) -> tuple:
        len_offers = len(info)
        if len_offers == 0:
            best_offer_price = 0
            second_offer_price = 0
        else:
            best_offer = info[0]
            if len_offers == 1:
                second_offer = best_offer
            else:
                if best_offer.Amount == 1:
                    second_offer = info[1]
                else:
                    second_offer = best_offer
            best_offer_price = best_offer.Price
            second_offer_price = second_offer.Price
        return best_offer_price, second_offer_price, len_offers

    async def analyze_market_offers(self, skin: SkinHistory):
        market_info = await self.bot.cumulative_price(skin.title, skin.game)
        len_avg = skin.LastSales[0:self.avg_price_count]
        avg_price_10 = sum([s.Price.Amount/100 for s in len_avg])/len(len_avg)
        best_offer, second_offer, offers_count = self.first_second_offer(market_info.Offers)
        best_target, second_target, targets_count = self.first_second_offer(market_info.Targets)
        if best_offer == 0 or (best_target - second_target)/best_offer*100 > 3:
            best_target = second_target
        if second_offer == 0 or (second_offer - best_offer)/second_offer*100 > 3:
            best_offer = second_offer
        profit = -(best_target - (1 - self.bot.SELL_FEE/100) * best_offer) / best_target * 100
        profit_by_avg = -(best_target - (1 - self.bot.SELL_FEE/100) * avg_price_10) / best_target * 100
        return best_offer, best_target, offers_count, targets_count, profit, round(profit_by_avg, 2)

    async def frequency2(self, skins: List[SkinHistory]) -> List[SkinOrder]:
        items = list()
        skins = sorted(skins, key=lambda x: x.title)
        for skin in skins:
            best_offer, best_target, offers_count, targets_count, profit, profit_2 = \
                await self.analyze_market_offers(skin)

            if profit_2 > self.profit_percent and profit > self.profit_percent:
                # print(skin.title, best_offer, offers_count, best_target, targets_count, profit, profit_2)
                my_sell_price = best_target * (1 + self.profit_percent / 100)
                count = 0
                points_count = math.ceil(len(skin.LastSales) / 100 * self.good_points_percent)
                for i in skin.LastSales:
                    price_with_fee = i.Price.Amount * (1 - self.bot.SELL_FEE / 100)
                    if price_with_fee > my_sell_price:
                        count += 1
                if count >= points_count:
                    if offers_count <= self.max_count_offers:
                        # logger.debug(f'{skin.title} | {best_target} | | {best_offer} | {profit}')
                        items.append(SkinOrder(title=skin.title, bestOrder=int(best_target*100), game=skin.game))
        return items

    async def skins_for_buy(self) -> List[SkinOrder]:
        t = time()
        new_skins = list()
        skins = []
        for game in GAMES:
            skins += [i for i in SelectSkin.select_all() if self.min_price < i.avg_price < self.max_price
                      and i.game == game.value]
        logger.info(f'SKINS {len(skins)}')
        if skins:
            skins = self.popularity_control(skins)
            logger.info(f'POP CONTROL {len(skins)}')
            skins = self.boost_control(skins)
            logger.info(f'BOOST CONTROL {len(skins)}')
            if self.frequency:
                #skins = await self.frequency_skins(skins)
                skins = await self.frequency2(skins)
            else:
                skins = await self.good_skins(skins)
            logger.info(f'GOOD CONTROL {len(skins)}')
            for skin in skins:
                skin.maxPrice = int(skin.bestOrder*(1 + self.max_threshold/100))
                skin.minPrice = int(skin.bestOrder*(1 - self.min_threshold/100))
                # logger.info(f'{skin.title} {skin.bestOrder} {skin.minPrice} {skin.maxPrice}')
                # SelectSkinOrder.create_skin(skin)
                new_skins.append(skin)
        logger.debug(f'База ордеров обновлялась {round(time() - t, 2)} сек.')
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
            order_price = best + 1
        else:
            order_price = min_p
        return order_price

    @staticmethod
    def sort_targets(skins: List[SkinOrder], targets: List[Target]) -> Tuple[List[SkinOrder], List[Target], List[Target]]:
        good_targets = [i for i in targets if i.Title in [s.title for s in skins]]
        bad_targets = [i for i in targets if i.Title not in [s.title for s in skins]]
        new_skins = [i for i in skins if i.title not in [s.Title for s in targets]]
        return new_skins, good_targets, bad_targets

    async def create_order(self, item: SkinOrder):
        offer = await self.bot.market_offers(name=item.title, limit=1, game=item.game)
        if offer.objects and offer.objects[0].title == item.title:
            offer = offer.objects[0]
            price = LastPrice(Currency='USD', Amount=item.bestOrder/100)
            attributes = [TargetAttributes(Name='name', Value=offer.extra.name),
                          TargetAttributes(Name='title', Value=offer.title),
                          TargetAttributes(Name='category', Value=offer.extra.category),
                          TargetAttributes(Name='gameId', Value=offer.gameId),
                          TargetAttributes(Name='categoryPath', Value=offer.extra.categoryPath),
                          TargetAttributes(Name='image', Value=offer.image)]
            if offer.extra.exterior:
                attributes.append(TargetAttributes(Name='exterior', Value=offer.extra.exterior))
            target = CreateTarget(Amount='1', Price=price, Attributes=attributes)
            targets = CreateTargets(Targets=[target])
            order = await self.bot.create_target(targets)
            return order
        return []

    async def check_offers(self, item: SkinOrder):
        offers = await self.bot.offers_by_title(name=item.title, limit=3)
        offers = sorted(offers.objects, key=lambda x: int(x.price.USD))
        offer_prices = [o.price.USD for o in offers]
        my_sell_price = item.bestOrder * (1 + self.order_list.profit_percent / 100)
        if any([my_sell_price <= p for p in offer_prices]):
            return True
        return False

    async def update_orders(self):
        t = time()
        skins = await self.order_list.skins_for_buy()
        targets = await self.bot.user_targets(limit='1000')
        name_group = [list(j) for _, j in groupby(targets.Items, key=lambda x: x.Title)]
        targets_inactive = await self.bot.user_targets(limit='1000', status='TargetStatusInactive')
        new, good, bad = self.sort_targets(skins, targets.Items)
        for name in name_group:
            if len(name) > 1:
                bad += name[1:]
        await self.bot.delete_target(bad + targets_inactive.Items)
        for skin in new:
            # logger.write(f'{skin.market_hash_name} {skin.best_order} {skin.min_price} {skin.max_price}')
            if self.bot.balance > skin.bestOrder:
                for i in BAD_ITEMS:
                    if i in skin.title.lower():
                        continue
                if await self.check_offers(skin):
                    await self.create_order(skin)
        if good:
            for i in good:
                for j in skins:
                    if i.Title == j.title:
                        if i.Price.Amount*100 != j.bestOrder:
                            order_price = self.order_price(j.maxPrice, j.minPrice, j.bestOrder)
                            j.bestOrder = order_price
                            if await self.check_offers(j):
                                await self.bot.delete_target([i])
                                await self.create_order(j)

        logger.debug(f'Обновление ордеров шло {round(time() - t, 2)} сек.')