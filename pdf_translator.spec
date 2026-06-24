# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for PDFTranslator.
# Build with:  pyinstaller --noconfirm pdf_translator.spec
# Produces a windowed (no console) app at dist/PDFTranslator/.

block_cipher = None

# Bundle the data directory (QSS themes + ECDICT offline dictionary).
# Resolved at runtime via pdf_translator.paths.bundled_data_dir(), which
# expects the data/ folder to sit next to the pdf_translator package inside
# the bundle (i.e. at _MEIPASS/data). The (src, dest) form below places it there.
datas = [
    ('data', 'data'),
]

# Dynamically-loaded backends PyInstaller can't see by static analysis.
hiddenimports = [
    'pyttsx3.drivers.sapi5',          # Windows TTS driver (pyttsx3.init() picks it at runtime)
    'keyring.backends.Windows',       # Windows credential store backend (API keys)
]


a = Analysis(
    ['pdf_translator/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='PDFTranslator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # windowed GUI app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PDFTranslator',
)
