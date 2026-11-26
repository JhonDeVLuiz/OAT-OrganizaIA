"""Testes do gerador de resposta local (sem chave, sem rede)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import gerador_local


def test_sem_trechos_nao_inventa_fontes():
    out = gerador_local.gerar_resposta("qualquer coisa", [])
    assert out["geracao"] == "local"
    assert out["fontes"] == []
    assert "Não encontrei" in out["resposta"]


def test_cita_hash_das_fontes():
    trechos = [
        {"arquivo": "fatura-luz.txt", "hash": "a" * 64,
         "texto": "valor da fatura de luz é 150,00 reais"},
        {"arquivo": "holerite.txt", "hash": "b" * 64,
         "texto": "salário bruto de 5000 reais"},
    ]
    out = gerador_local.gerar_resposta("valor da fatura de luz", trechos)
    assert out["geracao"] == "local"
    assert len(out["fontes"]) == 2
    assert out["fontes"][0] == {"arquivo": "fatura-luz.txt", "hash": "a" * 64}
    # resposta cita os hashes curtos e os nomes dos arquivos
    assert "fatura-luz.txt" in out["resposta"]
    assert "holerite.txt" in out["resposta"]
    assert "a" * 16 in out["resposta"]
    assert "150,00" in out["resposta"]


def test_limita_a_5_fontes():
    trechos = [
        {"arquivo": f"arq{i}.txt", "hash": ("h" * 64), "texto": f"conteudo {i}"}
        for i in range(8)
    ]
    out = gerador_local.gerar_resposta("x", trechos)
    assert len(out["fontes"]) == 5
