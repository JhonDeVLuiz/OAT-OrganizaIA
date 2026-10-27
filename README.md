# OrganizaIA

Organizador de arquivos **local** com classificação por IA (GLM Flash, gratuito)
e banco de dados com histórico/auditoria — trabalho final de
**Projeto de IA** + **Segurança e Otimização de BD**.

## O que é

Provo que dá para automatizar a pasta bagunçada: `.pdf .docx .xlsx .csv .txt .md .odt`
soltos em `entrada/` são observados em tempo real, têm o texto extraído
(somente um trecho curto), deduplicados por sha256, classificados
(regras por extensão ou IA) e movidos para `organizados/<Categoria>/<Subcategoria>/`
— **sem nada sair da máquina e sem sobrescrever** (sufixo ` (1).ext`).
Dúvida de baixa confiança → `organizados/Revisar/`; hash repetido → `Duplicados/`.
Todo movimento vai para logs JSON + SQLite, com `--desfazer` para restaurar.

**Trava de segurança:** `.env`, chaves, senhas e documentos pessoais **nunca são
lidos nem enviados à IA**; CPF/cartão/e-mail são mascarados; SQL sempre parametrizado.

## Como rodar

```powershell
# 1) varre entrada/ uma vez (modo tipo — só regras, zero rede)
.\.venv\Scripts\python.exe main.py --once

# 2) varre uma vez decidindo conteúdo com IA (GLM, z.ai; precisa da .env)
.\.venv\Scripts\python.exe main.py --modo ia --once

# 3) modo demonstração sem mover nada
.\.venv\Scripts\python.exe main.py --once --dry-run

# 4) observe em tempo real
.\.venv\Scripts\python.exe main.py --watch

# 5) chat com o organizador (11 tools, confirmação em toda ação)
.\.venv\Scripts\python.exe main.py --chat

# extras: --desfazer  --exportar backup.zip  --importar backup.zip
```

## Pilha

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.13 (venv local) |
| Watch | `watchdog` observando `entrada/` |
| Leitura | `pypdf`, `python-docx`, `openpyxl`, `.txt` |
| Banco | SQLite (modo WAL) em `dados/organizaia.db` — 3 tabelas, SQL paramétrico |
| IA | GLM `glm-4.7-flash`/`glm-4.5-flash` via `https://api.z.ai/api/anthropic` (formato Anthropic), **grátis**; modo tipo roda sem rede |
| Chat | CLI com function calling por texto — 11 tools |
| Testes | `pytest` — **96+ testes** (injection, path traversal, SQL, mascaramento) |
| Backup | `.zip` do banco + manifest (`--exportar/--importar`) |
| Painel | `painel.py` (tkinter) com barra de progresso (opcional) |

## Estrutura

```
entrada/      caixa de entrada (obs. watchdog)
organizados/  saída organizada (+Revisar/ +Duplicados/)
dados/        banco SQLite (gitignored)
logs/         logs JSON por execução (gitignored)
src/          monitor, seguranca, leitor, duplicatas, regras,
              classificador, organizador, repositorio, chat
tests/        96+ pytest
```

> Documentos do trabalho (canvas, partes, scripts, base fictícia, PDF) em `entrega/`.
> **Nenhuma chave de API está versionada.** Configure `GLM_API_KEY` em `.env`
> (veja `.env.example`) — sem a chave, o projeto roda em modo `--modo tipo` apenas.
