'''
Last Modified: 2021-05-07

@author: Jesse M. Barr

Contains:
    -QueueItem
    -QueuePanel

Changes:
-2021-05-07:
    -Cleaner list widget.
    -Fixed bug with list updating too quickly.
-2021-04-24:
    -Updated to work with acestatpy library.
-2020-05-21:
    -Added preset handling.
-2020-06-17:
    -Completely cancel running test.

ToDo:

'''
from PyQt5.QtCore import pyqtSignal as Signal, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QScrollArea, QGridLayout, QVBoxLayout,
    QHBoxLayout, QSizePolicy, QMenu, QGridLayout
)
from threading import Lock
# Local
from Widgets import CollapsibleBox, ElideLabel


class QueueItem(QWidget):
    sigCancel = Signal()

    def __init__(self, test):
        super().__init__()
        self.test = test
        self.initUI()

    def initUI(self):
        relTest = self.test.info
        qItem = CollapsibleBox("{0}".format(relTest.name))
        hLayout = qItem.header().layout()
        hLayout.addStretch()

        if self.test.run_forever:
            self.__count1 = QLabel(u"\N{INFINITY}")
        else:
            self.__count1 = QLabel("{0}".format(self.test.iterations))
        self.__count1.setStyleSheet("padding-right: 3px;")
        hLayout.addWidget(self.__count1)

        boxLayout = QVBoxLayout()
        boxLayout.setContentsMargins(15, 3, 3, 3)

        paramLayout = QGridLayout()
        paramLayout.setContentsMargins(0, 0, 0, 0)
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

        paramLayout.addWidget(QLabel("Start delay:"), paramLayout.rowCount(), 0)
        paramLayout.addWidget(QLabel("{0}s".format(
            self.test.start_delay)), paramLayout.rowCount()-1, 1)

        paramLayout.addWidget(QLabel("Remaining:"), paramLayout.rowCount(), 0)
        if self.test.run_forever:
            self.__count2 = QLabel(u"\N{INFINITY}")
        else:
            self.__count2 = QLabel("{0}".format(self.test.iterations))
        paramLayout.addWidget(self.__count2, paramLayout.rowCount()-1, 1)

        paramLayout.addWidget(QLabel("Iteration delay:"), paramLayout.rowCount(), 0)
        paramLayout.addWidget(QLabel("{0}s".format(
            self.test.inner_delay)), paramLayout.rowCount()-1, 1)

        paramLayout.addWidget(QLabel("Export:"), paramLayout.rowCount(), 0)
        lbl = QLabel()
        lbl.static = "{0}".format(self.test.export)
        lbl.installEventFilter(self)
        paramLayout.addWidget(lbl, paramLayout.rowCount()-1, 1)

        paramLayout.setColumnStretch(0, 0)
        paramLayout.setColumnStretch(1, 1)

        boxLayout.addLayout(paramLayout)

        hl = QHBoxLayout()
        btnRemove = QPushButton("Cancel")
        btnRemove.setStyleSheet("padding:2px 15px;")
        btnRemove.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btnRemove.clicked.connect(self.sigCancel.emit)
        hl.addWidget(btnRemove)
        boxLayout.addLayout(hl)
        qItem.setContentLayout(boxLayout)

        l = QVBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(qItem)
        self.setLayout(l)

    def updateCount(self):
        # Count only needs updated if not run_forever
        if not self.test.run_forever:
            self.__count1.setText("{0}".format(self.test.iterations))
            self.__count2.setText("{0}".format(self.test.iterations))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        cancel = menu.addAction("Cancel")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == cancel:
            self.sigCancel.emit()

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Resize):
            if hasattr(obj, "static"):
                ElideLabel(obj, obj.static)
        return super().eventFilter(obj, event)


class QueuePanel(QWidget):
    sigPause = Signal()
    sigCancel = Signal(int)

    def __init__(self, paused, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__lock = Lock()
        self.__queue = queue # Hold reference to queue
        self.initUI()
        self.setPause(paused)
        self.updateQueue()

    def initUI(self):
        ui = QWidget(self)
        ui.setObjectName("TestQueue")

        testScroll = QScrollArea()
        testScroll.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        testScroll.setWidget(ui)
        testScroll.setWidgetResizable(True)

        listLayout = QVBoxLayout()

        self.__list = QVBoxLayout()
        listLayout.addLayout(self.__list)
        listLayout.addStretch(1)
        ui.setLayout(listLayout)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        hLayout = QHBoxLayout()
        hLayout.setContentsMargins(0, 0, 0, 0)
        self.__pauseButton = QPushButton()
        self.__pauseButton.setStyleSheet("margin: 5px;")
        self.__pauseButton.clicked.connect(self.sigPause.emit)
        hLayout.addWidget(self.__pauseButton)
        mainLayout.addLayout(hLayout)
        mainLayout.addWidget(testScroll)
        self.setLayout(mainLayout)

    def updateQueue(self):
        with self.__lock:
            queue = self.__queue
            for i in reversed(range(self.__list.count())):
                w = self.__list.itemAt(i).widget()
                if not hasattr(w, "test"):
                    # deleteLater() has been called, but has not completed yet
                    continue
                elif w.test in queue:
                    # If the test is still in the queue, just update it
                    w.updateCount()
                else:
                    # print("Deleting:", i)
                    w.deleteLater()
            # Add new items.
            # Note:
            #   If we ever make it possible to rearrange tests, this will not work!
            for i in queue[self.__list.count():]:
                item = QueueItem(i)
                item.sigCancel.connect(self.cancelTest)
                self.__list.insertWidget(self.__list.count(), item)

    def cancelTest(self):
        self.sigCancel.emit(self.__list.indexOf(self.sender()))

    def setPause(self, pause):
        self.__pauseButton.setText("Resume Queue" if pause else "Pause Queue")

    def onCancelItem(self, fn):
        if not callable(fn):
            return
        self.sigCancel.connect(fn)

    def onPause(self, fn):
        if not callable(fn):
            return
        self.sigPause.connect(fn)
