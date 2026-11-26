"""Un'esecuzione: legge le fonti, tiene gli avvisi pertinenti e aggiorna site/interpelli.json."""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

from . import filters, sources

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "site" / "interpelli.json"
KEEP_DAYS = 60       # gli avvisi più vecchi spariscono dalla pagina
BROKEN_AFTER = 3     # errori di fila prima di segnare una fonte come rotta


def _yaml(name):
    return yaml.safe_load((ROOT / "config" / name).read_text(encoding="utf-8")) or []


def _load_previous():
    if OUTPUT.exists():
        return json.loads(OUTPUT.read_text(encoding="utf-8"))
    return {"avvisi": [], "fonti": []}


def _save(data):
    text = json.dumps(data, ensure_ascii=False, indent=1)
    OUTPUT.write_text(text + "\n", encoding="utf-8")
    # stessa cosa in .js: così index.html si apre anche con doppio clic, senza server
    OUTPUT.with_suffix(".js").write_text(f"window.INTERPELLI = {text};\n", encoding="utf-8")


def _check(src, prev, now):
    """Legge una fonte e restituisce (avvisi_trovati, stato_della_fonte)."""
    status = {"nome": src["name"], "url": src["url"], "ultimo_controllo": now, "errore": None}
    try:
        items = sources.read(src)
    except Exception as e:  # una fonte rotta non deve fermare le altre
        status |= {"errori_di_fila": prev.get("errori_di_fila", 0) + 1,
                   "trovati": prev.get("trovati", 0),
                   "errore": f"{type(e).__name__}: {e}"}
        status["rotta"] = status["errori_di_fila"] >= BROKEN_AFTER
        return [], status
    status |= {"errori_di_fila": 0, "trovati": len(items), "rotta": False}
    if not items and prev.get("trovati"):
        status |= {"rotta": True, "errore": "0 avvisi letti, prima ce n'erano"}
    return items, status


def run():
    rules = _yaml("filters.yaml")
    previous = _load_previous()
    known = {a["url"]: a for a in previous["avvisi"]}
    prev_status = {f["nome"]: f for f in previous["fonti"]}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    new, statuses = [], []
    for src in _yaml("sources.yaml"):
        items, status = _check(src, prev_status.get(src["name"], {}), now)
        statuses.append(status)
        for it in items:
            if it["url"] in known:
                continue
            labels = filters.classes(f"{it['titolo']} {it['testo']}", rules)
            if not labels:
                continue
            # il titolo originale può contenere nomi (es. il docente da sostituire): non si salva.
            # Sul sito resta solo un titolo neutro + il link all'avviso ufficiale.
            avviso = {"titolo": "Interpello " + ", ".join(labels), "url": it["url"],
                      "data": it["data"], "scadenza": it.get("scadenza"),
                      "fonte": src["name"], "provincia": src.get("province"), "visto_il": now}
            known[it["url"]] = avviso
            new.append(avviso)

    cutoff = (date.today() - timedelta(days=KEEP_DAYS)).isoformat()
    avvisi = [a for a in known.values() if (a["data"] or a["visto_il"][:10]) >= cutoff]
    avvisi.sort(key=lambda a: a["data"] or a["visto_il"][:10], reverse=True)
    _save({"aggiornato": now, "avvisi": avvisi, "fonti": statuses})

    for s in statuses:
        mark = "ROTTA" if s["rotta"] else ("errore" if s["errore"] else "ok")
        print(f"[{mark:6}] {s['nome']}: {s['trovati']} elementi" + (f" - {s['errore']}" if s["errore"] else ""))
    print(f"\n{len(new)} avvisi nuovi, {len(avvisi)} in pagina.")
    for a in new:
        print(f"  + {a['titolo']} ({a['fonte']})\n    {a['url']}")


def debug(name):
    """Mostra cosa legge una fonte e cosa passa i filtri, senza salvare nulla."""
    src = next((s for s in _yaml("sources.yaml") if s["name"] == name), None)
    if src is None:
        raise SystemExit(f"Fonte '{name}' non trovata in config/sources.yaml")
    rules = _yaml("filters.yaml")
    items = sources.read(src)
    for it in items:
        labels = filters.classes(f"{it['titolo']} {it['testo']}", rules)
        print(f"{', '.join(labels) or 'scarta':12} {it['data'] or '':10} {it['titolo'][:100]}")
    print(f"\n{len(items)} elementi letti da {src['url']}")
