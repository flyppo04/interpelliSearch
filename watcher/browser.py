"""Pagine che si caricano con JavaScript: le apre un Chromium invisibile (Playwright).

Usato solo per le fonti con `render: true` in config/sources.yaml. Installazione (una volta):
    pip install -r requirements-browser.txt
    python -m playwright install chromium
"""
from . import fetch


def get(url):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError("fonte con render: true ma Playwright non è installato (vedi README)") from None
    if not fetch.allowed(url):
        raise PermissionError(f"robots.txt non consente {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(user_agent=fetch.USER_AGENT)
            page.goto(url, wait_until="networkidle", timeout=fetch.TIMEOUT * 1000)
            return page.content().encode("utf-8")
        finally:
            browser.close()
