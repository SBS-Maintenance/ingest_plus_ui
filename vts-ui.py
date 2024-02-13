import sys

import pymediainfo
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5 import uic


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.show()

    def initUI(self):
        self.ui = uic.loadUi("./window.ui", self)

        self.ui.ingestTypeComboBox.addItem("Consolidation")
        self.ui.ingestTypeComboBox.addItem("Normal")

        self.subjectComboBox.addItem("취재원본(보도국)")
        self.subjectComboBox.addItem("스포츠")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
