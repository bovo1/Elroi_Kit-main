"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from utils.worker import Threading_Worker
from qtwidgets import AnimatedToggle
import spectral
import numpy as np
import os
import glob
import datetime

from advanced.stylesheet.stylesheet_adv_label_optimization_mode import stylesheet


class signal_(QtCore.QObject):
    string_signal = QtCore.pyqtSignal(str)

class advanced_label_optimization_Form(QtWidgets.QWidget):
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
            @author : JiHoon
            @parameters
                - self.header_dict : 기능설정에 대한 오브젝트를 딕셔너리형태로 저장
                - self.adv_model_info : 기능설정에 대한 정보를 딕셔너리형태로 저장
                    0: hyperspectra에 대한 정보
                    1: 원물에 대한 정보
                    2: 데이터 생성 후 저장할 경로
                    2: Calibration 설정
                    3: Calibration Ratio 설정
                - self.adv_data_list_info : 기능을 적용할 데이터 대상리스트를 딕셔너리형태로 저장
                - self.worker_id : 기능 병렬처리를 위해 할당된 ID
                - self.dash: Qplaintextedit에 보여줄 특수문자
                - self.mode: 기능에 대한 명
                - self.interrupt_: 쓰레딩 중간 정지를 위한 스위칭 변수
                - self.signal_sw: 시그널 발동시 동시처리를 방지하기 위한 스위칭 변수
        """
        self.header_dict_ = {}

        self.adv_model_info = {
            0: # VNIR/NIR Select
                {
                    "type":"Hyperspectra",
                    "tip":["label:1. Hyperspectra"],
                    "value": [0, 0],
                    "obj_list":["combobox:VNIR,NIR"]
                },
            
            1: # Raw Ingredient
                {
                    "type": "Raw Ingredient",
                    "tip": ["label:2. Raw Ingredient"],
                    "value": "",
                    "obj_list": ["textbox:"]
                },

            2: # model
                {
                    "type":"Save Path",
                    "tip":["label:3. Save Path"],
                    "value": ["-",""],
                    "obj_list":["lineedit:path", "button:Load" ]
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
                    "obj_list":["spinbox:0.0,1.0,1.0"]
                },

        }
        self.adv_data_list_info = {

        }

        self.worker_id = -1
        self.dash = "-"
        self.mode = "Label Optimization Mode"
        self.interrupt_ = False
        self.signal_sw = True


    @pyqtSlot(dict)
    def recv_from_threading(self, output):
        """
            @description: Recv threading process result
            @author : JiHoon
        """
        self.worker_id = -1
        self.advanced_label_optimization_setting_start_btn.toggle()
        self.advanced_label_optimization_setting_start_btn.setEnabled(True)
        self.advanced_label_optimization_setting_stop_btn.setEnabled(False)
        self.advanced_label_optimization_setting_groupbox.setEnabled(True)
        self.advanced_label_optimization_datalist_groupbox.setEnabled(True)


    def init_ui(self, MainWindow):
        """
            @description: 초기 변수 선언부분
            @author : JiHoon
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        MainWindow.setObjectName("adv_setting_form")
        MainWindow.resize(840, 640)
        MainWindow.setWindowTitle("Advanced Setting")
        MainWindow.setStyleSheet(stylesheet)

        self.advanced_label_optimization_main_horizon = QtWidgets.QHBoxLayout(MainWindow)
        self.advanced_label_optimization_main_horizon.setObjectName("advanced_label_optimization_main_horizon")

        self.advanced_label_optimization_main_vertical = QtWidgets.QVBoxLayout()
        self.advanced_label_optimization_main_vertical.setObjectName("advanced_label_optimization_main_vertical")

        self.advanced_label_optimization_setting_groupbox = QtWidgets.QGroupBox()
        self.advanced_label_optimization_setting_groupbox.setObjectName("advanced_label_optimization_setting_groupbox")
        self.advanced_label_optimization_setting_groupbox.setFixedWidth(933)        
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_setting_groupbox", self.advanced_label_optimization_setting_groupbox)

        self.advanced_label_optimization_setting_vertical = QtWidgets.QVBoxLayout()
        self.advanced_label_optimization_setting_vertical.setObjectName("advanced_label_optimization_setting_vertical")

        self.advanced_label_optimization_datalist_groupbox = QtWidgets.QGroupBox()
        self.advanced_label_optimization_datalist_groupbox.setObjectName("advanced_label_optimization_datalist_groupbox")
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_datalist_groupbox", self.advanced_label_optimization_datalist_groupbox)

        self.advanced_label_optimization_datalist_vertical = QtWidgets.QVBoxLayout()
        self.advanced_label_optimization_datalist_vertical.setObjectName("advanced_label_optimization_datalist_vertical")

        self.advanced_label_optimization_datalist_tableview = QtWidgets.QTableWidget()
        self.advanced_label_optimization_datalist_tableview.setObjectName("advanced_label_optimization_datalist_tableview")
        self.advanced_label_optimization_datalist_tableview.setColumnCount(3)
        self.advanced_label_optimization_datalist_tableview.setRowCount(4)
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_datalist_tableview", self.advanced_label_optimization_datalist_tableview)
        self.advanced_label_optimization_datalist_tableview_header = self.advanced_label_optimization_datalist_tableview.horizontalHeader()
        self.advanced_label_optimization_datalist_tableview_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.advanced_label_optimization_datalist_tableview_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.advanced_label_optimization_datalist_tableview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.advanced_label_optimization_datalist_tableview.setDragEnabled(False)
        self.advanced_label_optimization_datalist_tableview.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.advanced_label_optimization_datalist_tableview.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.advanced_label_optimization_datalist_tableview.verticalHeader().hide()

        self.advanced_label_optimization_datalist_global_horizon = QtWidgets.QHBoxLayout()
        self.advanced_label_optimization_datalist_global_horizon.setObjectName("advanced_label_optimization_datalist_global_horizon")
        self.advanced_label_optimization_datalist_global_search_btn = QtWidgets.QPushButton()
        self.advanced_label_optimization_datalist_global_search_btn.setObjectName("advanced_label_optimization_datalist_global_search_btn")
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_datalist_global_search_btn", self.advanced_label_optimization_datalist_global_search_btn)
        self.advanced_label_optimization_datalist_global_clear_btn = QtWidgets.QPushButton()
        self.advanced_label_optimization_datalist_global_clear_btn.setObjectName("advanced_label_optimization_datalist_global_clear_btn")
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_datalist_global_clear_btn", self.advanced_label_optimization_datalist_global_clear_btn)
    
        self.advanced_label_optimization_setting_horizon = QtWidgets.QHBoxLayout()
        self.advanced_label_optimization_setting_horizon.setObjectName("advanced_label_optimization_setting_horizon")

        self.advanced_label_optimization_setting_start_btn = QtWidgets.QPushButton()
        self.advanced_label_optimization_setting_start_btn.setObjectName("advanced_label_optimization_setting_start_btn")
        self.advanced_label_optimization_setting_start_btn.resize(150,150)
        self.advanced_label_optimization_setting_start_btn.setCheckable(True)
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_setting_start_btn", self.advanced_label_optimization_setting_start_btn)

        self.advanced_label_optimization_setting_stop_btn = QtWidgets.QPushButton()
        self.advanced_label_optimization_setting_stop_btn.setObjectName("advanced_label_optimization_setting_stop_btn")
        self.advanced_label_optimization_setting_stop_btn.resize(150,150)
        self.advanced_label_optimization_setting_stop_btn.setEnabled(False)
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_setting_stop_btn", self.advanced_label_optimization_setting_stop_btn)

        self.advanced_label_optimization_status_vertical = QtWidgets.QVBoxLayout()
        self.advanced_label_optimization_status_vertical.setObjectName("advanced_label_optimization_status_vertical")
        self.advanced_label_optimization_status_groupbox = QtWidgets.QGroupBox()
        self.advanced_label_optimization_status_groupbox.setObjectName("advanced_label_optimization_status_groupbox")
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_status_groupbox", self.advanced_label_optimization_status_groupbox)

        self.advanced_label_optimization_status_textedit = QtWidgets.QPlainTextEdit()
        self.advanced_label_optimization_status_textedit.setReadOnly(True)
        self.advanced_label_optimization_status_textedit.setUndoRedoEnabled(False)



    def setup_ui(self):
        """
            @description: 초기 UI 선언에 대한 설정 부분
            @author : JiHoon
        """
        self.advanced_label_optimization_setting_groupbox.setLayout(self.advanced_label_optimization_setting_vertical)

        self.advanced_label_optimization_setting_horizon.addWidget(self.advanced_label_optimization_setting_start_btn)
        self.advanced_label_optimization_setting_horizon.addWidget(self.advanced_label_optimization_setting_stop_btn)
        
        self.advanced_label_optimization_datalist_global_horizon.addWidget(self.advanced_label_optimization_datalist_global_search_btn)
        self.advanced_label_optimization_datalist_global_horizon.addStretch()
        self.advanced_label_optimization_datalist_global_horizon.addWidget(self.advanced_label_optimization_datalist_global_clear_btn)

        self.advanced_label_optimization_datalist_vertical.addLayout(self.advanced_label_optimization_datalist_global_horizon)
        self.advanced_label_optimization_datalist_vertical.addWidget(self.advanced_label_optimization_datalist_tableview)
        self.advanced_label_optimization_datalist_groupbox.setLayout(self.advanced_label_optimization_datalist_vertical)

        self.advanced_label_optimization_main_vertical.addWidget(self.advanced_label_optimization_setting_groupbox)
        self.advanced_label_optimization_main_vertical.addWidget(self.advanced_label_optimization_datalist_groupbox)
        self.advanced_label_optimization_main_vertical.addLayout(self.advanced_label_optimization_setting_horizon)

        self.advanced_label_optimization_status_vertical.addWidget(self.advanced_label_optimization_status_textedit)
        self.advanced_label_optimization_status_groupbox.setLayout(self.advanced_label_optimization_status_vertical)

        self.advanced_label_optimization_main_horizon.addLayout(self.advanced_label_optimization_main_vertical)
        self.advanced_label_optimization_main_horizon.addWidget(self.advanced_label_optimization_status_groupbox)

    def init_function(self):
        """
            @description: Qtablewidget 영역 외 버튼 사용을 위한 signal 정의 부분
            @author : Jihoon
        """
        self.advanced_label_optimization_datalist_global_search_btn.clicked.connect(lambda : self.button_datalist_event(mode=0, obj=self.advanced_label_optimization_datalist_global_search_btn))
        self.advanced_label_optimization_datalist_global_clear_btn.clicked.connect(lambda : self.button_datalist_event(mode=1, obj=self.advanced_label_optimization_datalist_global_clear_btn))
        self.advanced_label_optimization_setting_start_btn.clicked.connect(lambda : self.button_event(mode=0))
        self.advanced_label_optimization_setting_stop_btn.clicked.connect(lambda : self.button_event(mode=1))

    def create_obj(self, idx, obj_type="widget", obj_list=["button:testbtn"], layout="horizon"):
        """
        @description: Qtable UI 생성시 Item 추가를 위한 object 생성 부분
        @author : Jihoon
        """
        if obj_type == "item":
            tmp_qitem = QtWidgets.QTableWidgetItem(obj_list)
            tmp_qitem.setTextAlignment(QtCore.Qt.AlignCenter)
            return tmp_qitem
        elif obj_type == "widget":
            tmp_obj_dict_ = {}
            tmp_qwidget = QtWidgets.QWidget()
            tmp_qlayout = QtWidgets.QHBoxLayout()

            for obj_ in obj_list:
                try:
                    object_, value_ = obj_.split(":")
                except ValueError:
                    print(f"Warning: '{obj_}' is not in the expected format 'object:value'. Skipping.")
                    continue
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
                    minv, maxv, curv = list(map(float, value_.split(",")))
                    tmp_spinbox = QtWidgets.QDoubleSpinBox()
                    tmp_spinbox.setObjectName(f"{idx}_tmp_spinbox")
                    tmp_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)  # 버튼 활성화
                    tmp_spinbox.setRange(minv, maxv)
                    tmp_spinbox.setFixedWidth(100)
                    tmp_spinbox.setValue(curv)
                    tmp_spinbox.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["spinbox"] = tmp_spinbox
                    tmp_qlayout.addWidget(tmp_spinbox)

                elif object_ == "doublespinbox":
                    minv, maxv, curv = list(map(float, value_.split(",")))  # float으로 유지
                    tmp_qdoublespinbox = QtWidgets.QDoubleSpinBox()
                    tmp_qdoublespinbox.setObjectName(f"{idx}_tmp_qdoublespinbox")
                    tmp_qdoublespinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)  # 버튼 활성화
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
                    tmp_qlineedit.setReadOnly(False)  # 읽기 전용 해제
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
                    tmp_qcombobox.setFixedWidth(100)

                    # 편집 가능하게 만들고 내부 lineEdit을 가져와 중앙 정렬 설정
                    tmp_qcombobox.setEditable(True)
                    line_edit = tmp_qcombobox.lineEdit()
                    line_edit.setAlignment(QtCore.Qt.AlignCenter)
                    line_edit.setReadOnly(True)  # 편집을 방지하기 위해 ReadOnly 설정

                    tmp_obj_dict_["combobox"] = tmp_qcombobox
                    tmp_qlayout.addWidget(tmp_qcombobox)

                elif object_ == "textbox":  # 새로운 조건 추가
                    tmp_qtextbox = QtWidgets.QLineEdit()
                    tmp_qtextbox.setObjectName(f"{idx}_tmp_qtextbox")
                    tmp_qtextbox.setText(value_)
                    tmp_qtextbox.setMinimumWidth(150)
                    tmp_qtextbox.setAlignment(QtCore.Qt.AlignLeft)
                    tmp_obj_dict_["textbox"] = tmp_qtextbox
                    tmp_qlayout.addWidget(tmp_qtextbox)

            tmp_qwidget.setLayout(tmp_qlayout)
            tmp_obj_dict_["widget"] = tmp_qwidget
            return tmp_obj_dict_


    def fill_table(self):
        """
        @description: 기능에 대한 UI 생성
        @author : Jihoon
        @history :
            1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        for idx, value in enumerate(self.adv_model_info.values()):
            self.header_dict_[idx] = {
                "obj_tip": self.create_obj(idx, obj_type="widget", obj_list=value["tip"]),
                "obj_set": self.create_obj(idx, obj_type="widget", obj_list=value["obj_list"])
            }
            tmp_horizon = QtWidgets.QHBoxLayout()
            tmp_horizon.setContentsMargins(3, 3, 3, 3)
            tmp_horizon.addWidget(self.header_dict_[idx]["obj_tip"]["widget"])
            tmp_horizon.addStretch()
            tmp_horizon.addWidget(self.header_dict_[idx]["obj_set"]["widget"])
            self.header_dict_[idx]['obj'] = tmp_horizon

        for row, value in enumerate(self.header_dict_.values()):
            self.advanced_label_optimization_setting_vertical.addLayout(value["obj"])

        # 시그널 연결 시 combobox가 존재하는지 확인 후 시그널 연결
        if "combobox" in self.header_dict_[0]["obj_set"]:
            self.header_dict_[0]["obj_set"]["combobox"].currentIndexChanged.connect(
                lambda value=self.header_dict_[0]["obj_set"]["combobox"], tmp_idx=0: self.valuechange_event(idx=tmp_idx, value=value)
            )

            # Raw Ingredient textbox 값 변경 시 업데이트
        if "textbox" in self.header_dict_[1]["obj_set"]:
            self.header_dict_[1]["obj_set"]["textbox"].textChanged.connect(
                lambda value: self.update_raw_ingredient_value(value)
            )
            
        self.header_dict_[2]["obj_set"]["button"].clicked.connect(lambda: self.button_setting_event(0, self.header_dict_[2]))

        self.header_dict_[3]["obj_set"]["toggle"].setChecked(True)
        
        #object function specific setting(checkbox)
        self.header_dict_[3]["obj_set"]["toggle"].toggled.connect(lambda ch=self.header_dict_[3]["obj_set"]["toggle"], tmp_idx=3 : self.toggle_event(mode=0, idx=tmp_idx, ch=ch, obj=self.header_dict_[3]))
        
        # Spinbox 값 변경 이벤트 설정
        calibration_spinbox = self.header_dict_[4]["obj_set"]["spinbox"]
        calibration_spinbox.setDecimals(2)  # 소수점 2자리로 표시
        calibration_spinbox.setValue(round(self.adv_model_info[4]["value"][0], 2))  # 초기값 반올림
        calibration_spinbox.setSingleStep(0.01)  # 0.01 단위로 설정
        calibration_spinbox.valueChanged.connect(
            lambda value: self.valuechange_event(idx=4, value=round(value, 2))  # 소수점 2자리로 강제 반올림
        )

        # 1. Hyperspectral
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_hyperspectral_label", self.header_dict_[0]["obj_tip"]["label"])

        # 2. Raw Ingredient
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_rawingredient_label", self.header_dict_[1]["obj_tip"]["label"])

        # 3. Save Path
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_savepath_label", self.header_dict_[2]["obj_tip"]["label"])
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_savepath_button", self.header_dict_[2]["obj_set"]["button"])

        # 4. Calibration
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_calibration_label", self.header_dict_[3]["obj_tip"]["label"])

        # 5. Calibration Ratio
        self.lang.set("advanced", "advanced_label_optimization_main", "advanced_label_optimization_calibrationratio_label", self.header_dict_[4]["obj_tip"]["label"])


    def update_raw_ingredient_value(self, value):
        """
        @description: Updates the Raw Ingredient value in adv_model_info when the textbox changes.
        """
        self.adv_model_info[1]["value"] = value  # Update value

    # valuechange_event 함수에서 mode 인수 제거
    def valuechange_event(self, idx, value):
        """
        Spinbox, Combobox 위젯 값 변경 시 호출되는 이벤트 함수
        """
        if self.signal_sw:
            # 기존 값과 다를 때만 처리
            if round(self.adv_model_info[idx]["value"][1], 2) != value:
                self.signal_sw = False

                # 변경된 값을 저장
                if idx == 4:  # Calibration Ratio
                    self.adv_model_info[idx]["value"][1] = value

                self.signal_sw = True




    def toggle_event(self, mode, idx, ch, obj=None):
        """
            @description: 토글버튼 시그널발생시 발동되는 함수
            @author : Jihoon
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
            @author : Jihoon
        """
        if mode == 0:  # select folder instead of file
            file_dialog = QtWidgets.QFileDialog()
            fname = file_dialog.getExistingDirectory(self, "폴더 선택", "")
            if fname:
                self.adv_model_info[2]["value"][1] = fname
                obj["obj_set"]["lineedit"].setText(str(self.adv_model_info[2]["value"][1]))
                obj["obj_set"]["lineedit"].setToolTip(str(self.adv_model_info[2]["value"][1]))
                print(f"Debug - Selected Save Path: {fname}")  # 선택한 경로 디버깅 출력
            else:
                print("Warning: Save path was not selected.")  # 경로가 선택되지 않았을 때 출력



    def button_datalist_event(self, mode, obj):
        """
            @description: 데이터 search 버튼 시그널발생시 발동되는 함수
            @author : Jihoon
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
                    self.advanced_label_optimization_datalist_tableview.setRowCount(cur_data_len + len(add_data_list))
                    
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
                        cur_row_cnt = self.advanced_label_optimization_datalist_tableview.rowCount()
                        for tmp_row in range(cur_row_cnt):
                            tmp_item = self.advanced_label_optimization_datalist_tableview.item(tmp_row,0)
                            if not tmp_item:
                                self.advanced_label_optimization_datalist_tableview.setItem(tmp_row, 0, value["obj_idx"])
                                self.advanced_label_optimization_datalist_tableview.setItem(tmp_row, 1, value["obj_path"])
                                self.advanced_label_optimization_datalist_tableview.setCellWidget(tmp_row, 2, value["obj_set"]["widget"])
                                value["obj_set"]["toggle"].setChecked(True)
                                value["obj_set"]["toggle"].toggled.connect(lambda ch, tmp_row2=key, tmp_value=value : self.toggle_event(mode=1, idx=tmp_row2, ch=ch, obj=tmp_value))
                                break
                    self.adv_data_list_info.update(tmp_data_list_info)

        elif mode == 1: # Clear
            self.clear_event()
            
    
    def button_event(self, mode):
        """
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        if mode == 0:  # Start
            if self.worker_id == -1:
                # 초기 설정
                self.interrupt_ = False
                self.advanced_label_optimization_setting_start_btn.setEnabled(False)
                self.advanced_label_optimization_setting_stop_btn.setEnabled(True)
                self.advanced_label_optimization_setting_groupbox.setEnabled(False)
                self.advanced_label_optimization_datalist_groupbox.setEnabled(False)

                # 상태 출력 초기화
                self.advanced_label_optimization_status_textedit.clear()
                header = f"Mode: {self.mode}\n{self.dash * 50}"
                self.advanced_label_optimization_status_textedit.appendPlainText(header)
                self.advanced_label_optimization_status_textedit.appendPlainText("\nParameter Setting:\n")

                # 각 위젯의 값을 동적으로 가져옴
                for idx, value in self.adv_model_info.items():
                    tmp_type = value["type"]

                    # 위젯별 값 가져오기
                    if idx == 0:  # ComboBox (Hyperspectra)
                        tmp_value = self.header_dict_[0]["obj_set"]["combobox"].currentText()
                    elif idx == 1:  # TextBox (Raw Ingredient)
                        tmp_value = self.header_dict_[1]["obj_set"]["textbox"].text()
                    elif idx == 2:  # LineEdit (Save Path)
                        tmp_value = self.header_dict_[2]["obj_set"]["lineedit"].text()
                    elif idx == 3:  # Calibration (Toggle)
                        toggle_value = self.header_dict_[3]["obj_set"]["toggle"].isChecked()
                        tmp_value = 'True' if toggle_value else 'False'  # Boolean 값을 문자열로 변환
                    elif idx == 4:  # Calibration Ratio (SpinBox)
                        calibration_ratio_spinbox = self.header_dict_[4]["obj_set"]["spinbox"]
                        tmp_value = f"{calibration_ratio_spinbox.value():.2f}"  # Spinbox 값 포맷팅
                    else:
                        tmp_value = value["value"][0]

                    tmp_string = f"{idx+1}. {tmp_type}: {tmp_value}"
                    self.advanced_label_optimization_status_textedit.appendPlainText(tmp_string)

                self.advanced_label_optimization_status_textedit.appendPlainText(f"\n{self.dash * 50}")
                self.advanced_label_optimization_status_textedit.appendPlainText("Processing Start...\n")

                # Start processing
                self.worker_1.staging(self.label_optimization)
                self.worker_id = self.worker_1.cur_id
                self.worker_1.start()
            else:
                QtWidgets.QMessageBox.information(self,
                    self.lang.get(
                        "advanced", "advanced_label_optimization_main", "advanced_label_optimization_msg_warning_already_allocated_title"),
                        f"{self.lang.get('advanced', 'advanced_label_optimization_main', 'advanced_label_optimization_msg_warning_already_allocated_message')} Worker ID: {self.worker_id}"
                    )

        elif mode == 1:  # Stop
            if self.yes_no_message(
                self.lang.get("advanced", "advanced_label_optimization_main", "advanced_label_optimization_msg_stop_title"),
                self.lang.get("advanced", "advanced_label_optimization_main", "advanced_label_optimization_msg_stop_message")
            ):
                self.interrupt_ = True
                self.worker_id = -1
                self.advanced_label_optimization_status_textedit.appendPlainText("\n[INFO] Process stop requested. Please wait for it to finish safely.\n")
                print("Process stop requested by user.")

    def label_optimization(self) -> None:
        if self.interrupt_:
            self.string_signal.emit("\n[INFO] Process interrupted before starting.\n")
            return

        gen = GenModule(self.signal_)
        ingredient = self.adv_model_info[1]["value"]
        save_path = self.adv_model_info[2]["value"][1]
        self.string_signal.emit(f"\n[DEBUG] Save Path: {save_path}\n")

        if not save_path:
            self.string_signal.emit("\n    [ERROR] Save path is not set.\n")
            return

        calibration = self.adv_model_info[3]["value"][0]
        calibration_rate = self.adv_model_info[4]["value"][0]
        hyp = self.header_dict_[0]["obj_set"]["combobox"].currentText()
        npy = "label.npy"

        labelled_data_1_2_list, labelled_coords_1_2_list, labelled_labels_1_2_list = [], [], []
        labelled_data_3_up_list, labelled_coords_3_up_list, labelled_labels_3_up_list = [], [], []

        try:
            # **Data List에서 선택된 데이터만 필터링**
            data_path_list = [key for key, value in self.adv_data_list_info.items() if value["use"]]

            if len(data_path_list) == 0:
                raise Exception("Data path is empty. No processing will be performed.")
            
            total_files_count = sum(len(glob.glob(os.path.join(data_path, "data.hdr"))) for data_path in data_path_list)
            processed_files_count = 0

            self.string_signal.emit(f"[INFO] Total data paths to process: {len(data_path_list)}\n")

            for data_path in data_path_list:
                if self.interrupt_:
                    self.string_signal.emit("\n[INFO] Process interrupted by user.\n")
                    return

                # 하위 폴더가 아닌 지정된 폴더 내에서만 데이터 검색
                data_files = glob.glob(os.path.join(data_path, "data.hdr"))  # recursive=False
                if len(data_files) == 0:
                    self.string_signal.emit(f"\n[INFO] No data files found in folder: {data_path}\n")
                    continue

                for idx, file in enumerate(data_files):
                    if self.interrupt_:
                        self.string_signal.emit("\n[INFO] Process interrupted by user.\n")
                        return

                    processed_files_count += 1
                    file_path = os.path.dirname(file)
                    self.string_signal.emit(f" \n{'='*100}\n    [{processed_files_count}/{total_files_count}] Processing file: {file_path}\n{'='*100}")

                    # 데이터 로드
                    if calibration:
                        data, _, _, labels = gen.load_data_and_labels(file_path, calibration=True, calibration_rate=calibration_rate, npy=npy, hyp=hyp)
                    else:
                        data, labels = gen.load_data_and_labels(file_path, calibration=False, npy=npy)

                    if data is None or labels is None:
                        self.string_signal.emit(f"    [WARNING] Skipping file due to data or label loading error: {file_path}")
                        continue

                    # 데이터 분류
                    (data_1_2, coords_1_2, label_1_2), (data_3_up, coords_3_up, label_3_up) = gen.get_labelled_data_by_class(data, labels)

                    labelled_data_1_2_list.append(data_1_2)
                    labelled_coords_1_2_list.append(coords_1_2)
                    labelled_labels_1_2_list.append(label_1_2)

                    labelled_data_3_up_list.append(data_3_up)
                    labelled_coords_3_up_list.append(coords_3_up)
                    labelled_labels_3_up_list.append(label_3_up)

            # 결과 저장
            if labelled_data_1_2_list:
                labelled_data_1_2 = np.vstack(labelled_data_1_2_list)
                labelled_labels_1_2 = np.concatenate(labelled_labels_1_2_list)
                self.string_signal.emit(f"\n[INFO] Total labelled data points for labels 1 and 2: {labelled_data_1_2.shape[0]}")
                gen.gen_merge_raw(save_path, labelled_data_1_2, labelled_labels_1_2, f"{ingredient}_1_2", calibration=calibration, hyp=hyp)
            else:
                self.string_signal.emit("\n[INFO] No labelled data for labels 1 and 2.\n")

            if labelled_data_3_up_list:
                labelled_data_3_up = np.vstack(labelled_data_3_up_list)
                labelled_labels_3_up = np.concatenate(labelled_labels_3_up_list)
                self.string_signal.emit(f"\n[INFO] Total labelled data points for labels 3 and up: {labelled_data_3_up.shape[0]}")
                gen.gen_merge_raw(save_path, labelled_data_3_up, labelled_labels_3_up, f"{ingredient}_3_up", calibration=calibration, hyp=hyp)
            else:
                self.string_signal.emit("\n[INFO] No labelled data for labels 3 and up.\n")

            self.string_signal.emit(f"\n{'=' * 100}\n[INFO] Processing Complete!\n{'=' * 100}\n")
        except Exception as e:
            self.string_signal.emit(f"\n[ERROR] An error occurred: {str(e)}\n{'=' * 50}\n")




    def clear_event(self):
        """
            @description: 데이터 리스트 초기화 하는 부분
            @author : Jihoon
        """
        self.advanced_label_optimization_datalist_tableview.clear()
        self.advanced_label_optimization_datalist_tableview.setRowCount(4)
        self.advanced_label_optimization_datalist_tableview.setHorizontalHeaderLabels(["Index", "Data", "Use"])
        self.adv_data_list_info = {}

    def update_status(self, string_):
        """
        상태창에 텍스트를 추가하는 함수
        """
        try:
            # 숫자라면 포맷을 적용
            formatted_string = f"{float(string_):.2f}" if string_.replace('.', '', 1).isdigit() else string_
            self.advanced_label_optimization_status_textedit.appendPlainText(formatted_string)
        except ValueError:
            # 변환 실패 시 원래 문자열을 출력
            self.advanced_label_optimization_status_textedit.appendPlainText(string_)

    def yes_no_message(self, title, message):
        """
            @description: 기능 정지 버튼 클릭 시 발생하는 확인 메시지
            @author : Jihoon
        """
        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Warning)
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        msgbox.setWindowTitle(title)
        msgbox.setText(message)
        answer = msgbox.exec_()
        if answer == QtWidgets.QMessageBox.Yes:
            return True
        else:
            return False

    def showEvent(self, e):
        pass

    def closeEvent(self, e):
        pass


class GenModule:
    def __init__(self, signal_instance):
        self.hdr_info = self.gen_hdr_info()
        self.string_signal = signal_instance.string_signal  # signal_ 인스턴스를 받도록 변경


    def gen_hdr_info(self, hyp="VNIR", info="None"):
        _dict = {}
        if hyp == "NIR":
            _dict = {
                "info":info,
                "width":400,
                "height": 640,
                "default band":{192,113,51},
                "WaveCount":224,
                "wavelength":[
                    900.00,903.57,907.14,910.71,914.29,917.86,921.43,925.00,928.57,932.14,935.71,939.29,942.86,946.43,950.00,953.57,
                    957.14,960.71,964.29,967.86,971.43,975.00,978.57,982.14,985.71,989.29,992.86,996.43,1000.00,1003.57,1007.14,1010.71,
                    1014.29,1017.86,1021.43,1025.00,1028.57,1032.14,1035.71,1039.29,1042.86,1046.43,1050.00,1053.57,1057.14,1060.71,1064.29,
                    1067.86,1071.43,1075.00,1078.57,1082.14,1085.71,1089.29,1092.86,1096.43,1100.00,1103.57,1107.14,1110.71,1114.29,1117.86,
                    1121.43,1125.00,1128.57,1132.14,1135.71,1139.29,1142.86,1146.43,1150.00,1153.57,1157.14,1160.71,1164.29,1167.86,1171.43,
                    1175.00,1178.57,1182.14,1185.71,1189.29,1192.86,1196.43,1200.00,1203.57,1207.14,1210.71,1214.29,1217.86,1221.43,1225.00,
                    1228.57,1232.14,1235.71,1239.29,1242.86,1246.43,1250.00,1253.57,1257.14,1260.71,1264.29,1267.86,1271.43,1275.00,1278.57,
                    1282.14,1285.71,1289.29,1292.86,1296.43,1300.00,1303.57,1307.14,1310.71,1314.29,1317.86,1321.43,1325.00,1328.57,1332.14,
                    1335.71,1339.29,1342.86,1346.43,1350.00,1353.57,1357.14,1360.71,1364.29,1367.86,1371.43,1375.00,1378.57,1382.14,1385.71,
                    1389.29,1392.86,1396.43,1400.00,1403.57,1407.14,1410.71,1414.29,1417.86,1421.43,1425.00,1428.57,1432.14,1435.71,1439.29,
                    1442.86,1446.43,1450.00,1453.57,1457.14,1460.71,1464.29,1467.86,1471.43,1475.00,1478.57,1482.14,1485.71,1489.29,1492.86,
                    1496.43,1500.00,1503.57,1507.14,1510.71,1514.29,1517.86,1521.43,1525.00,1528.57,1532.14,1535.71,1539.29,1542.86,1546.43,
                    1550.00,1553.57,1557.14,1560.71,1564.29,1567.86,1571.43,1575.00,1578.57,1582.14,1585.71,1589.29,1592.86,1596.43,1600.00,
                    1603.57,1607.14,1610.71,1614.29,1617.86,1621.43,1625.00,1628.57,1632.14,1635.71,1639.29,1642.86,1646.43,1650.00,1653.57,
                    1657.14,1660.71,1664.29,1667.86,1671.43,1675.00,1678.57,1682.14,1685.71,1689.29,1692.86,1696.43
                ]
            }
        elif hyp == "VNIR":
            _dict = {
                "info":info,
                "width":400,
                "height": 512,
                "default band":{192,113,51},
                "WaveCount":224,
                "wavelength":[
                    400.67,403.35,406.03,408.71,411.38,414.06,416.74,419.42,422.10,424.78,427.46,430.13,432.81,435.49,
                    438.17,440.85,443.53,446.21,448.88,451.56,454.24,456.92,459.60,462.28,464.96,467.63,470.31,472.99,
                    475.67,478.35,481.03,483.71,486.38,489.06,491.74,494.42,497.10,499.78,502.46,505.13,507.81,510.49,
                    513.17,515.85,518.53,521.21,523.88,526.56,529.24,531.92,534.60,537.28,539.96,542.63,545.31,547.99,
                    550.67,553.35,556.03,558.71,561.38,564.06,566.74,569.42,572.10,574.78,577.46,580.13,582.81,585.49,
                    588.17,590.85,593.53,596.21,598.88,601.56,604.24,606.92,609.60,612.28,614.96,617.63,620.31,622.99,
                    625.67,628.35,631.03,633.71,636.38,639.06,641.74,644.42,647.10,649.78,652.46,655.13,657.81,660.49,
                    663.17,665.85,668.53,671.21,673.88,676.56,679.24,681.92,684.60,687.28,689.96,692.63,695.31,697.99,
                    700.67,703.35,706.03,708.71,711.38,714.06,716.74,719.42,722.10,724.78,727.46,730.13,732.81,735.49,
                    738.17,740.85,743.53,746.21,748.88,751.56,754.24,756.92,759.60,762.28,764.96,767.63,770.31,772.99,
                    775.67,778.35,781.03,783.71,786.38,789.06,791.74,794.42,797.10,799.78,802.46,805.13,807.81,810.49,
                    813.17,815.85,818.53,821.21,823.88,826.56,829.24,831.92,834.60,837.28,839.96,842.63,845.31,847.99,
                    850.67,853.35,856.03,858.71,861.38,864.06,866.74,869.42,872.10,874.78,877.46,880.13,882.81,885.49,
                    888.17,890.85,893.53,896.21,898.88,901.56,904.24,906.92,909.60,912.28,914.96,917.63,920.31,922.99,
                    925.67,928.35,931.03,933.71,936.38,939.06,941.74,944.42,947.10,949.78,952.46,955.13,957.81,960.49,
                    963.17,965.85,968.53,971.21,973.88,976.56,979.24,981.92,984.60,987.28,989.96,992.63,995.31,997.99
                    ]
            }

        return _dict

    def gen_merge_raw(self, save_path, data, labels, product_name, calibration=True, hyp="VNIR"):
        w, h = self.hdr_info["width"], self.hdr_info["height"]
        data_len = (data.shape[0] + w * h - 1) // (w * h)

        tmp_data = np.zeros((w * h * data_len, 224))
        tmp_label = np.zeros((w * h * data_len))
        tmp_data[:data.shape[0]] = data
        tmp_label[:labels.shape[0]] = labels

        for idx in range(data_len):
            start_idx, end_idx = idx * w * h, (idx + 1) * w * h
            if start_idx >= data.shape[0]:
                self.string_signal.emit(f"Skipping empty data at index {idx}.")
                continue

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"{timestamp}_{product_name}_라벨링 종합_{idx}"
            output_path = os.path.join(save_path, file_name)
            os.makedirs(output_path, exist_ok=True)

            self.string_signal.emit(f"Saving file: {file_name}")
            tmp_save_data = tmp_data[start_idx:end_idx]
            tmp_save_label = tmp_label[start_idx:end_idx]

            if np.count_nonzero(tmp_save_data) > 0:
                save_data = tmp_save_data.reshape(w, h, -1)
                save_label = tmp_save_label.reshape(w, h)
                np.save(f"{output_path}/label.npy", save_label)
                output_data_hdr_path = os.path.join(output_path, "data.hdr")
                spectral.io.envi.save_image(output_data_hdr_path, save_data, ext=".raw", interleave="bil", dtype=np.uint16, force=True, metadata=self.hdr_info)

                if calibration:
                    whiteref = np.ones((100, h)) * 4095.0
                    darkref = np.zeros((100, h))
                    self.save_reference(output_path, "DARKREF", darkref)
                    self.save_reference(output_path, "WHITEREF", whiteref)

    def save_reference(self, output_path, ref_name, ref_data):
        output_hdr_path = os.path.join(output_path, f"{ref_name}.hdr")
        spectral.io.envi.save_image(output_hdr_path, ref_data, ext=".raw", interleave="bil", dtype=np.uint16, force=True, metadata=self.hdr_info)
                    

    def load_data_and_labels(self, data_path, calibration=True, calibration_rate=1.0, npy="label.npy", hyp="VNIR"):
        try:
            data = np.array(spectral.io.envi.open(os.path.join(data_path, "data.hdr"), os.path.join(data_path, "data.raw")).load())
            labels = np.load(os.path.join(data_path, npy))
        except Exception as e:
            self.string_signal.emit(f"Error loading data or labels: {e}")
            return None, None, None, None

        if calibration:
            try:
                dark_data = np.array(spectral.io.envi.open(os.path.join(data_path, "DARKREF.hdr"), os.path.join(data_path, "DARKREF.raw")).load()).mean(0)
                white_data = np.array(spectral.io.envi.open(os.path.join(data_path, "WHITEREF.hdr"), os.path.join(data_path, "WHITEREF.raw")).load()).mean(0)

                data = (((data - dark_data) / (white_data - dark_data)) * 4095.0) * calibration_rate
                data = np.array(np.clip(data, 0, 4095.0), dtype=np.float32)
            except Exception as e:
                self.string_signal.emit(f"Error during calibration: {e}")
                return None, None, None, None

            return data, white_data, dark_data, labels
        else:
            self.string_signal.emit("Calibration not applied")
            return data, None, None, labels


    def get_labelled_data_by_class(self, data, labels):
        labelled_data_1_2 = []
        labelled_coords_1_2 = []
        labelled_labels_1_2 = []
        labelled_data_3_up = []
        labelled_coords_3_up = []
        labelled_labels_3_up = []

        # 라벨 번호가 1 또는 2인 경우 따로 분류
        labelled_coords_1_2 = np.column_stack(np.where((labels == 1) | (labels == 2)))
        labelled_data_1_2 = data[(labels == 1) | (labels == 2), :]
        labelled_labels_1_2 = labels[(labels == 1) | (labels == 2)]

        # 라벨 번호가 3 이상인 경우 분류
        labelled_coords_3_up = np.column_stack(np.where(labels >= 3))
        labelled_data_3_up = data[labels >= 3, :]
        labelled_labels_3_up = labels[labels >= 3]

        return (labelled_data_1_2, labelled_coords_1_2, labelled_labels_1_2), (labelled_data_3_up, labelled_coords_3_up, labelled_labels_3_up)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = advanced_label_optimization_Form()
    sys.exit(app.exec_())
