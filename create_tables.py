from db import models

from db.models import db


db.connect()
#models.Skin.drop_table()
models.Skin.create_table()
#models.SkinOrder.drop_table()
models.SkinOffer.create_table()
db.close()
