# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

# Increase recursion limit
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

distinctipy_module = collect_submodules('distinctipy')
distinctipy_meta = copy_metadata('distinctipy')

block_cipher = None

a = Analysis(['src/ElroiKit.py'],
             pathex=['/src'],
             binaries=[],
             datas=[
                ('ico\\', 'ico'), 
                ('rsrc\\', 'rsrc'), 
                ('font\\', 'font'), 
             ] + distinctipy_meta,
             hiddenimports=distinctipy_module,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='ElroiKit',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          uac_admin=True,
          icon='ico\\E.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ElroiKit')
