import sys

import pymediainfo
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QListWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QProcess

form_class = uic.loadUiType("window.ui")[0]


class MyApp(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.show()

    def initUI(self):
        self = uic.loadUi("./window.ui", self)

        self.ingestTypeComboBox.addItem("Consolidation")
        self.ingestTypeComboBox.addItem("Normal")

        self.subjectComboBox.addItem("취재원본(보도국)")
        self.subjectComboBox.addItem("스포츠")

        self.setAcceptDrops(True)

        self.upButton.clicked.connect(self.itemUp)
        self.downButton.clicked.connect(self.itemDown)

        self.xmlCreateButton.clicked.connect(self.createXml)

    def createXml(self):
        pass

    def itemUp(self):
        currentRow = self.fileListWidget.currentRow()
        currentItem = self.fileListWidget.takeItem(currentRow)
        self.fileListWidget.insertItem(currentRow - 1, currentItem)
        self.fileListWidget.setCurrentRow(currentRow-1)

    def itemDown(self):
        currentRow = self.fileListWidget.currentRow()
        currentItem = self.fileListWidget.takeItem(currentRow)
        self.fileListWidget.insertItem(currentRow + 1, currentItem)
        self.fileListWidget.setCurrentRow(currentRow+1)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                item = QListWidgetItem(path)
                self.fileListWidget.addItem(item)
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
