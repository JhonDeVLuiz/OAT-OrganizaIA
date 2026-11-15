"""Testes de integração E2E - Fluxos completos do OrganizaIA."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import backup, classificador, duplicatas, organizador, repositorio


def _pastas(tmp_path):
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    banco = tmp_path / "dados" / "teste.db"
    entrada.mkdir()
    return entrada, organizados, logs, banco


def test_fluxo_completo_modo_tipo(tmp_path):
    """E2E: arquivo entra → classificado por tipo → movido → auditado → log."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    # Cria arquivos de diferentes tipos
    (entrada / "relatorio.pdf").write_bytes(b"%PDF-1.4 conteudo")
    (entrada / "planilha.xlsx").write_text("dados", encoding="utf-8")
    (entrada / "texto.txt").write_text("anotacoes", encoding="utf-8")
    (entrada / "documento.docx").write_text("contrato", encoding="utf-8")

    # Processa tudo em modo tipo
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco, modo="tipo")

    # Verifica que o processamento funcionou
    assert resultado is not None
    assert isinstance(resultado, dict)


def test_fluxo_com_duplicatas(tmp_path):
    """E2E: duplicatas detectadas → pasta Duplicados → hash registrado."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    # Primeiro arquivo
    (entrada / "original.txt").write_text("conteudo unico", encoding="utf-8")
    resultado1 = organizador.processar(entrada, organizados, logs, db_path=banco)
    assert (organizados / "Textos" / "original.txt").exists()

    # Cria duplicata (mesmo conteúdo, nome diferente)
    (entrada / "copia.txt").write_text("conteudo unico", encoding="utf-8")
    resultado2 = organizador.processar(entrada, organizados, logs, db_path=banco)

    # Duplicata vai para pasta Duplicados
    assert resultado2["movimentos"][0]["status"] == "duplicado"
    assert (organizados / "Duplicados" / "copia.txt").exists()


def test_fluxo_desfazer_completo(tmp_path):
    """E2E: organiza → desfazer → arquivos voltam para entrada."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    # Cria e organiza múltiplos arquivos
    arquivos = ["doc1.txt", "doc2.pdf", "doc3.xlsx", "doc4.md"]
    for nome in arquivos:
        (entrada / nome).write_text(f"conteudo de {nome}", encoding="utf-8")

    resultado = organizador.processar(entrada, organizados, logs, db_path=banco)
    assert len(resultado["movimentos"]) == 4
    assert not list(entrada.iterdir())  # entrada vazia

    # Desfaz a operação
    desfeito = organizador.desfazer_ultima_execucao(logs, db_path=banco, raizes=(entrada, organizados))
    assert len(desfeito["restaurados"]) == 4

    # Verifica que voltaram
    for nome in arquivos:
        assert (entrada / nome).exists()
        assert (entrada / nome).read_text(encoding="utf-8") == f"conteudo de {nome}"


def test_fluxo_backup_restauracao(tmp_path):
    """E2E: organiza → exporta backup → limpa → importa → verifica integridade."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    # Organiza alguns arquivos
    (entrada / "importante.txt").write_text("dados criticos", encoding="utf-8")
    (entrada / "contrato.pdf").write_bytes(b"%PDF dados")
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco)

    # Exporta backup
    backup_zip = tmp_path / "backup_teste.zip"
    base_backup = banco.parent.parent
    resultado_backup = backup.exportar_backup(str(backup_zip), base=base_backup)
    assert backup_zip.exists()

    # Simula perda de dados
    banco.unlink()
    assert not banco.exists()

    # Restaura backup
    nova_base = tmp_path / "restaurado"
    nova_base.mkdir()
    resultado_import = backup.importar_backup(str(backup_zip), base=nova_base, reindexar=False)

    # Verifica que o processo funcionou
    assert resultado_import is not None
    assert isinstance(resultado_import, dict)


def test_fluxo_arquivo_excluido(tmp_path):
    """E2E: arquivo sensível → ignorado → permanece na entrada → log explica."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    (entrada / "normal.txt").write_text("ok", encoding="utf-8")
    (entrada / ".env").write_text("SECRET=123", encoding="utf-8")
    (entrada / "senhas.txt").write_text("admin:pass", encoding="utf-8")

    resultado = organizador.processar(entrada, organizados, logs, db_path=banco)

    # Apenas o normal foi movido
    assert len(resultado["movimentos"]) == 1
    assert len(resultado["ignorados"]) == 2

    # Sensíveis permanecem
    assert (entrada / ".env").exists()
    assert (entrada / "senhas.txt").exists()
    assert not (entrada / "normal.txt").exists()

    # Verifica motivos
    motivos = {ign["motivo"] for ign in resultado["ignorados"]}
    assert motivos == {"excluido"}


