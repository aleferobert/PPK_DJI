# -*- mode: python ; coding: utf-8 -*-
import os

import pyproj
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

_project = SPECPATH
_pyproj_data = os.path.join(os.path.dirname(pyproj.__file__), "proj_dir", "share", "proj")

_datas = [
    (f"{_project}/rnx2rtkp.exe", "."),
    (f"{_project}/crx2rnx.exe", "."),
    (f"{_project}/config.conf", "."),
]
if os.path.isdir(_pyproj_data):
    _datas.append((_pyproj_data, "pyproj/proj_dir/share/proj"))
_datas += collect_data_files("pyproj")

_hiddenimports = [
    "ppk_process",
    "reference_points",
    "obs_coverage",
    "ppk_runner",
    "mission_utils",
    "numpy",
    "pandas",
    "pyproj",
    "pyproj.database",
    "pyproj.datadir",
    "sqlite3",
]
_hiddenimports += collect_submodules("pyproj")

a = Analysis(
    [f"{_project}/ppk_drone.py"],
    pathex=[_project],
    binaries=[],
    datas=_datas,
    hiddenimports=_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "numpy.distutils",
        "numpy.f2py",
        "numpy.tests",
        "numpy.testing",
        "pandas.tests",
        "matplotlib",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        "setuptools",
        "wheel",
        "tkinter.test",
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
    name="PPK_Drone",
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
    icon=f"{_project}/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PPK_Drone",
)
