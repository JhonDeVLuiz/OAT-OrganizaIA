"""Fase 2: pastas, limites, categorias fixas e mapa extensao -> categoria."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Congelado (PyInstaller): dados ficam ao lado do .exe, nunca em _MEIPASS nem no cwd.
BASE_DIR = (Path(sys.executable).resolve().parent
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent.parent)

# .env primeiro (da pasta do programa, nao do cwd), para IA_BASE_URL/IA_MODELOS.
load_dotenv(BASE_DIR / ".env")

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
# 30s: gateway medido em 5-9s mesmo para pings; 10s do colega estourava -> "API ocupada".
CHAT_TIMEOUT_SEG = 30.0
CHAT_ESPERA_MODELOS = 4.0
# Estilo da resposta: temperatura baixa corta divagacao; teto de tokens encurta.
# 900 ainda cabe um criar_arquivo (.txt/.md) de tamanho normal em JSON.
CHAT_TEMPERATURE = 0.2
CHAT_MAX_TOKENS = 900

# IA: endpoint no formato Anthropic (/v1/messages). Padrao: GLM (z.ai) gratuito.
# Via .env aponta para Claude: IA_BASE_URL oficial https://api.anthropic.com
# ou um gateway ex.: https://gpt.teamsoclo.site ; IA_MODELOS=nome1,nome2 (rotatividade).
# Seguranca: so https (a chave nunca pode trafegar em claro) e host avisado.
_IA_BASE_URL_PADRAO = "https://api.z.ai/api/anthropic"
_HOSTS_IA_CONHECIDOS = ("api.z.ai", "api.anthropic.com", "gpt.teamsoclo.site")

def _base_url_ia():
    url = (os.getenv("IA_BASE_URL") or _IA_BASE_URL_PADRAO).strip()
    if not url.lower().startswith("https://"):
        raise ValueError(
            f"IA_BASE_URL invalida ({url!r}): use https:// para a chave nao "
            "trafegar em claro")
    host = url.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0].lower()
    if host not in _HOSTS_IA_CONHECIDOS:
        import sys
        print(f"[aviso] IA_BASE_URL aponta para host nao habitual ({host}): "
              "a chave e o texto do prompt sao enviados a esse servidor",
              file=sys.stderr)
    return url

IA_BASE_URL = _base_url_ia()

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
