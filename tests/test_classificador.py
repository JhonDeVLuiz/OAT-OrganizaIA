"""Fase 4: classificador GLM (tudo mock; nenhum teste chama a API de verdade)."""
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import classificador, organizador, repositorio


def _fake(resposta, caixa=None):
    def _chamar(prompt):
        if caixa is not None:
            caixa.append(prompt)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta
    return _chamar


def test_retry_transitorio_recupera():
    from src import classificador as clf

    chamadas = []

    def instavel():
        chamadas.append(1)
        if len(chamadas) < 3:
            raise RuntimeError("503 UNAVAILABLE")
        return "ok"

    assert clf.chamar_com_retry(instavel, esperar=lambda s: None) == "ok"
    assert len(chamadas) == 3


def test_retry_nao_repete_erro_final():
    from src import classificador as clf

    chamadas = []

    def final():
        chamadas.append(1)
        raise RuntimeError("quota excedida")

    with pytest.raises(RuntimeError):
        clf.chamar_com_retry(final, esperar=lambda s: None)
    assert len(chamadas) == 1


def test_retry_esgota_e_levanta():
    from src import classificador as clf

    chamadas = []

    def sempre_503():
        chamadas.append(1)
        raise RuntimeError("503 UNAVAILABLE")

    with pytest.raises(RuntimeError):
        clf.chamar_com_retry(sempre_503, esperar=lambda s: None)
    assert len(chamadas) == 3


def test_rotatividade_modelo_falha_proximo(tmp_path, monkeypatch):
    from src import classificador as clf

    tentados = []

    def _fake_post(_base, _chave, modelo_nome, _prompt, _timeout):
        tentados.append(modelo_nome)
        if modelo_nome == "ruim":
            raise RuntimeError("HTTP 404: Not Found")
        return "ok"

    monkeypatch.setattr(clf, "_post_anthropic", _fake_post)
    monkeypatch.setattr(clf, "IA_MODELOS", ["ruim", "bom"])
    assert clf._chamar_glm("oi", "k", esperar=lambda s: None) == "ok"
    assert tentados == ["ruim", "bom"]


def test_rotatividade_404_vai_para_o_proximo(tmp_path, monkeypatch):
    from src import classificador as clf

    tentados = []

    def _fake_post(_base, _chave, modelo_nome, _prompt, _timeout):
        tentados.append(modelo_nome)
        if modelo_nome == "ruim":
            raise RuntimeError("HTTP 404: Not Found")
        return "ok"

    monkeypatch.setattr(clf, "_post_anthropic", _fake_post)
    monkeypatch.setattr(clf, "IA_MODELOS", ["ruim", "bom"])
    assert clf._chamar_glm("oi", "k", esperar=lambda s: None) == "ok"
    assert tentados == ["ruim", "bom"]


def test_erro_final_chave_invalida_nao_troca(tmp_path, monkeypatch):
    from src import classificador as clf

    tentados = []

    def _fake_post(_base, _chave, modelo_nome, _prompt, _timeout):
        tentados.append(modelo_nome)
        raise RuntimeError("HTTP 401: Unauthorized")

    monkeypatch.setattr(clf, "_post_anthropic", _fake_post)
    monkeypatch.setattr(clf, "IA_MODELOS", ["a", "b"])
    with pytest.raises(RuntimeError):
        clf._chamar_glm("oi", "k", esperar=lambda s: None)
    assert tentados == ["a"]


def test_conteudo_longo_corte_07():
    from src import classificador as clf

    longo = "x" * 30
    ok = lambda p: '{"categoria": "Faturas", "confianca": 0.7}'
    baixo = lambda p: '{"categoria": "Faturas", "confianca": 0.69}'
    assert clf.classificar_conteudo("a.xyz", longo, chamar_ia=ok) == ("Faturas", 0.7)
    assert clf.classificar_conteudo("a.xyz", longo, chamar_ia=baixo) is None
    fora = lambda p: '{"categoria": "Astronomia", "confianca": 0.99}'
    assert clf.classificar_conteudo("a.xyz", longo, chamar_ia=fora) is None


def test_conteudo_curto_so_nome_corte_085():
    from src import classificador as clf

    caixa = []
    alto = lambda p: caixa.append(p) or '{"categoria": "Faturas", "confianca": 0.9}'
    assert clf.classificar_conteudo("fatura.xyz", "curto", chamar_ia=alto) == ("Faturas", 0.9)
    assert "SOMENTE pelo nome" in caixa[0]
    medio = lambda p: '{"categoria": "Faturas", "confianca": 0.8}'
    assert clf.classificar_conteudo("fatura.xyz", "curto", chamar_ia=medio) is None


def test_json_quebrado_vira_revisar():
    assert classificador.classificar_ia("x.xyz", "trecho",
                                         chamar_ia=_fake("nao e json {")) is None
    assert classificador.classificar_ia("x.xyz", "trecho",
                                         chamar_ia=_fake('["lista"]')) is None
    assert classificador.classificar_ia("x.xyz", "trecho",
                                         chamar_ia=_fake('{"categoria": "Textos"}')) is None


