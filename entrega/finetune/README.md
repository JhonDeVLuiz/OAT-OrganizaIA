# Fine-tuning — experimento executado

## Feito

- **Dados preparados**: `preparar_dataset.py` gera `dataset.jsonl` com os 20
  documentos fictícios de `entrega/base-exemplo/`, no formato de chat
  (`system` + `user` + `assistant` JSON) — **14 treino / 6 validação**, rótulos
  manuais (Faturas, Estudos, Trabalho, Pessoal, Outros).
- **Experimento executado** (`executar_experimento.py`, 100% offline, sem
  chave/GPU): compara **baseline por regras** (palavras-chave do nome) vs
  **few-shot local** (vizinho mais próximo pelos 14 exemplos de treino) nos 6
  itens de validação. Métricas: acurácia, F1 macro e matriz de confusão.
- **Resultado** (`resultado_finetune.json`):
  - baseline: acurácia 0.50, F1 macro 0.30
  - few-shot local: acurácia 0.50, F1 macro 0.27
  - 6 predições de validação com acerto/erro por abordagem.

> Sem acesso ao modelo de base (gateway HTTP 401) e sem GPU local, não foi
> possível treinar LoRA/fine-tuning total nem medir o modelo base zero-shot. O
> experimento fica registrado com as duas abordagens executáveis offline; ao
> obter acesso ao modelo, repete-se o mesmo protocolo sobre `dataset.jsonl`.

