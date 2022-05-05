'''
Last Modified: 2020-04-10

@author: Jesse M. Barr

Contains:
    -ExportDialog

Description:

ToDo:

'''
# PyQt5
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QVBoxLayout, QFileDialog, QStackedLayout,
                             QComboBox, QWidget, QMainWindow)
# import qdarkstyle
# PyQtGraph
from pyqtgraph import PlotWidget
# Local
from . import Exporter, ImageExporter, MPLExporter


class ExportDialog(QMainWindow):
    ExporterClasses = [ImageExporter, MPLExporter]

    def __init__(self, plot, *args, **kwargs):
        if not isinstance(plot, PlotWidget):
            raise Exception("Expected PlotWidget")
        super().__init__()
        # self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

        self.plot = plot
        self.exporters = {}

        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle("Export")
        self.resize(250, 375)
        self.initUI()

    def initUI(self):
        vLayout = QVBoxLayout()

        self.selection = QComboBox()
        vLayout.addWidget(self.selection)

        self.exporterWidgets = QStackedLayout()

        for e in self.ExporterClasses:
            self.selection.addItem(e.Name)
            self.exporters[e.Name] = self.exporterWidgets.addWidget(e(self.plot, self))

        self.selection.currentTextChanged.connect(self.showTool)

        vLayout.addLayout(self.exporterWidgets)

        ui = QWidget()
        ui.setLayout(vLayout)
        self.setCentralWidget(ui)

    def setTool(self, exp):
        if self.selection.currentText() == exp:
            return self.showTool(exp)
        self.selection.setCurrentText(exp)

    def showTool(self, exp):
        self.exporterWidgets.setCurrentIndex(self.exporters[exp])
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.raise_()
        self.activateWindow()

    def show(self, item=None):
        super().show()
