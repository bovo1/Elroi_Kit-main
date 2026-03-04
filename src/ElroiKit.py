"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

stylesheet = """
QMainWindow#merge_MainWindow{
    border-style: outset;
    border-width: 1px;
    border-color: gray;
}
"""

import os
import sys
import multiprocessing
import psutil
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from top import Top_MainWindow_Form
from mid import Mid_MainWindow_Form
from utils.language import Language
from core.main_core import Main_Core
from utils.shared import shared_root_path, license_path, temp_path, icon_path, font_path
from utils.license import make_HW_status, check_lic_status
from constants.constants import LABEL_UNSELECTED
from constants.constants import *

class main_sub_Sync(QtCore.QObject):
    """
        Main Window들간 실시간 상태 업데이트를 위한 slot/signal 클래스
    """
    ## top main window에서 merge mainwindow로 signal을 전송하기 위한 pyqt signal obejct
    main_top_to_merge_signal = QtCore.pyqtSignal(dict)

    ## merg main window에서 top mainwindow로 signal을 전송하기 위한 pyqt signal obejct
    main_merge_to_top_signal = QtCore.pyqtSignal(dict)


class Merge_MainWindow_Form(QtWidgets.QMainWindow):
    """
        Top Mainwindow와 Mid mainwindow를 호출하기 위한 Mainwindow
    """
    
    def __init__(self):
        super().__init__() 
        self.init()
        self.init_Ui_main(self)
        self.setup_Ui_Main(self)
        if __name__ == "__main__":
            self.show()
            self.showMaximized()
        
    def init(self):
        """
            @Description: merge  mainwindow ui 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
            @Author: MyoungHwan
            @History
                1. Added by MyoungHwan(2025.03.14): Added function to detect focus widget changed
                2. Added by GaEun Hwang(2025.09.29): Added label_control_dict for shortcut key
            
        """
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.lang = Language()

        self.main_sub_Sync = main_sub_Sync()
        self.main_top_to_merge_signal = self.main_sub_Sync.main_top_to_merge_signal
        self.main_top_to_merge_signal.connect(self.resize_signal)
        self.main_merge_to_top_signal = self.main_sub_Sync.main_merge_to_top_signal

        self.Main_Core = Main_Core()
        self.Sub_Core_Sync_Labeling = self.Main_Core.Sub_Core_Sync_Labeling
        self.Sub_Core_Sync_Training = self.Main_Core.Sub_Core_Sync_Training

        self.core_obj_dict = self.Main_Core.core_obj_dict
        self.label_obj_dict = self.Sub_Core_Sync_Labeling.label_obj_dict
        self.label_control_dict = self.Sub_Core_Sync_Labeling.label_control_dict
        self.sub_widget_dict = self.Sub_Core_Sync_Labeling.sub_widget_dict

        self.window_moveable = False
        self.init_resize = False
        self.resize_count = 0
        self.init_sw = True
        self.max_w = 0
        self.normal_width = 0
        self.lic_chk()
        self.timer = QTimer(self)
        self.timer.start(15 * 60 * 1000) # 30 min
        self.timer.timeout.connect(self.lic_chk)
        # Added by MyoungHwan(2025.03.14): Added function to detect focus widget changed
        QApplication.instance().focusChanged.connect(self.focus_changed)

    def focus_changed(self, _, new_widget):
        """
            @Description: focus widget 상태 저장함수
            @Author: MyoungHwan(2025.03.14)
            @Parmeters
                1.	new_widget(Qwidget): 현재 포커싱된 위젯 반환
        """
        if new_widget:
            new_widget_name = new_widget.objectName() or new_widget.__class__.__name__
        else:
            # 프로그램 외부로 진입 또는 widget에서 벗어날 경우 None 처리
            new_widget_name = "None"
        self.core_obj_dict["cur_focus_widget"] = new_widget_name


    def init_Ui_main(self, merge_MainWindow):
        """Merge UI 생성을 위한 초기 선언문이다.
                Parmeters
                1.	merge_MainWindow(object): PyQt widget object
        """
        merge_MainWindow.setObjectName("merge_MainWindow")
        merge_MainWindow.setStyleSheet(stylesheet)
        # merge_MainWindow.resize(800, 600)
        
        self.merge_MainWindow_centralwidget = QtWidgets.QWidget(merge_MainWindow)
        self.merge_MainWindow_centralwidget.setObjectName("merge_MainWindow_centralwidget")
        self.merge_MainWindow_gridLayout = QtWidgets.QGridLayout(self.merge_MainWindow_centralwidget)
        self.merge_MainWindow_gridLayout.setObjectName("merge_MainWindow_gridLayout")
        self.top_mainwindow = Top_MainWindow_Form(Sync=self.main_sub_Sync, lang=self.lang)
        self.mid_mainwindow = Mid_MainWindow_Form(Core=self.Main_Core, lang=self.lang)
        merge_MainWindow.setCentralWidget(self.merge_MainWindow_centralwidget)
        QtCore.QMetaObject.connectSlotsByName(merge_MainWindow)
        # self.mid_mainwindow.setEnabled(False)

    def setup_Ui_Main(self, merge_MainWindow):
        """초기화된 ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
                Parmeters
                1.	merge_MainWindow(object): PyQt widget object        
        """
        _translate = QtCore.QCoreApplication.translate
        merge_MainWindow.setWindowTitle(_translate("merge_MainWindow", "ElroiKit"))

        self.merge_MainWindow_gridLayout.setContentsMargins(0, 0, 0, 0)
        self.merge_MainWindow_gridLayout.setVerticalSpacing(0)
        self.merge_MainWindow_gridLayout.addWidget(self.top_mainwindow, 0, 0, 1, 1)
        self.merge_MainWindow_gridLayout.addWidget(self.mid_mainwindow, 1, 0, 1, 1)

        self.lang.apply("en")

    def center(self):
        """UI 위치를 센터에 위치하도록 배치하기 위한 함수이다.
        """
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def resizeEvent(self, _):
        """UI 사이즈를 변경하기 위한 함수이다. 초기 프로그램 실행시 화면 정중앙에 위치하도록 지정
        """
        print("merge resize event")
        tmp_main= {}
        tmp_main['mode'] = 'max'
        if self.isMaximized():
            tmp_main['value'] = 1
            self.max_w = self.width()
        else:
            tmp_main['value'] = 0
            self.normal_width = self.width()
            if self.init_resize == False:
                self.center()
                # self.showMaximized()
                self.init_resize = True
        self.main_merge_to_top_signal.emit(tmp_main)

    def mouseMoveEvent(self, e):
        """윈도우 타이틀을 클릭후 움직일때 발동하는 함수이다. 드래그 하여 UI 위치를 이동하거나 최대일 때 최소로 바꿔준다.
        """
        if e.buttons() == QtCore.Qt.LeftButton and self.window_moveable:
            if self.isMaximized(): #Not maximized
                self.showNormal()
            else:
                if self.init_sw:
                    mid_value = self.normal_width//2
                    po = QtCore.QPoint(mid_value, 10)
                    value = e.globalPos() - po
                    self.init_sw = False
                else:
                    value = self.pos() + e.globalPos() - self.offset
                self.move(value)
                self.offset = e.globalPos()
    
    def keyPressEvent(self, e):
        """
            Description: pass the event to current page widget
            Author : Hyeok Yoon (2025.10.17)
            Modify : add page constant variable (2025.10.27)
        """
        if(self.mid_mainwindow.stackedWidget.currentIndex() == LABELLING):
            self.mid_mainwindow.page_1.scrollAreaWidgetContents.keyPressEvent(e)
    
    def keyReleaseEvent(self, e):
        """
            Description: pass the event to current page widget
            Author : Hyeok Yoon (2025.10.17)
            Modify : add page constant variable (2025.10.27)
        """
        if(self.mid_mainwindow.stackedWidget.currentIndex() == LABELLING):
            self.mid_mainwindow.page_1.scrollAreaWidgetContents.keyReleaseEvent(e)

    @QtCore.pyqtSlot(dict)
    def resize_signal(self, output):
        """윈도우 타이틀 기능 동작에 대한 아이콘 변경 및 상태를 merge mainwindow로 부터 받는 함수이다.
                Parameters
                1.  output(dict)
                    - mode(str)
                        - min : UI 최소화 모드
                        - max : UI 최대화 또는 노멀 모드
                        - close : UI 클로즈 모드
                        - move : UI 이동 모드
        """
        mode = output['mode']
        if mode == "min" : #minimize
            self.showMinimized()
        elif mode == "resize":
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
                self.init_sw = True
        elif mode == "close":
            """
                Description: Elroikit 종료 관련 코드수정
                Modified by MyoungHwan (2024.10.23)
            """
            self.close()
        elif mode == "move":
            self.window_moveable =  output['bool']
            self.offset = output['offset']
        
    def hideEvent(self, e):
        for _, obj in self.sub_widget_dict.items():
            if obj.isVisible():
                obj.showMinimized()

    def showEvent(self, e) -> None:
        for _, obj in self.sub_widget_dict.items():
            if obj.isMinimized():
                obj.showNormal()

    def closeEvent(self, e) -> None:
        """
            @description: 종료할때 발생하는 함수
            @author : MyoungHwan
            @history
                1. Modified by MyoungHwan (2024.10.23): Elroikit 종료 관련 코드수정
        """
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setWindowTitle(self.lang.get("main", "top", "quit_title"))
        msg_box.setText(self.lang.get("main", "top", "quit_title_msg"))
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
        msb_box_ybtn = msg_box.button(QtWidgets.QMessageBox.Yes)
        msb_box_ybtn.setText(self.lang.get("main", "top", "quit_title_msg_yes"))
        msb_box_nbtn = msg_box.button(QtWidgets.QMessageBox.No)
        msb_box_nbtn.setText(self.lang.get("main", "top", "quit_title_msg_no"))
        msg_box.exec_()
        if msg_box.clickedButton() == msb_box_ybtn:
            e.accept()
        else:
            e.ignore()


    def lic_chk(self):
        print("License Check Timer : ", QTime.currentTime().toString("hh:mm:ss"))
        if check_lic_status():
            if self.isEnabled()==False:
                self.setEnabled(True)
        else:
            result = QtWidgets.QMessageBox.critical(self, "License is not authentication", "License is not authentication!!!", 
                    QtWidgets.QMessageBox.Cancel| QtWidgets.QMessageBox.Reset )
            if result == QtWidgets.QMessageBox.Cancel:
                sys.exit(0)
            elif result == QtWidgets.QMessageBox.Reset:
                self.lic_chk()

