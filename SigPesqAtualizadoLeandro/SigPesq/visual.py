"""Identidade visual do SIGPesq e ícones desenhados localmente."""
import sys
import customtkinter as ctk
from PIL import Image, ImageDraw
from customtkinter.windows.widgets.core_rendering import DrawEngine
# Desenho vetorial evita depender da fonte de formas em ambientes Linux.
if sys.platform != 'win32': DrawEngine.preferred_drawing_method='polygon_shapes'
FUNDO='#f7f8ff'
BRANCO='#ffffff'
AZUL='#102e5b'
TITULO='#061e41'
TEXTO='#414752'
MUTED='#737b8a'
CLARO='#eef3ff'
BORDA='#e3eaf7'
CIANO='#006c9b'
FONTE='Segoe UI' if sys.platform=='win32' else 'Helvetica'

def fonte(size=14,bold=False): return (FONTE,size+2,'bold' if bold else 'normal')

def label(master,text='',size=14,bold=False,color=TEXTO,**kwargs):
    return ctk.CTkLabel(master,text=text,font=fonte(size,bold),text_color=color,**kwargs)

def botao(master,text,command,kind='primary',icon=None,width=100,height=38,**kwargs):
    # Reserva a largura real do texto, do ícone e das margens internas.
    if text:
        medida=ctk.CTkFont(family=FONTE,size=15,weight='bold').measure(text)
        width=max(width,medida+(60 if icon else 32))
    cor=AZUL if kind=='primary' else CLARO
    fg=BRANCO if kind=='primary' else (CIANO if kind=='accent' else TITULO)
    return ctk.CTkButton(master,text=text,command=command,width=width,height=height,corner_radius=8,
                         fg_color=cor,hover_color='#244875' if kind=='primary' else '#dfe8fc',
                         text_color=fg,text_color_disabled='#a3acbd',font=fonte(13,True),
                         image=icone(icon,fg) if icon else None,**kwargs)

def icone(nome,cor=AZUL,size=18):
    scale=3; im=Image.new('RGBA',(size*scale,size*scale)); d=ImageDraw.Draw(im)
    def xy(coords): return tuple(v*size*scale/24 for v in coords)
    def line(coords): d.line(xy(coords),fill=cor,width=2*scale,joint='curve')
    def rect(coords,r=1): d.rounded_rectangle(xy(coords),radius=r*scale,outline=cor,width=2*scale)
    def oval(coords): d.ellipse(xy(coords),outline=cor,width=2*scale)
    if nome in ('projetos','home'):
        rect((3,5,21,21)); line((3,9,21,9)); line((8,5,8,3,14,3,14,5)); line((8,14,11,17,16,12))
    elif nome in ('participantes','user'):
        oval((9,3,15,9)); d.arc(xy((4,11,20,25)),180,360,fill=cor,width=2*scale); line((5,19,19,19))
        if nome=='participantes': d.arc(xy((1,10,9,20)),110,220,fill=cor,width=2*scale); d.arc(xy((15,10,23,20)),-40,80,fill=cor,width=2*scale)
    elif nome in ('financiamentos','alocacoes'):
        rect((2,6,22,19)); oval((9,9,15,16)); line((5,9,7,9)); line((17,16,19,16))
    elif nome=='producoes':
        line((12,6,12,21)); line((12,6,7,3,2,4,2,19,7,18,12,21,17,18,22,19,22,4,17,3,12,6))
        line((5,8,9,9)); line((15,9,19,8)); line((5,12,9,13)); line((15,13,19,12))
    elif nome=='vinculos':
        d.arc(xy((1,9,15,22)),40,305,fill=cor,width=2*scale); d.arc(xy((9,1,23,15)),220,485,fill=cor,width=2*scale); line((8,16,16,8))
    elif nome=='search': oval((3,3,16,16)); line((15,15,22,22))
    elif nome=='plus': line((12,4,12,20)); line((4,12,20,12))
    elif nome=='edit': line((4,16,16,4,20,8,8,20,3,21,4,16,8,20)); line((14,6,18,10))
    elif nome=='trash': line((4,7,20,7)); rect((7,7,17,21)); line((9,7,9,3,15,3,15,7)); line((10,11,10,17)); line((14,11,14,17))
    elif nome=='info': oval((3,3,21,21)); line((12,10,12,17)); d.ellipse(xy((11,6,13,8)),fill=cor)
    elif nome=='arrow': line((4,12,20,12)); line((15,7,20,12,15,17))
    elif nome=='save': rect((3,3,21,21)); rect((7,3,16,9)); rect((7,14,17,21))
    elif nome=='logout': line((11,3,3,3,3,21,11,21)); line((10,12,22,12)); line((17,7,22,12,17,17))
    elif nome=='refresh': d.arc(xy((3,3,21,21)),35,320,fill=cor,width=2*scale); line((20,3,20,9,14,9))
    return ctk.CTkImage(im,size=(size,size))

