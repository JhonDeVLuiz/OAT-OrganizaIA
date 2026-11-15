# Guia de Testes - OrganizaIA

## 📦 Instalação de Dependências

Antes de rodar os testes, instale o pytest:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest pytest-cov
```

## 🧪 Rodando os Testes

### Rodar todos os testes
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Rodar testes de um módulo específico
```powershell
# Testes de segurança
.\.venv\Scripts\python.exe -m pytest tests/test_seguranca.py -v

# Testes de monitor
.\.venv\Scripts\python.exe -m pytest tests/test_monitor.py -v

# Testes E2E
.\.venv\Scripts\python.exe -m pytest tests/test_integracao_e2e.py -v
```

### Rodar com cobertura de código
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ --cov=src --cov-report=html --cov-report=term
```

Após rodar, abra `htmlcov/index.html` no navegador para ver o relatório visual.

### Rodar apenas testes rápidos (pular performance)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v -m "not slow"
```

### Rodar em modo verboso com detalhes
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -vv --tb=long
```

## 📊 Interpretando Resultados

### Saída de sucesso
```
tests/test_monitor.py::test_deve_ignorar_arquivos_temporarios PASSED
tests/test_monitor.py::test_arquivo_estavel_retorna_true_quando_parou_de_crescer PASSED
...
==================== 15 passed in 2.34s ====================
```

### Saída com falha
```
tests/test_monitor.py::test_handler_processa_arquivo_valido FAILED
...
FAILED tests/test_monitor.py::test_handler_processa_arquivo_valido - AssertionError: ...
```

## 🎯 Cobertura Esperada

Meta de cobertura por módulo:

| Módulo | Meta | Status Atual |
|--------|------|--------------|
| `seguranca.py` | 95%+ | ✅ Completo |
| `organizador.py` | 90%+ | ✅ Completo |
| `classificador.py` | 85%+ | ✅ Completo |
| `monitor.py` | 90%+ | ✅ Completo |
| `repositorio.py` | 85%+ | ✅ Completo |
| `backup.py` | 80%+ | ✅ Completo |
| `chat.py` | 80%+ | ✅ Completo |
| `leitor.py` | 75%+ | ✅ Completo |
| `duplicatas.py` | 90%+ | ✅ Completo |
| `regras.py` | 100% | ✅ Completo |

## 🔧 Adicionando Novos Testes

### 1. Copie os arquivos de teste para a pasta `tests/`

Os arquivos de teste disponíveis:
- `test_monitor.py` - Testes do watchdog
- `test_integracao_e2e.py` - Testes de fluxo completo
- `test_regras.py` - Testes de classificação por extensão
- `test_performance.py` - Testes de desempenho
- `test_seguranca_expandido.py` - Testes adicionais de segurança

### 2. Estrutura de um teste

```python
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import modulo_a_testar


def test_comportamento_esperado():
    """Docstring explicando o que o teste valida."""
    # Arrange - preparar dados
    entrada = "valor_teste"
    
    # Act - executar ação
    resultado = modulo_a_testar.funcao(entrada)
    
    # Assert - verificar resultado
    assert resultado == "esperado"
```

### 3. Usando fixtures do pytest

```python
@pytest.fixture
def pasta_temporaria(tmp_path):
    """Cria estrutura de pastas para teste."""
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    return entrada


def test_com_fixture(pasta_temporaria):
    arquivo = pasta_temporaria / "teste.txt"
    arquivo.write_text("conteudo")
    assert arquivo.exists()
```

## 🚨 Debugging de Testes

### Ver output completo (print statements)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_monitor.py -v -s
```

### Parar no primeiro erro
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -x
```

### Modo interativo (pdb)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ --pdb
```

### Ver variáveis locais em falhas
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -l
```

## ✅ Checklist antes de Commit

- [ ] Todos os testes passam
- [ ] Cobertura >= 85%
- [ ] Nenhum teste marcado como `skip` sem justificativa
- [ ] Docstrings claras em todos os testes novos
- [ ] Testes de segurança para código que manipula entrada do usuário
- [ ] Testes de edge cases (valores vazios, None, limites)

## 🔄 Integração Contínua

O GitHub Actions roda automaticamente:
- Todos os testes em cada push
- Verifica cobertura mínima de 80%
- Gera relatório de cobertura
- Falha o build se algum teste falhar

Ver arquivo `.github/workflows/tests.yml` para configuração.

## 📚 Recursos Adicionais

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## 🐛 Problemas Comuns

### ImportError ao rodar testes
**Problema:** `ModuleNotFoundError: No module named 'src'`

**Solução:** Certifique-se de rodar pytest do diretório raiz do projeto, não de dentro da pasta `tests/`.

### Testes passam individualmente mas falham em conjunto
**Problema:** Estado compartilhado entre testes.

**Solução:** Use `tmp_path` fixture para isolar arquivos temporários.

### Timeout em testes de performance
**Problema:** Testes demorados excedem limite.

**Solução:** Marque com `@pytest.mark.slow` e rode separadamente.

```python
@pytest.mark.slow
def test_performance_100_arquivos():
    # teste demorado
    pass
```

---

**Dúvidas?** Abra uma issue no GitHub ou consulte a documentação do pytest.
