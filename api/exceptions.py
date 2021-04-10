from config import logger

__all__ = ['Error', 'BadGatewayError', 'WrongResponseException', 'BadAPIKeyException', 'InsufficientFundsException',
           'UnknownError', 'TooManyRequests', 'BadRequestError']


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class BadAPIKeyException(Error):
    """Bad api key exception."""

    def __init__(self):
        logger.error('Bad API key used or Unauthorized')


class WrongResponseException(Error):
    """Получен некорректный ответ от сервера."""

    def __init__(self, response_text: str):
        """
        :param response: Received response.
        """
        logger.error(f'Wrong response was received {response_text}')
        self.response = response_text


class UnknownError(Error):
    """Произошла неизвестная ошибка."""

    def __init__(self, text: str):
        """
        :param text: Error text.
        """
        logger.error('Response contains unknown error')
        logger.debug(text)
        self.response = text


class InsufficientFundsException(Error):
    """Недостаточно средств для совершения операции."""
    pass


class TooManyRequests(Error):
    """Недостаточно средств для совершения операции."""
    pass


class BadGatewayError(Error):

    def __init__(self, text: str = ''):
        """
        :param text: Error text
        """
        if text == '':
            logger.error('Bad gateway error')
        else:
            logger.error(text)
        self.response = text


class BadRequestError(Error):
    """Неправильный вызов метода."""
    pass
