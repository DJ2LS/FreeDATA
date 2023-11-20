# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

# DAEMON --------------------------------------------------
server_a = Analysis(['server.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
server_pyz = PYZ(server_a.pure, server_a.zipped_data,
             cipher=block_cipher)

server_exe = EXE(server_pyz,
          server_a.scripts,
          [],
          exclude_binaries=True,
          name='freedata-server',
          bundle_identifier='app.freedata.freedata-server',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
          
# add lib folder to system path. We only need to do this once
server_a.datas += Tree('lib', prefix='lib')
# daemon_a.datas += Tree('./codec2', prefix='codec2')



coll = COLLECT(server_exe,
               server_a.binaries,
               server_a.zipfiles,
               server_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='modem')
