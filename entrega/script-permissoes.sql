-- ============================================================================
-- OrganizaIA - Papeis, GRANT e DENY (SQL Server) - banco-alvo da disciplina
-- Complementa entrega/script-sql-server.sql (DDL + seed).
-- 100% ficticio. Nenhuma senha/chave neste arquivo.
--
-- Execucao (quando houver instancia SQL Server):
--   sqlcmd -S localhost -E -i entrega\script-sql-server.sql
--   sqlcmd -S localhost -E -i entrega\script-permissoes.sql
--
-- Situacao em 16/11/2026: NAO executado nesta maquina (sem instancia SQL
-- Server/LocalDB; SQLCMD presente, servidor ausente). As provas equivalentes
-- no SQLite estao em entrega/evidencias/teste_permissoes.py.
-- ============================================================================

USE OrganizaIA;
GO
SET NOCOUNT ON;
GO

-- ----------------------------------------------------------------------------
-- 1) Views de exposicao minima (a IA/leitor nunca recebem a tabela crua)
--    - arquivos.origem/destino sao "interno" (caminho da maquina)
--    - auditoria e "interno" e fica restrita ao admin
-- ----------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.vw_arquivos_publicos', N'V') IS NOT NULL
    DROP VIEW dbo.vw_arquivos_publicos;
GO
CREATE VIEW dbo.vw_arquivos_publicos
AS
    SELECT hash, categoria, origem_decisao, criado_em
    FROM dbo.arquivos;
GO

IF OBJECT_ID(N'dbo.vw_classificacoes_publicas', N'V') IS NOT NULL
    DROP VIEW dbo.vw_classificacoes_publicas;
GO
CREATE VIEW dbo.vw_classificacoes_publicas
AS
    SELECT c.arquivo_id, c.categoria, c.confianca, c.data
    FROM dbo.classificacoes AS c;
GO

-- ----------------------------------------------------------------------------
-- 2) Papeis (roles) e usuarios de aplicacao (sem login: nao abrem o SSMS)
-- ----------------------------------------------------------------------------
IF DATABASE_PRINCIPAL_ID(N'app_leitor') IS NULL
    CREATE ROLE app_leitor;
IF DATABASE_PRINCIPAL_ID(N'app_ia') IS NULL
    CREATE ROLE app_ia;
IF DATABASE_PRINCIPAL_ID(N'app_admin') IS NULL
    CREATE ROLE app_admin;
GO

IF USER_ID(N'u_leitor') IS NULL
    CREATE USER u_leitor WITHOUT LOGIN;
IF USER_ID(N'u_ia') IS NULL
    CREATE USER u_ia WITHOUT LOGIN;
IF USER_ID(N'u_admin') IS NULL
    CREATE USER u_admin WITHOUT LOGIN;
GO

ALTER ROLE app_leitor ADD MEMBER u_leitor;
ALTER ROLE app_ia    ADD MEMBER u_ia;
ALTER ROLE app_admin ADD MEMBER u_admin;
GO

-- ----------------------------------------------------------------------------
-- 3) DENY explicito nas tabelas (defesa em profundidade)
--    Mesmo que alguem conceda SELECT em dbo.arquivos por engano, o DENY vence.
-- ----------------------------------------------------------------------------
DENY SELECT, INSERT, UPDATE, DELETE ON dbo.arquivos        TO app_leitor, app_ia;
DENY SELECT, INSERT, UPDATE, DELETE ON dbo.classificacoes  TO app_leitor, app_ia;
DENY SELECT, INSERT, UPDATE, DELETE ON dbo.auditoria       TO app_leitor, app_ia;

-- ----------------------------------------------------------------------------
-- 4) GRANT minimo nas views
-- ----------------------------------------------------------------------------
GRANT SELECT ON dbo.vw_arquivos_publicos       TO app_leitor, app_ia;
GRANT SELECT ON dbo.vw_classificacoes_publicas TO app_leitor, app_ia;

-- admin: leitura/escrita completa + auditoria (dono da operacao)
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.arquivos       TO app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.classificacoes TO app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.auditoria      TO app_admin;
GRANT SELECT ON dbo.vw_arquivos_publicos        TO app_admin;
GRANT SELECT ON dbo.vw_classificacoes_publicas  TO app_admin;
GO

-- ============================================================================
-- 5) PROVAS (rode cada bloco; o resultado esperado esta em comentario)
-- ============================================================================

-- PROVA 1 - leitor: acesso PERMITIDO a metadados publicos
EXECUTE AS USER = N'u_leitor';
SELECT TOP (1) hash, categoria FROM dbo.vw_arquivos_publicos;
-- Esperado: 1 linha (ou 0 se a base estiver vazia), sem erro.
REVERT;
GO

-- PROVA 2 - leitor: acesso NEGADO a tabela crua (caminho/origem)
EXECUTE AS USER = N'u_leitor';
SELECT TOP (1) origem, destino FROM dbo.arquivos;
-- Esperado: Msg 229 "The SELECT permission was denied on the object 'arquivos'".
REVERT;
GO

-- PROVA 3 - leitor: acesso NEGADO a auditoria (quem leu o que)
EXECUTE AS USER = N'u_leitor';
SELECT TOP (1) acao, caminho, usuario, data FROM dbo.auditoria;
-- Esperado: Msg 229 "... object 'auditoria'".
REVERT;
GO

-- PROVA 4 - IA: acesso PERMITIDO a metadados e classificacoes
EXECUTE AS USER = N'u_ia';
SELECT TOP (1) hash, categoria FROM dbo.vw_arquivos_publicos;
SELECT TOP (1) categoria, confianca FROM dbo.vw_classificacoes_publicas;
-- Esperado: sem erro.
REVERT;
GO

-- PROVA 5 - IA: escrita NEGADA (mesmo em tabela publica)
EXECUTE AS USER = N'u_ia';
INSERT INTO dbo.arquivos (hash, origem, destino, categoria, origem_decisao, criado_em)
VALUES (REPLICATE('f', 64), N'entrada/x.txt', N'organizados/x.txt',
        N'Outros', N'ia', SYSDATETIME());
-- Esperado: Msg 229 "The INSERT permission was denied ...".
REVERT;
GO

-- PROVA 6 - IA: auditoria NEGADA
EXECUTE AS USER = N'u_ia';
SELECT TOP (1) * FROM dbo.auditoria;
-- Esperado: Msg 229.
REVERT;
GO

-- PROVA 7 - admin: auditoria PERMITIDA (consulta de conformidade)
EXECUTE AS USER = N'u_admin';
SELECT TOP (5) acao, caminho, usuario, data
FROM dbo.auditoria ORDER BY id DESC;
-- Esperado: ate 5 linhas, sem erro.
REVERT;
GO
