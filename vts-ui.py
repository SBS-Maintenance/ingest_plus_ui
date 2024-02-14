import sys
import os

import pymediainfo
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QListWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QProcess

form_class = uic.loadUiType("window.ui")[0]


class MyApp(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.show()
        self.items = []
        self.isGopro = False

    def init_ui(self):
        self = uic.loadUi("./window.ui", self)

        self.ingestTypeComboBox.addItem("Consolidation")
        self.ingestTypeComboBox.addItem("Normal")

        self.subjectComboBox.addItem("취재원본(보도국)")
        self.subjectComboBox.addItem("스포츠")

        self.setAcceptDrops(True)

        self.upButton.clicked.connect(self.item_up)
        self.downButton.clicked.connect(self.item_down)

        self.xmlCreateButton.clicked.connect(self.create_xml)

    def create_xml(self):
        pass

    def item_up(self):
        currentRow = self.fileListWidget.currentRow()
        currentItem = self.fileListWidget.takeItem(currentRow)
        self.fileListWidget.insertItem(currentRow - 1, currentItem)
        self.fileListWidget.setCurrentRow(currentRow-1)

    def item_down(self):
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
                path = url.toLocalFile().replace("/", "\\")
                # item = QListWidgetItem(path)
                # self.fileListWidget.addItem(item)
                self.items.append(path)
            event.accept()
        else:
            event.ignore()

        firstItem = self.items[0]
        if (os.path.isdir(firstItem)):
            self.items = [os.path.join(firstItem, f) for f in os.listdir(
                firstItem) if (os.path.isfile(os.path.join(firstItem, f)))]
        if (firstItem.split("\\")[-1] == "100GOPRO" or firstItem.split("\\")[-2] == "100GOPRO"):
            self.isGopro = True

        self.sort()

    def sort(self):
        itemDict = {}
        if self.isGopro:
            self.items = [f for f in self.items if f.split(
                ".")[-1].lower() == "mp4"]
            gopro_dict = {}
            for item in self.items:
                gopro_dict[item[-7:-4]] = []
            for item in self.items:
                gopro_dict[item[-7:-4]].append(item)
            self.items = []
            for key in gopro_dict.keys():
                gopro_dict[key].sort(key=lambda x: x.split(
                    "\\")[-1].split(".")[0][:-4])
                for item in gopro_dict[key]:
                    self.items.append(item)
        else:
            for item in self.items:
                itemDict[item.split("\\")[-1]] = item
            self.items = []
            for key in (sorted(itemDict.keys())):
                self.items.append(itemDict[key])

        for item in self.items:
            self.fileListWidget.addItem(QListWidgetItem(item))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
