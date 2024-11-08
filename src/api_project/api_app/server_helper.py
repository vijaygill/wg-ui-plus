import datetime
import os
import requests

from django.core.cache import cache

from .models import ServerConfiguration

from .common import CACHE_KEY_APP_LIVE_VERSION, APP_URL


def get_application_details():
    res = {}
    latest_live_version = "unknown"
    res["current_version"] = "v0.0.0"
    res["current_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allow_check_updates = False
    try:
        res["current_version"] = os.environ.get("APP_VERSION", "v0.0.0")
    except Exception:
        res["current_version"] = "**Error**"
        pass
    try:
        sc = ServerConfiguration.objects.all()[0]
        allow_check_updates = sc.allow_check_updates
        latest_live_version = (
            "v0.0.0" if allow_check_updates else "Updates check diabled."
        )

        latest_live_version_temp = cache.get(CACHE_KEY_APP_LIVE_VERSION)
        if latest_live_version_temp:
            latest_live_version = latest_live_version_temp
        else:
            if allow_check_updates:
                response = requests.get(APP_URL)
                latest_live_version = response.url.split("/").pop()
                cache.add(CACHE_KEY_APP_LIVE_VERSION, latest_live_version, 60 * 60)
    except Exception:
        latest_live_version = "**Error**"
        pass

    res["latest_live_version"] = latest_live_version
    res["allow_allow_check_updates"] = allow_check_updates
    return res
