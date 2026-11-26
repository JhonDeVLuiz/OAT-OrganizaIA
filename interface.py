"""Interface desktop do OrganizaIA. Execute: python interface.py"""
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - ambiente sem a dependencia
    raise SystemExit(
        "customtkinter nao instalado. Rode: "
        r".\.venv\Scripts\python.exe -m pip install customtkinter")

from src import config, organizador
from src.chat import ChatSession
from src.classificador import chave_glm, definir_chave_sessao, definir_log_callback

# Tokens de design — cada cor e uma tupla (claro, escuro)
BG = ('#F4F7FA', '#08090B')            # fundo do app
CARD = ('#FFFFFF', '#111216')          # superficie dos cards
INPUT = ('#EFF3F8', '#0B0C0F')         # campos de entrada
BORDER = ('#D6E0EB', '#1E293B')        # borda sutil
BORDER_SOFT = ('#E3EAF2', '#26282E')   # divisores e controles
TEXT = ('#0F172A', '#F8FAFC')
MUTED = ('#5C6B80', '#94A3B8')
SUCCESS = ('#15803D', '#22C55E')
WARNING = ('#B45309', '#F59E0B')
FONTE = 'Segoe UI'
# Botoes verdes (esmeralda)
EMERALD = ('#05B98A', '#06D6A0')
EMERALD_MID = ('#0AA47C', '#0BB98A')
EMERALD_HOVER = ('#0FD3A3', '#2EE6B6')
EMERALD_INK = '#032B22'
# Segmentado (modo de organizacao e tema)
SEG_SEL = ('#A7F3DE', '#0A7F61')
SEG_SEL_HOVER = ('#8FE9D0', '#0E9F7A')
SEG_OFF = ('#E8F7F1', '#10231D')
SEG_OFF_HOVER = ('#DCF2EA', '#163027')
# Balao do usuario no chat
USER_BALAO = ('#CCFBEF', '#0A7F61')
USER_BORDA = ('#A7F3DE', '#0E9F7A')
USER_AUTOR = ('#0A7F61', '#D1FAE5')

MODOS = {'ia': '✧  Organização Inteligente (IA)', 'tipo': '▤  Por Tipo de Arquivo'}


