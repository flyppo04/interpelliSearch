"""Download: 1 richiesta al secondo per host, timeout 20 s, rispetto di robots.txt."""
import ssl
import time
import urllib.request
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import certifi

# User-Agent generico da browser: nessun nome di progetto, nessun contatto
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
TIMEOUT = 20
# certificati radice di Mozilla: uguali su ogni PC (a Windows ne mancano alcuni, es. Actalis)
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

_last_request = {}  # host -> istante dell'ultima richiesta
_robots = {}        # https://host -> righe del robots.txt


def _download(url):
    host = urlsplit(url).netloc
    wait = 1 - (time.monotonic() - _last_request.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=SSL_CONTEXT) as r:
            return r.read()
    finally:
        _last_request[host] = time.monotonic()


def _groups_for_everyone(lines):
    """Ogni blocco 'User-agent: *' del file, separato. Python leggerebbe solo il primo."""
    groups, current, reading_agents = [], [], False
    for raw in lines:
        line = raw.split("#")[0].strip()
        if not line:
            continue
        is_agent = line.lower().startswith("user-agent:")
        if is_agent and not reading_agents:
            current = []
            groups.append(current)
        reading_agents = is_agent
        current.append(line)
    return [g for g in groups if any(l.lower().replace(" ", "") == "user-agent:*" for l in g)]


def robots_allow(lines, url):
    """Severo: se anche un solo blocco per tutti i programmi vieta l'indirizzo, è vietato."""
    for group in _groups_for_everyone(lines):
        rp = RobotFileParser()
        rp.parse(group)
        if not rp.can_fetch("*", url):
            return False
    return True


def allowed(url):
    p = urlsplit(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        try:
            _robots[base] = _download(base + "/robots.txt").decode("utf-8", "replace").splitlines()
        except OSError:
            _robots[base] = []  # robots.txt assente o irraggiungibile: tutto consentito
    return robots_allow(_robots[base], url)


def get(url):
    if not allowed(url):
        raise PermissionError(f"robots.txt non consente {url}")
    return _download(url)
