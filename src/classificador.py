"""Fase 4: Gemini so se as regras nao decidirem. Falha vira Revisar, nunca excecao."""
import json
import os
import time

from dotenv import load_dotenv

from . import regras, repositorio, seguranca
from .config import CATEGORIAS, CATEGORIAS_CONTEUDO, MIN_CHARS_IA, TRECHO_MAX_CHARS

LIMIAR_CONFIANCA = 0.7
LIMIAR_NOME = 0.85
MODELO_PADRAO = "gemini-flash-latest"  # override via GEMINI_MODEL
MODELOS_FALLBACK = ["gemini-flash-latest", "gemini-3.5-flash", "gemini-3.6-flash"]
TENTATIVAS_IA = 3


class SemChave(RuntimeError):
    """GEMINI_API_KEY ausente (modo so-regras / chat indisponivel)."""


_TRANSITORIO_TIPOS = {
    "ServerError", "TimeoutError", "Timeout", "ResourceExhausted", "ServiceUnavailable",
}
_TRANSITORIO_TEXTO = (
    "503", "429", "unavailable", "resource_exhausted", "timeout", "timed out", "temporar",
)


def _eh_transitorio(exc):
    if type(exc).__name__ in _TRANSITORIO_TIPOS:
        return True
    msg = str(exc).lower()
    return any(parte in msg for parte in _TRANSITORIO_TEXTO)


def chamar_com_retry(func, tentativas=TENTATIVAS_IA, esperar=time.sleep):
    """Tenta ate `tentativas` vezes com backoff curto; so repete erro transitorio."""
    ultimo = None
    for n in range(tentativas):
        try:
            return func()
        except Exception as exc:
            ultimo = exc
            if not _eh_transitorio(exc) or n == tentativas - 1:
                raise
            esperar(2 ** n)
    raise ultimo


def carregar_chave():
    """GEMINI_API_KEY via python-dotenv. None se ausente (modo so-regras)."""
    load_dotenv()
    return os.getenv("GEMINI_API_KEY") or None


def modelo():
    return modelos()[0]


def modelos():
    """GEMINI_MODEL sozinho ou a lista de rotatividade (fallback)."""
    unico = os.getenv("GEMINI_MODEL")
    if unico:
        return [unico]
    return list(MODELOS_FALLBACK)


def montar_prompt(nome, trecho):
    categorias = ", ".join(CATEGORIAS)
    return (
        "Classifique o arquivo abaixo em UMA destas categorias: "
        f"{categorias}.\n"
        "Responda SOMENTE com JSON, sem markdown, nesse formato exato:\n"
        '{"categoria": "<uma das categorias>", "confianca": <0 a 1>}\n'
        f"Nome do arquivo: {nome}\n"
        f"Trecho do conteudo: {(trecho or '')[:TRECHO_MAX_CHARS]}"
    )


def _chamar_gemini(prompt, chave, esperar=time.sleep):
    from google import genai

    cliente = genai.Client(api_key=chave)
    ultimo = None
    for nome in modelos():
        def _pedir(_nome=nome):
            resposta = cliente.models.generate_content(model=_nome, contents=prompt)
            texto = getattr(resposta, "text", None) or str(resposta)
            return texto or ""

        try:
            return chamar_com_retry(_pedir, esperar=esperar)
        except Exception as exc:
            ultimo = exc
            if _eh_transitorio(exc) or "404" in str(exc) or "NOT_FOUND" in str(exc):
                continue  # proximo modelo da rotatividade
            raise
    raise ultimo


def extrair_json(texto):
    """Aceita JSON puro ou cercado de ```json. None se invalido ou sem os campos."""
    bruto = (texto or "").strip()
    if bruto.startswith("```"):
        bruto = bruto.strip("`").strip()
        if bruto.lower().startswith("json"):
            bruto = bruto[4:].strip()
    try:
        dados = json.loads(bruto)
    except (ValueError, TypeError):
        return None
    if not isinstance(dados, dict):
        return None
    categoria, confianca = dados.get("categoria"), dados.get("confianca")
    if not isinstance(categoria, str) or isinstance(confianca, bool):
        return None
    if not isinstance(confianca, (int, float)):
        return None
    return {"categoria": categoria.strip(), "confianca": float(confianca)}


