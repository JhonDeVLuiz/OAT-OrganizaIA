"""Fase 2: pastas, limites, categorias fixas e mapa extensao -> categoria."""
import os
from pathlib import Path

from dotenv import load_dotenv

# .env primeiro, para que IA_BASE_URL/IA_MODELOS sejam lidos aqui embaixo.
load_dotenv()

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
INTERVALO_IA_SEG = 5.0

LEITURA_COMPLETA_MAX_CHARS = 8000

# Chat: rotação rápida (1 tentativa por modelo, timeout curto).
CHAT_TIMEOUT_SEG = 10.0
CHAT_ESPERA_MODELOS = 4.0

# IA: endpoint no formato Anthropic (/v1/messages). Padrao: GLM (z.ai) gratuito.
# Via .env aponta para Claude: IA_BASE_URL oficial https://api.anthropic.com
# ou um gateway ex.: https://gpt.teamsoclo.site ; IA_MODELOS=nome1,nome2 (rotatividade).
IA_BASE_URL = os.getenv("IA_BASE_URL") or "https://api.z.ai/api/anthropic"

def _modelos_da_ia():
    """IA_MODELOS do .env (separada por virgula) ou os Flash do GLM gratuito."""
    bruto = os.getenv("IA_MODELOS")
    if bruto:
        nomes = [n.strip() for n in bruto.split(",") if n.strip()]
        if nomes:
            return nomes
    return ["glm-4.7-flash", "glm-4.5-flash"]

IA_MODELOS = _modelos_da_ia()
GLM_TIMEOUT_SEG = 45.0
GLM_ESPERA_MODELOS = 1.0

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
