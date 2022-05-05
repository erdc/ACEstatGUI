'''
Last Modified: 2021-05-27

@author: Jesse M. Barr

Contains:
    -TestParameter
    -TestPanel
    -TestForm

Changes:
    -2021-05-05:
        -Hide repeat/export if unchecked
    -2021-04-27:
        -Updated to work with acestatpy

ToDo:

'''
from os import getcwd
from acestatpy import Signal as ACEstatSignal

from PyQt5.QtCore import QEvent, pyqtSignal as Signal
from PyQt5.QtWidgets import (
    QWidget, QFrame, QComboBox, QLabel, QRadioButton, QPushButton, QSpinBox,
    QScrollArea, QGridLayout, QVBoxLayout, QHBoxLayout, QSizePolicy, QCheckBox,
    QStackedWidget, QFileDialog
)


# Local
from . import ElideLabel, FuncComboBox, GroupComboBox


class TestParameter(QWidget):
    sigChanged = Signal(object)

    def __init__(self, param, *args, **kwargs):
        super(TestParameter, self).__init__(*args, **kwargs)
        hLayout = QHBoxLayout()
        hLayout.setContentsMargins(0, 0, 0, 0)
        self.param = param

        if param.type == "int":
            self.input = QSpinBox()
            self.input.setRange(param.min, param.max)
            self.input.valueChanged.connect(self.valueChanged)
        elif param.type == "select":
            self.input = QComboBox()
            self.input.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
            self.input.currentIndexChanged.connect(self.valueChanged)
            self.input.addItems(param.options.values())
        else:
            raise Exception("Unrecognized parameter type")

        hLayout.addWidget(self.input)
        self.setLayout(hLayout)

    def valueChanged(self, val):
        if isinstance(self.input, QComboBox):
            self.input.setToolTip(self.input.currentText())
        self.sigChanged.emit(self.getValue())

    def setValue(self, value):
        if isinstance(self.input, QSpinBox):
            self.input.setValue(int(value))
        elif isinstance(self.input, QComboBox):
            self.input.setCurrentText(self.param.options[value])

    def getValue(self):
        value = None
        # Check widget type
        if isinstance(self.input, QSpinBox):
            value = str(self.input.value())
        elif isinstance(self.input, QComboBox):
            value = list(self.param.options.keys())[self.input.currentIndex()]
        return value


class TestPanel(QWidget):
    name = None
    parameters = None

    def __init__(self, test, *args, **kwargs):
        super(TestPanel, self).__init__(*args, **kwargs)
        self.test = test
        self.name = test.name
        self.parameters = {}
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Presets:"), 0, 0)
        def refreshPresets():
            return list(self.test.presets.keys())
        presets = FuncComboBox(refreshPresets, autoSelect=False)
        layout.addWidget(presets, 0, 1, 1, 2)

        def resetPreset():
            presets.setCurrentIndex(-1)

        for id in self.test.parameters:
            p = self.test.parameters[id]
            layout.addWidget(QLabel("{0}:".format(p.name)), layout.rowCount(), 0)
            self.parameters[id] = TestParameter(p)
            if hasattr(p, "units"):
                layout.addWidget(self.parameters[id], layout.rowCount() - 1, 1)
                layout.addWidget(QLabel(p.units), layout.rowCount() - 1, 2)
            else:
                layout.addWidget(self.parameters[id], layout.rowCount() - 1, 1, 1, 2)
            self.parameters[id].sigChanged.connect(resetPreset)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)

        self.setLayout(layout)

        def applyPreset(idx):
            presets.setToolTip(presets.currentText())
            if not idx:
                return
            for p in self.test.presets[idx].parameters:
                if p in self.parameters:
                    self.parameters[p].blockSignals(True)
                    self.parameters[p].setValue(self.test.presets[idx].parameters[p])
                    self.parameters[p].blockSignals(False)

        resetPreset()
        presets.currentTextChanged.connect(applyPreset)


