from playhouse.sqlite_ext import *

import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db = SqliteExtDatabase(BASE_DIR + '/skins.db')


class BaseModel(Model):
    class Meta:
        database = db


class Skin(BaseModel):
    market_hash_name = CharField()
    avg_price = FloatField()
    history = JSONField()
    update_time = IntegerField()


class SkinOffer(BaseModel):
    market_hash_name = CharField(null=True)
    asset_id = CharField()
    buy_price = FloatField(null=True)
    buy_time = IntegerField(null=True)
    offer_id = CharField(null=True)
    sell_time = IntegerField(null=True)
    sell_price = FloatField(null=True)