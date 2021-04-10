from datetime import datetime
from db.crud import SelectSkinOffer
from config import logger

skins = [i for i in SelectSkinOffer.select_all() if i.sellTime]
logger.info(f'Количество проданных скинов: {len(skins)}')
total_profit = 0
date = datetime(2021, 3, 7)
for i in skins:
    if i.sellTime >= date:
        if i.title != 'Operation Hydra Case Key':
            profit = round(i.sellPrice - i.buyPrice, 2)
            total_profit += profit
            profit_percent = round(profit / i.buyPrice * 100, 2)
            logger.info(f'{i.buyTime} - {i.sellTime} {i.title} {i.buyPrice} '
                        f'{round(i.sellPrice, 2)} {profit} {profit_percent}')

logger.info(f'Полный профит: {round(total_profit, 2)} $.')
