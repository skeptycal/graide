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
import json

class ContextToolButton(QtGui.QToolButton) :
    rightClick = QtCore.Signal(QtGui.QContextMenuEvent)

    def contextMenuEvent(self, event) :
        self.rightClick.emit(event)

class DebugMenu(QtGui.QMenu) :

    def __init__(self, app, parent = None) :
        super(DebugMenu, self).__init__(parent)
        self.app = app

        self.addAction('Reload Font').triggered.connect(self.reloadFont)
        self.addAction('Save Run as JSON').triggered.connect(self.runSave)

    def reloadFont(self) :
        self.app.loadFont(self.app.fontFileName)

    def runSave(self) :
        f = file('_graide.json', 'w')
        json.dump(self.app.json, f, indent=2)
        f.close()
