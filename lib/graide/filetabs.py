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
from graide.utils import configintval, configval
from graide.layout import Layout
import os, codecs

class FindDialog(QtGui.QDialog) :

    def __init__(self, parent = None) :
        super(FindDialog, self).__init__(parent)
        self.hb = QtGui.QHBoxLayout(self)
        self.text = QtGui.QLineEdit(self)
        self.text.returnPressed.connect(self.searchFwd)
        self.hb.addWidget(self.text)
        self.bBack = QtGui.QToolButton(self)
        self.bBack.setArrowType(QtCore.Qt.UpArrow)
        self.bBack.clicked.connect(self.searchBkwd)
        self.hb.addWidget(self.bBack)
        self.bFwd = QtGui.QToolButton(self)
        self.bFwd.setArrowType(QtCore.Qt.DownArrow)
        self.bFwd.clicked.connect(self.searchFwd)
        self.hb.addWidget(self.bFwd)
        self.bClose = QtGui.QToolButton(self)
        self.bClose.setIcon(QtGui.QIcon.fromTheme('window-close', QtGui.QIcon(":/images/window-close.png")))
        self.bClose.clicked.connect(self.closeDialog)
        self.hb.addWidget(self.bClose)

    def searchFwd(self) :
        t = self.text.text()
        if not t : return
        self.parent().find(t)

    def searchBkwd(self) :
        t = self.text.text()
        if not t : return
        self.parent().find(t, QtGui.QTextDocument.FindBackward)

    def closeDialog(self) :
        self.hide()
        self.parent().closedSearch()

    def openDialog(self) :
        self.show()
        #self.raise_()
        #self.activateWindow()
        self.text.setFocus(QtCore.Qt.MouseFocusReason)
        return True


class EditFile(QtGui.QPlainTextEdit) :

    highlighFormat = None

    def __init__(self, fname, abspath, fileTabs, size = 14, fontspec = 'mono', tabstop = 40) :
        super(EditFile, self).__init__()
        self.fname = fname
        self.abspath = abspath
        self.fileTabs = fileTabs
        self.selection = QtGui.QTextEdit.ExtraSelection()
        self.selection.format = QtGui.QTextCharFormat()
        self.selection.format.setBackground(QtGui.QColor(QtCore.Qt.yellow))
        self.selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
        
        font = QtGui.QFont(fontspec)
        font.setPointSize(size)
        self.setFont(font)
        self.setTabStopWidth(tabstop)

        try :
            self.fileTabs.addOpenFile(self.fname)
            f = codecs.open(fname, encoding="UTF-8")
            self.setPlainText("".join(f.readlines()))
            f.close()
        except :
            self.setPlainText("")
        a = QtGui.QAction(self)
        a.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_F))
        a.triggered.connect(self.search)
        self.addAction(a)
        self.fDialog = FindDialog(self)
        self.fIsOpen = False

    def highlight(self, lineno) :
        self.selection.cursor = QtGui.QTextCursor(self.document().findBlockByNumber(lineno))
        self.setExtraSelections([self.selection])
        self.setTextCursor(self.selection.cursor)

    def unhighlight(self, lineno) :
        self.setExtraSelections([])

    def writeIfModified(self) :
        if self.document().isModified() :
            f = codecs.open(self.fname, "w", encoding="UTF-8")
            f.write(self.document().toPlainText())
            f.close()
            self.document().setModified(False)
            return True
        else :
            return False

    def setSize(self, size) :
        f = self.font()
        f.setPointSize(size)
        self.setFont(f)
        
    def updateFont(self, fontspec, size) :
        font = QtGui.QFont(fontspec)
        font.setPointSize(size)
        self.setFont(font)
        
    def updateTabstop(self, tabstop) :
    	self.setTabStopWidth(tabstop)

    def reload(self) :
        f = file(self.fname)
        self.setPlainText("".join(f.readlines()))
        f.close()

    def closeEvent(self, event) :
        self.fileTabs.deleteOpenFile(self.fname)
        self.writeIfModified()
        self.fDialog.close()

    def search(self) :
        self.fDialog.openDialog()
        self.fIsOpen = True

    def closedSearch(self) :
        self.fIsOpen = False

    def lostFocus(self) :
        self.fDialog.hide()

    def gainedFocus(self) :
        if self.fIsOpen :
            self.fDialog.show()
        selectedText = self.textCursor().selectedText()
        self.fileTabs.setSelectedText(selectedText)
            
    def mouseReleaseEvent(self, event) :
        super(EditFile,self).mouseReleaseEvent(event)
        selectedText = self.textCursor().selectedText()
        self.fileTabs.setSelectedText(selectedText)
        
    def mouseDoubleClickEvent(self, event) :
        super(EditFile,self).mouseDoubleClickEvent(event)
        selectedText = self.textCursor().selectedText()
        self.fileTabs.setSelectedText(selectedText)


