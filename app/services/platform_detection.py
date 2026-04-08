import re
from typing import Literal
import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, SSLError
from urllib3.exceptions import InsecureRequestWarning
import urllib3

Platform = Literal["squarespace", "shopify", "wordpress", "wix", "unknown"]

# Suppress InsecureRequestWarning when verify=False
urllib3.disable_warnings(InsecureRequestWarning)

def detect_platform(base_url: str) -> Platform:
    """
    Heuristic platform detection based on homepage HTML.
    Handles SSL errors and network issues gracefully.
    """
    try:
        resp = requests.get(base_url, timeout=10)
        html = resp.text.lower()
    except SSLError:
        # Retry with SSL verification disabled
        try:
            resp = requests.get(base_url, timeout=10, verify=False)
            html = resp.text.lower()
        except RequestException:
            return "unknown"
    except RequestException:
        return "unknown"

    if resp.status_code >= 400:
        return "unknown"

    # Quick string checks
    if "squarespace" in html or "static1.squarespace.com" in html:
        return "squarespace"
    if "cdn.shopify.com" in html or "x-shopify-stage" in resp.headers:
        return "shopify"
    if "wp-content/" in html or "wp-includes/" in html or "wordpress" in html:
        return "wordpress"
    if "wixstatic.com" in html or "wix.com" in html:
        return "wix"

    # Meta generator tag
    try:
        soup = BeautifulSoup(html, "html.parser")
        generator = soup.find("meta", attrs={"name": re.compile("generator", re.I)})
        if generator and generator.get("content"):
            g = generator["content"].lower()
            if "wordpress" in g:
                return "wordpress"
            if "shopify" in g:
                return "shopify"
            if "squarespace" in g:
                return "squarespace"
            if "wix" in g:
                return "wix"
    except Exception:
        pass

    return "unknown"