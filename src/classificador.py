"""Fase 4: Gemini so se as regras nao decidirem. Falha vira Revisar, nunca excecao."""
import json
import os

from dotenv import load_dotenv

from . import regras, repositorio, seguranca
from .config import CATEGORIAS, TRECHO_MAX_CHARS

LIMIAR_CONFIANCA = 0.7
MODELO_PADRAO = "gemini-3.5-flash"  # override via GEMINI_MODEL


def carregar_chave():
    """GEMINI_API_KEY via python-dotenv. None se ausente (modo so-regras)."""
    load_dotenv()
    return os.getenv("GEMINI_API_KEY") or None


def modelo():
    return os.getenv("GEMINI_MODEL") or MODELO_PADRAO


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


def _chamar_gemini(prompt, chave):
    from google import genai

    cliente = genai.Client(api_key=chave)
    resposta = cliente.models.generate_content(model=modelo(), contents=prompt)
    texto = getattr(resposta, "text", None) or str(resposta)
    return texto or ""


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


def classificar_ia(nome, trecho, categorias=None, chamar_ia=None):
    """So IA (regras decidem antes, no chamador). Retorna (categoria, confianca) ou None."""
    if seguranca.excluido(nome):
        return None
    chave = carregar_chave()
    if not chave and chamar_ia is None:
        return None  # sem chave: modo so-regras
    prompt = montar_prompt(nome, seguranca.mascarar_sensivel(trecho or ""))
    try:
        bruto = chamar_ia(prompt) if chamar_ia else _chamar_gemini(prompt, chave)
    except Exception:
        return None  # timeout, rede, cota: vira Revisar, nunca derruba
    return validar_resposta(extrair_json(bruto), categorias)


def categoria_registrada(banco, resumo):
    """Categoria ja classificada para o hash (para nao classificar duas vezes)."""
    historico = None
    try:
        historico = repositorio.historico_do_arquivo(banco, resumo)
    except Exception:
        return None
    if not historico or not historico["classificacoes"]:
        return None
    return historico["classificacoes"][-1]["categoria"]