def test_categoria_inexistente_vira_revisar():
    fake = _fake('{"categoria": "Astronomia", "confianca": 0.95}')
    assert classificador.classificar_ia("x.xyz", "trecho", chamar_ia=fake) is None


def test_confianca_baixa_vira_revisar_e_limite_aceito():
    assert classificador.classificar_ia(
        "x.xyz", "t", chamar_ia=_fake('{"categoria": "Textos", "confianca": 0.69}')) is None
    assert classificador.classificar_ia(
        "x.xyz", "t", chamar_ia=_fake('{"categoria": "Textos", "confianca": 0.7}')) == ("Textos", 0.7)
    assert classificador.classificar_ia(
        "x.xyz", "t", chamar_ia=_fake('{"categoria": "Textos", "confianca": 1.5}')) is None
    assert classificador.classificar_ia(
        "x.xyz", "t", chamar_ia=_fake('{"categoria": "Textos", "confianca": -0.1}')) is None


def test_falha_de_rede_nao_derruba():
    assert classificador.classificar_ia(
        "x.xyz", "t", chamar_ia=_fake(RuntimeError("timeout"))) is None
    assert classificador.classificar_ia(
        "x.xyz", "t", chamar_ia=_fake(RuntimeError("quota"))) is None


def test_texto_mascarado_antes_do_envio():
    caixa = []
    trecho = "CPF 123.456.789-09, cartao 4111 1111 1111 1111, mail a@b.com"
    resultado = classificador.classificar_ia(
        "x.xyz", trecho,
        chamar_ia=_fake('{"categoria": "Textos", "confianca": 0.9}', caixa))
    assert resultado == ("Textos", 0.9)
    prompt = caixa[0]
    assert "123.456.789-09" not in prompt and "[CPF]" in prompt
    assert "4111 1111 1111 1111" not in prompt and "[CARTAO]" in prompt
    assert "a@b.com" not in prompt and "[EMAIL]" in prompt


def test_exclusao_nunca_chama_ia():
    chamadas = []
    assert classificador.classificar_ia(
        ".env", "K=v", chamar_ia=_fake('{"categoria": "Textos", "confianca": 1}', chamadas)) is None
    assert chamadas == []


def test_sem_chave_sem_rede(monkeypatch):
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.setattr(classificador, "load_dotenv", lambda *a, **k: False)
    assert classificador.classificar_ia("x.xyz", "trecho") is None


