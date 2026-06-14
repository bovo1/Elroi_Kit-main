stylesheet = """
QMainWindow{
    background-color: rgb(39, 38, 39);
}

QWidget{
    background-color: rgb(39, 38, 39);
}

QPushButton {
    background-color: transparent;
}

QPushButton:hover {
    background-color: rgb(16, 97, 150);
}

QPushButton:pressed {
    background-color: rgb(16, 97, 150);
}

QLabel{
    font: 14px;
    color : white;
}
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from constants.constants import QT_MAX_SIZE

class Top_MainWindow_Form(QtWidgets.QMainWindow):
    """윈도우 타이틀을 대신하기 위해 만든 클래스이다.
    """
    def __init__(self, Sync, lang):
        super().__init__()
        self.init(Sync, lang)        
        self.init_Ui_main(self)
        self.init_Function(self)
        self.setup_Ui_Main(self)

        self.statusBar().setVisible(False)
        self.setMouseTracking(True)

        if __name__ == "__main__":
            self.show()

    def init(self, Sync, lang):
        """초기 선언 시 변수 선언문이다.
                Parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스
        """
        self.lang = lang
        self.main_top_to_merge_signal = Sync.main_top_to_merge_signal
        self.main_merge_to_top_signal = Sync.main_merge_to_top_signal
        self.main_merge_to_top_signal.connect(self.recv_top_from_merge)

        self.window_height = 30
        self.click_sw = False
        self.dragPos = None


    def init_Ui_main(self, top_MainWindow):
        """윈도우 타이틀 UI 생성을 위한 초기 선언문이다.
                Parameters
                1.   top_MainWindow(object): PyQt widget object
        """
        top_MainWindow.setObjectName("top_MainWindow")
        top_MainWindow.resize(800, self.window_height)

        self.top_MainWindow_centralwidget = QtWidgets.QWidget(top_MainWindow)
        self.top_MainWindow_centralwidget.setObjectName("top_MainWindow_centralwidget")

        self.top_MainWindow_centralwidget_horizontalLayout = QtWidgets.QHBoxLayout(self.top_MainWindow_centralwidget)
        self.top_MainWindow_centralwidget_horizontalLayout.setObjectName("top_MainWindow_centralwidget_horizontalLayout")

        self.blank_label = QtWidgets.QLabel()
        self.blank_label.setObjectName("blank_label")
        self.blank_label.setText("")

        self.blank_label2 = QtWidgets.QLabel()
        self.blank_label2.setObjectName("blank_label")
        self.blank_label2.setText("")

        self.blank_label3 = QtWidgets.QLabel()
        self.blank_label3.setObjectName("blank_label")
        self.blank_label3.setText("")

        self.company_logo_label = QtWidgets.QLabel()
        self.company_logo_label.setObjectName("company_logo_label")
        self.logo_background = QtGui.QPixmap("ico/labeling/title/logo_3.png")
        self.company_logo_label.setPixmap(self.logo_background)

        self.company_name_label = QtWidgets.QLabel()
        self.company_name_label.setObjectName("company_name_label")

        self.minimize_button = QtWidgets.QPushButton()
        self.minimize_button.setObjectName("minimize_button")
        self.minimize_button_icon= QtGui.QIcon()
        self.minimize_button_icon.addPixmap(QtGui.QPixmap("ico/labeling/title/window_minimize.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.minimize_button.setIcon(self.minimize_button_icon)

        self.resizable_button = QtWidgets.QPushButton()
        self.resizable_button.setObjectName("resizable_button")
        self.maximize_button_icon= QtGui.QIcon()
        self.maximize_button_icon.addPixmap(QtGui.QPixmap("ico/labeling/title/window_maximize.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.nomalize_button_icon= QtGui.QIcon()
        self.nomalize_button_icon.addPixmap(QtGui.QPixmap("ico/labeling/title/window_nomal.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.resizable_button.setIcon(self.maximize_button_icon)

        self.close_button = QtWidgets.QPushButton()
        self.close_button.setObjectName("close_button")
        close_button_icon= QtGui.QIcon()
        close_button_icon.addPixmap(QtGui.QPixmap("ico/labeling/title/window_close.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.close_button.setIcon(close_button_icon)

        top_MainWindow.setCentralWidget(self.top_MainWindow_centralwidget)

        QtCore.QMetaObject.connectSlotsByName(top_MainWindow)


    def setup_Ui_Main(self, top_MainWindow):
        """초기화된 ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
                Parameters
                1.   top_MainWindow(object): PyQt widget object
        """
        self.lang.set("main", "top", "company_name_label", self.company_name_label)
        self.top_MainWindow_centralwidget_horizontalLayout.setContentsMargins(6, 0, 6, 0)
        
        top_MainWindow.setMinimumSize(QtCore.QSize(0, self.window_height))
        top_MainWindow.setMaximumSize(QtCore.QSize(QT_MAX_SIZE, self.window_height))
        self.top_MainWindow_centralwidget.setMinimumSize(QtCore.QSize(0, self.window_height))
        self.top_MainWindow_centralwidget.setMaximumSize(QtCore.QSize(QT_MAX_SIZE, self.window_height))

        self.top_MainWindow_centralwidget_horizontalLayout.addWidget(self.blank_label)
        self.top_MainWindow_centralwidget_horizontalLayout.addWidget(self.blank_label2)
        self.top_MainWindow_centralwidget_horizontalLayout.addWidget(self.blank_label3)
        self.top_MainWindow_centralwidget_horizontalLayout.addStretch()
        self.top_MainWindow_centralwidget_horizontalLayout.addWidget(self.company_name_label)
        # self.top_MainWindow_centralwidget_horizontalLayout.addWidget(self.company_logo_label)
        self.top_MainWindow_centralwidget_horizontalLayout.addStretch()
        self.top_MainWindow_centralwidget_horizontalLayout.addWidget(self.minimize_button)
        self.top_MainWindow_centralwidget_horizontalLayout.addWidget(self.resizable_button)
        self.top_MainWindow_centralwidget_horizontalLayout.addWidget(self.close_button)

    def init_Function(self, _):
        """윈도우 타이틀에 존재하는 기능들에 대한 connect 함수를 정의한다.
        """
        self.minimize_button.clicked.connect(lambda : self.custom_event(mode="min"))
        self.resizable_button.clicked.connect(lambda : self.custom_event(mode="resize"))
        self.close_button.clicked.connect(lambda: self.custom_event(mode="close"))

    def custom_event(self, mode=None):
        """
            @description: 윈도우 타이틀 기능 동작에 대한 아이콘 변경 및 상태를 merge mainwindow에 전달하는 함수이다.
            @author: MyoungHwan
            @Parameters
                1.  mode(str)
                    - min : 윈도우 최소화
                    - resize : 윈도우 최대화, 표준사이즈로 resize
                    - close : 닫기
            @history
                1. Modified by MyoungHwan (2024.10.23): Elroikit 종료 관련 코드수정
        """
        tmp_dict = {}
        tmp_dict['mode'] = mode
        self.main_top_to_merge_signal.emit(tmp_dict)

        if self.isMaximized():
            self.resizable_button.setIcon(self.nomalize_button_icon)
        else:
            self.resizable_button.setIcon(self.maximize_button_icon)

    def mouseDoubleClickEvent(self, _):
        """윈도우 타이틀을 두번 클릭했을 때 발동하는 함수이다. merge mainwindow에 상태를 전달한다.
        """
        tmp_dict = {}
        tmp_dict['mode'] = "resize"
        self.main_top_to_merge_signal.emit(tmp_dict)

    def mousePressEvent(self, e):
        """윈도우 타이틀을 클릭했을 때 발동하는 함수이다. merge mainwindow에 상태를 전달한다.
        """
        if e.buttons() == QtCore.Qt.LeftButton:
            self.click_sw = True
            tmp_dict = {}
            tmp_dict['mode'] = "move"
            tmp_dict['bool'] = True
            tmp_dict['offset'] = e.globalPos()
            self.main_top_to_merge_signal.emit(tmp_dict)

    def mouseReleaseEvent(self, e):
        """윈도우 타이틀을 클릭후 뗏을 때 발동하는 함수이다. merge mainwindow에 상태를 전달한다.
        """
        self.click_sw = False
        tmp_dict = {}
        tmp_dict['mode'] = "move"
        tmp_dict['bool'] = False
        tmp_dict['offset'] = e.globalPos()
        self.main_top_to_merge_signal.emit(tmp_dict)


    @QtCore.pyqtSlot(dict)
    def recv_top_from_merge(self,output):
        """윈도우 타이틀 기능 동작에 대한 아이콘 변경 및 상태를 merge mainwindow로 부터 받는 함수이다.
            Parameters
                1.  output(dict)
                    - mode(str)
                        1. max : 윈도우 최대화 또는 노멀 모드
                            - value(int)
                                - 0 : 노멀 상태, 윈도우 최대 사이즈 아이콘으로 변경
                                - 1 : 최대화 상태, 윈도우 노멀 사이즈 아이콘으로 변경
        """
        mode = output['mode']
        if mode == 'max':
            value = output['value']
            if value: # 1일때 최대화 된 상태, 노멀 아이콘으로 변경
                self.resizable_button.setIcon(self.nomalize_button_icon)
            else: # 0일때 노멀상태, 최대 아이콘으로 변경
                self.resizable_button.setIcon(self.maximize_button_icon)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    top_MainWindow = QtWidgets.QMainWindow()
    ui = Top_MainWindow_Form()
    sys.exit(app.exec_())
