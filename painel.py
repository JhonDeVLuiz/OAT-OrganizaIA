"""Painel de TESTE (tkinter). Descartavel: nao entra no pipeline nem no commit final."""
import queue
import sqlite3
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from src import backup, chat as chat_mod, config, monitor, organizador, repositorio

PYTHON = BASE / ".venv" / "Scripts" / "python.exe"


def confirmar_gui(acao, origem, destino):
    return messagebox.askyesno("Confirmar", f"[{acao}]\n{origem}\n-> {destino}")


class Painel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OrganizaIA - painel de teste")
        self.geometry("900x600")
        self.observador = None
        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True)
        self._aba_pipeline(abas)
        self._aba_banco(abas)
        self._aba_testes(abas)
        self._aba_chat(abas)

    # ---- Pipeline ----
    def _aba_pipeline(self, abas):
        f = ttk.Frame(abas)
        abas.add(f, text="Pipeline")
        botoes = ttk.Frame(f)
        botoes.pack(fill="x", padx=8, pady=6)
        for texto, cmd in [
            ("--once", self._once),
            ("--dry-run", self._dry_run),
            ("--desfazer", self._desfazer),
            ("--exportar", self._exportar),
            ("▶ watch", self._watch_on),
            ("■ parar", self._watch_off),
        ]:
            ttk.Button(botoes, text=texto, command=cmd).pack(side="left", padx=4)
        meio = ttk.Frame(f)
        meio.pack(fill="both", expand=True, padx=8)
        self.lista_entrada = self._lista(meio, "entrada/")
        self.lista_org = self._lista(meio, "organizados/")
        self.saida = tk.Text(f, height=10)
        self.saida.pack(fill="x", padx=8, pady=6)
        self._atualizar_listas()

    def _lista(self, pai, titulo):
        fr = ttk.LabelFrame(pai, text=titulo)
        fr.pack(side="left", fill="both", expand=True, padx=4)
        lb = tk.Listbox(fr)
        lb.pack(fill="both", expand=True)
        return lb

    def _log(self, texto):
        self.saida.insert("end", texto + "\n")
        self.saida.see("end")

    def _atualizar_listas(self):
        """Atualiza listas com glob() otimizado, sem congelar GUI."""
        def _atualizar_em_thread():
            resultados = {}
            for nome_pasta, pasta in (("entrada", config.ENTRADA_DIR),
                                      ("org", config.ORGANIZADOS_DIR)):
                arquivos = []
                if pasta.is_dir():
                    # ✅ glob() em vez de rglob() - muito mais rápido
                    # ✅ Ignora pastas pesadas
                    for p in sorted(pasta.glob("*")):
                        if p.is_file():
                            arquivos.append(p.relative_to(pasta).as_posix())
                        elif p.is_dir() and p.name not in {'.venv', '.git', '__pycache__', '.pytest_cache'}:
                            # Listagem simples de subpastas (sem recursão)
                            for sub in sorted(p.glob("*")):
                                if sub.is_file():
                                    arquivos.append(sub.relative_to(pasta).as_posix())
                resultados[nome_pasta] = arquivos
            return resultados

        # Processa em thread para não travar GUI
        fila = queue.Queue()
        threading.Thread(target=lambda: fila.put(_atualizar_em_thread()), daemon=True).start()
        self._esperar_listas(fila)

    def _esperar_listas(self, fila):
        """Espera resultado da thread de atualização."""
        try:
            resultados = fila.get_nowait()
        except queue.Empty:
            self.after(100, self._esperar_listas, fila)
            return

        # Atualiza GUI com resultados
        for lb, chave in ((self.lista_entrada, "entrada"),
                          (self.lista_org, "org")):
            lb.delete(0, "end")
            for arquivo in resultados[chave]:
                lb.insert("end", arquivo)

    def _resultado(self, res):
        for mov in res["movimentos"]:
            tag = "dry-run" if res["dry_run"] else mov["status"]
            self._log(f"[{tag}] {mov['origem']} -> {mov['destino']}")
        for ign in res["ignorados"]:
            self._log(f"[ignorado:{ign['motivo']}] {ign['origem']}")
        if res["id"]:
            self._log(f"log: exec_{res['id']}.json")
        self._atualizar_listas()

    def _once(self):
        self._resultado(organizador.processar())

    def _dry_run(self):
        self._resultado(organizador.processar(dry_run=True))

    def _desfazer(self):
        res = organizador.desfazer_ultima_execucao()
        if not res["restaurados"]:
            self._log("nada a desfazer")
        for item in res["restaurados"]:
            self._log(f"[desfeito] {item['de']} -> {item['para']}")
        self._atualizar_listas()

    def _exportar(self):
        destino = filedialog.asksaveasfilename(defaultextension=".zip",
                                               filetypes=[("ZIP", "*.zip")])
        if destino:
            res = backup.exportar_backup(destino)
            self._log(f"backup: {res['zip']} ({len(res['arquivos'])} arquivos)")

    def _watch_on(self):
        if self.observador:
            return
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        painel = self

        class Handler(FileSystemEventHandler):
            def _cuidar(self, caminho):
                if monitor.deve_ignorar(caminho) or not monitor.arquivo_estavel(caminho):
                    return
                res = organizador.processar_um(caminho)
                painel.after(0, painel._resultado, res)

            def on_created(self, event):
                if not event.is_directory:
                    self._cuidar(event.src_path)

            def on_moved(self, event):
                if not event.is_directory:
                    self._cuidar(event.dest_path)

        self.observador = Observer()
        self.observador.schedule(Handler(), str(config.ENTRADA_DIR), recursive=False)
        self.observador.start()
        self._log(f"observando {config.ENTRADA_DIR}")

    def _watch_off(self):
        if self.observador:
            self.observador.stop()
            self.observador.join()
            self.observador = None
            self._log("watch parado")

    # ---- Banco ----
    def _aba_banco(self, abas):
        f = ttk.Frame(abas)
        abas.add(f, text="Banco")
        ttk.Button(f, text="Atualizar", command=self._atualizar_banco).pack(pady=6)
        self.texto_banco = tk.Text(f)
        self.texto_banco.pack(fill="both", expand=True, padx=8, pady=6)
        self._atualizar_banco()

    def _atualizar_banco(self):
        linhas = []
        db = config.DB_PATH
        if db.is_file():
            con = sqlite3.connect(str(db))
            try:
                for tab in ("arquivos", "classificacoes", "auditoria"):
                    linhas.append(f"== {tab} ==")
                    for row in con.execute(f"SELECT * FROM {tab} ORDER BY 1 DESC LIMIT 20;"):
                        linhas.append(str(tuple(row)))
            finally:
                con.close()
        else:
            linhas.append("(sem banco ainda — rode --once)")
        logs = sorted(config.LOGS_DIR.glob("exec_*.json")) if config.LOGS_DIR.is_dir() else []
        linhas.append(f"-- {len(logs)} logs em logs/ --")
        self.texto_banco.delete("1.0", "end")
        self.texto_banco.insert("end", "\n".join(linhas))

    # ---- Testes ----
    def _aba_testes(self, abas):
        f = ttk.Frame(abas)
        abas.add(f, text="Testes")
        topo = ttk.Frame(f)
        topo.pack(fill="x", padx=8, pady=6)
        self.status_pytest = ttk.Label(topo, text="não rodado")
        self.status_pytest.pack(side="left", padx=4)
        ttk.Button(topo, text="Rodar pytest", command=self._pytest).pack(side="left")
        self.texto_testes = tk.Text(f)
        self.texto_testes.pack(fill="both", expand=True, padx=8, pady=6)

    def _pytest(self):
        """Roda pytest em thread separada para não congelar GUI."""
        self.status_pytest.config(text="rodando...")
        self.texto_testes.delete("1.0", "end")
        self.texto_testes.insert("end", "Processando testes...\n")
        fila = queue.Queue()

        def _rodar():
            try:
                proc = subprocess.run([str(PYTHON), "-m", "pytest", "-q"],
                                      capture_output=True, text=True, cwd=str(BASE))
                fila.put(("sucesso", proc))
            except Exception as e:
                fila.put(("erro", str(e)))

        threading.Thread(target=_rodar, daemon=True).start()
        self._esperar_pytest(fila)

    def _esperar_pytest(self, fila):
        """Espera resultado do pytest rodando em thread."""
        try:
            status, resultado = fila.get_nowait()
        except queue.Empty:
            self.after(200, self._esperar_pytest, fila)
            return

        self.texto_testes.delete("1.0", "end")
        if status == "erro":
            self.texto_testes.insert("end", f"Erro: {resultado}")
            self.status_pytest.config(text="ERRO", foreground="red")
        else:
            proc = resultado
            self.texto_testes.insert("end", proc.stdout + proc.stderr)
            ok = proc.returncode == 0
            self.status_pytest.config(text="PASSOU" if ok else "FALHOU",
                                      foreground="green" if ok else "red")

    # ---- Chat ----
    def _aba_chat(self, abas):
        f = ttk.Frame(abas)
        abas.add(f, text="Chat")
        self.texto_chat = tk.Text(f, state="disabled")
        self.texto_chat.pack(fill="both", expand=True, padx=8, pady=6)
        self.area_barra = ttk.Frame(f)
        self.area_barra.pack(fill="x", padx=8, pady=(0, 2))
        self.barra = ttk.Progressbar(self.area_barra, mode="indeterminate")
        self.status_chat = ttk.Label(self.area_barra, text="", foreground="#555")
        self.status_chat.pack(side="left", fill="x", expand=True, padx=4)
        baixo = ttk.Frame(f)
        baixo.pack(fill="x", padx=8, pady=6)
        self.campo_chat = ttk.Entry(baixo)
        self.campo_chat.pack(side="left", fill="x", expand=True)
        self.campo_chat.bind("<Return>", lambda _e: self._perguntar())
        ttk.Button(baixo, text="Enviar", command=self._perguntar).pack(side="left", padx=4)
        self.sessao = chat_mod.ChatSession(confirmar=confirmar_gui,
                                           avisar=self._aviso_chat)
        self._falar("ia", "Chat pronto. Sem chave/rede, respondo que falhou — ferramentas só via GLM.")

    def _aviso_chat(self, texto):
        self.fila_chat.put(("aviso", texto))

    def _barrar_chat(self, ligada):
        if ligada:
            self.barra.pack(fill="x", padx=0, pady=(0, 2), before=self.status_chat)
            self.barra.start(12)
        else:
            self.barra.stop()
            self.barra.pack_forget()
            self.status_chat.config(text="")

    def _falar(self, quem, texto):
        self.texto_chat.config(state="normal")
        self.texto_chat.insert("end", f"{quem}: {texto}\n")
        self.texto_chat.see("end")
        self.texto_chat.config(state="disabled")

    def _perguntar(self):
        pergunta = self.campo_chat.get().strip()
        if not pergunta or str(self.campo_chat.cget("state")) == "disabled":
            return
        self.campo_chat.delete(0, "end")
        self._falar("voce", pergunta)
        self._falar("ia", "...")
        self.campo_chat.config(state="disabled")
        self._barrar_chat(True)
        self.status_chat.config(text="Iniciando...")
        self.fila_chat = queue.Queue()
        threading.Thread(
            target=lambda: self.fila_chat.put(
                ("pronto", self._responder_seguro(pergunta))),
            daemon=True).start()
        self.after(200, self._esperar_chat)

    def _responder_seguro(self, pergunta):
        try:
            return self.sessao.responder(pergunta)
        except Exception as exc:  # noqa: BLE001 - painel de teste
            return f"erro: {exc}"

    def _esperar_chat(self):
        pronto = None
        try:
            while True:
                tipo, valor = self.fila_chat.get_nowait()
                if tipo == "aviso":
                    self.status_chat.config(text=valor)
                else:
                    pronto = valor
        except queue.Empty:
            pass
        if pronto is None:
            self.after(200, self._esperar_chat)
            return
        self._barrar_chat(False)
        self._falar("ia", pronto)
        self.campo_chat.config(state="normal")


if __name__ == "__main__":
    Painel().mainloop()
