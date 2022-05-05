# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

a = Analysis(['./src/Main.py'],
             pathex=[],
             binaries=[],
             datas=[
                ('./resources', 'resources'),
                *collect_data_files('acestatpy')
            ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='ACEstatGUI',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon='resources/icons/usace_logo.ico' )
