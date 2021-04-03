from pyti.simple_moving_average import simple_moving_average as sma


def mov_av_5(history: list) -> list:
    prices = [int(i['Price']['Amount'])/100 for i in history]
    prices.reverse()
    mov_av = [i for i in list(sma(prices, 5))]
    mov_av.reverse()
    return mov_av
