"""Layout compartilhado: formulário lateral, busca, filtros e tabela rolável."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from decimal import Decimal
import csv
import unicodedata
import customtkinter as ctk
import repositorio
from db import mensagem_erro
from validacao import validar, formatar
from telas.modelos import MODELOS

AZUL = '#122f59'
FUNDO = '#f5f7fc'
TEXTO = '#152f52'
MUTED = '#67758a'
CLARO = '#edf2fc'


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD',str(texto).casefold())
                   if not unicodedata.combining(c))


class TelaCadastro(ctk.CTkFrame):
    def __init__(self, master, app, modulo):
        super().__init__(master, fg_color=FUNDO, corner_radius=0)
        self.app, self.modulo, self.modelo = app, modulo, MODELOS[modulo]
        self.registros, self.opcoes, self.equipe = [], {}, []
        self.widgets, self.maps, self.author_vars = {}, {}, {}
        self.chave, self.busy = None, False
        self.grid_columnconfigure(1,weight=1)
        self.grid_rowconfigure(2,weight=1)
        ctk.CTkLabel(self,text=self.modelo['titulo'],font=('Arial',26,'bold'),text_color=TEXTO).grid(row=0,column=0,columnspan=2,sticky='w',padx=28,pady=(25,4))
        ctk.CTkLabel(self,text=self.modelo['subtitulo'],text_color=MUTED).grid(row=1,column=0,columnspan=2,sticky='w',padx=28,pady=(0,20))

        self.form = ctk.CTkScrollableFrame(self,width=320,fg_color='white',corner_radius=12)
        self.form.grid(row=2,column=0,sticky='nsew',padx=(28,18),pady=(0,24))
        self.form.grid_columnconfigure(0,weight=1)
        self.form_title = ctk.CTkLabel(self.form,text='Novo registro',font=('Arial',18,'bold'),text_color=TEXTO)
        self.form_title.grid(row=0,column=0,sticky='w',padx=12,pady=16)
        self.new_btn = ctk.CTkButton(self.form,text='+ Novo registro',fg_color=CLARO,text_color=TEXTO,command=self.limpar)
        self.new_btn.grid(row=1,column=0,sticky='ew',padx=12,pady=(0,8))
        for i,c in enumerate(self.modelo['campos']):
            row=2+i*2
            text=c.rotulo+(' *' if c.obrigatorio else '')
            ctk.CTkLabel(self.form,text=text,anchor='w',text_color=MUTED,font=('Arial',12,'bold')).grid(row=row,column=0,sticky='w',padx=12,pady=(12,3))
            if c.tipo == 'multilinha':
                widget=ctk.CTkTextbox(self.form,height=90,fg_color=CLARO,text_color=TEXTO)
            elif c.tipo == 'autores':
                widget=ctk.CTkScrollableFrame(self.form,height=130,fg_color=CLARO)
            elif c.tipo in ('opcao','projeto','docente','participante','financiamento'):
                widget=ctk.CTkOptionMenu(self.form,values=['Selecione...'],fg_color=CLARO,text_color=TEXTO,
                                         button_color='#dce6f7',button_hover_color='#c8d9f3',dynamic_resizing=False,
                                         command=lambda value,n=c.nome:self.opcao_mudou(n))
            else:
                placeholder='DD/MM/AAAA' if c.tipo=='data' else ('Ex.: 1234,56' if c.tipo=='dinheiro' else '')
                widget=ctk.CTkEntry(self.form,height=36,placeholder_text=placeholder,fg_color=CLARO,border_width=0,text_color=TEXTO)
            widget.grid(row=row+1,column=0,sticky='ew',padx=12)
            self.widgets[c.nome]=widget
        row=2+len(self.modelo['campos'])*2
        self.save_btn=ctk.CTkButton(self.form,text='Salvar '+self.modelo['singular'],fg_color=AZUL,height=42,command=self.salvar)
        self.save_btn.grid(row=row,column=0,sticky='ew',padx=12,pady=(24,8))
        ctk.CTkLabel(self.form,text='* Obrigatório • Datas em DD/MM/AAAA',text_color=MUTED,font=('Arial',11)).grid(row=row+1,column=0,pady=(0,16))

        panel=ctk.CTkFrame(self,fg_color='white',corner_radius=12)
        panel.grid(row=2,column=1,sticky='nsew',padx=(0,28),pady=(0,24))
        panel.grid_columnconfigure(0,weight=1)
        panel.grid_rowconfigure(2,weight=1)
        bar=ctk.CTkFrame(panel,fg_color='transparent')
        bar.grid(row=0,column=0,sticky='ew',padx=18,pady=(18,8))
        bar.grid_columnconfigure(0,weight=1)
        self.search_var=tk.StringVar()
        ctk.CTkEntry(bar,textvariable=self.search_var,placeholder_text='Buscar em todos os campos...',width=260,fg_color=CLARO,border_width=0,height=36).grid(row=0,column=0,sticky='ew',padx=(0,12))
        self.filter_var=tk.StringVar(value='Todos')
        self.filter=ctk.CTkOptionMenu(bar,variable=self.filter_var,values=['Todos'],command=lambda _:self.filtrar(),width=150,fg_color=CLARO,text_color=TEXTO,button_color='#dce6f7')
        self.filter.grid(row=0,column=1)
        self.year_var=tk.StringVar(value='Todos os anos')
        if modulo=='producoes':
            self.year_filter=ctk.CTkOptionMenu(bar,variable=self.year_var,values=['Todos os anos'],width=130,command=lambda _:self.filtrar(),fg_color=CLARO,text_color=TEXTO,button_color='#dce6f7')
            self.year_filter.grid(row=1,column=0,sticky='w',pady=(8,0))
        actions=ctk.CTkFrame(panel,fg_color='transparent')
        actions.grid(row=1,column=0,sticky='ew',padx=18,pady=(0,12))
        self.action_btns=[]
        for i,(label,command) in enumerate([('Editar',self.editar),('Excluir',self.excluir),('Atualizar',self.atualizar),('Exportar CSV',self.exportar)]):
            b=ctk.CTkButton(actions,text=label,command=command,width=88,fg_color=CLARO,text_color=TEXTO)
            b.grid(row=0,column=i,padx=(0,8))
            self.action_btns.append(b)
        if modulo in ('financiamentos','alocacoes'):
            target='alocacoes' if modulo=='financiamentos' else 'financiamentos'
            ctk.CTkButton(actions,text='Destinar a projetos' if target=='alocacoes' else 'Voltar a contratos',command=lambda:app.mostrar(target),fg_color=AZUL,width=140).grid(row=1,column=0,columnspan=3,sticky='w',pady=(10,0))
        table_frame=ctk.CTkFrame(panel,fg_color='white',corner_radius=0)
        table_frame.grid(row=2,column=0,sticky='nsew',padx=18)
        table_frame.grid_columnconfigure(0,weight=1)
        table_frame.grid_rowconfigure(0,weight=1)
        columns=[c[0] for c in self.modelo['colunas']]
        self.tree=ttk.Treeview(table_frame,columns=columns,show='headings',selectmode='browse',style='Sig.Treeview')
        for key,label,width in self.modelo['colunas']:
            self.tree.heading(key,text=label,command=lambda k=key:self.ordenar(k))
            self.tree.column(key,width=width,minwidth=70,stretch=True)
        self.tree.grid(row=0,column=0,sticky='nsew')
        sy=ttk.Scrollbar(table_frame,orient='vertical',command=self.tree.yview)
        sx=ttk.Scrollbar(table_frame,orient='horizontal',command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        sy.grid(row=0,column=1,sticky='ns')
        sx.grid(row=1,column=0,sticky='ew')
        self.tree.tag_configure('par',background='#f6f8fd')
        self.tree.bind('<Double-1>',lambda _:self.editar())
        self.status=ctk.CTkLabel(panel,text='Carregando...',text_color=MUTED,anchor='w',wraplength=650)
        self.status.grid(row=3,column=0,sticky='ew',padx=18,pady=14)
        self.search_var.trace_add('write',lambda *_:self.filtrar())
        self.atualizar()

    def set_busy(self,busy):
        self.busy=busy
        for b in [self.save_btn,self.new_btn,*self.action_btns]:
            b.configure(state='disabled' if busy else 'normal')

    def atualizar(self):
        if self.busy:
            return
        self.set_busy(True)
        self.status.configure(text='Consultando o banco...')
        self.app.trabalho(lambda:repositorio.carregar(self.modulo),self.carregado,self.falhou)

    def carregado(self,result):
        self.registros,self.opcoes,self.equipe=result
        for c in self.modelo['campos']:
            if c.tipo == 'opcao' or c.tipo in self.opcoes:
                values=c.opcoes if c.tipo=='opcao' else self.opcoes[c.tipo]
                self.maps[c.nome]={str(label):key for key,label in values}
                self.widgets[c.nome].configure(values=['Selecione...',*self.maps[c.nome]])
        filter_field=next((c for c in self.modelo['campos'] if c.tipo=='opcao'),None)
        self.filter_field=filter_field.nome if filter_field else None
        self.filter_map={label:key for key,label in filter_field.opcoes} if filter_field else {}
        self.filter.configure(values=['Todos',*self.filter_map])
        if self.filter_var.get() not in ['Todos',*self.filter_map]:
            self.filter_var.set('Todos')
        if self.modulo=='producoes':
            years=sorted({str(r['ano_publicacao']) for r in self.registros},reverse=True)
            self.year_filter.configure(values=['Todos os anos',*years])
            if self.year_var.get() not in ['Todos os anos',*years]:
                self.year_var.set('Todos os anos')
        self.set_busy(False)
        self.limpar()
        self.filtrar()

    def falhou(self,exc):
        self.set_busy(False)
        self.status.configure(text='Operação não concluída. Use Atualizar para tentar novamente.')
        messagebox.showerror('SIGPesq',mensagem_erro(exc),parent=self)

    def opcao_mudou(self,nome):
        if self.modulo=='producoes' and nome=='codigo_projeto':
            self.atualizar_autores()

    def atualizar_autores(self,selecionados=()):
        if 'autores' not in self.widgets:
            return
        box=self.widgets['autores']
        for child in box.winfo_children():
            child.destroy()
        self.author_vars={}
        project=self.maps.get('codigo_projeto',{}).get(self.widgets['codigo_projeto'].get())
        rows=[a for a in self.equipe if a['codigo_projeto']==project]
        if not rows:
            ctk.CTkLabel(box,text='Selecione o projeto e cadastre\nos vínculos dos autores.',text_color=MUTED).pack(pady=8)
        for a in rows:
            var=tk.BooleanVar(value=a['cpf'] in selecionados)
            self.author_vars[a['cpf']]=var
            ctk.CTkCheckBox(box,text=a['nome'],variable=var,text_color=TEXTO,font=('Arial',12)).pack(anchor='w',padx=4,pady=5)

    def limpar(self):
        if self.busy:
            return
        self.chave=None
        self.form_title.configure(text='Novo registro')
        for c in self.modelo['campos']:
            w=self.widgets[c.nome]
            if c.tipo=='autores':
                continue
            w.configure(state='normal')
            if isinstance(w,ctk.CTkOptionMenu):
                w.set('Selecione...')
            elif c.tipo=='multilinha':
                w.delete('1.0','end')
            else:
                w.delete(0,'end')
                if c.tipo=='horas':
                    w.insert(0,'20')
                if c.tipo=='ano':
                    w.insert(0,str(date.today().year))
        self.atualizar_autores()

    def selecionado(self):
        selected=self.tree.selection()
        if not selected:
            messagebox.showinfo('Selecione um registro','Clique em uma linha da tabela.',parent=self)
            return None
        return self.registros[int(selected[0])]

    def editar(self):
        if self.busy:
            return
        row=self.selecionado()
        if row is None:
            return
        self.limpar()
        self.chave=tuple(row[k] for k in self.modelo['pk'])
        self.form_title.configure(text='Editando registro')
        for c in self.modelo['campos']:
            w=self.widgets[c.nome]
            value=row.get(c.nome)
            if c.tipo=='autores':
                continue
            if isinstance(w,ctk.CTkOptionMenu):
                w.set(next((label for label,key in self.maps[c.nome].items() if key==value),'Selecione...'))
            elif c.tipo=='multilinha':
                w.delete('1.0','end')
                w.insert('1.0',str(value or ''))
            else:
                w.delete(0,'end')
                w.insert(0,'' if value is None else (formatar(value) if isinstance(value,date) else str(value)))
            if c.nome in self.modelo['pk']:
                w.configure(state='disabled')
            # O vínculo inicial só é usado na criação; demais vínculos têm módulo próprio.
            if self.modulo=='participantes' and c.nome in ('projeto','funcao','inicio','fim'):
                w.configure(state='disabled')
        self.atualizar_autores(row.get('autores',[]))
        self.status.configure(text='Editando. Chaves não podem ser alteradas. Use Salvar ou Novo registro.')

    def valores(self):
        result={}
        for c in self.modelo['campos']:
            w=self.widgets[c.nome]
            if c.tipo=='autores':
                result[c.nome]=[cpf for cpf,var in self.author_vars.items() if var.get()]
            elif isinstance(w,ctk.CTkOptionMenu):
                result[c.nome]=self.maps[c.nome].get(w.get())
            elif c.tipo=='multilinha':
                result[c.nome]=w.get('1.0','end-1c')
            else:
                result[c.nome]=w.get()
        return validar(self.modelo['campos'],result)

    def salvar(self):
        if self.busy:
            return
        try:
            dados=self.valores()
        except ValueError as exc:
            messagebox.showwarning('Confira o formulário',str(exc),parent=self)
            return
        self.set_busy(True)
        self.status.configure(text='Salvando...')
        self.app.trabalho(lambda:repositorio.salvar(self.modulo,dados,self.chave),self.salvo,self.falhou)

    def salvo(self,_):
        self.set_busy(False)
        self.atualizar()

    def excluir(self):
        if self.busy:
            return
        row=self.selecionado()
        if row is None:
            return
        key=tuple(row[k] for k in self.modelo['pk'])
        impact={
            'projetos':'Também serão excluídos os vínculos, destinações financeiras, produções e respectivas autorias deste projeto.',
            'participantes':'Também serão excluídos seus vínculos e suas autorias. Projetos e produções serão mantidos.',
            'financiamentos':'Também serão excluídas as destinações deste contrato. Os projetos serão mantidos.',
            'vinculos':'As autorias deste participante nas produções deste projeto também serão excluídas.',
            'producoes':'Todas as autorias desta produção também serão excluídas.',
            'alocacoes':'O financiamento e o projeto serão mantidos.'
        }
        if not messagebox.askyesno('Confirmar exclusão',f'Excluir {self.modelo["singular"].lower()} {key}?\n\n'+impact[self.modulo],parent=self):
            return
        self.set_busy(True)
        self.app.trabalho(lambda:repositorio.excluir(self.modulo,key),self.salvo,self.falhou)

    def rotulo(self,key,value):
        c=next((c for c in self.modelo['campos'] if c.nome==key),None)
        if c and c.tipo=='opcao':
            return dict(c.opcoes).get(value,formatar(value))
        return formatar(value)

    def filtrar(self):
        needle=normalizar(self.search_var.get().strip())
        self.tree.delete(*self.tree.get_children())
        count=0
        for i,r in enumerate(self.registros):
            text=' '.join(self.rotulo(k,v) for k,v in r.items())
            if needle and needle not in normalizar(text):
                continue
            filter_value=getattr(self,'filter_map',{}).get(self.filter_var.get())
            if filter_value is not None and r.get(self.filter_field)!=filter_value:
                continue
            if self.modulo=='producoes' and self.year_var.get()!='Todos os anos' and str(r['ano_publicacao'])!=self.year_var.get():
                continue
            self.tree.insert('', 'end',iid=str(i),values=[self.rotulo(k,r.get(k)) for k,_,_ in self.modelo['colunas']],tags=('par',) if count%2 else ())
            count+=1
        total=f'{count} de {len(self.registros)} registros'
        if self.modulo=='financiamentos':
            total+=' • Total cadastrado: '+formatar(sum((r['valor_total'] for r in self.registros),Decimal(0)))
        self.status.configure(text=total+(' • Nenhum resultado.' if not count else ' • Selecione uma linha para editar ou excluir.'))

    def ordenar(self,key):
        reverse=getattr(self,'ordem',None)==(key,False)
        self.ordem=(key,reverse)
        def sort_value(r):
            v=r.get(key)
            return (v is None, v if isinstance(v,(int,Decimal,date)) else normalizar(v or ''))
        self.registros.sort(key=sort_value,reverse=reverse)
        self.filtrar()

    def exportar(self):
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.csv',initialfile=self.modulo+'.csv',filetypes=[('CSV','*.csv')])
        if not path:
            return
        try:
            with open(path,'w',encoding='utf-8-sig',newline='') as f:
                writer=csv.writer(f,delimiter=';')
                writer.writerow([label for _,label,_ in self.modelo['colunas']])
                for iid in self.tree.get_children():
                    r=self.registros[int(iid)]
                    values=[self.rotulo(k,r.get(k)) for k,_,_ in self.modelo['colunas']]
                    # Evita interpretar texto cadastrado como fórmula em planilhas.
                    writer.writerow(["'"+v if v.lstrip().startswith(('=','+','-','@')) else v for v in values])
            self.status.configure(text='CSV exportado com os registros filtrados.')
        except OSError as exc:
            messagebox.showerror('Exportação',str(exc),parent=self)
