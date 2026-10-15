"""Fase 2: guards de seguranca (s so arquivos falsos de teste)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import seguranca


def test_caminho_fora_da_raiz_rejeitado(tmp_path):
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    with pytest.raises(ValueError):
        seguranca.resolver_confinado(tmp_path / "fora.txt", raiz)
    with pytest.raises(ValueError):
        seguranca.resolver_confinado(raiz / ".." / "fora.txt", raiz)


def test_caminho_dentro_ok(tmp_path):
    raiz = tmp_path / "projeto"
    (raiz / "entrada").mkdir(parents=True)
    alvo = raiz / "entrada" / "a.txt"
    alvo.write_text("x", encoding="utf-8")
    assert seguranca.resolver_confinado(alvo, raiz / "entrada") == alvo.resolve()


def test_nome_malicioso_sanitizado():
    assert seguranca.nome_seguro("../../evil.txt") == "evil.txt"
    limpo = seguranca.nome_seguro("a/b\\c:d?.txt")
    assert "/" not in limpo and "\\" not in limpo and ":" not in limpo and "?" not in limpo
    with pytest.raises(ValueError):
        seguranca.nome_seguro("..")


def test_lista_de_exclusao(tmp_path):
    assert seguranca.excluido(".env")
    assert seguranca.excluido("minhas SENHAS.txt")
    assert seguranca.excluido("chave_pix.txt")
    assert seguranca.excluido("documentos pessoais.docx")
    assert not seguranca.excluido("relatorio.txt")
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    alvo = raiz / ".env"
    alvo.write_text("x=1", encoding="utf-8")
    ok, motivo = seguranca.validar_arquivo(alvo, raiz)
    assert (ok, motivo) == (False, "excluido")


def test_arquivo_grande_bloqueado(tmp_path):
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    alvo = raiz / "grande.bin"
    alvo.write_bytes(b"0" * 64)
    ok, motivo = seguranca.validar_arquivo(alvo, raiz, max_bytes=10)
    assert (ok, motivo) == (False, "grande")


def test_mascaramento():
    texto = "CPF 123.456.789-09, cartao 4111 1111 1111 1111, mail a@b.com"
    mascarado = seguranca.mascarar_sensivel(texto)
    assert "123.456.789-09" not in mascarado and "[CPF]" in mascarado
    assert "4111 1111 1111 1111" not in mascarado and "[CARTAO]" in mascarado
    assert "a@b.com" not in mascarado and "[EMAIL]" in mascarado
