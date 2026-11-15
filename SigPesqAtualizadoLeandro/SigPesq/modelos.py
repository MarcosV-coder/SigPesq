"""Somente os campos das seis tabelas originais e a senha de participante."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Campo:
    nome: str
    rotulo: str
    tipo: str = 'texto'
    obrigatorio: bool = True
    opcoes: tuple = ()
    limite: int = 100

def enum(*labels): return tuple(enumerate(labels, 1))
SITUACOES=enum('Em andamento','Concluído','Cancelado')
TIPOS=enum('Discente','Docente','Técnico-administrativo')
FUNCOES=enum('Colaborador','Bolsista','Coordenador')
AGENCIAS=enum('CAPES','FAPES','CNPq')
FOMENTOS=enum('Bolsa','Auxílio','Convênio')
PRODUCOES=enum('Artigo','Capítulo de livro','Software','Relatório técnico')
MEIOS=enum('Revista','Congresso','Repositório')
C=Campo
def O(n,r,o): return C(n,r,'opcao',opcoes=o)
MODELOS={
'projetos': dict(tabela='projeto', pk=('codigo_projeto',), titulo='Projetos', campos=[C('codigo_projeto','Código','inteiro'),C('titulo','Título'),C('descricao','Descrição','multilinha',False,limite=300),O('situacao','Situação',SITUACOES),C('data_inicio','Início','data'),C('data_termino','Término','data',False)], colunas=['codigo_projeto','titulo','situacao','data_inicio','data_termino']),
'participantes': dict(tabela='participante',pk=('cpf',),titulo='Participantes',campos=[C('cpf','CPF','cpf'),C('nome','Nome'),C('email','E-mail'),O('tipo_participante','Tipo',TIPOS),C('senha','Senha (vazio na edição mantém a atual)','senha',False,limite=128)],colunas=['cpf','nome','email','tipo_participante']),
'financiamentos': dict(tabela='financiamento',pk=('codigo_financiamento',),titulo='Financiamentos',campos=[C('codigo_financiamento','Código','inteiro'),O('agencia_financiadora','Agência',AGENCIAS),O('tipo_fomento','Fomento',FOMENTOS),C('valor_total','Valor total','dinheiro'),C('data_inicio','Início','data'),C('data_termino','Término','data')],colunas=['codigo_financiamento','agencia_financiadora','tipo_fomento','valor_total','data_inicio','data_termino']),
'producoes': dict(tabela='producao_cientifica',pk=('codigo_projeto','codigo_prod'),titulo='Produções científicas',campos=[C('codigo_projeto','Projeto','projeto'),C('codigo_prod','Código da produção','inteiro'),C('titulo','Título'),O('tipo_prod','Tipo',PRODUCOES),O('meio_divulgacao','Divulgação',MEIOS),C('ano_publicacao','Ano','ano')],colunas=['codigo_projeto','codigo_prod','titulo','tipo_prod','meio_divulgacao','ano_publicacao']),
'vinculos': dict(tabela='vinculo_projeto_participante',pk=('codigo_projeto','cpf'),titulo='Equipe dos projetos',campos=[C('codigo_projeto','Projeto','projeto'),C('cpf','Participante','participante'),O('funcao_desempenhada','Função',FUNCOES),C('data_entrada','Entrada','data',False),C('data_saida','Saída','data',False)],colunas=['codigo_projeto','cpf','funcao_desempenhada','data_entrada','data_saida']),
'alocacoes': dict(tabela='vinculo_projeto_financiamento',pk=('codigo_projeto','codigo_financiamento'),titulo='Recursos por projeto',campos=[C('codigo_projeto','Projeto','projeto'),C('codigo_financiamento','Financiamento','financiamento'),C('valor_destinado','Valor destinado','dinheiro')],colunas=['codigo_projeto','codigo_financiamento','valor_destinado'])}
