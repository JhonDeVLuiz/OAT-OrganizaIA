# SPEC.md — OrganizaIA

## Visão geral
Organizador local de arquivos: observa `entrada/`, extrai texto, decide destino por
regras ou IA (Gemini), move para `organizados/` e registra tudo em SQLite.
Sem código neste arquivo — apenas o plano aprovado.

## Arquitetura (4 partes)
- **Algoritmo (Fase 2):** `src/monitor.py` (watchdog em `entrada/`) → `src/leitor.py`
  (pdf/docx/xlsx/txt) → `src/duplicatas.py` (hash) → `src/regras.py` (fallback
  determinístico) → `src/organizador.py` (move com `--dry-run` + desfazer) →
  `src/seguranca.py` (guards em todo passo). Entrypoint `main.py` nesta fase.
- **Banco (Fase 3):** `src/repositorio.py` (SQLite em `dados/`) integrado ao
  `organizador.py`, gravando movimentações e auditoria. Só metadados, nunca
  conteúdo de arquivo.
- **IA (Fase 4):** `src/classificador.py` (Gemini via `google-genai`), chamada só
  se `regras.py` não decidir.
- **Chat (Fase 5):** `src/chat.py` — function calling do Gemini com
  `listar_arquivos`, `buscar_historico`, `mover_arquivo`, `desfazer_ultima_acao`.

## Estrutura de pastas
- `main.py`, `SPEC.md`, `.env.example`, `requirements.txt`, `README.md`
- `src/{config,seguranca,monitor,leitor,regras,organizador,duplicatas,classificador,repositorio,chat}.py`
- `tests/test_{seguranca,organizador,repositorio,classificador}.py`,
  `tests/test_leitor.py`, `tests/test_duplicatas.py`
- `entrada/` (inbox), `organizados/Revisar/` (baixa confiança),
  `organizados/Duplicados/` (hash repetido), `dados/` (SQLite), `logs/` (JSON)

## Fase 2 — Algoritmo (+ monitor.py e main.py)
- `config.py`: paths (`entrada/`, `organizados/`, `dados/`, `logs/`), leitura do
  `.env` via `python-dotenv`, **lista fixa de categorias**.
- `seguranca.py`: lista de exclusão (`.env`, chaves, senhas, documentos pessoais —
  nunca lidos nem enviados); mascaramento de CPF, cartão e e-mail antes de enviar
  texto ao Gemini; validação de caminho com `Path.resolve()` confinado à raiz;
  tamanho máximo de arquivo de 20 MB (configurável em `config.py`), extensões
  permitidas, e leitura de apenas um trecho curto do texto.
- `monitor.py` + `main.py` nesta fase. `main.py`: `--once`, `--watch`,
  `--dry-run`, `--desfazer`, `--modo tipo|ia` (e `--chat` só na Fase 5).
- `organizador.py`: modos `--modo tipo` (só regras por extensão, padrão, nenhuma
  chamada à IA) e `--modo ia` (conteúdo via Gemini); `--dry-run` mostra o mesmo
  destino do real (mesmo caminho de classificação, cache por hash); log JSON em
  `logs/` com `{id, origem, destino, data}` (`id` único por execução); `--desfazer`
  desfaz a última execução inteira (todas as movimentações daquele `id`). A ferramenta `desfazer_ultima_acao` do chat
  desfaz só a última movimentação.
- `duplicatas.py` (antes do banco existir): compara o `hash` com os arquivos já em
  `organizados/` e com o log em `logs/`; na Fase 3 o `hash` UNIQUE do banco assume
  essa função.

## Fase 3 — Banco (integração repositorio ↔ organizador)
- Tabelas: `arquivos` (+ `classificacoes(categoria, confianca, data)` e
  `auditoria(acao, caminho, data)`).
- `arquivos.hash` UNIQUE; índices em `hash`, `destino` e `categoria`; modo WAL;
  inserção em lote; segunda execução com o mesmo `hash` não duplica registros.
- Consultas sempre parametrizadas (`?`). Só metadados, nunca conteúdo de arquivo.

## Fase 4 — IA
- Modo `tipo`: só regras por extensão, nenhuma chamada ao Gemini.
- Modo `ia`: nome + trecho mascarado ao Gemini; categorias de conteúdo em
  `config.py` (Faturas, Estudos, Trabalho, Pessoal, Outros); JSON validado
  `{categoria, confianca}`.
- Texto curto (< `MIN_CHARS_IA`): classifica só pelo nome, exige `>= 0.85`.
- `Revisar/`: abaixo do limiar, categoria fora da lista ou JSON inválido.
- IA indisponível (sem chave, 429, erro ou `MAX_CHAMADAS_IA`): regras por extensão
  + aviso na tela; `Revisar/` só se as regras também não decidirem.
- `MAX_CHAMADAS_IA` e `INTERVALO_IA_SEG` em `config.py`; cache por hash; sem
  reclassificar o mesmo hash.
- Testes com mock, sem chamar o Gemini (modo degradado só-regras sem chave/rede).

## Fase 5 — Chat
- Tools: `listar_arquivos`, `buscar_historico`, `ler_trecho`, `mover_arquivo`,
  `desfazer_ultima_acao` (+ flag `--chat` no `main.py`). Opcional: `sugerir_destino`.
- `ler_trecho`: só dentro de `entrada/` e `organizados/`; passa pela lista de
  exclusão e pelo limite de tamanho do `seguranca.py`; devolve no máximo 1500
  caracteres com CPF, cartão e e-mail mascarados.
- O texto lido é dado não confiável: instruções dentro dele nunca são obedecidas.
- No máximo 5 leituras por pergunta; auditoria registra só o nome do arquivo,
  nunca o conteúdo.
- Sempre confirmação antes de mover/apagar; caminho fora de `entrada/` ou
  `organizados/` é recusado (`Path.resolve()`).
- Nunca enviar `.env`, chaves, senhas ou conteúdo sensível à IA.

## Duplicatas
- `hash` repetido → `organizados/Duplicados/`.
- Nome já existente no destino ganha sufixo (`nome (1).ext`); nunca sobrescrever.

## Critérios de pronto
- **Fase 2:** `--dry-run` não move nada (só lista origem → destino); `--desfazer`
  restaura tudo ao estado anterior; teste com arquivos falsos passa.
- **Fase 3:** rodar duas vezes o mesmo lote não duplica registros (`hash` UNIQUE);
  `auditoria` contém uma linha por movimentação.
- **Fase 4:** `confianca < 0.7`, categoria inexistente ou JSON inválido →
  `organizados/Revisar/`; mesmo `hash` nunca chama o Gemini duas vezes; testes
  passam sem rede/chave (mock).
- **Fase 5:** `mover_arquivo` pede confirmação e sem ela nada muda; caminho fora
  de `entrada/`/`organizados/` é recusado; `desfazer_ultima_acao` reverte a última
  ação registrada.
