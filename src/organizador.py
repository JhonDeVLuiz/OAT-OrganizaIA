"""Fase 2: entrada/ -> organizados/. Dry-run, log com id, sufixo, desfazer."""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from . import config, duplicatas, regras, seguranca

SUFFIXOS_TEMPORARIOS = (".tmp", ".crdownload", ".part")


def _id_execucao():
    agora = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{agora}_{uuid4().hex[:8]}"


def _padrao(pasta, nome):
    destino = Path(pasta) / nome
    if not destino.exists():
        return destino
    haste, ext = Path(nome).stem, Path(nome).suffix
    i = 1
    while True:
        candidato = Path(pasta) / f"{haste} ({i}){ext}"
        if not candidato.exists():
            return candidato
        i += 1


def _ignorado(origem, motivo):
    return {"status": "ignorado", "origem": str(origem), "motivo": motivo}


def _processar_um(caminho, entrada, organizados, indice, max_bytes):
    origem = Path(caminho)
    if origem.suffix.lower() in SUFFIXOS_TEMPORARIOS:
        return _ignorado(origem, "temporario")
    if not origem.is_file():
        return _ignorado(origem, "ausente")
    try:
        seguranca.resolver_confinado(origem, entrada)
    except ValueError:
        return _ignorado(origem, "fora-da-raiz")
    if seguranca.excluido(origem.name):
        return _ignorado(origem, "excluido")
    try:
        nome = seguranca.nome_seguro(origem.name)
    except ValueError:
        return _ignorado(origem, "nome-invalido")
    if origem.is_symlink():
        return _ignorado(origem, "link")
    try:
        if origem.stat().st_size > max_bytes:
            return _ignorado(origem, "grande")
    except OSError:
        return _ignorado(origem, "ausente")

    resumo = duplicatas.sha256_arquivo(origem)
    if resumo in indice:
        destino = _padrao(Path(organizados) / "Duplicados", nome)
        status, categoria = "duplicado", regras.decidir(nome)
    else:
        categoria = regras.decidir(nome)
        pasta = (Path(organizados) / "Revisar") if categoria is None else (Path(organizados) / categoria)
        destino = _padrao(pasta, nome)
        status = "revisar" if categoria is None else "movido"
    indice.add(resumo)
    return {
        "status": status,
        "origem": str(origem),
        "destino": str(destino),
        "hash": resumo,
        "categoria": categoria,
    }


def processar(entrada=None, organizados=None, logs=None, dry_run=False, max_bytes=None):
    entrada = Path(entrada or config.ENTRADA_DIR)
    organizados = Path(organizados or config.ORGANIZADOS_DIR)
    logs = Path(logs or config.LOGS_DIR)
    max_bytes = config.MAX_TAMANHO_BYTES if max_bytes is None else max_bytes
    for pasta in (organizados / "Revisar", organizados / "Duplicados", logs):
        pasta.mkdir(parents=True, exist_ok=True)

    indice = duplicatas.indice_hashes(organizados, logs)
    movidos, ignorados = [], []
    for item in sorted(entrada.iterdir()):
        if not item.is_file():
            continue
        resultado = _processar_um(item, entrada, organizados, indice, max_bytes)
        if resultado["status"] == "ignorado":
            ignorados.append(resultado)
            continue
        if dry_run:
            movidos.append(resultado)
            continue
        Path(resultado["destino"]).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(resultado["origem"], resultado["destino"])
        movidos.append(resultado)

    exec_id = None
    if not dry_run and movidos:
        exec_id = _id_execucao()
        agora = datetime.now(timezone.utc).isoformat()
        for mov in movidos:
            mov["data"] = agora
        (logs / f"exec_{exec_id}.json").write_text(
            json.dumps({"id": exec_id, "data": agora, "movimentos": movidos},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return {"id": exec_id, "movimentos": movidos, "ignorados": ignorados, "dry_run": dry_run}


def processar_um(caminho, entrada=None, organizados=None, logs=None,
                 dry_run=False, max_bytes=None):
    """Uma so arquivo (usado pelo monitor). Gera log proprio se mover."""
    entrada = Path(entrada or config.ENTRADA_DIR)
    organizados = Path(organizados or config.ORGANIZADOS_DIR)
    logs = Path(logs or config.LOGS_DIR)
    max_bytes = config.MAX_TAMANHO_BYTES if max_bytes is None else max_bytes
    for pasta in (organizados / "Revisar", organizados / "Duplicados", logs):
        pasta.mkdir(parents=True, exist_ok=True)

    resultado = _processar_um(caminho, entrada, organizados,
                              duplicatas.indice_hashes(organizados, logs), max_bytes)
    if resultado["status"] == "ignorado" or dry_run:
        return {"id": None, "movimentos": [resultado],
                "ignorados": [], "dry_run": dry_run}
    Path(resultado["destino"]).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(resultado["origem"], resultado["destino"])
    exec_id = _id_execucao()
    agora = datetime.now(timezone.utc).isoformat()
    resultado["data"] = agora
    (logs / f"exec_{exec_id}.json").write_text(
        json.dumps({"id": exec_id, "data": agora, "movimentos": [resultado]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"id": exec_id, "movimentos": [resultado],
            "ignorados": [], "dry_run": dry_run}


def _logs_ativos(logs_dir):
    pasta = Path(logs_dir)
    if not pasta.is_dir():
        return []
    return [log for log in pasta.glob("exec_*.json")
            if not log.name.endswith(".undone.json")]


def desfazer_ultima_execucao(logs_dir=None):
    """Desfaz a ultima execucao inteira (todas as movimentacoes do id)."""
    logs = Path(logs_dir or config.LOGS_DIR)
    ativos = sorted(_logs_ativos(logs), key=lambda p: p.stat().st_mtime)
    if not ativos:
        return {"id": None, "restaurados": []}
    ultimo = ativos[-1]
    dados = json.loads(ultimo.read_text(encoding="utf-8"))
    restaurados = []
    for mov in reversed(dados.get("movimentos", [])):
        destino = Path(mov["destino"])
        if not destino.is_file():
            continue
        origem = Path(mov["origem"])
        origem.parent.mkdir(parents=True, exist_ok=True)
        alvo = origem if not origem.exists() else _padrao(origem.parent, origem.name)
        shutil.move(str(destino), str(alvo))
        restaurados.append({"de": str(destino), "para": str(alvo)})
    ultimo.rename(ultimo.with_name(ultimo.name.replace(".json", ".undone.json")))
    return {"id": dados.get("id"), "restaurados": restaurados}
