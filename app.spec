
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
	datas=[
		(ICON, "."), 
		('haarcascade_frontalface_default.xml', '.')
	],
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
    a.binaries,
    a.datas,
    name=APP_NAME,
    icon=ICON,
    exclude_binaries=False,
    console=False,
    debug=False,
    strip=False,
    upx=True,
    bootloader_ignore_signals=False,
	onefile=True,
)
