from api.dmarketapi import DMarketApi
from config import *
from modules.skinbase import SkinBase
import asyncio


bot = DMarketApi(PUBLIC_KEY, SECRET_KEY)
skin_base = SkinBase(bot)


async def create_pre_base():
    """Создание первичной базы предметов"""
    while True:
        try:
            await skin_base.update_base()
            await asyncio.sleep(skin_base.repeat)
        except Exception as e:
            logger.error(f' Не удалось обновить первичную базу: {e}. Спим 5 секунд.')
            await asyncio.sleep(5)


async def main_loop():
    tasks = await asyncio.gather(
            bot.get_money_loop(),
            create_pre_base(), return_exceptions=True
            )
    return tasks


def main():
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_loop())
    except KeyboardInterrupt:
        asyncio.run(bot.close())
        logger.info('Good bye')


if __name__ == '__main__':
    main()
