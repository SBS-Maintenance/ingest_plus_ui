import sys
import os

import pymediainfo
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QMessageBox, QTreeView, QTreeWidget, QTreeWidgetItem
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import Qt, QEvent, QThread, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import struct
import socket
import select

from xml.etree.ElementTree import Element, SubElement, ElementTree

import datetime

import configparser

import threading

import json

from natsort import natsorted

config = configparser.ConfigParser()
config.read("config.ini")


STATUS_PORT = config["ports"]["status"]
STATUS_SOCKET = socket.socket(
    family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
STATUS_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
STATUS_SOCKET.bind(("", int(STATUS_PORT)))
mreq = struct.pack("4sl", socket.inet_aton(
    "224.1.1.1"), socket.INADDR_ANY)
STATUS_SOCKET.setsockopt(
    socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

FAILURE_PORT = config["ports"]["failure"]
FAILURE_SOCKET = socket.socket(
    family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
FAILURE_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
FAILURE_SOCKET.bind(("", int(FAILURE_PORT)))
FAILURE_SOCKET.setsockopt(
    socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
form_class = uic.loadUiType(BASE_DIR + r'\\window.ui')[0]
folderDict = {"원본-디지털": ["D_EditDone", "D_CLN", "Download", "Partial Download", "InComing"],
              "취재원본 (보도국)": ["News"]}
categoryDict = {"취재원본 (보도국)": {"정치": {"": [""],
                                      "국방": ["", "공군", "국방부", "남북대치", "방위산업",
                                             "병무", "예비군", "육군", "종합훈련", "주한미군", "특수부대", "파병", "학군단", "해군"],
                                      "국회": ["", "국회기관", "본회의", "상임위원회", "대표회담", "국회의원", "국정감사", "청문회", "토론회"],
                                      "선거": ["", "국회의원", "대통령", "선거관리위원회", "지방자치단체"],
                                      "외교": ["", "교민이민", "외교부", "재외공관", "주한공관", "회담"],
                                      "정당": ["", "군소정당", "여당", "야당"],
                                      "지방자치단체": ["", "서울특별시", "광역시", "경기도", "강원도", "충청도", "전라도", "경상도", "제주도", "이북5도", "세종시"],
                                      "청와대": ["", "청와대외경", "정상회담", "영수회담", "집무기자회견담화", "오찬만찬", "회의및행사", "수석", "접견및수여식", "업무보고", "가족행사", "현장방문", "해외순방"],
                                      "용산대통령실": ["", "용산대통령실외견", "정상회담", "영수회담", "집무기자회견담화", "오찬만찬", "회의및행사", "수석", "접견및수여식", "업무보고", "가족행사", "현장방문", "해외순방"],
                                      "행정": ["", "관계기관", "국무총리", "정부청사", "정부청사(세종)", "정부청사(대전)", "정부청사(중앙)"]
                                      },
                               "경제": {"": [""],
                                      "1차금융": ["", "기관", "시중은행", "한국은행", "화폐 통화 환율"],
                                      "2차금융": ["", "개인신용", "대부업", "보험", "신용카드", "제2금융", "증권"],
                                      "건설": ["", "교량 터널 도로", "아파트 빌딩", "재개발 택지개발"],
                                      "경제사건": [""],
                                      "경제편집완본": [""],
                                      "기업": ["", "경제단체", "공기업", "외국기업", "대기업", "중소기업"],
                                      "농림수산": ["", "광업", "농업", "어업", "임업", "축산업"],
                                      "무역": ["", "물류기지", "수,출입", "통관,세관"],
                                      "부동산": ["", "건물", "분양", "아파트", "임야", "주택가", "부동산거래"],
                                      "서비스업": ["", "숙박업소", "유흥업", "요식업", "임대,리스업", "이사,택배"],
                                      "에너지": ["", "가스", "대체에너지", "석유", "수력", "연탄", "원자력", "전기", "주유소", "풍력", "태양광"],
                                      "유통": ["", "경매", "귀금속", "노점", "농수산물시장", "백화점", "도소매업", "쇼핑몰", "재래시장", "전자상가", "편의점", "마트", "온라인쇼핑"],
                                      "자동차": ["", "렌터카", "생산라인", "영업소", "정비", "중고차", "폐차", "수입차"],
                                      "전기전자": ["", "가전", "반도체", "컴퓨터", "휴대폰"],
                                      "제조업": ["", "공단 공장", "식음료", "조선", "주류", "철강", "화학", "섬유", "생활용품"],
                                      },
                               "사회": {"": [""],
                                      "경찰소방서": ["", "경찰청", "경찰서", "단속검문", "소방서", "치안", "해양경찰"],
                                      "공항항만": ["", "김포공항", "선박", "인천공항", "지방공항", "항공사", "항만시설"],
                                      "교육": ["", "고등학교", "교육기관", "대학교", "온라인교육", "영유아교육", "입시", "중학교", "초등학교", "특수학교", "학원", "학교폭력", "사교육"],
                                      "교통운수": ["", "고속도로", "기차", "버스", "승용차", "도로", "이륜차", "지하철", "택시", "트럭", "교통일반", "운전면허"],
                                      "노동": ["", "노동단체", "시민단체", "시위", "고용", "노사문제"],
                                      "법조": ["", "검사", "검찰", "교도소", "법원", "변호사", "사법연수원", "판사", "헌법재판소"],
                                      "복지": ["", "노동자", "노숙자", "노인", "미혼모", "복지기관", "입양", "장묘시설", "장애인", "취약계층"],
                                      "사건사고": ["", "교통사고", "성범죄", "부정부패", "폭력", "화재", "인명사고", "사기,절도", "안전사고", "사이버범죄"],
                                      "사람들": ["", "여성", "인물", "직장인", "은퇴자", "청소년"],
                                      "사회편집완본": [""],
                                      "외국인": ["", "관광객", "다문화가정", "불법체류", "외국인노동자", "외국인범죄"],
                                      "유해환경": ["", "대기오염", "도박", "마약", "방역", "소음", "수질오염", "유흥업소", "토양오염", "중금속오염", "폐기물"],
                                      "자연환경": ["", "강", "갯벌", "남극북극", "늪지", "동식물", "산", "섬", "시가지", "전원", "해양"]
                                      },
                               "문화과학": {"": [""],
                                        "과학통신": ["", "교육기관", "기술과학", "연구기관", "우주개발", "첨단과학", "통신"],
                                        "날씨풍경": ["", "봄", "여름", "가을", "겨울", "기상청", "자연재해"],
                                        "문화과학사건": [""],
                                        "문화과학편집완본": [""],
                                        "미디어": ["", "광고", "방송사(지상파)", "신문사", "케이블", "홈쇼핑"],
                                        "예술": ["", "무용", "뮤지컬", "문학", "미술", "연극", "영화", "음악", "패션", "연예"],
                                        "유적역사전통": ["", "공원", "기념물", "명승고적", "멍절", "박물관", "유적지", "전통문화"],
                                        "인터넷": [""],
                                        "의료건강": ["", "기관", "병원", "보건소", "생명공학", "약국", "웰빙", "음주", "질병", "흡연"],
                                        "종교": ["", "기독교", "기타종교", "불교", "사이비종교", "천주교"],
                                        "취미레저": ["", "경기장", "공연장", "극장가", "복권", "여행", "운동", "음반서점", "오락"]
                                        },
                               "스포츠": {"": [""],
                                       "골프": ["", "KPGA", "KLPGA", "PGA", "LPGA", "올림픽", "아시안게임", "아마추어골프", "기타골프"],
                                       "농구": ["", "남자프로농구", "여자프로농구", "NBA", "농구대표팀", "올림픽", "아시안게임", "아마추어농구", "기타농구"],
                                       "이벤트": ["", "런던올림픽"],
                                       "배구": ["", "냄자프로배구", "여자프로배구", "해외배구", "올림픽", "아시안게임", "아마추어배구", "기타배구"],
                                       "스포츠사건사고": [""],
                                       "스포츠편집완본": [""],
                                       "야구": ["", "프로야구", "메이저리그", "일본야구", "올림픽", "아시안게임", "WBC", "아마추어야구", "기타야구"],
                                       "종합": ["", "국내종합경기", "국제종합경기", "하계올림픽", "동계올림픽", "패럴림픽", "아시안게임", "동계스포츠", "모터스포츠", "E스포츠", "걱투기", "보드게임", "사회체육", "기관단체행정", "스포츠시설", "스포츠행사", "체육인", "기타스포츠"],
                                       "축구": ["", "프로축구", "해외축구", "남자국가대표축구", "여자국가대표축구", "올림픽", "아시안게임", "월드컵", "아마추어축구", "기타축구"]
                                       },
                               "국제": {"": [""],
                                      "국제편집완본": [""],
                                      "기구회담": ["", "UN회의", "국제회의"],
                                      "기후질병": ["", "환경오염", "기상이변", "질병"],
                                      "남미": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "미국": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "북중미": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "분쟁": ["", "영토분쟁", "인종분쟁", "종교분쟁"],
                                      "아시아": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "아프리카": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "오세아니아": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "유럽": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "일본": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "중동": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"],
                                      "중국": ["", "경제", "군사", "문화과학", "사건사고", "자연재해", "정치"]
                                      },
                               "북한": {"": [""],
                                      "경제": ["", "경제일반", "경제협력", "공업", "광업", "농림축수산", "유통", "토목건설"],
                                      "군사": ["", "국경", "군사일반", "미사일", "핵시설"],
                                      "문화": ["", "공연예술", "남북교류", "보도", "북한유적", "북한풍속"],
                                      "북한편집완본": [""],
                                      "사회": ["", "북한도시", "주민시설", "교육"],
                                      "정치": ["", "김정일", "김정은", "인물", "정치일반", "회의대화"],
                                      "통일": ["", "수용소", "이산가족", "일반", "탈북", "한국전쟁", "회담"]
                                      },
                               "뉴스": {"": [""],
                                      "아침뉴스": [""],
                                      "오전 뉴스": [""],
                                      "오후뉴스": [""],
                                      "저녁뉴스": [""],
                                      "8뉴스뉴스": [""],
                                      "마감뉴스": [""],
                                      "스포츠뉴스": [""],
                                      "속보특보": [""],
                                      "기타": [""],
                                      },
                               "기타": {"": [""]},
                               "미분류": {"": [""]},
                               "스브스뉴스": {"": [""]},
                               "상용": {"": [""]},
                               },
                "원본-디지털": {"": {"": [""]}}
                }


class Model(QStandardItemModel):
    def __init__(self, data):
        QStandardItemModel.__init__(self)

        for j, _subject in enumerate(data):
            item = QStandardItem(_subject["upper"])
            for k, mid in enumerate(_subject["mid"]):
                item2 = QStandardItem(mid["mid"])
                item.setChild(k, 0, item2)
                if "low" in mid.keys():
                    for l, low in enumerate(mid["low"]):
                        child2 = QStandardItem(low)
                        item2.setChild(l, 0, child2)
            self.setItem(j, 0, item)


class ListenThread(QThread):
    received = pyqtSignal(object)

    def __init__(self, parent, socket):
        QThread.__init__(self, parent)
        self.socket = socket

    def run(self):
        with STATUS_SOCKET:
            while True:
                reti, retw, rete = select.select([self.socket], [], [])
                msg, addr = self.socket.recvfrom(1024)
                self.received.emit(msg.decode())


class MyApp(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_ui()
        self.show()
        self.items = []
        self.failure_list = []

        self.listen_status_thread = ListenThread(self, STATUS_SOCKET)
        self.listen_status_thread.received.connect(self.on_status_received)
        self.listen_status_thread.start()

        self.listen_failure_thread = ListenThread(self, FAILURE_SOCKET)
        self.listen_failure_thread.received.connect(self.on_failure_received)
        self.listen_failure_thread.start()

    def on_status_received(self, msg):
        recv = json.loads(msg)
        print(recv)
        recv_str = ""
        for k in recv:
            recv_str = recv_str+f"{k}:{recv[k]}\n"
        self.statusPlainTextEdit.setPlainText(recv_str)

    def on_failure_received(self, msg):
        print(msg)

    def init_ui(self):
        self.ingestTypeComboBox.addItem("Consolidation")
        self.ingestTypeComboBox.addItem("Normal")

        self.subjectComboBox.addItem("취재원본 (보도국)")
        self.subjectComboBox.addItem("원본-디지털")
        self.subjectComboBox.currentIndexChanged.connect(self.subjectChanged)

        for folder in folderDict["취재원본 (보도국)"]:
            self.folderComboBox.addItem(folder)

        for category1 in categoryDict["취재원본 (보도국)"].keys():
            self.categoryComboBox1.addItem(category1)

        for category2 in categoryDict["취재원본 (보도국)"]["정치"].keys():
            self.categoryComboBox2.addItem(category2)

        self.categoryComboBox1.currentIndexChanged.connect(
            self.category1changed)

        self.categoryComboBox2.currentIndexChanged.connect(
            self.category2changed)

        self.contentTextEdit.setAcceptDrops(False)

        self.sourceComboBox.addItem("VCR")
        self.sourceComboBox.addItem("GRAPHIC")
        self.sourceComboBox.addItem("RSW")
        self.sourceComboBox.addItem("CAP")
        self.sourceComboBox.addItem("XDCAM")
        self.sourceComboBox.addItem("TH")
        self.sourceComboBox.addItem("WEB")
        self.sourceComboBox.addItem("6mm(HDV)")

        self.restrictionComboBox.addItem("보도제작")
        self.restrictionComboBox.addItem("보도본부")
        self.restrictionComboBox.addItem("스포츠")
        self.restrictionComboBox.addItem("전체")
        self.restrictionComboBox.addItem("보도")

        self.fileListWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)

        self.setAcceptDrops(True)

        self.upButton.clicked.connect(self.item_up)
        self.downButton.clicked.connect(self.item_down)

        self.xmlCreateButton.clicked.connect(self.create_xml)

        self.deleteButton.clicked.connect(self.delete_item)
        self.resetButton.clicked.connect(self.reset_list)

        self.failureTreeWidget.setColumnCount(3)
        self.failureTreeWidget.setHeaderLabels(["제목", "인제스트실패", "전송실패"])
        self.failureTreeWidget.setColumnWidth(1, 120)
        self.failureTreeWidget.setColumnWidth(2, 100)
        self.failureTreeWidget.setColumnWidth(0, 310)
        self.root = self.failureTreeWidget.invisibleRootItem()

    def subjectChanged(self):
        self.categoryComboBox1.clear()
        self.categoryComboBox2.clear()
        self.categoryComboBox3.clear()
        self.folderComboBox.clear()
        for folder in folderDict[self.subjectComboBox.currentText()]:
            self.folderComboBox.addItem(folder)
        for category1 in categoryDict[self.subjectComboBox.currentText()].keys():
            self.categoryComboBox1.addItem(category1)

    def category1changed(self):
        if self.categoryComboBox1.currentText() == "":
            return

        self.categoryComboBox2.clear()
        for category2 in categoryDict[self.subjectComboBox.currentText()][self.categoryComboBox1.currentText()].keys():
            self.categoryComboBox2.addItem(category2)

    def category2changed(self):
        self.categoryComboBox3.clear()
        for category3 in categoryDict[self.subjectComboBox.currentText()][self.categoryComboBox1.currentText()][self.categoryComboBox2.currentText()]:
            self.categoryComboBox3.addItem(category3)

    def reset_list(self):
        self.items = []
        self.fileListWidget.clear()

    def delete_item(self):
        listItems = self.fileListWidget.selectedItems()
        if not listItems:
            return
        for item in listItems:
            self.fileListWidget.takeItem(self.fileListWidget.row(item))
        self.items = []
        for x in range(self.fileListWidget.count()):
            self.items.append(self.fileListWidget.item(x).text())

    def create_xml(self):
        filename = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")+".xml"
        path = config["xml"]["dir"]+"//"+filename
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
        SubElement(source_info, "folder").text = "News"
        SubElement(source_info, "event").text = "미분류"
        SubElement(
            source_info, "ingest_src").text = self.sourceComboBox.currentText()
        SubElement(
            source_info, "category1").text = self.categoryComboBox1.currentText()
        SubElement(
            source_info, "category2").text = self.categoryComboBox2.currentText()
        SubElement(
            source_info, "category3").text = self.categoryComboBox3.currentText()
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
        self.items = []
        for x in range(self.fileListWidget.count()):
            self.items.append(self.fileListWidget.item(x).text())

    def item_down(self):
        currentRow = self.fileListWidget.currentRow()
        currentItem = self.fileListWidget.takeItem(currentRow)
        self.fileListWidget.insertItem(currentRow + 1, currentItem)
        self.fileListWidget.setCurrentRow(currentRow+1)
        self.items = []
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
                path = url.toLocalFile().replace("/", "\\")
                temp_items.append(path)
            event.accept()
        else:
            event.ignore()

        self.items = self.items+sort(temp_items)

        self.fileListWidget.clear()
        for item in self.items:
            self.fileListWidget.addItem(QListWidgetItem(item))


def sort(targetList):
    isGopro = False
    if (len(targetList) == 0):
        return []

    firstItem = targetList[0]
    if (os.path.isdir(firstItem)):
        targetList = [os.path.join(firstItem, f) for f in os.listdir(
            firstItem)]
    try:
        if (firstItem.split("\\")[-1] == "100GOPRO" or firstItem.split("\\")[-2] == "100GOPRO"):
            isGopro = True
    except:
        pass
    itemDict = {}
    if isGopro:
        targetList = [f for f in targetList if f.split(
            ".")[-1].lower() == "mp4"]
        gopro_dict = {}
        for item in targetList:
            gopro_dict[item[-7:-4]] = []
        for item in targetList:
            gopro_dict[item[-7:-4]].append(item)
        targetList = []
        for key, value in gopro_dict.items():
            gopro_dict[key].sort(key=lambda x: x.split(
                "\\")[-1].split(".")[0][:-4])
            for item in gopro_dict[key]:
                targetList.append(item)
    else:
        for item in targetList:
            itemDict[item.split("\\")[-1]] = item
        targetList = []
        for key in (natsorted(itemDict.keys())):
            if (os.path.isdir(itemDict[key])):
                inside = []
                try:
                    inside = os.listdir(itemDict[key])
                except:
                    pass
                full_inside = []
                for item in inside:
                    full_inside.append(os.path.join(itemDict[key], item))
                print(full_inside)
                targetList = targetList+sort(full_inside)
            else:
                targetList.append(itemDict[key])

    return targetList


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
