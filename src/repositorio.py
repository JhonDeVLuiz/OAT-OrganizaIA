"""Fase 3: unico ponto de acesso ao SQLite. So metadados, tudo parametrizado."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS arquivos (
    id INTEGER PRIMARY KEY,
    hash TEXT NOT NULL UNIQUE,
    origem TEXT NOT NULL,
    destino TEXT NOT NULL,
    categoria TEXT,
    origem_decisao TEXT NOT NULL,
    criado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS classificacoes (
    id INTEGER PRIMARY KEY,
    arquivo_id INTEGER NOT NULL REFERENCES arquivos(id),
    categoria TEXT NOT NULL,
    confianca REAL NOT NULL,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY,
    acao TEXT NOT NULL,
    caminho TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_arquivos_hash ON arquivos(hash);
CREATE INDEX IF NOT EXISTS idx_arquivos_destino ON arquivos(destino);
CREATE INDEX IF NOT EXISTS idx_arquivos_categoria ON arquivos(categoria);
CREATE INDEX IF NOT EXISTS idx_classificacoes_arquivo ON classificacoes(arquivo_id);
"""

_DECISAO_POR_STATUS = {"movido": "regras", "duplicado": "duplicata", "revisar": "revisao"}


def _agora():
    return datetime.now(timezone.utc).isoformat()


def _conectar(banco):
    caminho = Path(banco or DB_PATH)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(caminho))
    con.row_factory = sqlite3.Row
    return con


def iniciar_banco(banco=None):
    """Cria tabelas e indices; ativa WAL. Idempotente."""
    con = _conectar(banco)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.executescript(_SCHEMA)
        con.commit()
    finally:
        con.close()


def salvar_arquivo(banco, resumo, origem, destino, categoria, origem_decisao, criado_em=None):
    """INSERT OR IGNORE pelo hash UNIQUE; retorna o id (existente ou novo)."""
    criado_em = criado_em or _agora()
    con = _conectar(banco)
    try:
        con.execute(
            "INSERT OR IGNORE INTO arquivos"
            " (hash, origem, destino, categoria, origem_decisao, criado_em)"
            " VALUES (?, ?, ?, ?, ?, ?);",
            (resumo, str(origem), str(destino), categoria, origem_decisao, criado_em),
        )
        con.commit()
        linha = con.execute("SELECT id FROM arquivos WHERE hash = ?;", (resumo,)).fetchone()
        return linha["id"]
    finally:
        con.close()


def salvar_classificacao(banco, arquivo_id, categoria, confianca, data=None):
    data = data or _agora()
    con = _conectar(banco)
    try:
        cur = con.execute(
            "INSERT INTO classificacoes (arquivo_id, categoria, confianca, data)"
            " VALUES (?, ?, ?, ?);",
            (arquivo_id, categoria, confianca, data),
        )
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def registrar_auditoria(banco, acao, caminho, data=None):
    data = data or _agora()
    con = _conectar(banco)
    try:
        cur = con.execute(
            "INSERT INTO auditoria (acao, caminho, data) VALUES (?, ?, ?);",
            (acao, str(caminho), data),
        )
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def salvar_movimentos(banco, movimentos):
    """Lote: arquivos (OR IGNORE) + classificacao (regras, 1.0) + auditoria mover."""
    movimentos = list(movimentos)
    if not movimentos:
        return []
    con = _conectar(banco)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.executemany(
            "INSERT OR IGNORE INTO arquivos"
            " (hash, origem, destino, categoria, origem_decisao, criado_em)"
            " VALUES (?, ?, ?, ?, ?, ?);",
            [(
                mov["hash"],
                str(mov["origem"]),
                str(mov["destino"]),
                mov.get("categoria"),
                mov.get("origem_decisao") or _DECISAO_POR_STATUS.get(mov["status"], "regras"),
                mov.get("data") or _agora(),
            ) for mov in movimentos],
        )
        ids = []
        for mov in movimentos:
            linha = con.execute("SELECT id FROM arquivos WHERE hash = ?;", (mov["hash"],)).fetchone()
            arquivo_id = linha["id"]
            ids.append(arquivo_id)
            decisao = mov.get("origem_decisao") or _DECISAO_POR_STATUS.get(mov["status"], "regras")
            if mov.get("categoria") and decisao in ("regras", "ia", "ia-registrada"):
                ja = con.execute(
                    "SELECT 1 FROM classificacoes WHERE arquivo_id = ?;", (arquivo_id,)
                ).fetchone()
                if not ja:
                    con.execute(
                        "INSERT INTO classificacoes (arquivo_id, categoria, confianca, data)"
                        " VALUES (?, ?, ?, ?);",
                        (arquivo_id, mov["categoria"],
                         mov.get("confianca", 1.0) or 1.0, mov.get("data") or _agora()),
                    )
            con.execute(
                "INSERT INTO auditoria (acao, caminho, data) VALUES (?, ?, ?);",
                ("mover", str(mov["destino"]), mov.get("data") or _agora()),
            )
        con.commit()
        return ids
    finally:
        con.close()


def buscar_por_categoria(banco, categoria):
    con = _conectar(banco)
    try:
        linhas = con.execute(
            "SELECT hash, origem, destino, categoria, origem_decisao, criado_em"
            " FROM arquivos WHERE categoria = ? ORDER BY destino;",
            (categoria,),
        ).fetchall()
        return [dict(linha) for linha in linhas]
    finally:
        con.close()


def buscar_por_nome(banco, termo):
    """Busca destino por trecho do nome (LIKE parametrizado com escape)."""
    limpo = (termo.replace("\\", "\\\\").replace("%", "\\%")
             .replace("_", "\\_"))
    con = _conectar(banco)
    try:
        linhas = con.execute(
            "SELECT hash, origem, destino, categoria, origem_decisao, criado_em"
            " FROM arquivos WHERE destino LIKE ? ESCAPE '\\' ORDER BY destino LIMIT 50;",
            (f"%{limpo}%",),
        ).fetchall()
        return [dict(linha) for linha in linhas]
    finally:
        con.close()


def buscar_por_hash(banco, resumo):
    con = _conectar(banco)
    try:
        linha = con.execute(
            "SELECT hash, origem, destino, categoria, origem_decisao, criado_em"
            " FROM arquivos WHERE hash = ?;",
            (resumo,),
        ).fetchone()
        return dict(linha) if linha else None
    finally:
        con.close()


def historico_do_arquivo(banco, resumo):
    """Arquivo + classificacoes + auditoria dos seus caminhos. None se desconhecido."""
    con = _conectar(banco)
    try:
        arquivo = con.execute(
            "SELECT id, hash, origem, destino, categoria, origem_decisao, criado_em"
            " FROM arquivos WHERE hash = ?;",
            (resumo,),
        ).fetchone()
        if not arquivo:
            return None
        arquivo = dict(arquivo)
        classificacoes = [dict(linha) for linha in con.execute(
            "SELECT categoria, confianca, data FROM classificacoes"
            " WHERE arquivo_id = ? ORDER BY data;",
            (arquivo["id"],),
        ).fetchall()]
        auditoria = [dict(linha) for linha in con.execute(
            "SELECT acao, caminho, data FROM auditoria"
            " WHERE caminho = ? OR caminho = ? ORDER BY data;",
            (arquivo["origem"], arquivo["destino"]),
        ).fetchall()]
        return {"arquivo": arquivo, "classificacoes": classificacoes, "auditoria": auditoria}
    finally:
        con.close()
