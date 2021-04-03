from loguru import logger


class BaseLogger:
    def __init__(self, debug, log_file):
        self.debug = debug
        if log_file:
            if self.debug:
                self.logger = logger.add("logs/debug.log", format="{time} {level} {message}", level="DEBUG",
                                         rotation="1 MB")
            else:
                self.logger = logger.add("logs/error.log", format="{time} {level} {message}", level="WARNING",
                                         rotation="1 MB")

    @staticmethod
    def get_log(msg: str, level: str):

        if level.lower() == 'debug':
            pass
        elif level.lower() == 'info':
            logger.info(msg)
        elif level.lower() == 'warning':
            logger.warning(msg)
        elif level.lower() == 'error':
            logger.error(msg)
        elif level.lower() == 'exception':
            logger.exception(msg)
        else:
            logger.critical(msg)

    def write(self, msg: str, level: str = 'info'):
        if self.debug:
            if level.lower() == 'debug':
                logger.debug(msg)
        self.get_log(msg, level)
