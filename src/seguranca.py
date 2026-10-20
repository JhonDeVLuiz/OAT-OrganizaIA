"""Fase 2: guards de caminho, exclusao, tamanho, extensao e mascaramento."""
import re
from pathlib import Path

from .config import EXTENSOES_PERMITIDAS, MAX_TAMANHO_BYTES

NOMES_EXCLUIDOS = (".env",)

PALAVRAS_EXCLUIDAS = (
    "chave",
    "chaves",
    "senha",
    "senhas",
    "password",
    "secret",
    "token",
    "documento",
    "documentos",
    "pessoal",
    "pessoais",
)

_CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_CARTAO_RE = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")

_CARACTERES_RUIDOSOS = '<>:"/\\|?*'


def dentro_da_raiz(caminho, raiz):
    try:
        Path(caminho).resolve().is_relative_to(Path(raiz).resolve())
        return True
    except (OSError, ValueError):
        return False


def resolver_confinado(caminho, raiz):
    """Resolve e garante que `caminho` esta dentro de `raiz`. Rejeita links."""
    p = Path(caminho)
    if p.is_symlink():
        raise ValueError(f"link rejeitado: {p.name}")
    resolvido = p.resolve()
    base = Path(raiz).resolve()
    try:
        resolvido.relative_to(base)
    except ValueError:
        raise ValueError(f"caminho fora da pasta permitida: {p.name}")
    return resolvido


def confinar_em(caminho, raizes):
    """Resolve e garante que `caminho` esta dentro de uma das `raizes`."""
    ultimo_erro = None
    for raiz in raizes:
        try:
            return resolver_confinado(caminho, raiz)
        except ValueError as exc:
            ultimo_erro = exc
    raise ValueError(f"caminho fora das pastas permitidas: {Path(caminho).name}") from ultimo_erro


def nome_seguro(nome):
    """Reduz a basename e remove caracteres perigosos. Nunca retorna caminho."""
    base = str(nome).replace("\\", "/").split("/")[-1].strip()
    for ch in _CARACTERES_RUIDOSOS:
        base = base.replace(ch, "_")
    base = base.rstrip(" .")
    if base in ("", ".", ".."):
        raise ValueError(f"nome invalido: {nome!r}")
    return base


def excluido(nome):
    """Lista de exclusao: .env, chaves, senhas, documentos pessoais."""
    base = str(nome).strip().lower()
    if base in NOMES_EXCLUIDOS:
        return True
    return any(palavra in base for palavra in PALAVRAS_EXCLUIDAS)


def extensao_permitida(ext):
    return str(ext).lower() in EXTENSOES_PERMITIDAS


def validar_arquivo(caminho, raiz, max_bytes=MAX_TAMANHO_BYTES):
    """Retorna (ok, motivo). Motivos: ok, ausente, fora-da-raiz, link, excluido, grande."""
    p = Path(caminho)
    if not p.is_file():
        return False, "ausente"
    try:
        resolver_confinado(p, raiz)
    except ValueError as exc:
        return False, "link" if "link" in str(exc) else "fora-da-raiz"
    if excluido(p.name):
        return False, "excluido"
    try:
        if p.stat().st_size > max_bytes:
            return False, "grande"
    except OSError:
        return False, "ausente"
    return True, "ok"


def mascarar_sensivel(texto):
    """Mascaramento para uso na Fase 4, antes de enviar texto à IA."""
    texto = _EMAIL_RE.sub("[EMAIL]", texto or "")
    texto = _CPF_RE.sub("[CPF]", texto)
    return _CARTAO_RE.sub("[CARTAO]", texto)
