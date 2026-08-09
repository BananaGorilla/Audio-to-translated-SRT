# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_all

# Automatically grab dynamically imported provider and native-model packages.
datas, binaries, hiddenimports = collect_all('litellm')
llama_datas, llama_binaries, llama_hiddenimports = collect_all('llama_cpp')
datas += llama_datas
binaries += llama_binaries
hiddenimports += llama_hiddenimports

hiddenimports += ['tiktoken_ext.openai_public', 'PySide6.QtMultimedia']
datas += [('ui', 'ui')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Transcription_And_Translation_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Transcription_And_Translation_Tool',
)
