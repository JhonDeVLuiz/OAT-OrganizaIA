# -*- mode: python ; coding: utf-8 -*-
# Spec do OrganizaIA — ONEFILE: gera UM UNICO OrganizaIA.exe que funciona sozinho.
# Compilar com: .venv\Scripts\python.exe -m PyInstaller --clean -y OrganizaIA.spec
from PyInstaller.utils.hooks import collect_all

# CustomTkinter tem arquivos de tema (JSON/imagens) que precisam vir junto.
ctk_datas, ctk_binaries, ctk_hidden = collect_all('customtkinter')

# O executavel nao embute .env nem qualquer chave. A chave pode ser informada
# pelo usuario no campo da interface e permanece somente na memoria da sessao.
datas = list(ctk_datas) + [('src', 'src')]

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
