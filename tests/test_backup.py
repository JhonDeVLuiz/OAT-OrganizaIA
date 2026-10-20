"""Backup .zip (exportar/importar/reindex; .env nunca entra)."""
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import backup, repositorio


def _base_com_banco(tmp_path):
    base = tmp_path / "proj"
    (base / "dados").mkdir(parents=True)
    banco = base / "dados" / "organizaia.db"
    repositorio.iniciar_banco(banco)
    repositorio.salvar_arquivo(banco, "h1", str(base / "e" / "a.txt"),
                               str(base / "o" / "a.txt"), "Textos", "regras")
    (base / ".env").write_text("GLM_API_KEY=falsa", encoding="utf-8")
    return base, banco


def test_exportar_sem_env(tmp_path):
    base, _banco = _base_com_banco(tmp_path)
    destino = tmp_path / "b.zip"
    resultado = backup.exportar_backup(destino, base=base)
    nomes = zipfile.ZipFile(destino).namelist()
    assert "dados/organizaia.db" in nomes and "manifest.json" in nomes
    assert not any(".env" in n for n in nomes)
    assert resultado["arquivos"] == ["dados/organizaia.db", "manifest.json"]


def test_zip_slip_rejeitado(tmp_path):
    mal = tmp_path / "mal.zip"
    with zipfile.ZipFile(mal, "w") as zf:
        zf.writestr("../../evil.txt", "x")
    with pytest.raises(ValueError):
        backup.importar_backup(mal, base=tmp_path / "nova")


def test_env_no_zip_ignorado(tmp_path):
    mal = tmp_path / "mal.zip"
    with zipfile.ZipFile(mal, "w") as zf:
        zf.writestr(".env", "K=v")
        zf.writestr("manifest.json", json.dumps({"base": "x"}))
    base = tmp_path / "nova"
    resultado = backup.importar_backup(mal, base=base)
    assert not (base / ".env").exists()
    assert resultado["arquivos"] == ["manifest.json"]


def test_reindex_troca_base(tmp_path):
    base, _banco = _base_com_banco(tmp_path)
    destino = tmp_path / "b.zip"
    backup.exportar_backup(destino, base=base)
    nova = tmp_path / "restaurado"
    resultado = backup.importar_backup(destino, base=nova, reindexar=True)
    assert resultado["reindexado"] is True
    linhas = repositorio.buscar_por_categoria(nova / "dados" / "organizaia.db", "Textos")
    assert linhas and all(str(nova) in l["origem"] and str(base) not in l["origem"]
                           for l in linhas)


def test_roundtrip_preserva_dados(tmp_path):
    base, _banco = _base_com_banco(tmp_path)
    destino = tmp_path / "b.zip"
    backup.exportar_backup(destino, base=base)
    nova = tmp_path / "restaurado"
    backup.importar_backup(destino, base=nova)
    achado = repositorio.buscar_por_hash(nova / "dados" / "organizaia.db", "h1")
    assert achado["categoria"] == "Textos" and achado["origem_decisao"] == "regras"