# Apenas apresentação. Não acrescenta campos ao esquema do banco.
PAGINAS={
 'projetos': ('Gestão de Projetos de Pesquisa','Cronograma, objetivos e coordenação dos projetos de pesquisa.','Projetos Registrados','Novo Projeto'),
 'participantes': ('Gestão de Participantes','Cadastro e consulta dos pesquisadores e colaboradores vinculados.','Participantes Cadastrados','Adicionar Participante'),
 'financiamentos': ('Gestão de Financiamentos','Controle de recursos, agências financiadoras e vigência dos contratos.','Financiamentos Registrados','Novo Financiamento'),
 'producoes': ('Gestão de Produções Científicas','Artigos, capítulos de livro, softwares e relatórios técnicos dos projetos.','Produções Registradas','Nova Produção'),
 'vinculos': ('Vincular Participantes em Projetos','Funções e vigência dos participantes em cada projeto de pesquisa.','Vínculos Registrados','Novo Vínculo'),
 'alocacoes': ('Recursos destinados aos Projetos','Distribuição dos financiamentos entre os projetos de pesquisa.','Destinações Registradas','Nova Destinação')}
NAV={'projetos':'Projetos','participantes':'Participantes','financiamentos':'Financiamentos','producoes':'Produções','vinculos':'Vínculos','alocacoes':'Destinações'}
TITULOS_HOME={'projetos':'Projetos de Pesquisa','participantes':'Participantes','financiamentos':'Financiamentos & Bolsas','producoes':'Produções Científicas','vinculos':'Vínculos dos Participantes','alocacoes':'Recursos por Projeto'}
# Título de coluna e peso relativo, ocupando sempre a largura disponível.
COLUNAS={
 'projetos':[('CÓD.',7),('TÍTULO',19),('DESCRIÇÃO',20),('COORDENAÇÃO',15),('VIGÊNCIA',14),('SITUAÇÃO',14),('AÇÕES',11)],
 'participantes':[('CPF',16),('NOME',27),('E-MAIL',28),('TIPO',18),('AÇÕES',11)],
 'financiamentos':[('CÓD.',8),('AGÊNCIA',12),('FOMENTO',12),('PROJETOS',22),('VALOR TOTAL',17),('VIGÊNCIA',17),('AÇÕES',12)],
 'producoes':[('CÓD.',8),('TÍTULO',25),('PROJETO',23),('TIPO',17),('DIVULGAÇÃO',14),('ANO',7),('AÇÕES',12)],
 'vinculos':[('PROJETO',31),('CPF',16),('PARTICIPANTE',24),('FUNÇÃO',16),('VIGÊNCIA',17),('AÇÕES',12)],
 'alocacoes':[('PROJETO',38),('FINANCIAMENTO',27),('VALOR DESTINADO',23),('AÇÕES',12)]}
