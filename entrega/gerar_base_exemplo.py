# -*- coding: utf-8 -*-
"""Gera entrega/base-exemplo/ com 20 documentos 100% FICTICIOS (arquivo .txt).

Uso: .\\.venv\\Scripts\\python.exe entrega\\gerar_base_exemplo.py
Dados inventados apenas para o trabalho: nomes, CPFs, valores e e-mails
de exemplo (nunca sao dados reais). Marca de ficcao no topo de cada arquivo.
"""
from pathlib import Path

MARCA = "DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real."
SAIDA = Path(__file__).resolve().parent / "base-exemplo"

DOCS = {
"fatura-luz-2026-03.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
COMPANHIA DE ENERGIA EXEMPLO S.A.
FATURA DE ENERGIA ELETRICA - REF. MARCO/2026

Instalacao (exemplo): 000000000-0
Cliente: MARIA SOARES FICTICIA
CPF/CNPJ: 000.000.000-00
Endereco: Rua Ficticia das Palmeiras, 120 - Apto 302
Bairro: Jardim Exemplo - Cidade Demo - CEP 00000-000

Vencimento: 20/03/2026
Valor total: R$ 184,73

Resumo do consumo:
- Leitura anterior: 04/02/2026   kwh: 1250
- Leitura atual:    03/03/2026   kwh: 1394
- Consumo do mes: 144 kwh
- Media diaria de consumo: 4,64 kwh

Itens de cobranca:
- Energia consumida (144 kwh): R$ 152,10
- Iluminacao publica: R$ 9,85
- Bandeira vermelha: R$ 22,78

Codigo de barras (inventado): 00000.00000 00000.000000 00000.000000 0 00000000000000

Situacao: NAO CANCELADA (exemplo de classificacao: categoria Faturas).
Este texto e usado como base ficticia do trabalho OrganizaIA.""",

"contrato_aluguel_2025.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
CONTRATO DE LOCACAO RESIDENCIAL (MODELO PARA TRABALHO ACADEMICO)

Locador: JOAO PINTO FICTICIO, CPF 111.111.111-11.
Locataria: MARIA SOARES FICTICIA, CPF 000.000.000-00.

CLAUSULA 1 - OBJETO: o imovel na Rua Ficticia das Palmeiras, 120,
apto 302, destina-se a residencia exclusiva da locataria.

CLAUSULA 2 - PRAZO: 30 meses a contar de 01/02/2025.

CLAUSULA 3 - ALUGUEL: R$ 1.350,00 (um mil e trezentos e cinquenta reais)
mensais, vencendo todo dia 10, incluindo condominio basico.

CLAUSULA 4 - GARANTIA: caução de R$ 2.700,00 depositada em conta exemplo.

CLAUSULA 5 - REAJUSTE: aplicado o indice IPCA plausivel de dezembro,
limitado a 8% a.a.

CLAUSULA 6 - SOLTEIAR: vedado sublocação.

Foro: cidade de Demo. Assinado em duas vias inventadas.
Assinado ficticiamente por JOAO PINTO FICTICIO e MARIA SOARES FICTICIA.
Categoria para classificação do trabalho: Trabalho / Documentos.""",

"boleto_escola_exemplo.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
COLlegio DEMO Ltda.
BOLETO DE MENSALIDADE ESCOLAR - MARCO/2026

Aluno: PEDRO FICTICIO SOARES    Turma: 6 ano   Matricula: 000000
Responsavel: MARIA SOARES FICTICIA (CPF 000.000.000-00)
E-mail de contato: nao-responda@exemplo.com

Item: Mensalidade escolar
Valor: R$ 480,00
Vencimento: 10/03/2026
Desconto por pontualidade: R$ 24,00 (ate o dia 07)
Valor com desconto: R$ 456,00

Onde pagar: qualquer banco, lotérica ou aplicativo do banco exemplo.
Segunda via: secretaria virtual (exemplo).

Avisos da escola (exemplo):
- Lembrete de reuniao de pais em 20/03.
- Prazo de entrega de lista de material: 15/03.
- Nao esqueça钱 o uniforme dos meses de frio.

Este boleto existe apenas para treinar classificación (categoria Faturas).""",

"holerite_exemplo_ana.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
FOLHA DE PAGAMENTO (ADMINISTRADORA EXEMPLO ME)
Referência: fevereiro/2026          Empregada: ANA FICTICIA SOUZA
Cargo: secretaria assistente        CPF: 222.222.222-22
CTPS ficticia: 000000-00            Admissão: 03/03/2024

PROVENTOS
Salario base:                 R$ 2.450,00
Hora extra 50% (4h):          R$ 132,00
Adicional noturno:            R$ 68,00
Total de provementos:         R$ 2.650,00

DESCONTOS
INSS (tabela ficticia):       R$ 240,75
IRRF:                         R$ 35,40
Vale transporte (6%):         R$ 76,00
Plano de saude (exemplo):     R$ 95,00
Total de descontos:           R$ 447,15

LIQUIDO A RECEBER:            R$ 2.202,85

Deposito em conta exemple 0000-0 ag 00000-9 conta 00000000-0.
Base FGTS: R$ 2.650,00    FGTS do mes: R$ 212,00
Doc recebido por e-mail inventado em 05/03/2026.""",

"nota_fiscal_padaria.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
PADARIA DO BAIRRO DEMO - CNPJ inventado 00.000.000/0001-00
NOTA FISCAL SIMPLIFICADA = DOCUMENTO FICTICIO DE TREINO

Consumidor: MARIA SOARES FICTICIA (CPF na nota: nao informado)
Data: 12/03/2026 14:32          Cupom: 999000

Itens:
- Pao frances 1/2 kg ............ R$ 9,80
- Bolo de cenoura fatia ........ R$ 8,50
- Cafe coado grande ............ R$ 6,00
- Leite integral caixa ......... R$ 5,20
- Queijo mussarela 150 g ....... R$ 12,90
- Sabonete liquido 250 ml ...... R$ 7,50

Total itens: 6                  Subtotal: R$ 49,90
Desconto fidelidade:            R$ 2,00
TOTAL: R$ 47,90                 Pagamento: cartao de debito

Codigo de cupom inventado: 2026-03-12-999000000
Autorizacao da operadora (inventada): 00/0000000

Guardado por tres meses (cliente ficticio).""",

"plano_estudos_eng.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
PLANO DE ESTUDOS - MATEMATICA/ENGENHARIA (exemplo do trabalho NORg)
Periodo: 01 de marco a 30 de abril de 2026 - Aluno demo [];

Meta: avancar 3 capitulos de calculo e 2 de algebra linear por mes.

SEGUNDA (90 min): derivadas - exercicios par/impares.
TERCA  (60 min): revisão de limites + correção de duvidas no caderno.
QUARTA (90 min): integrais por partes; lista dos professores demo.
QUINTA (60 min): algebra linear - matrizes e determinos.
SEXTA  (90 min): simulado de 10 questoes com gabarito.
SABADO (2h): projeto do curso - exercicios de programa aplicada.

Recursos:
- Apostila exemplo alpha (PDF ficticio).
- Playlist "calculo para eng demo" (link inventado).
- Fichas de formula criadas por mim (exemplo).

Ordem do dia: 5 min revisao de formula; 60 min exercicio; 25 min correcao.
Recompensa semanal: sexta a noite livre se cumprir 5/6 dias."""
,
"resumo_curso_sql.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
RESUMO - CURSO DE SQL PROFISSIONAL (aulas 1 a 8, versao estudante)

Aula 1: SELECT basico. SELECT coluna, coluna2 FROM tabela WHERE filtro;
Aula 2: funcoes de agregacao (COUNT, SUM, AVG) e GROUP BY sem HAVING.
Aula 3: JOINs. INNER JOIN cruza o que existe nas duas; LEFT JOIN mantem da esquerda.
Aula 4: subconsultas; cuidado com correlacionada (custo alto).
Aula 5: indices B-tree: ajudam em WHERE/ORDER BY; LIKE '%x%' os ignora.
Aula 6: transacoes: BEGIN, COMMIT, ROLLBACK; niveis de isolamento.
Aula 7: normalização 1FN, 2FN, 3FN, com exemplo de tabela de pedidos.
Aula 8: planos de execucao - EXPLAIN QUERY PLAN no SQLite; SET STATISTICS TIME no SQL Server.

Dica do professor demo: medir ANTES e DEPOIS da otimizacao, nunca confiar
na intuicao. Colocar 100 mil linhas ficticias e ver o plano de execucao.

Erros clássicos apresentados: confiar em OR sem indice; usar OR de colunas
sem indice; esquecer de COMMIT; usar LIKE sem escape de % e _.""",

"carta_banco_exemplo.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
BANCO EXEMPLO S.A.
Aviso de pendencia (carta inventada, fim didatico)

Ref.: Agência 0000-0 - Conta 00000000-0
Cliente: MARIA SOARES FICTICIA - CPF 000.000.000-00

Prezada cliente,

Detectamos em nossos sistemas de exemplo uma movimentacao incomum
nesta conta nos dias 10 e 11 de marco de 2026.

Orientamos (procedimento inventado para o trabalho):
1. Acessar o aplicativo (versão demo) e validar os ultimos lançamentos.
2. Caso reconheça todos, dispensamos contato.
3. Caso NÃO reconheca, ligar para o telefone ficticio 0000-000-0000.

Registramos taxa de servico ajustada: anuidade do cartao exemplo
inciando em R$ 0,00 nos 90 dias de demonstracao.

Atenciosamente, direçãokosten do Banco Exemplo.
Este documento foi criado somente para treinar classificação de Pessoal.""",

"lista_compras.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
LISTA DE COMPRAS DA SEMANA (exemplo criado pelo trabalho)

- arroz 5 kg
- feijao 2 pacotes
- cafe 500 g
- leite 6 caixas
- macarrao integral
- tomate 1 kg
- cebola 1 kg
- alho maior
- papel higienico 12 rolos
- detergente 2
- sabonete 4
- pilha AA (4)
- remédio de dor de cabeca (exemplo generico)
- pao de forma
- ovos 1 bandeja
- fralda (não usar exemplo)          [cut]
- bateria AAA (2)
- farinha de trigo 1 kg

Restricoes da casa demo: nenhum alimento com amendoa.
Orçamento alvo: R$ 420,00 (max R$ 450).
Compreido dia: sábado pela manha antes das 10.
""",

"exercicios_sql_basico.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
EXERCICIOS DE SQL NIVEL BASICO (lista inventada para o Estudos)

Tabelas de treino (esquema exemplo):
  alunos(id, nome, matricula)
  notas(id, aluno_id, disciplina, valor)
  cursos(id, nome, carga_horaria)

1) Liste todos os alunos ordenados por nome.
2) Conte quantas notas existem por disciplina.
3) Mostre a media das notas por aluno acima de 7.
4) Encontre alunos sem nota alguma (LEFT JOIN + IS NULL).
5) Liste alunos e suas disciplinas com INNER JOIN.
6) Insira 3 alunos fake com VALUES e depois ALTERE o nome de um deles.
7) DELETE as notas abaixo de 3 (dentro de transacao com ROLLBACK).
8) Crie indice em notas(aluno_id) e compare EXPLAIN QUERY PLAN.
9) Monte consulta com GROUP BY e HAVING que lista disciplinas com media >= 8.
10) Escreva consulta parametrizada no formato: WHERE nome = ? (dica do professor).

Entrega: arquivo .txt com suas queries, sem dados reais.
Dica da corretora demo: use tabelas pequenas primeiro.""",

"fatura-agua-2026-02.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
CIA DE AGUA DEMO
FATURA DE AGUA E ESGOTO - REFERENCIA FEVEREIRO/2026

Instalacao exemplo: 24500000000-1
Cliente: MARIA SOARES FICTICIA - CPF 000.000.000-00
Endereco: Rua Ficticia das Palmeiras, 120, Apto 302 - CEP 00000-000

Volume consumido: 11 m3
Tarifa de agua (11 m3):          R$ 68,75
Servico de esgoto (60%):         R$ 41,25
Contribuo municipal:             R$ 3,20
TOTAL:                           R$ 113,20
Vencimento: 15/03/2026

Historico ficticio (m3): 12 - 10 - 13 - 11 - 9 - 11
Media dos ultimos 6 meses: 11,0 m3

Cd de barras (inventado): 8 00000000 00000000 00000000 0 000
Codigo da fatura: DEMO-2026-02-000111

Emissao: 01/03/2026 via site exemplo.""",

"recibo-pintura-apartamento.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
RECIBO DE SERVICO SIMPLES (MODELO DE TREINO - TUDO INVENTADO)

Recebemos de MARIA SOARES FICTICIA (CPF 000.000.000-00)
a importancia de R$ 890,00 (oitocentos e noventa reais)
referente a pintura do apartamento demo, endereco ficticio:
Rua Ficticia das Palmeiras, 120 - Apto 302.

Servicos prestado (inventados para treinar classificação Trabalho):
- massa corrida em 2 paredes da sala
- pintura acrilica da sala e 2 quartos (tecto)
- retoque de rodapes (3 pecas)

Executado nos dias 18 a 21 de fevereiro de 2026.
Sem riscos de garantia de materiais (termo exemplo).

Prestador: JOSE TINTAS DEMO - CPF 333.333.333-33 (inventado)
Assinado ficticiamente em duas vias.

Obs: documento criado apenas para teste do organizador OrganizaIA.""",

"cronograma-tcc-redes.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
CRONOGRAMA DE TCC (EXEMPLO) - CURSO DE REDES DE COMPUTADORES
Aluno demo []	                Orientador ficticio: Prof. demo

Entregas do semestre 2026-1 (datas inventadas):
04/03 - Definicao do tema e bibliografia inicial (8 referencias fake).
11/03 - Proposta de metodologia (1 pagina).
18/03 - Revisao 1: estrutura de capitulos aprovada (orientador demo).
25/03 - Coleta de dados de laboratorio (pt1) - switch household.
01/04 - Resultados parciais (graficos de latencia exemplo).
15/04 - Revisao 2: escrito completo do capitulo 2.
29/04 - Banco de dados da simulação ok.
13/05 - Revisao 3 final com corretor externo.
20/05 - Impresao + entrega eletrónica na secretaria demo.
27/05 - Defesa publica (sala demo, banca de 3).

Riscos mapeados (exemplo): falha de laboratorio; atraso no revisor.
Plano B: simulador gratuito de rede para reproducir dados fake.""",

"receita-bolo-cenoura.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
RECEITA (EXEMPLO) - BOLO DE CENOURA DA CASA DEMO
Rendimento: 12 fatias   Tempo: 50 minutos (inventado)

Massa:
- 3 cenouras medias (aprox 400 g) picadas
- 3 ovos (exemplo)
- 1 xicara de oleo
- 2 xicaras de acucar
- 2 xicaras de farinha de trigo
- 1 colher (sopa) de fermento em po

Modo:
1) Bata no liqueficador as cenouras com os ovos e o oleo.
2) Despeje numa bacia, misture acucar e farinha.
3) Por ultimo o fermento, sem bater.
4) Forma untada, forno demo a 180 C por uns 40 min (teste do palito).

Cobertura (opcional):
- 1 lata de leite condensado exemplo
- 2 colheres de copidigital do cacau
- 1 colher de manteiga
Leve ao fogo baixo ate desgrudar, sem chiado (dica demo).

Nota inventor: receita fictícia criada para o trabalho OrganizaIA.""",

"apontamentos-python-aula5.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
APONTAMENTOS DA AULA 5 - INTRODUCAO A PYTHON (professor demo)

Tema da aula: funcoes e coleções.

def saudacao(nome):
    return "Ola, " + nome  # exemplo

listas (mutáveis) x tuplas (imutáveis).
dicionario: { "chave": valor } - acesso por chave, O(1) na media.
set: sem duplicados, boa para deduplicar (assim como o sha256 do projeto!).

Funcoes utis mostradas na aula (exemplos):
- sorted(lista, reverse=True)
- "".join(pedacos)
- enumerate / zip

Exercicio da aula demo: escreveral funcao que soma so os pares de uma lista.

Erro da aula anterior corrigido: esquecer o "return" faz a funcao
devolver None (silencioso e comum).

Para a prova: saberei explicar diferença de list(set()) vs set().""",

"contrato-prestacao-servicos.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
CONTRATO DE PRESTACAO DE SERVICOS INTELIGENTES (MODELO FICTICIO)

CONTRATANTE: Maria Soares Ficticia, CPF 000.000.000-00.
CONTRATADO: Analista demo Ltda. (CNPJ inventado 00.000.000/0002-00).

CL 1 - OBJETO: formalização de 12 horas mensais de consultoria de
dados para o trabalho OrganizaIA (escopo exempolo).

CL 2 - VALOR: R$ 1.800,00/mes, boleto vence dia 5.
Houras extra: R$ 90,00/h, somadas na fatura seguinte (teto 10 h).

CL 3 - VIGENCIA: 01/03/2026 a 28/02/2027 (renovação automática fictional).

CL 4 - CONFIDENCIALIDADE: as informacoes trocadas sao de teste;
nin guma informacao real e utilizada neste tramite.

CL 5 - RESCISAO: 30 dias de aviso previo.

Assinaturas ficticias das duas partes em cidade demo.
Esse contrato demonstra a caategorira Trabalho no organizador.""",

"fatura-internet-2026-01.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
PROVEDOR INTERNET DEMO
FATURA DE SERVIÇO - JANEIRO/2026 (documento inventado)

Cliente: Maria Soares Ficticia  -  Codigo: 0000000-0
Plano: Fibra 300 Mega (exemplo) - R$ 99,90/mes
Vencimento: 05/02/2026

Detalhes:
- Servico base 300 mega ......................... R$ 89,90
- Instalacao parcela 1/3 ........................ R$ 20,00
- Fi extra bonus (promocional) .................. -R$ 10,00
- Modem alido já inclui nível
TOTAL: R$ 99,90     Fidelidade restante: 12 meses (inventada)

Suporte: 0000 000 0000 (plausibilidade)  chat no site demo.

Historico simplificado (meses ficticios):
Jan: R$ 99,90 | Dez: R$ 89,90 | Nov: R$ 89,90

Este arquivo treina a classe "Faturas" no OrganizaIA.""",

"checklist-mudanca-apartamento.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
CHECKLIST DE MUDANÇA (exemplo inventado) - Trabalho OrganizaIA

Antes do dia (1 semana):
[ ] pedir orcamento de 3 transportadoras demo
[ ] agendar dia de recolha de fumos (feira exemplo)
[ ] reservar caixas (20 grandes, 10 medianas)

Na semana:
[ ] embalar livros: 2 caixas medianas
[ ] utensilios de cozinha: 3 caixas grandes
[ ] roupas: sacolas + malas demo
[ ] marcar desligamento da internet na residência antiga (dia 30)

No dia:
[ ] conferir caixa por caixa com lista impressa
[ ] tirar foto de contadores (água e luz demo)
[ ] entregar chaves ao sindico exemplo

Depois:
[ ] trocar endereço no banco demo
[ ] atualizar cadastro da escola exemplo
[ ] comprar luminária nova para sala (R$ alocação fake)

Tudo ficticio, para treinar categoria Outros/Trabalho.""",

"resenha-livro-sapiens.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
RESENHA ESCOLAR (EXEMPLO CRIADO PARA O TRABALHO) - livro demo do genero história

1) Contexto: o livro demo descreve a "revolucao cognitiva" de uma
sociedade de exemplo, abordando como as narrativas coletivas organizam grupos.

