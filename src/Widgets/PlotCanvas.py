'''
Last Modified: 2021-05-03

@author: Jesse M. Barr

Contains:
    -PlotHistory
    -PlotToolbar
    -PlotWidget
    -PlotCanvas

ToDo:
    -Potentially customize the context menu.
        -It can unfortunately override some settings and cause things to not
        work properly.
        -The built-in export tool causes a memory leak.
        -It is disabled entirely for now.
    -Add plot customizations to the toolbar.
        -Include color settings for the plot.
        -Include tools from the context menu.

'''
# PyQt5
from PyQt5.QtCore import Qt, pyqtSignal, QRectF, QEvent
from PyQt5.QtWidgets import (QWidget, QLabel, QSizePolicy, QVBoxLayout, QMenu,
                             QToolBar, QToolButton)
from PyQt5.QtGui import QColor
# PyQtGraph
from pyqtgraph import PlotWidget as PW  # , SignalProxy
from pyqtgraph.graphicsItems.ViewBox import ViewBox
# Local
from Exporters import ExportDialog
from .Images import Icon


class PlotHistory(object):
    previous = None
    next = None
    plotRange = None

    def __init__(self, plotRange):
        self.plotRange = plotRange

    def addItem(self, item):
        item.previous = self
        self.next = item
        return self.next

    def __eq__(self, plotRange):
        c1 = self.plotRange
        if isinstance(plotRange, PlotHistory):
            c2 = plotRange.plotRange
        elif isinstance(plotRange, QRectF):
            c2 = plotRange
        return c1.left() == c2.left() and c1.right() == c2.right() and \
            c1.top() == c2.top() and c1.bottom() == c2.bottom()

    def range(self):
        return self.plotRange


class PlotToolbar(QToolBar):
    def __init__(self, plot, *args, **kwargs):
        if not isinstance(plot, PW):
            raise Exception("Expected PlotWidget")
        super().__init__(*args, **kwargs)
        self.setObjectName("PlotToolbar")
        self.plot = plot
        self.plotHistory = None
        # Qt objects are not deleted on close, therefore, we will re-use them.
        self.exporter = ExportDialog(self.plot)

        self.initUI()

    def initUI(self):
        # Reversed because of dark theme
        # background_color = self.palette().color(self.backgroundRole())
        # foreground_color = self.palette().color(self.foregroundRole())
        # print(foreground_color, background_color)
        # icon_color = (foreground_color
        #               if background_color.value() < 128 else None)
        icon_color = QColor("white")
        disabled_color = QColor("gray")

        def resetView():
            self.plot.plotItem.vb.setRange(self.homeView, padding=0.0)
            self.addHistory()

        btnHome = self.addAction(Icon("light:home.png", icon_color,
                                      disabled_color), 'Reset', resetView)

        def rangeChanged():
            if self.plot.mouseHeld:
                return
            self.addHistory()

        self.plot.plotItem.vb.sigRangeChangedManually.connect(rangeChanged)

        def plotChange():
            self.plotHistory = None
            self.plot.plotItem.vb.autoRange()
            self.homeView = self.plot.plotItem.vb.viewRect()
            self.btnUndo.setEnabled(False)
            self.btnRedo.setEnabled(False)
            resetView()

        self.plot.sigPlotChanged.connect(plotChange)

        def undo():
            self.plotHistory = self.plotHistory.previous
            self.plot.plotItem.vb.setRange(self.plotHistory.range(), padding=0.0)
            self.btnRedo.setEnabled(True)
            if self.plotHistory.previous is None:
                self.btnUndo.setEnabled(False)

        self.btnUndo = self.addAction(
            Icon("light:prev.png", icon_color, disabled_color), "Undo", undo)

        def redo():
            self.plotHistory = self.plotHistory.next
            self.plot.plotItem.vb.setRange(self.plotHistory.range(), padding=0.0)
            self.btnUndo.setEnabled(True)
            if self.plotHistory.next is None:
                self.btnRedo.setEnabled(False)

        self.btnRedo = self.addAction(
            Icon("light:next.png", icon_color, disabled_color), "Redo", redo)

        self.addSeparator()

        def togglePan():
            if btnPan.isChecked():
                btnZoom.setChecked(False)
                self.plot.setPanEnabled(True)
            else:
                self.plot.setPanEnabled(False)
            setLabel()

        btnPan = self.addAction(Icon("light:move.png", icon_color,
                                     disabled_color), "Pan", togglePan)
        btnPan.setCheckable(True)

        def toggleZoom():
            if btnZoom.isChecked():
                btnPan.setChecked(False)
                self.plot.setZoomEnabled(True)
            else:
                self.plot.setZoomEnabled(False)
            setLabel()

        btnZoom = self.addAction(Icon("light:zoom_to_rect.png", icon_color,
                                      disabled_color), "Zoom", toggleZoom)
        btnZoom.setCheckable(True)

        self.addSeparator()

        saveButton = QToolButton(self)
        saveButton.setText("Export")
        saveButton.setToolTip("Export")
        saveButton.setIcon(Icon("light:filesave.png", icon_color, disabled_color))
        saveButton.setPopupMode(QToolButton.InstantPopup)
        saveMenu = QMenu(saveButton)
        for e in self.exporter.ExporterClasses:
            saveMenu.addAction(e.Name,
                               lambda item=e.Name: self.exporter.setTool(item))
        saveButton.setMenu(saveMenu)
        self.addWidget(saveButton)

        lblInfo = QLabel("", self)
        lblInfo.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lblInfo.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,
                                          QSizePolicy.Ignored))
        labelAction = self.addWidget(lblInfo)

        def setLabel(s=""):
            if self.plot.mode and s:
                lblInfo.setText("{0}, {1}".format(self.plot.mode, s))
            elif self.plot.mode:
                lblInfo.setText("{0}".format(self.plot.mode))
            else:
                lblInfo.setText("{0}".format(s))

        def mouseMoved(ev):
            if self.plot.mouseHeld and btnPan.isChecked():
                return
            coords = self.plot.plotItem.vb.mapSceneToView(ev)
            coords = "x={0:<12g} y={1:<12g}".format(coords.x(), coords.y())
            setLabel(coords)

        # proxy = SignalProxy(self.plot.scene().sigMouseMoved, rateLimit=60, slot=mouseMoved)
        self.plot.scene().sigMouseMoved.connect(mouseMoved)

        def mouseLeft(ev):
            setLabel()

        self.plot.sigMouseLeave.connect(mouseLeft)

    def addHistory(self):
        currRange = self.plot.plotItem.vb.viewRect()
        if self.plotHistory is None:
            self.plotHistory = PlotHistory(currRange)
        elif currRange != self.plotHistory:
            self.plotHistory = self.plotHistory.addItem(PlotHistory(currRange))
            self.btnRedo.setEnabled(False)
            self.btnUndo.setEnabled(True)


