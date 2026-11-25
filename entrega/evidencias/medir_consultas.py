"""Gera volume ficticio e mede as 2 consultas lentas (antes/depois).

Uso: .\\.venv\\Scripts\\python.exe entrega\\evidencias\\medir_consultas.py

Nao toca em dados/organizaia.db: usa um banco temporario. Saida:
entrega/evidencias/resultados_consultas.json + resumo no terminal.
"""
import hashlib
import json
import sqlite3
import statistics
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import repositorio

N_ARQUIVOS = 100_000
N_CLASSIFICACOES = 100_000
N_AUDITORIA = 300_000
REPETICOES = 200

CATEGORIAS = ["Faturas", "Estudos", "Trabalho", "Pessoal", "Outros", "PDFs", "Textos"]
EXTENSOES = [".pdf", ".txt", ".docx", ".xlsx", ".csv"]
PASTAS = ["Faturas", "Estudos", "Trabalho", "Pessoal", "Outros"]
PALAVRAS = ["fatura", "relatorio", "resumo", "contrato", "receita", "nota", "carta"]
SAIDA = Path(__file__).resolve().parent / "resultados_consultas.json"


def _agora():
    return datetime.now(timezone.utc).isoformat()


def gerar_volume(banco):
    repositorio.iniciar_banco(banco)
    con = sqlite3.connect(str(banco))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=OFF;")
    agora = _agora()
    print(f"gerando {N_ARQUIVOS:,} arquivos...".replace(",", "."))
    con.executemany(
        "INSERT OR IGNORE INTO arquivos"
        " (hash, origem, destino, categoria, origem_decisao, criado_em)"
        " VALUES (?, ?, ?, ?, ?, ?);",
        [(
            hashlib.sha256(f"volume-{i}".encode()).hexdigest(),
            f"entrada/arquivo_{i:06d}{EXTENSOES[i % len(EXTENSOES)]}",
            f"organizados/{PASTAS[i % len(PASTAS)]}/"
            f"{PALAVRAS[i % len(PALAVRAS)]}_{i:06d}{EXTENSOES[i % len(EXTENSOES)]}",
            CATEGORIAS[i % len(CATEGORIAS)],
            "regras" if i % 3 else "ia",
            agora,
        ) for i in range(N_ARQUIVOS)],
    )
    print(f"gerando {N_CLASSIFICACOES:,} classificacoes...".replace(",", "."))
    con.executemany(
        "INSERT INTO classificacoes (arquivo_id, categoria, confianca, data)"
        " VALUES (?, ?, ?, ?);",
        [(i + 1, CATEGORIAS[i % len(CATEGORIAS)], 0.6 + (i % 40) / 100, agora)
         for i in range(N_CLASSIFICACOES)],
    )
    print(f"gerando {N_AUDITORIA:,} auditoria...".replace(",", "."))
    con.executemany(
        "INSERT INTO auditoria (acao, caminho, data) VALUES (?, ?, ?);",
        [(
            "mover" if i % 5 else "ler",
            f"organizados/{PASTAS[i % len(PASTAS)]}/"
            f"{PALAVRAS[i % len(PALAVRAS)]}_{(i * 7) % N_ARQUIVOS:06d}"
            f"{EXTENSOES[i % len(EXTENSOES)]}",
            agora,
        ) for i in range(N_AUDITORIA)],
    )
    con.commit()
    total = {t: con.execute(f"SELECT count(*) FROM {t};").fetchone()[0]
             for t in ("arquivos", "classificacoes", "auditoria")}
    con.close()
    return total


def plano(con, sql, params=()):
    linhas = con.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return [dict(linha)["detail"] for linha in linhas]


def medir(con, sql, params, repeticoes=REPETICOES):
    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        con.execute(sql, params).fetchall()
        tempos.append((time.perf_counter() - inicio) * 1000)
    tempos.sort()
    return {
        "p50_ms": round(statistics.median(tempos), 2),
        "p95_ms": round(tempos[int(len(tempos) * 0.95) - 1], 2),
        "min_ms": round(tempos[0], 2),
        "max_ms": round(tempos[-1], 2),
        "repeticoes": repeticoes,
    }


