import sys
import os

import pymediainfo
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QListWidgetItem, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QProcess

from xml.etree.ElementTree import Element, SubElement, ElementTree

import datetime

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

        self.deleteButton.clicked.connect(self.delete_item)
        self.resetButton.clicked.connect(self.reset_list)

    def reset_list(self):
        self.fileListWidget.clear()

    def delete_item(self):
        self.fileListWidget.takeItem(self.fileListWidget.currentRow())

    def create_xml(self):
        filename = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")+".xml"
        path = "./"+filename
        with open(path, "w") as f:
            f.write("")

        root = Element("sbsvts")
        job_info = SubElement(root, "job_info")

        source_info = SubElement(job_info, "source_info")
        SubElement(
            source_info, "ingest_type").text = self.ingestTypeComboBox.currentText()
        SubElement(
            source_info, "subject").text = self.subjectComboBox.currentText()
        SubElement(source_info, "folder").text = self.folderComboBox.currentText()
        SubElement(source_info, "event").text = self.eventComboBox.currentText()
        SubElement(
            source_info, "category").text = self.categoryComboBox.currentText()
        SubElement(
            source_info, "ingest_src").text = self.sourceComboBox.currentText()
        SubElement(
            source_info, "restriction").text = self.restrictionComboBox.currentText()
        SubElement(source_info, "title").text = self.titleLineEdit.text()

        creation_info = SubElement(job_info, "creation_info")
        SubElement(creation_info, "department").text = self.deptLineEdit.text()
        SubElement(creation_info,
                   "journalist").text = self.journalistLineEdit.text()
        SubElement(creation_info,
                   "video_reporter").text = self.videoReporterLineEdit.text()
        SubElement(creation_info, "place").text = self.placeLineEdit.text()
        SubElement(creation_info,
                   "date").text = datetime.datetime.strptime(self.videoDateWidget.selectedDate().toString(Qt.ISODate), "%Y-%m-%d").strftime("%Y-%m-%d")
        SubElement(creation_info,
                   "contents").text = self.contentTextEdit.toPlainText()

        file_list = SubElement(job_info, "file_list")
        for i in range(self.fileListWidget.count()):
            file = SubElement(file_list, "file")
            SubElement(file, "order").text = str(i)
            SubElement(
                file, "full_path").text = self.fileListWidget.item(i).text()

        tree = ElementTree(root)
        tree.write(path, encoding="utf-8", xml_declaration=True)
        QMessageBox.information(self, "XML 생성 완료", "XML 생성을 완료하였습니다.")

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
