# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],  # Remplace par le nom de ton fichier principal
    pathex=[],
    binaries=[],
    datas=[
        ('qr.png', '.'),
        ('qr.ico', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ArbitreQRGenerator',  # Nom de ton exécutable
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False pour une app GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='qr.ico'
)