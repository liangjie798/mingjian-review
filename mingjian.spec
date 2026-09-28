# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

import PySide6

hiddenimports = []

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=[],
    datas=[("scenario-packs", "scenario-packs"), ("assets/mingjian.ico", "assets")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["customtkinter", "fastapi", "uvicorn", "webview", "starlette", "pydantic"],
    noarchive=False,
    optimize=0,
)

# Python 3.13附带的MSVC运行库可能低于当前Qt构建版本。单文件模式会优先
# 从解压根目录加载DLL，因此用PySide6随附版本替换根目录副本。
pyside_dir = Path(PySide6.__file__).resolve().parent
qt_runtime_names = {
    "MSVCP140.dll",
    "MSVCP140_1.dll",
    "MSVCP140_2.dll",
    "VCRUNTIME140.dll",
    "VCRUNTIME140_1.dll",
}
for runtime_name in qt_runtime_names:
    runtime_source = pyside_dir / runtime_name
    if runtime_source.exists():
        a.binaries = [entry for entry in a.binaries if entry[0].lower() != runtime_name.lower()]
        a.binaries.append((runtime_name, str(runtime_source), "BINARY"))

# Qt 6.11 uses the ICU implementation shipped by Windows. Some development
# environments add Poppler to PATH; PyInstaller can then mistake Poppler's
# incompatible ICU 78 DLLs for Qt dependencies and bundle them at the app root.
# Those copies shadow System32 at runtime and make importing QtCore fail.
a.binaries = [
    entry
    for entry in a.binaries
    if Path(entry[0]).name.lower() not in {"icuuc.dll", "icudt78.dll"}
]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MingJian",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/mingjian.ico",
)
