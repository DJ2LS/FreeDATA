# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

# DAEMON --------------------------------------------------
daemon_a = Analysis(['daemon.py'],
             pathex=[],
             binaries=[],
             datas=[( './lib/hamlib/linux/python3.8/site-packages/libhamlib.so.4', '.' )],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
daemon_pyz = PYZ(daemon_a.pure, daemon_a.zipped_data,
             cipher=block_cipher)

daemon_exe = EXE(daemon_pyz,
          daemon_a.scripts, 
          [],
          exclude_binaries=True,
          name='freedata-daemon',
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
daemon_a.datas += Tree('lib', prefix='lib')
# daemon_a.datas += Tree('./codec2', prefix='codec2')


# TNC --------------------------------------------------
tnc_a = Analysis(['main.py'],
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
tnc_pyz = PYZ(tnc_a.pure, tnc_a.zipped_data,
             cipher=block_cipher)

tnc_exe = EXE(tnc_pyz,
          tnc_a.scripts, 
          [],
          exclude_binaries=True,
          name='freedata-tnc',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )


coll = COLLECT(daemon_exe,
               daemon_a.binaries,
               daemon_a.zipfiles,
               daemon_a.datas,
               tnc_exe,
               tnc_a.binaries,
               tnc_a.zipfiles,
               tnc_a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='tnc')
