# Fine-tuning — status em 16/11/2026

## Feito

- **Dados preparados**: `preparar_dataset.py` gera `dataset.jsonl` com os 20
  documentos fictícios de `entrega/base-exemplo/`, no formato de chat
  (`system` + `user` + `assistant` JSON) — **14 treino / 6 validação**, rótulos
  manuais (Faturas, Estudos, Trabalho, Pessoal, Outros).
- **Métrica definida**: acurácia e F1 macro nos 6 itens de validação + matriz de
  confusão; baseline = regras por extensão (determinístico, roda offline).
- **Estratégia escolhida**: LoRA (ou few-shot com os 14 exemplos) antes de
  fine-tuning total, porque o volume é pequeno e o modelo é gratuito.

## Não feito (bloqueio)

- **Treino não executado**. Bloqueios reais em 16/11/2026:
  1. O gateway de IA configurado (`gpt.teamsoclo.site`) respondeu
     **HTTP 401 Unauthorized** na sonda `entrega/evidencias/probe_ia.py`.
  2. Não há GPU local nem credencial de outro provedor no `.env`
     (apenas `GLM_API_KEY`).
- **Primeira medição contra o modelo base**: pendente pela mesma causa (sem
  modelo acessível). O baseline por regras pode ser medido hoje e está no
  relatório; falta o número do modelo base.

## Próximo passo (quando a chave voltar)

1. Rodar o modelo base zero-shot nos 6 itens de validação e anotar acurácia/F1.
2. Rodar few-shot com os 14 exemplos de treino e comparar.
3. Só então avaliar LoRA (ex.: PEFT em um modelo aberto pequeno) com o mesmo
   conjunto — e registrar a matriz de confusão no relatório.
