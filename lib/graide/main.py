#!/usr/bin/python

from graide.font import Font
from graide.run import Run
from graide.attribview import AttribView
from graide.fontview import FontView
from graide.runview import RunView, RunModel
from graide.passes import PassesView
from graide.ruledialog import RuleDialog
from graide.gdx import Gdx
from graide.filetabs import FileTabs
from graide.utils import runGraphite
from graide.featureselector import FeatureRefs, FeatureDialog
from graide.testlist import TestList
from PySide import QtCore, QtGui
from tempfile import NamedTemporaryFile
import json, os

class MainWindow(QtGui.QMainWindow) :

    def __init__(self, config, jsonfile) :
        super(MainWindow, self).__init__()
        self.rules = None
        self.runfile = None
        self.runloaded = False
        self.fDialog = None

        if config.has_option('main', 'font') :
            if config.has_option('main', 'size') :
                fontsize = config.getint('main', 'size')
            else :
                fontsize = 40
            self.fontfile = config.get('main', 'font')
            self.font = Font()
            self.font.loadFont(self.fontfile, config.get('main', 'ap') if config.has_option('main', 'ap') else None)
            self.font.makebitmaps(fontsize)
            self.feats = FeatureRefs(self.fontfile)
        else :
            self.font = None

        if jsonfile :
            f = file(jsonfile)
            self.json = json.load(f)
            f.close()
        else :
            self.json = None

        if config.has_option('main', 'gdx') :
            self.gdx = Gdx()
            self.gdx.readfile(config.get('main', 'gdx'))
        else :
            self.gdx = None

        if config.has_option('main', 'testsfile') :
            self.testsfile = config.get('main', 'testsfile')
        else :
            self.testsfile = None

        self.setupUi()
        self.createActions()
        self.createToolBars()
        self.createStatusBar()

    def closeEvent(self, event) :
        if self.rules :
            self.rules.close()
        event.accept()

    def setupUi(self) :
        self.resize(994, 696)
        self.centralwidget = QtGui.QWidget(self)
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.vsplitter = QtGui.QSplitter(self.centralwidget)
        self.vsplitter.setOrientation(QtCore.Qt.Vertical)
        self.vsplitter.setHandleWidth(2)

        self.widget = QtGui.QWidget(self.vsplitter)
        self.setwidgetstretch(self.widget, 100, 55)
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.hsplitter = QtGui.QSplitter(self.widget)
        self.hsplitter.setOrientation(QtCore.Qt.Horizontal)
        self.hsplitter.setHandleWidth(4)

        self.tabInfo = QtGui.QTabWidget(self.hsplitter)
        self.setwidgetstretch(self.tabInfo, 30, 100)
        self.tab_glyph = AttribView()
        self.tabInfo.addTab(self.tab_glyph, "Glyph")
        self.tab_slot = AttribView()
        self.tabInfo.addTab(self.tab_slot, "Slot")
        self.tab_classes = QtGui.QWidget()
        self.tabInfo.addTab(self.tab_classes, "Classes")
        self.buttonTool = QtGui.QToolButton()
        self.buttonTool.setArrowType(QtCore.Qt.DownArrow)
        self.tabInfo.setCornerWidget(self.buttonTool)

        self.tabEdit = FileTabs(self.hsplitter)
        self.setwidgetstretch(self.tabEdit, 40, 100)
        self.tabEdit.setTabsClosable(True)
        self.buttonEdit = QtGui.QToolButton()
        self.buttonEdit.setArrowType(QtCore.Qt.DownArrow)
        self.tabEdit.setCornerWidget(self.buttonEdit)

        self.tabTest = TestList(self, self.testsfile, parent = self.hsplitter)
        self.setwidgetstretch(self.tabTest, 30, 100)

        self.horizontalLayout.addWidget(self.hsplitter)

        self.tabResults = QtGui.QTabWidget(self.vsplitter)
        self.setwidgetstretch(self.tabResults, 100, 45)
        self.tabResults.setTabPosition(QtGui.QTabWidget.South)

        self.tab_font = FontView(self.font)
        self.tabResults.addTab(self.tab_font, "Font")

        self.tab_errors = QtGui.QWidget()
        self.tabResults.addTab(self.tab_errors, "Errors")
        self.tab_results = QtGui.QWidget()
        self.tab_vbox = QtGui.QVBoxLayout(self.tab_results)
        self.tab_vbox.setSpacing(0)
        self.tab_results_editor = QtGui.QWidget()
        self.tab_hbox = QtGui.QHBoxLayout(self.tab_results_editor)
        self.runEdit = QtGui.QLineEdit(self.tab_results_editor)
        self.runEdit.returnPressed.connect(self.runClicked)
        self.tab_hbox.addWidget(self.runEdit)
        self.tab_hbox.setContentsMargins(0, 2, 0, 2)
        self.runRtl = QtGui.QCheckBox("RTL", self.tab_results_editor)
        self.tab_hbox.addWidget(self.runRtl)
        self.runFeats = QtGui.QPushButton("Features", self.tab_results_editor)
        self.runFeats.clicked.connect(self.featuresClicked)
        self.tab_hbox.addWidget(self.runFeats)
        self.runGo = QtGui.QPushButton("Run", self.tab_results_editor)
        self.runGo.clicked.connect(self.runClicked)
        self.tab_hbox.addWidget(self.runGo)
        self.runSave = QtGui.QPushButton("Save", self.tab_results_editor)
        self.runSave.clicked.connect(self.runSaveClicked)
        self.tab_hbox.addWidget(self.runSave)
        self.tab_vbox.addWidget(self.tab_results_editor)
        self.run = Run()
        self.runView = RunView()
        self.tab_vbox.addWidget(self.runView)
        self.tab_vbox.addStretch()
        self.tabResults.addTab(self.tab_results, "Results")

        self.tab_passes = PassesView()
        self.tab_passes.slotSelected.connect(self.tab_slot.changeData)
        self.tab_passes.glyphSelected.connect(self.tab_glyph.changeData)
        self.tab_passes.rowActivated.connect(self.ruledialog)
        self.tabResults.addTab(self.tab_passes, "Passes")
        if self.json :
            self.run.addslots(self.json['output'])
            self.runView.set_run(self.run, self.font)
            self.runView.model.slotSelected.connect(self.tab_slot.changeData)
            self.runView.model.glyphSelected.connect(self.tab_glyph.changeData)
            self.tab_passes.loadResults(self.font, self.json['passes'], self.gdx)
            self.runloaded = True
        self.verticalLayout.addWidget(self.vsplitter)
        self.setCentralWidget(self.centralwidget)
        self.tab_font.changeGlyph.connect(self.tab_glyph.changeData)
        self.tabResults.currentChanged.connect(self.setrunEditFocus)

    def setwidgetstretch(self, widget, hori, vert) :
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        if hori != 100 : sizePolicy.setHorizontalStretch(hori)
        if vert != 100 : sizePolicy.setVerticalStretch(vert)
        sizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        size = self.size()
        widget.resize(QtCore.QSize(size.width() * hori / 100, size.height() * vert / 100))
        widget.setSizePolicy(sizePolicy)

    def createActions(self) :
        pass

    def createToolBars(self) :
        pass

    def createStatusBar(self) :
        pass

    def closeEvent(self, event) :
        if self.testsfile :
            self.tabTest.writeXML(self.testsfile)

    def ruledialog(self, row, model) :
        if self.rules : self.rules.close()
        else : self.rules = RuleDialog(self)
        self.ruleView = PassesView(parent = self.rules, index = row)
        self.ruleView.loadRules(self.font, self.json['passes'][row]['rules'], model.run, self.gdx)
        self.ruleView.slotSelected.connect(self.tab_slot.changeData)
        self.ruleView.glyphSelected.connect(self.tab_glyph.changeData)
        self.ruleView.rowActivated.connect(self.ruleSelected)
        self.rules.setView(self.ruleView, "Pass %d" % (row + 1))
        self.rules.show()

    def rulesclosed(self, dialog) :
        self.ruleView.slotSelected.disconnect()
        self.ruleView.glyphSelected.disconnect()
        self.ruleView = None

    def ruleSelected(self, row, model) :
        if self.gdx and hasattr(model.run, 'passindex') :
            rule = self.gdx.passes[model.run.passindex][model.run.ruleindex]
            self.tabEdit.selectLine(rule.srcfile, rule.srcline)

    def setRun(self, test) :
        self.runRtl.setChecked(True if test.rtl else False)
        self.runEdit.setText(test.text)
        if not self.fDialog :
            self.fDialog = FeatureDialog(self)
        self.fDialog.set_feats(self.feats, test.feats)

    def runClicked(self) :
        runfile = NamedTemporaryFile(mode="rw")
        text = self.runEdit.text().decode('unicode_escape')
        runGraphite(self.fontfile, text, runfile, size = self.font.size, rtl = self.runRtl.isChecked(),
            feats = self.fDialog.get_feats() if self.fDialog else self.feats.fval)
        runfile.seek(0)
        self.json = json.load(runfile)
        runfile.close()
        self.run = Run()
        self.run.addslots(self.json['output'])
        self.runView.set_run(self.run, self.font)
        if not self.runloaded :
            self.runView.model.slotSelected.connect(self.tab_slot.changeData)
            self.runView.model.glyphSelected.connect(self.tab_glyph.changeData)
            self.runloaded = True
        self.tab_passes.loadResults(self.font, self.json['passes'], self.gdx)

    def runSaveClicked(self) :
        f = file("graide.json", "w")
        json.dump(self.json, f)
        f.close()

    def featuresClicked(self) :
        if self.font :
            if not self.fDialog :
                self.fDialog = FeatureDialog(self)
                self.fDialog.set_feats(self.feats)
            self.fDialog.show()

    def setrunEditFocus(self, widget) :
        if (isinstance(widget, QtGui.QWidget) and widget == self.tab_results) \
                or (not isinstance(widget, QtGui.QWidget) and widget == 2) :
            self.runEdit.setFocus(QtCore.Qt.MouseFocusReason)

if __name__ == "__main__" :
    from argparse import ArgumentParser
    import sys

    app = QtGui.QApplication(sys.argv)
    p = ArgumentParser()
    p.add_argument("font", help="Font .ttf file to process")
    p.add_argument("-a","--ap",help="AP XML database file for font")
    p.add_argument("-r","--results",help="graphite JSON debug output")
    args = p.parse_args()

    if args.font :
        mainWindow = MainWindow(args.font, args.ap, args.results, 40)
        mainWindow.show()
        sys.exit(app.exec_())
