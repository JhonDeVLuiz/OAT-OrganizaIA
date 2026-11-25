"""Sonda rapida: a IA responde? Quanto tempo leva? (nao imprime a chave)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import classificador, config

print("chave presente:", bool(classificador.chave_ativa()))
print("modelos:", classificador.modelos())
print("base:", config.IA_BASE_URL)

t0 = time.perf_counter()
try:
    detalhe = {}
    r = classificador.classificar_conteudo(
        "fatura-luz-2026-03.txt",
        "Fatura de energia eletrica. Vencimento 10/03/2026. Valor total R$ 184,32. "
        "CPF 123.456.789-00.",
        detalhe=detalhe,
    )
    print("resultado:", r, "motivo:", detalhe,
          "segundos:", round(time.perf_counter() - t0, 2))
except Exception as exc:
    print("erro:", type(exc).__name__, str(exc)[:160],
          "segundos:", round(time.perf_counter() - t0, 2))
