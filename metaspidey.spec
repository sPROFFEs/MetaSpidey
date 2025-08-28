# -*- mode: python ; coding: utf-8 -*-

import os
import platform

# Determine the name of the ffuf binary
ffuf_binary = 'ffuf.exe' if platform.system() == 'Windows' else 'ffuf'
ffuf_path = os.path.join('bin', ffuf_binary)

# Define the data to be included (the ffuf binary)
# The second part of the tuple is the destination directory inside the bundle.
datas = [(ffuf_path, 'bin')]

a = Analysis(['launch.py'],
             pathex=['.'],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=None)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='MetaSpidey',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True ) # Use console=False for a GUI-only application on Windows
