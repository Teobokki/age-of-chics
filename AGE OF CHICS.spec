# -*- mode: python ; coding: utf-8 -*-
import os
ONEFILE = bool(os.environ.get("AOC_ONEFILE"))
try:
    from PyInstaller.utils.hooks import collect_all
except Exception:
    collect_all = None

def _collect(pkg):
    if collect_all is None:
        return [], [], []
    try:
        d, b, h = collect_all(pkg)
        return list(d), list(b), list(h)
    except Exception:
        return [], [], []

_d, _b, _h = [], [], []
for _pkg in ("pypdfium2", "pypdfium2_raw", "comtypes"):
    d, b, h = _collect(_pkg)
    _d += d
    _b += b
    _h += h
excl = ['matplotlib', 'scipy', 'pandas', 'IPython', 'pytest', 'torch', 'cv2', 'tkinter',
        'numpy',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
        'PySide6.QtPdf', 'PySide6.QtPdfWidgets', 'PySide6.QtSql', 'PySide6.QtTest', 'PySide6.QtBluetooth',
        'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtDesigner', 'PySide6.QtHelp',
        'PySide6.QtSpatialAudio', 'PySide6.QtGraphs', 'PySide6.QtQuick3D', 'PySide6.QtRemoteObjects',
        'PySide6.QtScxml', 'PySide6.QtStateMachine', 'PySide6.QtTextToSpeech', 'PySide6.QtVirtualKeyboard',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
        'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtQuickWidgets', 'PySide6.QtWebChannel',
        'PySide6.QtPositioning', 'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets', 'PySide6.QtNfc',
        'PySide6.QtHttpServer', 'PySide6.QtLocation', 'PySide6.QtAxContainer', 'PySide6.QtMultimedia']
a = Analysis(
    ['age_of_chics.py'],
    datas=[('assets', 'assets')] + _d,
    binaries=_b,
    hiddenimports=_h + [
        'pypdfium2', 'pypdfium2.raw', 'pypdfium2_raw', 'pypdfium2.version',
        'comtypes', 'comtypes.client', 'comtypes.stream',
        'PIL', 'PIL.Image', 'PIL.PngImagePlugin',
        'deck_io',
    ],
    excludes=excl,
    noarchive=False,
)
def _keep(entry):
    dst = entry[0].replace('/', '\\').lower()
    if 'pyside6\\qml\\' in dst or 'pyside6\\resources\\' in dst:
        return False
    base = dst.rsplit('\\', 1)[-1]
    if base.startswith(('qt6webengine', 'qtwebengine', 'qt6quick', 'qt6qml', 'qt6pdf', 'qt6webchannel', 'qt6positioning', 'opengl32sw')):
        return False
    if 'pyside6\\translations\\' in dst and not dst.endswith('en-us.pak'):
        return False
    return True
a.datas = [e for e in a.datas if _keep(e)]
a.binaries = [e for e in a.binaries if _keep(e)]
pyz = PYZ(a.pure)
if ONEFILE:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='AGE OF CHICS Portable', console=False, upx=False,
              version='version.txt', icon=['assets/logo.ico'])
else:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='AGE OF CHICS', console=False, upx=False,
              version='version.txt', icon=['assets/logo.ico'])
    coll = COLLECT(exe, a.binaries, a.datas, upx=False, name='AGE OF CHICS')
