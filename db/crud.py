from typing import List
from datetime import datetime
from peewee import DoesNotExist

from db.models import Skin, SkinOffer, db
from api.schemas import SkinHistory, MarketOffer, SellOffer

db.connect()
Skin.create_table()
SkinOffer.create_table()
db.close()


class SelectSkin:
    @staticmethod
    def create_all_skins(items: List[SkinHistory]):
        skins = [Skin(**i.dict()) for i in items]
        with db.atomic():
            Skin.bulk_create(skins, batch_size=500)

    @staticmethod
    def skin_existence(item: MarketOffer):
        skin = Skin.select().where(Skin.title == item.title)
        if skin:
            return True
        return False

    @staticmethod
    def find_by_name(items: List[SkinHistory]):
        skins_to_update = list()
        skin_to_create = list()
        for item in items:
            try:
                skin = Skin.get(Skin.title == item.title)
                it = item.dict()
                skin.avg_price = it['avg_price']
                skin.LastSales = it['LastSales']
                skin.update_time = it['update_time']
                skins_to_update.append(skin)
            except DoesNotExist:
                skin_to_create.append(Skin(**item.dict()))
        with db.atomic():
            Skin.bulk_update(skins_to_update,
                             fields=[Skin.avg_price, Skin.LastSales, Skin.update_time],
                             batch_size=500)
        with db.atomic():
            Skin.bulk_create(skin_to_create, batch_size=500)

    @staticmethod
    def select_all() -> List[SkinHistory]:
        skins = Skin.select()
        return [SkinHistory.from_orm(skin) for skin in skins]

    @staticmethod
    def select_update_time(now, delta) -> List[SkinHistory]:
        skins = Skin.select().where(Skin.update_time < datetime.fromtimestamp(now - delta))
        if skins:
            return [SkinHistory.from_orm(skin) for skin in skins]
        return []


class SelectSkinOffer:

    @staticmethod
    def create_skin(item: SellOffer) -> None:
        new_skin = SkinOffer.create(
            title=item.title,
            game=item.game,
            AssetID=item.AssetID,
            buyPrice=item.buyPrice,
            buyTime=item.buyTime,
            OfferID=item.OfferID,
            sellTime=item.sellTime,
            sellPrice=item.sellPrice
        )
        new_skin.save()

    @staticmethod
    def update_sold(skins: List[SkinOffer]):

        with db.atomic():
            SkinOffer.bulk_update(skins, fields=[SkinOffer.title, SkinOffer.sellPrice,
                                                 SkinOffer.sellTime, SkinOffer.OfferID])

    @staticmethod
    def select_not_sell() -> List[SellOffer]:
        skins = SkinOffer.select().where(SkinOffer.sellTime == None)
        return [SellOffer.from_orm(s) for s in skins]

    @staticmethod
    def select_all() -> List[SkinOffer]:
        skins = SkinOffer.select()
        return skins

    @staticmethod
    def delete_all():
        skins = SkinOffer.select()
        for s in skins:
            s.delete_instance()

    @staticmethod
    def update_by_asset(skin: SellOffer):
        try:
            item = SkinOffer.get(SkinOffer.AssetID == skin.AssetID)
            item.OfferID = skin.OfferID
            item.sellTime = skin.sellTime
            item.sellPrice = skin.sellPrice
            item.save()
        except DoesNotExist:
            pass

    @staticmethod
    def update_offer_id(skin: SellOffer):
        try:
            item = SkinOffer.get(SkinOffer.AssetID == skin.AssetID)
            item.OfferID = skin.OfferID
            item.title = skin.title
            item.fee = skin.fee
            item.sellPrice = skin.sellPrice
            # item.sell_time = skin.sell_time
            # item.sell_price = skin.sell_price
            # item.update_time = skin.update_time
            item.save()
        except DoesNotExist:
            pass
