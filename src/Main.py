'''
Last Modified: 2020-06-30

@author: Jesse M. Barr

Runs ACEstatGUI application.

'''
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QStyleFactory

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Import the main GUI after initializing app. This allows using message
    #   dialogs if any errors occur.
    from ACEstatGUI import ACEstatGUI
    ex = ACEstatGUI()
    ex.show()
    sys.exit(app.exec_())
