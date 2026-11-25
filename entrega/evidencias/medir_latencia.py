"""Mede latencia do pipeline local, da consulta ao banco e da chamada de IA.

Uso: .\\.venv\\Scripts\\python.exe entrega\\evidencias\\medir_latencia.py
Saida: entrega/evidencias/resultados_latencia.json
"""
import json
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import classificador, organizador, repositorio

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "entrega" / "base-exemplo"
SAIDA = Path(__file__).resolve().parent / "resultados_latencia.json"


def _tempos(fn, repeticoes):
    valores = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        fn()
        valores.append((time.perf_counter() - inicio) * 1000)
    valores.sort()
    return {"p50_ms": round(statistics.median(valores), 2),
            "p95_ms": round(valores[int(len(valores) * 0.95) - 1], 2),
            "min_ms": round(valores[0], 2), "max_ms": round(valores[-1], 2),
            "repeticoes": repeticoes}


def main():
    raiz = Path(tempfile.mkdtemp(prefix="organizaia_lat_"))
    resultado = {}
    try:
        entrada, organizados, logs = raiz / "entrada", raiz / "organizados", raiz / "logs"
        entrada.mkdir()
        for doc in sorted(BASE.glob("*.txt")):
            shutil.copy2(doc, entrada / doc.name)
        banco = raiz / "dados" / "lat.db"
        inicio = time.perf_counter()
        saida = organizador.processar(entrada=entrada, organizados=organizados,
                                      logs=logs, db_path=banco, modo="tipo")
        total = (time.perf_counter() - inicio) * 1000
        n = len(saida["movimentos"])
        resultado["pipeline_modo_tipo"] = {
            "arquivos": n,
            "total_ms": round(total, 2),
            "media_por_arquivo_ms": round(total / n, 2) if n else None,
            "arquivos_por_segundo": round(n / (total / 1000), 2) if total else None,
        }

        resultado["consulta_buscar_por_nome"] = _tempos(
            lambda: repositorio.buscar_por_nome(banco, "fatura"), 100)
        resultado["consulta_buscar_por_categoria"] = _tempos(
            lambda: repositorio.buscar_por_categoria(banco, "Textos"), 100)

        inicio = time.perf_counter()
        detalhe = {}
        valor = classificador.classificar_conteudo(
            "fatura-luz-2026-03.txt",
            "Fatura de energia eletrica. Vencimento 10/03/2026. Valor R$ 184,32.",
            detalhe=detalhe)
        resultado["chamada_ia"] = {
            "resultado": valor,
            "motivo": detalhe.get("motivo"),
            "segundos_ate_falhar": round(time.perf_counter() - inicio, 2),
            "observacao": "gateway respondeu HTTP 401; nao e latencia de inferencia",
        }

        SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        print("salvo em", SAIDA)
    finally:
        shutil.rmtree(raiz, ignore_errors=True)


if __name__ == "__main__":
    main()