def checkSameProcess(processName):
    """
        @Description: Check if there is any running process that contains the given process name.
        @Author: GaEun Hwang (2025.10.14)
    """
    currentProcessPid = os.getpid()
    for process in psutil.process_iter(['pid', 'name', 'ppid']):
        try:
            # not to compare with itself
            if process.info['pid'] == currentProcessPid:
                continue
            if process.info['name'] == processName and process.info['ppid'] != currentProcessPid:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

if __name__ == "__main__":
    # do not remove this !!
    multiprocessing.freeze_support()
    # Check ElroiKit is already running for prevent multiple instances
    processName = "ElroiKit.exe"
    if multiprocessing.current_process().name == "MainProcess" and checkSameProcess(processName):
        tempApp = QtWidgets.QApplication([]) # Create a temporary QApplication instance for QMessageBox with low resource usage
        QtWidgets.QMessageBox.information(None, "Error", "ElroiKit is already running", QtWidgets.QMessageBox.Ok)
        sys.exit(0)
    
    # Limit BLAS/OMP/MKL threads to 1 to prevent memory error
    try:
        threadLimit = '1'
        os.environ['OPENBLAS_NUM_THREADS'] = threadLimit
        os.environ['MKL_NUM_THREADS'] = threadLimit
        os.environ['OMP_NUM_THREADS'] = threadLimit

    except Exception as e:
        print(f"Error setting thread limits: {e}")

    # Must be called before creating the QApplication object
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) # Enable High DPI scaling
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True) # Use High DPI icons
    QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough) # Set DPI scale factor rounding policy to PassThrough (no rounding)

    # shared root path
    if not os.path.exists(shared_root_path):
        os.mkdir(shared_root_path)

    # license path
    if not os.path.isdir(license_path):
        os.mkdir(license_path)
    make_HW_status() # license check !

    # temp directory
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)

    app = QtWidgets.QApplication(sys.argv)
    # Adjust application font size based on DPI scaling factor
    screen = app.primaryScreen()
    factor  = screen.devicePixelRatio() # Get DPI scaling factor
    nunumSquareFont = "NanumSquareNeo-bRg.ttf"
    fontID = QtGui.QFontDatabase.addApplicationFont(os.path.join(font_path, nunumSquareFont))
    font = QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(fontID)[0])
    font.setHintingPreference(QtGui.QFont.HintingPreference.PreferFullHinting) # Set hinting preference to full hinting
    font.setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias) # Set style strategy to prefer antialiasing
    #
    #font = app.font()
    #font.setPointSizeF(font.pointSizeF() * factor) # Scale font size
    app.setFont(font)
    merge_MainWindow = QtWidgets.QMainWindow()
    ui = Merge_MainWindow_Form()
    icon = QIcon(os.path.join(icon_path, 'E.ico'))
    app.setWindowIcon(icon)
    sys.exit(app.exec_())
