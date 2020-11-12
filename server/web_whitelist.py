from ipaddress import (
    IPv4Network,
    IPv6Network,
    ip_network,
    IPv4Address,
    IPv6Address,
    ip_address,
)
from typing import List, Union

from flask import request, abort

# list of Cloudflare IPs: https://www.cloudflare.com/ips/
from .app import app

cloudflare_ip_list = [
    # V4 address blocks
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/12",
    "172.64.0.0/13",
    "131.0.72.0/22",
    # V6 address blocks
    "2400:cb00::/32",
    "2606:4700::/32",
    "2803:f800::/32",
    "2405:b500::/32",
    "2405:8100::/32",
    "2a06:98c0::/29",
    "2c0f:f248::/32",
]

_whitelist: List[Union[IPv4Network, IPv6Network]] = [ip_network(x) for x in cloudflare_ip_list]


def addr_is_whitelisted(remote_addr: Union[IPv4Address, IPv6Address]) -> bool:
    for net in _whitelist:
        if remote_addr in net:
            return True
    return False


# https://stackoverflow.com/questions/24222220/block-an-ip-address-from-accessing-my-flask-app-on-heroku
@app.before_request
def block_method():
    ip = request.environ.get("REMOTE_ADDR")
    if not addr_is_whitelisted(ip_address(ip)):
        abort(403)  # "Forbidden"
