# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pynput.mouse._win32', 'pynput.keyboard._win32'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'scipy', 'matplotlib', 'pandas', 'IPython', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'Crypto', 'zmq', 'jupyter_client', 'notebook'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MouseTrail',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

