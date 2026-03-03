# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main_bt_button_v2.py'],
    pathex=[],
    binaries=[],
    datas=[('src/TheTab_KGrgb_72ppi.png', './src'), ('SortingExperiment.env', './experimentSettings.env'), ('camera_10_14_2025b.json', './camera_10_14_2025b.json')],
    hiddenimports=['tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FOW_Sorting_Experiment_phase_1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
