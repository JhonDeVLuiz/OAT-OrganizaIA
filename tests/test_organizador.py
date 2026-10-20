"""Fase 2+3: organizador (dry-run, desfazer, sufixo, duplicata, limites)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import organizador


def _pastas(tmp_path):
    entrada = tmp_path / "entrada"
    organizados = tmp_path / "organizados"
    logs = tmp_path / "logs"
    banco = tmp_path / "teste.db"
    entrada.mkdir()
    return entrada, organizados, logs, banco


def test_dry_run_nao_move(tmp_path):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "a.txt").write_text("oi", encoding="utf-8")
    (entrada / "x.tmp").write_text("temp", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs, dry_run=True, db_path=banco)
    assert resultado["dry_run"] is True and resultado["id"] is None
    assert (entrada / "a.txt").is_file()  # nada saiu do lugar
    assert not (organizados / "Textos" / "a.txt").exists()
    assert list(logs.glob("exec_*.json")) == []  # sem log no dry-run
    assert not banco.exists()  # dry-run nao toca no banco


def test_desfazer_restaura_tudo(tmp_path):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "a.txt").write_text("um", encoding="utf-8")
    (entrada / "b.txt").write_text("dois", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco)
    assert resultado["id"] is not None
    assert not list(entrada.iterdir())
    desfeito = organizador.desfazer_ultima_execucao(logs, db_path=banco,
                                                    raizes=(entrada, organizados))
    assert desfeito["id"] == resultado["id"]
    assert len(desfeito["restaurados"]) == 2
    assert (entrada / "a.txt").read_text(encoding="utf-8") == "um"
    assert (entrada / "b.txt").read_text(encoding="utf-8") == "dois"


def test_nome_repetido_ganha_sufixo(tmp_path):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (organizados / "Textos").mkdir(parents=True)
    (organizados / "Textos" / "a.txt").write_text("antigo", encoding="utf-8")
    (entrada / "a.txt").write_text("novo", encoding="utf-8")
    organizador.processar(entrada, organizados, logs, db_path=banco)
    copia = organizados / "Textos" / "a (1).txt"
    assert copia.is_file() and copia.read_text(encoding="utf-8") == "novo"
    assert (organizados / "Textos" / "a.txt").read_text(encoding="utf-8") == "antigo"


def test_duplicata_vai_para_duplicados(tmp_path):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (organizados / "Textos").mkdir(parents=True)
    (organizados / "Textos" / "orig.txt").write_text("mesmo", encoding="utf-8")
    (entrada / "copia.txt").write_text("mesmo", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco)
    assert resultado["movimentos"][0]["status"] == "duplicado"
    assert (organizados / "Duplicados" / "copia.txt").is_file()


def test_arquivo_grande_e_excluido_ficam(tmp_path):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "grande.txt").write_bytes(b"0" * 64)
    (entrada / ".env").write_text("K=v", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs, max_bytes=10, db_path=banco)
    motivos = {ign["motivo"] for ign in resultado["ignorados"]}
    assert motivos == {"grande", "excluido"}
    assert (entrada / "grande.txt").is_file() and (entrada / ".env").is_file()


def test_log_adulterado_nao_restaura_fora(tmp_path):
    import json as _json

    entrada, organizados, logs, banco = _pastas(tmp_path)
    (organizados / "Textos").mkdir(parents=True)
    vitima = organizados / "Textos" / "v.txt"
    vitima.write_text("falso", encoding="utf-8")
    fora = tmp_path / ".." / "evil_fora.txt"
    (logs).mkdir(exist_ok=True)
    (logs / "exec_evil.json").write_text(_json.dumps({
        "id": "evil", "data": "2026-01-01",
        "movimentos": [
            {"status": "movido", "origem": str(fora), "destino": str(vitima),
             "hash": "h1", "categoria": "Textos"},
            {"status": "movido", "origem": str(entrada / "b.txt"),
             "destino": str(tmp_path / "outro_fora.txt"),
             "hash": "h2", "categoria": "Textos"},
        ],
    }), encoding="utf-8")
    raizes = (entrada, organizados)
    assert organizador.prever_desfazer(logs, raizes=raizes) is None
    assert organizador.desfazer_ultima_execucao(logs, banco, raizes)["restaurados"] == []
    assert organizador.desfazer_ultima_movimentacao(logs, banco, raizes)["restaurados"] == []
    assert vitima.is_file() and not fora.exists()  # nada saiu do lugar


def test_log_tem_id_e_sem_conteudo(tmp_path):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "segredo.txt").write_text("conteudo sensivel 123", encoding="utf-8")
    resultado = organizador.processar(entrada, organizados, logs, db_path=banco)
    dados = json.loads(next(logs.glob("exec_*.json")).read_text(encoding="utf-8"))
    assert dados["id"] == resultado["id"]
    bruto = json.dumps(dados)
    assert "conteudo sensivel" not in bruto  # log so com metadados


def _mock_ia(monkeypatch, categoria="Faturas", confianca=0.9):
    from src import classificador as _clf

    chamadas = []

    def _fake(nome, trecho, categorias=None, chamar_ia=None, detalhe=None):
        chamadas.append((nome, trecho))
        if detalhe is not None:
            detalhe["motivo"] = "ok"
        return (categoria, confianca)

    monkeypatch.setattr(_clf, "classificar_conteudo", _fake)
    return chamadas


def _sem_intervalo(monkeypatch):
    from src import config as _config

    monkeypatch.setattr(_config, "INTERVALO_IA_SEG", 0)


CONTEUDO_LONGO = "conteudo longo de teste para a IA ler com calma e decidir"


def _mock_leitor_legivel(monkeypatch, texto=CONTEUDO_LONGO):
    from src import leitor as _leitor

    monkeypatch.setattr(_leitor, "extrair_trecho", lambda *a, **k: texto)


def test_modo_tipo_sem_ia(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "m.xyz").write_text(CONTEUDO_LONGO, encoding="utf-8")
    _mock_leitor_legivel(monkeypatch)
    chamadas = _mock_ia(monkeypatch)
    real = organizador.processar(entrada, organizados, logs, db_path=banco, modo="tipo")
    mov = real["movimentos"][0]
    assert mov["status"] == "revisar" and mov["nota"] is None and chamadas == []
    assert (organizados / "Revisar" / "m.xyz").is_file()


def test_modo_ia_conteudo(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "m.xyz").write_text(CONTEUDO_LONGO, encoding="utf-8")
    _mock_leitor_legivel(monkeypatch)
    _mock_ia(monkeypatch, "Faturas", 0.9)
    real = organizador.processar(entrada, organizados, logs, db_path=banco, modo="ia")
    mov = real["movimentos"][0]
    assert mov["categoria"] == "Faturas" and mov["origem_decisao"] == "ia"
    assert (organizados / "Faturas" / "m.xyz").is_file()


def test_dry_run_igual_real(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "m.xyz").write_text(CONTEUDO_LONGO, encoding="utf-8")
    _mock_leitor_legivel(monkeypatch)
    _mock_ia(monkeypatch)
    seco = organizador.processar(entrada, organizados, logs, dry_run=True,
                                 db_path=banco, modo="ia")
    real = organizador.processar(entrada, organizados, logs, db_path=banco, modo="ia")
    assert [m["destino"] for m in seco["movimentos"]] == [m["destino"] for m in real["movimentos"]]
    assert seco["movimentos"][0]["destino"].endswith(str(Path("Faturas") / "m.xyz"))
    assert (organizados / "Faturas" / "m.xyz").is_file()


def test_ia_indisponivel_preview(tmp_path, monkeypatch):
    from src import classificador as _clf

    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "m.xyz").write_text(CONTEUDO_LONGO, encoding="utf-8")
    monkeypatch.setattr(_clf, "load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    _mock_leitor_legivel(monkeypatch)
    seco = organizador.processar(entrada, organizados, logs, dry_run=True,
                                 db_path=banco, modo="ia")
    mov = seco["movimentos"][0]
    assert mov["status"] == "revisar" and mov["nota"] == "IA indisponível"
    assert (entrada / "m.xyz").is_file() and list(logs.glob("exec_*.json")) == []


def test_texto_curto_revisar_sem_ia(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "m.xyz").write_text("curto", encoding="utf-8")
    chamadas = _mock_ia(monkeypatch)
    real = organizador.processar(entrada, organizados, logs, db_path=banco)
    mov = real["movimentos"][0]
    assert mov["status"] == "revisar" and mov["nota"] is None
    assert chamadas == [] and (organizados / "Revisar" / "m.xyz").is_file()


def _mock_ia_backend(monkeypatch, resposta):
    """IA real com backend falso: passa pela validacao e pelos limiares de verdade."""
    from src import classificador as _clf

    real = _clf.classificar_conteudo
    monkeypatch.setattr(
        _clf, "classificar_conteudo",
        lambda nome, trecho, **k: real(nome, trecho, chamar_ia=lambda p: resposta))


def test_modo_ia_texto_curto_nome_alta(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "fatura-luz.xyz").write_text("curto", encoding="utf-8")
    _mock_ia_backend(monkeypatch, '{"categoria": "Faturas", "confianca": 0.9}')
    real = organizador.processar(entrada, organizados, logs, db_path=banco, modo="ia")
    assert real["movimentos"][0]["categoria"] == "Faturas"
    assert (organizados / "Faturas" / "fatura-luz.xyz").is_file()


def test_modo_ia_texto_curto_nome_baixa(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "fatura-luz.xyz").write_text("curto", encoding="utf-8")
    _mock_ia_backend(monkeypatch, '{"categoria": "Faturas", "confianca": 0.8}')
    real = organizador.processar(entrada, organizados, logs, db_path=banco, modo="ia")
    mov = real["movimentos"][0]
    assert mov["status"] == "revisar" and mov["nota"] == "baixa-confiança"


def test_modo_ia_indisponivel_fallback_regras(tmp_path, monkeypatch):
    from src import classificador as _clf

    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "n.txt").write_text(CONTEUDO_LONGO, encoding="utf-8")
    (entrada / "m.xyz").write_text(CONTEUDO_LONGO + " diferente", encoding="utf-8")
    _mock_leitor_legivel(monkeypatch)
    monkeypatch.setattr(_clf, "load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    real = organizador.processar(entrada, organizados, logs, db_path=banco, modo="ia")
    por_destino = {Path(m["destino"]).name: m for m in real["movimentos"]}
    assert por_destino["n.txt"]["categoria"] == "Textos"
    assert por_destino["m.xyz"]["status"] == "revisar"
    assert real["avisos"] == ["IA indisponível (sem-chave), usando regras por extensão"]
    assert (organizados / "Textos" / "n.txt").is_file()


def test_max_chamadas_limita_ia(tmp_path, monkeypatch):
    from src import config as _config

    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "a.xyz").write_text(CONTEUDO_LONGO, encoding="utf-8")
    (entrada / "b.xyz").write_text(CONTEUDO_LONGO + "2", encoding="utf-8")
    _mock_leitor_legivel(monkeypatch)
    chamadas = _mock_ia(monkeypatch)
    monkeypatch.setattr(_config, "MAX_CHAMADAS_IA", 1)
    monkeypatch.setattr(_config, "INTERVALO_IA_SEG", 0)
    real = organizador.processar(entrada, organizados, logs, db_path=banco, modo="ia")
    assert len(chamadas) == 1
    assert real["avisos"] == ["IA indisponível (limite de chamadas), usando regras por extensão"]


def test_intervalo_entre_chamadas(tmp_path, monkeypatch):
    import time as _time

    from src import config as _config

    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "a.xyz").write_text(CONTEUDO_LONGO, encoding="utf-8")
    (entrada / "b.xyz").write_text(CONTEUDO_LONGO + "2", encoding="utf-8")
    _mock_leitor_legivel(monkeypatch)
    _mock_ia(monkeypatch)
    monkeypatch.setattr(_config, "INTERVALO_IA_SEG", 5)
    dormidas = []
    monkeypatch.setattr(_time, "sleep", lambda s: dormidas.append(s))
    organizador.processar(entrada, organizados, logs, db_path=banco, modo="ia")
    assert dormidas == [5]


def test_cache_hash_uma_chamada(tmp_path, monkeypatch):
    entrada, organizados, logs, banco = _pastas(tmp_path)
    (entrada / "m.xyz").write_text(CONTEUDO_LONGO, encoding="utf-8")
    _mock_leitor_legivel(monkeypatch)
    chamadas = _mock_ia(monkeypatch)
    cache = {}
    kwargs = dict(entrada=entrada, organizados=organizados, max_bytes=10 ** 9,
                  db_path=banco, usar_ia=True, cache_ia=cache, modo="ia")
    r1 = organizador._processar_um(entrada / "m.xyz", indice=set(), **kwargs)
    r2 = organizador._processar_um(entrada / "m.xyz", indice=set(), **kwargs)
    assert len(chamadas) == 1 and r1["destino"] == r2["destino"]
