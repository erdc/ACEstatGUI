'''
Last Modified: 2021-05-06

@author: Jesse M. Barr

Contains:
    -FuncComboBox

Changes:
-2021-05-06:
    -Allow a list or a function.
    -Block signals while updating the list, to prevent triggering selection
        change events.
-2021-04-27:
    -Changed from PortComboBox to FuncComboBox. Now the list is refreshed
        through a provided function.

ToDo:

'''
# PyQt5
from PyQt5.QtWidgets import QComboBox


class FuncComboBox(QComboBox):
    def __init__(self, items, autoSelect=True, *args, **kwargs):
        super(QComboBox, self).__init__(*args, **kwargs)
        if not callable(items) and not isinstance(items, list):
            raise Exception("Items must be a function or a list.")
        self.setMinimumContentsLength(10)
        self.__items = items
        self.__autoSelect = autoSelect
        self.refreshItems()

    def refreshItems(self):
        if callable(self.__items):
            return self.updateList(self.__items())
        return self.updateList(self.__items)

    def updateList(self, new_list):
        idx = self.currentIndex()
        sel = self.currentText()
        if not self.__autoSelect:
            self.blockSignals(True)
        self.clear()
        self.addItems(new_list)
        self.blockSignals(False)
        if idx == -1 and not self.__autoSelect:
            self.setCurrentIndex(idx)
        else:
            self.setCurrentText(sel)

    def keyReleaseEvent(self, event):
        self.refreshItems()
        super(FuncComboBox, self).keyReleaseEvent(event)

    def mousePressEvent(self, event):
        self.refreshItems()
        super(FuncComboBox, self).mousePressEvent(event)
