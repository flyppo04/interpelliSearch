"""python -m watcher               -> controlla tutte le fonti e aggiorna la pagina
python -m watcher --fonte NOME  -> mostra cosa legge una sola fonte (debug, non salva)"""
import sys

from .main import debug, run

if len(sys.argv) == 3 and sys.argv[1] == "--fonte":
    debug(sys.argv[2])
elif len(sys.argv) == 1:
    run()
else:
    print(__doc__)