def executar():
    temp = Path(tempfile.mkdtemp(prefix="organizaia_volume_"))
    banco = temp / "volume.db"
    try:
        totais = gerar_volume(banco)
        con = sqlite3.connect(str(banco))
        con.row_factory = sqlite3.Row
        resultado = {"volume": totais, "banco_temporario": str(banco)}

        q1 = ("SELECT hash, origem, destino, categoria, origem_decisao, criado_em"
              " FROM arquivos WHERE destino LIKE ? ESCAPE '\\'"
              " ORDER BY destino LIMIT 50;")
        p1 = ("%fatura%",)
        p1_ruim = ("%nao_existe_em_lugar_nenhum%",)
        resultado["q1_busca_por_nome"] = {
            "sql": q1,
            "antes": {
                "termo_frequente": {"plano": plano(con, q1, p1),
                                    "tempo": medir(con, q1, p1)},
                "pior_caso_sem_match": {"plano": plano(con, q1, p1_ruim),
                                        "tempo": medir(con, q1, p1_ruim)},
            },
        }

        q2 = ("SELECT acao, caminho, data FROM auditoria"
              " WHERE caminho = ? OR caminho = ? ORDER BY data;")
        caminho = con.execute("SELECT destino FROM arquivos WHERE id = 1;").fetchone()[0]
        p2 = (caminho, caminho.replace("organizados", "entrada"))
        resultado["q2_historico_auditoria"] = {
            "sql": q2,
            "antes": {"plano": plano(con, q2, p2), "tempo": medir(con, q2, p2)},
        }

        print("criando indice auditoria(caminho, data)...")
        con.execute("CREATE INDEX idx_auditoria_caminho ON auditoria(caminho, data);")
        resultado["q2_historico_auditoria"]["depois"] = {
            "indice": "CREATE INDEX idx_auditoria_caminho ON auditoria(caminho, data);",
            "plano": plano(con, q2, p2),
            "tempo": medir(con, q2, p2),
        }

        print("criando indice comum em arquivos(destino) - nao resolve LIKE '%x%'...")
        con.execute("CREATE INDEX IF NOT EXISTS idx_arquivos_destino ON arquivos(destino);")
        resultado["q1_busca_por_nome"]["com_indice_btree"] = {
            "indice": "arquivos(destino) ja existe",
            "termo_frequente": {"plano": plano(con, q1, p1),
                                "tempo": medir(con, q1, p1)},
            "pior_caso_sem_match": {"plano": plano(con, q1, p1_ruim),
                                    "tempo": medir(con, q1, p1_ruim)},
        }

        print("criando FTS5 de destino...")
        con.execute(
            "CREATE VIRTUAL TABLE arquivos_fts USING fts5("
            "destino, content='arquivos', content_rowid='id');")
        con.execute("INSERT INTO arquivos_fts(arquivos_fts) VALUES('rebuild');")
        q1b = ("SELECT a.hash, a.origem, a.destino, a.categoria, a.origem_decisao,"
               " a.criado_em FROM arquivos_fts f JOIN arquivos a ON a.id = f.rowid"
               " WHERE arquivos_fts MATCH ? ORDER BY a.destino LIMIT 50;")
        q1b_ruim = q1b.replace("ORDER BY a.destino", "ORDER BY rank")
        resultado["q1_busca_por_nome"]["depois_fts5"] = {
            "indice": "CREATE VIRTUAL TABLE arquivos_fts USING fts5(destino, ...)",
            "termo_frequente": {"plano": plano(con, q1b, ("fatura",)),
                                "tempo": medir(con, q1b, ("fatura",))},
            "pior_caso_sem_match": {"plano": plano(con, q1b_ruim, ("nao_existe",)),
                                    "tempo": medir(con, q1b_ruim, ("nao_existe",))},
            "termo_seletivo": {"plano": plano(con, q1b, ("fatura_000123",)),
                               "tempo": medir(con, q1b, ("fatura_000123",))},
        }
        con.close()

        SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        print("salvo em", SAIDA)
    finally:
        con.close() if "con" in dir() else None
        import shutil
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    executar()
