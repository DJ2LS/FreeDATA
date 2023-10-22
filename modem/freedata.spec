# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

# DAEMON --------------------------------------------------
daemon_a = Analysis(['daemon.py'],
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
daemon_pyz = PYZ(daemon_a.pure, daemon_a.zipped_data,
             cipher=block_cipher)

daemon_exe = EXE(daemon_pyz,
          daemon_a.scripts, 
          [],
          exclude_binaries=True,
          name='freedata-daemon',
          bundle_identifier='com.dj2ls.freedata-daemon',
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


# Modem --------------------------------------------------
modem_a = Analysis(['main.py'],
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
modem_pyz = PYZ(modem_a.pure, modem_a.zipped_data,
             cipher=block_cipher)

modem_exe = EXE(modem_pyz,
          modem_a.scripts, 
          [],
          exclude_binaries=True,
          name='freedata-modem',
          bundle_identifier='com.dj2ls.freedata-modem',
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
               modem_exe,
               modem_a.binaries,
               modem_a.zipfiles,
               modem_a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='modem')
