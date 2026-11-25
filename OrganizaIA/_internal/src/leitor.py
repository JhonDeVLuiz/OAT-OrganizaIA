"""Fase 2: trecho curto de texto. Vazio ou corrompido retorna '' sem levantar."""
from pathlib import Path

from .config import TRECHO_MAX_CHARS


def extrair_trecho(caminho, max_chars=TRECHO_MAX_CHARS):
    try:
        ext = Path(caminho).suffix.lower()
        if ext == ".pdf":
            texto = _de_pdf(caminho)
        elif ext == ".docx":
            texto = _de_docx(caminho)
        elif ext in (".xlsx", ".xls"):
            texto = _de_planilha(caminho)
        elif ext in (".txt", ".md", ".csv"):
            texto = _de_texto(caminho, max_chars)
        else:
            return ""
    except Exception:
        return ""
    return (texto or "")[:max_chars]


def _de_pdf(caminho):
    from pypdf import PdfReader

    partes = []
    for pagina in PdfReader(str(caminho)).pages:
        partes.append(pagina.extract_text() or "")
        if sum(len(p) for p in partes) >= TRECHO_MAX_CHARS:
            break
    return "\n".join(partes)


def _de_docx(caminho):
    import docx

    return "\n".join(p.text for p in docx.Document(str(caminho)).paragraphs)


def _de_planilha(caminho):
    import openpyxl

    livro = openpyxl.load_workbook(str(caminho), read_only=True, data_only=True)
    try:
        planilha = livro.active
        linhas = []
        for linha in planilha.iter_rows(values_only=True):
            linhas.append(" ".join("" if c is None else str(c) for c in linha))
            if sum(len(x) for x in linhas) >= TRECHO_MAX_CHARS:
                break
        return "\n".join(linhas)
    finally:
        livro.close()


def _de_texto(caminho, max_chars):
    with open(caminho, encoding="utf-8", errors="replace") as fh:
        return fh.read(max_chars + 1)
