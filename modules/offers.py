import datetime
from typing import List
from db.crud import SelectSkinOffer, SkinOffer
from api.schemas import SellOffer, CreateOffer, CreateOffers, LastPrice, EditOffer, EditOffers, \
    DeleteOffers, DeleteOffer, OfferDetails
from api.dmarketapi import DMarketApi
from config import PUBLIC_KEY, SECRET_KEY, SellParams, logger, GAMES
from time import time


class History:
    def __init__(self, bot: DMarketApi):
        self.bot = bot

    @staticmethod
    def skins_db() -> List[SkinOffer]:
        skins = SelectSkinOffer.select_all()
        if skins:
            return [i for i in skins if not i.sellTime]
        return list()

    async def save_skins(self):
        buy = await self.bot.closed_targets(limit='100')

        buy = buy.Trades
        buy = [SellOffer(AssetID=i.AssetID, buyPrice=i.Price.Amount) for i in buy]
        sold = []
        for game in GAMES:
            sell = await self.bot.user_offers(status='OfferStatusSold', game=game, limit='100')
            sell = sell.Items
            sold += sell

        sell = [SellOffer(AssetID=i.AssetID, OfferID=i.Offer.OfferID,
                          sellPrice=i.Offer.Price.Amount, sellTime=datetime.datetime.now(),
                          title=i.Title, game=i.GameID) for i in sold]
        buy_asset_ids = [s.AssetID for s in SelectSkinOffer.select_all()]
        for b in buy:
            if b.AssetID not in buy_asset_ids:
                SelectSkinOffer.create_skin(b)
        skins = self.skins_db()

        for s in skins:
            for i in sell:
                if s.AssetID == i.AssetID:
                    s.title = i.title
                    s.sellPrice = i.sellPrice * (1 - s.fee / 100)
                    s.OfferID = i.OfferID
                    s.sellTime = i.sellTime
                    s.game = i.game
                    break
        SelectSkinOffer.update_sold(skins)


class Offers:
    def __init__(self, bot: DMarketApi):
        self.bot = bot
        self.max_percent = SellParams.MAX_PERCENT
        self.min_percent = SellParams.MIN_PERCENT

    async def add_to_sell(self):
        skins = SelectSkinOffer.select_not_sell()
        inv_skins = []
        invent = []
        for game in GAMES:
            inv = await self.bot.user_items(game=game)
            inv_skins += inv.objects
        for i in inv_skins:
            fee = 7
            if 'custom' in i.fees['dmarket']['sell']:
                fee = int(i.fees['dmarket']['sell']['custom']['percentage'])
            if i.inMarket:
                invent.append(SellOffer(AssetID=i.itemId, title=i.title, game=i.gameId, fee=fee))
        create_offers = []
        for i in invent:
            for j in skins:
                if i.AssetID == j.AssetID:
                    price = j.buyPrice * (1 + self.max_percent / 100 + i.fee / 100)
                    i.sellPrice = price
            try:
                create_offers.append(CreateOffer(AssetID=i.AssetID,
                                                 Price=LastPrice(Currency='USD', Amount=round(i.sellPrice, 2))))
            except TypeError:
                pass

        add = await self.bot.user_offers_create(CreateOffers(Offers=create_offers))
        if add.Result:
            for i in add.Result:
                for j in invent:
                    if i.CreateOffer.AssetID == j.AssetID:
                        j.sellPrice = i.CreateOffer.Price.Amount
                        j.OfferID = i.OfferID
                        SelectSkinOffer.update_offer_id(j)
        logger.debug(f'Add to sell: {add}')

    @staticmethod
    def offer_price(max_p, min_p, best) -> float:
        if best < min_p:
            order_price = min_p
        elif min_p < best <= max_p:
            order_price = best - 0.01
        else:
            order_price = max_p
        return order_price

    async def update_offers(self):
        on_sell = sorted([i for i in SelectSkinOffer.select_not_sell() if i.OfferID],
                         key=lambda x: x.title)

        # names = [i.title for i in on_sell]
        # agr = await self.bot.agregated_prices(names=names, limit=len(names))
        items_to_update = list()

        for i in on_sell:
            itemid = OfferDetails(items=[i.AssetID])
            details = await self.bot.user_offers_details(body=itemid)
            best_price = details.objects[0].minListedPrice.amount / 100
            if i.sellPrice != best_price:
                max_sell_price = i.buyPrice * (1 + self.max_percent / 100 + i.fee / 100)
                min_sell_price = i.buyPrice * (1 + self.min_percent / 100 + i.fee / 100)
                price = self.offer_price(max_sell_price, min_sell_price, best_price)
                if round(price, 2) != round(i.sellPrice, 2):

                    i.sellPrice = price
                    items_to_update.append(EditOffer(OfferID=i.OfferID, AssetID=i.AssetID,
                                                     Price=LastPrice(Currency='USD', Amount=round(i.sellPrice, 2))))

        updated = await self.bot.user_offers_edit(EditOffers(Offers=items_to_update))
        for i in updated.Result:
            for j in on_sell:
                if i.EditOffer.AssetID == j.AssetID:
                    j.sellPrice = i.EditOffer.Price.Amount
                    j.OfferID = i.NewOfferID
                    logger.debug(f'{i.EditOffer.AssetID} {j.AssetID}')
                    SelectSkinOffer.update_offer_id(j)
        logger.debug(f'UPDATE OFFERS: {updated}')

    async def delete_all_offers(self):
        offers = await self.bot.user_offers(status='OfferStatusActive')
        do = [DeleteOffer(itemId=o.AssetID, offerId=o.Offer.OfferID, price=o.Offer.Price) for o in offers.Items]
        await self.bot.user_offers_delete(DeleteOffers(objects=do))
