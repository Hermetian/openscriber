# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['openscriber/openscriber.py'],
    pathex=[],
    binaries=[],
    datas=[('prompts_config.json', '.'), ('models', 'models')],
    hiddenimports=['huggingface_hub', 'ctransformers', 'whisper', 'pyaudio', 'cryptography', 'numpy', 'hashlib'],
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
    [],
    exclude_binaries=True,
    name='OpenScriber',
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
    icon=['app_icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenScriber',
)
app = BUNDLE(
    coll,
    name='OpenScriber.app',
    icon='app_icon.icns',
    bundle_identifier='com.openscriber.openscriber',
)
