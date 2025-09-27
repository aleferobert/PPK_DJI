# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ppk_drone.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('rnx2rtkp.exe', '.'),
        ('crx2rnx.exe', '.'),
        ('config.conf', '.'),
        ('ppk_process.py', '.')
    ],
    hiddenimports=[
        'ppk_process',
        'pyproj',
        'pyproj.crs',
        'pyproj.transformer',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'datetime',
        're',
        'os',
        'subprocess',
        'sys',
        'pandas',
        'numpy',
        'PIL',
        'PIL.Image'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PPK_Drone',
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
    icon='icon.ico'  # Remova esta linha se não tiver ícone
)