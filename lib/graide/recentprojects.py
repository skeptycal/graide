#    Copyright 2012, SIL International
#    All rights reserved.
#
#    This library is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation; either version 2.1 of License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should also have received a copy of the GNU Lesser General Public
#    License along with this library in the file named "LICENSE".
#    If not, write to the Free Software Foundation, 51 Franklin Street,
#    suite 500, Boston, MA 02110-1335, USA or visit their web page on the 
#    internet at http://www.fsf.org/licenses/lgpl.html.


from PySide import QtCore, QtGui
from graide.utils import configval, configintval
import _winreg
import os


class RecentProjectList(object) :

    def __init__(self) :
        self.maxCount = 4
        
        filesAbsPath = self.getFileList_Win()  # TODO: extend for other OSes
        self.files = []
        for f in filesAbsPath :
            basename = os.path.basename(f)
            self.files.append((basename, f))
        self.limitFileList()

    # Ensure any changes are saved.
    def saveFiles(self) :
        self._save_Win(self._absFiles())        # TODO: extend for other OSes

    # Add a project to the list, keeping the list to the specified length.
    def addProject(self, fname) :
        abspath = os.path.abspath(fname)
        for x in self.files :
            (xf,xa) = x
            if xf == fname and xa == abspath :
                self.files.remove(x)
                break
            
        self.files.insert(0, (fname,abspath))
        self.limitFileList()

        self.putFileList_Win(self._absFiles())  # TODO: extend for other OSes

    # Return the list of projects.
    def projects(self) :
        return self.files

    def _absFiles(self) :
        absFiles = []
        for (bname, aname) in self.files :
            absFiles.append(aname)
        return absFiles

    def limitFileList(self) :
        # Only keep 4
        while (len(self.files) > self.maxCount) :
            self.files.remove(self.files[-1])

    def close(self) :
        self._close_Win()  # TODO: extend for other OSes


### Windows registry routines ###

    # On Windows, get the list from the registry.
    def getFileList_Win(self) :
        self.regPath = r"\Software\SIL\Graide\RecentProjects"
        h1 = _winreg.ConnectRegistry(None, _winreg.HKEY_CURRENT_USER)
        # Add the keys for the path
        h2 = _winreg.CreateKeyEx(h1, "Software", 0, _winreg.KEY_ALL_ACCESS)
        h3 = _winreg.CreateKeyEx(h2, "SIL", 0, _winreg.KEY_ALL_ACCESS)
        h4 = _winreg.CreateKeyEx(h3, "Graide", 0, _winreg.KEY_ALL_ACCESS)
        self.regKey = _winreg.CreateKeyEx(h4, "RecentProjects", 0, _winreg.KEY_ALL_ACCESS)

        value = _winreg.QueryValue(self.regKey, None)
        files = value.split(';')
        files.remove('')
        return files

    def putFileList_Win(self, files) :
        fileString = ""
        for f in files :
            fileString = fileString + f + ';'
        _winreg.SetValue(self.regKey, None, _winreg.REG_SZ, fileString)
        # _winreg.FlushKey(self.regKey) - documentation says this is not required
        
    def _save_Win(self, files) :
        self.putFileList_Win(files)

    def _close_Win(self) :
        _winreg.CloseKey(self.regKey)

