from db import models
from time import time
__all__ = ['Item', 'ItemHistory', 'ItemOrder', 'ItemOffer']


class Item:
    def __init__(self, market_hash_name: str):
        self.market_hash_name = market_hash_name


class ItemHistory(Item):
    def __init__(self, market_hash_name: str, avg_price: float, history: dict = None, update_time: int = None):
        self.avg_price = avg_price
        self.history = history
        self.update_time = update_time
        super().__init__(market_hash_name)

    @staticmethod
    def new_from_last_sales(params: dict):
        params['update_time'] = int(time())
        return ItemHistory(**params)

    @staticmethod
    def new_item_from_skin(skin: models.Skin):
        item_data = {
            'market_hash_name': skin.market_hash_name,
            'avg_price': skin.avg_price,
            'history': skin.history,
            'update_time': skin.update_time
        }
        return ItemHistory(**item_data)


class ItemOrder(Item):
    def __init__(self, market_hash_name: str, min_price: float = None, max_price: float = None, best_order: float = None,
                 target_id: str = None):
        self.min_price = min_price
        self.max_price = max_price
        self.best_order = best_order
        self.target_id = target_id
        super().__init__(market_hash_name)

    '''@staticmethod
    def new_from_skin_order(skin: models.SkinOrder):
        item_data = {
            'market_hash_name': skin.market_hash_name,
            'min_price': skin.min_price,
            'max_price': skin.max_price,
            'best_order': skin.best_order,
            'target_id': skin.target_id
        }
        return ItemOrder(**item_data)'''

    @staticmethod
    def new_from_item_history(skin: ItemHistory, best_order: float):
        item_data = {
            'market_hash_name': skin.market_hash_name,
            'best_order': best_order
        }
        return ItemOrder(**item_data)


class ItemOffer:
    def __init__(self, asset_id: str, buy_price: float = None, buy_time: int = None, offer_id: str = None,
                 sell_time: int = None, sell_price: float = None, market_hash_name: str = None):
        self.asset_id = asset_id
        self.buy_price = buy_price
        self.buy_time = buy_time
        self.offer_id = offer_id
        self.sell_time = sell_time
        self.sell_price = sell_price
        self.market_hash_name = market_hash_name

    @staticmethod
    def new_from_skin_offer(skin: models.SkinOffer):
        item_data = {
            'market_hash_name': skin.market_hash_name,
            'asset_id': skin.asset_id,
            'buy_price': skin.buy_price,
            'buy_time': skin.buy_time,
            'offer_id': skin.offer_id,
            'sell_time': skin.sell_time,
            'sell_price': skin.sell_price
        }
        return ItemOffer(**item_data)