class Interface(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode('dark')
        super().__init__(fg_color=BG)
        self.title('OrganizaIA — Organizador de Documentos e Pastas')
        self.geometry('1180x800'); self.minsize(1000,740)
        self.pasta=tk.StringVar(value=str(config.ENTRADA_DIR)); self.modo=tk.StringVar(value='ia')
        self.regras=[tk.BooleanVar(value=True),tk.BooleanVar(value=True),tk.BooleanVar(value=False)]
        self.status=tk.StringVar(value='Pronto para organizar')
        self.arquivos=[]  # arquivos escolhidos no seletor de arquivos (modo alternativo a pasta)
        self.pct=0.0      # progresso 0..1 da barra (porcentagem mostrada no status)
        self.sessao=None; self.ocupado=False
        self._balaos=[]        # (linha, label) das mensagens do chat
        self._wrap_after=None  # debounce do recalculo de quebra de linha
        self._montar()

    # ---------- componentes ----------
    def _card(self,parent):
        return ctk.CTkFrame(parent,fg_color=CARD,corner_radius=12,
                            border_width=1,border_color=BORDER)

    def _titulo_card(self,parent,texto):
        ctk.CTkLabel(parent,text=texto,font=(FONTE,12,'bold'),text_color=TEXT,
                     anchor='w').pack(fill='x',padx=16,pady=(14,10))

    def _botao(self,parent,text,command,**kw):
        return ctk.CTkButton(parent,text=text,command=command,
                             height=kw.pop('height',36),
                             corner_radius=kw.pop('corner_radius',8),
                             font=kw.pop('font',(FONTE,11,'bold')),**kw)

    def _montar(self):
        # ---------- cabecalho ----------
        topo=ctk.CTkFrame(self,fg_color='transparent')
        topo.pack(fill='x',padx=24,pady=(18,12))
        marca=ctk.CTkFrame(topo,fg_color=CARD,corner_radius=12,
                           border_width=1,border_color=BORDER_SOFT,width=44,height=44)
        marca.pack(side='left'); marca.pack_propagate(False)
        ctk.CTkLabel(marca,text='🤖',font=(FONTE,20)).pack(expand=True)
        textos=ctk.CTkFrame(topo,fg_color='transparent')
        textos.pack(side='left',padx=(12,0))
        ctk.CTkLabel(textos,text='OrganizaIA',font=(FONTE,22,'bold'),
                     text_color=TEXT).pack(anchor='w')
        ctk.CTkLabel(textos,text='Organizador de Documentos e Pastas com IA',
                     font=(FONTE,11),text_color=MUTED).pack(anchor='w')
        self.badge=ctk.CTkFrame(topo,fg_color=CARD,corner_radius=14,
                                border_width=1,border_color=BORDER_SOFT)
        self.badge.pack(side='right',pady=4)
        self.badge_dot=ctk.CTkLabel(self.badge,text='●',font=(FONTE,13),
                                    text_color=SUCCESS,width=16)
        self.badge_dot.pack(side='left',padx=(10,2),pady=6)
        self.badge_txt=ctk.CTkLabel(self.badge,text='',font=(FONTE,10,'bold'),
                                    text_color=MUTED)
        self.badge_txt.pack(side='left',padx=(0,12),pady=6)
        self._atualizar_badge()
        self.tema=tk.StringVar(value='🌙  Escuro')
        self.seletor_tema=ctk.CTkSegmentedButton(
            topo,values=['☀  Claro','🌙  Escuro'],variable=self.tema,
            command=self._mudar_tema,height=32,corner_radius=8,border_width=0,
            width=170,fg_color=INPUT,selected_color=SEG_SEL,
            selected_hover_color=SEG_SEL_HOVER,unselected_color=SEG_OFF,
            unselected_hover_color=SEG_OFF_HOVER,text_color=TEXT,
            font=(FONTE,10,'bold'),dynamic_resizing=False)
        self.seletor_tema.pack(side='right',padx=(0,10),pady=4)

        # ---------- corpo em 2 colunas ----------
        corpo=ctk.CTkFrame(self,fg_color='transparent')
        corpo.pack(fill='both',expand=True,padx=24,pady=(0,16))
        corpo.grid_columnconfigure(0,weight=1,uniform='col')
        corpo.grid_columnconfigure(1,weight=1,uniform='col')
        corpo.grid_rowconfigure(0,weight=1)

        esq=ctk.CTkFrame(corpo,fg_color='transparent')
        esq.grid(row=0,column=0,sticky='nsew',padx=(0,7))
        esq.grid_columnconfigure(0,weight=1)
        esq.grid_rowconfigure(4,weight=1)
        direita=self._card(corpo)
        direita.grid(row=0,column=1,sticky='nsew',padx=(7,0))

        # ---------- card 1: selecao ----------
        sec=self._card(esq)
        sec.grid(row=0,column=0,sticky='ew',pady=(0,8))
        self._titulo_card(sec,'Selecione o que deseja organizar')
        linha=ctk.CTkFrame(sec,fg_color='transparent')
        linha.pack(fill='x',padx=14)
        self.campo_pasta=ctk.CTkEntry(linha,textvariable=self.pasta,height=40,
                                      corner_radius=8,fg_color=INPUT,border_width=1,
                                      border_color=BORDER,text_color=TEXT,
                                      font=(FONTE,11))
        self.campo_pasta.pack(fill='x')
        botoes=ctk.CTkFrame(sec,fg_color='transparent')
        botoes.pack(fill='x',padx=14,pady=(10,8))
        self._botao(botoes,'Buscar Pasta',self._buscar,fg_color=EMERALD,
                    hover_color=EMERALD_HOVER,text_color=EMERALD_INK).pack(side='left')
        self._botao(botoes,'Buscar Arquivos',self._buscar_arquivos,fg_color=EMERALD_MID,
                    hover_color=EMERALD_HOVER,
                    text_color=EMERALD_INK).pack(side='left',padx=(8,0))
        linha_arq=ctk.CTkFrame(sec,fg_color='transparent')
        linha_arq.pack(fill='x',padx=14,pady=(0,14))
        self.rotulo_arquivos=tk.StringVar(value='Nenhum arquivo selecionado (organiza a pasta inteira)')
        ctk.CTkLabel(linha_arq,textvariable=self.rotulo_arquivos,font=(FONTE,9),
                     text_color=MUTED,anchor='w',justify='left',
                     wraplength=330).pack(side='left',fill='x',expand=True)
        self._botao(linha_arq,'Limpar',self._limpar_arquivos,fg_color=EMERALD_MID,
                    hover_color=EMERALD_HOVER,text_color=EMERALD_INK,width=62,height=28,
                    font=(FONTE,10)).pack(side='right')

        # ---------- card 2: modo ----------
        sec=self._card(esq)
        sec.grid(row=1,column=0,sticky='ew',pady=(0,8))
        self._titulo_card(sec,'Modo de Organização')
        self.modo_exibicao=tk.StringVar(value=MODOS['ia'])
        ctk.CTkSegmentedButton(
            sec,values=[MODOS['ia'],MODOS['tipo']],variable=self.modo_exibicao,
            command=self._mudar_modo,height=38,corner_radius=8,border_width=0,
            fg_color=INPUT,selected_color=SEG_SEL,selected_hover_color=SEG_SEL_HOVER,
            unselected_color=SEG_OFF,unselected_hover_color=SEG_OFF_HOVER,
            text_color=TEXT,font=(FONTE,10,'bold'),
            dynamic_resizing=False).pack(fill='x',padx=14,pady=(0,14))

        # ---------- card 3: chave da API ----------
        sec=self._card(esq)
        sec.grid(row=2,column=0,sticky='ew',pady=(0,8))
        self._titulo_card(sec,'Chave da API')
        ctk.CTkLabel(sec,text='Use uma chave autorizada pela empresa. Ela fica somente nesta sessão.',
                     font=(FONTE,9),text_color=MUTED,anchor='w',wraplength=430,
                     justify='left').pack(fill='x',padx=16,pady=(0,8))
        ctk.CTkLabel(sec,text='Provedor',font=(FONTE,9),text_color=MUTED,
                     anchor='w').pack(fill='x',padx=14,pady=(0,4))
        self.provedor_api=tk.StringVar(value='Google Gemini')
        self.seletor_provedor=ctk.CTkOptionMenu(
            sec,values=['Google Gemini','Anthropic-compatible'],
            variable=self.provedor_api,command=self._mudar_provedor,
            height=32,corner_radius=8,fg_color=INPUT,button_color=EMERALD_MID,
            button_hover_color=EMERALD_HOVER,text_color=TEXT,font=(FONTE,10))
        self.seletor_provedor.pack(fill='x',padx=14,pady=(0,8))

        linha_chave=ctk.CTkFrame(sec,fg_color='transparent')
        linha_chave.pack(fill='x',padx=14,pady=(0,8))
        self.chave_api=ctk.CTkEntry(linha_chave,show='•',height=38,corner_radius=8,
                                    fg_color=INPUT,border_width=1,border_color=BORDER,
                                    text_color=TEXT,placeholder_text='Cole sua chave aqui')
        self.chave_api.pack(side='left',fill='x',expand=True)
        self._botao(linha_chave,'Mostrar',self._alternar_visibilidade_chave,
                    width=82,height=36,fg_color=EMERALD_MID,
                    hover_color=EMERALD_HOVER,text_color=EMERALD_INK,
                    font=(FONTE,10,'bold')).pack(side='left',padx=(8,0))
        self._botao(linha_chave,'Usar chave',self._usar_chave,width=100,height=36,
                    fg_color=EMERALD,hover_color=EMERALD_HOVER,
                    text_color=EMERALD_INK,font=(FONTE,10,'bold')).pack(side='right',padx=(8,0))

        linha_gateway=ctk.CTkFrame(sec,fg_color='transparent')
        linha_gateway.pack(fill='x',padx=14,pady=(0,6))
        ctk.CTkLabel(linha_gateway,text='Gateway / Base URL',font=(FONTE,9),
                     text_color=MUTED,anchor='w').pack(side='left')
        self.base_url_api=ctk.CTkEntry(linha_gateway,height=32,corner_radius=8,
                                       fg_color=INPUT,border_width=1,border_color=BORDER,
                                       text_color=TEXT,placeholder_text='https://... (opcional)')
        self.base_url_api.pack(side='left',fill='x',expand=True,padx=(12,0))

        linha_modelo=ctk.CTkFrame(sec,fg_color='transparent')
        linha_modelo.pack(fill='x',padx=14,pady=(0,14))
        ctk.CTkLabel(linha_modelo,text='Modelo (opcional)',font=(FONTE,9),
                     text_color=MUTED,anchor='w').pack(side='left')
        self.modelo_api=ctk.CTkEntry(linha_modelo,height=32,corner_radius=8,
                                     fg_color=INPUT,border_width=1,border_color=BORDER,
                                     text_color=TEXT,placeholder_text='ex: gemini-2.5-flash')
        self.modelo_api.pack(side='left',fill='x',expand=True,padx=(12,0))

        # ---------- card 4: regras + acao ----------
        sec=self._card(esq)
        sec.grid(row=3,column=0,sticky='ew')
        self._titulo_card(sec,'Regras automáticas')
        for var,texto in zip(self.regras,['Criar subpastas por data/mês',
                                          'Agrupar por contexto do arquivo',
                                          'Agrupar por contexto da data']):
            ctk.CTkSwitch(sec,text=texto,variable=var,onvalue=True,offvalue=False,
                          font=(FONTE,11),text_color=TEXT,progress_color=EMERALD,
                          fg_color=BORDER_SOFT,button_color=TEXT,
                          button_hover_color=('#FFFFFF','#FFFFFF'),switch_width=42,
                          switch_height=22).pack(fill='x',padx=16,pady=4)
        self._botao(sec,'⚡  ORGANIZAR AGORA',self._organizar,height=50,
                    corner_radius=10,fg_color=EMERALD,hover_color=EMERALD_HOVER,
                    text_color=EMERALD_INK,
                    font=(FONTE,14,'bold')).pack(fill='x',padx=14,pady=(14,8))
        self.progresso=ctk.CTkProgressBar(sec,height=8,corner_radius=4,
                                          fg_color=BORDER,progress_color=EMERALD)
        self.progresso.set(0)
        self.progresso.pack(fill='x',padx=16,pady=(0,6))
        ctk.CTkLabel(sec,textvariable=self.status,font=(FONTE,9),
                     text_color=MUTED).pack(pady=(0,12))

        # ---------- coluna direita: chat e logs ----------
        direita.grid_columnconfigure(0,weight=1)
        direita.grid_rowconfigure(2,weight=1)
        direita.grid_rowconfigure(4,weight=0)
        cab=ctk.CTkFrame(direita,fg_color='transparent')
        cab.grid(row=0,column=0,sticky='ew')
        ctk.CTkLabel(cab,text='💬  Chat com OrganizaIA',font=(FONTE,15,'bold'),
                     text_color=TEXT).pack(side='left',padx=16,pady=16)
        ctk.CTkLabel(cab,text='assistente',font=(FONTE,9),
                     text_color=MUTED).pack(side='right',padx=16)
        ctk.CTkFrame(direita,fg_color=BORDER,height=1,
                     corner_radius=0).grid(row=1,column=0,sticky='ew')

        composer=ctk.CTkFrame(direita,fg_color=INPUT,corner_radius=12,
                              border_width=1,border_color=BORDER_SOFT)
        composer.grid(row=3,column=0,sticky='ew',padx=12,pady=(0,12))
        self.entrada=ctk.CTkEntry(composer,
                                  placeholder_text='Digite como quer organizar seus arquivos...',
                                  height=42,corner_radius=0,fg_color='transparent',
                                  border_width=0,text_color=TEXT,
                                  placeholder_text_color=MUTED,font=(FONTE,12))
        self.entrada.pack(side='left',fill='x',expand=True,padx=(10,6),pady=6)
        self.entrada.bind('<Return>',lambda e:self._enviar())
        self._botao(composer,'Enviar',self._enviar,width=86,height=34,
                    fg_color=EMERALD,hover_color=EMERALD_HOVER,
                    text_color=EMERALD_INK).pack(side='right',padx=6,pady=6)

        self.chat=ctk.CTkScrollableFrame(direita,fg_color='transparent',
                                         corner_radius=0,
                                         scrollbar_button_color=BORDER_SOFT,
                                         scrollbar_button_hover_color=MUTED)
        self.chat.grid(row=2,column=0,sticky='nsew',padx=(10,2),pady=(10,4))
        # add='+' preserva o binding interno que mantem o scrollregion do canvas
        self.chat.bind('<Configure>',self._ao_redimensionar_chat,add='+')
        self.chat._parent_canvas.bind('<Configure>',self._ao_redimensionar_canvas,add='+')

        # ---------- registo de atividade ----------
        seclog=self._card(direita)
        seclog.grid(row=4,column=0,sticky='nsew',padx=12,pady=(0,12))
        self._titulo_card(seclog,'Registo de atividade (chamadas de API e passos)')
        self.log=ctk.CTkTextbox(seclog,height=160,corner_radius=8,border_width=0,
                                fg_color=INPUT,text_color=MUTED,
                                font=('Consolas',9),wrap='word',border_spacing=6,
                                scrollbar_button_color=BORDER_SOFT,
                                scrollbar_button_hover_color=MUTED)
        self.log.pack(fill='both',expand=True,padx=14,pady=(0,14))
        self.log.configure(state='disabled')
        definir_log_callback(lambda texto: self.after(0, self._log, texto))
        self._log('Interface iniciada. Aguardando ação.')

    # ---------- estado / visual ----------
    def _alternar_visibilidade_chave(self):
        """Mostra ou oculta o texto apenas no campo de entrada."""
        visivel = bool(self.chave_api.cget('show'))
        self.chave_api.configure(show='' if visivel else '•')
        # O texto do botao descreve a proxima acao disponivel.
        for widget in self.chave_api.master.winfo_children():
            if isinstance(widget, ctk.CTkButton) and widget.cget('text') in ('Mostrar', 'Ocultar'):
                widget.configure(text='Ocultar' if visivel else 'Mostrar')
                break

    def _mudar_provedor(self, valor):
        """Atualiza os defaults visuais sem tocar em nenhuma chave."""
        gemini = valor == 'Google Gemini'
        self.base_url_api.delete(0, 'end')
        self.modelo_api.delete(0, 'end')
        if gemini:
            self.base_url_api.insert(0, 'https://generativelanguage.googleapis.com/v1beta')
            self.modelo_api.insert(0, 'gemini-2.5-flash')

    def _usar_chave(self):
        """Aplica a chave e o provedor somente na memoria desta execucao."""
        chave = self.chave_api.get().strip()
        base_url = self.base_url_api.get().strip()
        modelo = self.modelo_api.get().strip()
        if not chave:
            definir_chave_sessao(None)
            self._atualizar_badge()
            self._log('Chave da sessao removida')
            messagebox.showinfo('Chave da API','Nenhuma chave foi informada. O programa usara apenas o modo por regras.')
            return
        if base_url and not modelo:
            messagebox.showwarning('Modelo obrigatorio','Ao informar um Gateway/Base URL diferente do padrao, voce tambem precisa preencher o campo Modelo para que o sistema saiba qual modelo usar.')
            return
        provedor = 'gemini' if self.provedor_api.get() == 'Google Gemini' else 'anthropic'
        definir_chave_sessao(chave, base_url or None, modelo or None, provedor)
        self.chave_api.delete(0,'end')
        self._atualizar_badge()
        self._log('Chave da sessao configurada (valor oculto)')
        messagebox.showinfo('Chave da API','Chave configurada somente nesta sessao. Ela nao foi salva em arquivo.')

    def _atualizar_badge(self):
        """Mostra apenas presenca da chave; nunca le nem exibe o valor."""
        try:
            conectada=bool(chave_glm())
        except Exception:
            conectada=False
        self.badge_dot.configure(text_color=SUCCESS if conectada else WARNING)
        self.badge_txt.configure(
            text='IA conectada' if conectada else 'IA não configurada',
            text_color=TEXT if conectada else WARNING)
        self.badge.configure(border_color=BORDER if conectada else ('#FDE9C8','#3A2E14'))

    def _mudar_tema(self,valor):
        """Alterna entre tema claro e escuro (todas as cores sao tuplas)."""
        escuro=valor.startswith('🌙')
        ctk.set_appearance_mode('dark' if escuro else 'light')
        try:self.seletor_tema.set(valor)
        except Exception:pass
        self._log('Tema escuro ativado' if escuro else 'Tema claro ativado')

    def _mudar_modo(self,valor):
        """CTkSegmentedButton exibe texto; self.modo mantem 'ia'/'tipo'."""
        self.modo.set('ia' if valor==MODOS['ia'] else 'tipo')

    def _barra(self,event=None):
        self.progresso.set(self.pct)
        self.progresso.configure(progress_color=SUCCESS if self.pct>=1 else EMERALD)

    def _zerar_barra(self):
        if not self.ocupado:
            self.pct=0.0; self.status.set('Pronto'); self._barra()

    # ---------- log ----------
    def _log(self,texto):
        """Registo de metadados (nunca conteudo de arquivo nem chave). Cap 500 linhas."""
        from datetime import datetime
        agora=datetime.now().strftime('%H:%M:%S')
        self.log.configure(state='normal')
        self.log.insert('end',f'[{agora}] {texto}\n')
        linhas=int(self.log.index('end-1c').split('.')[0])
        if linhas>500:self.log.delete('1.0',f'{linhas-500}.0')
        self.log.configure(state='disabled');self.log.see('end')

    def _progresso(self,pct,texto=None):
        """Atualiza barra determinada: preenchimento + '40% — Pesquisando: ...'."""
        self.pct=max(0.0,min(1.0,pct))
        if texto is not None:
            self.status.set(f'{int(round(self.pct*100))}% — {texto}')
        self._barra()

    # ---------- selecao de pasta/arquivos ----------
    def _buscar(self):
        pasta=filedialog.askdirectory(initialdir=self.pasta.get() if Path(self.pasta.get()).is_dir() else str(Path.home()))
        if pasta:self.pasta.set(pasta);self.sessao=None

    def _buscar_arquivos(self):
        """Seletor de arquivos (multipla escolha): organiza so os escolhidos."""
        inicial=self.pasta.get() if Path(self.pasta.get()).is_dir() else str(Path.home())
        escolhidos=filedialog.askopenfilenames(title='Selecione os arquivos para organizar',initialdir=inicial)
        if not escolhidos:return
        self.arquivos=[Path(c) for c in escolhidos]
        self._atualizar_rotulo_arquivos()
        self._log(f'{len(self.arquivos)} arquivo(s) selecionado(s)')

    def _limpar_arquivos(self):
        self.arquivos=[]
        self._atualizar_rotulo_arquivos()
        self._log('Seleção de arquivos limpa (modo pasta)')

    def _atualizar_rotulo_arquivos(self):
        if not self.arquivos:
            self.rotulo_arquivos.set('Nenhum arquivo selecionado (organiza a pasta inteira)')
            return
        nomes=', '.join(a.name for a in self.arquivos[:4])
        extra=f' ... +{len(self.arquivos)-4}' if len(self.arquivos)>4 else ''
        self.rotulo_arquivos.set(f'{len(self.arquivos)} arquivo(s): {nomes}{extra}')

    # ---------- chat ----------
    def _wrap_chat(self):
        largura=self.chat.winfo_width()
        if largura<=1:largura=520
        return max(220,int(largura*0.70))

    def _ao_redimensionar_canvas(self,event=None):
        """Atualiza o scrollregion sempre que a area visivel muda de tamanho."""
        try:
            bbox=self.chat._parent_canvas.bbox('all')
            if bbox:self.chat._parent_canvas.configure(scrollregion=bbox)
        except Exception:pass

    def _ajustar_scrollregion(self):
        try:
            canvas=self.chat._parent_canvas
            canvas.update_idletasks()
            bbox=canvas.bbox('all')
            if bbox:canvas.configure(scrollregion=bbox)
        except Exception:pass

    def _ao_redimensionar_chat(self,event=None):
        if self._wrap_after is not None:
            try:self.after_cancel(self._wrap_after)
            except Exception:pass
        self._wrap_after=self.after(120,self._aplicar_wrap)

    def _aplicar_wrap(self):
        self._wrap_after=None
        largura=self._wrap_chat()
        for _linha,corpo in self._balaos:
            try:corpo.configure(wraplength=largura)
            except Exception:pass
        self._ajustar_scrollregion()

    def _rolar_chat(self):
        """Mantem o canvas rolavel e desce ate a mensagem mais recente."""
        try:
            canvas=self.chat._parent_canvas
            canvas.update_idletasks()
            bbox=canvas.bbox('all')
            if bbox:canvas.configure(scrollregion=bbox)
            canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _no_fim_do_chat(self):
        """True quando a view ja esta no fim (ou o conteudo cabe na tela)."""
        try:
            _topo,fim=self.chat._parent_canvas.yview()
            return fim>=0.999
        except Exception:
            return True

    def _mensagem(self,autor,conteudo):
        """Balão distinto para a IA (esquerda) e para o usuário (direita)."""
        eh_bot=autor=='bot'
        deve_rolar=(not eh_bot) or self._no_fim_do_chat()
        linha=ctk.CTkFrame(self.chat,fg_color='transparent')
        linha.pack(fill='x',padx=6,pady=(4,6))
        balao=ctk.CTkFrame(linha,fg_color=CARD if eh_bot else USER_BALAO,
                           corner_radius=12,border_width=1,
                           border_color=BORDER_SOFT if eh_bot else USER_BORDA)
        balao.pack(side='left' if eh_bot else 'right',
                   padx=(0,36) if eh_bot else (36,0))
        ctk.CTkLabel(balao,text='OrganizaIA' if eh_bot else 'Você',
                     font=(FONTE,10,'bold'),height=16,
                     text_color=MUTED if eh_bot else USER_AUTOR,
                     anchor='w').pack(anchor='w',padx=16,pady=(8,0))
        corpo=ctk.CTkLabel(balao,text=str(conteudo),font=(FONTE,12),height=20,
                           text_color=TEXT,justify='left',anchor='w',width=96,
                           wraplength=self._wrap_chat())
        corpo.pack(anchor='w',padx=16,pady=(1,8))
        self._balaos.append((linha,corpo))
        while len(self._balaos)>300:
            antiga,_corpo=self._balaos.pop(0)
            try:antiga.destroy()
            except Exception:pass
        if deve_rolar:
            self.after(30,self._rolar_chat)
            self.after(160,self._rolar_chat)

    # ---------- execucao ----------
    def _rodar(self,func):
        if self.ocupado:return
        self.ocupado=True; self.pct=0.0; self._barra()
        def job():
            try: func()
            except Exception as exc:self.after(0,lambda msg=str(exc):self._mensagem('bot','Erro: '+msg))
            finally:self.after(0,self._terminar)
        threading.Thread(target=job,daemon=True).start()

    def _terminar(self):
        self.ocupado=False
        self.pct=1.0; self.status.set('100% — Concluído'); self._barra()
        self.after(1500,self._zerar_barra)

    def _organizar(self):
        if self.arquivos:
            self._organizar_arquivos()
            return
        pasta=Path(self.pasta.get()).expanduser()
        if not pasta.is_dir():messagebox.showerror('Pasta inválida','Selecione uma pasta existente.');return
        destino=pasta/'OrganizaIA_Organizados'
        if not messagebox.askyesno('Confirmar organização',f'Organizar os arquivos de:\n{pasta}\n\nDestino: {destino}\n\nOs arquivos serão movidos. Deseja continuar?'):return
        try:
            total=sum(1 for f in pasta.iterdir() if f.is_file())
        except OSError:
            total=0
        def job():
            self.after(0,self._progresso,0.0,'Organizando arquivos...')
            feitos=[0]
            def aviso(texto):
                if texto.startswith('processando') and total:
                    feitos[0]+=1
                    nome=texto[len('processando'):].strip().rstrip('.')
                    self.after(0,self._progresso,min(1.0,feitos[0]/total),f'Pesquisando: {nome}')
                self.after(0,self._log,texto)
            resultado=organizador.processar(entrada=pasta,organizados=destino,
                                            modo=self.modo.get(),avisar=aviso)
            movidos=len(resultado.get('movimentos',[]));ignorados=len(resultado.get('ignorados',[]))
            msg=f'Organização concluída: {movidos} arquivos processados; {ignorados} ignorados.'
            self.after(0,lambda:(self.status.set(msg),self._mensagem('bot',msg),
                                 self._log(f'Organização concluída: {movidos} processados, {ignorados} ignorados')))
        self._rodar(job)

    def _organizar_arquivos(self):
        """Organiza somente os arquivos escolhidos no seletor (confirma antes)."""
        arquivos=list(self.arquivos)
        pasta=Path(self.pasta.get()).expanduser()
        base=pasta if pasta.is_dir() else arquivos[0].parent
        destino=base/'OrganizaIA_Organizados'
        lista='\n'.join(f'• {a.name}' for a in arquivos[:10])
        extra=f'\n… e mais {len(arquivos)-10}' if len(arquivos)>10 else ''
        origens=sorted({str(a.parent) for a in arquivos})
        origem_txt=origens[0] if len(origens)==1 else f'{len(origens)} pastas de origem'
        if not messagebox.askyesno(
                'Confirmar organização',
                f'Organizar estes {len(arquivos)} arquivo(s)?\n\n{lista}{extra}\n\n'
                f'Origem: {origem_txt}\nDestino: {destino}\n\n'
                'Os arquivos serão movidos. Deseja continuar?'):
            return
        def job():
            self.after(0,self._progresso,0.0,'Organizando arquivos selecionados...')
            self.after(0,self._log,f'Organização de {len(arquivos)} arquivo(s) selecionado(s) iniciada')
            aviso=lambda texto:self.after(0,self._log,texto)
            movidos=ignorados=0
            for i,caminho in enumerate(arquivos):
                self.after(0,self._progresso,(i+1)/len(arquivos),f'Pesquisando: {caminho.name}')
                try:
                    resultado=organizador.processar_um(caminho,entrada=caminho.parent,
                                                       organizados=destino,
                                                       modo=self.modo.get(),avisar=aviso)
                    if resultado['movimentos'] and resultado['movimentos'][0]['status']=='ignorado':
                        ignorados+=1
                    else:
                        movidos+=1
                except Exception as exc:
                    ignorados+=1
                    aviso(f'falha em {caminho.name}: {exc}')
            msg=f'Organização concluída: {movidos} arquivos processados; {ignorados} ignorados.'
            self.after(0,lambda:(self.status.set(msg),self._mensagem('bot',msg),
                                 self._log(f'Organização concluída: {movidos} processados, {ignorados} ignorados'),
                                 self.arquivos.clear(),self._atualizar_rotulo_arquivos()))
        self._rodar(job)

    def _aviso_chat(self,texto):
        """Log + progresso do chat: rodada 1/6 -> %, modelo em uso, ferramenta."""
        self._log(texto)
        import re
        m=re.search(r'rodada (\d+)/(\d+)',texto)
        if m:
            r,total=int(m.group(1)),int(m.group(2))
            self._progresso((r-1)/max(total,1),f'Pesquisando (rodada {r}/{total})')
        elif texto.startswith('chamando o modelo'):
            modelo=texto[len('chamando o modelo'):].strip().rstrip('.')
            self._progresso(self.pct,f'Pesquisando com {modelo}')
        elif texto.startswith('executando'):
            ferramenta=texto[len('executando'):].strip().rstrip('.')
            self._progresso(self.pct,f'Executando {ferramenta}')

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
                                        avisar=lambda texto:self.after(0,self._aviso_chat,texto))
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
