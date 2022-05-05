'''
Last Modified: 2021-04-30

@author: Jesse M. Barr

Contains:
    -CollapsibleBox

Changes:
    -2021-04-27:
        -Using the QToolButton expansion flag to determine whether the widget
            should be expanded or not frequently did not function correctly.
            Solved by adding a simple class boolean flag.
ToDo:

'''
from PyQt5.QtCore import (
    Qt, QEvent, QParallelAnimationGroup, QAbstractAnimation, QPropertyAnimation,
    pyqtSignal as Signal
)
from PyQt5.QtGui import QColor, QFont, QTransform
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QToolButton, QScrollArea, QFrame,
    QSizePolicy, QLabel, QStyle
)
# Local
from .Images import Pixmap
from .Formatting import ElideLabel


class ScrollArea(QScrollArea):
    resized = Signal()

    def resizeEvent(self, e):
        self.resized.emit()
        return super(ScrollArea, self).resizeEvent(e)


class CollapsibleBox(QWidget):

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.__imgExpand = Pixmap("light:plus.png", QColor("white"))
        self.__imgCollapse = Pixmap("light:minus.png", QColor("white"))

        self.__header = QToolButton()
        self.__header.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.__header.setStyleSheet("border: none;")
        self.__header.setCheckable(True)
        self.__header.setChecked(False)

        btnLayout = QHBoxLayout()
        btnLayout.setContentsMargins(0, 0, 0, 0)

        self.arrow = QLabel()
        self.arrow.setPixmap(self.__imgExpand)
        btnLayout.addWidget(self.arrow)

        lbl = QLabel()
        lbl.static = title
        lbl.installEventFilter(self)
        btnLayout.addWidget(lbl, 1)

        self.__header.setLayout(btnLayout)

        self.toggle_animation = QParallelAnimationGroup(self)

        self.content_area = ScrollArea(maximumHeight=0, minimumHeight=0)
        self.content_area.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QFrame.NoFrame)
        self.content_area.resized.connect(self.updateContentLayout)

        lay = QVBoxLayout()
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.__header)
        lay.addWidget(self.content_area)
        self.setLayout(lay)

        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QPropertyAnimation(self.content_area, b"maximumHeight")
        )

        def start_animation(checked):
            self.arrow.setPixmap(
                self.__imgCollapse
                if checked
                else self.__imgExpand
            )
            self.toggle_animation.setDirection(
                QAbstractAnimation.Forward
                if checked
                else QAbstractAnimation.Backward
            )
            self.toggle_animation.start()

        self.__header.toggled.connect(start_animation)

    def header(self):
        return self.__header

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        margins = layout.getContentsMargins()
        collapsed_height = self.__header.layout().sizeHint().height() + margins[3]
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(100)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(100)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

    def updateContentLayout(self):
        if self.__header.isChecked() and self.toggle_animation.state() != self.toggle_animation.Running:
            margins = self.content_area.layout().getContentsMargins()
            collapsed_height = self.__header.layout().sizeHint().height() + margins[3]
            content_height = self.content_area.layout().sizeHint().height()
            self.setMinimumHeight(collapsed_height + content_height)
            self.setMaximumHeight(collapsed_height + content_height)
            self.content_area.setMaximumHeight(content_height)
        self.updateGeometry()
        p = self.parent()
        if isinstance(p, ScrollArea):
            p.resized.emit()

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Resize):
            if hasattr(obj, "static"):
                ElideLabel(obj, obj.static)
        return super().eventFilter(obj, event)


if __name__ == "__main__":
    import sys
    import random
    from PyQt5.QtGui import QColor
    from PyQt5.QtWidgets import QLabel, QDockWidget, QMainWindow, QApplication

    app = QApplication(sys.argv)

    w = QMainWindow()
    w.setCentralWidget(QWidget())
    dock = QDockWidget("Collapsible Demo")
    w.addDockWidget(Qt.LeftDockWidgetArea, dock)
    scroll = QScrollArea()
    dock.setWidget(scroll)
    content = QWidget()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    vlay = QVBoxLayout(content)
    for i in range(10):
        box = CollapsibleBox("Collapsible Box Header-{}".format(i))
        vlay.addWidget(box)
        lay = QVBoxLayout()
        for j in range(8):
            label = QLabel("{}".format(j))
            color = QColor(*[random.randint(0, 255) for _ in range(3)])
            label.setStyleSheet(
                "background-color: {}; color : white;".format(color.name())
            )
            label.setAlignment(Qt.AlignCenter)
            lay.addWidget(label)

        box.setContentLayout(lay)
    vlay.addStretch()
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())