class TestForm(QWidget):

    def __init__(self, tests, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tests = tests
        self.exportDir = getcwd()
        self.sigSubmit = ACEstatSignal("testform_submit")
        self.initUI()

    def initUI(self):
        if self.layout():
            QWidget().setLayout(self.layout())
        ui = QWidget()
        ui.setObjectName("TestStaging")
        vLayout = QVBoxLayout()

        hLayout = QHBoxLayout()
        hLayout.addWidget(QLabel("Technique:"), 0)

        testSelect = GroupComboBox()

        testSelect.setObjectName("testSelect")
        testSelect.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)

        hLayout.addWidget(testSelect, 1)
        # btnTestHelp = QPushButton("?")
        # btnTestHelp.setObjectName("btnTestHelp")
        # btnTestHelp.setFixedSize(32, 32)
        # tsLayout.addWidget(btnTestHelp, 0)
        vLayout.addLayout(hLayout)

        hLayout = QHBoxLayout()
        hLayout.setContentsMargins(0, 0, 0, 0)
        hLayout.addWidget(QLabel("Run Delay:"))
        preDelay = QSpinBox()
        preDelay.setRange(0, 3600)  # No delay - 1 hour
        hLayout.addWidget(preDelay)
        hLayout.addWidget(QLabel("s"))
        hLayout.addStretch()
        vLayout.addLayout(hLayout)

        self.__testPanels = QStackedWidget()
        self.__testPanels.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        tests = {}

        for t in self.tests.values():
            testSelect.Group(t.technique).addChild(t.name, t.description)
            p = TestPanel(t)
            p.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            tests[t.name] = self.__testPanels.addWidget(p)

        def setTest():
            testSelect.setToolTip(testSelect.currentText())
            self.__testPanels.currentWidget().setSizePolicy(QSizePolicy.Ignored,
                                                     QSizePolicy.Ignored)
            self.__testPanels.setCurrentIndex(tests[testSelect.currentText()])
            self.__testPanels.currentWidget().setSizePolicy(QSizePolicy.Expanding,
                                                     QSizePolicy.Expanding)

        vLayout.addWidget(self.__testPanels)

        testSelect.currentIndexChanged.connect(setTest)
        testSelect.setCurrentIndex(1)

        # Repeat
        repeatGroup = QCheckBox("Repeat")
        vLayout.addWidget(repeatGroup)

        rLayout = QVBoxLayout()
        rLayout.setContentsMargins(15, 0, 0, 15)

        hLayout = QHBoxLayout()
        hLayout.setContentsMargins(0, 0, 0, 0)
        rLimited = QRadioButton()
        hLayout.addWidget(rLimited)
        repeatNum = QSpinBox()
        repeatNum.setRange(2, 100)
        rLimited.toggled.connect(repeatNum.setEnabled)
        rLimited.setChecked(True)
        hLayout.addWidget(repeatNum)
        hLayout.addWidget(QLabel("times"))
        hLayout.addStretch()
        rLayout.addLayout(hLayout)

        hLayout = QHBoxLayout()
        hLayout.setContentsMargins(0, 0, 0, 0)
        rInfinite = QRadioButton()
        hLayout.addWidget(rInfinite)
        hLayout.addWidget(QLabel("Until cancelled"))
        hLayout.addStretch()
        rLayout.addLayout(hLayout)

        hLayout = QHBoxLayout()
        hLayout.setContentsMargins(0, 0, 0, 0)
        hLayout.addWidget(QLabel("Delay Between:"))
        inDelay = QSpinBox()
        inDelay.setRange(0, 3600)  # No delay - 1 hour
        hLayout.addWidget(inDelay)
        hLayout.addWidget(QLabel("s"))
        hLayout.addStretch()
        rLayout.addLayout(hLayout)

        repeatPanel = QWidget()
        repeatPanel.setLayout(rLayout)
        repeatPanel.setVisible(False)
        vLayout.addWidget(repeatPanel)

        repeatGroup.toggled.connect(repeatPanel.setVisible)

        # Export
        exportGroup = QCheckBox("Autosave")
        vLayout.addWidget(exportGroup)

        rLayout = QVBoxLayout()
        rLayout.setContentsMargins(15, 0, 0, 15)
        outpath = QLabel()
        outpath.installEventFilter(self)
        outpath.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

        def setOutDir():
            path = QFileDialog.getExistingDirectory(
                self, "Choose Directory")
            if path:
                self.exportDir = path
                ElideLabel(outpath, path)

        rLayout.addWidget(outpath)

        hLayout = QHBoxLayout()
        hLayout.setContentsMargins(0, 0, 0, 0)
        exportBtn = QPushButton("Choose Location")
        exportBtn.setStyleSheet("padding:2px 15px;")
        exportBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        exportBtn.clicked.connect(setOutDir)
        hLayout.addWidget(exportBtn)
        rLayout.addLayout(hLayout)

        exportPanel = QWidget()
        exportPanel.setLayout(rLayout)
        exportPanel.setVisible(False)
        vLayout.addWidget(exportPanel)

        exportGroup.toggled.connect(exportPanel.setVisible)

        def runTest():
            params = self.CurrentParameters
            export = False
            run_forever = False
            iterations = 1
            if repeatGroup.isChecked():
                if rInfinite.isChecked():
                    run_forever = True
                else:
                    iterations = repeatNum.value()
            if exportGroup.isChecked():
                export = self.exportDir
            self.sigSubmit.emit(
                params[0],
                params[1],
                start_delay=preDelay.value(),
                inner_delay=inDelay.value(),
                run_forever=run_forever,
                iterations=iterations,
                export=export
            )

        hl = QHBoxLayout()
        testSubmitBtn = QPushButton("Add to Queue")
        testSubmitBtn.setStyleSheet("padding:2px 15px;")
        testSubmitBtn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        testSubmitBtn.clicked.connect(runTest)
        hl.addWidget(testSubmitBtn)
        vLayout.addLayout(hl)
        vLayout.addStretch()

        ui.setLayout(vLayout)

        testScroll = QScrollArea()
        testScroll.setFrameStyle(QFrame.NoFrame | QFrame.Plain)
        testScroll.setWidget(ui)
        testScroll.setWidgetResizable(True)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(testScroll)
        self.setLayout(mainLayout)

    @property
    def CurrentParameters(self):
        params = {}
        test = self.__testPanels.currentWidget()
        for p in test.parameters:
            params[p] = test.parameters.get(p).getValue()
        return test.test.id, params

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Resize):
            if isinstance(obj, QLabel):
                ElideLabel(obj, self.exportDir)
        return super().eventFilter(obj, event)
