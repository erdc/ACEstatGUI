from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QIcon, QPixmap, QColor)


def Icon(resource_path, color=None, disabled_color=None):
    pm = QPixmap(resource_path)
    icon = QIcon(pm)
    if color is not None:
        mask = pm.createMaskFromColor(QColor('black'),
                                      Qt.MaskOutColor)
        pm.fill(color)
        pm.setMask(mask)
        icon.addPixmap(pm, QIcon.Normal)

    if disabled_color is not None:
        pm.fill(disabled_color)
        pm.setMask(mask)
        icon.addPixmap(pm, QIcon.Disabled)
    return icon


def Pixmap(resource_path, color=None):
    pm = QPixmap(resource_path)
    if color is not None:
        mask = pm.createMaskFromColor(QColor('black'),
                                      Qt.MaskOutColor)
        pm.fill(color)
        pm.setMask(mask)

    return pm
