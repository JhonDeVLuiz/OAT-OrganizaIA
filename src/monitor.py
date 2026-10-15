"""Fase 2: watchdog em entrada/ (recursive=False). Sem IA, sem banco."""
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import config, organizador

SUFFIXOS_IGNORADOS = (".tmp", ".crdownload", ".part")


def deve_ignorar(nome):
    return Path(nome).suffix.lower() in SUFFIXOS_IGNORADOS


def arquivo_estavel(caminho, intervalo=0.5, tentativas=30):
    """Espera o arquivo parar de crescer. False se sumir ou estourar tentativas."""
    anterior = -1
    for _ in range(tentativas):
        try:
            atual = Path(caminho).stat().st_size
        except OSError:
            return False
        if atual == anterior:
            return True
        anterior = atual
        time.sleep(intervalo)
    return False


class _Handler(FileSystemEventHandler):
    def __init__(self, entrada, organizados, logs, dry_run):
        self.entrada = entrada
        self.organizados = organizados
        self.logs = logs
        self.dry_run = dry_run

    def _cuidar(self, caminho):
        if deve_ignorar(caminho):
            return
        if not arquivo_estavel(caminho):
            return
        organizador.processar_um(caminho, entrada=self.entrada,
                                 organizados=self.organizados, logs=self.logs,
                                 dry_run=self.dry_run)

    def on_created(self, event):
        if not event.is_directory:
            self._cuidar(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._cuidar(event.dest_path)


def iniciar(entrada=None, organizados=None, logs=None, dry_run=False):
    entrada = Path(entrada or config.ENTRADA_DIR)
    observador = Observer()
    observador.schedule(_Handler(entrada,
                                 Path(organizados or config.ORGANIZADOS_DIR),
                                 Path(logs or config.LOGS_DIR), dry_run),
                        str(entrada), recursive=False)
    observador.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observador.stop()
    observador.join()
