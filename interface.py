"""Interface desktop do OrganizaIA. Execute: python interface.py"""
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from src import config, organizador
from src.chat import ChatSession

BG='#0b1423'; PANEL='#172538'; PANEL2='#213247'; BORDER='#34465b'; TEXT='#f2f6fc'; MUTED='#a7b8cb'; BLUE='#237ac5'; GREEN='#06db89'

class Interface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('OrganizaIA — Organizador de Documentos e Pastas')
        self.geometry('1050x650'); self.minsize(850,540); self.configure(bg=BG)
        self.pasta=tk.StringVar(value=str(config.ENTRADA_DIR)); self.modo=tk.StringVar(value='ia')
        self.regras=[tk.BooleanVar(value=True),tk.BooleanVar(value=True),tk.BooleanVar(value=False)]
        self.status=tk.StringVar(value='Pronto para organizar')
        self.sessao=None; self.ocupado=False
        self._montar()

    def label(self,parent,text,size=11,bold=False,color=TEXT,**kw):
        return tk.Label(parent,text=text,font=('Segoe UI',size,'bold' if bold else 'normal'),bg=parent['bg'],fg=color,**kw)

    def botao(self,parent,text,command,bg=BLUE,fg='white',**kw):
        return tk.Button(parent,text=text,command=command,bg=bg,fg=fg,activebackground=bg,activeforeground=fg,relief='flat',bd=0,font=('Segoe UI',10,'bold'),cursor='hand2',padx=13,pady=10,**kw)

    def painel(self,parent):
        f=tk.Frame(parent,bg=PANEL,highlightbackground=BORDER,highlightthickness=1)
        return f

    def _montar(self):
        topo=tk.Frame(self,bg=BG); topo.pack(fill='x',padx=22,pady=(18,12))
        self.label(topo,'🤖  OrganizaIA',23,True).pack(anchor='w')
        self.label(topo,'Organizador de Documentos e Pastas com IA',10,color=MUTED).pack(anchor='w')
        corpo=tk.Frame(self,bg=BG); corpo.pack(fill='both',expand=True,padx=22,pady=(0,20))
        corpo.grid_columnconfigure(0,weight=1); corpo.grid_columnconfigure(1,weight=1)
        corpo.grid_rowconfigure(0,weight=1)
        esq=tk.Frame(corpo,bg=BG); esq.grid(row=0,column=0,sticky='nsew',padx=(0,7))
        direita=self.painel(corpo); direita.grid(row=0,column=1,sticky='nsew',padx=(7,0))

        sec=self.painel(esq); sec.pack(fill='x',pady=(0,10))
        self.label(sec,'Selecione o que deseja organizar',11,True).pack(anchor='w',padx=14,pady=(12,7))
        linha=tk.Frame(sec,bg=PANEL); linha.pack(fill='x',padx=12,pady=(0,12))
        tk.Entry(linha,textvariable=self.pasta,bg=BG,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',10)).pack(side='left',fill='x',expand=True,ipady=9,padx=(0,7))
        self.botao(linha,'Buscar Pasta',self._buscar).pack(side='right')

        sec=self.painel(esq); sec.pack(fill='x',pady=(0,10))
        self.label(sec,'Modo de Organização',11,True).pack(anchor='w',padx=14,pady=(12,7))
        linha=tk.Frame(sec,bg=PANEL); linha.pack(fill='x',padx=12,pady=(0,12))
        for value,texto in [('ia','✧  Organização Inteligente (IA)'),('tipo','▤  Por Tipo de Arquivo')]:
            tk.Radiobutton(linha,text=texto,variable=self.modo,value=value,bg=PANEL,fg=TEXT,selectcolor=BG,activebackground=PANEL,activeforeground=TEXT,font=('Segoe UI',10),indicatoron=True).pack(side='left',padx=(0,10))

        sec=self.painel(esq); sec.pack(fill='both',expand=True)
        self.label(sec,'Regras automáticas',11,True).pack(anchor='w',padx=14,pady=(14,10))
        for var,texto in zip(self.regras,['Criar subpastas por data/mês','Agrupar por contexto do arquivo','Agrupar por contexto da data']):
            tk.Checkbutton(sec,text=texto,variable=var,bg=PANEL,fg=TEXT,selectcolor=BG,activebackground=PANEL,activeforeground=TEXT,font=('Segoe UI',10),anchor='w').pack(fill='x',padx=14,pady=3)
        self.botao(sec,'ϟ  ORGANIZAR AGORA',self._organizar,bg=GREEN,fg='#05291e').pack(fill='x',padx=13,pady=(22,12))
        self.progresso=tk.Canvas(sec,height=7,bg=BORDER,highlightthickness=0)
        self.progresso.pack(fill='x',padx=14,pady=(0,9)); self.progresso.bind('<Configure>',self._barra)
        self.label(sec,'',9,color=MUTED,textvariable=self.status).pack(pady=(0,12))

        seclog=self.painel(esq); seclog.pack(fill='both',expand=True,pady=(0,10))
        self.label(seclog,'Registo de atividade (chamadas de API e passos)',11,True).pack(anchor='w',padx=14,pady=(12,7))
        self.log=tk.Text(seclog,bg=BG,fg=MUTED,wrap='word',state='disabled',relief='flat',
                         font=('Consolas',9),padx=10,pady=8,height=8)
        self.log.pack(fill='both',expand=True,padx=12,pady=(0,12))
        self.rolagem=tk.Scrollbar(seclog,command=self.log.yview,bg=PANEL2,relief='flat')
        self.rolagem.pack(side='right',fill='y',padx=(0,12))
        self.log.configure(yscrollcommand=self.rolagem.set)
        self._log('Interface iniciada. Aguardando ação.')

        cab=tk.Frame(direita,bg=PANEL); cab.pack(fill='x')
        self.label(cab,'💬  Chat com OrganizaIA',15,True).pack(anchor='w',padx=14,pady=15)
        tk.Frame(direita,bg=BORDER,height=1).pack(fill='x')
        # Reservar primeiro a faixa inferior para a entrada do chat.
        envio=tk.Frame(direita,bg=PANEL)
        envio.pack(side='bottom',fill='x',padx=10,pady=(0,10))
        self.entrada=tk.Entry(envio,bg=BG,fg=TEXT,insertbackground=TEXT,relief='flat',font=('Segoe UI',10))
        self.entrada.pack(side='left',fill='x',expand=True,ipady=12,padx=(0,7))
        self.entrada.bind('<Return>',lambda e:self._enviar())
        self.botao(envio,'Enviar',self._enviar).pack(side='right')

        self.historico=tk.Text(direita,bg=BG,fg=TEXT,wrap='word',state='disabled',relief='flat',font=('Segoe UI',11),padx=14,pady=14,spacing3=12)
        self.historico.pack(side='top',fill='both',expand=True,padx=10,pady=10)
        self.historico.tag_configure('bot',foreground='#b5d9ff'); self.historico.tag_configure('user',foreground='#d8fce9')
        self._mensagem('bot','Olá! Selecione uma pasta ao lado, configure sua API Key e me diga como quer organizar seus arquivos.')
        self.label(self,'API: configure GLM_API_KEY no ambiente ou arquivo .env',9,color=MUTED).pack(anchor='e',padx=23,pady=(0,8))

    def _log(self,texto):
        """Registo de metadados (nunca conteudo de arquivo nem chave). Cap 500 linhas."""
        from datetime import datetime
        agora=datetime.now().strftime('%H:%M:%S')
        self.log.configure(state='normal')
        self.log.insert('end',f'[{agora}] {texto}\n')
        linhas=int(self.log.index('end-1c').split('.')[0])
        if linhas>500:self.log.delete('1.0',f'{linhas-500}.0')
        self.log.configure(state='disabled');self.log.see('end')

    def _barra(self,event=None):
        self.progresso.delete('all'); w=self.progresso.winfo_width()
        self.progresso.create_rectangle(0,0,w*(0.85 if self.ocupado else 0),7,fill=BLUE,outline='')

    def _buscar(self):
        pasta=filedialog.askdirectory(initialdir=self.pasta.get() if Path(self.pasta.get()).is_dir() else str(Path.home()))
        if pasta:self.pasta.set(pasta);self.sessao=None

    def _mensagem(self,autor,conteudo):
        self.historico.configure(state='normal')
        self.historico.insert('end',('OrganizaIA' if autor=='bot' else 'Você')+'\n',autor)
        self.historico.insert('end',str(conteudo)+'\n\n')
        self.historico.configure(state='disabled');self.historico.see('end')

    def _rodar(self,func):
        if self.ocupado:return
        self.ocupado=True;self._barra()
        def job():
            try: func()
            except Exception as exc:self.after(0,lambda msg=str(exc):self._mensagem('bot','Erro: '+msg))
            finally:self.after(0,self._terminar)
        threading.Thread(target=job,daemon=True).start()

    def _terminar(self):
        self.ocupado=False;self._barra()

    def _organizar(self):
        pasta=Path(self.pasta.get()).expanduser()
        if not pasta.is_dir():messagebox.showerror('Pasta inválida','Selecione uma pasta existente.');return
        destino=pasta/'OrganizaIA_Organizados'
        if not messagebox.askyesno('Confirmar organização',f'Organizar os arquivos de:\n{pasta}\n\nDestino: {destino}\n\nOs arquivos serão movidos. Deseja continuar?'):return
        def job():
            self.after(0,lambda:(self.status.set('Organizando arquivos...'),self._log('Organização iniciada')))
            resultado=organizador.processar(entrada=pasta,organizados=destino,
                                            modo=self.modo.get(),
                                            avisar=lambda texto:self.after(0,self._log,texto))
            movidos=len(resultado.get('movimentos',[]));ignorados=len(resultado.get('ignorados',[]))
            msg=f'Organização concluída: {movidos} arquivos processados; {ignorados} ignorados.'
            self.after(0,lambda:(self.status.set(msg),self._mensagem('bot',msg),
                                 self._log(f'Organização concluída: {movidos} processados, {ignorados} ignorados')))
        self._rodar(job)

    def _enviar(self):
        pergunta=self.entrada.get().strip()
        if not pergunta or self.ocupado:return
        pasta=Path(self.pasta.get()).expanduser()
        if not pasta.is_dir():messagebox.showerror('Pasta inválida','Selecione uma pasta existente.');return
        self.entrada.delete(0,'end');self._mensagem('user',pergunta)
        def job():
            if self.sessao is None:
                self._log('Chat iniciado (IA configurada com GLM_API_KEY/.env)')
                self.sessao=ChatSession(entrada=pasta,organizados=pasta/'OrganizaIA_Organizados',
                                        confirmar=self._confirmar_chat,
                                        avisar=lambda texto:self.after(0,self._log,texto))
            resposta=self.sessao.responder(pergunta)
            self.after(0,lambda:self._mensagem('bot',resposta))
        self._rodar(job)

    def _confirmar_chat(self,acao,origem,destino):
        import queue
        q=queue.Queue()
        self.after(0,lambda:q.put(messagebox.askyesno('Confirmar ação da IA',f'{acao}\n\nOrigem: {origem}\nDestino: {destino}')))
        return q.get()

if __name__=='__main__':
    Interface().mainloop()
