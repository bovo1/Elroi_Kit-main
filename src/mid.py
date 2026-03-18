"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

stylesheet = """
QMainWindow, QMenuBar{
    background-color: rgb(39, 38, 39);
}

QMenuBar {
    spacing: 3px; /* spacing between menu bar items */
    font: 15px;
    color : white;
}
QMenuBar::item
{
    background-color: rgb(39, 38, 39);
    color: white;
}
QMenuBar::item::selected
{
    background-color: rgb(39, 38, 39);
    color: rgb(16, 97, 150);
}
QMenu
{
    background-color: rgb(39, 38, 39);
    color: white;
}
QMenu::item::selected
{
    background-color: rgb(39, 38, 39);
    color: rgb(16, 97, 150);
}


QAction::selected{
    background-color: transparent;
}

QToolBar{
    padding-left: 5px;
    spacing: 10px;
    border-top: 1px solid #282728;
    border-bottom: 1px solid #282728;
    background : no-repeat right/ url("ico/labeling/logo/logo.png");
    background-color: rgb(65, 65, 65);
}

QToolButton:hover, QToolButton::checked {
    background-color: transparent;
}


QStatusBar {
    background-color: rgb(83, 83, 83);
    font: 15px;
    color : white;
    border: 0;
}

QStatusBar::item {
    border: none;
}
QStatusBar QLabel{
        font: 15px;
        color : white;
        border: 0;
    }
"""

import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QKeySequence
from labeling.ui.labeling_mode_main import Label_Main
from training.ui.training_mode_main import Train_Main
from advanced.ui.adv_main import Advanced_Main

from license_term import License_Form
from utils.custom_ui import messageBox
from constants.constants import MESSAGE_BOX_INFORMATION, FONT_DEFAULT, FONT_PRETENDARD, FONT_NANUM_SQUARE_NEO, FONT_NANUM_GOTHIC
"""
    description
    modified by MyoungHwan(20240605) : modification of Version Variable Information
"""
from version import major, minor, patch

class VLine(QtWidgets.QFrame):
    # a simple VLine, like the one you get from designer
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine|self.Sunken)


