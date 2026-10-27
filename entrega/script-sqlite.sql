-- ============================================================================
-- OrganizaIA - Script SQLite (versão do produto real)
-- Equivalente ao schema de src/repositorio.py (fase 3)
-- 100% fictício: hashes/nomes/valores de exemplo; nenhum dado real.
-- Rodar:  sqlite3 dados/organizaia.db < entrega/script-sqlite.sql
-- Politica do projeto: SQL SEMPRE parametrizado (?). Este script e apenas DDL+seed.
-- ============================================================================

PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS arquivos (
    id INTEGER PRIMARY KEY,
    hash TEXT NOT NULL UNIQUE,          -- sha256 (publico)
    origem TEXT NOT NULL,               -- interno (caminho em entrada/)
    destino TEXT NOT NULL,              -- interno (caminho em organizados/)
    categoria TEXT,                     -- publico (lista fechada)
    origem_decisao TEXT NOT NULL,       -- regras | ia | duplicata | revisao
    criado_em TEXT NOT NULL             -- ISO-8601 (interno)
);

CREATE TABLE IF NOT EXISTS classificacoes (
    id INTEGER PRIMARY KEY,
    arquivo_id INTEGER NOT NULL REFERENCES arquivos(id),
    categoria TEXT NOT NULL,            -- publico
    confianca REAL NOT NULL,            -- interno (0.0-1.0)
    data TEXT NOT NULL                  -- interno
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY,
    acao TEXT NOT NULL,                 -- mover | reescrever | ler_trecho ...
    caminho TEXT NOT NULL,              -- interno
    data TEXT NOT NULL                  -- interno
);

-- Indices existentes no produto
CREATE INDEX IF NOT EXISTS idx_arquivos_hash ON arquivos(hash);
CREATE INDEX IF NOT EXISTS idx_arquivos_destino ON arquivos(destino);
CREATE INDEX IF NOT EXISTS idx_arquivos_categoria ON arquivos(categoria);
CREATE INDEX IF NOT EXISTS idx_classificacoes_arquivo ON classificacoes(arquivo_id);

-- Indice da OTIMIZACAO 2 (Parte 3, secao 3.4): auditoria.caminho
CREATE INDEX IF NOT EXISTS idx_auditoria_caminho ON auditoria(caminho, data);

-- ============================================================================
-- SEED: 10 registros ficticios (hashes sao placeholders hex de 64 chars)
-- ============================================================================

-- arquivos (10)
INSERT OR IGNORE INTO arquivos (hash, origem, destino, categoria, origem_decisao, criado_em) VALUES
('0a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9','entrada/fatura-luz-2026-03.txt','organizados/Textos/Faturas/fatura-luz-2026-03.txt','Faturas','ia','2026-03-05T14:22:01+00:00'),
('1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a','entrada/contrato_aluguel_2025.txt','organizados/Documentos/Trabalho/contrato_aluguel_2025.txt','Trabalho','ia','2026-03-06T09:10:00+00:00'),
('2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b','entrada/boleto_escola_exemplo.txt','organizados/Textos/Faturas/boleto_escola_exemplo.txt','Faturas','ia','2026-03-07T11:45:12+00:00'),
('3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c','entrada/holerite_exemplo_ana.txt','organizados/Documentos/Trabalho/holerite_exemplo_ana.txt','Trabalho','revisao','2026-03-08T16:30:44+00:00'),
('4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d','entrada/nota_fiscal_padaria.txt','organizados/Textos/Faturas/nota_fiscal_padaria.txt','Faturas','ia','2026-03-10T08:05:02+00:00'),
('5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e','entrada/plano_estudos_eng.txt','organizados/Textos/Estudos/plano_estudos_eng.txt','Estudos','ia','2026-03-11T19:00:36+00:00'),
('60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f','entrada/resumo_curso_sql.txt','organizados/Textos/Estudos/resumo_curso_sql.txt','Estudos','regras','2026-03-12T07:55:00+00:00'),
('718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60','entrada/carta_banco_exemplo.txt','organizados/Documentos/Pessoal/carta_banco_exemplo.txt','Pessoal','revisao','2026-03-13T13:24:59+00:00'),
('8293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f607','entrada/lista_compras.txt','organizados/Textos/Outros/lista_compras.txt','Outros','regras','2026-03-14T18:47:03+00:00'),
('93a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f6071','entrada/exercicios_sql_basico.txt','organizados/Textos/Estudos/exercicios_sql_basico.txt','Estudos','ia','2026-03-15T10:12:00+00:00');

-- classificacoes (uma por arquivo de exemplo)
INSERT INTO classificacoes (arquivo_id, categoria, confianca, data)
SELECT id, categoria, CASE WHEN origem_decisao='regras' THEN 1.0 WHEN origem_decisao='revisao' THEN 0.52 ELSE 0.88 END, criado_em
FROM arquivos
WHERE NOT EXISTS (SELECT 1 FROM classificacoes);

-- auditoria (mover por arquivo de exemplo)
INSERT INTO auditoria (acao, caminho, data)
SELECT 'mover', destino, criado_em FROM arquivos
WHERE NOT EXISTS (SELECT 1 FROM auditoria);

-- ============================================================================
-- CARGA EM VOLUME (Parte 3, secao 3.4 / plano de otimizacao)
-- Gerar N=100k movimentos ficticios com o gerador (dados_ficticios.py),
-- depois importar CSV. Exemplo:
--   .mode csv
--   .import --skip 1 dados/fake_movimentos.csv etapa_carga
--   INSERT OR IGNORE INTO arquivos (hash,origem,destino,categoria,origem_decisao,criado_em)
--     SELECT hash,origem,destino,categoria,origem_decisao,criado_em FROM etapa_carga;
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Carga dos 20 documentos ficticios da base (base-exemplo/): no produto real
-- basta copiar os arquivos para entrada/ e rodar `main.py --once`:
--   .\.venv\Scripts\python.exe main.py --once --dry-run   (ver destino)
--   .\.venv\Scripts\python.exe main.py --once             (executar)
-- ----------------------------------------------------------------------------