def validar_resposta(dados, categorias=None):
    """(categoria, confianca) se valida e >= limiar; senao None (= Revisar/)."""
    if not dados:
        return None
    categorias = list(categorias or CATEGORIAS)
    categoria, confianca = dados.get("categoria"), dados.get("confianca")
    if categoria not in categorias:
        return None
    if not (0 <= confianca <= 1) or confianca < LIMIAR_CONFIANCA:
        return None
    return categoria, confianca


def classificar_ia(nome, trecho, categorias=None, chamar_ia=None, detalhe=None):
    """So IA (regras decidem antes, no chamador). Retorna (categoria, confianca) ou None.

    Se `detalhe` (dict) for passado, recebe `detalhe["motivo"]`: ok, sem-chave,
    falha ou rejeitado.
    """
    def _motivo(valor):
        if detalhe is not None:
            detalhe["motivo"] = valor

    if seguranca.excluido(nome):
        _motivo("rejeitado")
        return None
    chave = carregar_chave()
    if not chave and chamar_ia is None:
        _motivo("sem-chave")  # sem chave: modo so-regras
        return None
    prompt = montar_prompt(nome, seguranca.mascarar_sensivel(trecho or ""))
    try:
        bruto = chamar_ia(prompt) if chamar_ia else _chamar_gemini(prompt, chave)
    except Exception:
        _motivo("falha")  # timeout, rede, cota: vira Revisar, nunca derruba
        return None
    valido = validar_resposta(extrair_json(bruto), categorias)
    _motivo("ok" if valido else "rejeitado")
    return valido


def montar_prompt_conteudo(nome, trecho, categorias, so_nome=False):
    categorias = ", ".join(categorias)
    instrucao = ("Classifique SOMENTE pelo nome do arquivo (sem conteudo confiavel)."
                 if so_nome else "Classifique pelo nome e pelo trecho do conteudo.")
    return (
        "Classifique o arquivo abaixo em UMA destas categorias de conteudo: "
        f"{categorias}.\n"
        f"{instrucao}\n"
        "Responda SOMENTE com JSON, sem markdown, nesse formato exato:\n"
        '{"categoria": "<uma das categorias>", "confianca": <0 a 1>}\n'
        f"Nome do arquivo: {nome}\n"
        f"Trecho do conteudo: {(trecho or '')[:TRECHO_MAX_CHARS]}"
    )


def classificar_conteudo(nome, trecho, categorias=None, chamar_ia=None, detalhe=None):
    """Modo ia: por conteudo (limiar 0.7); texto curto classifica so pelo nome (>= 0.85)."""
    def _motivo(valor):
        if detalhe is not None:
            detalhe["motivo"] = valor

    cats = list(categorias or CATEGORIAS_CONTEUDO)
    if seguranca.excluido(nome):
        _motivo("rejeitado")
        return None
    chave = carregar_chave()
    if not chave and chamar_ia is None:
        _motivo("sem-chave")
        return None
    curto = len((trecho or "").strip()) < MIN_CHARS_IA
    prompt = montar_prompt_conteudo(
        nome, seguranca.mascarar_sensivel(trecho or ""), cats, so_nome=curto)
    try:
        bruto = chamar_ia(prompt) if chamar_ia else _chamar_gemini(prompt, chave)
    except Exception:
        _motivo("falha")
        return None
    dados = extrair_json(bruto)
    if not dados or dados.get("categoria") not in cats:
        _motivo("rejeitado")
        return None
    confianca = dados.get("confianca")
    if not isinstance(confianca, (int, float)) or isinstance(confianca, bool):
        _motivo("rejeitado")
        return None
    limiar = LIMIAR_NOME if curto else LIMIAR_CONFIANCA
    if not (0 <= confianca <= 1) or confianca < limiar:
        _motivo("rejeitado")
        return None
    _motivo("ok")
    return dados["categoria"], float(confianca)


def categoria_registrada(banco, resumo):
    """Categoria ja classificada para o hash (para nao classificar duas vezes)."""
    from pathlib import Path

    from .config import DB_PATH

    if not Path(banco or DB_PATH).is_file():
        return None  # sem banco: nao cria arquivo so para consultar
    historico = None
    try:
        historico = repositorio.historico_do_arquivo(banco, resumo)
    except Exception:
        return None
    if not historico or not historico["classificacoes"]:
        return None
    return historico["classificacoes"][-1]["categoria"]
