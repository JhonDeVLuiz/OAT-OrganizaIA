"""Fase 3: repositorio SQLite (insercao, duplicado, consulta, injection)."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import organizador, repositorio


def _banco(tmp_path):
    banco = tmp_path / "teste.db"
    repositorio.iniciar_banco(banco)
    return banco


def _contar(banco, tabela):
    con = sqlite3.connect(str(banco))
    try:
        return con.execute(f"SELECT COUNT(*) FROM {tabela};").fetchone()[0]
    finally:
        con.close()


def test_iniciar_cria_tabelas_e_wal(tmp_path):
    banco = _banco(tmp_path)
    con = sqlite3.connect(str(banco))
    try:
        tabelas = {linha[0] for linha in con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table';")}
        modo = con.execute("PRAGMA journal_mode;").fetchone()[0]
    finally:
        con.close()
    assert {"arquivos", "classificacoes", "auditoria"} <= tabelas
    assert modo == "wal"


def test_insercao_e_consultas(tmp_path):
    banco = _banco(tmp_path)
    repositorio.salvar_arquivo(banco, "h1", "e/a.txt", "o/Textos/a.txt", "Textos", "regras")
    repositorio.salvar_arquivo(banco, "h2", "e/b.csv", "o/Planilhas/b.csv", "Planilhas", "regras")
    achado = repositorio.buscar_por_hash(banco, "h1")
    assert achado["destino"] == "o/Textos/a.txt" and achado["categoria"] == "Textos"
    assert repositorio.buscar_por_hash(banco, "inexistente") is None
    textos = repositorio.buscar_por_categoria(banco, "Textos")
    assert [linha["hash"] for linha in textos] == ["h1"]


def test_duplicado_nao_duplica(tmp_path):
    banco = _banco(tmp_path)
    id1 = repositorio.salvar_arquivo(banco, "h1", "e/a.txt", "o/a.txt", "Textos", "regras")
    id2 = repositorio.salvar_arquivo(banco, "h1", "e/a.txt", "o/a.txt", "Textos", "regras")
    assert id1 == id2 and _contar(banco, "arquivos") == 1


def test_lote_idempotente(tmp_path):
    banco = _banco(tmp_path)
    movs = [{"status": "movido", "origem": "e/a.txt", "destino": "o/a.txt",
             "hash": "h1", "categoria": "Textos", "data": "2026-01-01"}]
    repositorio.salvar_movimentos(banco, movs)
    repositorio.salvar_movimentos(banco, movs)
    assert _contar(banco, "arquivos") == 1
    assert _contar(banco, "classificacoes") == 1


def test_historico_do_arquivo(tmp_path):
    banco = _banco(tmp_path)
    repositorio.salvar_movimentos(banco, [
        {"status": "movido", "origem": "e/a.txt", "destino": "o/a.txt",
         "hash": "h1", "categoria": "Textos", "data": "2026-01-01"}])
    hist = repositorio.historico_do_arquivo(banco, "h1")
    assert hist["arquivo"]["categoria"] == "Textos"
    assert hist["classificacoes"][0]["confianca"] == 1.0
    assert hist["auditoria"][0] == {"acao": "mover", "caminho": "o/a.txt", "data": "2026-01-01"}
    assert repositorio.historico_do_arquivo(banco, "desconhecido") is None


def test_sql_injection_pelo_nome(tmp_path):
    banco = _banco(tmp_path)
    malicioso = "x'; DROP TABLE arquivos; --.txt"
    repositorio.salvar_arquivo(banco, "h1", f"e/{malicioso}", "o/Textos/a.txt", "Textos", "regras")
    assert repositorio.buscar_por_categoria(banco, "Textos' OR '1'='1") == []
    assert _contar(banco, "arquivos") == 1  # tabela intacta


def test_so_metadados_sem_conteudo(tmp_path):
    banco = _banco(tmp_path)
    (tmp_path / "e").mkdir()
    alvo = tmp_path / "e" / "s.txt"
    alvo.write_text("segredo-unico-987", encoding="utf-8")
    repositorio.salvar_movimentos(banco, [
        {"status": "movido", "origem": str(alvo), "destino": "o/s.txt",
         "hash": "h1", "categoria": "Textos"}])
    con = sqlite3.connect(str(banco))
    try:
        bruto = "\n".join(str(linha) for linha in con.execute(
            "SELECT hash, origem, destino, categoria FROM arquivos;"))
    finally:
        con.close()
    assert "segredo-unico-987" not in bruto


def test_integracao_organizador_grava_banco(tmp_path):
    entrada, organizados, logs = tmp_path / "e", tmp_path / "o", tmp_path / "l"
    banco = tmp_path / "teste.db"
    entrada.mkdir()
    (entrada / "a.txt").write_text("oi", encoding="utf-8")
    organizador.processar(entrada, organizados, logs, db_path=banco)
    assert [linha["hash"] for linha in repositorio.buscar_por_categoria(banco, "Textos")]
    con = sqlite3.connect(str(banco))
    try:
        acoes = [linha[0] for linha in con.execute("SELECT acao FROM auditoria;")]
    finally:
        con.close()
    assert acoes == ["mover"]
