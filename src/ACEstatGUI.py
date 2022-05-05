'''
Last Modified: 2021-08-20

@author: Jesse M. Barr

Contains:
    -ACEstatGUI

Changes:
    -2021-08-20:
        -Added table to display matrix results.
    -2021-04-28:
        -Change widgets in response to acestatpy events rather than assuming.
        -Added countdown timer.

ToDo:

'''
# PyQt
from PyQt5.QtCore import Qt, QDir, QFile, QTextStream, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QSplitter, QTabWidget, QPushButton, QLineEdit,
                             QGroupBox, QComboBox, QLabel, QPlainTextEdit,
                             QMessageBox, QStyleFactory, QFileDialog)
# Installed
from acestatpy import ACEstatPy
# Local
from Settings import LoadConfig, SettingsDialog
from Utilities import SignalTranslator, resource_path
from Widgets import (FuncComboBox, PlotCanvas, QueuePanel, ResultPanel,
                     ResultTable, TestForm)

QDir.addSearchPath('icons', resource_path("icons"))
QDir.addSearchPath('styles', resource_path("styles"))
QDir.addSearchPath('dark', resource_path("icons", "dark"))
QDir.addSearchPath('light', resource_path("icons", "light"))

# Temporary, for testing only
# import random

# Global Variables
DEFAULT_BAUD = 9600
CONFIGFILE = 'config.ini'
CONFIG = LoadConfig(CONFIGFILE)


class ACEstatGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = "ACEstatGUI"
        self.acestat = ACEstatPy()
        xScale = self.logicalDpiX() / 96.0
        yScale = self.logicalDpiY() / 96.0

        # Setting this closes all child windows when this window is closed.
        self.setAttribute(Qt.WA_DeleteOnClose)
        # self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        self.setStyle(QStyleFactory.create("Fusion"))
        # self.setStyleSheet(pkg_resources.resource_string("resources", 'styles/ElegantDark.qss').decode("utf-8") )
        styles = QFile("styles:ElegantDark.qss")
        if styles.open(styles.ReadOnly | styles.Text):
            self.setStyleSheet(QTextStream(styles).readAll())
        styles.close()
        self.initUI()

        self.setWindowIcon(QIcon("icons:usace_logo.ico"))
        self.setWindowTitle(self.title)
        # self.adjustSize()
        self.resize(int(875 * xScale), int(550 * yScale))

    def messageDialog(self, message, title, icon=None, detailed=None, informative=None):
        msg = QMessageBox()
        msg.setText(message)
        if icon:
            msg.setIcon(icon)
        if informative:
            msg.setInformativeText(informative)
        msg.setWindowTitle(title)
        if detailed:
            msg.setDetailedText(detailed)
        msg.exec_()

    def closeEvent(self, event):
        try:
            with open(CONFIGFILE, 'w') as configfile:
                CONFIG.write(configfile)
        except:
            pass
        event.accept()

    def initUI(self):
        #######################
        ### LOCAL FUNCTIONS ###
        #######################
        def updateCountdown():
            rem = self.acestat.currentTest.estimateRemaining()
            if rem is None:
                testStatus.setText("Running {0}...".format(self.acestat.currentTest.id))
                return
            else:
                testStatus.setText("Running {0}: ~{1}s".format(
                    self.acestat.currentTest.id, round(rem)))
            if rem == 0:
                _timer.stop()

        def updatePreference(section, option, value):
            if section == "console":
                if option == "show_console":
                    CONFIG.set(section, option, str(value).lower())
                    value = CONFIG.getboolean(section, option)
                    mToggleConsole.setChecked(value)
                    right_bottom.setVisible(value)
                    if not value:
                        handleConsoleClear()
                elif option == "console_lines":
                    CONFIG.set(section, option, str(value))
                    value = CONFIG.getint(section, option)
                    consoleTE.setMaximumBlockCount(value)
            elif section == "results":
                if option == "result_sort":
                    CONFIG.set(section, option, str(value))
                    value = CONFIG.getint(section, option)
                    resultList.applySort(value)
                elif option == "result_limit":
                    CONFIG.set(section, option, str(value))
                    value = CONFIG.getint(section, option)
                    resultList.setLimit(value)

        def handleFileAction(action):
            if action == mLoadTests:
                fpath = QFileDialog.getOpenFileName(
                    self, "Import Test Definitions", filter="XML (*.xml)")
                if fpath[0]:
                    try:
                        self.acestat.Definitions.importTests(fpath[0])
                        testForm.initUI()
                        self.acestat.clearQueue()
                        testQueue.updateQueue()
                        resultList.clear()
                    except:
                        self.messageDialog(
                            "Error encountered when importing: {0}.".format(fpath[0]),
                            "Import Error",
                            QMessageBox.Warning)
            elif action == mExportTests:
                fpath = QFileDialog.getSaveFileName(
                    self, "Export Default Test Definitions", filter="XML (*.xml)")
                if fpath[0]:
                    self.acestat.Definitions.copyDefaultTests(fpath[0])
            elif action == mPreferences:
                dlg = SettingsDialog(self, config=CONFIG)
                if dlg.exec_():
                    for i in dlg.Changes.items():
                        updatePreference(*i[0], i[1])
            elif action == mQuit:
                self.close()

        def handleToolAction(action):
            if action == mReset:
                self.acestat.sendCancel()
            elif action == mSavePreset:
                fpath = QFileDialog.getSaveFileName(
                    self, "Save Preset", filter="JSON (*.json)")
                if fpath[0]:
                    params = testForm.CurrentParameters
                    self.acestat.Definitions.saveCustomPreset(
                        params[0], params[1], fpath[0])
            elif action == mLoadPreset:
                fpaths = QFileDialog.getOpenFileNames(
                    self, "Import Custom Presets", filter="JSON (*.json)")
                for p in fpaths[0]:
                    try:
                        self.acestat.Definitions.loadCustomPreset(p)
                    except Exception as e:
                        self.messageDialog(
                            "Error encountered when importing: {0}.".format(p),
                            "Import Error",
                            QMessageBox.Warning,
                            "{0}".format(e))

        def handleViewAction(action):
            if action == mToggleConsole:
                updatePreference("console", "show_console", action.isChecked())

        def validateConnection():
            if portCB.currentText() and baudCB.currentText() \
                and (not serialComms.isOpen() or portCB.currentText() != serialComms.port
                     or baudCB.currentText() != str(serialComms.baud)):
                btnConnect.setEnabled(True)
            else:
                btnConnect.setEnabled(False)

        def Connect():
            self.acestat.disconnect()
            try:
                self.acestat.connect(portCB.currentText(), int(baudCB.currentText()))
            except Exception as e:
                self.messageDialog(
                    "Connection to {0} was unsuccessful.".format(portCB.currentText()),
                    "Connection Error",
                    QMessageBox.Warning,
                    "{0}".format(e))

        def addToQueue(*args, **kwargs):
            self.acestat.addToQueue(*args, **kwargs)
            testQueue.updateQueue()

        def handlePause():
            self.acestat.togglePause()
            testQueue.setPause(self.acestat.paused)

        def handleCancel(idx):
            self.acestat.removeFromQueue(idx, force=True)
            testQueue.updateQueue()

        def plotResult(id, test):
            pltLayout.removeWidget(self.rDisplay)
            self.rDisplay.close()
            self.rDisplay = PlotCanvas(self)
            pltLayout.addWidget(self.rDisplay)
            pltLayout.update()
            # self.rDisplay.clear()
            labels = {}
            axes = {}
            info = test.info.plots[id]

            title = info.title
            self.rDisplay.setLabel("x", label=info.x_label)
            self.rDisplay.setLabel("y", label=info.y_label)

            for s in info.series:
                self.rDisplay.plot({
                    "x": test.results[s.x.output][s.x.field],
                    "y": test.results[s.y.output][s.y.field],
                })
            self.rDisplay.setEnabled(True)

        def showTable(id, test):
            # print(id)
            pltLayout.removeWidget(self.rDisplay)
            self.rDisplay.close()

            info = test.info.outputs[id]
            # print([f.label for f in info.fields])

            self.rDisplay = ResultTable([
                f"{f.label}{f' ({f.units})' if hasattr(f, 'units') else ''}"
                for f in info.fields], list(zip(*reversed([
                    test.results[id][f.label] for f in info.fields
                ]))), self)
            pltLayout.addWidget(self.rDisplay)
            pltLayout.update()
            self.rDisplay.setEnabled(True)

        def handleSend():
            if inputLE.text():
                try:
                    serialComms.send(inputLE.text())
                    inputLE.clear()
                except Exception as e:
                    self.messageDialog(
                        "Message to {0} was unsuccessful.".format(portCB.currentText()),
                        "Error Sending Message",
                        QMessageBox.Warning,
                        "{0}".format(e))

        def handleConsoleClear():
            # Draw new plot, used for testing
            # self.rDisplay.plot([random.uniform(-1, 1) for i in range(10)])
            consoleTE.clear()

        def onError(err):
            # On error signal
            testStatus.setText("{0}".format(err))
            self.messageDialog(
                "Error Encountered",
                "Error Encountered",
                QMessageBox.Warning,
                "{0}".format(err))

        def onResult(id):
            # On result signal
            print(id)

        def onReady(ready):
            # On ready signal
            if ready:
                _timer.stop()
                testStatus.setText("Ready")
            testQueue.updateQueue()

        def onStart(test, *args, **kwargs):
            # On test start signal
            updateCountdown()
            _timer.start(1000)

        def onEnd(test, *args, **kwargs):
            # On test end signal
            _timer.stop()
            resultList.append(test)

        def sendingData(msg):
            # On serial sending signal
            if right_bottom.isVisible():
                consoleTE.ensureCursorVisible()
                consoleTE.insertPlainText("{0}\n".format(msg))

        def receiveData(msg):
            # On serial received signal
            if right_bottom.isVisible():
                consoleTE.insertPlainText(msg)
                consoleTE.ensureCursorVisible()
            if self.acestat.running:
                testStatus.setText("Receiving data...")

        def onConnected():
            # On serial connected signal
            testStatus.setText("Waiting for board response...")
            btnConnect.setEnabled(False)
            connectionStatus.setText(
                'Port: {0} Baud: {1}'.format(serialComms.port, serialComms.baud))
            # inputBtn.setEnabled(True)
            # inputLE.setEnabled(True)
            disconnectBtn.setEnabled(True)

        def onDisconnect(err=None):
            # On serial disconnected signal
            _timer.stop()
            # inputBtn.setEnabled(False)
            # inputLE.setEnabled(False)
            disconnectBtn.setEnabled(False)
            connectionStatus.setText("Disconnected")
            testStatus.setText("")
            portCB.clear()
            if err:
                self.messageDialog(
                    "Connection lost!",
                    "Connection Error",
                    QMessageBox.Critical,
                    "{0}".format(err))
            portCB.refreshItems()
            validateConnection()

        #################
        ### INTERFACE ###
        #################
        _timer = QTimer(self)
        _timer.timeout.connect(updateCountdown)

        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        mLoadTests = fileMenu.addAction("Import Tests")
        mExportTests = fileMenu.addAction("Export Default Tests")
        fileMenu.addSeparator()
        mPreferences = fileMenu.addAction("Preferences")
        fileMenu.addSeparator()
        mQuit = fileMenu.addAction("Quit")
        fileMenu.triggered.connect(handleFileAction)

        toolMenu = menuBar.addMenu("&Tools")
        mReset = toolMenu.addAction("Send Reset")
        mLoadPreset = toolMenu.addAction("Import Presets")
        mSavePreset = toolMenu.addAction("Save Preset")
        toolMenu.triggered.connect(handleToolAction)

        viewMenu = menuBar.addMenu("&View")
        mToggleConsole = viewMenu.addAction("Show Console")
        mToggleConsole.setCheckable(True)
        viewMenu.triggered.connect(handleViewAction)

        serialComms = self.acestat.Serial

        vLayout = QVBoxLayout()

        ''' Start Connection bar '''
        connLayout = QHBoxLayout()
        connLayout.addWidget(QLabel("Port:"))

        portCB = FuncComboBox(self.acestat.Serial.PORTS)
        portCB.currentIndexChanged.connect(validateConnection)
        connLayout.addWidget(portCB)

        connLayout.addWidget(QLabel("Baud:"))
        baudCB = QComboBox()
        baudCB.addItems([str(b) for b in self.acestat.Serial.BAUDRATES()])
        baudCB.setCurrentText(str(DEFAULT_BAUD))
        baudCB.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        baudCB.currentIndexChanged.connect(validateConnection)
        connLayout.addWidget(baudCB)

        btnConnect = QPushButton("Connect")
        connLayout.addWidget(btnConnect)
        btnConnect.clicked.connect(Connect)

        disconnectBtn = QPushButton("Disconnect")
        connLayout.addWidget(disconnectBtn)
        disconnectBtn.clicked.connect(self.acestat.disconnect)
        disconnectBtn.setEnabled(False)

        connLayout.addStretch(1)
        vLayout.addLayout(connLayout)
        ''' End Connection bar '''

        ''' Start Horizontal panes '''
        hPanes = QSplitter(Qt.Horizontal, handleWidth=5)
        hPanes.setChildrenCollapsible(False)

        ''' Start Left pane '''
        leftPane = QTabWidget()

        ''' Start Test tab '''
        testForm = TestForm(self.acestat.Definitions)
        SignalTranslator(testForm.sigSubmit, addToQueue)
        leftPane.addTab(testForm, "Test")
        ''' End Test tab '''

        ''' Start Queue tab '''
        testQueue = QueuePanel(self.acestat.paused, self.acestat.queue)
        testQueue.onPause(handlePause)
        testQueue.onCancelItem(handleCancel)
        leftPane.addTab(testQueue, "Queue")
        ''' End Queue tab '''

        ''' Start Multiplexer tab '''
        # multTab = QWidget()
        # leftPane.addTab(multTab, "Multiplexer")
        ''' End Multiplexer tab '''

        hPanes.addWidget(leftPane)
        hPanes.setStretchFactor(0, 0)
        ''' End Left '''

        ''' Start Middle pane '''
        middlePane = QGroupBox("Result Display")

        pltLayout = QVBoxLayout()
        pltLayout.setContentsMargins(0, 0, 0, 0)
        # self.rDisplay = PlotCanvas(self)
        self.rDisplay = QLabel("No results to display")
        self.rDisplay.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        pltLayout.addWidget(self.rDisplay)
        # self.rDisplay.plot([random.uniform(-1, 1) for i in range(10)])
        middlePane.setLayout(pltLayout)
        self.rDisplay.setEnabled(False)

        hPanes.addWidget(middlePane)
        hPanes.setStretchFactor(1, 1)
        ''' End Middle pane '''

        ''' Start Right pane '''
        rightPane = QSplitter(Qt.Vertical, handleWidth=5)
        rightPane.setChildrenCollapsible(False)

        ''' Start Right Top pane '''
        right_top = QGroupBox("Results")
        rtLayout = QVBoxLayout()
        rtLayout.setContentsMargins(0, 0, 0, 0)
        resultList = ResultPanel()
        resultList.sigPlot.connect(plotResult)
        resultList.sigTable.connect(showTable)
        rtLayout.addWidget(resultList)
        right_top.setLayout(rtLayout)
        rightPane.addWidget(right_top)
        ''' End Right Top pane '''

        ''' Start Right Bottom pane '''
        right_bottom = QGroupBox("Console")
        rbLayout = QVBoxLayout()
        rbLayout.setContentsMargins(0, 0, 0, 0)

        consoleTE = QPlainTextEdit()
        consoleTE.setReadOnly(True)
        rbLayout.addWidget(consoleTE)

        rbInputLayout = QHBoxLayout()
        # inputLE = QLineEdit()
        # inputLE.setEnabled(False)
        # inputLE.returnPressed.connect(handleSend)
        #
        # inputBtn = QPushButton("Send")
        # inputBtn.clicked.connect(handleSend)
        # inputBtn.setEnabled(False)

        btnClear = QPushButton("Clear")
        btnClear.clicked.connect(handleConsoleClear)
        # rbInputLayout.addWidget(inputLE)
        # rbInputLayout.addWidget(inputBtn)
        rbInputLayout.addWidget(btnClear)
        rbLayout.addLayout(rbInputLayout)

        right_bottom.setLayout(rbLayout)
        rightPane.addWidget(right_bottom)
        ''' End Right Bottom pane '''

        rightPane.setSizes([1, 9])
        hPanes.addWidget(rightPane)
        hPanes.setStretchFactor(2, 0)
        ''' End Right pane '''

        hPanes.setSizes([215, 1, 200])
        # hPanes.setSizes([215 * self.__xScale, 1, 200 * self.__xScale])
        ''' End Horizontal panes '''

        vLayout.addWidget(hPanes)

        ######################
        ### ACEstatPy Signals ###
        ######################
        SignalTranslator(self.acestat.sigReady, onReady)
        SignalTranslator(self.acestat.sigTestStart, onStart)
        SignalTranslator(self.acestat.sigTestEnd, onEnd)
        SignalTranslator(self.acestat.sigError, onError)
        # SignalTranslator(self.acestat.sigResult, onResult)
        SignalTranslator(serialComms.sigSendMessage, sendingData)
        SignalTranslator(serialComms.sigMessageReceived, receiveData)
        SignalTranslator(serialComms.sigConnected, onConnected)
        SignalTranslator(serialComms.sigDisconnected, onDisconnect)

        validateConnection()
        connectionStatus = QLabel("Disconnected")
        self.statusBar().addPermanentWidget(connectionStatus, 1)
        testStatus = QLabel("")
        self.statusBar().addPermanentWidget(testStatus, 3)

        for s in CONFIG.sections():
            for o in CONFIG.items(s):
                updatePreference(s, *o)

        ui = QWidget()
        ui.setLayout(vLayout)
        self.setCentralWidget(ui)