2) Ponto forte da minha leitura:
- mostra mudanca de escala (bando -> cidade -> estado demo);
- bom para introducao de aula de sociologia com turma fake do 9o ano.

3) Limitaco Wahrnehmong:
- generaliza periodos inteiros sem sempre mostrar fontes;
- navegacao por capitulos demo podia ter mais dados.

4) Frases marcadoras (aproximadas, do demo):
- "a maior parte do poder veio das historias que contamos entre nos".

5) Para que usar: intro de seminario; comparar com outro livro demo da lista.

Recomendo 7/10 para o conteudo didático (avaliação ficticia minha).""",

"roteiro-viagem-ferias.txt": """DOCUMENTO FICTICIO - gerado para o trabalho, nenhuma relevancia real.
ROTEIRO DE VIAGEM (EXEMPLO) - ferias demo, cidade de exemplo

DIA 1 - chegada
- voo demonstrativo chegadas 14:00 (aeroporto demo)
- check-in pousada exemplo (reserva ficticia 000000)
- jantar na praca central da cidade demo

DIA 2 - passeios
- museu demo das manhas (entrada R$ 20 fake)
- mercado local (compras: queijo demo, mel demo)
- tarde livre na orla exemplo

DIA 3 - dia no parque
- trilha leve de 4 km (guia demo)
- cachoeira exemplo (levar agua e calçado demo)

DIA 4 - despedida
- cafe da manha demo
- voo ficticio de volta as 18:10

Budurgeto total inventado: R$ 2.300,00
Estimativa por item: passagem R$ 900; hospedagem R$ 850; tours R$ 300;
resto R$ 250 (alimentacao e extras).

Todos nomes, valores e lugares sao para teste de classificação Outros.""",
}

def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    for nome, conteudo in DOCS.items():
        texto = conteudo if conteudo.lstrip().startswith("DOCUMENTO FICTICIO") else MARCA + "\n" + conteudo
        # garante unico marcador no topo
        if not texto.lstrip().startswith("DOCUMENTO FICTICIO"):
            texto = MARCA + "\n" + texto
        (SAIDA / nome).write_text(texto.replace("[cut]", "").replace("钱", "").replace("中美", "").replace("中美", ""), encoding="utf-8")
    print(f"OK: {len(DOCS)} documentos ficticios em {SAIDA}")

if __name__ == "__main__":
    main()
