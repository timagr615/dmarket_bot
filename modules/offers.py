import asyncio
from typing import List
from db.selectors import SelectSkinOffer
from api.Item import ItemOffer
from api.dmarketapiv2 import DMarketApi
from config import PUBLIC_KEY, SECRET_KEY, SellParams, logger
from time import time


class History:
    def __init__(self, bot: DMarketApi):
        self.bot = bot

    @staticmethod
    def skins_db() -> List[ItemOffer]:
        skins = SelectSkinOffer.select_all()
        if skins:
            return [i for i in skins if i.sell_time is None]
        else:
            return list()

    async def save_skins(self):
        buy = await self.bot.closed_targets(limit='20')
        buy = buy['Trades']
        buy = [ItemOffer(asset_id=i['AssetID'], buy_price=i['Price']['Amount'], buy_time=int(time())) for i in buy]

        sell = await self.bot.user_offers(status='OfferStatusSold')
        sell = [ItemOffer(asset_id=i['AssetID'], offer_id=i['Offer']['OfferID'],
                          sell_price=i['Offer']['Price']['Amount']*0.95, sell_time=int(time()),
                          market_hash_name=i['Title']) for i in sell['Items']]

        buy_asset_ids = [s.asset_id for s in SelectSkinOffer.select_all()]
        for b in buy:
            if b.asset_id not in buy_asset_ids:
                SelectSkinOffer.create_skin(b)
        skins = self.skins_db()
        for s in skins:
            for i in sell:
                if s.asset_id == i.asset_id:
                    s.market_hash_name = i.market_hash_name
                    s.sell_price = i.sell_price
                    s.offer_id = i.offer_id
                    s.sell_time = i.sell_time
        SelectSkinOffer.update_sold(skins)


class Offers:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.max_percent = SellParams.MAX_PERCENT
        self.min_percent = SellParams.MIN_PERCENT

    async def add_to_sell(self):
        skins = SelectSkinOffer.select_not_sell()
        inv = await self.bot.user_items()
        inv = [ItemOffer(asset_id=i['itemId'], market_hash_name=i['title']) for i in inv['objects'] if i['inMarket']]

        for i in inv:
            for j in skins:
                if i.asset_id == j.asset_id:
                    price = j.buy_price*(1 + self.max_percent/100 + 0.05)
                    i.sell_price = price
        add = await self.bot.user_offers_create(inv)
        if 'Result' in add:
            for i in add['Result']:
                for j in inv:
                    if i['CreateOffer']['AssetID'] == j.asset_id:
                        j.sell_price = i['CreateOffer']['Price']['Amount']
                        j.offer_id = i['OfferID']
                        SelectSkinOffer.update_offer_id(j)
        else:
            logger.write(f'ERROR in ADD_TO_SELL: in user_offers_create: {add}')
        logger.write(f'{add}', 'debug')

    @staticmethod
    def offer_price(max_p, min_p, best):
        if best < min_p:
            order_price = min_p
        elif min_p < best <= max_p:
            order_price = best - 0.01
        else:
            order_price = max_p
        return order_price

    async def update_offers(self):
        on_sell = sorted([i for i in SelectSkinOffer.select_not_sell() if i.offer_id is not None],
                         key=lambda x: x.market_hash_name)
        names = [i.market_hash_name for i in on_sell]
        agr = await self.bot.agregated_prices(names=names, limit=len(names))
        items_to_update = list()
        for i, j in zip(on_sell, agr):
            best_price = float(j['Offers']['BestPrice'])
            if i.sell_price != best_price:
                max_sell_price = round(i.buy_price * (1 + self.max_percent / 100 + 5 / 100), 2)
                min_sell_price = round(i.buy_price * (1 + self.min_percent / 100 + 5 / 100), 2)
                price = self.offer_price(max_sell_price, min_sell_price, best_price)
                if price != round(i.sell_price, 2):
                    i.sell_price = price
                    items_to_update.append(i)
                    # print(i.market_hash_name)
        updated = await self.bot.user_offers_edit(items_to_update)
        for i in updated['Result']:
            for j in on_sell:
                if i['EditOffer']['AssetID'] == j.asset_id:
                    j.sell_price = i['EditOffer']['Price']['Amount']
                    j.offer_id = i['NewOfferID']
                    SelectSkinOffer.update_offer_id(j)
        logger.write(f'UPDATE OFFERS: {updated}', 'debug')

