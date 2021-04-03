from typing import List
from furl import furl
import asyncio
import aiohttp
import requests
import json
from datetime import datetime
from asyncio import CancelledError, shield
from nacl.bindings import crypto_sign
import urllib.parse
from config import proxies, GAME, API_URL, API_URL_TRADING, BaseSettings, logger
import time
from api.Exceptions import *
from api.Item import ItemOffer


def request_possibility_check(func):
    """Декоратор проверки возможности отправить запрос."""
    async def magic(self, *args, **kwargs):
        while not self.request_possibility():
            await asyncio.sleep(0.3)
        return await func(self, *args, **kwargs)
    return magic


class DMarketApi:
    def __init__(self, public_key: str, secret_key: str):
        self.PUBLIC_KEY = public_key
        self.SECRET_KEY = secret_key
        self.MAX_REQUESTS = 15
        self.SELL_FEE = 5
        self.RPS = BaseSettings.RPS
        self.request_counter = 0
        self.request_history_counter = 0
        self.balance = 0

        conn = aiohttp.TCPConnector(limit=self.RPS, limit_per_host=self.RPS)
        self.session = aiohttp.ClientSession(connector=conn)

    async def close(self):
        return await self.session.close()

    def generate_headers(self, method: str, api_path: str, params: dict = None, body: dict = None):
        nonce = str(round(datetime.now().timestamp()))
        string_to_sign = method + api_path
        string_to_sign = str(furl(string_to_sign).add(params))
        if body:
            string_to_sign += json.dumps(body)
        string_to_sign += nonce
        signature_prefix = "dmar ed25519 "
        encoded = string_to_sign.encode('utf-8')
        secret_bytes = bytes.fromhex(self.SECRET_KEY)
        signature_bytes = crypto_sign(encoded, secret_bytes)
        signature = signature_bytes[:64].hex()

        headers = {
            "X-Api-Key": self.PUBLIC_KEY,
            "X-Request-Sign": signature_prefix + signature,
            "X-Sign-Date": nonce
        }
        return headers

    async def refresh_request_counter_loop(self) -> None:
        """Loop для обновления счетчика запросов."""

        while True:
            self.request_counter = 0
            try:
                await shield(asyncio.sleep(1))
            except CancelledError:
                return

    def request_possibility(self) -> bool:
        """
        Проверяет возможность отправки запроса, и обновляет счетчик.
        :return: bool
        """
        if self.request_counter < self.MAX_REQUESTS:
            self.request_counter += 1
            logger.write(self.request_counter)
            return True
        else:
            return False

    @staticmethod
    async def validate_response(response: aiohttp.ClientResponse) -> dict:
        """
        Проверяет ответ на наличие ошибок.
        :param response: Received response.
        :raises BadAPIKey: Bad api key used.
        :return: JSON like dict from response.
        """
        headers = dict(response.headers)
        if 'RateLimit-Remaining' not in headers:
            await asyncio.sleep(5)
        if 'RateLimit-Remaining' in headers and headers['RateLimit-Remaining'] in ['1', '0']:
            # logger.write(f'RATE LIMIT {headers["RateLimit-Remaining"]}', 'warning')
            await asyncio.sleep(int(headers['RateLimit-Reset']))

        if response.status == 502 or response.status == 500:
            raise BadGatewayError()
        if response.status == 429:
            raise TooManyRequests()
        if response.status != 200 and 'application/json' not in response.headers['content-type']:
            raise WrongResponseException(response)
        if response.status == 401:
            raise BadAPIKeyException()
        body = await response.json()

        '''if 'error' in body:
            if body['error'] == 'Bad KEY':
                raise BadAPIKeyException()
            raise UnknownError(body['error'])'''

        return body

    @staticmethod
    async def validate_response_sync(response: requests.Response) -> dict:
        """
        Проверяет ответ на наличие ошибок.
        :param response: Received response.
        :raises BadAPIKey: Bad api key used.
        :return: JSON like dict from response.
        """
        headers = dict(response.headers)
        if 'RateLimit-Remaining' not in headers:
            await asyncio.sleep(5)
        if 'RateLimit-Remaining' in headers and headers['RateLimit-Remaining'] in ['1', '0']:
            # logger.write(f'RATE LIMIT {headers["RateLimit-Remaining"]}', 'warning')
            await asyncio.sleep(int(headers['RateLimit-Reset']))
        if response.status_code == 502:
            raise BadGatewayError()
        if response.status_code == 429:
            logger.write(f'RATE LIMIT {headers}', 'error')
            raise TooManyRequests()
        if response.status_code != 200 and 'application/json' not in response.headers['content-type']:
            raise WrongResponseException(response)
        if response.status_code == 401:
            raise BadAPIKeyException()
        body = response.json()

        '''if 'error' in body:
            if body['error'] == 'Bad KEY':
                raise BadAPIKeyException()
            raise UnknownError(body['error'])'''

        return body

    # @request_possibility_check
    async def api_call(self, url: str, method: str, headers: dict, params: dict = None, body: dict = None,
                       aio: bool = True):
        if not aio:
            response = requests.get(url, params=params, headers=headers)
            await asyncio.sleep(0.001)
            return await self.validate_response_sync(response)
        if method == 'GET':
            async with self.session.get(url, params=params, headers=headers) as response:
                data = await self.validate_response(response)
                return data
        else:
            async with self.session.post(url, params=params, json=body, headers=headers) as response:
                data = await self.validate_response(response)
                return data

    # ACCOUNT
    # ----------------------------------------------------------------

    async def user(self):
        method = 'GET'
        url_path = '/account/v1/user'
        headers = self.generate_headers(method, url_path)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers)
        return response

    async def get_balance(self):
        method = 'GET'
        url_path = '/account/v1/balance'
        headers = self.generate_headers(method, url_path)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers)
        if 'usd' in response:
            self.balance = int(response['usd'])/100
            logger.write(f'BALANCE: {self.balance}', 'debug')
            return int(response['usd'])/100
        else:
            logger.write(f'{response}', 'debug')

    async def get_money_loop(self) -> None:
        while True:
            try:
                logger.write('get money_loop', 'debug')
                await self.get_balance()
                await asyncio.sleep(60*5)
            except (BadGatewayError, WrongResponseException, TooManyRequests):
                continue
            except UnknownError:
                continue
            except KeyboardInterrupt:
                break
            except CancelledError:
                break
        return

    # MARKET METHODS
    # ------------------------------------------------------------------

    async def last_sales(self, item_name: str, game: str = 'a8db', currency: str = 'USD') -> dict:
        """Метод для получения и обработки ответа для последних продаж."""

        method = 'GET'
        params = {'GameID': game, 'Title': item_name, 'Currency': currency}
        url_path = '/marketplace-api/v1/last-sales'
        headers = self.generate_headers(method, url_path, params)
        url = API_URL_TRADING + url_path
        response = await self.api_call(url, method, headers, params)
        return response

    async def sales_history(self, item_name: str, game: str = 'a8db', currency: str = 'USD',
                            period: str = '1M') -> dict:
        """Метод для получения и обработки ответа для последних продаж."""

        method = 'GET'
        params = {'GameID': game, 'Title': item_name, 'Currency': currency, 'Period': period}
        url_path = '/marketplace-api/v1/sales-history'
        headers = self.generate_headers(method, url_path, params)
        url = API_URL_TRADING + url_path
        response = await self.api_call(url, method, headers, params)
        return response

    async def market_offers(self, game: str = 'a8db', name: str = '', limit: int = 100, offset: int = 0,
                            orderby: str = 'price', orderdir: str = 'asc', tree_filters: str = '',
                            currency: str = 'USD', price_from: int = 0, price_to: int = 0, types: str = 'dmarket',
                            cursor: str = ''):
        method = 'GET'
        url_path = '/exchange/v1/market/items'
        params = {'gameId': game, 'title': name, 'limit': limit, 'orderBy': orderby, 'currency': currency,
                  'offset': offset, 'orderDir': orderdir, 'treeFilters': tree_filters, 'priceFrom': price_from,
                  'priceTo': price_to, 'types': types, 'cursor': cursor}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        try:
            return response['objects'], response['cursor']
        except KeyError:
            return response['objects'], None

    # BUY ITEMS
    # ------------------------------------------------------------------

    async def agregated_prices(self, names: List[str], limit: int = 100, offset: str = None) -> dict:
        method = "GET"

        url_path = '/price-aggregator/v1/aggregated-prices'
        if len(names) > 100:
            addiction_items = await self.agregated_prices(names[100:])
        else:
            addiction_items = []
        params = {'Titles': names[:100], 'Limit': limit}
        if offset:
            params['Offset'] = offset
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params, aio=False)
        return response['AggregatedTitles'] + addiction_items

    async def offers_by_title(self, name: str, limit: int = 100, cursor: str = ''):
        method = 'GET'
        url_path = '/exchange/v1/offers-by-title'
        params = {'Title': name, 'Limit': limit, 'Cursor': cursor}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return response["objects"]

    async def user_targets(self, game: str = 'a8db', price_from: float = None, price_to: float = None,
                           title: str = None, target_id: str = None, status: str = 'TargetStatusActive',
                           limit: str = '100', cursor: str = '', currency: str = 'USD'):
        method = 'GET'
        url_path = '/marketplace-api/v1/user-targets'
        params = {'BasicFilters.Status': status, 'GameId': game, 'BasicFilters.Currency': currency,
                  'Limit': limit}
        if price_from:
            params['BasicFilters.PriceFrom'] = price_from
        if price_to:
            params['BasicFilters.PriceTo'] = price_to
        if title:
            params['BasicFilters.Title'] = title
        if target_id:
            params['BasicFilters.TargetID'] = target_id
        if cursor:
            params['Cursor'] = cursor
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return response

    async def closed_targets(self, limit: str = '100', order_dir: str = 'desc'):
        method = 'GET'
        url_path = '/marketplace-api/v1/user-targets/closed'
        params = {'Limit': limit, 'OrderDir': order_dir}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return response

    async def create_target(self, body: dict):
        """
        BODY TYPE
        {
          "Targets": [
            {
              "Amount": "string",
              "Price": {
                "Currency": "string",
                "Amount": 0
              },
              "Attributes": [
                {
                  "Name": "string",
                  "Value": "string"
                }
              ]
            }
          ]
        }
        :param body:
        :return:
        """
        method = 'POST'
        url_path = '/marketplace-api/v1/user-targets/create'
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return response

    async def delete_target(self, target_ids: List[str]):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-targets/delete'
        if len(target_ids) > 150:
            addiction_items = await self.delete_target(target_ids[150:])
        else:
            addiction_items = []
        targets = [{'TargetID': i} for i in target_ids[:150]]
        body = {"Targets": targets}
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        # logger.write(f'delete_targets() {url}', 'debug')
        response = await self.api_call(url, method, headers, body=body)
        return response['Result'] + addiction_items

    # SELL ITEMS
    # ---------------------------------------------

    async def user_inventory(self, game: str = 'a8db', in_market: bool = True, limit: str = '100'):
        method = 'GET'
        url_path = '/marketplace-api/v1/user-inventory'
        params = {'GameID': game, 'BasicFilters.InMarket': 'true', 'Limit': limit}
        headers = self.generate_headers(method, url_path)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers)
        return response

    async def user_inventory_sync(self):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-inventory/sync'
        headers = self.generate_headers(method, url_path)
        url = API_URL + url_path
        body = {"Type": "Inventory", "GameID": "a8db"}
        response = await self.api_call(url, method, headers, body=body, aio=False)
        return response

    async def user_items(self):
        method = 'GET'
        url_path = '/exchange/v1/user/items'
        params = {'GameId': 'a8db', 'currency': 'USD', 'limit': '50'}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params=params)
        return response

    async def user_offers(self, game: str = 'a8db', status: str = 'OfferStatusDefault',
                          sort_type: str = 'UserOffersSortTypeDateNewestFirst', limit: str = '20'):
        method = 'GET'
        url_path = '/marketplace-api/v1/user-offers'
        params = {'GameId': game, 'Status': status, 'Limit': limit, 'SortType': sort_type}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params=params)
        return response

    async def user_offers_create(self, items: List[ItemOffer]):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-offers/create'
        skins = [{'AssetID': item.asset_id,
                  'Price': {'Currency': 'USD', 'Amount': item.sell_price}} for item in items]
        body = {'Offers': skins}
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return response

    async def user_offers_edit(self, items: List[ItemOffer]):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-offers/edit'
        skins = [{'OfferID': item.offer_id, 'AssetID': item.asset_id,
                  'Price': {'Currency': 'USD', 'Amount': item.sell_price}} for item in items]
        body = {'Offers': skins}
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return response

    async def user_offers_delete(self, items: list):
        method = 'DELETE'
        url_path = '/exchange/v1/offers'
        skins = [{'itemId': item.asset_id, 'offerId': item.offer_id,
                  'Price': {'Currency': 'USD', 'Amount': item.price}} for item in items]
        body = {'force': 'true', 'Offers': skins}
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return response
