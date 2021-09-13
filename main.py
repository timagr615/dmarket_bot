import asyncio

from api.dmarketapi import DMarketApi
from config import *
from modules.skinbase import SkinBase
from modules.orders import Orders
from modules.offers import History, Offers


bot = DMarketApi(PUBLIC_KEY, SECRET_KEY)
skin_base = SkinBase(bot)
orders = Orders(bot)
history = History(bot)
offers = Offers(bot)


async def create_pre_base():
    """Создание первичной базы предметов"""
    while True:
        logger.info('Обработка базы скинов')
        try:
            await skin_base.update()
            await asyncio.sleep(skin_base.repeat)
        except Exception as e:
            logger.exception(f' Не удалось обновить первичную базу: {e}. Спим 5 секунд.')
            await asyncio.sleep(5)


async def orders_loop():
    await asyncio.sleep(5)
    while True:
        logger.debug(f'orders loop')
        try:
            logger.debug(f'{bot.balance}')
            if bot.balance > orders.order_list.min_price + BuyParams.STOP_ORDERS_BALANCE:
                await orders.update_orders()
                await asyncio.sleep(5)
            else:
                targets = await orders.bot.user_targets(limit='1000')
                targets_inactive = await orders.bot.user_targets(limit='1000', status='TargetStatusInactive')
                await orders.bot.delete_target(targets.Items + targets_inactive.Items)
                logger.debug('Не хватает денег для выставления ордеров, откладываем аналитику')
                await asyncio.sleep(60 * 5)
        except Exception as e:
            logger.error(f' Не удалось получить базу ордеров: {e}. Спим 30 секунд.')
            await asyncio.sleep(5)


async def history_loop():
    while True:
        logger.debug('History loop')
        try:
            await history.save_skins()
            await asyncio.sleep(60*15)
        except Exception as e:
            logger.error(f' Не удалось получить историю: {e}. Спим 10 секунд.')
            await asyncio.sleep(30)


async def add_to_sell_loop():
    while True:
        try:
            await offers.add_to_sell()
            await asyncio.sleep(60*10)
        except Exception as e:
            logger.error(f' Не удалось выставить на продажу: {e}. Спим 10 секунд.')
            await asyncio.sleep(30)


async def update_offers_loop():
    while True:
        try:
            await offers.update_offers()
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f' Не удалось обновить продаваемые предметы: {e}. Спим 10 секунд.')
            await asyncio.sleep(30)


async def delete_offers_loop():
    while True:
        try:
            await asyncio.sleep(60*60*24*2)
            await offers.delete_all_offers()
        except Exception as e:
            logger.error(f'Не удалось удалить офферы: {e}')
            await asyncio.sleep(30)


async def main_loop():
    tasks = await asyncio.gather(
            bot.get_money_loop(),
            history_loop(),
            orders_loop(),
            add_to_sell_loop(),
            update_offers_loop(),
            create_pre_base(), return_exceptions=True
            )
    return tasks


def main():
    try:
        logger.info('Запуск бота')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_loop())
    except KeyboardInterrupt:
        asyncio.run(bot.close())
        logger.info('Good bye')


if __name__ == '__main__':
    main()
