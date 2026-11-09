"""Metadados internos. Identificadores SQL vêm exclusivamente deste arquivo."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Campo:
    nome: str
    rotulo: str
    tipo: str = 'texto'
    obrigatorio: bool = True
    opcoes: tuple = ()
    limite: int = 100


SITUACOES = (('em_andamento', 'Em andamento'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado'))
TIPOS = (('discente', 'Discente'), ('docente', 'Docente'), ('tec_adm', 'Técnico-administrativo'))
FUNCOES = (('colaborador', 'Colaborador'), ('bolsista', 'Bolsista'), ('coordenador', 'Coordenador'))
AGENCIAS = (('capes', 'CAPES'), ('fapes', 'FAPES'), ('cnpq', 'CNPq'), ('finep', 'FINEP'))
FOMENTOS = (('bolsa', 'Bolsa'), ('auxilio', 'Auxílio'), ('convenio', 'Convênio'))
PRODUCOES = (('artigo', 'Artigo'), ('cap_livro', 'Capítulo de livro'), ('software', 'Software'), ('relatorio_tecnico', 'Relatório técnico'), ('patente', 'Patente'))
MEIOS = (('revista', 'Revista'), ('congresso', 'Congresso'), ('repositorio', 'Repositório'))

MODELOS = {
 'projetos': dict(tabela='projeto', pk=('codigo_projeto',), titulo='Gestão de Projetos de Pesquisa', subtitulo='Cronograma, objetivos e coordenação dos projetos de pesquisa.', singular='Projeto',
 campos=[Campo('codigo_projeto','Código do projeto','inteiro'),Campo('titulo','Título do projeto'),Campo('descricao','Descrição resumida','multilinha',False,limite=300),Campo('data_inicio','Data de início','data'),Campo('data_termino','Data de término','data',False),Campo('situacao','Situação operacional','opcao',opcoes=SITUACOES),Campo('coordenador','Coordenador responsável','docente')],
 colunas=[('codigo_projeto','Código',75),('titulo','Projeto / resumo',260),('coordenacao','Coordenação',190),('data_inicio','Início',100),('data_termino','Término',100),('situacao','Situação',130)]),
 'participantes': dict(tabela='participante',pk=('cpf',),titulo='Gestão de Participantes',subtitulo='Pesquisadores, docentes, discentes e colaboradores da equipe.',singular='Participante',
 campos=[Campo('nome','Nome completo'),Campo('email','E-mail institucional'),Campo('cpf','CPF','cpf'),Campo('tipo_participante','Tipo de participante','opcao',opcoes=TIPOS),Campo('projeto','Projeto vinculado','projeto',False),Campo('funcao','Função no projeto','opcao',False,FUNCOES),Campo('inicio','Início do vínculo','data',False),Campo('fim','Término do vínculo','data',False)],
 colunas=[('nome','Participante',210),('email','E-mail',220),('cpf','CPF',130),('tipo_participante','Tipo',140),('projetos','Projetos / função / vigência',420)]),
 'financiamentos': dict(tabela='financiamento',pk=('codigo_financiamento',),titulo='Gestão de Financiamentos',subtitulo='Recursos, auxílios e bolsas vinculados aos projetos de pesquisa.',singular='Financiamento',
 campos=[Campo('codigo_financiamento','Código do financiamento','inteiro'),Campo('agencia_financiadora','Agência financiadora','opcao',opcoes=AGENCIAS),Campo('tipo_fomento','Tipo de fomento','opcao',opcoes=FOMENTOS),Campo('valor_total','Valor total (R$)','dinheiro'),Campo('data_inicio','Vigência: início','data'),Campo('data_termino','Vigência: término','data')],
 colunas=[('codigo_financiamento','Código',80),('agencia_financiadora','Agência',120),('tipo_fomento','Fomento',110),('projetos','Projetos apoiados',270),('valor_total','Valor total',150),('data_inicio','Início',110),('data_termino','Término',110)]),
 'producoes': dict(tabela='producao_cientifica',pk=('codigo_projeto','codigo_prod'),titulo='Gestão de Produções Científicas',subtitulo='Artigos, capítulos, patentes, softwares e relatórios da pesquisa.',singular='Produção',
 campos=[Campo('codigo_projeto','Projeto vinculado','projeto'),Campo('codigo_prod','Código da produção (dentro do projeto)','inteiro'),Campo('titulo','Título da produção'),Campo('tipo_prod','Tipo de produção','opcao',opcoes=PRODUCOES),Campo('ano_publicacao','Ano de publicação','ano'),Campo('meio_divulgacao','Categoria do meio','opcao',opcoes=MEIOS),Campo('veiculo','Periódico / evento / veículo','texto',False,limite=200),Campo('identificador','DOI / registro','texto',False,limite=200),Campo('autores','Autores do projeto','autores')],
 colunas=[('codigo_prod','Código',80),('titulo','Título',280),('tipo_prod','Tipo',160),('ano_publicacao','Ano',70),('veiculo','Veículo',220),('identificador','DOI / registro',200),('projeto_titulo','Projeto',200),('autores_nomes','Autores',250)]),
 'vinculos': dict(tabela='vinculo_projeto_participante',pk=('codigo_projeto','cpf'),titulo='Vincular Participantes em Projetos',subtitulo='Papéis acadêmicos, vigência, carga semanal e plano de trabalho.',singular='Vínculo',
 campos=[Campo('codigo_projeto','Projeto de pesquisa','projeto'),Campo('cpf','Participante / pesquisador','participante'),Campo('funcao_desempenhada','Função / papel acadêmico','opcao',opcoes=FUNCOES),Campo('carga_semanal','Carga semanal (horas)','horas'),Campo('fomento','Fomento / bolsa','texto',False,limite=100),Campo('data_entrada','Início do vínculo','data'),Campo('data_saida','Término do vínculo','data',False),Campo('plano_trabalho','Plano de trabalho / atividades','multilinha',False,limite=2000)],
 colunas=[('projeto_titulo','Projeto',220),('participante_nome','Participante',200),('cpf','CPF',130),('funcao_desempenhada','Função',130),('fomento','Fomento',140),('carga_semanal','Horas/sem',90),('data_entrada','Início',110),('data_saida','Término',110)]),
 'alocacoes': dict(tabela='vinculo_projeto_financiamento',pk=('codigo_projeto','codigo_financiamento'),titulo='Recursos destinados aos projetos',subtitulo='Um financiamento pode apoiar vários projetos. O total destinado respeita o contrato.',singular='Destinação',
 campos=[Campo('codigo_projeto','Projeto apoiado','projeto'),Campo('codigo_financiamento','Financiamento','financiamento'),Campo('valor_destinado','Valor destinado (R$)','dinheiro')],
 colunas=[('projeto_titulo','Projeto',300),('codigo_financiamento','Contrato',100),('agencia_financiadora','Agência',140),('valor_destinado','Valor destinado',180)])
}
