from datetime import datetime
from db.selectors import SelectSkinOffer
from config import logger

skins = [i for i in SelectSkinOffer.select_all() if i.sell_time]
logger.write(f'Клличество проданных скинов: {len(skins)}')
total_profit = 0
date = datetime(2021, 3, 7).timestamp()
for i in skins:
    if i.sell_time >= date:
        if i.market_hash_name != 'Operation Hydra Case Key':
            profit = round(i.sell_price - i.buy_price, 2)
            total_profit += profit
            profit_percent = round(profit / i.buy_price * 100, 2)
            buy_date = datetime.utcfromtimestamp(i.buy_time).strftime('%d-%m-%Y %H:%M:%S')
            sell_date = datetime.utcfromtimestamp(i.sell_time).strftime('%d-%m-%Y %H:%M:%S')
            logger.write(f'{buy_date} - {sell_date} {i.market_hash_name} {i.buy_price} '
                         f'{round(i.sell_price, 2)} {profit} {profit_percent}')

logger.write(f'Полный профит: {round(total_profit, 2)} $.')
