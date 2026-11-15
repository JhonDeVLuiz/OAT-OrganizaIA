"""Testes para src/monitor.py - Observador de pasta em tempo real com watchdog."""
import sys
import time
from pathlib import Path
from threading import Thread

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import monitor


def test_deve_ignorar_arquivos_temporarios():
    """Arquivos .tmp, .crdownload e .part devem ser ignorados."""
    assert monitor.deve_ignorar("download.tmp")
    assert monitor.deve_ignorar("arquivo.crdownload")
    assert monitor.deve_ignorar("video.part")
    assert monitor.deve_ignorar("ARQUIVO.TMP")  # case insensitive
    assert not monitor.deve_ignorar("documento.txt")
    assert not monitor.deve_ignorar("relatorio.pdf")


def test_arquivo_estavel_retorna_true_quando_parou_de_crescer(tmp_path):
    """Arquivo que não está mais sendo escrito deve ser considerado estável."""
    arquivo = tmp_path / "teste.txt"
    arquivo.write_text("conteudo completo", encoding="utf-8")

    # Arquivo pronto deve ser estável imediatamente
    assert monitor.arquivo_estavel(arquivo, intervalo=0.1, tentativas=3)


def test_arquivo_estavel_retorna_false_se_sumiu(tmp_path):
    """Se arquivo desaparece durante verificação, retorna False."""
    arquivo = tmp_path / "temporario.txt"
    arquivo.write_text("existe", encoding="utf-8")
    arquivo.unlink()  # remove o arquivo

    assert not monitor.arquivo_estavel(arquivo, intervalo=0.1, tentativas=2)


def test_arquivo_estavel_aguarda_parar_de_crescer(tmp_path):
    """Arquivo sendo escrito deve aguardar estabilização."""
    arquivo = tmp_path / "crescendo.txt"
    arquivo.write_text("inicio", encoding="utf-8")

    def escrever_aos_poucos():
        time.sleep(0.2)
        arquivo.write_text("inicio" + "x" * 100, encoding="utf-8")
        time.sleep(0.2)
        arquivo.write_text("inicio" + "x" * 200, encoding="utf-8")

    Thread(target=escrever_aos_poucos, daemon=True).start()

    # Com intervalo e tentativas suficientes, deve detectar estabilização
    resultado = monitor.arquivo_estavel(arquivo, intervalo=0.15, tentativas=20)
    assert resultado  # eventualmente estabiliza


def test_handler_ignora_temporarios(tmp_path):
    """Handler não deve processar arquivos temporários."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    entrada.mkdir()

    handler = monitor._Handler(entrada, organizados, logs, dry_run=True)

    # Cria arquivo temporário
    temp = entrada / "download.tmp"
    temp.write_text("temporario", encoding="utf-8")

    # Simula evento de criação
    from watchdog.events import FileCreatedEvent
    evento = FileCreatedEvent(str(temp))
    handler.on_created(evento)

    # Arquivo temporário não deve ser movido
    assert temp.exists()
    assert not list(organizados.rglob("*"))


def test_handler_processa_arquivo_valido(tmp_path):
    """Handler deve processar arquivos válidos em modo dry-run."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    entrada.mkdir()

    handler = monitor._Handler(entrada, organizados, logs, dry_run=True, modo="tipo")

    arquivo = entrada / "documento.txt"
    arquivo.write_text("conteudo valido", encoding="utf-8")

    from watchdog.events import FileCreatedEvent
    evento = FileCreatedEvent(str(arquivo))
    handler.on_created(evento)

    # Em dry-run, arquivo permanece no lugar
    assert arquivo.exists()


def test_handler_nao_processa_diretorios(tmp_path):
    """Handler deve ignorar eventos de diretórios."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    entrada.mkdir()

    handler = monitor._Handler(entrada, organizados, logs, dry_run=True)

    subpasta = entrada / "nova_pasta"
    subpasta.mkdir()

    from watchdog.events import DirCreatedEvent
    evento = DirCreatedEvent(str(subpasta))
    handler.on_created(evento)

    # Diretórios são ignorados, não deve gerar erro
    assert subpasta.exists()


def test_handler_on_moved_processa_destino(tmp_path):
    """Evento on_moved deve processar o arquivo no destino."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    entrada.mkdir()

    handler = monitor._Handler(entrada, organizados, logs, dry_run=True, modo="tipo")

    origem = entrada / "original.txt"
    destino = entrada / "renomeado.txt"
    origem.write_text("conteudo", encoding="utf-8")
    origem.rename(destino)

    from watchdog.events import FileMovedEvent
    evento = FileMovedEvent(str(origem), str(destino))
    handler.on_moved(evento)

    # Arquivo renomeado deve ser processado
    assert destino.exists()


def test_handler_modo_ia(tmp_path):
    """Handler deve aceitar modo='ia' e repassar ao organizador."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    entrada.mkdir()

    handler = monitor._Handler(entrada, organizados, logs, dry_run=True, modo="ia")

    assert handler.modo == "ia"
    assert handler.entrada == entrada
    assert handler.organizados == organizados


def test_arquivo_estavel_timeout_retorna_false(tmp_path):
    """Se exceder tentativas, retorna False mesmo que arquivo exista."""
    arquivo = tmp_path / "infinito.txt"

    def crescer_infinitamente():
        for i in range(50):
            arquivo.write_text("x" * (i * 100), encoding="utf-8")
            time.sleep(0.05)

    Thread(target=crescer_infinitamente, daemon=True).start()
    time.sleep(0.1)  # aguarda começar a escrever

    # Com poucas tentativas, deve desistir
    resultado = monitor.arquivo_estavel(arquivo, intervalo=0.05, tentativas=3)
    assert not resultado  # desistiu antes de estabilizar


def test_handler_dry_run_true(tmp_path):
    """Handler em dry_run=True não deve mover arquivos."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    entrada.mkdir()

    handler = monitor._Handler(entrada, organizados, logs, dry_run=True)
    assert handler.dry_run is True


def test_handler_dry_run_false(tmp_path):
    """Handler em dry_run=False deve mover arquivos (não testamos movimento real aqui)."""
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    entrada.mkdir()

    handler = monitor._Handler(entrada, organizados, logs, dry_run=False)
    assert handler.dry_run is False


def test_deve_ignorar_case_insensitive():
    """Extensões devem ser case-insensitive."""
    assert monitor.deve_ignorar("arquivo.TMP")
    assert monitor.deve_ignorar("arquivo.CrDoWnLoAd")
    assert monitor.deve_ignorar("arquivo.PART")
