"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""


import glob
import numpy as np
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from utils.worker import Threading_Worker
from utils.advanced import simplelabeling
from qtwidgets import AnimatedToggle
import cv2
from utils.custom_ui import messageBox
from constants.constants import MESSAGE_BOX_CONFIRMATION, MESSAGE_BOX_WARNING

if __name__ == "__main__" :
    from adv_gen_module import gen_module
else:
    from .adv_gen_module import gen_module

from advanced.stylesheet.stylesheet_adv_sal_mode import stylesheet

class signal_(QtCore.QObject):
    string_signal = QtCore.pyqtSignal(str)

class advanced_sal_Form(QtWidgets.QWidget):
    def __init__(self, Sync=None, lang=None) -> None:
        super().__init__()
        self.init(Sync=Sync, lang=lang)
        self.init_variable()
        self.init_ui(self)
        self.setup_ui()
        self.init_function()
        self.fill_table()
        if __name__ == "__main__":
            self.show()

    def init(self, Sync=None, lang=None):
        self.Sync = Sync
        self.lang = lang

        self.worker_1 = Threading_Worker()
        self.worker_1.output.connect(self.recv_from_threading)
        
        self.signal_ = signal_()
        self.string_signal = self.signal_.string_signal

        self.string_signal.connect(self.update_status)

    def init_variable(self):
        """
            @description: 초기 변수 선언부분
            @author : MyoungHwan
            @parameters
                - self.header_dict : 기능설정에 대한 오브젝트를 딕셔너리형태로 저장
                - self.adv_model_info : 기능설정에 대한 정보를 딕셔너리형태로 저장
                    0: SAL 수행시 기준이 되는 정보, 어두운 영역을 기준으로 정할지 밝은 스펙트럼 영역을 기준으로 정할지 선택
                    1: Expand/Reduce 적용 여부
                    2: Expand/Reduce 적용 시 커널 사이즈
                    3: Calibration 설정여부
                    4: Calibration Ratio 조정
                - self.adv_data_list_info : 기능을 적용할 데이터 대상리스트를 딕셔너리형태로 저장
                - self.worker_id : 기능 병렬처리를 위해 할당된 ID
                - self.dash: Qplaintextedit에 보여줄 특수문자
                - self.mode: 기능에 대한 명
                - self.interrupt_: 쓰레딩 중간 정지를 위한 스위칭 변수
                - self.signal_sw: 시그널 발동시 동시처리를 방지하기 위한 스위칭 변수
        """
        self.header_dict_ = {}
        """
            description
            modified by MyoungHwan(20240604) : 오타 수정
        """
        self.adv_model_info = {
            #[init value, set value]
            0: # Select Standard Normal label
                {
                    "type":"Select Standard Normal label",
                    "tip":["label:1. Select Standard Normal label"],
                    "value": [0, 0],
                    "obj_list":["combobox:Negative,Positive" ]
                },
            1: #Expand/Reduce Detected Normal Area
                {
                    "type":"Expand/Reduce Detected Normal Area",
                    "tip":["label:2. Expand/Reduce Detected Normal Area"],
                    "value": [0, 0],
                    "obj_list":["combobox:Not Use,Expand,Reduce"]
                },
            
            2: # Expand/Reduce Threshold
                {
                    "type":"Expand/Reduce kernel size (3, 5, 7, 9, 11)",
                    "tip":["label:3. Expand/Reduce kernel size (3, 5, 7, 9, 11)"],
                    "value": [3, 3],
                    "obj_list":["spinbox:3,11,3"]
                    
                },
            3: # Calibration
                {
                    "type":"Calibration",
                    "tip":["label:4. Calibration"],
                    "value": [True,True],
                    "obj_list":["toggle:"]
                    
                },
            4: # Calibration ratio
                {
                    "type":"Calibration Ratio",
                    "tip":["label:5. Calibration Ratio"],
                    "value": [1.0,1.0],
                    "obj_list":["doublespinbox:0.0,1.0,1.0"]
                    
                },
            5: # Select save label method
                {
                    "type":"Select save label method",
                    "tip":["label:6. Label Data Save"],
                    "value": [0,0],
                    "obj_list":["combobox:Create,Overwrite"]
                    
                },
        }
        self.adv_data_list_info = {

        }

        self.worker_id = -1
        self.dash = "-"
        self.mode = "Simple Auto Labeling Mode"
        self.interrupt_ = False
        self.signal_sw = True


    @pyqtSlot(dict)
    def recv_from_threading(self, output):
        """
            @description: Recv threading process result
            @author : MyoungHwan
        """
        self.worker_id = -1
        self.advanced_sal_setting_start_btn.toggle()
        self.advanced_sal_setting_start_btn.setEnabled(True)
        self.advanced_sal_setting_stop_btn.setEnabled(False)
        self.advanced_sal_setting_groupbox.setEnabled(True)
        self.advanced_sal_datalist_groupbox.setEnabled(True)


    def init_ui(self, MainWindow):
        """
            @description: 초기 변수 선언부분
            @author : MyoungHwan
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        MainWindow.setObjectName("adv_setting_form")
        MainWindow.resize(840, 640)
        MainWindow.setWindowTitle("Advanced Setting")
        MainWindow.setStyleSheet(stylesheet)

        self.advanced_simpleautolabel_main_horizon = QtWidgets.QHBoxLayout(MainWindow)
        self.advanced_simpleautolabel_main_horizon.setObjectName("advanced_simpleautolabel_main_horizon")

        self.advanced_simpleautolabel_main_vertical = QtWidgets.QVBoxLayout()
        self.advanced_simpleautolabel_main_vertical.setObjectName("advanced_simpleautolabel_main_vertical")

        self.advanced_sal_setting_groupbox = QtWidgets.QGroupBox()
        self.advanced_sal_setting_groupbox.setObjectName("advanced_sal_setting_groupbox")
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_setting_groupbox", self.advanced_sal_setting_groupbox)

        self.advanced_sal_setting_vertical = QtWidgets.QVBoxLayout()
        self.advanced_sal_setting_vertical.setObjectName("advanced_sal_setting_vertical")

        self.advanced_sal_datalist_groupbox = QtWidgets.QGroupBox()
        self.advanced_sal_datalist_groupbox.setObjectName("advanced_sal_datalist_groupbox")
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_datalist_groupbox", self.advanced_sal_datalist_groupbox)

        self.advanced_sal_datalist_vertical = QtWidgets.QVBoxLayout()
        self.advanced_sal_datalist_vertical.setObjectName("advanced_sal_datalist_vertical")

        self.advanced_sal_datalist_tableview = QtWidgets.QTableWidget()
        self.advanced_sal_datalist_tableview.setObjectName("advanced_sal_datalist_tableview")
        self.advanced_sal_datalist_tableview.setColumnCount(3)
        self.advanced_sal_datalist_tableview.setRowCount(4)
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_datalist_tableview", self.advanced_sal_datalist_tableview)
        self.advanced_sal_datalist_tableview_header = self.advanced_sal_datalist_tableview.horizontalHeader()
        self.advanced_sal_datalist_tableview_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.advanced_sal_datalist_tableview_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.advanced_sal_datalist_tableview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.advanced_sal_datalist_tableview.setDragEnabled(False)
        self.advanced_sal_datalist_tableview.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.advanced_sal_datalist_tableview.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.advanced_sal_datalist_tableview.verticalHeader().hide()

        self.advanced_sal_datalist_global_horizon = QtWidgets.QHBoxLayout()
        self.advanced_sal_datalist_global_horizon.setObjectName("advanced_sal_datalist_global_horizon")
        self.advanced_sal_datalist_global_search_btn = QtWidgets.QPushButton()
        self.advanced_sal_datalist_global_search_btn.setObjectName("advanced_sal_datalist_global_search_btn")
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_datalist_global_search_btn", self.advanced_sal_datalist_global_search_btn)
        self.advanced_sal_datalist_global_clear_btn = QtWidgets.QPushButton()
        self.advanced_sal_datalist_global_clear_btn.setObjectName("advanced_sal_datalist_global_clear_btn")
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_datalist_global_clear_btn", self.advanced_sal_datalist_global_clear_btn)
    
        self.advanced_sal_setting_horizon = QtWidgets.QHBoxLayout()
        self.advanced_sal_setting_horizon.setObjectName("advanced_sal_setting_horizon")

        self.advanced_sal_setting_start_btn = QtWidgets.QPushButton()
        self.advanced_sal_setting_start_btn.setObjectName("advanced_sal_setting_start_btn")
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_setting_start_btn", self.advanced_sal_setting_start_btn)
        self.advanced_sal_setting_start_btn.resize(150,150)
        self.advanced_sal_setting_start_btn.setCheckable(True)

        self.advanced_sal_setting_stop_btn = QtWidgets.QPushButton()
        self.advanced_sal_setting_stop_btn.setObjectName("advanced_sal_setting_stop_btn")
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_setting_stop_btn", self.advanced_sal_setting_stop_btn)
        self.advanced_sal_setting_stop_btn.resize(150,150)
        self.advanced_sal_setting_stop_btn.setEnabled(False)

        self.advanced_sal_status_vertical = QtWidgets.QVBoxLayout()
        self.advanced_sal_status_vertical.setObjectName("advanced_sal_status_vertical")
        self.advanced_sal_status_groupbox = QtWidgets.QGroupBox()
        self.advanced_sal_status_groupbox.setObjectName("advanced_sal_status_groupbox")
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_status_groupbox", self.advanced_sal_status_groupbox)

        self.advanced_sal_status_textedit = QtWidgets.QPlainTextEdit()
        self.advanced_sal_status_textedit.setReadOnly(True)
        self.advanced_sal_status_textedit.setUndoRedoEnabled(False)



    def setup_ui(self):
        """
            @description: 초기 UI 선언에 대한 설정 부분
            @author : MyoungHwan
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        self.advanced_sal_setting_groupbox.setLayout(self.advanced_sal_setting_vertical)

        self.advanced_sal_setting_horizon.addWidget(self.advanced_sal_setting_start_btn)
        self.advanced_sal_setting_horizon.addWidget(self.advanced_sal_setting_stop_btn)
        
        self.advanced_sal_datalist_global_horizon.addWidget(self.advanced_sal_datalist_global_search_btn)
        self.advanced_sal_datalist_global_horizon.addStretch()
        self.advanced_sal_datalist_global_horizon.addWidget(self.advanced_sal_datalist_global_clear_btn)

        self.advanced_sal_datalist_vertical.addLayout(self.advanced_sal_datalist_global_horizon)
        self.advanced_sal_datalist_vertical.addWidget(self.advanced_sal_datalist_tableview)
        self.advanced_sal_datalist_groupbox.setLayout(self.advanced_sal_datalist_vertical)

        self.advanced_simpleautolabel_main_vertical.addWidget(self.advanced_sal_setting_groupbox)
        self.advanced_simpleautolabel_main_vertical.addWidget(self.advanced_sal_datalist_groupbox)
        self.advanced_simpleautolabel_main_vertical.addLayout(self.advanced_sal_setting_horizon)

        self.advanced_sal_status_vertical.addWidget(self.advanced_sal_status_textedit)
        self.advanced_sal_status_groupbox.setLayout(self.advanced_sal_status_vertical)

        self.advanced_simpleautolabel_main_horizon.addLayout(self.advanced_simpleautolabel_main_vertical)
        self.advanced_simpleautolabel_main_horizon.addWidget(self.advanced_sal_status_groupbox)

    def init_function(self):
        """
            @description: Qtablewidget 영역 외 버튼 사용을 위한 signal 정의 부분
            @author : MyoungHwan
        """
        self.advanced_sal_datalist_global_search_btn.clicked.connect(lambda : self.button_datalist_event(mode=0, obj=self.advanced_sal_datalist_global_search_btn))
        self.advanced_sal_datalist_global_clear_btn.clicked.connect(lambda : self.button_datalist_event(mode=1, obj=self.advanced_sal_datalist_global_clear_btn))
        self.advanced_sal_setting_start_btn.clicked.connect(lambda : self.button_event(mode=0))
        self.advanced_sal_setting_stop_btn.clicked.connect(lambda : self.button_event(mode=1))

    def create_obj(self, idx, obj_type="widget",obj_list=["button:testbtn"], layout="horizon"):
        """
            @description: Qtable UI 생성시 Item 추가를 위한 object 생성 부분
            @author : MyoungHwan
        """
        if obj_type == "item":
            tmp_qitem = QtWidgets.QTableWidgetItem(obj_list)
            tmp_qitem.setTextAlignment(QtCore.Qt.AlignCenter)
            return tmp_qitem
        elif obj_type== "widget":
            tmp_obj_dict_ = {}
            # layout
            tmp_qwidget = QtWidgets.QWidget()
            if layout=="horizon":
                tmp_qlayout = QtWidgets.QHBoxLayout()

            for obj_ in obj_list:
                object_, value_ = obj_.split(":")
                if object_ == "button":
                    tmp_qbtn = QtWidgets.QPushButton()
                    tmp_qbtn.setObjectName(f"{idx}_tmp_qbtn")
                    tmp_qbtn.setText(value_)
                    tmp_obj_dict_["button"] = tmp_qbtn
                    tmp_qlayout.addWidget(tmp_qbtn)
                
                elif object_ == "toggle":
                    tmp_qtogglebox = AnimatedToggle(
                        pulse_checked_color="transparent",
                        pulse_unchecked_color="transparent"
                    )
                    tmp_qtogglebox.setObjectName(f"{idx}_tmp_qtogglebox")
                    tmp_qtogglebox.setFixedWidth(100)
                    tmp_obj_dict_["toggle"] = tmp_qtogglebox
                    tmp_qlayout.addWidget(tmp_qtogglebox)
                
                elif object_ == "spinbox":
                    minv, maxv, curv = list(map(int, value_.split(",")))
                    tmp_qspinbox = QtWidgets.QSpinBox()
                    tmp_qspinbox.setObjectName(f"{idx}_tmp_qspinbox")
                    tmp_qspinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
                    tmp_qspinbox.setRange(minv, maxv)
                    tmp_qspinbox.setFixedWidth(100)
                    tmp_qspinbox.setValue(curv)
                    tmp_qspinbox.setSingleStep(2)
                    tmp_qspinbox.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["spinbox"] = tmp_qspinbox
                    tmp_qlayout.addWidget(tmp_qspinbox)

                elif object_ == "doublespinbox":
                    minv, maxv, curv = list(map(float, value_.split(",")))
                    tmp_qdoublespinbox = QtWidgets.QDoubleSpinBox()
                    tmp_qdoublespinbox.setObjectName(f"{idx}_tmp_qdoublespinbox")
                    tmp_qdoublespinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
                    tmp_qdoublespinbox.setRange(minv, maxv)
                    tmp_qdoublespinbox.setFixedWidth(100)
                    tmp_qdoublespinbox.setValue(curv)
                    tmp_qdoublespinbox.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["spinbox"] = tmp_qdoublespinbox
                    tmp_qlayout.addWidget(tmp_qdoublespinbox)

                elif object_ == "label":
                    tmp_qlabel = QtWidgets.QLabel()
                    tmp_qlabel.setObjectName(f"{idx}_tmp_qlabel")
                    tmp_qlabel.setText(value_)
                    tmp_qlabel.setFixedWidth(tmp_qlabel.width() + 50)
                    tmp_obj_dict_["label"] = tmp_qlabel
                    tmp_qlayout.addWidget(tmp_qlabel)
                
                elif object_ == "lineedit":
                    tmp_qlineedit = QtWidgets.QLineEdit()
                    tmp_qlineedit.setObjectName(f"{idx}_tmp_qlineedit")
                    tmp_qlineedit.setReadOnly(True)
                    tmp_qlineedit.setDragEnabled(True)
                    tmp_qlineedit.setText(value_)
                    tmp_qlineedit.setMinimumWidth(350)
                    tmp_qlineedit.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["lineedit"] = tmp_qlineedit
                    tmp_qlayout.addWidget(tmp_qlineedit)
                
                elif object_ == "combobox":
                    combo_qitems = value_.split(",")
                    tmp_qcombobox = QtWidgets.QComboBox()
                    tmp_qcombobox.setObjectName(f"{idx}_tmp_qcombobox")
                    tmp_qcombobox.addItems(combo_qitems)
                    tmp_obj_dict_["combobox"] = tmp_qcombobox
                    tmp_qlayout.addWidget(tmp_qcombobox)

            tmp_qwidget.setLayout(tmp_qlayout)
            tmp_obj_dict_["widget"] = tmp_qwidget
            return tmp_obj_dict_


    def fill_table(self):
        """
            @description: 기능에 대한 Ui 생성
            @author : MyoungHwan
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        for idx, value in enumerate(self.adv_model_info.values()):
            self.header_dict_[idx] = {
                "obj_tip":self.create_obj(idx, obj_type="widget", obj_list=value["tip"]),
                "obj_set":self.create_obj(idx, obj_type="widget", obj_list=value["obj_list"])
            }
            tmp_horizon = QtWidgets.QHBoxLayout()
            tmp_horizon.setContentsMargins(3,3,3,3)
            tmp_horizon.addWidget(self.header_dict_[idx]["obj_tip"]["widget"])
            tmp_horizon.addStretch()
            tmp_horizon.addWidget(self.header_dict_[idx]["obj_set"]["widget"])
            self.header_dict_[idx]['obj'] = tmp_horizon

        for row, value in enumerate(self.header_dict_.values()):
            self.advanced_sal_setting_vertical.addLayout(value["obj"])


        self.header_dict_[0]["obj_set"]["combobox"].currentIndexChanged.connect(lambda value=self.header_dict_[0]["obj_set"]["combobox"], tmp_idx=0: self.valuechange_event(idx=tmp_idx,  value=value))
        
        self.header_dict_[1]["obj_set"]["combobox"].currentIndexChanged.connect(lambda value=self.header_dict_[1]["obj_set"]["combobox"], tmp_idx=1: self.valuechange_event(idx=tmp_idx,  value=value))
        
        self.header_dict_[2]["obj_set"]["spinbox"].valueChanged.connect(lambda value=self.header_dict_[2]["obj_set"]["spinbox"], tmp_idx=2: self.valuechange_event(idx=tmp_idx,  value=value))
        self.header_dict_[2]["obj_set"]["spinbox"].setEnabled(False)


        #object specific setting
        self.header_dict_[3]["obj_set"]["toggle"].setChecked(True)
        
        #object function specific setting(checkbox)
        self.header_dict_[3]["obj_set"]["toggle"].toggled.connect(lambda ch=self.header_dict_[3]["obj_set"]["toggle"], tmp_idx=3 : self.toggle_event(mode=0, idx=tmp_idx, ch=ch, obj=self.header_dict_[4]))
        
        self.header_dict_[4]["obj_set"]["spinbox"].valueChanged.connect(lambda value=self.header_dict_[4]["obj_set"]["spinbox"], tmp_idx=4: self.valuechange_event(idx=tmp_idx, value=value))
        self.header_dict_[5]["obj_set"]["combobox"].currentIndexChanged.connect(lambda value=self.header_dict_[5]["obj_set"]["combobox"], tmp_idx=5: self.valuechange_event(idx=tmp_idx,  value=value))

        # 1. select standard normal label
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_selectlabel_label", self.header_dict_[0]["obj_tip"]["label"])
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_selectlabel_combobox", self.header_dict_[0]["obj_set"]["combobox"])
        
        # 2. expand/reduce detectd normal area
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_detectedscale_label", self.header_dict_[1]["obj_tip"]["label"])
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_detectedscale_combobox", self.header_dict_[1]["obj_set"]["combobox"])

        # 3. expand/reduce kernel size
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_kernelsize_label", self.header_dict_[2]["obj_tip"]["label"])

        # 4. calibration
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_calibration_label", self.header_dict_[3]["obj_tip"]["label"])

        # 5. calibration ratio
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_calibrationratio_label", self.header_dict_[4]["obj_tip"]["label"])

        # 6. label source
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_labelsource_label", self.header_dict_[5]["obj_tip"]["label"])    
        self.lang.set("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_labelsource_combobox", self.header_dict_[5]["obj_set"]["combobox"])    

    def valuechange_event(self, idx, value):
        """
            @description: combobox, spinbox 위젯의 value change에 대한 시그널발생시 발동되는 함수
            @author : MyoungHwan
        """
        if self.signal_sw:
            self.signal_sw = False
            if idx == 0: # Standard Normal type
                self.adv_model_info[0]["value"][1] = value 
            elif idx == 1: # Expand/Reduce
                self.adv_model_info[1]["value"][1] = value
                if value == 0: # Not use
                    self.header_dict_[2]["obj_set"]["spinbox"].setEnabled(False)
                else: # Expand/Reduce
                    self.header_dict_[2]["obj_set"]["spinbox"].setEnabled(True)
            elif idx == 2: # Threshold spinbox
                if value % 2 == 0:
                    value -= 1 
                    value_list = self.adv_model_info[2]["obj_list"][0].split(":")[-1]
                    min_, max_, _ = list(map(int, value_list.split(",")))
                    value = max(min_, min(value, max_))
                    self.header_dict_[2]["obj_set"]["spinbox"].setValue(value)
                self.adv_model_info[2]["value"][1] = value
            elif idx == 4: # calibration ratio
                self.adv_model_info[4]["value"][1] = value
            elif idx == 5: # save label method
                self.adv_model_info[5]["value"][1] = value
            self.signal_sw = True


    def toggle_event(self, mode, idx, ch, obj=None):
        """
            @description: 토글버튼 시그널발생시 발동되는 함수
            @author : MyoungHwan
        """
        if mode == 0: # setting mode
            if idx == 3: #calibration toggle
                if ch:
                    if obj["obj_set"]["spinbox"].isEnabled() == 0:
                        obj["obj_set"]["spinbox"].setEnabled(True)
                        obj["obj_set"]["spinbox"].setValue(self.adv_model_info[4]["value"][1])
                        self.adv_model_info[idx]["value"][1] = True
                else:
                    if obj["obj_set"]["spinbox"].isEnabled():
                        obj["obj_set"]["spinbox"].setEnabled(False)
                        self.adv_model_info[idx]["value"][1] = False

        elif mode == 1: # datalist mode
            if ch:
                self.adv_data_list_info[idx]['use'] = True
            else:
                self.adv_data_list_info[idx]['use'] = False


    def button_setting_event(self, mode, obj):
        """
            @description: 셋팅버튼 시그널발생시 발동되는 함수
            @author : MyoungHwan
        """
        if mode == 0: # select model
            file_dialog = QtWidgets.QFileDialog()
            fname = file_dialog.getOpenFileName(self,"파일 선택","","Files (*.el)")
            if fname[0]:
                self.adv_model_info[mode]["value"][1] = fname[0]
                obj["obj_set"]["lineedit"].setText(str(self.adv_model_info[mode]["value"][1]))
                obj["obj_set"]["lineedit"].setToolTip(str(self.adv_model_info[mode]["value"][1]))


    def button_datalist_event(self, mode, obj):
        """
            @description: 데이터 search 버튼 시그널발생시 발동되는 함수
            @author : MyoungHwan
        """
        if mode == 0: # Search
            file_dialog = QtWidgets.QFileDialog()
            file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
            file_dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            file_dialog.findChild(QtWidgets.QListView, 'listView').setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            file_dialog.findChild(QtWidgets.QTreeView, 'treeView').setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            if file_dialog.exec_():
                fname = file_dialog.selectedFiles()
                if len(fname):
                    cur_data_len = len(self.adv_data_list_info.keys())
                    add_data_list = []
                    for tmp_flist in fname:
                        tmp_path = f"{tmp_flist}/**/data.hdr"
                        tmp_lists = sorted(glob.glob(tmp_path, recursive=True), key=len)
                        tmp_lists = list(map(lambda x:x.replace("\\","/"), tmp_lists))
                        tmp_lists = list(map(lambda x:x.split("/data.hdr")[0], tmp_lists))
                        for tmp_list in tmp_lists:
                            if tmp_list in self.adv_data_list_info.keys():
                                print("data conflict!", tmp_list)
                                continue
                            add_data_list.append(tmp_list)
                    self.advanced_sal_datalist_tableview.setRowCount(cur_data_len + len(add_data_list))
                    
                    tmp_data_list_info = {}
                    for idx, tmp_data in enumerate(add_data_list):
                        tmp_idx = cur_data_len + idx
                        tmp_data_list_info[tmp_data] = {
                            "idx":tmp_idx,
                            "use":True,
                            "obj_idx":self.create_obj(tmp_idx, obj_type="item", obj_list=str(tmp_idx)),
                            "obj_path":self.create_obj(tmp_idx, obj_type="item", obj_list=tmp_data),
                            "obj_set":self.create_obj(tmp_idx, obj_type="widget", obj_list=["toggle:"])
                        }

                    for key, value in tmp_data_list_info.items():
                        cur_row_cnt = self.advanced_sal_datalist_tableview.rowCount()
                        for tmp_row in range(cur_row_cnt):
                            tmp_item = self.advanced_sal_datalist_tableview.item(tmp_row,0)
                            if not tmp_item:
                                self.advanced_sal_datalist_tableview.setItem(tmp_row, 0, value["obj_idx"])
                                self.advanced_sal_datalist_tableview.setItem(tmp_row, 1, value["obj_path"])
                                self.advanced_sal_datalist_tableview.setCellWidget(tmp_row, 2, value["obj_set"]["widget"])
                                value["obj_set"]["toggle"].setChecked(True)
                                value["obj_set"]["toggle"].toggled.connect(lambda ch, tmp_row2=key, tmp_value=value : self.toggle_event(mode=1, idx=tmp_row2, ch=ch, obj=tmp_value))
                                break
                    self.adv_data_list_info.update(tmp_data_list_info)

        elif mode == 1: # Clear
            self.clear_event()
            
    
    def button_event(self, mode):
        """
            @description: 기능 실행/정지 버튼 시그널발생시 발동되는 함수
            @author : MyoungHwan
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
                2. Yugyeong Hong(2026.02.24): Refactor message box with util method and language support
        """
        if mode == 0: #start
            if self.worker_id == -1 :
                self.advanced_sal_setting_start_btn.setEnabled(False)
                self.advanced_sal_setting_stop_btn.setEnabled(True)
                self.advanced_sal_setting_groupbox.setEnabled(False)
                self.advanced_sal_datalist_groupbox.setEnabled(False)

                self.advanced_sal_status_textedit.clear()
                mode_string = f"{self.mode}\n{self.dash* 30}"
                self.advanced_sal_status_textedit.appendPlainText(mode_string)
                self.advanced_sal_status_textedit.appendPlainText("Parameter Setting\n")
                for idx, value in enumerate(self.adv_model_info.values()):
                    tmp_type = value["type"]
                    tmp_value = value["value"][1]
                    tmp_string = f"{idx+1}. {tmp_type} : {tmp_value}\n"
                    self.advanced_sal_status_textedit.appendPlainText(tmp_string)
                self.advanced_sal_status_textedit.appendPlainText(self.dash*30)
                self.advanced_sal_status_textedit.appendPlainText("Predict Data List\n")
                self.advanced_sal_status_textedit.appendPlainText(f"Total: {len(self.adv_data_list_info.keys())}\n")
                self.advanced_sal_status_textedit.appendPlainText(f"Processing Start....\n")
                self.worker_1.staging(self.predict_label_mode)
                self.worker_id = self.worker_1.cur_id
                self.worker_1.start()
            else:
                messageBox(
                    mode=MESSAGE_BOX_WARNING,
                    title=self.lang.get("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_msg_warning_already_allocated_title"),
                    text=f'{self.lang.get("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_msg_warning_already_allocated_message")} Worker ID:{self.worker_id}',
                    buttons = {self.lang.get("main", "messageBox", "msgOk"):"accept"}
                )


        elif mode == 1: #stop
            response = messageBox(
                mode=MESSAGE_BOX_CONFIRMATION,
                title=self.lang.get("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_msg_stop_title"),
                text=self.lang.get("advanced", "advanced_simpleautolabel_main", "advanced_simpleautolabel_msg_stop_message"),
                buttons={self.lang.get("main", "messgaeBox", "msgYes"): "accept", self.lang.get("main", "messgaeBox", "msgNo"): "reject"}
            )
            if response == "accept":
                self.interrupt_ = True


    def predict_label_mode(self) -> None:
        """
            @description: SAL 기능 실행 및 상태 표시를 위한 함수
            @author : MyoungHwan
        """
        gen = gen_module()
        normal_label = self.adv_model_info[0]['value'][1]
        preproc_mode = self.adv_model_info[1]["value"][1]
        preproc_kernel = self.adv_model_info[2]["value"][1]
        calibration = self.header_dict_[3]["obj_set"]["toggle"].isChecked()
        calibration_ratio = self.adv_model_info[4]["value"][1]
        saveLabelMethod = self.adv_model_info[5]["value"][1]  # 0: Create, 1: Overwrite
        try:
            data_path_list = []
            for key, value in self.adv_data_list_info.items():
                if value["use"]:
                    data_path_list.append(key)
            if len(data_path_list) == 0:
                raise Exception("data path is empty")
            result = self.predict_data(gen=gen, data_list=data_path_list, 
                                            calibration=calibration, calibration_rate=calibration_ratio, normal_label=normal_label,
                                            preproc_mode=preproc_mode , preproc_kernel=preproc_kernel,
                                            saveLabelMethod=saveLabelMethod
                                            )
            for cur_value in result:
                tmp_status, tmp_string = cur_value
                self.string_signal.emit(tmp_string)
        except Exception as e:
            self.string_signal.emit(f"Error Occured...{str(e)} Best Top\n")
        finally:
            self.string_signal.emit(f"\nProcessing Finish...\n")

    def predict_data(self, gen,
                     data_list="" ,
                     calibration=True, calibration_rate=1.0, normal_label=0,
                     preproc_mode=0 , preproc_kernel=0,
                     label_dir="/label.npy",predict_label_dir="/label_SAL.npy", predict_count=100, saveLabelMethod=0
                     ):
        """
            @description: Simple Auto Labeling이 실행되는 함수
            @author : MyoungHwan
            @parameters
                1. normal_label: 두 스펙트럼을 비교하여 크기에 따라 기준 라벨 정의
                    0 : 두 스펙트럼 비교 시 크기가 작은 스펙트럼을 기준으로 설정
                    1 : 두 스펙트럼 비교 시 크기가 큰 스펙트럼을 기준으로 설정
                
                2. preproc_mode: normal label 기준으로 확장/축소 수행 여부
                    0 : 확장/축소 수행 안함
                    1 : 확장
                    2 : 축소

                3. preproc_kernel: 확장/축소 사용 시 커널 사이즈
                    k : k x k 사이즈로 확장/축소

                4. predict_count: SAL 수행후 기준이 되는 라벨의 번호
                    100 :  100으로 라벨이 생성됨
        """
        for idx, _list in enumerate(data_list):
            try:
                if self.interrupt_:
                    self.interrupt_ = False
                    yield [True, f"Process Stop."]
                    break
                total_len = len(data_list)
                file_path = _list.split("data.hdr")[0]
                yield [True, f"\n{idx}. {file_path} ({idx+1}/{total_len})"]
                data = gen.load_data(file_path, calibration=calibration, calibration_rate=calibration_rate)
                width, height, _ = data.shape
                if os.path.isfile(file_path+label_dir):
                    label=np.load(file_path+label_dir).reshape(width*height)
                else:
                    label=np.zeros((width,height)).reshape(width*height)
                if 100 in np.unique(label):
                    np.save(file_path + "/label_origin.npy", label.reshape(width, height))
                result = simplelabeling(data, label)
                if result[0]:
                    _, indices, cluster_centers, predict_result = result
                    """
                        1번 라벨 기준으로 kernel 처리가 되므로 기준을 1로 조정해야함
                    """
                    yield [True, f"Normal label: {normal_label}"]
                    if np.sum(cluster_centers[0] - cluster_centers[1] > 0) >= np.sum(cluster_centers[1] - cluster_centers[0] > 0):
                        # 0번 스펙트럼이 큰놈일 때 
                        if normal_label == 1:  # 큰놈을 기준으로 할때
                            predict_result = 1 - predict_result
                            # yield [True, f"swapp, 0번 스펙트럼이 1번보다 더 큼, 큰놈을 기준으로 정했기 때문에 0번을 1번으로 "]

                    elif np.sum(cluster_centers[0] - cluster_centers[1] > 0) < np.sum(cluster_centers[1] - cluster_centers[0] > 0):
                        # 1번 스펙트럼이 큰놈일 때
                        if normal_label == 0:  # 작은놈을 기준으로 할때
                            predict_result = 1 - predict_result
                            # yield [True, f"swapp, 0번 스펙트럼이 1번보다 더 작음, 작은놈을 기준으로 정했기 때문에 0번을 1번으로 "]

                    if preproc_mode == 0: # not use
                        label[indices] = predict_result * predict_count
                        yield [True, f"Only Simple Labeling Mode"]
                    else:
                        tmp_qlabel = np.zeros((width*height))
                        tmp_qlabel[indices] = predict_result * predict_count
                        tmp_qlabel = np.where(tmp_qlabel==predict_count,1,0)
                        tmp_qlabel = tmp_qlabel.reshape(width,height).astype('uint8')
                        tmp_kernel = np.ones((preproc_kernel,preproc_kernel), np.uint8)
                        if preproc_mode == 1: # expand
                            tmp_qlabel_result = cv2.dilate(tmp_qlabel, tmp_kernel, iterations=1)
                            yield [True, f"Expand, kernel size: {preproc_kernel}"]
                        elif preproc_mode == 2: # reduce
                            tmp_qlabel_result = cv2.erode(tmp_qlabel, tmp_kernel, iterations=1) 
                            yield [True, f"Reduce, kernel size: {preproc_kernel}"]
                        tmp_qlabel_result = tmp_qlabel_result.reshape(width*height)
                        tmp_indice = np.where(tmp_qlabel_result==1) # 2D
                        label[tmp_indice] = predict_count

                    label = label.reshape(width, height)
                    if saveLabelMethod == 0:  # Create
                        np.save(file_path + predict_label_dir, label)
                        yield [True, f"save complete Simple Auto Labeling ({predict_label_dir}) result"]
                    elif saveLabelMethod == 1:  # Overwrite
                        np.save(file_path + label_dir, label)
                        yield [True, f"save complete Simple Auto Labeling ({label_dir}) result"]
                
                elif result[0] == 0:
                    _, error_msg = result
                    yield [True, f"Error occured...{error_msg}, Sub"]

            except Exception as e:
                tmp_str = f"Error Occured...{str(e)}, Top"
                yield [False, tmp_str]



    def clear_event(self):
        """
            @description: 데이터 리스트 초기화 하는 부분
            @author : MyoungHwan
        """
        self.advanced_sal_datalist_tableview.clear()
        self.advanced_sal_datalist_tableview.setRowCount(4)
        self.advanced_sal_datalist_tableview.setHorizontalHeaderLabels(["Index", "Data", "Use"])
        self.adv_data_list_info = {}

    def update_status(self, string_):
        """
            @description: 기능 상태에 대한 텍스트를 업데이트 하는 함수
            @author : MyoungHwan
        """
        self.advanced_sal_status_textedit.appendPlainText(string_)

    def showEvent(self, e):
        pass

    def closeEvent(self, e):
        pass




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = advanced_sal_Form()
    sys.exit(app.exec_())
