import asyncio
import requests
import json
from datetime import datetime
from asyncio import CancelledError, shield
from nacl.bindings import crypto_sign
import urllib.parse
from config import proxies, GAME, API_URL, API_URL_TRADING
import time
from api.Exceptions import *


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
        self.request_counter = 0
        self.request_history_counter = 0
        self.proxies = proxies
        self.GAME = GAME

    def generate_headers(self, method: str, api_path: str, params: dict = None, body: dict = None):
        nonce = str(round(datetime.now().timestamp()))

        string_to_sign = method + api_path
        if params:
            string_to_sign += '?' + urllib.parse.urlencode(params)
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
            return True
        else:
            return False

    @staticmethod
    def validate_response(response: requests.Response) -> dict:
        """
        Проверяет ответ на наличие ошибок.
        :param response: Received response.
        :raises BadAPIKey: Bad api key used.
        :return: JSON like dict from response.
        """
        if response.status_code == 502:
            raise BadGatewayError()
        if response.status_code != 200 and 'application/json' not in response.headers['content-type']:
            print(response.text)
            raise WrongResponseException(response)
        if response.status_code == 401:
            raise BadAPIKeyException()
        body = response.json()

        '''if 'error' in body:
            if body['error'] == 'Bad KEY':
                raise BadAPIKeyException()
            raise UnknownError(body['error'])'''

        return body

    @request_possibility_check
    async def api_call(self, url: str, method: str, headers: dict, params: dict = None, body: dict = None):
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers)
            print(response.url)
            await asyncio.sleep(0.001)
            return self.validate_response(response)
        else:
            response = requests.post(url, params=params, json=body, headers=headers)
            await asyncio.sleep(0.001)
            return self.validate_response(response)

    async def balance(self):
        method = 'GET'
        url_path = '/account/v1/balance'
        headers = self.generate_headers(method, url_path)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers)
        return response

    async def last_sales(self, item_name: str) -> dict:
        """Метод для получения и обработки ответа для последних продаж."""

        method = 'GET'
        params = {'GameID': self.GAME, 'Title': item_name, 'Currency': 'USD'}
        url_path = '/marketplace-api/v1/last-sales'
        headers = self.generate_headers(method, url_path, params)
        url = API_URL_TRADING + url_path
        response = await self.api_call(url, method, headers, params)
        return response

    async def sales_history(self, item_name: str, period: str) -> dict:
        """Метод для получения и обработки ответа для последних продаж."""

        method = 'GET'
        params = {'GameID': self.GAME, 'Title': item_name, 'Currency': 'USD', 'Period': period}
        url_path = '/marketplace-api/v1/sales-history'
        headers = self.generate_headers(method, url_path, params)
        url = API_URL_TRADING + url_path
        response = await self.api_call(url, method, headers, params)
        return response

    async def agregated_prices(self, item_name: str) -> dict:
        method = "GET"
        params = {'Titles': item_name, 'Limit': 10}
        url_path = '/price-aggregator/v1/aggregated-prices'
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return response['AggregatedTitles']

    async def offers_by_title(self, name: str):
        method = 'GET'
        url_path = '/exchange/v1/offers-by-title'
        params = {'Title': name, 'Limit': 1}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return response["objects"][0]

    async def create_target(self, body: dict):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-targets/create'
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return response

    async def user_targets(self):
        method = 'GET'
        url_path = '/marketplace-api/v1/user-targets'
        params = {'BasicFilters.Status': 'TargetStatusActive', 'SortType': 'UserTargetsSortTypeDefault'}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return response

    async def delete_target(self, targetid: str):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-targets/delete'
        body = {"Targets": [{"TargetID": targetid}]}
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return response

    async def market_offers(self, name: str = ''):
        method = 'GET'
        url_path = '/exchange/v1/market/items'
        params = {'gameId': self.GAME, 'title': name, 'limit': 1, 'orderBy': name, 'currency': 'USD'}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return response['objects']
