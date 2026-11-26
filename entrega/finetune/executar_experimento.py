r"""Executa o experimento de fine-tuning 100% offline (sem chave, sem GPU).

Carrega entrega/finetune/dataset.jsonl (14 treino / 6 validacao, rotulos
manuais de categoria de conteúdo) e compara duas abordagens nos 6 itens de
validacao:

1. Baseline - regras por extensao/nome (deterministico, palavras-chave).
2. Few-shot local - vizinho mais proximo pelos 14 exemplos de treino
   (sobreposicao de tokens entre nome+trecho; prediz o rotulo do melhor vizinho).

Métricas: acurácia, F1 macro e matriz de confusão.
Saída: entrega/finetune/resultado_finetune.json

Uso: .\.venv\Scripts\python.exe entrega\finetune\executar_experimento.py
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATASET = RAIZ / "entrega" / "finetune" / "dataset.jsonl"
SAIDA = RAIZ / "entrega" / "finetune" / "resultado_finetune.json"

CATEGORIAS = ["Faturas", "Estudos", "Trabalho", "Pessoal", "Outros"]

# --------------------------- 1) baseline (regras por nome) -------------------


def _palavras(texto):
    return set(re.findall(r"[a-zà-ú0-9]+", (texto or "").lower()))


def baseline_regras(nome):
    """Heuristica determinística por palavras-chave do nome do arquivo."""
    n = nome.lower()
    if any(k in n for k in ("fatura", "boleto", "nota fiscal", "recibo",
                            "holerite", "prestacao", "padaria", "agua",
                            "luz", "internet", "cartao")):
        return "Faturas"
    if any(k in n for k in ("estudo", "exercicio", "cronograma", "resumo",
                            "resenha", "plano", "aula", "apontamentos",
                            "sql", "tcc", "redes", "python", "curso")):
        return "Estudos"
    if any(k in n for k in ("contrato", "servicos", "aluguel", "trabalho")):
        return "Trabalho"
    if any(k in n for k in ("checklist", "mudanca", "roteiro", "viagem",
                            "compras", "carta", "pessoal")):
        return "Pessoal"
    return "Outros"


# --------------------------- 2) few-shot local (vizinho mais proximo) -------


def fewshot_local(item, treino):
    """Prediz rotulo do exemplo de treino mais parecido (overlap de tokens)."""
    alvo = _palavras(item["nome"] + " " + item["trecho"])
    melhor, melhor_score = None, -1
    for ex in treino:
        ex_palavras = _palavras(ex["nome"] + " " + ex["trecho"])
        inter = len(alvo & ex_palavras)
        uni = len(alvo | ex_palavras) or 1
        score = inter / uni  # Jaccard
        if score > melhor_score:
            melhor, melhor_score = ex["rotulo"], score
    return melhor


# ------------------------------- metricas ----------------------------------


def metricas(y_true, y_pred):
    labels = list(CATEGORIAS)
    matriz = {l: {c: 0 for c in labels} for l in labels}
    for t, p in zip(y_true, y_pred):
        matriz[t][p] = matriz.get(t, {}).get(p, 0) + 1

    precisao = {}
    recall = {}
    f1 = {}
    suporte = {}
    for l in labels:
        tp = matriz[l][l]
        fp = sum(matriz[o][l] for o in labels if o != l)
        fn = sum(matriz[l][o] for o in labels if o != l)
        suporte[l] = sum(matriz[l].values())
        precisao[l] = tp / (tp + fp) if (tp + fp) else 0.0
        recall[l] = tp / (tp + fn) if (tp + fn) else 0.0
        f1[l] = (2 * precisao[l] * recall[l] /
                 (precisao[l] + recall[l])) if (precisao[l] + recall[l]) else 0.0

    acuracia = sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
    f1_macro = sum(f1.values()) / len(labels)
    return {
        "acuracia": round(acuracia, 4),
        "f1_macro": round(f1_macro, 4),
        "por_categoria": {
            l: {"precisao": round(precisao[l], 4), "recall": round(recall[l], 4),
                "f1": round(f1[l], 4), "suporte": suporte[l]}
            for l in labels
        },
        "matriz_confusao": matriz,
    }


def _extrair_trecho(mensagem_usuario):
    """Pega o texto após 'Trecho do conteúdo: ' na mensagem de usuario."""
    conteudo = mensagem_usuario.get("content", "")
    idx = conteudo.lower().find("trecho")
    if idx == -1:
        return conteudo
    dois_pontos = conteudo.find(":", idx)
    if dois_pontos == -1:
        return conteudo[idx:]
    return conteudo[dois_pontos + 1:]


def main():
    exemplos = [json.loads(linha) for linha in DATASET.read_text(
        encoding="utf-8").splitlines() if linha.strip()]
    for e in exemplos:
        # nome e trecho ficam dentro da mensagem de usuario do formato chat
        user = next((m for m in e["messages"] if m.get("role") == "user"), {})
        e["nome"] = e.get("arquivo") or ""
        e["trecho"] = _extrair_trecho(user)

    treino = [e for e in exemplos if e["split"] == "treino"]
    validacao = [e for e in exemplos if e["split"] == "validacao"]

    itens = []
    y_true = []
    for e in validacao:
        item = {"nome": e["nome"], "trecho": e["trecho"]}
        itens.append(item)
        y_true.append(e["rotulo"])

    y_base = [baseline_regras(it["nome"]) for it in itens]
    y_few = [fewshot_local(it, treino) for it in itens]

    resultado = {
        "experimento": "fine-tuning classificacao de conteúdo (offline)",
        "dataset": {"treino": len(treino), "validacao": len(validacao),
                    "categorias": CATEGORIAS},
        "baseline_regras": metricas(y_true, y_base),
        "fewshot_local": metricas(y_true, y_few),
        "predicoes_validacao": [
            {"arquivo": it["nome"], "verdadeiro": vt,
             "baseline": vb, "fewshot": vf, "correto_base": vb == vt,
             "correto_fewshot": vf == vt}
            for it, vt, vb, vf in zip(itens, y_true, y_base, y_few)
        ],
    }
    SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    print(json.dumps({
        "baseline_acuracia": resultado["baseline_regras"]["acuracia"],
        "baseline_f1_macro": resultado["baseline_regras"]["f1_macro"],
        "fewshot_acuracia": resultado["fewshot_local"]["acuracia"],
        "fewshot_f1_macro": resultado["fewshot_local"]["f1_macro"],
    }, ensure_ascii=False, indent=2))
    print("salvo em", SAIDA)


if __name__ == "__main__":
    main()
