"""
Dynamic content fetcher using a persistent Playwright browser.
- Single browser instance reused across all fetches (massive speed gain).
- Realistic user-agent + viewport to avoid bot detection.
- networkidle wait strategy + lazy-load scroll for JS-heavy pages.
- Thread-safe initialization via lock.
- Falls back gracefully to None if Playwright is not installed.
"""
from __future__ import annotations

import atexit
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

_BROWSER_AVAILABLE: Optional[bool] = None  # None = untested, False = unavailable
_playwright_instance = None
_browser = None
_context = None
_browser_lock = threading.Lock()

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _init_browser() -> bool:
    
    global _playwright_instance, _browser, _context, _BROWSER_AVAILABLE

    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        logger.warning("[BrowserFetch] Playwright not installed — dynamic fetch disabled.")
        _BROWSER_AVAILABLE = False
        return False

    try:
        _playwright_instance = sync_playwright().start()
        _browser = _playwright_instance.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        _context = _browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            ignore_https_errors=True,   # handle self-signed / misconfigured SSL certs
        )
        _BROWSER_AVAILABLE = True
        logger.info("[BrowserFetch] Playwright browser initialized.")
        return True
    except Exception as exc:
        logger.error("[BrowserFetch] Browser init failed: %s", exc)
        _BROWSER_AVAILABLE = False
        return False


def _get_context():
    """Return the shared browser context, initializing it if needed."""
    global _BROWSER_AVAILABLE

    if _BROWSER_AVAILABLE is False:
        return None

    with _browser_lock:
        # Already up
        if _context is not None and _BROWSER_AVAILABLE is True:
            return _context
        # First call or after a crash — try to init
        success = _init_browser()
        return _context if success else None


def _shutdown_browser() -> None:
    """Cleanly close browser on process exit."""
    global _browser, _playwright_instance, _context
    try:
        if _context:
            _context.close()
        if _browser:
            _browser.close()
        if _playwright_instance:
            _playwright_instance.stop()
    except Exception:
        pass


atexit.register(_shutdown_browser)


def fetch_with_browser(
    url: str,
    wait_until: str = "networkidle",
    timeout_ms: int = 20_000,
    scroll: bool = True,
    scroll_pause_ms: int = 800,
) -> Optional[str]:
   
    ctx = _get_context()
    if ctx is None:
        return None

    page = None
    try:
        page = ctx.new_page()

        page.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,mp4,webm}",
            lambda route: route.abort(),
        )


        try:
            page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        except Exception as nav_exc:
            if "timeout" in str(nav_exc).lower() and wait_until == "networkidle":
                logger.warning(
                    "[BrowserFetch] networkidle timeout for %s — retrying with domcontentloaded",
                    url,
                )
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            else:
                raise

        if scroll:

            try:
                page.evaluate(
                    """async () => {
                        await new Promise(resolve => {
                            let totalHeight = 0;
                            const distance = 400;
                            const timer = setInterval(() => {
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                if (totalHeight >= document.body.scrollHeight) {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 100);
                        });
                    }"""
                )
                time.sleep(scroll_pause_ms / 1000)
            except Exception as scroll_exc:
                logger.debug("[BrowserFetch] Scroll failed for %s: %s", url, scroll_exc)
                # Non-fatal — continue with whatever content loaded

        html = page.content()

        # 528-byte pages are JS shells — the framework hasn't mounted yet.
        # Wait for any <a> tag or a body with real text content, then re-capture.
        if len(html) < 5_000:
            logger.warning(
                "[BrowserFetch] Suspiciously small page (%d bytes) for %s "
                "— waiting for JS to mount content...", len(html), url
            )
            try:
                # Wait up to 8s for the first anchor tag to appear in the DOM
                page.wait_for_selector("a[href]", timeout=8_000)
                time.sleep(1.0)  # brief pause for remaining hydration
                html = page.content()
                logger.info(
                    "[BrowserFetch] Re-captured after JS mount: %d bytes", len(html)
                )
            except Exception:
                # Selector never appeared — page may be truly empty or an error page
                logger.warning(
                    "[BrowserFetch] No <a> tags appeared after wait for %s "
                    "(%d bytes captured anyway)", url, len(html)
                )

        logger.info("[BrowserFetch] OK  %s (%d bytes)", url, len(html))
        return html

    except Exception as exc:
        logger.warning("[BrowserFetch] FAIL %s → %s", url, exc)
        return None

    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass


def is_browser_available() -> bool:
    """Return True if the browser has been successfully initialized."""
    return bool(_BROWSER_AVAILABLE)