'''
Last Modified: 2021-08-19

@author: Jesse M. Barr

Contains:
    -ResultItem
    -ResultPanel

Changes:

ToDo:

'''
from PyQt5.QtCore import pyqtSignal as Signal, QEvent, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QScrollArea, QGridLayout, QVBoxLayout,
    QHBoxLayout, QSizePolicy, QGridLayout, QMenu, QFileDialog
)
from datetime import datetime
# Local
from Widgets import CollapsibleBox, ElideLabel


class ResultItem(QWidget):
    sigPlot = Signal(str, object)
    sigTable = Signal(str, object)

    def __init__(self, test):
        super().__init__()
        self.test = test
        self.initUI()

    def initUI(self):
        relTest = self.test.info
        name = "{0} {1}".format(datetime.fromtimestamp(
            self.test.startTime).strftime('%Y%m%d-%H%M%S'), self.test.info.name)
        rItem = CollapsibleBox("{0}".format(name))
        hLayout = rItem.header().layout()
        hLayout.addStretch()

        boxLayout = QVBoxLayout()
        boxLayout.setContentsMargins(15, 0, 3, 3)

        params = CollapsibleBox("Parameters")

        paramLayout = QGridLayout()
        paramLayout.setContentsMargins(15, 3, 3, 3)
        for p in self.test.parameters:
            paramInfo = relTest.parameters[p]
            paramLayout.addWidget(QLabel("{0}:".format(
                paramInfo.name)), paramLayout.rowCount(), 0)

            if hasattr(paramInfo, "options"):
                value = paramInfo.options[self.test.parameters[p]]
            else:
                value = self.test.parameters[p]
            if hasattr(paramInfo, "units"):
                value = "{0}{1}".format(value, paramInfo.units)
            else:
                value = "{0}".format(value)
            paramLayout.addWidget(QLabel("{0}".format(value)), paramLayout.rowCount()-1, 1)

        paramLayout.setColumnStretch(0, 0)
        paramLayout.setColumnStretch(1, 1)
        params.setContentLayout(paramLayout)
        boxLayout.addWidget(params)

        results = CollapsibleBox("Results")
        resultLayout = QGridLayout()
        resultLayout.setContentsMargins(15, 3, 3, 3)

        def createSignalTable(id):
            def signalTable():
                self.sigTable.emit(id, self.test)
            return signalTable

        for p in relTest.outputs:
            rInfo = relTest.outputs[p]

            if rInfo.type in ["field", "list"]:
                for f in rInfo.fields:
                    resultLayout.addWidget(QLabel(f"{p}.{f.label}:"), resultLayout.rowCount(), 0)
                    resultLayout.addWidget(
                        QLabel(f"{self.test.results[p][f.label]}{getattr(f, 'units', '')}"), resultLayout.rowCount()-1, 1)
            elif rInfo.type == "matrix":
                resultLayout.addWidget(QLabel(f"{p}:"), resultLayout.rowCount(), 0)
                btnTable = QPushButton("View")
                btnTable.clicked.connect(createSignalTable(p))
                resultLayout.addWidget(btnTable, resultLayout.rowCount()-1, 1)
            else:
                pass

        resultLayout.setColumnStretch(0, 0)
        resultLayout.setColumnStretch(1, 1)
        results.setContentLayout(resultLayout)
        boxLayout.addWidget(results)

        plots = CollapsibleBox("Plots")
        plotLayout = QGridLayout()
        plotLayout.setContentsMargins(15, 3, 3, 3)

        def createSignalPlot(id):
            def signalPlot():
                self.sigPlot.emit(id, self.test)
            return signalPlot

        for p in relTest.plots:
            pInfo = relTest.plots[p]

            plotLayout.addWidget(QLabel(f"{p}:"), plotLayout.rowCount(), 0)
            btnPlot = QPushButton("Plot")
            btnPlot.clicked.connect(createSignalPlot(p))
            plotLayout.addWidget(btnPlot, plotLayout.rowCount()-1, 1)

        plotLayout.setColumnStretch(0, 0)
        plotLayout.setColumnStretch(1, 1)
        plots.setContentLayout(plotLayout)
        boxLayout.addWidget(plots)

        rItem.setContentLayout(boxLayout)

        l = QVBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(rItem)
        self.setLayout(l)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        saveResults = menu.addAction("Save Results")
        savePreset = menu.addAction("Save as Preset")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == saveResults:
            path = QFileDialog.getExistingDirectory(
                self, "Choose Directory")
            if path:
                self.test.export(path)
        elif action == savePreset:
            path = QFileDialog.getSaveFileName(
                self, "Save Preset", filter="JSON (*.json)")
            if path[0]:
                self.test.parameters.export(path[0])

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Resize):
            if hasattr(obj, "static"):
                ElideLabel(obj, obj.static)
        return super().eventFilter(obj, event)


class ResultPanel(QWidget):
    sigPlot = Signal(str, object)
    sigTable = Signal(str, object)

    def __init__(self, *args, **kwargs):
        self.__limit = kwargs.pop("limit", 5)
        self.__direction = kwargs.pop("direction", 0)
        super().__init__(*args, **kwargs)
        self.__tests = []
        self.initUI()

    def initUI(self):
        ui = QWidget(self)
        ui.setObjectName("ResultPanel")
        # self.ui.setStyleSheet("background-color: #0000FF")

        testScroll = QScrollArea()
        testScroll.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        testScroll.setWidget(ui)
        testScroll.setWidgetResizable(True)

        listLayout = QVBoxLayout()

        self.__list = QVBoxLayout()
        self.applySort(self.__direction)
        listLayout.addLayout(self.__list)
        listLayout.addStretch(1)
        ui.setLayout(listLayout)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        hLayout = QHBoxLayout()
        hLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addLayout(hLayout)
        mainLayout.addWidget(testScroll)
        self.setLayout(mainLayout)

    def setLimit(self, limit=None):
        if limit is None:
            pass
        elif limit < 1:
            raise Exception("Result limit must be 1 or more.")
        else:
            self.__limit = limit
        while len(self.__tests) > self.__limit:
            self.__tests[0].deleteLater()
            del self.__tests[0]

    def applySort(self, direction):
        # For now, anything other than 0 reverses order
        if direction >= 0:
            self.__list.setDirection(self.__list.BottomToTop)
        else:
            self.__list.setDirection(self.__list.TopToBottom)

    def append(self, test):
        item = ResultItem(test)
        item.sigPlot.connect(self.sigPlot.emit)
        item.sigTable.connect(self.sigTable.emit)
        self.__tests.append(item)
        self.setLimit()
        self.__list.insertWidget(0, item)

    def clear(self):
        for i in self.__tests:
            i.deleteLater()
        self.__tests.clear()
