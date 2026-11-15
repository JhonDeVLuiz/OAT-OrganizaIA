"""Testes expandidos para src/regras.py - Decisão de categoria por extensão."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import regras


def test_categoria_por_extensao_pdf():
    """PDFs devem ir para categoria PDFs."""
    assert regras.categoria_por_extensao(".pdf") == "PDFs"
    assert regras.categoria_por_extensao(".PDF") == "PDFs"


def test_categoria_por_extensao_documentos():
    """DOC, DOCX e ODT devem ir para Documentos."""
    assert regras.categoria_por_extensao(".doc") == "Documentos"
    assert regras.categoria_por_extensao(".docx") == "Documentos"
    assert regras.categoria_por_extensao(".odt") == "Documentos"
    assert regras.categoria_por_extensao(".DOCX") == "Documentos"


def test_categoria_por_extensao_planilhas():
    """XLS, XLSX, CSV e ODS devem ir para Planilhas."""
    assert regras.categoria_por_extensao(".xls") == "Planilhas"
    assert regras.categoria_por_extensao(".xlsx") == "Planilhas"
    assert regras.categoria_por_extensao(".csv") == "Planilhas"
    assert regras.categoria_por_extensao(".ods") == "Planilhas"
    assert regras.categoria_por_extensao(".XLSX") == "Planilhas"


def test_categoria_por_extensao_textos():
    """TXT e MD devem ir para Textos."""
    assert regras.categoria_por_extensao(".txt") == "Textos"
    assert regras.categoria_por_extensao(".md") == "Textos"
    assert regras.categoria_por_extensao(".TXT") == "Textos"


def test_categoria_por_extensao_desconhecida():
    """Extensões desconhecidas devem retornar None."""
    assert regras.categoria_por_extensao(".xyz") is None
    assert regras.categoria_por_extensao(".unknown") is None
    assert regras.categoria_por_extensao(".exe") is None
    assert regras.categoria_por_extensao(".zip") is None


def test_categoria_por_extensao_vazia():
    """Extensão vazia deve retornar None."""
    assert regras.categoria_por_extensao("") is None
    assert regras.categoria_por_extensao(".") is None


def test_categoria_por_extensao_case_insensitive():
    """Extensões devem ser case-insensitive."""
    assert regras.categoria_por_extensao(".Pdf") == "PDFs"
    assert regras.categoria_por_extensao(".TxT") == "Textos"
    assert regras.categoria_por_extensao(".XlSx") == "Planilhas"
    assert regras.categoria_por_extensao(".dOcX") == "Documentos"


def test_decidir_com_caminho_completo():
    """Decidir deve funcionar com caminho completo."""
    assert regras.decidir("/pasta/arquivo.pdf") == "PDFs"
    assert regras.decidir("C:\\Users\\Documents\\relatorio.docx") == "Documentos"
    assert regras.decidir("./entrada/dados.xlsx") == "Planilhas"


def test_decidir_com_apenas_nome():
    """Decidir deve funcionar com apenas o nome do arquivo."""
    assert regras.decidir("documento.txt") == "Textos"
    assert regras.decidir("foto.jpg") is None  # não suportado


def test_decidir_multiplas_extensoes():
    """Arquivo com múltiplas extensões deve usar a última."""
    assert regras.decidir("backup.tar.gz") is None  # .gz não mapeado
    assert regras.decidir("arquivo.backup.txt") == "Textos"
    assert regras.decidir("dados.old.xlsx") == "Planilhas"


def test_decidir_sem_extensao():
    """Arquivo sem extensão deve retornar None."""
    assert regras.decidir("README") is None
    assert regras.decidir("Makefile") is None
    assert regras.decidir("arquivo_sem_extensao") is None


def test_decidir_com_path_object():
    """Decidir deve aceitar Path objects."""
    assert regras.decidir(Path("arquivo.pdf")) == "PDFs"
    assert regras.decidir(Path("/tmp/teste.txt")) == "Textos"


def test_todas_extensoes_mapeadas():
    """Verifica que todas as extensões do config estão funcionando."""
    from src.config import EXTENSAO_PARA_CATEGORIA

    for ext, categoria_esperada in EXTENSAO_PARA_CATEGORIA.items():
        assert regras.categoria_por_extensao(ext) == categoria_esperada
        assert regras.categoria_por_extensao(ext.upper()) == categoria_esperada


def test_decidir_none_vai_para_revisar():
    """Arquivos com categoria None devem ir para pasta Revisar (lógica no organizador)."""
    # Regras apenas retorna None, organizador decide enviar para Revisar
    assert regras.decidir("arquivo.unknown") is None
    assert regras.decidir("sem_extensao") is None
