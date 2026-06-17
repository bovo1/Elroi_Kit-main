"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

import os
import sys
import multiprocessing
import psutil
import json
import atexit
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt, QTimer, QTime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from top import Top_MainWindow_Form
from mid import Mid_MainWindow_Form
from utils.language import Language
from core.main_core import Main_Core
from utils.shared import shared_root_path, license_path, temp_path, icon_path, font_path, settings_path
from utils.license import make_HW_status, check_lic_status
from constants.constants import *
from utils.custom_ui import messageBox
from utils.tools import shutdownRunningProcesses

from stylesheet.stylesheet_component import buildStylesheet
from stylesheet.stylesheet_common import STYLE
from stylesheet.stylesheet_labeling import LABELING_STYLESHEET
from stylesheet.stylesheet_training import TRAINING_STYLESHEET
from stylesheet.stylesheet_advanced import ADVANCED_STYLESHEET

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
        self.lang = Language()
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
        self.lang.apply("en")

        self.main_sub_Sync = main_sub_Sync()
        self.main_top_to_merge_signal = self.main_sub_Sync.main_top_to_merge_signal
        self.main_top_to_merge_signal.connect(self.resize_signal)
        self.main_merge_to_top_signal = self.main_sub_Sync.main_merge_to_top_signal

        self.Main_Core = Main_Core(lang=self.lang)
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
        QApplication.instance().applicationStateChanged.connect(self.applicationFocusOut)

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

    def applicationFocusOut(self, state):
        """
            @Description: application focus out 상태 저장함수
            @Author: Hyunsu Kim (2026.03.23)
        """
        if state != QtCore.Qt.ApplicationInactive:
            return

        app = QApplication.instance()
        if app.activeModalWidget() is not None or app.activePopupWidget() is not None:
            return

        for widget in app.topLevelWidgets():
            if isinstance(widget, QtWidgets.QFileDialog) and widget.isVisible():
                return

        for _, obj in self.sub_widget_dict.items():
            if obj.isVisible():
                obj.close()


    def init_Ui_main(self, merge_MainWindow):
        """Merge UI 생성을 위한 초기 선언문이다.
                Parmeters
                1.	merge_MainWindow(object): PyQt widget object
        """
        merge_MainWindow.setObjectName("merge_MainWindow")
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
            for _, obj in self.sub_widget_dict.items():
                if obj.isVisible():
                    obj.close()
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
                2. Modified by Yugyeong Hong(2026.02.24) : Refactor message box with util method and language support
                3. Modified by Hyunsu Kim (2026.03.25): Added function to close all sub windows when main window is closed
                4. Modified by Hyunsu Kim (2026.05.12): Added function to shutdown all running background processes when main window is closed
        """
        self.messageBoxResponse = messageBox(mode=MESSAGE_BOX_CONFIRMATION,
                                             title=self.lang.get("main", "top", "quit_title"),
                                             text=self.lang.get("main", "top", "quit_title_msg"),
                                             buttons={self.lang.get("main", "messageBox", "msgYes"): "accept", self.lang.get("main", "messageBox", "msgNo"): "reject"})
        if self.messageBoxResponse == "accept":
            for _, obj in self.sub_widget_dict.items():
                if obj.isVisible():
                    obj.close()
            e.accept()
        else:
            e.ignore()


    def lic_chk(self):
        print("License Check Timer : ", QTime.currentTime().toString("hh:mm:ss"))
        if check_lic_status():
            if self.isEnabled()==False:
                self.setEnabled(True)
        else:
            """
                Description
                    modified by Yugyeong Hong(2026.02.24) : Refactor message box with util method and language support
            """
            title = self.lang.get("main", "top", "licenseErrorTitle")
            text = self.lang.get("main", "top", "licenseErrorMsg")
            buttonRetry = self.lang.get("main", "messageBox", "msgRetry")
            buttonCancel = self.lang.get("main", "messageBox", "msgCancel")
            messageBoxResponse = messageBox(mode=MESSAGE_BOX_WARNING, title=title, text=text, buttons={buttonRetry: "accept", buttonCancel: "reject"})
            if messageBoxResponse == "accept":
                self.lic_chk()
            else:
                sys.exit(0)

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

def runningErrorMessage():
    """
        Description: Show error message box when ElroiKit is already running
        Author: Yugyeong Hong(2026.02.24)
    """
    lang = Language()
    lang.apply("en") # Set default language to English for error message box
    messageBox(mode=MESSAGE_BOX_WARNING,
               title=lang.get("main", "top", "WarningTitle"), 
               text=lang.get("main", "top", "alreadyRunningMsg"), 
               buttons={lang.get("main", "messageBox", "msgOk"): "accept"})


if __name__ == "__main__":
    # do not remove this !!
    multiprocessing.freeze_support()
    # Check ElroiKit is already running for prevent multiple instances
    processName = "ElroiKit.exe"
    if multiprocessing.current_process().name == "MainProcess" and checkSameProcess(processName):
        tempApp = QtWidgets.QApplication([]) # Create a temporary QApplication instance for QMessageBox with low resource usage
        runningErrorMessage()
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
    
    # settings
    defaultSettings = {
        "Common":{
            "font": FONT_DEFAULT,
        },
        "Training":{
            "dataLoadThread": DATA_LOAD_WORKERS
        }
    }

    if not os.path.isfile(settings_path):
        # If the settings.json file does not exist, create it with default settings
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(defaultSettings, f, indent=4)

    app = QtWidgets.QApplication(sys.argv)
    # Adjust application font size based on DPI scaling factor
    screen = app.primaryScreen()
    factor  = screen.devicePixelRatio() # Get DPI scaling factor
    # Build the application stylesheet by combining global styles and specific styles
    stylesheet = buildStylesheet(globalStyle=STYLE, specificStyle=[LABELING_STYLESHEET, TRAINING_STYLESHEET, ADVANCED_STYLESHEET])
    app.setStyleSheet(stylesheet)
    # defaultFont is system default font, which is used when user select "Default" font option.
    # It can be different by OS and user settings.
    defaultFont = app.font()

    # add fonts to application
    fontDict = dict()
    for fontName, fontInfo in FONT_DICTIONARY.items():
        # add font to application not require font installation on OS
        fontID = QtGui.QFontDatabase.addApplicationFont(os.path.join(font_path, fontInfo["fileName"]))
        # it returns the fontID if the font is successfully added, otherwise it returns -1
        if fontID != -1:
            # applicationFontFamilies() returns a list of font families for the given font ID
            # first element of the list is the primary font family name
            fontDict[fontName] = {
                "font": QtGui.QFont(QtGui.QFontDatabase.applicationFontFamilies(fontID)[0])
            }
            fontDict[fontName]["font"].setPointSizeF(fontInfo["defaultSize"] * factor)
            fontDict[fontName]["font"].setHintingPreference(QtGui.QFont.HintingPreference.PreferFullHinting)
            fontDict[fontName]["font"].setStyleStrategy(QtGui.QFont.StyleStrategy.PreferAntialias)
        else:
            print(f"Failed to load font: {fontName}")

    # load settings
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settingsJson = json.load(f)
    except Exception as e:
        print(f"Error loading UI settings: {e}\n Load default UI settings.")
        settingsJson = defaultSettings
        # If there is an error loading the settings.json file, overwrite it with default settings to prevent errors
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settingsJson, f, indent=4)

    savedFont = settingsJson["Common"]["font"]
    if savedFont in fontDict:
        font = fontDict[savedFont]["font"]
        fontName = savedFont
    else:
        font = defaultFont
        fontName = FONT_DEFAULT

    app.setFont(font)
    ui = Merge_MainWindow_Form()
    icon = QIcon(os.path.join(icon_path, 'E.ico'))
    app.setWindowIcon(icon)

    # Set the corresponding font menu action as checked based on the loaded font setting
    for fontAction in ui.mid_mainwindow.menuSettingFont.actions():
        if fontAction.data() == fontName:
            fontAction.setChecked(True)

    def changeFont(fontName, messageTitle, message):
        """
            @description: Change application font based on user selection from the settings menu
            @author: GaEun Hwang (2026.03.10)
        """
        # Save the selected font to settings.json for persistence
        settingsJson["Common"]["font"] = fontName
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settingsJson, f, indent=4)
        
        # Show message box to inform user that font change will be applied after restarting the application
        messageBox(
            mode=MESSAGE_BOX_INFORMATION,
            title=messageTitle,
            text=message,
        )
    
    # Connect the font change function to the font menu actions
    ui.mid_mainwindow.settingFontFunction_signal.connect(changeFont)
    atexit.register(shutdownRunningProcesses) # Register the onExit function to be called when the application is exiting

    sys.exit(app.exec_())