class PlotWidget(PW):
    # Custom PlotWidget for custom event handling
    # # Might be able to use an event filter in PlotToolbar
    sigMousePressed = pyqtSignal(object)
    sigPlotChanged = pyqtSignal()
    sigMouseEnter = pyqtSignal(object)
    sigMouseLeave = pyqtSignal(object)
    sigAfterResize = pyqtSignal(object)
    mouseHeld = None
    myPlot = None
    mode = None

    def __init__(self, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)
        self.scene().installEventFilter(self)
        self.mouseHeld = False

    def mouseReleaseEvent(self, ev):
        self.mouseHeld = False
        self.sigMouseReleased.emit(ev)
        super(PlotWidget, self).mouseReleaseEvent(ev)

    def mousePressEvent(self, ev):
        self.mouseHeld = True
        self.sigMousePressed.emit(ev)
        super(PlotWidget, self).mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        super(PlotWidget, self).mouseMoveEvent(ev)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.sigAfterResize.emit(ev)

    def setPanEnabled(self, enabled=True):
        if enabled:
            self.plotItem.setMouseEnabled(True, True)
            self.plotItem.vb.setMouseMode(ViewBox.PanMode)
            self.mode = "pan/zoom"
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.plotItem.setMouseEnabled(False, False)
            self.plotItem.vb.setMouseMode(ViewBox.PanMode)
            self.mode = None
            self.unsetCursor()

    def setZoomEnabled(self, enabled=True):
        if enabled:
            self.mode = "zoom rect"
            self.plotItem.setMouseEnabled(True, True)
            self.plotItem.vb.setMouseMode(ViewBox.RectMode)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.plotItem.setMouseEnabled(False, False)
            self.plotItem.vb.setMouseMode(ViewBox.PanMode)
            self.mode = None
            self.unsetCursor()

    def eventFilter(self, src, ev):
        # https://doc.qt.io/qt-5/qevent.html
        if ev.type() == QEvent.Enter:
            self.sigMouseEnter.emit(ev)
        elif ev.type() == QEvent.Leave:
            self.sigMouseLeave.emit(ev)
        # Can capture much more here, especially if more EventFilters are added
        return super(PlotWidget, self).eventFilter(src, ev)

    def clear(self):
        self.plotItem.clear()
        self.sigPlotChanged.emit()

    def plot(self, *args, **kwargs):
        self.plotItem.plot(*args, **kwargs)
        # if self.myPlot is None:
        #     self.myPlot = self.plotItem.plot(*args, **kwargs)
        # else:
        #     self.myPlot.setData(*args, **kwargs)
        self.sigPlotChanged.emit()

    def setLabel(self, axis=None, label=None, units=None):
        if axis == 'x':
            self.plotItem.setLabel('bottom', label, units)
        elif axis == 'y':
            self.plotItem.setLabel('left', label, units)


class PlotCanvas(QWidget):
    # Container to hold the plot and toolbar
    def __init__(self, *args, **kwargs):
        super(PlotCanvas, self).__init__(*args, **kwargs)
        self.initUI()

    def initUI(self):
        self.__plot = PlotWidget()
        self.setLabel = self.__plot.setLabel
        # Built-in exportDialog causes a memory leak
        # self.__plot.scene().exportDialog = ExportDialog(self.__plot)
        self.__plot.plotItem.vb.setMenuEnabled(False)  # disable entire context menu
        # self.__plot.plotItem.vb.menu.clear()  # disable context menu above 'Plot Options'
        # self.__plot.plotItem.ctrlMenu = None  # disable context menu 'Plot Options'
        # self.__plot.scene().contextMenu = None  # disable context menu 'Export'
        self.__plot.plotItem.hideButtons()
        self.__plot.plotItem.setMouseEnabled(False, False)
        # self.__plot.plotItem.setMenuEnabled(True)
        vLayout = QVBoxLayout()
        vLayout.setContentsMargins(0, 0, 0, 0)

        vLayout.addWidget(PlotToolbar(self.__plot))
        vLayout.addWidget(self.__plot)
        self.setLayout(vLayout)

    def plot(self, *args, **kwargs):
        self.__plot.plot(*args, **kwargs)

    # @property
    # def plot(self):
    #     return self.__plot

    def clear(self):
        self.__plot.clear()

    def removePlot(self, plt):
        self.__plot.removeItem(plt)

    def closeEvent(self, event):
        super(PlotCanvas, self).closeEvent(event)
