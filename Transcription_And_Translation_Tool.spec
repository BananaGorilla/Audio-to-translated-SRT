# -*- mode: python ; coding: utf-8 -*-
import os
import sys

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_all

# Automatically grab dynamically imported provider and native-model packages.
datas, binaries, hiddenimports = collect_all('litellm')
llama_datas, llama_binaries, llama_hiddenimports = collect_all('llama_cpp')
datas += llama_datas
binaries += llama_binaries
hiddenimports += llama_hiddenimports

yt_dlp_datas, yt_dlp_binaries, yt_dlp_hiddenimports = collect_all('yt_dlp')
datas += yt_dlp_datas
binaries += yt_dlp_binaries
hiddenimports += yt_dlp_hiddenimports

# Browser impersonation is optional at runtime, but include its native
# curl_cffi components when it is available in the build environment.
curl_cffi_datas, curl_cffi_binaries, curl_cffi_hiddenimports = collect_all('curl_cffi')
datas += curl_cffi_datas
binaries += curl_cffi_binaries
hiddenimports += curl_cffi_hiddenimports

hiddenimports += [
    'tiktoken_ext.openai_public',
    'PySide6.QtMultimedia',
    'workers.MediaDownload',
]
datas += [('ui', 'ui')]

# To ship FFmpeg inside the app, place ffmpeg and ffprobe in ./bin before building.
executable_suffix = '.exe' if sys.platform == 'win32' else ''
for executable_name in ('ffmpeg', 'ffprobe'):
    executable_name += executable_suffix
    executable_path = os.path.join(SPECPATH, 'bin', executable_name)
    if os.path.isfile(executable_path):
        binaries.append((executable_path, 'bin'))

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
