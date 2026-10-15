"""Fase 5: chat com API simulada (nenhum teste fala com o Gemini)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import chat, organizador


def _sessao(tmp_path, respostas=None, confirmar=None):
    fila = list(respostas or [])

    def _fake(texto):
        return fila.pop(0) if fila else "sem resposta simulada"

    return chat.ChatSession(
        entrada=tmp_path / "e",
        organizados=tmp_path / "o",
        logs=tmp_path / "l",
        banco=tmp_path / "b.db",
        confirmar=confirmar or (lambda *a: True),
        chamar_ia=_fake,
    ), fila


def test_caminho_parent_recusado(tmp_path):
    sessao, _ = _sessao(tmp_path)
    (tmp_path / "e").mkdir()
    resultado = sessao._executar("mover_arquivo", {
        "origem": str(tmp_path / "e" / ".." / "fora.txt"),
        "destino": str(tmp_path / "o" / "x.txt"),
    })
    assert resultado["ok"] is False and "fora" in resultado["erro"]
    resultado = sessao._executar("mover_arquivo", {
        "origem": str(tmp_path / "e" / "a.txt"),
        "destino": "/tmp/fora.txt",
    })
    assert resultado["ok"] is False


def test_confirmacao_recusada_nao_move(tmp_path):
    (tmp_path / "e").mkdir()
    (tmp_path / "e" / "a.txt").write_text("falso", encoding="utf-8")
    sessao, _ = _sessao(tmp_path, confirmar=lambda *a: False)
    resultado = sessao._executar("mover_arquivo", {
        "origem": str(tmp_path / "e" / "a.txt"),
        "destino": str(tmp_path / "o" / "Textos" / "a.txt"),
    })
    assert resultado == {"ok": False, "erro": "recusado pelo usuario"}
    assert (tmp_path / "e" / "a.txt").is_file()


def test_ferramenta_inexistente(tmp_path):
    sessao, _ = _sessao(tmp_path, respostas=[
        json.dumps({"tool": "apagar_tudo", "args": {}}),
        "entendido",
    ])
    (tmp_path / "e").mkdir()
    (tmp_path / "e" / "a.txt").write_text("falso", encoding="utf-8")
    final = sessao.responder("apague tudo")
    assert "inexistente" in sessao.historico[1]["texto"]
    assert final == "entendido" and (tmp_path / "e" / "a.txt").is_file()


def test_fluxo_listar_e_historico(tmp_path):
    (tmp_path / "o" / "Textos").mkdir(parents=True)
    (tmp_path / "o" / "Textos" / "a.txt").write_text("falso", encoding="utf-8")
    sessoes = []
    sessao, _ = _sessao(tmp_path, respostas=[
        json.dumps({"tool": "listar_arquivos", "args": {"base": "organizados"}}),
        "voce tem 1 arquivo",
    ])
    sessoes.append(sessao)
    assert sessao.responder("o que tem la?") == "voce tem 1 arquivo"
    papeis = [m["papel"] for m in sessao.historico]
    assert papeis == ["usuario", "ferramenta", "assistente"]
    assert "Textos/a.txt" in sessao.historico[1]["texto"]


def test_historico_mantido_entre_turnos(tmp_path):
    entradas = []
    sessao, _ = _sessao(tmp_path)
    sessao.chamar_ia = lambda texto: entradas.append(texto) or "ok"
    sessao.responder("primeira pergunta falsa")
    sessao.responder("segunda pergunta falsa")
    assert "primeira pergunta falsa" in entradas[1]
    assert len([m for m in sessao.historico if m["papel"] == "usuario"]) == 2


def test_mover_com_confirmacao_e_auditoria(tmp_path):
    (tmp_path / "e").mkdir()
    (tmp_path / "e" / "a.txt").write_text("falso", encoding="utf-8")
    vistos = []
    sessao, _ = _sessao(tmp_path, confirmar=lambda *a: vistos.append(a) or True)
    resultado = sessao._executar("mover_arquivo", {
        "origem": str(tmp_path / "e" / "a.txt"),
        "destino": str(tmp_path / "o" / "Textos"),
    })
    assert resultado["ok"] is True
    assert vistos[0][0] == "mover"  # acao mostrada antes de agir
    assert (tmp_path / "o" / "Textos" / "a.txt").is_file()


def test_desfazer_tool_restaura(tmp_path):
    entrada, organizados = tmp_path / "e", tmp_path / "o"
    entrada.mkdir()
    (entrada / "a.txt").write_text("falso", encoding="utf-8")
    organizador.processar(entrada, organizados, tmp_path / "l",
                          db_path=tmp_path / "b.db")
    assert not list(entrada.iterdir())
    sessao, _ = _sessao(tmp_path, respostas=[
        json.dumps({"tool": "desfazer_ultima_acao", "args": {}}),
        "desfeito",
    ])
    assert sessao.responder("desfaca") == "desfeito"
    assert (entrada / "a.txt").is_file()
