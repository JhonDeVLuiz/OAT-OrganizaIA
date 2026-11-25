"""Fase 2: SHA-256 em blocos; compara com organizados/ e com o log."""
import hashlib
import json
from pathlib import Path

CHUNK_BYTES = 64 * 1024


def sha256_arquivo(caminho):
    digest = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for bloco in iter(lambda: fh.read(CHUNK_BYTES), b""):
            digest.update(bloco)
    return digest.hexdigest()


def hashes_dos_logs(logs_dir):
    """Hashes ja movimentados (logs ativos; ignora *.undone.json e corrompidos)."""
    hashes = set()
    pasta = Path(logs_dir)
    if not pasta.is_dir():
        return hashes
    for log in pasta.glob("exec_*.json"):
        if log.name.endswith(".undone.json"):
            continue
        try:
            dados = json.loads(log.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for mov in dados.get("movimentos", []):
            if mov.get("hash"):
                hashes.add(mov["hash"])
    return hashes


def hashes_organizados(organizados_dir):
    """Hashes dos arquivos que ja estao em organizados/."""
    hashes = set()
    pasta = Path(organizados_dir)
    if not pasta.is_dir():
        return hashes
    for item in pasta.rglob("*"):
        if not item.is_file() or item.is_symlink():
            continue
        try:
            hashes.add(sha256_arquivo(item))
        except OSError:
            continue
    return hashes


def indice_hashes(organizados_dir, logs_dir):
    return hashes_organizados(organizados_dir) | hashes_dos_logs(logs_dir)
