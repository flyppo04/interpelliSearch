"""Lettura delle fonti. Ogni parser restituisce dict {titolo, url, data, testo}.

- rss:  feed RSS (tutti i siti WordPress, quindi USP e scuole con tema "Design Scuole": indirizzo + /feed/)
- html: qualsiasi pagina; prende tutti i link e lascia ai filtri il compito di scegliere
"""
import html
import re
import urllib.error
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

from . import browser, fetch


def _clean(text):
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return " ".join(text.split())


def parse_rss(body, base_url):
    for item in ET.fromstring(body).iter("item"):
        pub = item.findtext("pubDate")
        link, guid = (item.findtext("link") or "").strip(), (item.findtext("guid") or "").strip()
        if "/index.php/" in link:  # Joomla: ".../3127-titolo-articolo" -> ".../3127", stessa pagina
            link = re.sub(r"/(\d+)-[^/?#]+$", r"/\1", link)
        yield {
            "titolo": _clean(item.findtext("title")),
            # WordPress: il guid "sito/?p=123" porta alla stessa pagina senza il titolo (e i nomi) nell'indirizzo
            "url": guid if re.search(r"[?&]p=\d+$", guid) else link,
            "data": parsedate_to_datetime(pub).date().isoformat() if pub else None,
            "testo": _clean(item.findtext("description")),  # usato solo per i filtri, non salvato
        }


class _LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href, self._text = dict(attrs).get("href"), []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


def parse_html(body, base_url):
    collector = _LinkCollector()
    collector.feed(body.decode("utf-8", "replace"))
    seen = set()
    for href, text in collector.links:
        url = urljoin(base_url, href)
        if text and url.startswith("http") and url not in seen:
            seen.add(url)
            yield {"titolo": text, "url": url, "data": None, "testo": ""}


PARSERS = {"rss": parse_rss, "html": parse_html}


def read(source):
    parser = PARSERS[source["type"]]
    download = browser.get if source.get("render") else fetch.get  # render: true -> pagina con JavaScript
    items = []
    for n in range(1, source.get("pages", 1) + 1):
        # pages: N -> legge anche le pagine precedenti del feed WordPress (?paged=2, 3...)
        url = source["url"] if n == 1 else source["url"] + ("&" if "?" in source["url"] else "?") + f"paged={n}"
        try:
            items += parser(download(url), source["url"])
        except urllib.error.HTTPError as e:
            if n > 1 and e.code == 404:  # il feed ha meno pagine di quelle richieste
                break
            raise
    return items
