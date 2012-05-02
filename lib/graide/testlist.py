
from PySide import QtGui
from xml.etree import ElementTree as et
from graide.test import Test
import os

class TestList(QtGui.QWidget) :

    def __init__(self, app, fname = None, parent = None) :
        super(TestList, self).__init__(parent)
        self.app = app
        self.tests = []
        self.vbox = QtGui.QVBoxLayout()
        self.list = QtGui.QListWidget(self)
        self.list.itemDoubleClicked.connect(self.loadTest)
        self.vbox.addWidget(self.list)
        self.bbox = QtGui.QWidget(self)
        self.hbbox = QtGui.QHBoxLayout()
        self.bbox.setLayout(self.hbbox)
        self.vbox.addWidget(self.bbox)
        self.bEdit = QtGui.QToolButton(self.bbox)
        self.bEdit.setIcon(QtGui.QIcon.fromTheme('document-properties'))
        self.bEdit.setToolTip('edit test')
        self.bEdit.clicked.connect(self.editClicked)
        self.hbbox.addWidget(self.bEdit)
        self.bAdd = QtGui.QToolButton(self.bbox)
        self.bAdd.setIcon(QtGui.QIcon.fromTheme('add'))
        self.bAdd.setToolTip('add new test')
        self.bAdd.clicked.connect(self.addClicked)
        self.hbbox.addWidget(self.bAdd)
        self.bDel = QtGui.QToolButton(self.bbox)
        self.bDel.setIcon(QtGui.QIcon.fromTheme('remove'))
        self.bDel.setToolTip('delete test')
        self.bDel.clicked.connect(self.delClicked)
        self.hbbox.addWidget(self.bDel)
        self.setLayout(self.vbox)

        if fname and os.path.exists(fname) :
            try :
                e = et.parse(fname)
            except :
                pass
            else :
                for t in e.iterfind('test') :
                    feats = {}
                    f = t.get('feats')
                    if f :
                        for ft in f.split(" ") :
                            (k, v) = ft.split('=')
                            feats[k] = int(v)
                    te = Test(t.text, feats, t.get('rtl'), t.get('name'))
                    self.appendTest(te)

    def appendTest(self, t) :
        self.tests.append(t)
        QtGui.QListWidgetItem(t.name, self.list)

    def editTest(self, index) :
        t = self.tests[index]
        t.editDialog(self.app)
        self.list.item(index).setText(t.name)

    def writeXML(self, fname) :
        e = et.Element('tests')
        e.text = "\n"
        for t in self.tests :
            t.addTree(e)
        et.ElementTree(e).write(fname, encoding="utf-8", xml_declaration=True)

    def editClicked(self) :
        self.editTest(self.list.currentRow())

    def addClicked(self) :
        t = Test('', {})
        self.appendTest(t)
        self.editTest(len(self.tests) - 1)

    def delClicked(self) :
        i = self.list.currentRow()
        self.tests.pop(i)
        self.list.takeItem(i)

    def loadTest(self, item) :
        i = self.list.currentRow()
        self.app.setRun(self.tests[i])
