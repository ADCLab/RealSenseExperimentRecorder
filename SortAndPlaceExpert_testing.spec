# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main_app.py'],
    pathex=[],
    binaries=[],
    datas=[('src/TheTab_KGrgb_72ppi.png', './src'), ('/data/UCF Dropbox/Adan Vela/git-ucf/RealSenseExperimentRecorder/settings/env/ExpertSortPlaceExperiment_TESTING_grrrr.env', './experimentSettings.env'), ('/data/UCF Dropbox/Adan Vela/git-ucf/RealSenseExperimentRecorder/settings/camera/calibration_20260204_v1.json', './/data/UCF Dropbox/Adan Vela/git-ucf/RealSenseExperimentRecorder/settings/camera/calibration_20260204_v1.json')],
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
    name='SortAndPlaceExpert_testing',
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
