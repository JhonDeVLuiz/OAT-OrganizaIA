# Prompt v2 — classificação por conteúdo (atual)

Origem: `src/classificador.py::montar_prompt_conteudo` (versão em uso em 16/11/2026).
Categorias: `Faturas, Estudos, Trabalho, Pessoal, Outros` (`CATEGORIAS_CONTEUDO`).

```text
Classifique o arquivo abaixo em UMA destas categorias de conteudo: {categorias}.
{instrucao}
Responda SOMENTE com JSON, sem markdown, nesse formato exato:
{"categoria": "<uma das categorias>", "confianca": <0 a 1>}
Nome do arquivo: {nome}
Trecho do conteudo: {trecho[:TRECHO_MAX_CHARS]}
```

`instrucao` assume um de dois valores conforme o tamanho do texto:

- normal: `Classifique pelo nome e pelo trecho do conteudo.`
- curto (< `MIN_CHARS_IA` = 20 chars): `Classifique SOMENTE pelo nome do arquivo (sem conteudo confiavel).`

## O que mudou em relação à v1

1. **Categoria de assunto** (Faturas/Estudos/Trabalho/Pessoal/Outros) em vez de
   categoria de formato — a pasta `<Categoria>/` passa a refletir o conteúdo.
2. **Regra para texto curto**: abaixo de 20 caracteres o modelo classifica só
   pelo nome e o limiar sobe de 0,70 para **0,85** (`LIMIAR_NOME`).
3. **Lista fechada validada no código** (`validar_resposta`/`classificar_conteudo`):
   categoria fora da lista ou confiança abaixo do limiar → `organizados/Revisar/`.
4. **Mascaramento antes do prompt**: `seguranca.mascarar_sensivel()` substitui
   CPF/cartão/e-mail por `[CPF]`, `[CARTAO]`, `[EMAIL]` antes de montar o texto
   (o conteúdo do arquivo é dado não confiável e nunca comando).
5. **Fallback explícito**: sem chave, HTTP 401/403, timeout ou JSON inválido, o
   classificador devolve `None` (motivo `sem-chave`/`falha`/`rejeitado`) e o
   organizador cai nas regras por extensão — nunca levanta exceção.
