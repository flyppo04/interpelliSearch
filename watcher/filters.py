"""Filtro a parole chiave (config/filters.yaml). Maiuscole e trattini non contano: "A-041" = "a041"."""


def _norm(text):
    return " ".join(text.lower().replace("-", "").split())


def classes(text, rules):
    """Etichette delle classi di concorso trovate nel testo. Lista vuota = avviso da scartare."""
    t = _norm(text)

    def has(words):
        return any(_norm(w) in t for w in words or [])

    if rules.get("must_any") and not has(rules["must_any"]):
        return []
    if has(rules.get("exclude_any")):
        return []
    if not rules.get("classes") and not rules.get("other"):
        return ["generico"]  # nessuna classe configurata: tutti gli interpelli
    found = [label for label, words in (rules.get("classes") or {}).items() if has(words)]
    if not found and has(rules.get("other")):
        found = ["informatica, classe da verificare"]
    return found
