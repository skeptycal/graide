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

from PySide import QtGui, QtCore
from graide.utils import Layout
import os

class EditFile(QtGui.QPlainTextEdit) :

    highlighFormat = None

    def __init__(self, fname) :
        super(EditFile, self).__init__()
        self.fname = fname
        self.selection = QtGui.QTextEdit.ExtraSelection()
        self.selection.format = QtGui.QTextCharFormat()
        self.selection.format.setBackground(QtGui.QColor(QtCore.Qt.yellow))
        self.selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
        self.setFont(QtGui.QFont('mono'))
        self.setTabStopWidth(40)
#        self.setFontPointSize(10)
        f = file(fname)
        self.setPlainText("".join(f.readlines()))
        f.close()
        a = QtGui.QAction(self)
        a.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_F))
        a.triggered.connect(self.search)
        self.addAction(a)

    def highlight(self, lineno) :
        self.selection.cursor = QtGui.QTextCursor(self.document().findBlockByNumber(lineno))
        self.setExtraSelections([self.selection])
        self.setTextCursor(self.selection.cursor)

    def unhighlight(self, lineno) :
        self.setExtraSelections([])

    def writeIfModified(self) :
        if self.document().isModified() :
            f = file(self.fname, "w")
            f.write(self.document().toPlainText())
            f.close()
            self.document().setModified(False)
            return True
        else :
            return False

    def reload(self) :
        f = file(self.fname)
        self.setPlainText("".join(f.readlines()))
        f.close()

    def closeEvent(self, event) :
        self.writeIfModified()

    def search(self) :
        print "Searching"

class FileTabs(QtGui.QWidget) :

    def __init__(self, config, app, parent = None) :
        super(FileTabs, self).__init__(parent)
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.setContentsMargins(*Layout.buttonMargins)
        self.tabs = QtGui.QTabWidget(self)
        self.tabs.tabCloseRequested.connect(self.closeRequest)
        self.tabs.setContentsMargins(*Layout.buttonMargins)
        self.vbox.addWidget(self.tabs)
        self.bbox = QtGui.QWidget(self)
        self.vbox.addWidget(self.bbox)
        self.hbox = QtGui.QHBoxLayout()
        self.bbox.setLayout(self.hbox)
        self.hbox.setContentsMargins(*Layout.buttonMargins)
        self.hbox.setSpacing(Layout.buttonSpacing)
        self.hbox.insertStretch(0)
        self.bBuild = QtGui.QPushButton('Build', self.bbox)
        self.bBuild.setToolTip("Save files and force rebuild")
        self.bBuild.clicked.connect(app.buildClicked)
        self.hbox.addWidget(self.bBuild)
        self.bSave = QtGui.QToolButton(self.bbox)
        self.bSave.setIcon(QtGui.QIcon.fromTheme('document-save'))
        self.bSave.setToolTip('Save all files')
        self.bSave.clicked.connect(self.writeIfModified)
        self.hbox.addWidget(self.bSave)
        self.bAdd = QtGui.QToolButton(self.bbox)
        self.bAdd.setIcon(QtGui.QIcon.fromTheme('document-open'))
        self.bAdd.setToolTip('open file in editor')
        self.bAdd.clicked.connect(self.addClicked)
        self.hbox.addWidget(self.bAdd)
        self.setLayout(self.vbox)
        self.currselIndex = None
        self.currselline = 0
        self.config = config

    def selectLine(self, fname, lineno) :
        for i in range(self.tabs.count()) :
            f = self.tabs.widget(i)
            if f.fname == fname :
                self.highlightLine(i, lineno)
                return
        newFile = EditFile(fname)
        self.tabs.addTab(newFile, fname)
        self.highlightLine(self.tabs.count() - 1, lineno)
        if self.config.has_option('build', 'gdlfile') and os.path.abspath(self.config.get('build', 'gdlfile')) == os.path.abspath(fname) :
            newFile.setReadOnly(True)

    def highlightLine(self, tabindex, lineno) :
        if lineno >= 0 :
            if self.currselIndex != None and (self.currselIndex != tabindex or self.currselline != lineno) :
                self.tabs.widget(self.currselIndex).unhighlight(self.currselline)
            self.tabs.widget(tabindex).highlight(lineno)
            self.currselIndex = tabindex
            self.currselline = lineno
        self.tabs.setCurrentIndex(tabindex)

    def writeIfModified(self) :
        res = False
        for i in range(self.tabs.count()) :
            res = res | self.tabs.widget(i).writeIfModified()
        return res

    def closeRequest(self, index) :
        self.tabs.widget(index).close()
        self.tabs.removeTab(index)

    def addClicked(self) :
        fname = os.path.relpath(QtGui.QFileDialog.getOpenFileName(self)[0])
        self.selectLine(fname, -1)

    def updateFileEdit(self, fname) :
        for i in range(self.tabs.count()) :
            f = self.tabs.widget(i)
            if f.name == fname :
                f.reload()
                break

