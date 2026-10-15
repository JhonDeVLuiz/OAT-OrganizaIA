"""Fase 2: duplicatas (hash estavel, organizados/ + log)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import duplicatas


def test_sha_estavel_e_em_blocos(tmp_path):
    a = tmp_path / "a.bin"
    b = tmp_path / "b.bin"
    a.write_bytes(b"abc" * 1000)
    b.write_bytes(b"abc" * 1000)
    assert duplicatas.sha256_arquivo(a) == duplicatas.sha256_arquivo(b)
    b.write_bytes(b"abd" * 1000)
    assert duplicatas.sha256_arquivo(a) != duplicatas.sha256_arquivo(b)


def test_indice_une_organizados_e_log(tmp_path):
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    (organizados / "Textos").mkdir(parents=True)
    logs.mkdir()
    (organizados / "Textos" / "a.txt").write_text("conteudo", encoding="utf-8")
    (logs / "exec_id1.json").write_text(
        json.dumps({"id": "id1", "movimentos": [{"hash": "abc123"}]}),
        encoding="utf-8",
    )
    (logs / "exec_id1.undone.json").write_text(
        json.dumps({"id": "id1", "movimentos": [{"hash": "zzz"}]}),
        encoding="utf-8",
    )
    (logs / "lixo.json").write_text("nao eh json", encoding="utf-8")
    indice = duplicatas.indice_hashes(organizados, logs)
    alvo = duplicatas.sha256_arquivo(organizados / "Textos" / "a.txt")
    assert alvo in indice and "abc123" in indice and "zzz" not in indice
