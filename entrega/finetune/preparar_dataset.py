"""Prepara o dataset de fine-tuning a partir de entrega/base-exemplo/.

Cada exemplo = nome do arquivo + primeiro trecho (500 chars) -> categoria de
assunto. Rotulos atribuidos manualmente (20 documentos ficticios).
Treino NAO executado: ver entrega/finetune/README.md.

Uso: .\\.venv\\Scripts\\python.exe entrega\\finetune\\preparar_dataset.py
Saida: entrega/finetune/dataset.jsonl (14 treino / 6 validacao)
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "entrega" / "base-exemplo"
SAIDA = Path(__file__).resolve().parent / "dataset.jsonl"

ROTULOS = {
    "apontamentos-python-aula5.txt": "Estudos",
    "boleto_escola_exemplo.txt": "Faturas",
    "carta_banco_exemplo.txt": "Faturas",
    "checklist-mudanca-apartamento.txt": "Pessoal",
    "contrato-prestacao-servicos.txt": "Trabalho",
    "contrato_aluguel_2025.txt": "Pessoal",
    "cronograma-tcc-redes.txt": "Estudos",
    "exercicios_sql_basico.txt": "Estudos",
    "fatura-agua-2026-02.txt": "Faturas",
    "fatura-internet-2026-01.txt": "Faturas",
    "fatura-luz-2026-03.txt": "Faturas",
    "holerite_exemplo_ana.txt": "Trabalho",
    "lista_compras.txt": "Pessoal",
    "nota_fiscal_padaria.txt": "Faturas",
    "plano_estudos_eng.txt": "Estudos",
    "receita-bolo-cenoura.txt": "Outros",
    "recibo-pintura-apartamento.txt": "Faturas",
    "resenha-livro-sapiens.txt": "Estudos",
    "resumo_curso_sql.txt": "Estudos",
    "roteiro-viagem-ferias.txt": "Pessoal",
}

SISTEMA = (
    "Classifique o arquivo em UMA destas categorias: "
    "Faturas, Estudos, Trabalho, Pessoal, Outros. "
    'Responda SOMENTE com JSON: {"categoria": "...", "confianca": 0.0-1.0}'
)


def main():
    arquivos = sorted(p for p in BASE.glob("*.txt") if p.name in ROTULOS)
    exemplos = []
    for i, caminho in enumerate(arquivos):
        texto = caminho.read_text(encoding="utf-8", errors="replace")[:500]
        exemplos.append({
            "split": "validacao" if i % 3 == 2 else "treino",
            "messages": [
                {"role": "system", "content": SISTEMA},
                {"role": "user", "content":
                    f"Nome do arquivo: {caminho.name}\nTrecho do conteudo: {texto}"},
                {"role": "assistant", "content": json.dumps(
                    {"categoria": ROTULOS[caminho.name], "confianca": 0.9},
                    ensure_ascii=False)},
            ],
            "rotulo": ROTULOS[caminho.name],
            "arquivo": caminho.name,
        })
    SAIDA.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in exemplos) + "\n",
        encoding="utf-8")
    treino = sum(1 for e in exemplos if e["split"] == "treino")
    print(f"{len(exemplos)} exemplos: {treino} treino / {len(exemplos) - treino} validacao")
    print("salvo em", SAIDA)


if __name__ == "__main__":
    main()
