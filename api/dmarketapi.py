import asyncio
import aiohttp
import requests
import json
from datetime import datetime
from asyncio import CancelledError
from typing import List, Union
from furl import furl
from nacl.bindings import crypto_sign

from config import API_URL, API_URL_TRADING, logger
from api.exceptions import *
from api.schemas import Balance, Games, LastSales, SalesHistory, MarketOffers, AggregatedTitle, \
    UserTargets, ClosedTargets, Target, UserItems, CreateOffers, CreateOffersResponse, EditOffers, EditOffersResponse, \
    DeleteOffers, CreateTargets, CumulativePrices, OfferDetails, OfferDetailsResponse


class DMarketApi:
    def __init__(self, public_key: str, secret_key: str):
        self.PUBLIC_KEY = public_key
        self.SECRET_KEY = secret_key
        self.SELL_FEE = 7
        self.balance = 0
        self.session = aiohttp.ClientSession()

    async def close(self):
        return await self.session.close()

    def generate_headers(self, method: str, api_path: str, params: dict = None, body: dict = None) -> dict:
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

    @staticmethod
    def catch_exception(response_status: int, headers: dict, response_text: str):
        if response_status == 400:
            raise BadRequestError()
        if response_status == 502 or response_status == 500:
            raise BadGatewayError()
        if response_status == 429:
            raise TooManyRequests()
        if response_status == 401:
            raise BadAPIKeyException()
        if response_status != 200 and 'application/json' not in headers['content-type']:
            raise WrongResponseException(response_text)

    async def validate_response(self, response: aiohttp.ClientResponse or requests.Response) -> dict:
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
            await asyncio.sleep(int(headers['RateLimit-Reset']))
        if isinstance(response, requests.Response):
            response_status = response.status_code
            self.catch_exception(response_status, headers, response.text)
            body = response.json()
        else:
            response_status = response.status
            self.catch_exception(response_status, headers, response.text)
            body = await response.json()

        return body

    async def api_call(self, url: str, method: str, headers: dict, params: dict = None, body: dict = None,
                       aio: bool = True) -> dict:
        if not aio:
            response = requests.get(url, params=params, headers=headers)
            await asyncio.sleep(0.001)
            return await self.validate_response(response)
        if method == 'GET':
            async with self.session.get(url, params=params, headers=headers) as response:
                data = await self.validate_response(response)
                return data
        elif method == 'DELETE':
            async with self.session.delete(url, params=params, json=body, headers=headers) as response:
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
            self.balance = Balance(**response).usd
            logger.debug(f'BALANCE: {self.balance}')
            return self.balance
        else:
            logger.debug(f'{response}')

    async def get_money_loop(self) -> None:
        while True:
            try:
                # logger.debug('get money_loop')
                await self.get_balance()
                await asyncio.sleep(60*5)
            except KeyboardInterrupt:
                break
            except CancelledError:
                break
            except Exception:
                continue
        return

    # MARKET METHODS
    # ------------------------------------------------------------------

    async def last_sales(self, item_name: str, game: Games = Games.CS, currency: str = 'USD') -> LastSales:
        """Метод для получения и обработки ответа для последних продаж."""

        method = 'GET'
        params = {'GameID': game.value, 'Title': item_name, 'Currency': currency}
        url_path = '/marketplace-api/v1/last-sales'
        headers = self.generate_headers(method, url_path, params)
        url = API_URL_TRADING + url_path
        response = await self.api_call(url, method, headers, params)
        return LastSales(**response)

    async def sales_history(self, item_name: str, game: Games = Games.CS, currency: str = 'USD',
                            period: str = '1M') -> SalesHistory:
        """Метод для получения и обработки ответа для последних продаж."""

        method = 'GET'
        params = {'GameID': game.value, 'Title': item_name, 'Currency': currency, 'Period': period}
        url_path = '/marketplace-api/v1/sales-history'
        headers = self.generate_headers(method, url_path, params)
        url = API_URL_TRADING + url_path
        response = await self.api_call(url, method, headers, params)
        return SalesHistory(**response)

    async def market_offers(self, game: Games = Games.CS, name: str = '', limit: int = 100, offset: int = 0,
                            orderby: str = 'price', orderdir: str = 'asc', tree_filters: str = '',
                            currency: str = 'USD', price_from: int = 0, price_to: int = 0, types: str = 'dmarket',
                            cursor: str = '') -> MarketOffers:
        method = 'GET'
        url_path = '/exchange/v1/market/items'
        params = {'gameId': game.value, 'title': name, 'limit': limit, 'orderBy': orderby, 'currency': currency,
                  'offset': offset, 'orderDir': orderdir, 'treeFilters': tree_filters, 'priceFrom': price_from,
                  'priceTo': price_to, 'types': types, 'cursor': cursor}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return MarketOffers(**response)

    async def agregated_prices(self, names: List[str], limit: int = 100, offset: str = None) -> List[AggregatedTitle]:
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
        return [AggregatedTitle(**i) for i in response['AggregatedTitles']] + addiction_items

    async def offers_by_title(self, name: str, limit: int = 100, cursor: str = '') -> MarketOffers:
        method = 'GET'
        url_path = '/exchange/v1/offers-by-title'
        params = {'Title': name, 'Limit': limit, 'Cursor': cursor}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return MarketOffers(**response)

    async def user_targets(self, game: Games = Games.CS, price_from: float = None, price_to: float = None,
                           title: str = None, target_id: str = None, status: str = 'TargetStatusActive',
                           limit: str = '100', cursor: str = '', currency: str = 'USD'):
        method = 'GET'
        url_path = '/marketplace-api/v1/user-targets'
        params = {'BasicFilters.Status': status, 'GameId': game.value, 'BasicFilters.Currency': currency,
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
        return UserTargets(**response)

    async def closed_targets(self, limit: str = '100', order_dir: str = 'desc') -> ClosedTargets:
        method = 'GET'
        url_path = '/marketplace-api/v1/user-targets/closed'
        params = {'Limit': limit, 'OrderDir': order_dir}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return ClosedTargets(**response)

    async def create_target(self, body: CreateTargets):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-targets/create'
        headers = self.generate_headers(method, url_path, body=body.dict())
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body.dict())
        return response

    async def delete_target(self, targets: List[Target]):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-targets/delete'
        if len(targets) > 150:
            addiction_items = await self.delete_target(targets[150:])
        else:
            addiction_items = []
        targets = [{'TargetID': i.TargetID} for i in targets[:150]]
        body = {"Targets": targets}
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        # logger.write(f'delete_targets() {url}', 'debug')
        response = await self.api_call(url, method, headers, body=body)
        return response['Result'] + addiction_items

    async def cumulative_price(self, name: str, game: str):
        method = 'GET'
        url_path = '/marketplace-api/v1/cumulative-price-levels'
        params = {'Title': name, 'GameID': game}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params)
        return CumulativePrices(**response)

    # SELL ITEMS
    # ---------------------------------------------

    async def user_inventory(self, game: Games = Games.CS, in_market: bool = 'true', limit: str = '100') -> UserItems:
        method = 'GET'
        url_path = '/marketplace-api/v1/user-inventory'
        params = {'GameID': game.value, 'BasicFilters.InMarket': in_market, 'Limit': limit}
        headers = self.generate_headers(method, url_path, params=params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params=params)
        return UserItems(**response)

    async def user_items(self, game: Games = Games.CS) -> MarketOffers:
        method = 'GET'
        url_path = '/exchange/v1/user/items'
        params = {'GameId': game.value, 'currency': 'USD', 'limit': '50'}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params=params)
        return MarketOffers(**response)

    async def user_offers(self, game: Games = Games.CS, status: str = 'OfferStatusDefault',
                          sort_type: str = 'UserOffersSortTypeDateNewestFirst', limit: str = '20'):
        method = 'GET'
        url_path = '/marketplace-api/v1/user-offers'
        params = {'GameId': game.value, 'Status': status, 'Limit': limit, 'SortType': sort_type}
        headers = self.generate_headers(method, url_path, params)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, params=params)
        return UserItems(**response)

    async def user_offers_create(self, body: CreateOffers):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-offers/create'

        body = body.dict()
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return CreateOffersResponse(**response)

    async def user_offers_edit(self, body: EditOffers):
        method = 'POST'
        url_path = '/marketplace-api/v1/user-offers/edit'
        body = body.dict()
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return EditOffersResponse(**response)

    async def user_offers_delete(self, body: DeleteOffers):
        method = 'DELETE'
        url_path = '/exchange/v1/offers'
        body = body.dict()
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return response

    async def user_offers_details(self, body: OfferDetails):
        method = 'POST'
        url_path = '/exchange/v1/offers/details'
        body = body.dict()
        headers = self.generate_headers(method, url_path, body=body)
        url = API_URL + url_path
        response = await self.api_call(url, method, headers, body=body)
        return OfferDetailsResponse(**response)
        #return response