class Mid_MainWindow_Form(QtWidgets.QMainWindow):
    """라벨링 모드 최상위 메인 클래스이다. 라벨링을 위한 이미지, 라벨, 디스플레이, 펜, 그래프 UI들이 하위 클래스에서 선언된다.
    """
    settingFontFunction_signal = QtCore.pyqtSignal(str, str, str)
    def __init__(self, Core, lang):
        super().__init__()
        self.init(Core, lang)
        self.init_Ui_main(self)
        self.init_Ui_bar(self)
        self.init_Ui_bar_menu(self)
        self.init_Qaction(self)
        self.init_Function(self)
        self.setup_Ui_Main(self)

        # self.showMaximized()
        self.setMouseTracking(True)
        if __name__ == "__main__":
            self.show()
    
    def init(self, Core, lang):
        """초기 선언 시 변수 선언문이다. Core DB 데이터를 이용하기 위해 Core 객체를 생성한다.

        """
        self.lang = lang
        self.Core = Core
        self.Sub_Core_Sync_Labeling = self.Core.Sub_Core_Sync_Labeling
        self.Sub_Core_Sync_Training = self.Core.Sub_Core_Sync_Training
        self.Sub_Core_Sync_Advanced = self.Core.Sub_Core_Sync_Advanced

        self.mainwindow_to_core_signal = self.Sub_Core_Sync_Labeling.mainwindow_to_core_signal
        self.mainwindow_to_pen_signal = self.Sub_Core_Sync_Labeling.mainwindow_to_pen_signal
        self.sub_widget_dict = self.Sub_Core_Sync_Labeling.sub_widget_dict

        # training -> statusbar
        self.Sub_Core_Sync_Training.statusbar_signal.connect(self.Status_bar)

        self.license_term = License_Form()

        self.core_obj_dict = self.Core.core_obj_dict
        self.image_control_dict = self.Sub_Core_Sync_Labeling.image_control_dict
        
        
    def init_Ui_main(self, Mid_MainWindow):
        """라벨링 모드 UI 생성을 위한 초기 선언문이다.
                Parameters
                1.   Mid_MainWindow(object): PyQt widget object
        """
        Mid_MainWindow.setObjectName("Mid_MainWindow")
        Mid_MainWindow.setStyleSheet(stylesheet)

        self.centralwidget = QtWidgets.QWidget(Mid_MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName("stackedWidget")

        self.page_1 = Label_Main(self.Sub_Core_Sync_Labeling, self.lang)
        self.page_1.setObjectName("page")
        self.stackedWidget.addWidget(self.page_1)

        self.page_2 = Train_Main(self.Sub_Core_Sync_Training, self.lang)
        self.page_2.setObjectName("page_2")
        self.stackedWidget.addWidget(self.page_2)

        self.page_3 = Advanced_Main(self.Sub_Core_Sync_Advanced, self.lang)
        self.page_3.setObjectName("page_3")
        self.stackedWidget.addWidget(self.page_3)
        
        self.gridLayout.addWidget(self.stackedWidget, 0, 0, 1, 1)
        self.gridLayout.setContentsMargins(6,6,6,6)
        self.stackedWidget.setCurrentIndex(0)

    def init_Ui_bar(self, Mid_MainWindow):
        """상위 bar 관련 UI 생성을 위한 초기 선언문이다. menubar, toolbar, statusbar 가 선언된다.
                Parameters
                1.   Mid_MainWindow(object): PyQt widget object
        """
        self.menubar = QtWidgets.QMenuBar(Mid_MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1116, 26))
        self.menubar.setObjectName("menubar")

        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")

        self.menuinfo = QtWidgets.QMenu(self.menubar)
        self.menuinfo.setObjectName("menuinfo")

        self.menuLanguage = QtWidgets.QMenu(self.menubar)
        self.menuLanguage.setObjectName("menuLanguage")

        self.statusbar = QtWidgets.QStatusBar(Mid_MainWindow)
        self.statusbar.setObjectName("statusbar")
        # self.statusbar.showMessage("Ready")

        self.statusbar.addWidget(VLine())
        self.statusbar.addWidget(self.core_obj_dict['status_image_status'][0])
        self.statusbar.addWidget(self.core_obj_dict['status_image_status'][1])
        self.statusbar.addWidget(VLine())
        self.statusbar.addWidget(self.core_obj_dict['status_labeling_status'][0])
        self.statusbar.addWidget(self.core_obj_dict['status_labeling_status'][1])
        self.statusbar.addWidget(VLine())
        self.statusbar.addWidget(self.core_obj_dict['status_pointer_status'][0])
        self.statusbar.addWidget(self.core_obj_dict['status_pointer_status'][1])
        self.statusbar.addWidget(VLine())
        self.statusbar.addPermanentWidget(self.core_obj_dict['status_training_status'])
        self.statusbar.addPermanentWidget(VLine())
        
        
        self.toolBar = QtWidgets.QToolBar(Mid_MainWindow)
        self.toolBar.setMovable(False)
        self.toolBar.setIconSize(QtCore.QSize(50, 50))
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.toolBar.setFloatable(False)
        self.toolBar.setObjectName("toolBar")

    def init_Ui_bar_menu(self, Mid_MainWindow):
        """상위 bar menu UI 생성을 위한 초기 선언문이다. menubar에 들어갈 항목을 추가하는 함수이다.
                Parameters
                1.   Mid_MainWindow(object): PyQt widget object
        """
        self.action_save = QtWidgets.QAction(Mid_MainWindow)
        self.action_save.setObjectName("action_save")
        self.action_save.setShortcut(QKeySequence("Ctrl+S"))
        self.lang.set("main", "mid", "action_save", self.action_save)

        self.action_save_as = QtWidgets.QAction(Mid_MainWindow)
        self.action_save_as.setObjectName("action_save_as")
        self.action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.lang.set("main", "mid", "action_save_as", self.action_save_as)
        
        self.action_save_all = QtWidgets.QAction(Mid_MainWindow)
        self.action_save_all.setObjectName("action_save_all")
        self.lang.set("main", "mid", "action_save_all", self.action_save_all)

        self.menuFile.addAction(self.action_save)
        self.menuFile.addAction(self.action_save_as)
        # self.menuFile.addAction(self.action_save_all)


        self.action_language_english = QtWidgets.QAction(Mid_MainWindow)
        self.action_language_english.setObjectName("action_language_english")
        self.lang.set("main", "mid", "action_language_english", self.action_language_english)
        self.action_language_korean = QtWidgets.QAction(Mid_MainWindow)
        self.action_language_korean.setObjectName("action_language_korean")
        self.lang.set("main", "mid", "action_language_korean", self.action_language_korean)
        self.menuLanguage.addAction(self.action_language_english)
        self.menuLanguage.addAction(self.action_language_korean)
    

        self.action_info_about = QtWidgets.QAction(Mid_MainWindow)
        self.action_info_about.setObjectName("action_info_about")
        self.lang.set("main", "mid", "action_info_about", self.action_info_about)

        self.action_info_license = QtWidgets.QAction(Mid_MainWindow)
        self.action_info_license.setObjectName("action_info_license")
        self.lang.set("main", "mid", "action_info_license", self.action_info_license)

        self.menuinfo.addMenu(self.menuLanguage)
        self.menuinfo.addAction(self.action_info_about)
        self.menuinfo.addAction(self.action_info_license)

        self.menuSettingFont = QtWidgets.QMenu(self.menubar)
        self.menuSettingFont.setObjectName("actionSettingFont")
        self.lang.set("main", "mid", "actionSettingFont", self.menuSettingFont)
        
        self.actionSettingFont_Default = QtWidgets.QAction(Mid_MainWindow)
        self.actionSettingFont_Pretendard = QtWidgets.QAction(Mid_MainWindow)
        self.actionSettingFont_NanumSquareNeo = QtWidgets.QAction(Mid_MainWindow)
        self.actionSettingFont_NanumGothic = QtWidgets.QAction(Mid_MainWindow)

        self.actionSettingFont_Default.setCheckable(True)
        self.actionSettingFont_Pretendard.setCheckable(True)
        self.actionSettingFont_NanumSquareNeo.setCheckable(True)
        self.actionSettingFont_NanumGothic.setCheckable(True)

        self.actionSettingFont_Default.setObjectName("actionSettingFont_Default")
        self.actionSettingFont_Pretendard.setObjectName("actionSettingFont_Pretendard")
        self.actionSettingFont_NanumSquareNeo.setObjectName("actionSettingFont_NanumSquareNeo")
        self.actionSettingFont_NanumGothic.setObjectName("actionSettingFont_NanumGothic")

        self.actionSettingFont_Default.setData(FONT_DEFAULT)
        self.actionSettingFont_Pretendard.setData(FONT_PRETENDARD)
        self.actionSettingFont_NanumSquareNeo.setData(FONT_NANUM_SQUARE_NEO)
        self.actionSettingFont_NanumGothic.setData(FONT_NANUM_GOTHIC)

        self.lang.set("main", "mid", "actionSettingFont_Default", self.actionSettingFont_Default)
        self.lang.set("main", "mid", "actionSettingFont_Pretendard", self.actionSettingFont_Pretendard)
        self.lang.set("main", "mid", "actionSettingFont_NanumSquareNeo", self.actionSettingFont_NanumSquareNeo)
        self.lang.set("main", "mid", "actionSettingFont_NanumGothic", self.actionSettingFont_NanumGothic)

        self.menuSetting.addMenu(self.menuSettingFont)
        self.menuSettingFont.addAction(self.actionSettingFont_Default)
        self.menuSettingFont.addAction(self.actionSettingFont_Pretendard)
        self.menuSettingFont.addAction(self.actionSettingFont_NanumSquareNeo)
        self.menuSettingFont.addAction(self.actionSettingFont_NanumGothic)

        self.fontActionGroup = QtWidgets.QActionGroup(Mid_MainWindow)
        self.fontActionGroup.setExclusive(True)
        self.fontActionGroup.addAction(self.actionSettingFont_Default)
        self.fontActionGroup.addAction(self.actionSettingFont_Pretendard)
        self.fontActionGroup.addAction(self.actionSettingFont_NanumSquareNeo)
        self.fontActionGroup.addAction(self.actionSettingFont_NanumGothic)

    def init_Qaction(self, Mid_MainWindow):
        """
            @description : 상위 toolbar 버튼에 대한 UI를 추가 또는 디자인 위한 선언문이다.
            @authors : MyoungHwan
            @parameters
                1. Mid_MainWindow(object): PyQt widget object
            @history
                1. modified by MyoungHwan(20240603): 아이콘 경로 수정
        """
        icon_LabelingMode = QtGui.QIcon()
        icon_LabelingMode.addPixmap(QtGui.QPixmap("ico/menu/Labeling_mode_white.PNG"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_LabelingMode.addPixmap(QtGui.QPixmap("ico/menu/Labeling_mode_yellow.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        icon_LabelingMode.addPixmap(QtGui.QPixmap("ico/menu/Labeling_mode_yellow.png"), QtGui.QIcon.Disabled, QtGui.QIcon.On)
        
        icon_TrainingMode = QtGui.QIcon()
        icon_TrainingMode.addPixmap(QtGui.QPixmap("ico/menu/training_mode_white.PNG"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_TrainingMode.addPixmap(QtGui.QPixmap("ico/menu/training_mode_yellow.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        icon_TrainingMode.addPixmap(QtGui.QPixmap("ico/menu/training_mode_yellow.png"), QtGui.QIcon.Disabled, QtGui.QIcon.On)

        icon_ADVMode = QtGui.QIcon()
        """
            description
            modified by MyoungHwan(20240603): 아이콘 경로 수정
        """
        icon_ADVMode.addPixmap(QtGui.QPixmap("ico/menu/utility_mode_white.PNG"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_ADVMode.addPixmap(QtGui.QPixmap("ico/menu/utility_mode_yellow.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        icon_ADVMode.addPixmap(QtGui.QPixmap("ico/menu/utility_mode_yellow.png"), QtGui.QIcon.Disabled, QtGui.QIcon.On)

        self.actionLabeling_mode = QtWidgets.QAction(Mid_MainWindow)
        self.actionLabeling_mode.setIcon(icon_LabelingMode)
        self.actionLabeling_mode.setObjectName("actionLabeling_mode")
        self.actionLabeling_mode.setCheckable(True)
        self.actionLabeling_mode.setChecked(True)
        self.actionLabeling_mode.setEnabled(False)

        self.actionTraining_mode = QtWidgets.QAction(Mid_MainWindow)
        self.actionTraining_mode.setIcon(icon_TrainingMode)
        self.actionTraining_mode.setObjectName("actionTraining_mode")
        self.actionTraining_mode.setCheckable(True)

        self.actionadvanced_mode = QtWidgets.QAction()
        self.actionadvanced_mode.setIcon(icon_ADVMode)
        self.actionadvanced_mode.setObjectName("actionadvanced_mode")
        self.actionadvanced_mode.setCheckable(True)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuinfo.menuAction())

        self.toolBar.addAction(self.actionLabeling_mode)
        self.toolBar.addAction(self.actionTraining_mode)
        self.toolBar.addAction(self.actionadvanced_mode)

    def init_Function(self, _):
        """bar Ui에 존재하는 기능들에 대한 connect 함수를 정의한다.
        """
        self.actionLabeling_mode.triggered.connect(lambda ch=self.actionLabeling_mode ,mode=0 : self.Page_changed(ch, mode, obj=self.actionLabeling_mode))
        self.actionTraining_mode.triggered.connect(lambda ch=self.actionTraining_mode  ,mode=1 : self.Page_changed(ch, mode, obj=self.actionTraining_mode))
        self.actionadvanced_mode.triggered.connect(lambda ch=self.actionadvanced_mode  ,mode=2 : self.Page_changed(ch, mode, obj=self.actionadvanced_mode))

        #File Menu list trigger
        self.action_save.triggered.connect(lambda  : self.Menu_function(mode=1))
        self.action_save_as.triggered.connect(lambda : self.Menu_function(mode=2))
        self.action_save_all.triggered.connect(lambda : self.Menu_function(mode=3))
        self.action_language_english.triggered.connect(lambda: self.lang.apply("en"))
        self.action_language_korean.triggered.connect(lambda: self.lang.apply("ko"))

        #File Menu list trigger
        self.action_info_about.triggered.connect(lambda : self.info_function(mode=0))
        self.action_info_license.triggered.connect(lambda : self.info_function(mode=1))

        self.actionSettingFont_Default.triggered.connect(lambda : self.settingFontFunction(fontName=FONT_DEFAULT))
        self.actionSettingFont_Pretendard.triggered.connect(lambda : self.settingFontFunction(fontName=FONT_PRETENDARD))
        self.actionSettingFont_NanumSquareNeo.triggered.connect(lambda : self.settingFontFunction(fontName=FONT_NANUM_SQUARE_NEO))
        self.actionSettingFont_NanumGothic.triggered.connect(lambda : self.settingFontFunction(fontName=FONT_NANUM_GOTHIC))
        

    def setup_Ui_Main(self, Mid_MainWindow):
        """초기화된 ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
                Parameters
                1.   Mid_MainWindow(object): PyQt widget object
        """
        Mid_MainWindow.setCentralWidget(self.centralwidget)
        Mid_MainWindow.setMenuBar(self.menubar)
        Mid_MainWindow.setStatusBar(self.statusbar)
        Mid_MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        Mid_MainWindow.insertToolBarBreak(self.toolBar)
        QtCore.QMetaObject.connectSlotsByName(Mid_MainWindow)

        self.lang.set("main", "mid", "toolBar", self.toolBar)
        self.lang.set("main", "mid", "menuFile", self.menuFile)
        self.lang.set("main", "mid", "menuInfo", self.menuinfo)
        self.lang.set("main", "mid", "menuLanguage", self.menuLanguage)
        self.lang.set("main", "mid", "actionLabeling_mode", self.actionLabeling_mode)
        self.lang.set("main", "mid", "actionTraining_mode", self.actionTraining_mode)

        self.toolbar_list = [self.actionLabeling_mode, self.actionTraining_mode, self.actionadvanced_mode]

    def Page_changed(self, ch, mode, obj):
        """
            Description: 탭 위젯에서 페이지 변경시 발동되는 기능
                Parameters
                1. ch(bool) : check status
                    - True : checked
                    - False : not checked
                2. mode(int) : change mode name
                    - 0 : labeling mode
                    - 1 : Training mode 
                    - 2 : Advanced mode
            
            Implement by MyoungHwan
            Modified by MyoungHwan(20240521)
        """
        for i, obj in enumerate(self.toolbar_list):
            if mode != i:
                if obj.isChecked():
                    obj.setChecked(False)
                    obj.setEnabled(True)
            else: # 똑같은 모드 한번더 눌렀을때
                obj.setEnabled(False)
        # print(ch, mode)
        if mode == 0:
            # training mode
            self.stackedWidget.setCurrentIndex(0)
            
        elif mode == 1:
            # labeling mode
            self.stackedWidget.setCurrentIndex(1)
            #labeling widget close if opened
            for _, obj in self.sub_widget_dict.items():
                if obj.isVisible():
                    obj.close()
        elif mode == 2:
            # adv mode
            self.stackedWidget.setCurrentIndex(2)
        else:
            pass
    
    def Menu_function(self, mode):
        """
            @Description: Select function list in "File" menu
            @Author: MyoungHwan
            @Parameters
                1. mode(int)
                    - 2 : 라벨링 후 경로를 지정하여 save
            
            @History
                1. Modified by MyoungHwan (2024.02.15): Add Excteption when input the empty path for "getSaveFileName" Function
                2. Modified by MyoungHwan (2024.12.13): 기능사용(Labeling, Training, Utility)에 따른 분기 코드 추가
                3. Modified by MyoungHwan (2025.03.14): 기능사용(Labeling, Training, Utility)에 따른 분기 코드 수정
        """
        # Modified by MyoungHwan (2024.12.13): 기능사용(Labeling, Training, Utility)에 따른 분기 코드 추가
        cur_page = self.stackedWidget.currentIndex()
        # Labeling mode일때
        if cur_page == 0:
            if self.image_control_dict['select_image_number'] > -1:
                temp_dict = {}
                temp_dict['mode'] = mode
                if mode == 1:
                    pass
                elif mode == 2:
                    fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save labeled file(*.npy)", "", "npy(*.npy)")
                    temp_dict['save_as_path'] = fname
                self.mainwindow_to_core(temp_dict)


    def info_function(self, mode):
        if mode == 0:#version info
            """
                description
                modified by MyoungHwan(20240605) : modify message
                modified by Yugyeong Hong(2026.02.24) : Refactor message box with util method and language support
            """
            message = f'<p style="font-size:15pt; color: #0078FF;">ElroiKit</p>\n \
                        <p style="font-size:10pt; ">{self.lang.get("main", "mid", "action_info_about_version_msg") + f" :{major}.{minor}.{patch}"}</p>\n \
                        <p style="font-size:10pt; ">{self.lang.get("main", "mid", "action_info_about_contact_msg") + " :elroilab@elroilab.com"}</p>' 
            messageBox(mode=MESSAGE_BOX_INFORMATION, title=self.lang.get("main", "mid", "action_info_about_title"), text=message, buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
        
        elif mode == 1: # license info
            self.license_term.exec_()
        elif mode == 2:
            pass 
        
    def settingFontFunction(self, fontName):
        """
            @description: send signal with selected font
            @author: GaEun Hwang (2026.03.10)
        """
        changeFontMessageTitle = self.lang.get("main", "mid", "changeFontMessageTitle")
        changeFontMessage = self.lang.get("main", "mid", "changeFontMessage")
        self.settingFontFunction_signal.emit(fontName, changeFontMessageTitle, changeFontMessage)

    def mainwindow_to_core(self, input):
        """mid mainwindow에서 core로 시그널을 보내기 위한 함수 선언문이다. 현재 라벨링 저장 경로를 전달하기 위해 사용중이다.
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary
        """
        self.mainwindow_to_core_signal.emit(input)
        # 
    
    @QtCore.pyqtSlot(str)
    def Status_bar(self, message):
        self.statusbar.showMessage(message)
        

if __name__ == "__main__":
    import sys
    print(f"Main Window cur path : "+ os.getcwd())
    app = QtWidgets.QApplication(sys.argv)
    Mid_MainWindow = QtWidgets.QMainWindow()
    ui = Mid_MainWindow_Form()
    sys.exit(app.exec_())
