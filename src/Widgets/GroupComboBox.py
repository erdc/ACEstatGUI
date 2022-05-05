'''
Last Modified: 2021-04-27

@author: Jesse M. Barr

Contains:
    -GroupDelegate
    -GroupItem
    -GroupComboBox

Changes:
    -2021-04-27
        -GroupComboBox now keeps track of groups, allowing the user to recall
            them.

ToDo:

'''
# PyQt5
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QStyledItemDelegate)
from PyQt5.QtGui import (QStandardItem, QStandardItemModel)


class GroupDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(GroupDelegate, self).initStyleOption(option, index)
        if index.data(Qt.UserRole):
            option.font.setBold(True)
        else:
            option.text = "   " + option.text


class GroupItem(QStandardItem):
    def __init__(self, text):
        super(GroupItem, self).__init__(text)
        self.setData(True, Qt.UserRole)
        self._number_of_childrens = 0
        self.setFlags(self.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)

    def addChild(self, text, tooltip=None):
        it = QStandardItem(text)
        it.setData(False, Qt.UserRole)
        if tooltip is not None:
            it.setToolTip(tooltip)
        self._number_of_childrens += 1
        self.model().insertRow(self.row() + self._number_of_childrens, it)
        return it


class GroupComboBox(QComboBox):
    def __init__(self, parent=None):
        super(GroupComboBox, self).__init__(parent)
        self.setModel(QStandardItemModel(self))
        delegate = GroupDelegate(self)
        self.setItemDelegate(delegate)
        self.__groups = {}

    def Group(self, text):
        if text in self.__groups:
            return self.__groups[text]
        it = GroupItem(text)
        self.__groups[text] = it
        self.model().appendRow(it)
        return it

    def addChild(self, text, tooltip=None):
        it = QStandardItem(text)
        it.setData(True, Qt.UserRole)
        if tooltip is not None:
            it.setToolTip(tooltip)
        self.model().appendRow(it)
