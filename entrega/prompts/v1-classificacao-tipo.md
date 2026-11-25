# Prompt v1 — classificação por tipo (legado)

Origem: `src/classificador.py::montar_prompt` (mantido para compatibilidade).
Categorias: `Documentos, Planilhas, PDFs, Textos` (lista `CATEGORIAS`).

```text
Classifique o arquivo abaixo em UMA destas categorias: {categorias}.
Responda SOMENTE com JSON, sem markdown, nesse formato exato:
{"categoria": "<uma das categorias>", "confianca": <0 a 1>}
Nome do arquivo: {nome}
Trecho do conteudo: {trecho[:TRECHO_MAX_CHARS]}
```

Limitações observadas:

- A categoria é **de formato** (PDFs, Planilhas), não de assunto.
- Texto curto/vazio ainda pede classificação por conteúdo — o modelo tende a
  "inventar" segurança e devolver confiança alta sem base.
- Não havia instrução explícita sobre texto não confiável nem sobre categoria
  fechada; a validação era só posterior, em `validar_resposta`.
