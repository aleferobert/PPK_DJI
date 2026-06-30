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
        ('ppk_process.py', '.'),
        ('reference_points.py', '.'),
        ('obs_coverage.py', '.'),
        ('ppk_runner.py', '.'),
        ('mission_utils.py', '.'),
    ],
    hiddenimports=[
        'ppk_process',
        'reference_points',
        'obs_coverage',
        'ppk_runner',
        'mission_utils',
        'numpy',
        'pandas'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy.distutils',
        'numpy.f2py',
        'numpy.tests',
        'numpy.testing',
        'pandas.tests',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'setuptools',
        'wheel'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PPK_Drone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PPK_Drone',
)