import sys
import os
import datetime
import time
import configparser
import json
import struct
import socket
import select
from xml.etree.ElementTree import Element, SubElement, ElementTree
from time import sleep
from threading import Thread
import logging
import traceback
import logging.handlers
import re
from functools import wraps

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QListWidgetItem,
    QMessageBox,
    QTreeWidgetItem,
    QAbstractItemView,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QCloseEvent, QStandardItemModel, QStandardItem, QColor
from PyQt5 import uic

from natsort import natsorted, os_sorted

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
streamhandler = logging.StreamHandler()
streamhandler.setFormatter(formatter)
logger.addHandler(streamhandler)
timedfilehandler = logging.handlers.TimedRotatingFileHandler(
    filename="log//logfile.log", when="midnight", interval=1, encoding="utf-8"
)
timedfilehandler.setFormatter(formatter)
timedfilehandler.suffix = "%Y%m%d"
logger.addHandler(timedfilehandler)


def tback(fn):
    @wraps(fn)
    def wrapit(self, *args, **kwargs):
        try:
            return fn(self)
        except:
            logger.exception(traceback.format_exc())

    return wrapit


def tback_args(fn):
    @wraps(fn)
    def wrapit(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except:
            logger.exception(traceback.format_exc())

    return wrapit


config = configparser.ConfigParser()
config.read("config.ini")

STATUS_PORT = int(config["ports"]["status"])
STATUS_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
STATUS_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
STATUS_SOCKET.bind(("", STATUS_PORT))
mreq = struct.pack(
    "4sl", socket.inet_aton(config["ip"]["multicast"]), socket.INADDR_ANY
)
STATUS_SOCKET.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


HOST_IP = config["ip"]["unicast"]
HOST_PORT = int(config["ports"]["unicast"])
SEND_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


source_news_folder = ".//source_news_folder.json"
source_news_category = ".//source_news_category.json"
source_digital_event = ".//source_digital_event.json"
source_digital_folder = ".//source_digital_folder.json"

news_folder_list = []
with open(source_news_folder, encoding="utf-8") as folder_json:
    folders = json.load(folder_json)
    news_folder_list.append({"KsimTree": folders["KsimTree"]})
    for folder in folders["ChildNodes"]:
        news_folder_list.append(folder)
        if folder["ChildNodes"]:
            for folder in folder["ChildNodes"]:
                news_folder_list.append(folder)

digital_folder_list = []
with open(source_digital_folder, encoding="utf-8") as folder_json:
    folders = json.load(folder_json)
    digital_folder_list.append({"KsimTree": folders["KsimTree"]})
    for folder in folders["ChildNodes"]:
        digital_folder_list.append(folder)
        if folder["ChildNodes"]:
            for folder in folder["ChildNodes"]:
                digital_folder_list.append(folder)

target_list = {
    "취재원본 (보도국)": news_folder_list,
    "원본-디지털": digital_folder_list,
}

event_list = []
with open(source_digital_event, encoding="utf-8") as event_json:
    event_list = json.load(event_json)["ChildNodes"]

category1_list = []
with open(source_news_category, encoding="utf-8") as category_json:
    category1_list = json.load(category_json)["ChildNodes"]

category2_list = [""]
for category2 in category1_list[0]["ChildNodes"]:
    category2_list.append(category2["KsimTree"]["Name"])


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
form_class = uic.loadUiType(BASE_DIR + r"\\window.ui")[0]

sources = ["VCR", "GRAPHIC", "RSW", "CAP", "XDCAM", "TH", "WEB", "6mm(HDV)"]

restrictions = ["보도제작", "보도본부", "스포츠", "전체", "보도"]

if not os.path.exists("work"):
    os.makedirs("work")

if not os.path.exists("log"):
    os.makedirs("log")


class Model(QStandardItemModel):
    def __init__(self, data):
        QStandardItemModel.__init__(self)

        for j, _subject in enumerate(data):
            item = QStandardItem(_subject["upper"])
            for k, mid in enumerate(_subject["mid"]):
                item2 = QStandardItem(mid["mid"])
                item.setChild(k, 0, item2)
                if "low" in mid.keys():
                    for l, low in enumerate(mid["low"]):  # noqa: E741
                        child2 = QStandardItem(low)
                        item2.setChild(l, 0, child2)
            self.setItem(j, 0, item)


class ListenThread(QThread):
    received = pyqtSignal(object)

    def __init__(self, parent, sock: socket):
        QThread.__init__(self, parent)
        self.sock = sock
        self.should_work = True
        self.parent = parent
        Thread(target=self.get_status, daemon=True).start()

    @tback
    def get_status(self):
        while self.should_work:
            SEND_SOCKET.sendto("get_title_fail".encode(), (HOST_IP, HOST_PORT))
            sleep(0.05)
            SEND_SOCKET.sendto("get_title_finished".encode(), (HOST_IP, HOST_PORT))
            sleep(0.05)
            SEND_SOCKET.sendto("get_title".encode(), (HOST_IP, HOST_PORT))
            sleep(5)

    @tback_args
    def send_msg(self, msg: str):
        SEND_SOCKET.sendto(msg.encode(), (HOST_IP, HOST_PORT))
        sleep(0.05)
        return True

    @tback
    def run(self):
        with STATUS_SOCKET:
            while self.should_work:
                select.select([self.sock], [], [])
                msg = self.sock.recvfrom(4096 * 4)[0]
                self.received.emit(msg.decode())
                js: dict = json.loads(msg.decode())
                temp_fin_title_list = []
                temp_fail_src_list = []
                temp_titles = []
                if "get_title" in js.keys():
                    temp_titles = js["get_title"]
                    # if (
                    #     len(
                    #         [
                    #             x
                    #             for x in temp_titles
                    #             if x not in self.parent.finished_title_list
                    #         ]
                    #     )
                    #     == 1
                    # ):
                    self.parent.current_title = [
                        x
                        for x in temp_titles
                        if x not in self.parent.finished_title_list
                        and x not in self.parent.failed_title_list
                    ]
                elif "get_title_fail" in js.keys():
                    self.parent.failed_title_list = js["get_title_fail"]
                elif "get_title_finished" in js.keys():
                    temp_fin_title_list = js["get_title_finished"]
                    self.parent.finished_title_list = [
                        x
                        for x in temp_fin_title_list
                        if x not in self.parent.failed_title_list
                    ]
                elif "get_src_fail" in js.keys():
                    temp_fail_src_list = js["get_src_fail"]
                    self.parent.failed_src_list = [
                        os.path.normpath(x) for x in temp_fail_src_list
                    ]

    def stop(self):
        self.should_work = False


class MyApp(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_ui()
        self.show()

        self.job_list = []
        self.load_jobs()

        self.items = []
        self.current_title = [None]
        self.finished_title_list = [None]
        self.failed_title_list = [None]

        self.selected_job_row = -1

        self.failed_src_list = []

        self.listen_status_thread = ListenThread(self, STATUS_SOCKET)
        self.listen_status_thread.received.connect(self.on_status_received)
        self.listen_status_thread.start()

    @tback
    def load_jobs(self) -> None:
        if os.path.exists("work/jobs.txt"):
            with open("work/jobs.txt", "r", encoding="utf-8") as f:
                file_content = f.read()
            if file_content != "":
                self.job_list = json.loads(file_content)
                for i, job in enumerate(self.job_list):
                    item = QTreeWidgetItem()
                    item.setText(0, job["metadata"]["title"])
                    item.setText(1, job["ingest_status"])
                    item.setText(2, job["ftp_status"])
                    self.root.addChild(item)
            else:
                self.job_list = []
                for i in range(self.root.childCount()):
                    self.root.removeChild(self.root.child(0))

    @tback_args
    def on_status_received(self, msg: str) -> None:
        display_str = ""
        for k in sorted(json.loads(msg).keys()):
            display_str += f"{k.ljust(22)} : {json.loads(msg)[k]}\n"
        self.statusPlainTextEdit.setPlainText(display_str)

        if (
            len(self.finished_title_list) == 0
            and len(self.failed_title_list) == 0
            and len(self.current_title) == 0
        ):
            if self.titleLineEdit.text() == "":
                with open("work/jobs.txt", "w", encoding="utf-8") as f:
                    f.write("")
                self.load_jobs()

            return None

        for index, job in enumerate(self.job_list):
            if job["metadata"]["title"] in self.finished_title_list:
                self.job_list[index]["ingest_status"] = "완료"
                self.root.child(index).setText(1, self.job_list[index]["ingest_status"])
                self.root.child(index).setText(2, self.job_list[index]["ftp_status"])
            elif job["metadata"]["title"] in self.failed_title_list:
                self.job_list[index]["ingest_status"] = "실패"
                self.root.child(index).setText(1, self.job_list[index]["ingest_status"])
            elif job["metadata"]["title"] in self.current_title:
                self.job_list[index]["ingest_status"] = "작업중"
                self.root.child(index).setText(1, self.job_list[index]["ingest_status"])
            item = QTreeWidgetItem()

        with open("work/jobs.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.job_list))

        for i in range(self.root.childCount()):
            item = self.root.child(i)
            if self.job_list[i]["ingest_status"] == "완료":
                self.jobTreeWidget.removeItemWidget(item, 1)

    def init_ui(self):
        self.ingestTypeComboBox.addItem("Consolidation")
        self.ingestTypeComboBox.addItem("Single")

        self.centralmediatypecodeComboBox.addItem("취재원본 (보도국)")
        self.centralmediatypecodeComboBox.addItem("원본-디지털")
        self.centralmediatypecodeComboBox.currentIndexChanged.connect(
            self.centralmediatypecodeChanged
        )

        for folder in news_folder_list:
            if folder["KsimTree"]["Flag"] == 10002 or folder["KsimTree"]["Flag"] == 0:
                if folder["KsimTree"]["Name"] not in WEEKDAYS:
                    self.folderComboBox.addItem(folder["KsimTree"]["Name"])

        for category1 in category1_list:
            self.categoryComboBox1.addItem(category1["KsimTree"]["Name"])

        for category2 in category2_list:
            self.categoryComboBox2.addItem(category2)

        self.categoryComboBox1.currentIndexChanged.connect(self.category1changed)

        self.categoryComboBox2.currentIndexChanged.connect(self.category2changed)

        self.contentTextEdit.setAcceptDrops(False)

        for src in sources:
            self.sourceComboBox.addItem(src)

        for r in restrictions:
            self.restrictionComboBox.addItem(r)

        self.fileListWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.setAcceptDrops(True)

        self.upButton.clicked.connect(self.item_up)
        self.downButton.clicked.connect(self.item_down)

        self.xmlCreateButton.clicked.connect(self.create_xml)

        self.deleteButton.clicked.connect(self.delete_item)
        self.resetButton.clicked.connect(self.reset_list)

        self.jobTreeWidget.setColumnCount(3)
        self.jobTreeWidget.setHeaderLabels(["제목", "인제스트", "전송"])
        self.jobTreeWidget.setColumnWidth(1, 80)
        self.jobTreeWidget.setColumnWidth(2, 80)
        self.jobTreeWidget.setColumnWidth(0, 410)
        self.root = self.jobTreeWidget.invisibleRootItem()
        self.jobTreeWidget.itemClicked.connect(self.onTreeItemClicked)

        self.filePushButton.clicked.connect(self.add_files)
        self.dirPushButton.clicked.connect(self.add_folders)

        self.newPushButton.clicked.connect(self.newPushButtonHandler)

    @tback
    def newPushButtonHandler(self):
        self.centralmediatypecodeComboBox.setCurrentIndex(0)
        self.folderComboBox.setCurrentIndex(0)
        self.sourceComboBox.setCurrentIndex(0)
        self.categoryComboBox1.setCurrentIndex(0)
        self.categoryComboBox2.setCurrentIndex(0)
        self.categoryComboBox3.setCurrentIndex(0)
        self.restrictionComboBox.setCurrentIndex(0)
        self.titleLineEdit.setText("")
        self.deptLineEdit.setText("")
        self.interviewrepoterLineEdit.setText("")
        self.mediarepoterLineEdit.setText("")
        self.shootingplaceLineEdit.setText("")
        self.contentTextEdit.setPlainText("")
        self.fileListWidget.clear()
        self.items.clear()
        self.videoDateWidget.setSelectedDate(
            QDate(
                int(datetime.date.today().strftime("%Y")),
                int(datetime.date.today().strftime("%m")),
                int(datetime.date.today().strftime("%d")),
            )
        )

    @tback
    def add_files(self):
        fnames = QFileDialog.getOpenFileNames(self, "파일 추가")[0]
        self.items = self.items + sort(fnames)

        self.fileListWidget.clear()
        for item in self.items:
            self.fileListWidget.addItem(QListWidgetItem(item))

    @tback
    def add_folders(self):
        dname = QFileDialog.getExistingDirectory(self, "폴더 추가")
        self.items = self.items + sort([dname])

        self.fileListWidget.clear()
        for item in self.items:
            self.fileListWidget.addItem(QListWidgetItem(item))

    @tback_args
    def onTreeItemClicked(self, item: QStandardItem, column):
        self.selected_job_row = self.jobTreeWidget.indexFromItem(item).row()
        logging.info(self.selected_job_row)

        job = self.job_list[self.jobTreeWidget.indexFromItem(item).row()]

        index = self.ingestTypeComboBox.findText(job["ingest_type"])
        if index >= 0:
            self.ingestTypeComboBox.setCurrentIndex(index)

        index = self.centralmediatypecodeComboBox.findText(
            job["source_info"]["centralmediatypecode"]
        )
        if index >= 0:
            self.centralmediatypecodeComboBox.setCurrentIndex(index)

        index = self.folderComboBox.findText(
            job["source_info"]["folder"]["folder_name"]
        )
        if index >= 0:
            self.folderComboBox.setCurrentIndex(index)

        index = self.sourceComboBox.findText(job["source_info"]["ingest_src"])
        if index >= 0:
            self.sourceComboBox.setCurrentIndex(index)

        for i in range(1, 4):
            eval(
                f"self.categoryComboBox{i}.setCurrentIndex(self.categoryComboBox{i}.findText(job['source_info']['category']['category{i}']))"
            )

        index = self.restrictionComboBox.findText(job["source_info"]["restriction"])
        if index >= 0:
            self.restrictionComboBox.setCurrentIndex(index)

        self.titleLineEdit.setText(job["metadata"]["title"])

        self.deptLineEdit.setText(job["metadata"]["sub_metadata"]["interviewdept"])

        self.interviewrepoterLineEdit.setText(
            job["metadata"]["sub_metadata"]["interviewrepoter"]
        )

        self.mediarepoterLineEdit.setText(
            job["metadata"]["sub_metadata"]["mediarepoter"]
        )

        self.shootingplaceLineEdit.setText(
            job["metadata"]["sub_metadata"]["shootingplace"]
        )

        date: list = job["metadata"]["sub_metadata"]["shootingdate"].split("-")
        year: str = date[0]
        month: str = date[1]
        day: str = date[2]
        date_var = QDate(int(year), int(month), int(day))
        self.videoDateWidget.setSelectedDate(date_var)

        self.contentTextEdit.setPlainText(job["metadata"]["contents"])

        self.listen_status_thread.send_msg("get_src_fail")

        self.items.clear()
        self.fileListWidget.clear()
        for i, file in enumerate(job["files"]):
            item = QListWidgetItem(job["files"][str(i)])
            if os.path.normpath(job["files"][str(i)]) in self.failed_src_list:
                item.setBackground(QColor("#ff0000"))
            self.fileListWidget.addItem(item)
        for x in range(self.fileListWidget.count()):
            self.items.append(self.fileListWidget.item(x).text())

    @tback
    def centralmediatypecodeChanged(self):
        self.categoryComboBox1.clear()
        self.categoryComboBox2.clear()
        self.categoryComboBox3.clear()
        self.folderComboBox.clear()
        self.folderComboBox.clear()
        if self.centralmediatypecodeComboBox.currentText() == "취재원본 (보도국)":
            for folder in news_folder_list:
                if (
                    folder["KsimTree"]["Flag"] == 10002
                    or folder["KsimTree"]["Flag"] == 0
                ):
                    if folder["KsimTree"]["Name"] not in WEEKDAYS:
                        self.folderComboBox.addItem(folder["KsimTree"]["Name"])
            for category1 in category1_list:
                self.categoryComboBox1.addItem(category1["KsimTree"]["Name"])

        elif self.centralmediatypecodeComboBox.currentText() == "원본-디지털":
            for folder in digital_folder_list:
                if (
                    folder["KsimTree"]["Flag"] == 10002
                    or folder["KsimTree"]["Flag"] == 0
                ):
                    self.folderComboBox.addItem(folder["KsimTree"]["Name"])

    @tback
    def category1changed(self):
        self.categoryComboBox2.clear()

        category2_list = [""]
        for category1 in category1_list:
            if category1["KsimTree"]["Name"] == self.categoryComboBox1.currentText():
                if category1["ChildNodes"] != None:
                    for category2 in category1["ChildNodes"]:
                        category2_list.append(category2["KsimTree"]["Name"])

        for category2 in category2_list:
            self.categoryComboBox2.addItem(category2)

    @tback
    def category2changed(self):
        self.categoryComboBox3.clear()

        category3_list = [""]
        for category1 in category1_list:
            if category1["KsimTree"]["Name"] == self.categoryComboBox1.currentText():
                if category1["ChildNodes"] is not None:
                    for category2 in category1["ChildNodes"]:
                        if (
                            category2["KsimTree"]["Name"]
                            == self.categoryComboBox2.currentText()
                        ):
                            if category2["ChildNodes"] is not None:
                                for category3 in category2["ChildNodes"]:
                                    category3_list.append(category3["KsimTree"]["Name"])

        for category3 in category3_list:
            self.categoryComboBox3.addItem(category3)

    @tback
    def reset_list(self):
        self.items.clear()
        self.fileListWidget.clear()

    @tback
    def delete_item(self):
        list_items: list = self.fileListWidget.selectedItems()
        if not list_items:
            return
        for item in list_items:
            self.fileListWidget.takeItem(self.fileListWidget.row(item))
        self.items.clear()
        for x in range(self.fileListWidget.count()):
            self.items.append(self.fileListWidget.item(x).text())

    @tback
    def create_xml(self):
        length_check_dict = {
            "취재부서": len(self.deptLineEdit.text().encode("utf-8")),
            "취재기자": len(self.interviewrepoterLineEdit.text().encode("utf-8")),
            "영상기자": len(self.mediarepoterLineEdit.text().encode("utf-8")),
            "촬영장소": len(self.shootingplaceLineEdit.text().encode("utf-8")),
        }
        too_long_entities = ""
        for key, length in length_check_dict.items():
            if length > 24:
                too_long_entities = too_long_entities + "," + key
        if len(too_long_entities) > 0:
            too_long_entities = too_long_entities[1:]
            QMessageBox.information(
                self,
                "오류",
                f"{too_long_entities}의 길이가 한글 8자를 넘습니다. 한글 8자 미만으로 줄여주세요.",
            )
            return None

        titles = []
        for item in self.job_list:
            titles.append(item["metadata"]["title"])
        job = {}

        filename = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S") + ".xml"
        path = config["xml"]["dir"] + "//" + filename
        job["xml"] = path
        with open(path, "w") as f:
            f.write("")

        root = Element("sbs_ingest_plus")

        generator = SubElement(root, "generator")
        SubElement(generator, "generator_name").text = "Ingest Plus UI"
        SubElement(generator, "generator_id").text = ""
        SubElement(generator, "generator_version").text = "1.0"

        job_info = SubElement(root, "job_info")
        SubElement(job_info, "job_id").text = ""
        SubElement(job_info, "ingest_type").text = self.ingestTypeComboBox.currentText()
        job["ingest_type"] = self.ingestTypeComboBox.currentText()

        source_info = SubElement(job_info, "source_info")
        job["source_info"] = {}

        SubElement(
            source_info, "centralmediatypecode"
        ).text = self.centralmediatypecodeComboBox.currentText()
        job["source_info"]["centralmediatypecode"] = (
            self.centralmediatypecodeComboBox.currentText()
        )

        SubElement(source_info, "ingest_src").text = self.sourceComboBox.currentText()
        job["source_info"]["ingest_src"] = self.sourceComboBox.currentText()

        folder_Id = ""
        folder_name = self.folderComboBox.currentText()
        folder_path = ""

        if folder_name == "News":
            folder_Id = str(20070)
            folder_path = "전체\\News"
            # for folder in target_list[self.centralmediatypecodeComboBox.currentText()]:
            #     if folder["KsimTree"]["Name"] == weekday_name:
            #         folder_Id = str(folder["KsimTree"]["Id"])
            #         folder_path = folder["KsimTree"]["Path"]
        else:
            for folder in target_list[self.centralmediatypecodeComboBox.currentText()]:
                if folder["KsimTree"]["Name"] == folder_name:
                    folder_Id = str(folder["KsimTree"]["Id"])
                    folder_path = folder["KsimTree"]["Path"]

        folder = SubElement(source_info, "folder")
        SubElement(folder, "folder_name").text = folder_name
        SubElement(folder, "folder_path").text = folder_path
        SubElement(folder, "folder_id").text = folder_Id
        job["source_info"]["folder"] = {}
        job["source_info"]["folder"]["folder_name"] = folder_name
        job["source_info"]["folder"]["folder_path"] = folder_path
        job["source_info"]["folder"]["folder_Id"] = folder_Id

        event_Id = ""
        event_name = "미분류"
        event_path = ""
        for event in event_list:
            if event["KsimTree"]["Name"] == event_name:
                event_Id = str(event["KsimTree"]["Id"])
                event_path = event["KsimTree"]["Path"]
        event = SubElement(source_info, "event")
        SubElement(event, "event_name").text = event_name
        SubElement(event, "event_path").text = event_path
        SubElement(event, "event_id").text = event_Id
        job["source_info"]["event"] = {}
        job["source_info"]["event"]["event_name"] = event_name
        job["source_info"]["event"]["event_path"] = event_path
        job["source_info"]["event"]["event_id"] = event_Id

        category3 = self.categoryComboBox3.currentText()
        category2 = self.categoryComboBox2.currentText()
        category1 = self.categoryComboBox1.currentText()

        category_name = ""
        category_path = ""
        category_Id = ""
        job["source_info"]["category"] = {}
        if category3 != "":
            for temp_cat_1 in category1_list:
                if temp_cat_1["KsimTree"]["Name"] == category1:
                    job["source_info"]["category"]["category1"] = temp_cat_1[
                        "KsimTree"
                    ]["Name"]
                    temp_cat_2_list = temp_cat_1["ChildNodes"]
                    for temp_cat_2 in temp_cat_2_list:
                        if temp_cat_2["KsimTree"]["Name"] == category2:
                            job["source_info"]["category"]["category2"] = temp_cat_2[
                                "KsimTree"
                            ]["Name"]
                            temp_cat_3_list = temp_cat_2["ChildNodes"]
                            for temp_cat_3 in temp_cat_3_list:
                                if temp_cat_3["KsimTree"]["Name"] == category3:
                                    category_name = temp_cat_3["KsimTree"]["Name"]
                                    category_path = temp_cat_3["KsimTree"]["Path"]
                                    category_Id = str(temp_cat_3["KsimTree"]["Id"])
                                    job["source_info"]["category"]["category3"] = (
                                        category_name
                                    )

        elif category2 != "":
            for temp_cat_1 in category1_list:
                if temp_cat_1["KsimTree"]["Name"] == category1:
                    job["source_info"]["category"]["category1"] = temp_cat_1[
                        "KsimTree"
                    ]["Name"]
                    temp_cat_2_list = temp_cat_1["ChildNodes"]
                    for temp_cat_2 in temp_cat_2_list:
                        if temp_cat_2["KsimTree"]["Name"] == category2:
                            job["source_info"]["category"]["category2"] = temp_cat_2[
                                "KsimTree"
                            ]["Name"]
                            category_name = temp_cat_2["KsimTree"]["Name"]
                            category_path = temp_cat_2["KsimTree"]["Path"]
                            category_Id = str(temp_cat_2["KsimTree"]["Id"])
                            job["source_info"]["category"]["category3"] = ""
        elif category1 != "":
            for temp_cat_1 in category1_list:
                if temp_cat_1["KsimTree"]["Name"] == category1:
                    job["source_info"]["category"]["category1"] = temp_cat_1[
                        "KsimTree"
                    ]["Name"]
                    category_name = temp_cat_1["KsimTree"]["Name"]
                    category_path = temp_cat_1["KsimTree"]["Path"]
                    category_Id = str(temp_cat_1["KsimTree"]["Id"])
                    job["source_info"]["category"]["category2"] = ""
                    job["source_info"]["category"]["category3"] = ""
        else:
            category_name = ""
            category_path = ""
            category_Id = ""
            job["source_info"]["category"]["category1"] = ""
            job["source_info"]["category"]["category2"] = ""
            job["source_info"]["category"]["category3"] = ""

        category = SubElement(source_info, "category")
        SubElement(category, "category_name").text = category_name
        SubElement(category, "category_path").text = category_path
        SubElement(category, "category_id").text = category_Id

        job["source_info"]["category"]["category_name"] = category_name
        job["source_info"]["category"]["category_path"] = category_path
        job["source_info"]["category"]["category_id"] = category_Id

        SubElement(
            source_info, "restriction"
        ).text = self.restrictionComboBox.currentText()
        job["source_info"]["restriction"] = self.restrictionComboBox.currentText()

        job["metadata"] = {}
        metadata = SubElement(job_info, "metadata")

        title = self.titleLineEdit.text()
        i = 0
        while title in titles:
            try:
                title = (
                    "-".join(title.split("-")[0:-1])
                    + "-"
                    + str(int(title.split("-")[-1]) + 1)
                )
            except:  # noqa: E722
                title = title + "-1"
            i = i + 1

        SubElement(metadata, "title").text = title
        job["metadata"]["title"] = title
        self.titleLineEdit.setText(title)

        dest_info = SubElement(job_info, "dest_info")
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
        SubElement(dest_info, "dest_filename").text = f"IngestPlus_{sanitized_title}"
        job["dest_info"] = {}
        job["dest_info"]["dest_filename"] = f"IngestPlus_{sanitized_title}"

        SubElement(metadata, "contents").text = self.contentTextEdit.toPlainText()
        job["metadata"]["contents"] = self.contentTextEdit.toPlainText()

        sub_metadata = SubElement(metadata, "sub_metadata")
        job["metadata"]["sub_metadata"] = {}

        SubElement(sub_metadata, "interviewdept").text = self.deptLineEdit.text()
        job["metadata"]["sub_metadata"]["interviewdept"] = self.deptLineEdit.text()

        SubElement(
            sub_metadata, "interviewrepoter"
        ).text = self.interviewrepoterLineEdit.text()
        job["metadata"]["sub_metadata"]["interviewrepoter"] = (
            self.interviewrepoterLineEdit.text()
        )

        SubElement(sub_metadata, "mediarepoter").text = self.mediarepoterLineEdit.text()
        job["metadata"]["sub_metadata"]["mediarepoter"] = (
            self.mediarepoterLineEdit.text()
        )

        SubElement(
            sub_metadata, "shootingplace"
        ).text = self.shootingplaceLineEdit.text()
        job["metadata"]["sub_metadata"]["shootingplace"] = (
            self.shootingplaceLineEdit.text()
        )

        SubElement(sub_metadata, "shootingdate").text = datetime.datetime.strptime(
            self.videoDateWidget.selectedDate().toString(Qt.ISODate), "%Y-%m-%d"
        ).strftime("%Y-%m-%d")
        job["metadata"]["sub_metadata"]["shootingdate"] = datetime.datetime.strptime(
            self.videoDateWidget.selectedDate().toString(Qt.ISODate), "%Y-%m-%d"
        ).strftime("%Y-%m-%d")

        file_list = SubElement(job_info, "file_list")
        job["files"] = {}
        for i in range(self.fileListWidget.count()):
            file = SubElement(file_list, "file")
            SubElement(file, "order").text = str(i)
            SubElement(file, "full_path").text = self.fileListWidget.item(i).text()
            job["files"][str(i)] = self.fileListWidget.item(i).text()

        tree = ElementTree(root)
        tree.write(path, encoding="utf-8", xml_declaration=True)

        job["ingest_status"] = "대기"
        job["ftp_status"] = ""

        while len(self.job_list) > 30:
            self.job_list.pop(0)
            self.root.takeChild(0)
            break
        item = QTreeWidgetItem()
        item.setText(0, job["metadata"]["title"])
        item.setText(1, job["ingest_status"])
        item.setText(2, job["ftp_status"])
        self.job_list.append(job)
        self.root.addChild(item)

        with open("work/jobs.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.job_list))

        QMessageBox.information(self, "XML 생성 완료", "XML 생성을 완료하였습니다.")

    @tback
    def item_up(self):
        current_row: int = self.fileListWidget.currentRow()
        current_item: QListWidgetItem = self.fileListWidget.takeItem(current_row)
        self.fileListWidget.insertItem(current_row - 1, current_item)
        self.fileListWidget.setCurrentRow(current_row - 1)
        self.items.clear()
        for x in range(self.fileListWidget.count()):
            self.items.append(self.fileListWidget.item(x).text())

    @tback
    def item_down(self):
        current_row: int = self.fileListWidget.currentRow()
        current_item: QListWidgetItem = self.fileListWidget.takeItem(current_row)
        self.fileListWidget.insertItem(current_row + 1, current_item)
        self.fileListWidget.setCurrentRow(current_row + 1)
        self.items.clear()
        for x in range(self.fileListWidget.count()):
            self.items.append(self.fileListWidget.item(x).text())

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
        temp_items = []
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path: str = url.toLocalFile().replace("/", "\\")
                temp_items.append(path)
            event.accept()
        else:
            event.ignore()
        self.items.clear()
        x_range = range(self.fileListWidget.count())
        for x in x_range:
            self.items.append(self.fileListWidget.item(x).text())

        new_items = self.items + sort(temp_items)
        self.items = new_items

        self.fileListWidget.clear()
        for item in self.items:
            self.fileListWidget.addItem(QListWidgetItem(item))

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.listen_status_thread.stop()
        self.listen_status_thread.terminate()
        self.listen_status_thread.wait()
        super().closeEvent(a0)


blacklist_exts = [
    "xml",
    "bdm",
    "mpl",
    "bin",
    "ind",
    "ds_store",
    "cpi",
    "bat",
    "txt",
    "smi",
    "ese",
    "ctg",
    "ppn",
    "bim",
    "sav",
    "url",
    "db",
    "htm",
    "js",
    "log",
    "css",
    "lwi",
    "ffindex",
    "idx",
    "zip",
    "exe",
    "hwp",
    "ppt",
    "pptx",
    "doc",
    "docx",
    "dll",
    "html",
    "lua",
    "vhdx",
    "ico",
    "cs",
    "csproj",
    "pdf",
    "cpf",
]


@tback_args
def sort(target_list):
    return_list = []
    is_gopro: bool = False
    if len(target_list) == 0:
        return []
    # first_item: str = target_list[0]
    for item in os_sorted(target_list):
        new_list = []
        if ("CLIPINF" in item.upper()) or ("THMBNL" in item.upper()):
            return []
        if os.path.isdir(item):
            target_list = [os.path.join(item, f) for f in os.listdir(item)]
        try:
            if item.split("\\")[-1] == "100GOPRO" or item.split("\\")[-2] == "100GOPRO":
                is_gopro = True
        except:  # noqa: E722
            pass

        if is_gopro:
            target_list = [f for f in target_list if f.split(".")[-1].lower() == "mp4"]
            gopro_dict = {}
            for item in target_list:
                gopro_dict[item[:-4]] = []
            for item in target_list:
                gopro_dict[item[:-4]].append(item)
            for key, value in gopro_dict.items():
                gopro_dict[key].sort(key=lambda x: x.split("\\")[-1].split(".")[0][:-4])
                for item in gopro_dict[key]:
                    new_list.append(item)
        else:
            if not os.path.isdir(item):
                if item.lower().split(".")[-1] not in blacklist_exts:
                    new_list.append(item)
            else:
                targets = [os.path.join(item, f) for f in os.listdir(item)]
                for target in targets:
                    new_list += sort([target])
        return_list = return_list + [os.path.normpath(x) for x in new_list]
    return return_list


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
