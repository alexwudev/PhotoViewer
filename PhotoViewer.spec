# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['photo_viewer.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['comtypes.client'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtQml', 'PyQt6.QtQuick', 'PyQt6.QtQuick3D', 'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets', 'PyQt6.QtNetwork', 'PyQt6.QtSql', 'PyQt6.QtPdf', 'PyQt6.QtCharts', 'PyQt6.Qt3DCore', 'PyQt6.QtDataVisualization', 'PyQt6.QtTest', 'PyQt6.QtBluetooth', 'PyQt6.QtSerialPort', 'PyQt6.QtPositioning', 'PyQt6.QtSensors', 'PyQt6.QtNfc'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhotoViewer',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhotoViewer',
)
