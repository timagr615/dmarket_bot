from api.dmarketapiv2 import DMarketApi
from config import *
from db.selectors import SelectSkinOffer
from modules.skin_base import SkinBase
from modules.orders import Orders
from modules.offers import History, Offers
import asyncio


bot = DMarketApi(PUBLIC_KEY, SECRET_KEY)
skin_base = SkinBase(bot)
# order_analytic = OrderAnalytics(bot)
orders = Orders(bot)
history = History(bot)
offers = Offers(bot)


async def create_pre_base():
    """Создание первичной базы предметов"""
    while True:
        try:
            await skin_base.update_other_items()
            await asyncio.sleep(skin_base.repeat)
        except Exception as e:
            logger.write(f' Не удалось обновить первичную базу: {e}. Спим 5 секунд.', 'error')
            await asyncio.sleep(5)


async def orders_loop():
    await asyncio.sleep(5)
    while True:
        logger.write(f'orders loop', 'debug')
        try:
            logger.write(f'{bot.balance}', 'debug')
            if bot.balance > orders.order_list.min_price + 10:
                await orders.update_orders()
                await asyncio.sleep(5)
            else:
                targets = await orders.bot.user_targets(limit='1000')
                targets_inactive = await orders.bot.user_targets(limit='1000', status='TargetStatusInactive')
                await orders.delete_targets(targets['Items'], targets_inactive['Items'])
                logger.write('Не хватает денег для выставления ордеров, откладываем аналитику')
                await asyncio.sleep(60*5)
        except Exception as e:
            logger.write(f' Не удалось получить базу ордеров: {e}. Спим 30 секунд.', 'exception')
            await asyncio.sleep(5)


async def history_loop():
    while True:
        try:
            # logger.write('history loop')
            await history.save_skins()
            await asyncio.sleep(60*15)
        except Exception as e:
            logger.write(f' Не удалось получить историю: {e}. Спим 10 секунд.', 'error')
            await asyncio.sleep(30)


async def add_to_sell_loop():
    while True:
        try:
            # logger.write('add to sell loop')
            await offers.add_to_sell()
            # await offers.update_sell_id()
            await asyncio.sleep(60*10)
        except Exception as e:
            logger.write(f' Не удалось выставить на продажу: {e}. Спим 10 секунд.', 'error')
            await asyncio.sleep(30)


async def update_offers_loop():
    while True:
        try:
            await offers.update_offers()
            await asyncio.sleep(5)
        except Exception as e:
            logger.write(f' Не удалось обновить продаваемые предметы: {e}. Спим 10 секунд.', 'error')
            await asyncio.sleep(30)


async def main_loop():
    tasks = await asyncio.gather(
            bot.get_money_loop(),
            # bot.refresh_request_counter_loop(),
            history_loop(),
            add_to_sell_loop(),
            update_offers_loop(),
            create_pre_base(),
            orders_loop(), return_exceptions=True
            #update_orders_loop(),
            )
    return tasks


def main():
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_loop())
    except KeyboardInterrupt:
        asyncio.run(bot.close())
        logger.write('Good bye')


if __name__ == '__main__':
    main()
