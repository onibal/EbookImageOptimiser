
# === CONFIG =======================================================

APP_VERSION = "1.0.2"
APP_NAME = f"EbookImageOptimiser-v{APP_VERSION}"
ENTRY_POINT = "app.py"
ICON = "app.ico"


# === ANALYSIS =====================================================

a = Analysis(
    [ENTRY_POINT],
    pathex=["."],
    binaries=[],
    datas=[(ICON, ".")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# === PYZ ARCHIVE ==================================================

pyz = PYZ(a.pure, a.zipped_data)

# === EXE  =====================================

exe = EXE(
    pyz,
    a.scripts,
    name=APP_NAME,
    icon=ICON,
    exclude_binaries=True,
    console=False,
    debug=False,
    strip=False,
    upx=True,
    bootloader_ignore_signals=False,
)

# === COLLECT PHASE  =============================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,                               # strip DLLs
    upx=True,                                 # compress DLLs
    name=APP_NAME,
)
