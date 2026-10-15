"""Fase 2: organizador (dry-run, desfazer, sufixo, duplicata, limites)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import organizador


def _pastas(tmp_path):
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    entrada.mkdir()
    return entrada, organizados, logs


def test_dry_run_nao_move(tmp_path):
    entrada, organizados, logs = _pastas(tmp_path)
    (entrada / "a.txt").write_text("oi", encoding="utf-8")
    (entrada / "x.tmp").write_text("temp", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs, dry_run=True)
    assert resultado["dry_run"] is True and resultado["id"] is None
    assert (entrada / "a.txt").is_file()  # nada saiu do lugar
    assert not (organizados / "Textos" / "a.txt").exists()
    assert list(logs.glob("exec_*.json")) == []  # sem log no dry-run


def test_desfazer_restaura_tudo(tmp_path):
    entrada, organizados, logs = _pastas(tmp_path)
    (entrada / "a.txt").write_text("um", encoding="utf-8")
    (entrada / "b.txt").write_text("dois", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs)
    assert resultado["id"] is not None
    assert not list(entrada.iterdir())
    desfeito = organizador.desfazer_ultima_execucao(logs)
    assert desfeito["id"] == resultado["id"]
    assert len(desfeito["restaurados"]) == 2
    assert (entrada / "a.txt").read_text(encoding="utf-8") == "um"
    assert (entrada / "b.txt").read_text(encoding="utf-8") == "dois"


def test_nome_repetido_ganha_sufixo(tmp_path):
    entrada, organizados, logs = _pastas(tmp_path)
    (organizados / "Textos").mkdir(parents=True)
    (organizados / "Textos" / "a.txt").write_text("antigo", encoding="utf-8")
    (entrada / "a.txt").write_text("novo", encoding="utf-8")
    organizador.processar(entrada, organizados, logs)
    copia = organizados / "Textos" / "a (1).txt"
    assert copia.is_file() and copia.read_text(encoding="utf-8") == "novo"
    assert (organizados / "Textos" / "a.txt").read_text(encoding="utf-8") == "antigo"


def test_duplicata_vai_para_duplicados(tmp_path):
    entrada, organizados, logs = _pastas(tmp_path)
    (organizados / "Textos").mkdir(parents=True)
    (organizados / "Textos" / "orig.txt").write_text("mesmo", encoding="utf-8")
    (entrada / "copia.txt").write_text("mesmo", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs)
    assert resultado["movimentos"][0]["status"] == "duplicado"
    assert (organizados / "Duplicados" / "copia.txt").is_file()


def test_arquivo_grande_e_excluido_ficam(tmp_path):
    entrada, organizados, logs = _pastas(tmp_path)
    (entrada / "grande.txt").write_bytes(b"0" * 64)
    (entrada / ".env").write_text("K=v", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs, max_bytes=10)
    motivos = {ign["motivo"] for ign in resultado["ignorados"]}
    assert motivos == {"grande", "excluido"}
    assert (entrada / "grande.txt").is_file() and (entrada / ".env").is_file()


def test_log_tem_id_e_sem_conteudo(tmp_path):
    entrada, organizados, logs = _pastas(tmp_path)
    (entrada / "segredo.txt").write_text("conteudo sensivel 123", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs)
    dados = json.loads(next(logs.glob("exec_*.json")).read_text(encoding="utf-8"))
    assert dados["id"] == resultado["id"]
    bruto = json.dumps(dados)
    assert "conteudo sensivel" not in bruto  # log so com metadados
