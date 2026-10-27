-- ============================================================================
-- OrganizaIA - Script T-SQL (SQL Server) - banco-alvo da disciplina
-- 100% ficticio: hashes sao placeholders, nomes/valores de exemplo.
-- Politica do projeto: consulte sempre via comandos parametrizados
-- (@hash, @destino...) - este script e apenas DDL + seed.
-- Rodar no SSMS: sqlcmd -S localhost -d master -E -i entrega\script-sql-server.sql
-- ============================================================================

IF DB_ID(N'OrganizaIA') IS NULL
    CREATE DATABASE OrganizaIA;
GO
USE OrganizaIA;
GO

-- ----------------------------------------------------------------------------
-- Tabelas equivalentes ao SQLite de src/repositorio.py
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.arquivos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.arquivos (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        hash            NVARCHAR(64)  NOT NULL UNIQUE,   -- sha256 (publico)
        origem          NVARCHAR(400) NOT NULL,          -- interno
        destino         NVARCHAR(400) NOT NULL,          -- interno
        categoria       NVARCHAR(30)  NULL,              -- publico (lista fechada)
        origem_decisao  NVARCHAR(15)  NOT NULL
            CONSTRAINT CK_arquivos_decisao
                CHECK (origem_decisao IN (N'regras', N'ia', N'duplicata', N'revisao')),
        criado_em       DATETIME2(0)  NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.classificacoes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.classificacoes (
        id          INT IDENTITY(1,1) PRIMARY KEY,
        arquivo_id  INT NOT NULL
            CONSTRAINT FK_class_arquivo FOREIGN KEY REFERENCES dbo.arquivos(id),
        categoria   NVARCHAR(30) NOT NULL,
        confianca   FLOAT        NOT NULL
            CONSTRAINT CK_class_conf CHECK (confianca BETWEEN 0.0 AND 1.0),
        data        DATETIME2(0) NOT NULL
    );
END;
GO

IF OBJECT_ID(N'dbo.auditoria', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.auditoria (
        id      INT IDENTITY(1,1) PRIMARY KEY,
        acao    NVARCHAR(30)  NOT NULL,
        caminho NVARCHAR(400) NOT NULL,
        data    DATETIME2(0)  NOT NULL DEFAULT SYSDATETIME()
    );
END;
GO

-- ----------------------------------------------------------------------------
-- Indices (inclui a OTIMIZACAO 2: auditoria.caminho - Parte 3, secao 3.4)
-- ----------------------------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_arquivos_destino')
    CREATE INDEX IX_arquivos_destino ON dbo.arquivos(destino);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_arquivos_categoria')
    CREATE INDEX IX_arquivos_categoria ON dbo.arquivos(categoria);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_classificacoes_arquivo')
    CREATE INDEX IX_classificacoes_arquivo ON dbo.classificacoes(arquivo_id);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_auditoria_caminho')
    CREATE INDEX IX_auditoria_caminho ON dbo.auditoria(caminho, data);
GO

-- ----------------------------------------------------------------------------
-- SEED: 10 registros ficticios (hash placeholder único, dados inventados)
-- ----------------------------------------------------------------------------
INSERT INTO dbo.arquivos (hash, origem, destino, categoria, origem_decisao, criado_em) VALUES
(N'0a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9', N'entrada/fatura-luz-2026-03.txt',   N'organizados/Textos/Faturas/fatura-luz-2026-03.txt',      N'Faturas',  N'ia',       '2026-03-05T14:22:01'),
(N'1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a', N'entrada/contrato_aluguel_2025.txt',N'organizados/Documentos/Trabalho/contrato_aluguel_2025.txt', N'Trabalho', N'ia',       '2026-03-06T09:10:00'),
(N'2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b', N'entrada/boleto_escola_exemplo.txt',N'organizados/Textos/Faturas/boleto_escola_exemplo.txt',    N'Faturas',  N'ia',       '2026-03-07T11:45:12'),
(N'3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c', N'entrada/holerite_exemplo_ana.txt', N'organizados/Documentos/Trabalho/holerite_exemplo_ana.txt', N'Trabalho', N'revisao',  '2026-03-08T16:30:44'),
(N'4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d', N'entrada/nota_fiscal_padaria.txt',  N'organizados/Textos/Faturas/nota_fiscal_padaria.txt',      N'Faturas',  N'ia',       '2026-03-10T08:05:02'),
(N'5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e', N'entrada/plano_estudos_eng.txt',    N'organizados/Textos/Estudos/plano_estudos_eng.txt',        N'Estudos',  N'ia',       '2026-03-11T19:00:36'),
(N'60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f', N'entrada/resumo_curso_sql.txt',     N'organizados/Textos/Estudos/resumo_curso_sql.txt',         N'Estudos',  N'regras',   '2026-03-12T07:55:00'),
(N'718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60', N'entrada/carta_banco_exemplo.txt',  N'organizados/Documentos/Pessoal/carta_banco_exemplo.txt',  N'Pessoal',  N'revisao',  '2026-03-13T13:24:59'),
(N'8293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f607',  N'entrada/lista_compras.txt',        N'organizados/Textos/Outros/lista_compras.txt',             N'Outros',   N'regras',   '2026-03-14T18:47:03'),
(N'93a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718',  N'entrada/exercicios_sql_basico.txt', N'organizados/Textos/Estudos/exercicios_sql_basico.txt',    N'Estudos',  N'ia',       '2026-03-15T10:12:00');
GO

INSERT INTO dbo.classificacoes (arquivo_id, categoria, confianca, data)
SELECT a.id, a.categoria,
       CASE a.origem_decisao WHEN N'regras' THEN 1.0 WHEN N'revisao' THEN 0.52 ELSE 0.88 END,
       a.criado_em
FROM dbo.arquivos a
WHERE NOT EXISTS (SELECT 1 FROM dbo.classificacoes c WHERE c.arquivo_id = a.id);
GO

INSERT INTO dbo.auditoria (acao, caminho, data)
SELECT N'mover', a.destino, a.criado_em
FROM dbo.arquivos a
WHERE NOT EXISTS (SELECT 1 FROM dbo.auditoria au WHERE au.caminho = a.destino);
GO

-- ----------------------------------------------------------------------------
-- Carga de VOLUME para o plano de otimizacao (100k movimentos ficticios)
-- 1) gerar CSV:  .\.venv\Scripts\python.exe entrega\gerar_volume.py --linhas 100000 --saida dados\fake_movimentos.csv
--    (gerador dedicado: hashes sha256 falsos + caminhos plausíveis fictícios)
-- 2) carregar em massa (comentado para nao rodar acidentalmente):
--
-- BULK INSERT dbo.arquivos
-- FROM 'C:\caminho\dados\fake_movimentos.csv'
-- WITH (
--     FORMAT = 'CSV',
--     FIRSTROW = 2,
--     FIELDTERMINATOR = ',',
--     ROWTERMINATOR = '\n',
--     CODEPAGE = '65001',
--     TABLOCK
-- );
-- GO
--
-- 3) medir antes/depois da OTIMIZACAO 1 (LIKE '%x%' -> FTS / ninho de indice):
-- SET STATISTICS TIME ON;
-- SELECT * FROM dbo.arquivos WHERE destino LIKE N'%fatura%' ORDER BY destino;
-- SET STATISTICS TIME OFF;
--
-- 4) plano da consulta (equivalente do EXPLAIN QUERY PLAN):
-- SET STATISTICS PROFILE ON;
-- SELECT a.*, c.categoria AS classificacao_recente
-- FROM dbo.arquivos a
-- LEFT JOIN dbo.classificacoes c ON c.arquivo_id = a.id
-- WHERE a.destino = N'organizados/Textos/Faturas/x.txt'
--    OR a.destino = N'organizados/Textos/Estudos/x.txt';
-- SET STATISTICS PROFILE OFF;
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- CONSULTAS de exemplo (sempre parametrizadas na aplicação):
--   EXEC sp_executesql N'SELECT * FROM dbo.arquivos WHERE destino = @d', N'@d nvarchar(400)', @d = @destino;
--   EXEC sp_executesql N'SELECT ... FROM dbo.arquivos WHERE destino LIKE @t', N'@t nvarchar(400)', @t = N'%' + @termo + N'%';
-- ----------------------------------------------------------------------------
