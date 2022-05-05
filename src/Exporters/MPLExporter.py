'''
Last Modified: 2020-04-10

@author: Jesse M. Barr

Contains:
    -MatplotWindow
    -MPLExporter

Description:

ToDo:

'''
# PyQt5
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMainWindow
# PyQtGraph
from pyqtgraph.graphicsItems.PlotItem import PlotItem
# Matplotlib
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
# Local
from .Exporter import Exporter


class MatplotWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        # Initializing with a parent parameter causes the window to be tied to
        #   the parent. No icon on the taskbar, and minimizes to a small frame
        #   at the bottom of the screen.
        super().__init__()
        self.bgUpdate = False  # background update
        self.initUI()

    def initUI(self):
        ui = QWidget()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        toolbar = NavigationToolbar(self.canvas, ui)

        vLayout = QVBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)
        vLayout.addWidget(toolbar)
        vLayout.addWidget(self.canvas)
        ui.setLayout(vLayout)
        self.setCentralWidget(ui)

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, value):
        if not isinstance(value, PlotItem):
            raise Exception("Item must be PlotItem")
        self._item = value
        # Whenever self.item is set, update the plot
        self.updatePlot()

    def updatePlot(self):
        self.clear()
        item = self.item
        axes = self.fig.add_subplot(111)
        # get labels from the plot
        title = item.titleLabel.text
        self.setWindowTitle(title)
        axes.set_title(title)

        xlabel = item.axes['bottom']['item'].label.toPlainText()
        axes.set_xlabel(xlabel)

        ylabel = item.axes['left']['item'].label.toPlainText()
        axes.set_ylabel(ylabel)

        # Let matplotlib handle plot colors
        for i in item.curves:
            x, y = i.getData()
            axes.plot(x, y)

        if self.isVisible() and not self.isMinimized():
            # Do not re-draw the plot if it isn't visible.
            self.canvas.draw()
        else:
            self.bgUpdate = True

    def clear(self, redraw=False):
        self.fig.clear()
        if redraw:
            self.canvas.draw()

    def showEvent(self, event):
        if self.bgUpdate:
            self.canvas.draw()
            self.bgUpdate = False
        super().showEvent(event)


class MPLExporter(Exporter):
    Name = "Matplotlib Window"
    TypeRestrictions = (PlotItem)

    def __init__(self, plot, *args, **kwargs):
        super().__init__(plot)
        self.exporter = MatplotWindow()
        self.initUI()

    def initUI(self):
        vLayout = self.layout()
        vLayout.setStretch(1, 1)

    def export(self):
        self.exporter.show()
        self.exporter.setWindowState(self.exporter.windowState() & ~Qt.WindowMinimized)
        self.exporter.raise_()
        self.exporter.activateWindow()