def test_glm_classifica_e_usa_o_primeiro_modelo(monkeypatch):
    capturado = {}

    def _fake_post(base, chave, modelo_nome, prompt, timeout):
        capturado.update(base=base, chave=chave, modelo=modelo_nome, url=base)
        return '{"categoria": "Faturas", "confianca": 0.9}'

    monkeypatch.setattr(classificador, "_post_anthropic", _fake_post)
    monkeypatch.setattr(classificador, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(classificador, "IA_BASE_URL", "https://api.z.ai/api/anthropic")
    monkeypatch.setenv("GLM_API_KEY", "falsa")
    resultado = classificador.classificar_conteudo("a.xyz", "x" * 30)
    assert resultado == ("Faturas", 0.9)
    assert capturado["modelo"] == classificador.modelos()[0]
    assert capturado["chave"] == "falsa"
    assert capturado["base"].endswith("/api/anthropic")


def test_glm_sem_chave_motivo(monkeypatch):
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.setattr(classificador, "load_dotenv", lambda *a, **k: False)
    detalhe = {}
    assert classificador.classificar_conteudo("a.xyz", "x" * 30, detalhe=detalhe) is None
    assert detalhe["motivo"] == "sem-chave"


def test_glm_rotatividade_para_o_proximo_modelo(monkeypatch):
    dormidas = []
    monkeypatch.setattr(classificador, "chamar_com_retry",
                        lambda func, **k: func())
    monkeypatch.setattr(classificador, "IA_MODELOS", ["a", "b"])

    def _fake_post(_base, _chave, modelo_nome, _prompt, _timeout):
        if modelo_nome == "a":
            raise RuntimeError("HTTP 429: Too Many Requests")
        return '{"categoria": "Faturas", "confianca": 0.9}'

    monkeypatch.setattr(classificador, "_post_anthropic", _fake_post)
    monkeypatch.setenv("GLM_API_KEY", "falsa")
    resultado = classificador._chamar_glm("p", "falsa",
                                          esperar=dormidas.append)
    assert resultado.startswith('{"categoria"')
    assert dormidas == [classificador.GLM_ESPERA_MODELOS]


def test_glm_todos_modelos_falham(monkeypatch):
    monkeypatch.setattr(classificador, "chamar_com_retry",
                        lambda func, **k: func())

    def _fake_post(*a, **k):
        raise RuntimeError("HTTP 500: Internal Server Error")

    monkeypatch.setattr(classificador, "_post_anthropic", _fake_post)
    monkeypatch.setenv("GLM_API_KEY", "falsa")
    detalhe = {}
    saida = classificador.classificar_conteudo("a.xyz", "x" * 30, detalhe=detalhe)
    assert saida is None and detalhe["motivo"] == "falha"


def test_modelos_da_ia():
    assert classificador.modelos() == classificador.IA_MODELOS


def test_ia_modelos_do_env(monkeypatch):
    """IA_MODELOS no .env sobrescreve a rotatividade (ex.: modelos Claude)."""
    from src import config as cfg

    monkeypatch.setenv("IA_MODELOS", "claude-haiku-4-5, claude-sonnet-4-5")
    assert cfg._modelos_da_ia() == ["claude-haiku-4-5", "claude-sonnet-4-5"]
    monkeypatch.setenv("IA_MODELOS", "  ,  ,claude-haiku-4-5,")
    assert cfg._modelos_da_ia() == ["claude-haiku-4-5"]
    monkeypatch.delenv("IA_MODELOS", raising=False)
    assert cfg._modelos_da_ia() == ["glm-4.7-flash", "glm-4.5-flash"]


def test_ia_base_url_do_env(monkeypatch):
    """IA_BASE_URL no .env muda o gateway sem tocar em codigo."""
    import os as _os
    import subprocess
    import sys

    env = dict(_os.environ)
    env["IA_BASE_URL"] = "https://gateway.exemplo.site"
    env["IA_MODELOS"] = "claude-haiku-4-5"
    env.pop("GLM_API_KEY", None)
    codigo = ("from src import config as c; "
              "print(c.IA_BASE_URL, c.IA_MODELOS)")
    saida = subprocess.run([sys.executable, "-c", codigo], env=env,
                           capture_output=True, text=True,
                           cwd=str(env.get("TESTS_CWD", _os.getcwd())))
    linha = saida.stdout.strip()
    assert linha == "https://gateway.exemplo.site ['claude-haiku-4-5']", linha


def test_ia_base_url_sem_https_e_recusada(monkeypatch):
    """Chave nunca pode trafegar em claro: http:// derruba na importacao."""
    import os as _os
    import subprocess
    import sys

    env = dict(_os.environ)
    env["IA_BASE_URL"] = "http://gateway.exemplo.site"
    env.pop("GLM_API_KEY", None)
    codigo = "from src import config"
    saida = subprocess.run([sys.executable, "-c", codigo], env=env,
                           capture_output=True, text=True,
                           cwd=str(env.get("TESTS_CWD", _os.getcwd())))
    assert saida.returncode != 0
    assert "https://" in saida.stderr


def test_base_dir_congelado_usa_pasta_do_exe():
    """No .exe (PyInstaller) dados e .env ficam ao lado do executavel."""
    import os as _os
    import subprocess
    import sys

    env = dict(_os.environ)
    env.pop("GLM_API_KEY", None)
    codigo = (
        "import sys; sys.frozen = True; "
        "sys.executable = r'C:\\Programa\\OrganizaIA.exe'; "
        "from src import config as c; print(c.BASE_DIR)")
    saida = subprocess.run([sys.executable, "-c", codigo], env=env,
                           capture_output=True, text=True,
                           cwd=str(_os.getcwd()))
    assert saida.returncode == 0, saida.stderr
    assert saida.stdout.strip().lower() == r"c:\programa", saida.stdout


def test_regras_decididas_nao_chamam_ia(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = (tmp_path / n for n in ("e", "o", "l", "b.db"))
    entrada.mkdir()
    (entrada / "nota.txt").write_text("falso", encoding="utf-8")
    chamadas = []
    monkeypatch.setattr(classificador, "classificar_ia",
                        lambda *a, **k: chamadas.append(a) or ("Textos", 1.0))
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco)
    assert resultado["movimentos"][0]["status"] == "movido" and chamadas == []


def test_nao_classifica_duas_vezes(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = (tmp_path / n for n in ("e", "o", "l", "b.db"))
    entrada.mkdir()
    (entrada / "misterio.xyz").write_text("conteudo ia", encoding="utf-8")
    resumo = hashlib.sha256(b"conteudo ia").hexdigest()
    repositorio.iniciar_banco(banco)
    arquivo_id = repositorio.salvar_arquivo(banco, resumo, "e/misterio.xyz",
                                            "o/Textos/misterio.xyz", "Textos", "ia")
    repositorio.salvar_classificacao(banco, arquivo_id, "Textos", 0.9)
    chamadas = []
    monkeypatch.setattr(classificador, "classificar_ia",
                        lambda *a, **k: chamadas.append(a) or ("Planilhas", 0.99))
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco, modo="ia")
    mov = resultado["movimentos"][0]
    assert mov["categoria"] == "Textos" and chamadas == []  # reusou o registro
    assert (organizados / "Textos" / "misterio.xyz").is_file()
