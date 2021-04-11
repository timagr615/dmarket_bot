import datetime
import json
from playhouse.sqlite_ext import Model, CharField, FloatField, TextField, DateTimeField, IntegerField

from db.database import db


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


class JSONField(TextField):
    def db_value(self, value):
        return json.dumps(value, default=default)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


class BaseModel(Model):
    class Meta:
        database = db


class Skin(BaseModel):
    title = CharField()
    game = CharField()
    LastSales = JSONField()
    avg_price = FloatField()
    update_time = DateTimeField()


class SkinOffer(BaseModel):
    title = CharField(null=True)
    AssetID = CharField()
    game = CharField(null=True)
    buyPrice = FloatField(null=True)
    buyTime = DateTimeField(null=True)
    OfferID = CharField(null=True)
    sellTime = DateTimeField(null=True)
    sellPrice = FloatField(null=True)
    fee = IntegerField(default=7)