"""Fase 3: unico ponto de acesso ao SQLite. So metadados, tudo parametrizado."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import DB_PATH

# Papéis de banco (equivalem a GRANT/DENY no SQL Server alvo).
# Acesso do chat (agente-IA) é restrito a leitura de metadados: nunca escreve
# nem enxerga a tabela de auditoria.
PERFIS_BANCO = {
    "ia": ({"arquivos", "classificacoes"}, False),
    "admin": ({"arquivos", "classificacoes", "auditoria"}, True),
}

_ACOES_ESCRITA = {
    sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE,
    sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_INDEX,
}


def conectar_restrito(banco, perfil="ia"):
    """Abre conexão SQLite com autorizador por perfil (RBAC).

    `perfil="ia"`: só SELECT em arquivos/classificacoes (metadados). Negado:
    escrita, PRAGMA e acesso a auditoria. Usado pelo chat para garantir o
    papel restrito sem dependir do SQL Server.
    """
    permitidas, escreve = PERFIS_BANCO.get(perfil, PERFIS_BANCO["ia"])

    def autorizar(acao, arg1, arg2, banco_nome, gatilho):
        if acao == sqlite3.SQLITE_READ:
            return sqlite3.SQLITE_OK if arg1 in permitidas else sqlite3.SQLITE_DENY
        if acao == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if acao in _ACOES_ESCRITA:
            return sqlite3.SQLITE_OK if escreve else sqlite3.SQLITE_DENY
        if acao == sqlite3.SQLITE_PRAGMA:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    con = sqlite3.connect(str(banco))
    con.set_authorizer(autorizar)
    con.row_factory = sqlite3.Row
    return con

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
    usuario TEXT,
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


def _usuario():
    """Quem pediu a acao (usuario local da sessao), sem dado sensivel."""
    import getpass
    import os

    try:
        return getpass.getuser() or os.getenv("USERNAME") or "local"
    except Exception:  # noqa: BLE001 - auditoria nunca derruba o fluxo
        return os.getenv("USERNAME") or "local"


def iniciar_banco(banco=None):
    """Cria tabelas e indices; ativa WAL. Idempotente."""
    con = _conectar(banco)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.executescript(_SCHEMA)
        colunas = {linha[1] for linha in con.execute("PRAGMA table_info(auditoria);")}
        if "usuario" not in colunas:  # migracao de bancos antigos
            con.execute("ALTER TABLE auditoria ADD COLUMN usuario TEXT;")
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


def registrar_auditoria(banco, acao, caminho, data=None, usuario=None):
    data = data or _agora()
    con = _conectar(banco)
    try:
        cur = con.execute(
            "INSERT INTO auditoria (acao, caminho, usuario, data) VALUES (?, ?, ?, ?);",
            (acao, str(caminho), usuario or _usuario(), data),
        )
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def listar_auditoria(banco, limite=20, perfil=None):
    """Ultimas acoes: o que foi consultado, quem pediu e quando.

    Com `perfil="ia"` a conexão é restrita (negada a leitura de auditoria),
    então o chat do papel restrito não enxerga essa tabela.
    """
    con = conectar_restrito(banco, perfil) if perfil else _conectar(banco)
    try:
        linhas = con.execute(
            "SELECT acao, caminho, usuario, data FROM auditoria"
            " ORDER BY id DESC LIMIT ?;",
            (int(limite),),
        ).fetchall()
        return [dict(linha) for linha in linhas]
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
                "INSERT INTO auditoria (acao, caminho, usuario, data) VALUES (?, ?, ?, ?);",
                ("mover", str(mov["destino"]), mov.get("usuario") or _usuario(),
                 mov.get("data") or _agora()),
            )
        con.commit()
        return ids
    finally:
        con.close()


def buscar_por_categoria(banco, categoria, perfil=None):
    con = conectar_restrito(banco, perfil) if perfil else _conectar(banco)
    try:
        linhas = con.execute(
            "SELECT hash, origem, destino, categoria, origem_decisao, criado_em"
            " FROM arquivos WHERE categoria = ? ORDER BY destino;",
            (categoria,),
        ).fetchall()
        return [dict(linha) for linha in linhas]
    finally:
        con.close()


def buscar_por_nome(banco, termo, perfil=None):
    """Busca destino por trecho do nome (LIKE parametrizado com escape)."""
    limpo = (termo.replace("\\", "\\\\").replace("%", "\\%")
             .replace("_", "\\_"))
    con = conectar_restrito(banco, perfil) if perfil else _conectar(banco)
    try:
        linhas = con.execute(
            "SELECT hash, origem, destino, categoria, origem_decisao, criado_em"
            " FROM arquivos WHERE destino LIKE ? ESCAPE '\\' ORDER BY destino LIMIT 50;",
            (f"%{limpo}%",),
        ).fetchall()
        return [dict(linha) for linha in linhas]
    finally:
        con.close()


def buscar_por_hash(banco, resumo, perfil=None):
    con = conectar_restrito(banco, perfil) if perfil else _conectar(banco)
    try:
        linha = con.execute(
            "SELECT hash, origem, destino, categoria, origem_decisao, criado_em"
            " FROM arquivos WHERE hash = ?;",
            (resumo,),
        ).fetchone()
        return dict(linha) if linha else None
    finally:
        con.close()


def historico_do_arquivo(banco, resumo, perfil=None):
    """Arquivo + classificacoes + auditoria dos seus caminhos. None se desconhecido.

    Com `perfil="ia"` a leitura da tabela auditoria é negada (papel restrito).
    """
    con = conectar_restrito(banco, perfil) if perfil else _conectar(banco)
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
