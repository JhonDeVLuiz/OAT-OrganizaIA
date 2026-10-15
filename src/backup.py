"""Backup .zip: banco + manifest. Nunca inclui .env; barra zip-slip e reindexa."""
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from . import config, repositorio, seguranca

VERSAO_BACKUP = 1
PERMITIDOS = ("dados/", "manifest.json")


def _agora():
    return datetime.now(timezone.utc).isoformat()


def _manifest(base):
    return {
        "versao": VERSAO_BACKUP,
        "exportado_em": _agora(),
        "categorias": list(config.CATEGORIAS),
        "base": str(Path(base).resolve()),
    }


def exportar_backup(destino_zip, base=None):
    """Gera .zip com dados/organizaia.db + manifest.json (caminhos relativos)."""
    base = Path(base or config.BASE_DIR)
    destino_zip = Path(destino_zip)
    banco = base / "dados" / config.DB_PATH.name
    incluidos = []
    with zipfile.ZipFile(destino_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        if banco.is_file():
            zf.write(banco, "dados/" + config.DB_PATH.name)
            incluidos.append("dados/" + config.DB_PATH.name)
        zf.writestr("manifest.json", json.dumps(_manifest(base), ensure_ascii=False, indent=2))
        incluidos.append("manifest.json")
    return {"zip": str(destino_zip), "arquivos": incluidos}


def _entrada_segura(nome):
    """Rejeita absoluto, .. e .env; aceita so dados/ e manifest.json."""
    partes = Path(nome).parts
    if Path(nome).is_absolute() or ".." in partes:
        raise ValueError(f"entrada insegura no zip: {nome}")
    if ".env" in partes:
        return False
    return nome == "manifest.json" or (partes and partes[0] == "dados")


def importar_backup(zip_path, base=None, reindexar=False):
    """Restaura backup; com reindexar=True reescreve origem/destino para a base nova."""
    base = Path(base or config.BASE_DIR)
    base_antiga, restaurados = None, []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            if not _entrada_segura(info.filename):
                continue
            destino = seguranca.confinar_em(base / info.filename, (base,))
            destino.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as origem, open(destino, "wb") as fh:
                fh.write(origem.read())
            restaurados.append(info.filename)
        try:
            base_antiga = json.loads(zf.read("manifest.json")).get("base")
        except KeyError:
            base_antiga = None
    if reindexar and base_antiga and Path(base_antiga).resolve() != base.resolve():
        reindexar_caminhos(base / "dados" / config.DB_PATH.name, base_antiga, str(base.resolve()))
    return {"base": str(base.resolve()), "arquivos": restaurados, "reindexado": bool(reindexar)}


def reindexar_caminhos(banco, base_antiga, base_nova):
    """Troca o prefixo base_antiga por base_nova em origem/destino (parametrizado)."""
    import sqlite3

    banco = Path(banco)
    if not banco.is_file():
        return 0
    con = sqlite3.connect(str(banco))
    try:
        linhas = con.execute("SELECT id, origem, destino FROM arquivos;").fetchall()
        trocados = 0
        for id_, origem, destino in linhas:
            nova_origem = _trocar_prefixo(origem, base_antiga, base_nova)
            novo_destino = _trocar_prefixo(destino, base_antiga, base_nova)
            if (nova_origem, novo_destino) != (origem, destino):
                con.execute("UPDATE arquivos SET origem = ?, destino = ? WHERE id = ?;",
                            (nova_origem, novo_destino, id_))
                trocados += 1
        con.commit()
        return trocados
    finally:
        con.close()


def _trocar_prefixo(caminho, antiga, nova):
    if caminho == antiga:
        return nova
    if caminho.startswith(antiga.rstrip("/\\") + "/") or caminho.startswith(antiga.rstrip("/\\") + "\\"):
        return nova + caminho[len(antiga):]
    return caminho