# The window containing all the code files.
class FileTabs(QtGui.QTabWidget) :

    def __init__(self, config, app, parent = None) :
        super(FileTabs, self).__init__(parent)
        self.setActions(app)

        self.tabCloseRequested.connect(self.closeRequest)
        self.setContentsMargins(*Layout.buttonMargins)
        self.currentChanged.connect(self.switchFile)
        self.bbox = QtGui.QWidget(self)
        self.setCornerWidget(self.bbox)
        self.hbox = QtGui.QHBoxLayout()
        self.bbox.setLayout(self.hbox)
        self.hbox.setContentsMargins(*Layout.buttonMargins)
        self.hbox.setSpacing(Layout.buttonSpacing)
        self.hbox.insertStretch(0)
        self.bBuild = QtGui.QToolButton(self.bbox)
        self.bBuild.setDefaultAction(self.aBuild)
        self.hbox.addWidget(self.bBuild)
        self.bSave = QtGui.QToolButton(self.bbox)
        self.bSave.setDefaultAction(self.aSave)
        self.hbox.addWidget(self.bSave)
        self.bAdd = QtGui.QToolButton(self.bbox)
        self.bAdd.setDefaultAction(self.aAdd)
        self.hbox.addWidget(self.bAdd)
        self.currselIndex = None
        self.currselline = 0
        self.app = app
        self.currIndex = -1
        self.size = configintval(config, 'ui', 'textsize') or 14
        self.fontspec = configval(config, 'ui', 'editorfont') or 'mono'
        self.tabstop = configintval(config, 'ui', 'tabstop') or 40
        if self.app.config.has_option('window', 'openfiles') :
            openFileString = configval(config, 'window', 'openfiles')
            self.openFiles = openFileString.split(';')
            self.openFiles.remove('')
        else :
            self.openFiles = []
        self.selectedText = ''

    def setActions(self, app) :
        self.aBuild = QtGui.QAction(QtGui.QIcon.fromTheme("run-build", QtGui.QIcon(":/images/run-build.png")), "&Build", app)
        self.aBuild.setToolTip("Save files and force rebuild")
        self.aBuild.triggered.connect(app.buildClicked)
        self.aSave = QtGui.QAction(QtGui.QIcon.fromTheme('document-save', QtGui.QIcon(":/images/document-save.png")), "&Save File", app)
        self.aSave.setToolTip('Save all files')
        self.aSave.triggered.connect(self.writeIfModified)
        self.aAdd = QtGui.QAction(QtGui.QIcon.fromTheme('document-open', QtGui.QIcon(":/images/document-open.png")), "&Open File ...", app)
        self.aAdd.setToolTip('Open file in editor')
        self.aAdd.triggered.connect(self.addClicked)

    def selectLine(self, fname, lineno) :
        for i in range(self.count()) :
            f = self.widget(i)
            if f.abspath == os.path.abspath(fname) :
                self.highlightLine(i, lineno)
                return
        newFile = EditFile(fname, os.path.abspath(fname), self, size = self.size, fontspec = self.fontspec, tabstop = self.tabstop)
        self.addTab(newFile, fname)
        self.highlightLine(self.count() - 1, lineno)
        apgdlfile = configval(self.app.config, 'build', 'makegdlfile')
        if apgdlfile and os.path.abspath(apgdlfile) == os.path.abspath(fname) :
            newFile.setReadOnly(True)

    def highlightLine(self, tabindex, lineno) :
        if lineno >= 0 :
            if self.currselIndex is not None and self.currselIndex > -1 and (self.currselIndex != tabindex or self.currselline != lineno) :
                self.widget(self.currselIndex).unhighlight(self.currselline)
            self.widget(tabindex).highlight(lineno)
            self.currselIndex = tabindex
            self.currselline = lineno
        self.setCurrentIndex(tabindex)

    def writeIfModified(self) :
        res = False
        for i in range(self.count()) :
            res = res | self.widget(i).writeIfModified()
        return res

    def closeRequest(self, index) :
        if index == self.currselIndex :
            self.currselIndex = -1
        self.widget(index).close()
        self.removeTab(index)

    def closeAllTabs(self) :
        while self.widget(0) :
            self.widget(0).close()
            self.removeTab(0)
        self.openFiles = []

    def addClicked(self) :        
        fname = os.path.relpath(QtGui.QFileDialog.getOpenFileName(self)[0])
        self.selectLine(fname, -1)
        self.updateFromConfigSettings(self.app.config)

    def updateFileEdit(self, fname) :
        for i in range(self.count()) :
            f = self.widget(i)
            if f.fname == fname :
                f.reload()
                break

    def switchFile(self, widget) :
        if (self.widget(0) == 0 ) :   # no tabs
            return
        
        if self.currIndex > -1 and self.widget(self.currIndex) :
        	self.widget(self.currIndex).lostFocus()
        self.currIndex = self.currentIndex()
        if self.widget(self.currIndex) :
            self.widget(self.currIndex).gainedFocus()
        
    def setSelectedText(self, text) :
        self.selectedText = text

    def setSize(self, size) :
        for i in range(self.count()) :
            self.widget(i).setSize(size)
            
    def updateFont(self, fontspec, size) :
        for i in range(self.count()) :
            self.widget(i).updateFont(fontspec, size)
            
    def updateTabstop(self, tabstop) :
        for i in range(self.count()) :
            self.widget(i).updateTabstop(tabstop)

    def updateFromConfigSettings(self, config) :
        editorfont = config.get('ui', 'editorfont') if config.has_option('ui', 'editorfont') else "monospace"
        fontsize = config.get('ui', 'textsize') if config.has_option('ui', 'textsize') else "10"
        fontsize = int(fontsize)
        self.updateFont(editorfont, fontsize)
        
        tabstop = config.get('ui', 'tabstop') if config.has_option('ui', 'tabstop') else 10
        tabstop = int(tabstop)
        self.updateTabstop(tabstop)

    def addOpenFile(self, filename) :
        if filename != '' :
            for f in self.openFiles :
                if f == filename :
                    return
            self.openFiles.append(filename)
            self.saveOpenFiles()

    def deleteOpenFile(self, filename) :
        self.openFiles.remove(filename)
        self.saveOpenFiles()
    
    def saveOpenFiles(self) :
        openFileString = ''
        for f in self.openFiles :
            openFileString = openFileString + f + ';'
        self.app.config.set('window', 'openfiles', openFileString)
		