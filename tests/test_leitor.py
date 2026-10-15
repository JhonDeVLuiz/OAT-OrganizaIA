"""Fase 2: leitor (trecho curto; vazio/corrompido nao derruba)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import leitor
from src.config import TRECHO_MAX_CHARS


def test_txt_retorna_trecho_curto(tmp_path):
    alvo = tmp_path / "a.txt"
    alvo.write_text("x" * (TRECHO_MAX_CHARS + 500), encoding="utf-8")
    assert len(leitor.extrair_trecho(alvo)) == TRECHO_MAX_CHARS


def test_arquivo_vazio(tmp_path):
    alvo = tmp_path / "vazio.txt"
    alvo.write_text("", encoding="utf-8")
    assert leitor.extrair_trecho(alvo) == ""


def test_corrompido_nao_derruba(tmp_path):
    alvo = tmp_path / "fake.pdf"
    alvo.write_bytes(b"%PDF-nao-eh-um-pdf-de-verdade{{{")
    assert leitor.extrair_trecho(alvo) == ""


def test_docx_falso(tmp_path):
    import docx

    alvo = tmp_path / "doc.docx"
    doc = docx.Document()
    doc.add_paragraph("paragrafo falso de teste")
    doc.save(str(alvo))
    assert "paragrafo falso" in leitor.extrair_trecho(alvo)


def test_xlsx_falso(tmp_path):
    import openpyxl

    alvo = tmp_path / "plan.xlsx"
    livro = openpyxl.Workbook()
    livro.active["A1"] = "celula falsa"
    livro.save(str(alvo))
    livro.close()
    assert "celula falsa" in leitor.extrair_trecho(alvo)
