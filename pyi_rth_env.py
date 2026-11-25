# Hook de execucao do PyInstaller (onefile): extrai o .env embutido
# para junto do .exe na primeira vez, pois o config.py procura por ele lá.
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    try:
        destino = Path(sys.executable).resolve().parent / ".env"
        if not destino.exists():
            origem = Path(getattr(sys, "_MEIPASS", ".")) / ".env"
            if origem.exists():
                destino.write_bytes(origem.read_bytes())
    except OSError:
        pass  # sem permissao de escrita: o app segue com os valores padrao
