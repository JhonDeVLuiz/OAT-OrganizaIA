"""Fase 4: classificador (tudo mock; nenhum teste chama o Gemini de verdade)."""
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
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(classificador, "load_dotenv", lambda *a, **k: False)
    assert classificador.classificar_ia("x.xyz", "trecho") is None


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
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco)
    mov = resultado["movimentos"][0]
    assert mov["categoria"] == "Textos" and chamadas == []  # reusou o registro
    assert (organizados / "Textos" / "misterio.xyz").is_file()
