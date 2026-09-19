# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the 洛天依 desktop pet (one-folder build)."""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = []
binaries = []
hiddenimports = []

for pkg in ("imgui", "glfw", "pybullet", "OpenGL", "edge_tts"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as exc:  # noqa: BLE001
        print(f"[spec] collect_all({pkg}) failed: {exc}")

datas += [
    ("models", "models"),
    ("vendor", "vendor"),
    ("assets", "assets"),
    ("tools/oi_worker.py", "tools"),
    ("README.md", "."),
    ("LICENSE", "."),
]

hiddenimports += collect_submodules("mmdpy")
hiddenimports += collect_submodules("mmdpy_world")

a = Analysis(
    ["main.py"],
    pathex=["vendor", "."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "pandas",
        "IPython",
        "pytest",
        "notebook",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="\u6d1b\u5929\u4f9d",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="\u6d1b\u5929\u4f9d",
)
