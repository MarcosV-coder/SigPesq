"""SIGPesq desktop: identidade visual da referência, cadastros em pop-ups."""
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from decimal import Decimal
from collections import Counter
import unicodedata
import customtkinter as ctk
import repositorio as repo
from modelos import MODELOS, TIPOS
from seguranca import autenticar
from validacao import formatar
from mascaras import aplicar_mascara
from db import mensagem_erro
from relatorios import AbaRelatorios
from visual import *


def normalizar(s):
    return ''.join(c for c in unicodedata.normalize('NFD',str(s).casefold()) if not unicodedata.combining(c))


class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode('light')
        super().__init__()
        self.title('SIGPesq | Sistema Integrado de Gestão de Pesquisa')
        self.geometry('1360x860'); self.minsize(1060,680); self.configure(fg_color=FUNDO)
        self.sessao=None; self.pendente=False; self.modal=None; self.modulo=None
        self.pool=ThreadPoolExecutor(max_workers=1); self.fila=Queue()
        self.status=tk.StringVar()
        self.header=ctk.CTkFrame(self,fg_color=FUNDO,corner_radius=0)
        self.header.pack(fill='x')
        self.body=ctk.CTkFrame(self,fg_color=FUNDO,corner_radius=0)
        self.body.pack(fill='both',expand=True,padx=28,pady=(8,0))
        label(self,textvariable=self.status,text='',size=11,color=MUTED,height=22).pack(fill='x',padx=28,pady=(0,4))
        self.protocol('WM_DELETE_WINDOW',self.fechar)
        self.after(60,self.processar); self.login()

    def limpar(self):
        for w in self.body.winfo_children(): w.destroy()
        for w in self.header.winfo_children(): w.destroy()
        self.registros=[]; self.opcoes={}; self.permitidos=set(); self.criar_projeto=False
        self.linhas_visuais=[]; self.atual=None; self.fontes_tabela={}

    def tarefa(self,fn,ok):
        if self.pendente: return
        self.pendente=True; self.status.set('Aguarde, carregando informações...'); self.configure(cursor='watch')
        def worker():
            try: self.fila.put((ok,fn(),None))
            except Exception as e: self.fila.put((ok,None,e))
        self.pool.submit(worker)

    def processar(self):
        try:
            while True:
                ok,r,e=self.fila.get_nowait(); self.pendente=False; self.configure(cursor=''); self.status.set('')
                if e: messagebox.showerror('Não foi possível concluir',mensagem_erro(e),parent=self.modal or self)
                else: ok(r)
        except Empty: pass
        self.after(60,self.processar)

    def fechar(self):
        if self.pendente:
            messagebox.showinfo('Aguarde','Há uma operação em andamento.',parent=self); return
        self.pool.shutdown(wait=False,cancel_futures=True); self.destroy()

    def cabecalho(self,ativo=None):
        top=ctk.CTkFrame(self.header,fg_color='transparent')
        top.pack(side='top',fill='x')
        fonte_logo=ctk.CTkFont(family=FONTE,size=22,weight='bold')
        logo=ctk.CTkButton(top,text='SIGPesq',font=fonte_logo,fg_color='transparent',text_color=TITULO,
                          hover_color=CLARO,width=fonte_logo.measure('SIGPesq')+24,height=40,
                          command=self.home if self.sessao else self.login)
        logo.pack(side='left',padx=(24,12),pady=11)
        ctk.CTkFrame(top,fg_color='#ccd4e1',width=1,height=22).pack(side='left',padx=(0,12))
        if self.sessao:
            # Navegação em linha própria deixa espaço para o nome completo.
            nav=ctk.CTkFrame(self.header,fg_color='transparent',height=42)
            nav.pack(side='bottom',fill='x',padx=24,pady=(0,6))
            for k,n in {**NAV, 'relatorios': 'Relatórios'}.items():
                btn=ctk.CTkButton(nav,text=n,font=fonte(13,k==ativo),width=10,height=34,corner_radius=8,
                                  fg_color=TITULO if k==ativo else 'transparent',
                                  hover_color=AZUL if k==ativo else CLARO,text_color=BRANCO if k==ativo else TEXTO,
                                  command=lambda k=k:self.consulta(k))
                btn.pack(side='left',padx=3)
            botao(top,'',self.login,kind='secondary',icon='logout',width=34,height=34).pack(side='right',padx=(7,24))
            account=ctk.CTkFrame(top,fg_color='transparent')
            account.pack(side='right',padx=(5,0))
            label(account,'Administrador geral' if self.sessao.admin else self.sessao.nome,size=11,bold=True,color=TITULO,anchor='e',justify='right',wraplength=700).pack(anchor='e')

    def login(self):
        if self.pendente or self.modal: return
        self.limpar(); self.sessao=None; self.modulo=None; self.cabecalho()
        card=ctk.CTkFrame(self.body,fg_color=BRANCO,corner_radius=16,border_width=1,border_color=BORDA,width=470)
        card.place(relx=.5,rely=.46,anchor='center')
        inner=ctk.CTkFrame(card,fg_color='transparent'); inner.pack(fill='both',padx=36,pady=32)
        label(inner,'Bem-vindo ao SIGPesq',size=27,bold=True,color=TITULO).pack(anchor='w')
        label(inner,'Sistema Integrado de Gestão de Pesquisa.',size=13,color=MUTED).pack(anchor='w',pady=(6,26))
        label(inner,'LOGIN',size=11,bold=True).pack(anchor='w')
        login=ctk.CTkEntry(inner,placeholder_text='E-mail, CPF ou admin',height=44,width=390,fg_color=CLARO,border_width=0,font=fonte(14),text_color=TITULO)
        login.pack(fill='x',pady=(6,18))
        label(inner,'SENHA',size=11,bold=True).pack(anchor='w')
        senha=ctk.CTkEntry(inner,show='*',placeholder_text='Sua senha',height=44,fg_color=CLARO,border_width=0,font=fonte(14),text_color=TITULO)
        senha.pack(fill='x',pady=(6,24))
        def entrar():
            usuario,segredo=login.get(),senha.get()
            self.tarefa(lambda:autenticar(usuario,segredo),self.entrar)
        botao(inner,'Entrar no SIGPesq',entrar,icon='arrow',height=44).pack(fill='x')
        senha.bind('<Return>',lambda _:entrar())
        botao(inner,'Cadastro opcional de participante',lambda:self.formulario('participantes',cadastro=True),kind='secondary').pack(fill='x',pady=(12,0))
        label(inner,'Acesso administrativo independente: login admin.',size=11,color=MUTED).pack(pady=(18,0))
        login.focus_set()

    def entrar(self,s):
        self.sessao=s; self.home()

    def home(self):
        if self.pendente or self.modal: return
        self.limpar(); self.modulo=None; self.cabecalho()
        label(self.body,'Bem-vindo ao SIGPesq',size=30,bold=True,color=TITULO).pack(anchor='w',pady=(9,0))
        label(self.body,'Sistema Integrado de Gestão de Pesquisa.',size=15).pack(anchor='w',pady=(4,0))
        label(self.body,'Selecione um módulo para cadastrar, consultar ou gerenciar sua pesquisa e equipe.',size=13).pack(anchor='w',pady=(3,20))
        title=ctk.CTkFrame(self.body,fg_color='transparent'); title.pack(fill='x',pady=(0,12))
        label(title,'Módulos Operacionais',size=18,bold=True,color=TITULO).pack(side='left')
        label(title,'Selecione uma área para gerenciamento',size=11,color=MUTED).pack(side='right')
        self.home_area=ctk.CTkScrollableFrame(self.body,fg_color='transparent',corner_radius=0,scrollbar_button_color='#d6dfef')
        self.home_area.pack(fill='both',expand=True); self.home_area.grid_columnconfigure(0,weight=1)
        self.cards_home=[]
        def worker(): return {k:repo.carregar(k,self.sessao)[0] for k in MODELOS}
        def ok(dados):
            for i,k in enumerate(MODELOS):
                registros=dados[k]; n=len(registros)
                numero=formatar(sum((r['valor_total'] for r in registros),Decimal('0'))) if k=='financiamentos' else f'{n} '+{'projetos':'projetos','participantes':'participantes','producoes':'produções','vinculos':'vínculos','alocacoes':'destinações'}[k]
                card=ctk.CTkFrame(self.home_area,fg_color=BRANCO,corner_radius=12,border_width=1,border_color=BORDA)
                card.grid(row=i,column=0,sticky='ew',pady=(0,16),padx=(0,6)); self.cards_home.append(card)
                head=ctk.CTkFrame(card,fg_color='transparent'); head.pack(fill='x',padx=22,pady=(19,8))
                box=ctk.CTkFrame(head,width=38,height=38,corner_radius=7,fg_color=CIANO if i%2 else AZUL); box.pack(side='left'); box.pack_propagate(False)
                ctk.CTkLabel(box,text='',image=icone(k,BRANCO,22)).pack(expand=True)
                label(head,numero,size=11,color=TEXTO,fg_color='#e4edff',corner_radius=12,height=24).pack(side='right',ipadx=10)
                label(card,TITULOS_HOME[k],size=16,bold=True,color=TITULO).pack(anchor='w',padx=22,pady=(0,3))
                label(card,PAGINAS[k][1],size=12,anchor='w').pack(fill='x',padx=22)
                ctk.CTkFrame(card,fg_color=BORDA,height=1).pack(fill='x',padx=22,pady=(16,10))
                foot=ctk.CTkFrame(card,fg_color='transparent'); foot.pack(fill='x',padx=22,pady=(0,15))
                estado=f"{sum(r['situacao']==1 for r in registros)} em andamento" if k=='projetos' else 'Informações do banco de pesquisa'
                label(foot,estado,size=11,color=CIANO).pack(side='left')
                botao(foot,'Acessar '+NAV[k],lambda k=k:self.consulta(k),icon='arrow',height=36).pack(side='right')
        self.tarefa(worker,ok)

    def consulta(self,modulo):
        if self.pendente or self.modal: return
        self.limpar(); self.modulo=modulo; self.cabecalho(modulo)
        if modulo=='relatorios':
            AbaRelatorios(self)
            return
        titulo,subtitulo,tabela,novo=PAGINAS[modulo]
        heading=ctk.CTkFrame(self.body,fg_color='transparent'); heading.pack(fill='x',pady=(9,22))
        left=ctk.CTkFrame(heading,fg_color='transparent'); left.pack(side='left',fill='x',expand=True)
        label(left,titulo,size=29,bold=True,color=AZUL,anchor='w').pack(fill='x')
        label(left,subtitulo,size=13,anchor='w').pack(fill='x',pady=(6,0))
        self.total_text=tk.StringVar(value='Carregando...')
        label(heading,textvariable=self.total_text,text='',size=12,bold=True,color=TITULO,fg_color=BRANCO,corner_radius=18,height=34).pack(side='right',padx=(15,1),ipadx=14)
        self.panel=ctk.CTkFrame(self.body,fg_color=BRANCO,corner_radius=13,border_width=1,border_color=BORDA)
        self.panel.pack(fill='both',expand=True,pady=(0,12))
        toolbar=ctk.CTkFrame(self.panel,fg_color='transparent'); toolbar.pack(fill='x',padx=22,pady=(21,13))
        toolbar.grid_columnconfigure(0,weight=1)
        label(toolbar,tabela,size=17,bold=True,color=TITULO).grid(row=0,column=0,sticky='w')
        self.contagem=tk.StringVar(value='0 cadastros')
        label(toolbar,textvariable=self.contagem,text='',size=11,bold=True,color=AZUL,fg_color='#d5e9ff',corner_radius=12,height=24).grid(row=0,column=1,padx=10,ipadx=9)
        self.novo=botao(toolbar,novo,lambda:self.formulario(self.modulo),icon='plus'); self.novo.grid(row=1,column=0,columnspan=2,sticky='e',pady=(10,0))
        filters=ctk.CTkFrame(self.panel,fg_color='transparent'); filters.pack(fill='x',padx=22,pady=(0,14))
        self.busca=tk.StringVar()
        self.search=ctk.CTkEntry(filters,placeholder_text='Buscar por nome, título, código ou projeto...',height=40,fg_color=CLARO,border_width=0,font=fonte(13),text_color=TITULO)
        self.search.pack(side='left',fill='x',expand=True,padx=(0,12))
        self.search.bind('<KeyRelease>',lambda _=None:self.busca.set(self.search.get()))
        self.campo_filtro=next((c for c in MODELOS[modulo]['campos'] if c.opcoes),None)
        self.filtro=tk.StringVar(value='Todos')
        if self.campo_filtro:
            self.dropdown=ctk.CTkOptionMenu(filters,values=['Todos']+[v for _,v in self.campo_filtro.opcoes],variable=self.filtro,
                command=lambda _:self.filtrar(),fg_color=CLARO,text_color=TITULO,button_color='#dfe8fc',button_hover_color='#d3dff5',height=40,width=175,font=fonte(12),dropdown_font=fonte(12))
            self.dropdown.pack(side='left',padx=(0,8))
        botao(filters,'Atualizar',self.carregar,kind='secondary',icon='refresh',width=100,height=40).pack(side='right')
        self.busca.trace_add('write',lambda *_:self.filtrar())
        self.colunas=COLUNAS[modulo]
        if not self.sessao.admin:
            self.colunas=[coluna for coluna in self.colunas if coluna[0]!='CPF']
        self.table_head=ctk.CTkFrame(self.panel,fg_color=CLARO,corner_radius=0,height=56)
        self.table_head.pack(fill='x',padx=(22,37)); self.table_head.pack_propagate(False)
        self.table_head.grid_propagate(False)
        for i,(nome,peso) in enumerate(self.colunas):
            self.table_head.grid_columnconfigure(i,weight=peso,uniform='col')
            cell=ctk.CTkFrame(self.table_head,width=1,height=56,fg_color='transparent',corner_radius=0)
            cell.grid(row=0,column=i,sticky='nsew'); cell.pack_propagate(False)
            w=label(cell,nome,size=11,bold=True,anchor='w',justify='left',wraplength=100)
            w.pack(fill='x',padx=10,pady=10)
            cell.bind('<Configure>',lambda e,w=w:w.configure(wraplength=max(30,e.width-20)))
        self.area_tabela=ctk.CTkScrollableFrame(self.panel,fg_color=BRANCO,corner_radius=0,scrollbar_button_color='#d2ddef',scrollbar_button_hover_color='#b8c9e3')
        self.area_tabela.pack(fill='both',expand=True,padx=(17,17)); self.area_tabela.grid_columnconfigure(0,weight=1)
        ctk.CTkFrame(self.panel,fg_color=BORDA,height=1).pack(fill='x',padx=22)
        bottom=ctk.CTkFrame(self.panel,fg_color='transparent'); bottom.pack(fill='x',padx=22,pady=13)
        self.rodape=tk.StringVar(value='Carregando registros...')
        label(bottom,textvariable=self.rodape,text='',size=11,color=MUTED).pack(side='left')
        label(bottom,'Ações: detalhes, editar e excluir.',size=11,color=MUTED).pack(side='right')
        self.carregar()

    def carregar(self):
        if self.modulo is None: return self.home()
        def worker():
            rows,opcoes=repo.carregar(self.modulo,self.sessao)
            from db import transacao
            with transacao() as cur:
                permitidos = {
                    p for p, _ in opcoes['projeto']
                    if repo.gestao(cur, self.sessao, p, modulo=self.modulo)
                }
                criar=repo.gestao(cur,self.sessao)
            return rows,opcoes,permitidos,criar
        def ok(r):
            self.registros,self.opcoes,self.permitidos,self.criar_projeto=r
            self.total_text.set(f'{len(self.registros)} registros'); self.contagem.set(f'{len(self.registros)} cadastros')
            self.filtrar(); self.botoes()
        self.tarefa(worker,ok)

    def texto(self,col,value):
        campo=next((c for c in MODELOS[self.modulo]['campos'] if c.nome==col),None)
        if campo and campo.opcoes: return dict(campo.opcoes).get(value,'Desconhecido')
        if campo and campo.tipo=='participante':
            nome=dict(self.opcoes.get('participante',[])).get(value)
            if nome is None:
                return 'Participante indisponível'
            return f'{nome} · {value}' if self.sessao.admin else nome
        if campo and campo.tipo in self.opcoes: return dict(self.opcoes[campo.tipo]).get(value,formatar(value))
        return formatar(value)

    def campos_consulta(self):
        return [
            campo for campo in MODELOS[self.modulo]['campos']
            if campo.nome!='senha'
            and not (self.modulo=='participantes' and campo.nome=='cpf' and not self.sessao.admin)
        ]

    def opcoes_participantes(self):
        participantes=self.opcoes.get('participante',[])
        if self.sessao.admin:
            return [(cpf,f'{nome} · {cpf}') for cpf,nome in participantes]
        totais=Counter(nome for _,nome in participantes)
        exibidos=Counter()
        opcoes=[]
        for cpf,nome in participantes:
            exibidos[nome]+=1
            rotulo=f'{nome} ({exibidos[nome]})' if totais[nome]>1 else nome
            opcoes.append((cpf,rotulo))
        return opcoes

    def pode(self,r=None):
        s=self.sessao; m=self.modulo
        if s.admin: return True
        if m=='participantes': return r is not None and r['cpf']==s.cpf
        if m=='financiamentos': return False
        if m=='projetos' and r is None: return self.criar_projeto
        return bool(self.permitidos) if r is None else r['codigo_projeto'] in self.permitidos

    def botoes(self):
        self.novo.configure(state='normal' if self.pode() else 'disabled')

    def filtrar(self):
        for w in self.area_tabela.winfo_children(): w.destroy()
        self.linhas_visuais=[]; self.atual=None
        q=normalizar(self.busca.get()); filtro=self.filtro.get()
        for r in self.registros:
            textos=[self.texto(c.nome,r.get(c.nome)) for c in self.campos_consulta()]
            if self.sessao.admin:
                textos.extend(str(v) for v in r.values())
            else:
                textos.extend(r[k] for k in ('coordenacao','equipes','projetos_apoiados','nomes_autores') if k in r)
            if q not in normalizar(' '.join(textos)): continue
            if self.campo_filtro and filtro!='Todos' and self.texto(self.campo_filtro.nome,r.get(self.campo_filtro.nome))!=filtro: continue
            self.inserir_linha(r,len(self.linhas_visuais))
        n=len(self.linhas_visuais); self.rodape.set(f'Exibindo {n} de {len(self.registros)} registros')
        if not n: label(self.area_tabela,'Nenhum registro encontrado.',size=14,color=MUTED,height=100).grid(row=0,column=0,sticky='ew')
        self.botoes()

    def selecionar(self,r):
        self.atual=r
        for frame,registro in self.linhas_visuais:
            frame.configure(fg_color='#f0f5ff' if registro is r else BRANCO)

    def selecionado(self): return self.atual

    def dados_celulas(self,r):
        m=self.modulo
        texto=lambda v,bold=False:[(str(v),bold)]
        projeto=lambda: self.texto('codigo_projeto',r.get('codigo_projeto'))
        vigencia=lambda: [(formatar(r.get('data_inicio',r.get('data_entrada'))),True),(('até '+formatar(r.get('data_termino',r.get('data_saida')))) if r.get('data_termino',r.get('data_saida')) else 'Sem término',False)]
        if m=='projetos':
            return [texto(r['codigo_projeto']),texto(r['titulo'],True),texto(r.get('descricao') or '-'),texto(r.get('coordenacao') or 'Sem coordenação'),vigencia(),self.texto('situacao',r['situacao'])]
        if m=='participantes':
            dados=[texto(r['nome'],True),texto(r['email']),self.texto('tipo_participante',r['tipo_participante'])]
            if self.sessao.admin:
                dados.insert(0,texto(r['cpf']))
            return dados
        if m=='financiamentos':
            return [texto(r['codigo_financiamento']),self.texto('agencia_financiadora',r['agencia_financiadora']),texto(self.texto('tipo_fomento',r['tipo_fomento'])),texto(r.get('projetos_apoiados') or 'Sem destinação'),texto(formatar(r['valor_total']),True),vigencia()]
        if m=='producoes':
            return [texto(r['codigo_prod']),texto(r['titulo'],True),texto(projeto()),texto(r.get('nomes_autores') or 'Autoria pendente de definição'),texto(self.texto('tipo_prod',r['tipo_prod'])),texto(self.texto('meio_divulgacao',r['meio_divulgacao'])),texto(r['ano_publicacao'])]
        if m=='vinculos':
            nome=dict(self.opcoes['participante']).get(r['cpf'],'Participante indisponível')
            dados=[texto(projeto()),texto(nome,True),self.texto('funcao_desempenhada',r['funcao_desempenhada']),vigencia()]
            if self.sessao.admin:
                dados.insert(1,texto(r['cpf']))
            return dados
        return [texto(projeto()),texto(self.texto('codigo_financiamento',r['codigo_financiamento'])),texto(formatar(r['valor_destinado']),True)]

    def inserir_linha(self,r,index):
        frame=ctk.CTkFrame(self.area_tabela,fg_color=BRANCO,corner_radius=0,height=140)
        frame.grid(row=index*2,column=0,sticky='ew'); frame.grid_propagate(False)
        self.linhas_visuais.append((frame,r)); frame.bind('<Button-1>',lambda _=None,r=r:self.selecionar(r))
        dados=self.dados_celulas(r)
        for i,(_,peso) in enumerate(self.colunas):
            frame.grid_columnconfigure(i,weight=peso,uniform='col')
            cell=ctk.CTkFrame(frame,width=1,height=140,corner_radius=0,fg_color='transparent')
            cell.grid(row=0,column=i,sticky='nsew'); cell.pack_propagate(False)
            cell.bind('<Button-1>',lambda _=None,r=r:self.selecionar(r))
            if i==len(self.colunas)-1:
                actions=ctk.CTkFrame(cell,fg_color='transparent'); actions.pack(anchor='w',padx=3,pady=28)
                for icon,cmd,enabled,color in [('info',lambda r=r:self.detalhes(r),True,CIANO),('edit',lambda r=r:self.edicao(r),self.pode(r),CIANO),('trash',lambda r=r:self.apagar(r),self.sessao.admin,'#bd2330')]:
                    b=ctk.CTkButton(actions,text='',image=icone(icon,color if enabled else '#bec7d6',16),width=24,height=32,corner_radius=5,fg_color='transparent',hover_color=CLARO,
                        command=cmd,state='normal' if enabled else 'disabled')
                    b.pack(side='left',padx=1)
                continue
            value=dados[i]
            if isinstance(value,str):
                bg,fg=('#e2edff',AZUL) if value!='Cancelado' else ('#ffe1df','#ad2330')
                badge=label(cell,value,size=11,bold=True,color=fg,fg_color=bg,corner_radius=12,height=25)
                badge.pack(anchor='w',padx=7,pady=(24,0))
                cell.bind('<Configure>',lambda e,w=badge:w.configure(wraplength=max(30,e.width-14)))
                badge.bind('<Button-1>',lambda _=None,r=r:self.selecionar(r))
            else:
                inner=ctk.CTkFrame(cell,fg_color='transparent'); inner.pack(fill='x',padx=10,pady=(20,0))
                labels=[]
                for texto,bold in value:
                    texto=str(texto)
                    w=label(inner,texto,size=13 if bold else 12,bold=bold,color=TITULO if bold else MUTED,anchor='w',justify='left',wraplength=180)
                    w.pack(fill='x',anchor='w',pady=(0,2)); labels.append((w,texto,13 if bold else 12,bold))
                    w.bind('<Button-1>',lambda _=None,r=r:self.selecionar(r))
                cell.bind('<Configure>',lambda e,ws=labels:self.ajustar_textos(e.width-20,ws))
        ctk.CTkFrame(self.area_tabela,fg_color=BORDA,height=1,corner_radius=0).grid(row=index*2+1,column=0,sticky='ew')

    def ajustar_textos(self,largura,informacoes):
        # Limita a prévia a quatro linhas; o valor completo continua em Detalhes.
        largura=max(24,largura)
        for widget,texto,tamanho,bold in informacoes:
            chave=(tamanho,bold)
            if chave not in self.fontes_tabela:
                self.fontes_tabela[chave]=tkfont.Font(self,family=FONTE,size=-fonte(tamanho)[1],weight='bold' if bold else 'normal')
            medida=self.fontes_tabela[chave].measure
            linhas=[]; atual=''
            for palavra in texto.split():
                candidato=(atual+' '+palavra).strip()
                if medida(candidato)<=largura: atual=candidato; continue
                if atual: linhas.append(atual); atual=''
                for char in palavra:
                    if atual and medida(atual+char)>largura: linhas.append(atual); atual=''
                    atual+=char
            if atual: linhas.append(atual)
            if len(linhas)>4:
                linhas=linhas[:4]; ultimo=linhas[-1]
                while ultimo and medida(ultimo+'...')>largura: ultimo=ultimo[:-1]
                linhas[-1]=ultimo+'...'
            widget.configure(text='\n'.join(linhas),wraplength=largura)

    def edicao(self,r=None):
        r=r or self.selecionado()
        if r and self.pode(r): self.formulario(self.modulo,r)

    def detalhes(self,r=None):
        if self.modal or self.pendente: return
        r=r or self.selecionado()
        if not r: return
        win=self.janela('Detalhes do registro',680,610)
        label(win,'Detalhes do registro',size=23,bold=True,color=TITULO).pack(anchor='w',padx=28,pady=(24,3))
        label(win,'Informações completas do cadastro selecionado.',size=12,color=MUTED).pack(anchor='w',padx=28,pady=(0,16))
        area=ctk.CTkScrollableFrame(win,fg_color=BRANCO,corner_radius=10); area.pack(fill='both',expand=True,padx=24,pady=(0,18))
        for c in self.campos_consulta():
            label(area,c.rotulo.upper(),size=11,bold=True,color=MUTED).pack(anchor='w',padx=12,pady=(14,2))
            w=label(area,self.texto(c.nome,r.get(c.nome)),size=14,color=TITULO,anchor='w',justify='left',wraplength=550)
            w.pack(fill='x',padx=12)
            area.bind('<Configure>',lambda e,w=w:w.configure(wraplength=max(150,e.width-36)),add='+')
        if self.modulo=='producoes':
            label(area,'AUTORES',size=11,bold=True,color=MUTED).pack(anchor='w',padx=12,pady=(14,2))
            label(area,r.get('nomes_autores') or 'Autoria pendente de definição.',size=14,anchor='w',justify='left',wraplength=550).pack(fill='x',padx=12)
        botao(win,'Fechar',self.fechar_modal,kind='secondary').pack(anchor='e',padx=24,pady=(0,20))

    def apagar(self,r=None):
        if self.pendente or self.modal: return
        r=r or self.selecionado()
        if not r: return
        if messagebox.askyesno('Excluir registro','Ocultar este registro e os registros que dependem dele nas consultas do sistema?',parent=self):
            chave=tuple(r[k] for k in MODELOS[self.modulo]['pk'])
            self.tarefa(lambda:repo.excluir(self.modulo,chave,self.sessao),lambda _:self.carregar())

    def janela(self,titulo,width,height):
        win=ctk.CTkToplevel(self); self.modal=win; win.title(titulo); win.configure(fg_color=FUNDO)
        h=min(height,self.winfo_screenheight()-90)
        win.geometry(f'{width}x{h}+{max(0,self.winfo_rootx()+(self.winfo_width()-width)//2)}+{max(0,self.winfo_rooty()+(self.winfo_height()-h)//2)}')
        win.minsize(520,440); win.transient(self)
        win.after(100,lambda:win.grab_set() if win.winfo_exists() else None)
        win.protocol('WM_DELETE_WINDOW',self.fechar_modal)
        return win

    def fechar_modal(self):
        if not self.pendente and self.modal:
            win=self.modal; self.modal=None; win.destroy()

    def formulario(self,modulo,registro=None,cadastro=False):
        if self.modal: self.modal.lift(); return
        if self.pendente: return
        m=MODELOS[modulo]
        singular={'projetos':'Projeto','participantes':'Participante','financiamentos':'Financiamento','producoes':'Produção','vinculos':'Vínculo','alocacoes':'Destinação'}[modulo]
        title=('Editar '+singular) if registro else PAGINAS[modulo][3]
        win=self.janela(title,660,760)
        top=ctk.CTkFrame(win,fg_color='transparent'); top.pack(fill='x',padx=28,pady=(24,6))
        label(top,title,size=23,bold=True,color=TITULO).pack(side='left')
        label(top,'Edição' if registro else 'Novo Registro',size=11,color=TEXTO,fg_color='#e2edff',corner_radius=12,height=25).pack(side='right',ipadx=10)
        label(win,'* Obrigatório  |  Datas em DD/MM/AAAA',size=11,color=MUTED).pack(anchor='w',padx=28,pady=(0,16))
        card=ctk.CTkFrame(win,fg_color=BRANCO,corner_radius=12,border_width=1,border_color=BORDA)
        card.pack(fill='both',expand=True,padx=24,pady=(0,14))
        area=ctk.CTkScrollableFrame(card,fg_color=BRANCO,corner_radius=12); area.pack(fill='both',expand=True,padx=10,pady=8)
        widgets={}; maps={}; self.form_widgets=widgets; self.form_maps=maps
        ocultar_cpf=modulo=='participantes' and registro is not None and not self.sessao.admin
        for c in m['campos']:
            if ocultar_cpf and c.nome=='cpf':
                continue
            rotulo=c.rotulo if c.nome!='senha' else 'Senha'
            label(area,rotulo.upper()+(' *' if c.obrigatorio or (c.nome=='senha' and not registro) else ''),size=11,bold=True,anchor='w').pack(fill='x',padx=12,pady=(14,6))
            value=registro.get(c.nome) if registro else None
            if c.tipo=='multilinha':
                w=ctk.CTkTextbox(area,height=100,fg_color=CLARO,border_width=0,text_color=TITULO,font=fonte(13),wrap='word'); w.insert('1.0',value or '')
            elif c.opcoes or c.tipo in ('projeto','participante','financiamento'):
                options=self.opcoes_participantes() if c.tipo=='participante' else list(c.opcoes or self.opcoes.get(c.tipo,[]))
                if cadastro and c.nome=='tipo_participante': options=list(TIPOS[:1])
                if not cadastro and c.nome=='codigo_projeto' and not self.sessao.admin and not registro: options=[(k,v) for k,v in options if k in self.permitidos]
                maps[c.nome]={str(v):k for k,v in options}
                w=ctk.CTkOptionMenu(area,values=['Selecione...']+list(maps[c.nome]),fg_color=CLARO,text_color=TITULO,
                    button_color=CLARO,button_hover_color='#dde7fc',font=fonte(13),dropdown_font=fonte(12),height=42,dynamic_resizing=False)
                w.set(next((v for v,k in maps[c.nome].items() if k==value), 'Discente' if cadastro and c.nome=='tipo_participante' else 'Selecione...'))
            else:
                placeholder='DD/MM/AAAA' if c.tipo=='data' else ('Deixe vazio para manter a senha' if c.tipo=='senha' and registro else ('Mínimo de 8 caracteres' if c.tipo=='senha' else ''))
                w=ctk.CTkEntry(area,show='*' if c.tipo=='senha' else '',placeholder_text=placeholder,height=42,fg_color=CLARO,border_width=0,text_color=TITULO,font=fonte(13))
                if value is not None: w.insert(0,formatar(value).replace('R$ ',''))
            if not c.opcoes and c.tipo not in ('multilinha','projeto','participante','financiamento'):
                aplicar_mascara(w,c.tipo)
            w.pack(fill='x',padx=12); widgets[c.nome]=w
            if registro and (c.nome in m['pk'] or (c.nome=='tipo_participante' and not self.sessao.admin)): w.configure(state='disabled')
        autores_vars={}
        if modulo=='producoes':
            label(area,'AUTORES *',size=11,bold=True,anchor='w').pack(fill='x',padx=12,pady=(14,6))
            label(area,'Selecione os participantes do projeto que assinam esta produção.',size=11,wraplength=520,justify='left').pack(fill='x',padx=12)
            autores_area=ctk.CTkFrame(area,fg_color='transparent')
            autores_area.pack(fill='x',padx=12,pady=8)
            def atualizar_autores(valor=None):
                selecionados={cpf for cpf,var in autores_vars.items() if var.get()}
                autores_salvos = dict(registro['autores']) if registro else {}
                if valor is None:
                    selecionados.update(autores_salvos)
                autores_vars.clear()
                for w in autores_area.winfo_children(): w.destroy()
                projeto=maps['codigo_projeto'].get(widgets['codigo_projeto'].get())
                equipe = dict(self.opcoes.get('autores_por_projeto', {}).get(projeto, []))
                for cpf, nome in autores_salvos.items():
                    equipe.setdefault(cpf, f'{nome} (vínculo oculto)')
                if not equipe:
                    label(autores_area,'Selecione um projeto com participantes vinculados para definir os autores.',size=12,wraplength=500,justify='left').pack(fill='x')
                for cpf,nome in equipe.items():
                    var=tk.BooleanVar(value=cpf in selecionados); autores_vars[cpf]=var
                    ctk.CTkCheckBox(autores_area,text=nome,variable=var,font=fonte(12)).pack(anchor='w',pady=6)
            widgets['codigo_projeto'].configure(command=atualizar_autores)
            atualizar_autores()
        if modulo=='projetos':
            aviso=label(area,'',size=11,color=MUTED,anchor='w')
            aviso.pack(fill='x',padx=12,pady=(6,0))
            def situacao_alterada(valor=None):
                concluido=widgets['situacao'].get()=='Concluído'
                aviso.configure(text='* Término obrigatório para projeto concluído.' if concluido else 'Término opcional enquanto o projeto não estiver concluído.')
            widgets['situacao'].configure(command=situacao_alterada)
            situacao_alterada()
        def salvar():
            dados={}
            for c in m['campos']:
                if ocultar_cpf and c.nome=='cpf':
                    dados[c.nome]=registro[c.nome]
                    continue
                w=widgets[c.nome]; v=w.get('1.0','end-1c') if c.tipo=='multilinha' else w.get()
                dados[c.nome]=maps[c.nome].get(v) if c.nome in maps else v
            if modulo=='producoes': dados['autores']=[cpf for cpf,var in autores_vars.items() if var.get()]
            chave=tuple(registro[k] for k in m['pk']) if registro else None
            def pronto(_):
                self.fechar_modal()
                if cadastro: messagebox.showinfo('Conta criada','Entre com seu e-mail ou CPF e sua senha. A equipe responsável poderá vinculá-lo a um projeto.',parent=self)
                else: self.carregar()
            self.tarefa(lambda:repo.salvar(modulo,dados,self.sessao,chave,cadastro),pronto)
        bottom=ctk.CTkFrame(win,fg_color='transparent'); bottom.pack(fill='x',padx=24,pady=(0,20))
        self.salvar_btn=botao(bottom,'Salvar alterações' if registro else 'Salvar cadastro',salvar,icon='save',height=42)
        self.salvar_btn.pack(side='right')
        botao(bottom,'Cancelar',self.fechar_modal,kind='secondary',height=42).pack(side='right',padx=10)


if __name__=='__main__': App().mainloop()
