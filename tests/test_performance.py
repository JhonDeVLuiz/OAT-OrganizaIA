"""Testes de performance - Validar desempenho com múltiplos arquivos e cenários de carga."""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import duplicatas, leitor, organizador, repositorio


def test_processar_100_arquivos_pequenos(tmp_path):
    """Performance: 100 arquivos pequenos devem ser processados rapidamente."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    banco = tmp_path / "teste.db"
    entrada.mkdir()

    # Cria 100 arquivos pequenos
    for i in range(100):
        (entrada / f"arquivo_{i:03d}.txt").write_text(f"conteudo {i}", encoding="utf-8")

    inicio = time.time()
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco, modo="tipo")
    duracao = time.time() - inicio

    assert len(resultado["movimentos"]) == 100
    assert duracao < 10.0  # deve processar em menos de 10 segundos


def test_hash_arquivo_grande(tmp_path):
    """Performance: SHA-256 de arquivo de 20MB deve ser rápido."""
    arquivo = tmp_path / "grande.bin"
    tamanho_mb = 20
    arquivo.write_bytes(b"X" * (tamanho_mb * 1024 * 1024))

    inicio = time.time()
    hash_resultado = duplicatas.sha256_arquivo(arquivo)
    duracao = time.time() - inicio

    assert len(hash_resultado) == 64  # SHA-256 hex
    assert duracao < 2.0  # deve hashear 20MB em menos de 2 segundos


def test_leitura_pdf_simples(tmp_path):
    """Performance: extração de trecho de PDF simples."""
    pdf = tmp_path / "simples.pdf"
    # Cria PDF mínimo válido
    pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    inicio = time.time()
    trecho = leitor.extrair_trecho(pdf)
    duracao = time.time() - inicio

    # Pode retornar vazio se PDF corrompido, mas não deve travar
    assert duracao < 1.0


def test_indice_hashes_500_arquivos(tmp_path):
    """Performance: índice de duplicatas com 500 arquivos organizados."""
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    organizados.mkdir()
    logs.mkdir()

    # Cria 500 arquivos organizados
    for i in range(500):
        pasta = organizados / f"Categoria_{i % 5}"
        pasta.mkdir(exist_ok=True)
        (pasta / f"arquivo_{i}.txt").write_text(f"conteudo {i}", encoding="utf-8")

    inicio = time.time()
    indice = duplicatas.indice_hashes(organizados, logs)
    duracao = time.time() - inicio

    assert len(indice) == 500
    assert duracao < 5.0  # deve indexar 500 arquivos em menos de 5 segundos


def test_consulta_banco_1000_registros(tmp_path):
    """Performance: consulta em banco com 1000+ registros."""
    banco = tmp_path / "grande.db"
    repositorio.iniciar_banco(banco)

    # Insere 1000 registros
    for i in range(1000):
        repositorio.salvar_arquivo(
            banco,
            resumo=f"hash_{i:04d}{'x' * 56}",
            origem=f"/entrada/arquivo_{i}.txt",
            destino=f"/organizados/Textos/arquivo_{i}.txt",
            categoria="Textos",
            origem_decisao="regras",
        )

    # Testa consulta
    con = repositorio._conectar(banco)
    try:
        inicio = time.time()
        resultados = con.execute("SELECT * FROM arquivos WHERE categoria = ?;", ("Textos",)).fetchall()
        duracao = time.time() - inicio

        assert len(resultados) == 1000
        assert duracao < 0.5  # consulta deve ser rápida com índice
    finally:
        con.close()


def test_processamento_arquivos_mistos(tmp_path):
    """Performance: mix de PDFs, DOCXs, TXTs e planilhas."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    banco = tmp_path / "teste.db"
    entrada.mkdir()

    # Cria arquivos de tipos diferentes
    for i in range(25):
        (entrada / f"doc_{i}.pdf").write_bytes(b"%PDF-1.4 content")
        (entrada / f"texto_{i}.txt").write_text(f"texto {i}", encoding="utf-8")
        (entrada / f"planilha_{i}.xlsx").write_text(f"dados {i}", encoding="utf-8")
        (entrada / f"documento_{i}.docx").write_text(f"doc {i}", encoding="utf-8")

    inicio = time.time()
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco, modo="tipo")
    duracao = time.time() - inicio

    # Conta apenas movimentos e duplicadas, ignora revisões
    processados = len([m for m in resultado["movimentos"] if m["status"] in ("movido", "duplicado")])
    assert processados >= 75
    assert duracao < 15.0


def test_hashes_logs_multiplas_execucoes(tmp_path):
    """Performance: leitura de hashes de 50 logs diferentes."""
    logs = tmp_path / "logs"
    logs.mkdir()

    # Cria 50 logs com 20 hashes cada
    import json
    for exec_num in range(50):
        log_data = {
            "id": f"exec_{exec_num}",
            "movimentos": [
                {"hash": f"hash_{exec_num}_{i}{'x' * 50}", "origem": f"arq_{i}.txt"}
                for i in range(20)
            ],
        }
        (logs / f"exec_{exec_num}.json").write_text(json.dumps(log_data), encoding="utf-8")

    inicio = time.time()
    hashes = duplicatas.hashes_dos_logs(logs)
    duracao = time.time() - inicio

    assert len(hashes) == 1000  # 50 logs × 20 hashes
    assert duracao < 2.0


def test_arquivo_no_limite_tamanho(tmp_path):
    """Performance: arquivo de exatamente 20MB (limite do sistema)."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    banco = tmp_path / "teste.db"
    entrada.mkdir()

    limite_bytes = 20 * 1024 * 1024
    (entrada / "no_limite.txt").write_bytes(b"X" * limite_bytes)

    inicio = time.time()
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco, modo="tipo")
    duracao = time.time() - inicio

    assert len(resultado["movimentos"]) == 1
    assert duracao < 5.0


@pytest.mark.slow
def test_stress_duplicatas_massivas(tmp_path):
    """Stress: detectar duplicatas em lote de 200 arquivos."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    banco = tmp_path / "teste.db"
    entrada.mkdir()

    # Cria 200 arquivos, sendo 100 duplicatas
    conteudos_unicos = [f"conteudo_unico_{i}" for i in range(100)]

    for i in range(100):
        (entrada / f"original_{i}.txt").write_text(conteudos_unicos[i], encoding="utf-8")
        (entrada / f"duplicata_{i}.txt").write_text(conteudos_unicos[i], encoding="utf-8")

    inicio = time.time()
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco, modo="tipo")
    duracao = time.time() - inicio

    # 100 originais movidos, 100 duplicatas detectadas
    duplicatas_encontradas = sum(1 for m in resultado["movimentos"] if m["status"] == "duplicado")
    assert duplicatas_encontradas == 100
    assert duracao < 30.0


def test_banco_wal_performance(tmp_path):
    """Performance: modo WAL deve permitir escritas rápidas."""
    banco = tmp_path / "wal_test.db"
    repositorio.iniciar_banco(banco)

    inicio = time.time()
    for i in range(100):
        repositorio.salvar_arquivo(
            banco,
            resumo=f"hash_{i}{'x' * 57}",
            origem=f"/entrada/arq_{i}.txt",
            destino=f"/organizados/Textos/arq_{i}.txt",
            categoria="Textos",
            origem_decisao="regras",
        )
    duracao = time.time() - inicio

    assert duracao < 2.0  # 100 inserções em menos de 2 segundos
