from pyti.simple_moving_average import simple_moving_average as sma
from typing import List
from api.schemas import LastSale


def mov_av_5(history: List[LastSale]) -> list:
    prices = [i.Price.Amount for i in history]
    prices.reverse()
    mov_av = [i for i in list(sma(prices, 5))]
    mov_av.reverse()
    return mov_av
