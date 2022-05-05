'''
Last Modified: 2020-04-10

@author: Jesse M. Barr

Contains:
    -Exporter

Description:

ToDo:

'''
# PyQt5
from PyQt5.QtCore import Qt
# from PyQt5.QtGui import 
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QFileDialog, QLabel,
                             QTreeWidget, QPushButton, QAbstractScrollArea,
                             QWidget, QTreeWidgetItem, QGraphicsRectItem)
# PyQtGraph
from pyqtgraph import PlotWidget, functions as fn
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.graphicsItems.PlotItem import PlotItem
from pyqtgraph.GraphicsScene import GraphicsScene


class Exporter(QWidget):
    allowCopy = False
    TypeRestrictions = (GraphicsScene, PlotItem, ViewBox)
    exporter = None

    def __init__(self, plot, *args, **kwargs):
        if not isinstance(plot, PlotWidget):
            raise Exception("Expected PlotWidget")
        super().__init__(*args, **kwargs)
        self.plot = plot
        self.scene = plot.scene()

        self.selectBox = QGraphicsRectItem()
        self.selectBox.setPen(fn.mkPen('y', width=3, style=Qt.DashLine))
        self.selectBox.hide()
        self.scene.addItem(self.selectBox)

        Exporter.initUI(self)

    def initUI(self):
        vLayout = QVBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)

        vLayout.addWidget(QLabel("Item to export:"))

        self.itemTree = QTreeWidget()
        self.itemTree.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.itemTree.headerItem().setText(0, "1")
        self.itemTree.header().setVisible(False)
        vLayout.addWidget(self.itemTree)

        self.updateItemList()

        btnLayout = QHBoxLayout()
        if self.allowCopy:
            self.copyBtn = QPushButton("Copy")
            self.copyBtn.clicked.connect(self.copyClicked)
            btnLayout.addWidget(self.copyBtn, 1)
        else:
            btnLayout.addStretch(1)
        self.exportBtn = QPushButton("Export")
        self.exportBtn.clicked.connect(self.exportClicked)
        btnLayout.addWidget(self.exportBtn, 1)
        vLayout.addLayout(btnLayout)

        self.setLayout(vLayout)

        self.itemTree.currentItemChanged.connect(self.exportItemChanged)

        def plotResized(ev):
            self.updateSelectBox()

        self.plot.sigAfterResize.connect(plotResized)

        def updatedPlot():
            item = self.itemTree.currentItem()
            if item is None:
                self.updateItemList()
                self.itemTree.setCurrentItem(self.itemTree.topLevelItem(0))
            else:
                self.updateItemList(item.gitem)

        self.plot.sigPlotChanged.connect(updatedPlot)

    def exportItemChanged(self, item):
        if item is None:
            return
        if self.exporter is not None:
            self.exporter.item = item.gitem
        self.updateSelectBox(item)
        if self.isVisible():
            self.selectBox.show()

    def updateSelectBox(self, item=None):
        if item is None and self.itemTree.currentItem() is None:
            return
        else:
            item = self.itemTree.currentItem()
        if item.gitem is self.scene:
            gview = self.scene.getViewWidget()
            newBounds = gview.mapToScene(gview.viewport().geometry()).boundingRect()
        else:
            newBounds = item.gitem.sceneBoundingRect()
        self.selectBox.setRect(newBounds)

    def updateItemList(self, select=None):
        self.itemTree.clear()
        si = None
        if isinstance(self.scene, self.TypeRestrictions):
            # Use whole scene
            si = QTreeWidgetItem(["Entire Scene"])
            si.gitem = self.scene
            self.itemTree.addTopLevelItem(si)
            si.setExpanded(True)

        for child in self.scene.items():
            if child.parentItem() is None:
                self.updateItemTree(child, si, select=select)

    def updateItemTree(self, item, treeItem=None, select=None):
        si = None
        if isinstance(item, ViewBox):
            si = QTreeWidgetItem(['ViewBox'])
        elif isinstance(item, PlotItem):
            if item.titleLabel.text:
                title = item.titleLabel.text
            else:
                title = "Plot"
            si = QTreeWidgetItem([title])

        if isinstance(item, self.TypeRestrictions):
            si.gitem = item
            if treeItem is None:
                self.itemTree.addTopLevelItem(si)
            else:
                treeItem.addChild(si)
            treeItem = si
            if si.gitem is select:
                self.itemTree.setCurrentItem(si)

        for ch in item.childItems():
            self.updateItemTree(ch, treeItem, select=select)

    def showEvent(self, event):
        self.updateSelectBox()
        self.selectBox.show()
        super().showEvent(event)

    def hideEvent(self, event):
        try:
            self.selectBox.setVisible(False)
            super().hideEvent(event)
        except:
            pass

    def getScene(self):
        return self.scene

    def fileSaveDialog(self, filter=None):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        if filter is not None:
            if isinstance(filter, str):
                dialog.setNameFilter(filter)
            elif isinstance(filter, list):
                dialog.setNameFilters(filter)
        if dialog.exec_():
            fpath = dialog.selectedFiles()[0]
            ext = dialog.selectedNameFilter().split('.')[-1].lower()
            f_ext = fpath.split('.')[-1].lower()
            if ext and ext != f_ext:
                fpath = "{0}.{1}".format(fpath, ext)
            return fpath

    def getSourceRect(self):
        item = self.itemTree.currentItem()
        if item is None:
            return
        if isinstance(item.gitem, GraphicsScene):
            w = item.gitem.getViewWidget()
            return w.viewportTransform().inverted()[0].mapRect(w.rect())
        else:
            return item.gitem.sceneBoundingRect()

    def getTargetRect(self):
        item = self.itemTree.currentItem()
        if item is None:
            return
        if isinstance(item.gitem, GraphicsScene):
            return item.gitem.getViewWidget().rect()
        else:
            return item.gitem.mapRectToDevice(item.gitem.boundingRect())

    def exportClicked(self):
        self.selectBox.hide()
        self.export()
        self.selectBox.show()

    def copyClicked(self):
        self.selectBox.hide()
        self.export(copy=True)
        self.selectBox.show()
