"""Fase 2: pastas, limites, categorias fixas e mapa extensao -> categoria."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ENTRADA_DIR = BASE_DIR / "entrada"
ORGANIZADOS_DIR = BASE_DIR / "organizados"
REVISAR_DIR = ORGANIZADOS_DIR / "Revisar"
DUPLICADOS_DIR = ORGANIZADOS_DIR / "Duplicados"
DADOS_DIR = BASE_DIR / "dados"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = DADOS_DIR / "organizaia.db"

MAX_TAMANHO_BYTES = 20 * 1024 * 1024
TRECHO_MAX_CHARS = 2000
MIN_CHARS_IA = 20

CATEGORIAS = ["Documentos", "Planilhas", "PDFs", "Textos"]

CATEGORIAS_CONTEUDO = ["Faturas", "Estudos", "Trabalho", "Pessoal", "Outros"]

MAX_CHAMADAS_IA = 15
INTERVALO_IA_SEG = 7.0

EXTENSAO_PARA_CATEGORIA = {
    ".pdf": "PDFs",
    ".doc": "Documentos",
    ".docx": "Documentos",
    ".odt": "Documentos",
    ".xls": "Planilhas",
    ".xlsx": "Planilhas",
    ".csv": "Planilhas",
    ".ods": "Planilhas",
    ".txt": "Textos",
    ".md": "Textos",
}

EXTENSOES_PERMITIDAS = frozenset(EXTENSAO_PARA_CATEGORIA)
