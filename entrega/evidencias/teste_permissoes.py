"""Prova de conceito de permissoes no banco + auditoria com 'quem pediu'.

1) SQLite nao tem CREATE ROLE/GRANT, mas tem sqlite3.Connection.set_authorizer:
   o mesmo mecanismo que o SQL Server resolve com GRANT/DENY e aplicado por
   perfil (leitor, ia, admin) nas consultas reais usadas pelo chat.
2) Executa uma leitura pelo ChatSession e mostra a auditoria (acao, caminho,
   usuario, data) gerada.

Uso: .\\.venv\\Scripts\\python.exe entrega\\evidencias\\teste_permissoes.py
Saida: entrega/evidencias/resultados_permissoes.json
"""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import repositorio
from src.chat import ChatSession

SAIDA = Path(__file__).resolve().parent / "resultados_permissoes.json"

ACOES_ESCRITA = {
    sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE,
    sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_INDEX,
}

# perfil -> (tabelas com SELECT permitido, pode escrever?)
PERFIS = {
    "leitor": ({"arquivos", "classificacoes"}, False),
    "ia": ({"arquivos", "classificacoes"}, False),
    "admin": ({"arquivos", "classificacoes", "auditoria"}, True),
}


def _autorizador(perfil):
    permitidas, escreve = PERFIS[perfil]

    def autorizar(acao, arg1, arg2, banco, gatilho):
        if acao == sqlite3.SQLITE_READ:
            return sqlite3.SQLITE_OK if arg1 in permitidas else sqlite3.SQLITE_DENY
        if acao == sqlite3.SQLITE_SELECT:
            return sqlite3.SQLITE_OK
        if acao in ACOES_ESCRITA:
            return sqlite3.SQLITE_OK if escreve else sqlite3.SQLITE_DENY
        if acao == sqlite3.SQLITE_PRAGMA:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    return autorizar


def _conectar(perfil, banco):
    con = sqlite3.connect(str(banco))
    con.set_authorizer(_autorizador(perfil))
    return con


def _tentar(perfil, banco, rotulo, sql, params=()):
    con = _conectar(perfil, banco)
    try:
        linhas = con.execute(sql, params).fetchall()
        return {"perfil": perfil, "operacao": rotulo, "resultado": "PERMITIDO",
                "linhas": len(linhas)}
    except sqlite3.DatabaseError as exc:
        return {"perfil": perfil, "operacao": rotulo, "resultado": "NEGADO",
                "erro": str(exc)}
    finally:
        con.close()


def executar():
    raiz = Path(tempfile.mkdtemp(prefix="organizaia_perm_"))
    try:
        banco = raiz / "perm.db"
        repositorio.iniciar_banco(banco)
        repositorio.salvar_movimentos(banco, [{
            "status": "movido", "origem": "entrada/fatura.pdf",
            "destino": "organizados/Faturas/fatura.pdf", "hash": "a" * 64,
            "categoria": "Faturas", "data": "2026-11-16T10:00:00+00:00",
        }])

        # ---- 1) RBAC no banco (equivalente a GRANT/DENY) ----
        sql_busca = ("SELECT hash, destino FROM arquivos"
                     " WHERE destino LIKE ? ESCAPE '\\' LIMIT 5;")
        sql_hist = ("SELECT acao, caminho, data FROM auditoria"
                    " WHERE caminho = ? OR caminho = ?;")
        sql_insert = ("INSERT INTO arquivos (hash, origem, destino, categoria,"
                      " origem_decisao, criado_em) VALUES (?,?,?,?,?,?);")
        caminho = "organizados/Faturas/fatura.pdf"
        provas = [
            _tentar("ia", banco, "IA consulta metadados (buscar_por_nome)",
                    sql_busca, ("%fatura%",)),
            _tentar("ia", banco, "IA consulta historico/auditoria",
                    sql_hist, (caminho, "entrada/fatura.pdf")),
            _tentar("ia", banco, "IA tenta INSERT (escrita)",
                    sql_insert, ("b" * 64, "e/x", "o/x", "Outros", "ia",
                                 "2026-11-16")),
            _tentar("leitor", banco, "Leitor consulta metadados",
                    sql_busca, ("%fatura%",)),
            _tentar("leitor", banco, "Leitor consulta auditoria",
                    sql_hist, (caminho, "entrada/fatura.pdf")),
            _tentar("admin", banco, "Admin consulta auditoria",
                    sql_hist, (caminho, "entrada/fatura.pdf")),
            _tentar("admin", banco, "Admin INSERT (escrita)",
                    sql_insert, ("b" * 64, "e/x", "o/x", "Outros", "ia",
                                 "2026-11-16")),
        ]

        # ---- 2) Auditoria da leitura feita pela IA (tool ler_trecho) ----
        organizados = raiz / "organizados"
        organizados.mkdir()
        (organizados / "nota.txt").write_text(
            "Nota ficticia com CPF 123.456.789-00.", encoding="utf-8")
        sessao = ChatSession(entrada=raiz / "entrada", organizados=organizados,
                             logs=raiz / "logs", banco=banco,
                             confirmar=lambda *a: False)
        leitura = sessao.ferramentas["ler_trecho"](
            {"caminho": "organizados/nota.txt"})
        auditoria = repositorio.listar_auditoria(banco, limite=5)

        resultado = {"rbac": provas, "auditoria": auditoria,
                     "leitura_ok": leitura.get("ok"),
                     "trecho": leitura.get("trecho", "")[:120]}
        SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        for prova in provas:
            print(f"[{prova['resultado']:8}] {prova['perfil']:6} {prova['operacao']}"
                  + (f" ({prova.get('erro')})" if prova.get("erro") else ""))
        print("\nauditoria:")
        for linha in auditoria:
            print(" ", linha)
        print("salvo em", SAIDA)
    finally:
        import shutil
        shutil.rmtree(raiz, ignore_errors=True)


if __name__ == "__main__":
    executar()
