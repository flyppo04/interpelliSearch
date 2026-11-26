# Interpelli Watch

Controlla i siti degli USP e delle scuole e raccoglie gli **interpelli per supplenze** pertinenti
(per ora classe A041) in una pagina web consultabile.

## Avvio (Windows)

Serve Python 3.12 o superiore.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m watcher
```

Poi apri `site/index.html` con doppio clic.

## Comandi

| Comando | Cosa fa |
|---|---|
| `python -m watcher` | Controlla tutte le fonti e aggiorna `site/interpelli.json` e la pagina |
| `python -m watcher --fonte "USP Lucca"` | Mostra cosa legge una fonte e cosa tiene il filtro, senza salvare |
| `python -m unittest` | Lancia i test sulle pagine salvate in `tests/fixtures` |

## Configurazione

- `config/sources.yaml`: elenco delle fonti. Due tipi:
  - `rss`: siti WordPress (USP e scuole con tema "Design Scuole"). Indirizzo + `/feed/`.
  - `html`: qualsiasi pagina; vengono letti tutti i link e i filtri tengono quelli giusti.
- `config/filters.yaml`: parole chiave da cercare e da escludere.

### Pagine con JavaScript (facoltativo)

Se una pagina mostra gli avvisi solo dopo averli caricati con JavaScript, `python -m watcher --fonte "Nome"`
legge pochi link o nessuno. In quel caso aggiungi `render: true` alla fonte e installa Playwright (una volta):

```powershell
pip install -r requirements-browser.txt
python -m playwright install chromium
```

La pagina verrà aperta da un Chromium invisibile. Le altre fonti continuano a usare il download normale.

Le richieste usano uno User-Agent generico da browser, al massimo 1 al secondo per sito,
e rispettano `robots.txt`.

## Online con GitHub (Actions + Pages)

Il workflow `.github/workflows/check.yml` controlla le fonti alle 7:40, 12:40, 17:40 e 21:40 (ora italiana),
salva `site/interpelli.json` nella repo e pubblica la cartella `site/` su GitHub Pages.

Una sola impostazione da fare nella repo: *Settings → Pages → Build and deployment → Source: **GitHub Actions***.
Per provarlo subito: scheda *Actions* → "Controllo interpelli" → *Run workflow*.

## Struttura

```
config/       fonti e filtri
watcher/      fetch.py (download) · browser.py (pagine JavaScript) · sources.py (rss/html) · filters.py · main.py
site/         index.html + interpelli.json/.js generati
tests/        test e pagine di esempio
```

## Note

Progetto personale e indipendente, non affiliato al MIM. Fa fede solo l'avviso ufficiale.

Si salvano e si pubblicano solo classe di concorso, fonte, provincia, date e link all'avviso ufficiale:
il titolo originale (che può contenere nomi) serve solo per il filtro e non viene salvato.

**Segnalazioni e rimozioni:** apri una *Issue* in questo repository.
