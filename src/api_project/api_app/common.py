import os
from functools import wraps
import logging

APP_NAME = "wg-ui-plus"
APP_OWNER = "vijaygill"
APP_REPO = "wg-ui-plus"
APP_URL = f"https://github.com/{APP_OWNER}/{APP_REPO}/releases/latest"

IP_ADDRESS_INTERNET = "0.0.0.0/0"
TARGET_INTERNET_NAME = "Internet"
PEER_GROUP_EVERYONE_NAME = "EveryOne"

MAX_LAST_HANDSHAKE_SECONDS = 120

CACHE_KEY_APP_LIVE_VERSION = "CACHE_KEY_APP_LIVE_VERSION"

WIREGUARD_CONFIG_PATH = "/config/wireguard/wg0.conf"
SCRIPT_PATH_POST_UP = "/config/wireguard/scripts/post-up.sh"
SCRIPT_PATH_POST_DOWN = "/config/wireguard/scripts/post-down.sh"


IS_EMAIL_ENABLED = True if os.environ.get("EMAIL_HOST", None) else False

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