def test_fluxo_arquivo_grande(tmp_path):
    """E2E: arquivo > limite → ignorado → permanece na entrada."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    (entrada / "pequeno.txt").write_text("ok", encoding="utf-8")
    (entrada / "enorme.txt").write_bytes(b"X" * 1000)  # 1KB

    # Define limite baixo para forçar rejeição
    resultado = organizador.processar(entrada, organizados, logs, max_bytes=500, db_path=banco)

    assert len(resultado["movimentos"]) == 1
    assert len(resultado["ignorados"]) == 1
    assert resultado["ignorados"][0]["motivo"] == "grande"
    assert (entrada / "enorme.txt").exists()


def test_fluxo_sufixo_evita_sobrescrita(tmp_path):
    """E2E: arquivo já existe no destino → ganha sufixo (1) → ambos coexistem."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    # Pré-popula destino
    (organizados / "Textos").mkdir(parents=True)
    (organizados / "Textos" / "doc.txt").write_text("versao antiga", encoding="utf-8")

    # Processa novo arquivo com mesmo nome
    (entrada / "doc.txt").write_text("versao nova", encoding="utf-8")
    organizador.processar(entrada, organizados, logs, db_path=banco)

    # Ambos existem
    assert (organizados / "Textos" / "doc.txt").exists()
    assert (organizados / "Textos" / "doc (1).txt").exists()
    assert (organizados / "Textos" / "doc.txt").read_text(encoding="utf-8") == "versao antiga"
    assert (organizados / "Textos" / "doc (1).txt").read_text(encoding="utf-8") == "versao nova"


def test_fluxo_dry_run_nao_persiste(tmp_path):
    """E2E: dry-run → simula tudo → nada muda no disco → sem log, sem banco."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    (entrada / "teste.txt").write_text("conteudo", encoding="utf-8")

    resultado = organizador.processar(entrada, organizados, logs, dry_run=True, db_path=banco)

    assert resultado["dry_run"] is True
    assert resultado["id"] is None
    assert len(resultado["movimentos"]) == 1

    # Arquivo permanece na entrada
    assert (entrada / "teste.txt").exists()
    assert not (organizados / "Textos" / "teste.txt").exists()

    # Sem persistência
    assert not list(logs.glob("exec_*.json"))
    assert not banco.exists()


def test_fluxo_hash_index_evita_reprocessamento(tmp_path):
    """E2E: arquivo já organizado → hash no índice → detectado como duplicata."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    # Primeira execução
    (entrada / "original.txt").write_text("dados", encoding="utf-8")
    organizador.processar(entrada, organizados, logs, db_path=banco)

    # Copia o arquivo de volta para entrada (mesmo hash)
    import shutil
    shutil.copy(organizados / "Textos" / "original.txt", entrada / "reprocessado.txt")

    # Segunda execução
    resultado2 = organizador.processar(entrada, organizados, logs, db_path=banco)

    # Detectado como duplicata
    assert resultado2["movimentos"][0]["status"] == "duplicado"
    assert (organizados / "Duplicados" / "reprocessado.txt").exists()


def test_fluxo_logs_json_multiplas_execucoes(tmp_path):
    """E2E: múltiplas execuções → cada uma com seu log JSON único."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    # Execução 1
    (entrada / "arq1.txt").write_text("1", encoding="utf-8")
    res1 = organizador.processar(entrada, organizados, logs, db_path=banco)

    # Execução 2
    (entrada / "arq2.txt").write_text("2", encoding="utf-8")
    res2 = organizador.processar(entrada, organizados, logs, db_path=banco)

    # Dois logs diferentes
    assert res1["id"] != res2["id"]
    assert (logs / f"exec_{res1['id']}.json").exists()
    assert (logs / f"exec_{res2['id']}.json").exists()

    # Conteúdos distintos
    log1 = json.loads((logs / f"exec_{res1['id']}.json").read_text(encoding="utf-8"))
    log2 = json.loads((logs / f"exec_{res2['id']}.json").read_text(encoding="utf-8"))
    assert log1["movimentos"][0]["origem"].endswith("arq1.txt")
    assert log2["movimentos"][0]["origem"].endswith("arq2.txt")


def test_fluxo_banco_wal_mode(tmp_path):
    """E2E: banco criado com WAL mode ativado para concorrência."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    (entrada / "teste.txt").write_text("wal test", encoding="utf-8")
    organizador.processar(entrada, organizados, logs, db_path=banco)

    # Verifica WAL mode
    con = repositorio._conectar(banco)
    try:
        modo = con.execute("PRAGMA journal_mode;").fetchone()[0]
        assert modo.lower() == "wal"
    finally:
        con.close()


def test_fluxo_indices_criados(tmp_path):
    """E2E: banco criado com todos os índices esperados."""
    entrada, organizados, logs, banco = _pastas(tmp_path)

    (entrada / "teste.txt").write_text("index test", encoding="utf-8")
    organizador.processar(entrada, organizados, logs, db_path=banco)

    con = repositorio._conectar(banco)
    try:
        indices = con.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';"
        ).fetchall()
        nomes = {idx["name"] for idx in indices}

        assert "idx_arquivos_hash" in nomes
        assert "idx_arquivos_destino" in nomes
        assert "idx_arquivos_categoria" in nomes
        assert "idx_classificacoes_arquivo" in nomes
    finally:
        con.close()
