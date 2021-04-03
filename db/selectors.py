from db import models
from api.Item import ItemHistory, ItemOrder, ItemOffer
from typing import List
from peewee import DoesNotExist
from db.models import db

__all__ = ['SelectSkin', 'SelectSkinOffer']


def db_connection(func):

    def wrapper(*args, **kwargs):
        db.connect()
        f = func(*args, **kwargs)
        db.close()
        return f

    return wrapper


class SelectSkin:

    @staticmethod
    def create_all_skins(items: List[ItemHistory]) -> None:
        skins = [models.Skin(
            market_hash_name=item.market_hash_name,
            avg_price=item.avg_price,
            history=item.history,
            update_time=item.update_time
        ) for item in items]
        with db.atomic():
            models.Skin.bulk_create(skins, batch_size=500)

    @staticmethod
    def create_skin(item: ItemHistory) -> None:
        new_skin = models.Skin.create(
            market_hash_name=item.market_hash_name,
            avg_price=item.avg_price,
            history=item.history,
            update_time=item.update_time
        )
        new_skin.save()

    @staticmethod
    def skin_existence(item: dict):
        skin = models.Skin.select().where(models.Skin.market_hash_name == item['market_hash_name'])
        if skin:
            return True
        else:
            return False

    @staticmethod
    def find_by_name(items: List[ItemHistory]):
        skins_to_update = list()
        skin_to_create = list()
        for item in items:
            try:
                skin = models.Skin.get(models.Skin.market_hash_name == item.market_hash_name)
                skin.avg_price = item.avg_price
                skin.history = item.history
                skin.update_time = item.update_time
                skins_to_update.append(skin)
                # skin.save()
            except DoesNotExist:
                skin_to_create.append(item)
                #self.create_skin(item)
        with db.atomic():
            models.Skin.bulk_update(skins_to_update,
                                    fields=[models.Skin.avg_price, models.Skin.history, models.Skin.update_time],
                                    batch_size=500)
        with db.atomic():
            models.Skin.bulk_create(skin_to_create, batch_size=500)

    @staticmethod
    def select_all():
        skins = models.Skin.select()
        return [ItemHistory.new_item_from_skin(skin) for skin in skins]

    @staticmethod
    def select_update_time(now, delta):
        skins = models.Skin.select().where(models.Skin.update_time < (now - delta))
        if skins:
            return [ItemHistory.new_item_from_skin(skin) for skin in skins]
        else:
            return []


class SelectSkinOffer:

    @staticmethod
    def create_skin(item: ItemOffer) -> None:
        new_skin = models.SkinOffer.create(
            market_hash_name=item.market_hash_name,
            asset_id=item.asset_id,
            buy_price=item.buy_price,
            buy_time=item.buy_time,
            offer_id=item.offer_id,
            sell_time=item.sell_time,
            sell_price=item.sell_price
        )
        new_skin.save()

    @staticmethod
    def update_sold(skins):
        with db.atomic():
            models.SkinOffer.bulk_update(skins, fields=[models.SkinOffer.market_hash_name, models.SkinOffer.sell_price,
                                                        models.SkinOffer.sell_time, models.SkinOffer.offer_id])

    @staticmethod
    def select_not_sell() -> List[ItemOffer]:
        skins = models.SkinOffer.select().where(models.SkinOffer.sell_time == None)
        return [ItemOffer.new_from_skin_offer(s) for s in skins]

    @staticmethod
    def select_all() -> List[ItemOffer]:
        skins = models.SkinOffer.select()
        #return [ItemOffer.new_from_skin_offer(s) for s in skins]
        return skins

    @staticmethod
    def delete_all():
        skins = models.SkinOffer.select()
        for s in skins:
            s.delete_instance()

    @staticmethod
    def update_by_asset(skin: ItemOffer):
        try:
            item = models.SkinOffer.get(models.SkinOffer.asset_id == skin.asset_id)
            # item.class_id = skin.class_id
            # item.instance_id = skin.instance_id
            item.offer_id = skin.offer_id
            item.sell_time = skin.sell_time
            item.sell_price = skin.sell_price
            item.save()
        except DoesNotExist:
            pass

    @staticmethod
    def update_offer_id(skin: ItemOffer):
        try:
            item = models.SkinOffer.get(models.SkinOffer.asset_id == skin.asset_id)
            item.offer_id = skin.offer_id
            item.market_hash_name = skin.market_hash_name
            item.sell_price = skin.sell_price
            # item.sell_time = skin.sell_time
            # item.sell_price = skin.sell_price
            # item.update_time = skin.update_time
            item.save()
        except DoesNotExist:
            pass
