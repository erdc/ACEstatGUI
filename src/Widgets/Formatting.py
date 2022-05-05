'''
Last Modified: 2020-05-12

@author: Jesse M. Barr

Contains:
    -ElideLabel

ToDo:

'''
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFontMetrics

def ElideLabel(obj, text):
    metrics = QFontMetrics(obj.font())
    obj.setText(metrics.elidedText(text, Qt.ElideRight, obj.width()-2))
    obj.setToolTip(text)
