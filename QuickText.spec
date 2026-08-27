# -*- mode: python ; coding: utf-8 -*-
# Build on Windows:  py -3 -m PyInstaller --noconfirm QuickText.spec

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden = ["rapidfuzz", "rapidfuzz.fuzz", "rapidfuzz.utils"]
hidden += collect_submodules("rapidfuzz")

qt_excludes = [
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQuick3D",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtPositioning",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSerialBus",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtNetworkAuth",
    "PySide6.QtHttpServer",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtUiTools",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtTextToSpeech",
    "tkinter",
    "matplotlib",
    "numpy",
    "pandas",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("data/defaults.json", "data"),
        ("knowledge/sample/knowledge.sample.json", "knowledge/sample"),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=qt_excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Keep only the Windows platform plugin and styles actually needed.
keep_plugin_bits = (
    "platforms/qwindows",
    "styles/qwindowsvistastyle",
    "styles/qmodernwindowsstyle",
    "imageformats/qico",
    "imageformats/qjpeg",
    "imageformats/qgif",
    "imageformats/qwbmp",
    "imageformats/qwebp",
)

def _keep_bin(item) -> bool:
    dest = str(item[1]).replace("\\", "/").lower()
    name = str(item[0]).replace("\\", "/").lower()
    blob = dest + " " + name
    drop_tokens = (
        "qml",
        "designer",
        "sqldrivers",
        "multimedia",
        "tls/",
        "networkinformation",
        "generic/",
        "geometryloaders",
        "renderers",
        "sceneparsers",
        "webview",
        "sensors",
        "position",
        "audio",
        "playlistformats",
        "canbus",
        "texttospeech",
        "translations/",
    )
    if any(tok in blob for tok in drop_tokens):
        return False
    if "plugins/platforms/" in blob or "/platforms/" in blob:
        return "qwindows" in blob
    if "plugins/styles/" in blob or "/styles/" in blob:
        return True
    if "plugins/imageformats/" in blob:
        return any(x in blob for x in ("qico", "qjpeg", "qgif", "qwebp", "qwbmp"))
    return True

a.binaries = [b for b in a.binaries if _keep_bin(b)]
a.datas = [d for d in a.datas if "translations" not in str(d[0]).replace("\\", "/").lower()
           and "qml" not in str(d[0]).replace("\\", "/").lower()]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="QuickText",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=["Qt6Core.dll", "Qt6Gui.dll", "Qt6Widgets.dll", "Qt6Network.dll", "python*.dll"],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
