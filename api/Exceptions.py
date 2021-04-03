import logging
import requests
import aiohttp

__all__ = ['Error', 'BadGatewayError', 'WrongResponseException', 'BadAPIKeyException', 'InsufficientFundsException',
           'UnknownError', 'TooManyRequests']


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class BadAPIKeyException(Error):
    """Bad api key exception."""

    def __init__(self):
        logging.error('Bad API key used or Unauthorized')


class WrongResponseException(Error):
    """Получен некорректный ответ от сервера."""

    def __init__(self, response: aiohttp.ClientResponse or requests.Response):
        """
        :param response: Received response.
        """
        logging.error('Wrong response was received')
        self.response = response


class UnknownError(Error):
    """Произошла неизвестная ошибка."""

    def __init__(self, text: str):
        """
        :param text: Error text.
        """
        logging.error('Response contains unknown error')
        logging.debug(text)
        self.response = text


class InsufficientFundsException(Error):
    """Недостаточно средств для совершения операции."""
    pass


class TooManyRequests(Error):
    """Недостаточно средств для совершения операции."""
    pass


class BadGatewayError(Error):
    """Cloudflare 502 error | Server bad gateway error."""

    def __init__(self, text: str = ''):
        """
        :param text: Error text
        """
        if text == '':
            logging.error('Bad gateway error')
        else:
            logging.error(text)
        self.response = text
