import datetime
import os
import requests

from django.core.cache import cache

from api_app.wireguardhelper import WireGuardHelper

from .models import Peer, PeerGroup, ServerConfiguration, Target

from .common import CACHE_KEY_APP_LIVE_VERSION, CACHE_TTL, APP_URL, IS_EMAIL_ENABLED


def get_server_status():
    peers = Peer.objects.all()
    peer_groups = PeerGroup.objects.all()
    targets = Target.objects.all()
    server_configurations = ServerConfiguration.objects.all()
    last_db_change_datetimes = (
        [x.last_changed_datetime for x in peers]
        + [x.last_changed_datetime for x in peer_groups]
        + [x.last_changed_datetime for x in targets]
        + [x.last_changed_datetime for x in server_configurations]
    )
    last_db_change_datetime = (
        max(last_db_change_datetimes) if last_db_change_datetimes else None
    )

    wg = WireGuardHelper()
    res = wg.get_server_status(
        last_db_change_datetime=last_db_change_datetime
    )
    return res


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
                cache.add(CACHE_KEY_APP_LIVE_VERSION, latest_live_version, CACHE_TTL)
    except Exception:
        latest_live_version = "**Error**"
        pass

    res["latest_live_version"] = latest_live_version
    res["allow_allow_check_updates"] = allow_check_updates
    res["is_email_enabled"] = IS_EMAIL_ENABLED
    return res


def generate_configuration_files():
    dt = datetime.datetime.now(datetime.timezone.utc)
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    peer_groups = PeerGroup.objects.all()
    peers = Peer.objects.all()
    targets = Target.objects.all()
    res = wg.generate_configuration_files(
        serverConfiguration=sc, targets=targets, peer_groups=peer_groups, peers=peers
    )
    sc.wireguard_config_change_datetime = dt
    sc.save()
    return res
