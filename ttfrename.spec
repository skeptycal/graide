# -*- mode: python -*-
import os, sys, platform

libdir = 'lib'
ext = ''
if sys.platform.startswith('linux') :
    libdir += '-linux-' + platform.machine() + '-2.7'
elif sys.platform == 'win32' :
    ext = '.exe'

a = Analysis(['ttfrename'],
             pathex=[os.path.dirname(sys.argv[0]), 'build/' + libdir],
             hiddenimports=['fontTools.ttLib.tables._p_o_s_t'],
	     excludes=['win32com', 'numpy.test', 'tcl', 'tk', '_tkinter'],
             hookspath=None)
pyz = PYZ(a.pure)
bins = a.binaries
# import pdb; pdb.set_trace()

exe = EXE(pyz,
          a.scripts,
          bins,
          a.zipfiles,
          a.datas,
          name=os.path.join('build', 'ttfrename' + ext),
          debug=False,
          strip=None,
          upx=True,
          console=True )
