'''
Last Modified: 2021-08-20

@author: Jesse M. Barr

Contains:
    -ResultTable

Changes:

ToDo:

'''
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QHeaderView)


class ResultTable(QWidget):

    def __init__(self, labels, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._columnHeaders = labels
        self._data = data
        self.setObjectName("ResultTable")
        self.initUI()

    def initUI(self):

        tableWidget = QTableWidget()
        tableWidget.setRowCount(len(self._data))
        tableWidget.setColumnCount(len(self._columnHeaders))
        for i in range(0, len(self._columnHeaders)):
            tableWidget.setHorizontalHeaderItem(
                i, QTableWidgetItem(self._columnHeaders[i]))

        for r in range(0, len(self._data)):
            for c in range(0, len(self._data[r])):
                item = QTableWidgetItem(str(self._data[r][c]))
                item.setTextAlignment(Qt.AlignCenter)
                tableWidget.setItem(r, c, item)
        tableWidget.move(0, 0)

        tableWidget.horizontalHeader().setTextElideMode(Qt.ElideRight)
        tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        layout = QVBoxLayout()
        layout.addWidget(tableWidget)
        self.setLayout(layout)
