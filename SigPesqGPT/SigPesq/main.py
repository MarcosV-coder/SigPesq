"""Entrada da aplicação desktop. Execute: python main.py."""
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from tkinter import ttk, messagebox
import customtkinter as ctk
from telas.base import AZUL,FUNDO,TEXTO,CLARO,TelaCadastro
from telas.home import Home
from telas.projetos import Projetos
from telas.participantes import Participantes
from telas.financiamentos import Financiamentos
from telas.producoes import Producoes
from telas.vinculos import Vinculos

TELAS={'home':Home,'projetos':Projetos,'participantes':Participantes,
       'financiamentos':Financiamentos,'producoes':Producoes,'vinculos':Vinculos}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('SIGPesq • Gestão de Pesquisa')
        self.geometry('1440x920')
        self.minsize(1120,720)
        self.configure(fg_color=FUNDO)
        self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='mysql')
        self.resultados=Queue()
        self.pendentes=0
        self.fechando=False
        self.tela=None
        self.nav_btns={}
        nav=ctk.CTkFrame(self,fg_color='white',corner_radius=0,height=72)
        nav.pack(fill='x')
        ctk.CTkButton(nav,text='SIGPesq',font=('Arial',21,'bold'),fg_color='transparent',text_color=AZUL,
                      hover_color=CLARO,width=110,command=lambda:self.mostrar('home')).pack(side='left',padx=(24,15),pady=18)
        for key,label in [('projetos','Projetos'),('participantes','Participantes'),('financiamentos','Financiamentos'),('producoes','Produções'),('vinculos','Vínculos')]:
            btn=ctk.CTkButton(nav,text=label,width=110,height=34,corner_radius=8,fg_color='transparent',
                              text_color=TEXTO,hover_color=CLARO,command=lambda k=key:self.mostrar(k))
            btn.pack(side='left',padx=4)
            self.nav_btns[key]=btn
        ctk.CTkLabel(nav,text='Pró-Reitoria de Pesquisa\nGestão acadêmica',justify='right',text_color=TEXTO,font=('Arial',12)).pack(side='right',padx=24)
        self.container=ctk.CTkFrame(self,fg_color=FUNDO,corner_radius=0)
        self.container.pack(fill='both',expand=True)
        style=ttk.Style()
        style.theme_use('clam')
        style.configure('Sig.Treeview',background='white',foreground=TEXTO,fieldbackground='white',rowheight=48,borderwidth=0,font=('Arial',11))
        style.configure('Sig.Treeview.Heading',background=CLARO,foreground=TEXTO,font=('Arial',11,'bold'),padding=(8,14),relief='flat')
        style.map('Sig.Treeview',background=[('selected','#d9e9fb')],foreground=[('selected',AZUL)])
        self.protocol('WM_DELETE_WINDOW',self.fechar)
        self.after(60,self.processar)
        self.mostrar('home')

    def mostrar(self,key):
        if self.pendentes:
            return
        if self.tela:
            if getattr(self.tela,'chave',None) is not None:
                if not messagebox.askyesno('Sair da edição','Descartar os campos em edição e trocar de módulo?',parent=self):
                    return
            self.tela.destroy()
        for k,b in self.nav_btns.items():
            b.configure(fg_color=AZUL if k==key or (key=='alocacoes' and k=='financiamentos') else 'transparent',
                        text_color='white' if k==key or (key=='alocacoes' and k=='financiamentos') else TEXTO)
        self.tela=TELAS[key](self.container,self) if key!='alocacoes' else TelaCadastro(self.container,self,'alocacoes')
        self.tela.pack(fill='both',expand=True)

    def trabalho(self,func,ok,erro):
        self.pendentes+=1
        def worker():
            try:
                result=func()
            except Exception as exc:
                self.resultados.put((erro,exc))
            else:
                self.resultados.put((ok,result))
        self.executor.submit(worker)

    def processar(self):
        try:
            while True:
                callback,result=self.resultados.get_nowait()
                self.pendentes-=1
                if not self.fechando:
                    callback(result)
        except Empty:
            pass
        if not self.fechando:
            self.after(60,self.processar)

    def fechar(self):
        if self.pendentes:
            messagebox.showinfo('Operação em andamento','Aguarde a operação do banco terminar antes de fechar.',parent=self)
            return
        self.fechando=True
        self.executor.shutdown(wait=False,cancel_futures=True)
        self.destroy()


if __name__=='__main__':
    ctk.set_appearance_mode('light')
    ctk.set_default_color_theme('blue')
    App().mainloop()
