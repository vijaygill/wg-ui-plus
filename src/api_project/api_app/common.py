from functools import wraps
import logging

APP_NAME = "wg-ui-plus"
IP_ADDRESS_INTERNET = "0.0.0.0/0"
TARGET_INTERNET_NAME = "Internet"
PEER_GROUP_EVERYONE_NAME = "EveryOne"

MAX_LAST_HANDSHAKE_SECONDS = 120


logger = logging.getLogger(APP_NAME)


def logged(func):
    @wraps(func)
    def logger_func(*args, **kwargs):
        func_name = func.__name__
        try:
            logger.debug(f"{func_name}: start")
            res = func(*args, **kwargs)
            return res
        finally:
            logger.debug(f"{func_name}: end")

    return logger_func
