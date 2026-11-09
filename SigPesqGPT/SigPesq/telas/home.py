import customtkinter as ctk
from telas.base import AZUL,FUNDO,TEXTO,MUTED,CLARO
import repositorio
from validacao import formatar
from db import mensagem_erro

MODULOS=[
 ('projetos','01','Projetos de Pesquisa','Cadastro de projetos, objetivos, cronogramas e coordenação.','projetos em andamento'),
 ('participantes','02','Participantes','Pesquisadores, docentes, discentes e equipe técnica.','participantes cadastrados'),
 ('financiamentos','03','Financiamentos & Bolsas','Agências de fomento, contratos e recursos destinados.','total contratado'),
 ('producoes','04','Produções Científicas','Artigos, capítulos, softwares, patentes e relatórios.','produções registradas'),
 ('vinculos','05','Vínculos dos Participantes','Funções, vigência, carga semanal e atividades no projeto.','vínculos cadastrados'),
]


class Home(ctk.CTkFrame):
    def __init__(self,master,app):
        super().__init__(master,fg_color=FUNDO,corner_radius=0)
        self.app=app
        ctk.CTkLabel(self,text='Bem-vindo ao SIGPesq',font=('Arial',29,'bold'),text_color=TEXTO).pack(anchor='w',padx=32,pady=(30,6))
        ctk.CTkLabel(self,text='Sistema Integrado de Gestão de Pesquisa.',font=('Arial',16),text_color=TEXTO).pack(anchor='w',padx=32)
        ctk.CTkLabel(self,text='Selecione um módulo para cadastrar, editar e gerenciar a pesquisa e sua equipe.',text_color=MUTED).pack(anchor='w',padx=32,pady=(8,20))
        scroll=ctk.CTkScrollableFrame(self,fg_color='transparent')
        scroll.pack(fill='both',expand=True,padx=24,pady=(0,14))
        scroll.grid_columnconfigure(0,weight=1)
        self.values={}
        for i,(key,number,title,desc,unit) in enumerate(MODULOS):
            card=ctk.CTkFrame(scroll,fg_color='white',corner_radius=12,border_width=1,border_color='#e5ebf5')
            card.grid(row=i,column=0,sticky='ew',pady=7)
            card.grid_columnconfigure(1,weight=1)
            ctk.CTkLabel(card,text=number,width=48,height=48,fg_color=CLARO,corner_radius=10,text_color=AZUL,font=('Arial',18,'bold')).grid(row=0,column=0,rowspan=2,padx=18,pady=20)
            ctk.CTkLabel(card,text=title,font=('Arial',18,'bold'),text_color=TEXTO).grid(row=0,column=1,sticky='w',pady=(18,0))
            ctk.CTkLabel(card,text=desc,text_color=MUTED,wraplength=580,justify='left').grid(row=1,column=1,sticky='w',pady=(0,18))
            label=ctk.CTkLabel(card,text='Consultando...',text_color=AZUL,font=('Arial',13,'bold'))
            label.grid(row=0,column=2,sticky='e',padx=18)
            self.values[key]=(label,unit)
            ctk.CTkButton(card,text='Acessar  →',fg_color=AZUL,width=130,command=lambda k=key:app.mostrar(k)).grid(row=1,column=2,padx=18,pady=(0,14))
        self.status=ctk.CTkLabel(self,text='Consultando indicadores...',text_color=MUTED)
        self.status.pack(anchor='w',padx=32,pady=(0,12))
        app.trabalho(repositorio.indicadores,self.carregado,self.erro)

    def carregado(self,values):
        for key,(label,unit) in self.values.items():
            label.configure(text=f'{formatar(values[key])} {unit}')
        self.status.configure(text='Indicadores consultados diretamente no MySQL.')

    def erro(self,exc):
        for label,unit in self.values.values():
            label.configure(text='Indisponível')
        self.status.configure(text=mensagem_erro(exc)+' Acesse um módulo e use Atualizar.')
