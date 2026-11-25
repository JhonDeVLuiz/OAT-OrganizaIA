# -*- mode: python ; coding: utf-8 -*-
# Spec do OrganizaIA — ONEFILE: gera UM UNICO OrganizaIA.exe que funciona sozinho.
# Compilar com: .venv\Scripts\python.exe -m PyInstaller --clean -y OrganizaIA.spec
from PyInstaller.utils.hooks import collect_all

# CustomTkinter tem arquivos de tema (JSON/imagens) que precisam vir junto.
ctk_datas, ctk_binaries, ctk_hidden = collect_all('customtkinter')

# .env embutido no exe; o runtime hook (pyi_rth_env.py) o extrai ao lado do
# exe na primeira execucao, onde o config.py procura por ele.
datas = list(ctk_datas) + [('src', 'src'), ('.env', '.')]

a = Analysis(
    ['interface.py'],
    pathex=[],
    binaries=list(ctk_binaries),
    datas=datas,
    hiddenimports=list(ctk_hidden),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_env.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Onefile: SEM COLLECT — tudo (binarios + dados) vai dentro do proprio EXE.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OrganizaIA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # sem janela preta de terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # se voce tiver um icone: icon='icone.ico'
)
