'''
Last Modified: 2021-05-07

@author: Jesse M. Barr

Contains:
    -PreferenceDialog

Changes:

ToDo:

'''
# PyQt
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QLabel,
    QSpinBox, QVBoxLayout, QGridLayout, QCheckBox
)
# Installed
from configparser import SafeConfigParser


def LoadConfig(fPath):
    config = SafeConfigParser()
    config.read(fPath)

    if not config.has_section("console"):
        config.add_section("console")

    try: config.getboolean('console', 'show_console')
    except: config.set('console', 'show_console', 'false')
    try: config.getint('console', 'console_lines')
    except: config.set('console', 'console_lines', '500')

    config.set('console', 'console_lines', str(min(config.getint('console', 'console_lines'), 100000)))
    config.set('console', 'console_lines', str(max(config.getint('console', 'console_lines'), 1)))

    if not config.has_section("results"):
        config.add_section("results")

    try: config.getint('results', 'result_limit')
    except: config.set('results', 'result_limit', '10')
    try: config.getint('results', 'result_sort')
    except: config.set('results', 'result_sort', '-1')

    config.set("results", "result_limit", str(min(config.getint("results", "result_limit"), 100)))
    config.set("results", "result_limit", str(max(config.getint("results", "result_limit"), 1)))

    return config


class SettingsDialog(QDialog):
    def __init__(self, *args, **kwargs):
        config = kwargs.pop("config")
        self.__changes = {}
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Preferences")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.button(QDialogButtonBox.Ok).setText("Apply")
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()

        ''' CONSOLE '''
        layout.addWidget(QLabel("Console:"))

        consoleLayout = QGridLayout()
        consoleLayout.setContentsMargins(15, 0, 0, 5)

        consoleLayout.addWidget(QLabel("Show Console:"), consoleLayout.rowCount(), 0)
        showConsole = QCheckBox()
        showConsole.setChecked(config.getboolean("console", "show_console"))
        consoleLayout.addWidget(showConsole, consoleLayout.rowCount()-1, 1)

        def setShowConsole(show):
            self.__changes[('console', 'show_console')] = show

        showConsole.toggled.connect(setShowConsole)

        consoleLayout.addWidget(QLabel("Console Line Limit:"), consoleLayout.rowCount(), 0)
        consoleLimit = QSpinBox()
        consoleLimit.setRange(1, 100000)
        consoleLimit.setValue(config.getint("console", "console_lines"))
        consoleLayout.addWidget(consoleLimit, consoleLayout.rowCount()-1, 1)

        def setConsoleLimit(lim):
            self.__changes[('console', 'console_lines')] = lim

        consoleLimit.valueChanged.connect(setConsoleLimit)

        layout.addLayout(consoleLayout)

        ''' RESULTS '''
        layout.addWidget(QLabel("Results:"))

        resultsLayout = QGridLayout()
        resultsLayout.setContentsMargins(15, 0, 0, 5)

        resultsLayout.addWidget(QLabel("Sort Results:"), resultsLayout.rowCount(), 0)
        resultSort = QComboBox()
        resultSort.addItems(["Newest to Oldest", "Oldest to Newest"])
        resultSort.setCurrentIndex(int(config.getint("results", "result_sort") >= 0))
        resultsLayout.addWidget(resultSort, resultsLayout.rowCount()-1, 1)

        def setResultSort(sort):
            if sort == 0:
                sort = -1
            self.__changes[('results', 'result_sort')] = sort

        resultSort.currentIndexChanged.connect(setResultSort)

        resultsLayout.addWidget(QLabel("Result Limit:"), resultsLayout.rowCount(), 0)
        resultLimit = QSpinBox()
        resultLimit.setRange(1, 100)
        resultLimit.setValue(config.getint("results", "result_limit"))
        resultsLayout.addWidget(resultLimit, resultsLayout.rowCount()-1, 1)

        def setResultLimit(lim):
            self.__changes[('results', 'result_limit')] = lim

        resultLimit.valueChanged.connect(setResultLimit)

        layout.addLayout(resultsLayout)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    @property
    def Changes(self):
        return self.__changes
