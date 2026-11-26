"""Gerador de resposta 100% local (sem chave de API, sem rede).

Substitui a geracao por LLM externo quando o gateway esta indisponível
(HTTP 401) ou quando não há chave configurada. Recebe os trechos
recuperados pelo RAG (arquivo, hash, texto ja mascarado) e devolve uma
resposta em portugues do Brasil citando as fontes pelo hash SHA-256 de
cada arquivo. Nada sai da máquina e nenhuma chave é necessária.
"""

from typing import Dict, List

FONTE_TRECHO_MAX = 220  # caracteres de cada trecho citado na resposta
MAX_FONTES = 5


def _limpar(texto: str) -> str:
    texto = (texto or "").replace("\n", " ").strip()
    return " ".join(texto.split())


def gerar_resposta(pergunta: str, trechos: List[Dict]) -> Dict:
    """Gera uma resposta com fontes a partir de trechos RAG.

    `trechos`: lista de dict {arquivo, hash, texto}. Retorna
    {resposta, fontes: [{arquivo, hash}], geracao: "local"}.
    Quando não há trechos relevantes, informa que não encontrou e não
    inventa fontes.
    """
    pergunta = (pergunta or "").strip()
    trechos = [t for t in (trechos or []) if t]
    if not trechos:
        return {
            "resposta": (
                "Não encontrei registros relevantes nos arquivos organizados. "
                "Tente reformular a pergunta (nome do arquivo ou palavra do conteúdo)."
            ),
            "fontes": [],
            "geracao": "local",
        }

    partes: List[str] = []
    fontes: List[Dict] = []
    for t in trechos[:MAX_FONTES]:
        arquivo = t.get("arquivo") or "arquivo"
        hash_completo = t.get("hash") or ""
        hash_curto = hash_completo[:16]
        trecho = _limpar(t.get("texto") or "")[:FONTE_TRECHO_MAX]
        partes.append(f"[{len(partes)+1}] {arquivo} (hash {hash_curto}...): {trecho}")
        fontes.append({"arquivo": arquivo, "hash": hash_completo})

    corpo = "\n".join(partes)
    resposta = (
        "Com base nos trechos localizados nos arquivos organizados:\n"
        f"{corpo}\n"
        "Os hashes acima (SHA-256) identificam unicamente cada arquivo e servem "
        "como fonte da resposta."
    )
    return {"resposta": resposta, "fontes": fontes, "geracao": "local"}
