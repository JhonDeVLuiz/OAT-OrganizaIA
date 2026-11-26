"""RAG local: chunking + indice FTS5 + top-k + prompt aumentado com citacao.

Nao usa embeddings (proposta com FAISS/e5-small) nem LLM: a geracao esta
bloqueada pelo HTTP 401 do gateway. O que roda aqui e a parte de recuperacao
do RAG e a montagem do prompt com provas (hash/arquivo).

Uso: .\\.venv\\Scripts\\python.exe entrega\\evidencias\\demo_rag.py
Saida: entrega/evidencias/resultados_rag.json
"""
import hashlib
import json
import re
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import gerador_local, seguranca

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "entrega" / "base-exemplo"
SAIDA = Path(__file__).resolve().parent / "resultados_rag.json"
CHUNK, OVERLAP, TOP_K = 500, 50, 5
PERGUNTA = "valor da fatura de luz de marco de 2026"
STOPWORDS = {"quanto", "custou", "qual", "valor", "conta", "para", "como",
             "onde", "quando", "the", "que", "dos", "das", "por"}


def _hash(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _chunks(texto):
    pedacos, inicio = [], 0
    while inicio < len(texto):
        pedacos.append(texto[inicio:inicio + CHUNK])
        inicio += CHUNK - OVERLAP
    return pedacos


def _termos(pergunta):
    palavras = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", pergunta.lower())
    palavras = [p for p in palavras if p not in STOPWORDS]
    return " OR ".join(dict.fromkeys(palavras))


def executar():
    import sqlite3

    temp = Path(tempfile.mkdtemp(prefix="organizaia_rag_"))
    try:
        con = sqlite3.connect(str(temp / "rag.db"))
        con.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, arquivo TEXT,"
                    " hash TEXT, texto TEXT);")
        con.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5("
                    "texto, content='chunks', content_rowid='id',"
                    " tokenize='unicode61 remove_diacritics 2');")
        linhas = []
        for doc in sorted(BASE.glob("*.txt")):
            texto = doc.read_text(encoding="utf-8", errors="replace")
            for pedaco in _chunks(texto):
                linhas.append((doc.name, _hash(texto), seguranca.mascarar_sensivel(pedaco)))
        con.executemany("INSERT INTO chunks (arquivo, hash, texto) VALUES (?, ?, ?);", linhas)
        con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild');")
        con.commit()

        consulta = ("SELECT c.arquivo, c.hash, c.texto, bm25(chunks_fts) AS score"
                    " FROM chunks_fts f JOIN chunks c ON c.id = f.rowid"
                    " WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?;")
        inicio = time.perf_counter()
        achados = con.execute(consulta, (_termos(PERGUNTA), TOP_K)).fetchall()
        latencia = (time.perf_counter() - inicio) * 1000
        con.close()

        prompt = (
            "Responda usando SOMENTE os trechos abaixo e cite o hash do arquivo.\n"
            "Categorias permitidas: Faturas, Estudos, Trabalho, Pessoal, Outros.\n"
            f"Pergunta: {PERGUNTA}\n\n"
            + "\n\n".join(f"[{i + 1}] arquivo={a} hash={h}\n{t}"
                         for i, (a, h, t, _) in enumerate(achados))
        )
        trechos = [
            {"arquivo": a, "hash": h, "texto": t} for a, h, t, _ in achados
        ]
        geracao = gerador_local.gerar_resposta(PERGUNTA, trechos)
        resultado = {
            "pergunta": PERGUNTA,
            "consulta_fts": _termos(PERGUNTA),
            "chunks_indexados": len(linhas),
            "documentos": len(list(BASE.glob("*.txt"))),
            "chunking": {"tamanho": CHUNK, "overlap": OVERLAP},
            "top_k": TOP_K,
            "latencia_busca_ms": round(latencia, 2),
            "resultados": [
                {"arquivo": a, "hash": h[:16] + "...", "score": round(s, 4),
                 "trecho": t[:200]} for a, h, t, s in achados],
            "prompt_aumentado": prompt[:1800],
            "geracao": "local",
            "resposta": geracao["resposta"],
            "fontes": geracao["fontes"],
        }
        SAIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        print("salvo em", SAIDA)
    finally:
        import shutil
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    executar()
