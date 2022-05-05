'''
Last Modified: 2020-04-10

@author: Jesse M. Barr

Contains:
    -ImageExporter

Description:

ToDo:

'''
# PyQt5
from PyQt5.QtGui import QImageWriter
from PyQt5.QtWidgets import QLabel, QMessageBox
# PyQtGraph
from pyqtgraph.parametertree import ParameterTree
from pyqtgraph.exporters import ImageExporter as pyqtgraphImageExporter
# Local
from .Exporter import Exporter

IMGFormats = ["*."+f.data().decode('utf-8') for f in QImageWriter.supportedImageFormats()]
preferred = ['*.png', '*.jpg']
for p in preferred[::-1]:
    if p in IMGFormats:
        IMGFormats.remove(p)
        IMGFormats.insert(0, p)


class ImageExporter(Exporter):
    Name = "Image File (PNG, TIF, JPG, ...)"
    allowCopy = True
    Formats = IMGFormats

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exporter = pyqtgraphImageExporter(self.scene)
        # Use a class boolean to control when auto-resizing should occur
        self.blockUpdates = False
        # Disconnect the default signals
        self.exporter.params.param('width').sigValueChanged.disconnect(self.exporter.widthChanged)
        self.exporter.params.param('height').sigValueChanged.disconnect(self.exporter.heightChanged)
        self.exporter.params.param('width').sigValueChanged.connect(self.widthChanged)
        self.exporter.params.param('height').sigValueChanged.connect(self.heightChanged)
        self.exporter.params.addChild({'name': 'showXAxis', 'type': 'bool', 'value': True})
        self.exporter.params.addChild({'name': 'showYAxis', 'type': 'bool', 'value': True})

        self.itemTree.currentItemChanged.connect(self.updateDefaultSize)
        self.plot.sigAfterResize.connect(self.updateDefaultSize)

        # Need to maintain aspect ratio for width/height

        self.initUI()

    def updateDefaultSize(self):
        sr = self.getTargetRect()
        if sr is None:
            return
        self.blockUpdates = True
        self.exporter.params.param('height').setDefault(int(sr.height()))
        self.exporter.params.param('width').setDefault(int(sr.width()))
        self.exporter.params.param('height').setToDefault()
        self.exporter.params.param('width').setToDefault()
        self.blockUpdates = False

    def widthChanged(self):
        if self.blockUpdates:
            return
        sr = self.getSourceRect()
        ar = float(sr.height()) / sr.width()
        self.blockUpdates = True
        self.exporter.params.param('height').setValue(int(self.exporter.params['width'] * ar))
        self.blockUpdates = False

    def heightChanged(self):
        if self.blockUpdates:
            return
        sr = self.getSourceRect()
        ar = float(sr.width()) / sr.height()
        self.blockUpdates = True
        self.exporter.params.param('width').setValue(int(self.exporter.params['height'] * ar))
        self.blockUpdates = False

    def initUI(self):
        vLayout = self.layout()
        vLayout.insertWidget(2, QLabel("Export options:"))
        self.paramTree = ParameterTree()

        self.paramTree.headerItem().setText(0, "1")
        self.paramTree.header().setVisible(False)
        self.paramTree.setParameters(self.exporter.params)
        vLayout.insertWidget(3, self.paramTree, 1)

    def export(self, filename=None, toBytes=False, copy=False):
        if not toBytes and not copy and filename is None:
            fname = self.fileSaveDialog(filter=self.Formats)
            if fname is not None:
                self.export(fname)
            return
        if not self.exporter.params['showXAxis']:
            self.plot.getPlotItem().hideAxis('bottom')
        if not self.exporter.params['showYAxis']:
            self.plot.getPlotItem().hideAxis('left')
        try:
            self.exporter.export(filename, toBytes, copy)
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("{0}".format(e))
            msg.setWindowTitle("Error")
            msg.exec_()
        finally:
            self.plot.getPlotItem().showAxis('bottom')
            self.plot.getPlotItem().showAxis('left')
