import requests
import json
import logging

logger = logging.getLogger("automation")

INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow"
]

def send_indexnow(domain: str, urls: list, key: str, key_location: str):

    payload = {
        "host": domain,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls
    }

    logger.warning("IndexNow key used: %s", key)
    logger.warning("IndexNow payload: %s", json.dumps(payload, indent=2))

    for endpoint in INDEXNOW_ENDPOINTS:
        try:
            res = requests.post(endpoint, json=payload, timeout=10)

            logger.warning(
                "IndexNow response from %s -> %s",
                endpoint,
                res.status_code
            )

        except Exception as e:
            logger.error("IndexNow failed for %s -> %s", endpoint, str(e))

import secrets


def generate_indexnow_key():
    return secrets.token_hex(16)