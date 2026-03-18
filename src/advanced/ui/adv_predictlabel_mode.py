"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSlot
from enum import Enum
import traceback
import cv2
import torch
import glob
import numpy as np
import os

if __name__ == "__main__" :
    from adv_gen_module import gen_module
else:
    from .adv_gen_module import gen_module

from utils.worker import Threading_Worker
from utils.viewer import Display_viewer
from qtwidgets import AnimatedToggle

from advanced.stylesheet.stylesheet_adv_predictlabel_mode import stylesheet
from utils.custom_ui import messageBox
from constants.constants import MESSAGE_BOX_CONFIRMATION, MESSAGE_BOX_WARNING

class signal_(QtCore.QObject):
    string_signal = QtCore.pyqtSignal(str)
    image_signal = QtCore.pyqtSignal(str)
    error_signal = QtCore.pyqtSignal(str, object, str, str, object)

class MessageBoxType(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2

class advanced_predictlabel_Form(QtWidgets.QWidget):
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
        self.image_signal = self.signal_.image_signal
        self.error_signal = self.signal_.error_signal

        self.string_signal.connect(self.update_status)
        self.image_signal.connect(self.update_predict_image)
        self.error_signal.connect(messageBox)

    def init_variable(self):
        """
            Description: 초기 변수 선언부분
                - self.header_dict : 기능설정에 대한 오브젝트를 딕셔너리형태로 저장
                - self.adv_model_info : 기능설정에 대한 정보를 딕셔너리형태로 저장
                    0: model 파일에 대한 경로
                    1: model에 대한 임계값 설정
                    2: Calibration 설정
                    3: noise gen 모드 사용여부 및 데이터 생성 후 저장할 경로
                - self.adv_data_list_info : 기능을 적용할 데이터 대상리스트를 딕셔너리형태로 저장
                - self.worker_id : 기능 병렬처리를 위해 할당된 ID

            Development by MyoungHwan(2024.05.10)
        """
        self.header_dict_ = {}
        self.adv_model_info = {
            #[init value, set value]
            0: # model
                {
                    "type":"Model Path (DA.el)",
                    "tip":["label:1. Model Path (DA.el)"],
                    "value": ["-",""],
                    "obj_list":["lineedit:path", "button:Load" ]
                },
            1: #Threshold
                {
                    "type":"Threshold",
                    "tip":["label:2. Model Threshold"],
                    "value": [0.0,0.0],
                    "obj_list":["spinbox:0.0,10000.0,0.0"]
                },
            
            2: # Calibration
                {
                    "type":"Calibration",
                    "tip":["label:3. Calibration"],
                    "value": [True,True],
                    "obj_list":["toggle:"]
                    
                },
            3: # Calibration ratio
                {
                    "type":"Calibration Ratio",
                    "tip":["label:4. Calibration Ratio"],
                    "value": [1.0,1.0],
                    "obj_list":["spinbox:0.0,1.0,1.0"]
                    
                },
        }
        self.adv_data_list_info = {

        }

        self.worker_id = -1

        self.MessageType = Enum("MessageType", ["STOP", "WARNING"])

        self.dash = "-"
        self.mode = "Predict Label Mode"
        self.interrupt_ = False
        self.normalLabel = 2
        self.abnormalLabel = 200
        self.label = {}
        self.dist = {}


    @pyqtSlot(dict)
    def recv_from_threading(self, output):
        """
            Description: Recv threading process result
            Implement by MyoungHwan
        """
        self.worker_id = -1
        self.interrupt_ = False # Reset when the task is finished and the stop button is pressed at the same time so that the next task is not affected.
        self.advanced_predictlabel_setting_start_btn.toggle()
        self.advanced_predictlabel_setting_start_btn.setEnabled(True)
        self.advanced_predictlabel_setting_stop_btn.setEnabled(False)
        self.advanced_predictlabel_setting_groupbox.setEnabled(True)
        self.advanced_predictlabel_datalist_groupbox.setEnabled(True)
        self.ImageSelectorComboBox.setEnabled(True)
        self.ThresholdButton.setEnabled(True)
        self.ThresholdLineEdit.setEnabled(True)


    def init_ui(self, MainWindow):
        """
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        MainWindow.setObjectName("adv_setting_form")
        MainWindow.resize(840, 640)
        MainWindow.setWindowTitle("Advanced Setting")
        MainWindow.setStyleSheet(stylesheet)

        self.advanced_predictlabel_main_horizon = QtWidgets.QHBoxLayout(MainWindow)
        self.advanced_predictlabel_main_horizon.setObjectName("advanced_predictlabel_main_horizon")

        self.advanced_predictlabel_main_vertical = QtWidgets.QVBoxLayout()
        self.advanced_predictlabel_main_vertical.setObjectName("advanced_predictlabel_main_vertical")

        self.advanced_predictlabel_setting_groupbox = QtWidgets.QGroupBox()
        self.advanced_predictlabel_setting_groupbox.setObjectName("advanced_predictlabel_setting_groupbox")
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_setting_groupbox", self.advanced_predictlabel_setting_groupbox)

        self.advanced_predictlabel_setting_vertical = QtWidgets.QVBoxLayout()
        self.advanced_predictlabel_setting_vertical.setObjectName("advanced_predictlabel_setting_vertical")

        self.advanced_predictlabel_datalist_groupbox = QtWidgets.QGroupBox()
        self.advanced_predictlabel_datalist_groupbox.setObjectName("advanced_predictlabel_datalist_groupbox")
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_datalist_groupbox", self.advanced_predictlabel_datalist_groupbox)

        self.advanced_predictlabel_datalist_vertical = QtWidgets.QVBoxLayout()
        self.advanced_predictlabel_datalist_vertical.setObjectName("advanced_predictlabel_datalist_vertical")

        self.advanced_predictlabel_datalist_tableview = QtWidgets.QTableWidget()
        self.advanced_predictlabel_datalist_tableview.setObjectName("advanced_predictlabel_datalist_tableview")
        self.advanced_predictlabel_datalist_tableview.setColumnCount(3)
        self.advanced_predictlabel_datalist_tableview.setRowCount(4)
        self.advanced_predictlabel_datalist_tableview.setVerticalHeaderLabels
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_datalist_tableview", self.advanced_predictlabel_datalist_tableview)
        self.advanced_predictlabel_datalist_tableview_header = self.advanced_predictlabel_datalist_tableview.horizontalHeader()
        self.advanced_predictlabel_datalist_tableview_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.advanced_predictlabel_datalist_tableview_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.advanced_predictlabel_datalist_tableview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.advanced_predictlabel_datalist_tableview.setDragEnabled(False)
        self.advanced_predictlabel_datalist_tableview.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.advanced_predictlabel_datalist_tableview.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.advanced_predictlabel_datalist_tableview.verticalHeader().hide()

        self.advanced_predictlabel_datalist_global_horizon = QtWidgets.QHBoxLayout()
        self.advanced_predictlabel_datalist_global_horizon.setObjectName("advanced_predictlabel_datalist_global_horizon")
        self.advanced_predictlabel_datalist_global_search_btn = QtWidgets.QPushButton()
        self.advanced_predictlabel_datalist_global_search_btn.setObjectName("advanced_predictlabel_datalist_global_search_btn")
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_datalist_global_search_btn", self.advanced_predictlabel_datalist_global_search_btn)
        self.advanced_predictlabel_datalist_global_clear_btn = QtWidgets.QPushButton()
        self.advanced_predictlabel_datalist_global_clear_btn.setObjectName("advanced_predictlabel_datalist_global_clear_btn")
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_datalist_global_clear_btn", self.advanced_predictlabel_datalist_global_clear_btn)
    
        self.advanced_predictlabel_setting_horizon = QtWidgets.QHBoxLayout()
        self.advanced_predictlabel_setting_horizon.setObjectName("advanced_predictlabel_setting_horizon")

        self.advanced_predictlabel_setting_start_btn = QtWidgets.QPushButton()
        self.advanced_predictlabel_setting_start_btn.setObjectName("advanced_predictlabel_setting_start_btn")
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_setting_start_btn", self.advanced_predictlabel_setting_start_btn)
        self.advanced_predictlabel_setting_start_btn.resize(150,150)
        self.advanced_predictlabel_setting_start_btn.setCheckable(True)

        self.advanced_predictlabel_setting_stop_btn = QtWidgets.QPushButton()
        self.advanced_predictlabel_setting_stop_btn.setObjectName("advanced_predictlabel_setting_stop_btn")
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_setting_stop_btn", self.advanced_predictlabel_setting_stop_btn)
        self.advanced_predictlabel_setting_stop_btn.resize(150,150)
        self.advanced_predictlabel_setting_stop_btn.setEnabled(False)

        self.advanced_predictlabel_status_vertical = QtWidgets.QVBoxLayout()
        self.advanced_predictlabel_status_vertical.setObjectName("advanced_predictlabel_status_vertical")

        self.advanced_predictlabel_status_textedit = QtWidgets.QPlainTextEdit()
        self.advanced_predictlabel_status_textedit.setReadOnly(True)
        self.advanced_predictlabel_status_textedit.setUndoRedoEnabled(False)

        # Image results tab widget and related widgets
        self.advancedMain = QtWidgets.QTabWidget()
        self.advancedMain.setObjectName("advancedMain")

        self.advanced_predictlabel_status_mainwidget = QtWidgets.QWidget()
        self.advanced_predictlabel_status_mainwidget.setObjectName("advanced_predictlabel_status_mainwidget")
        self.advanced_predictlabel_status_mainwidgetLayout = QtWidgets.QVBoxLayout(self.advanced_predictlabel_status_mainwidget)
        self.advanced_predictlabel_status_mainwidgetLayout.setObjectName("advanced_predictlabel_status_mainwidgetLayout")

        self.advanced_predictlabel_status_groupbox = QtWidgets.QGroupBox(self.advanced_predictlabel_status_mainwidget)
        self.advanced_predictlabel_status_groupbox.setObjectName("advanced_predictlabel_status_groupbox")
        self.advanced_predictlabel_status_groupbox_Layout = QtWidgets.QVBoxLayout(self.advanced_predictlabel_status_groupbox)
        self.advanced_predictlabel_status_groupbox_Layout.setObjectName("advanced_predictlabel_status_groupbox_Layout")
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_status_groupbox", self.advanced_predictlabel_status_groupbox)

        self.advanced_predictlabel_status_textedit = QtWidgets.QPlainTextEdit()
        self.advanced_predictlabel_status_textedit.setReadOnly(True)
        self.advanced_predictlabel_status_textedit.setUndoRedoEnabled(False)
        # Image results tab widget and related widgets
        self.advanced_predictlabel_image_widget = QtWidgets.QWidget()
        self.advanced_predictlabel_image_widget.setObjectName("advanced_predictlabel_image_widget")
        self.advanced_predictlabel_image_widget_Layout = QtWidgets.QVBoxLayout(self.advanced_predictlabel_image_widget)
        self.advanced_predictlabel_image_widget_Layout.setObjectName("advanced_predictlabel_image_widget_Layout")

        self.advanced_predictlabel_image_groupbox = QtWidgets.QGroupBox(self.advanced_predictlabel_image_widget)
        self.advanced_predictlabel_image_groupbox.setObjectName("advanced_predictlabel_image_groupbox")
        self.advanced_predictlabel_image_groupbox_Layout = QtWidgets.QVBoxLayout(self.advanced_predictlabel_image_groupbox)
        self.advanced_predictlabel_image_groupbox_Layout.setObjectName("advanced_predictlabel_image_groupbox_Layout")

        self.ResultControlWidget = QtWidgets.QWidget()
        self.ResultControlWidget.setObjectName("ResultControlWidget")
        self.ResultControlLayout = QtWidgets.QHBoxLayout(self.ResultControlWidget)
        self.ResultControlLayout.setObjectName("ResultControlLayout")

        # Image selection controller
        self.ImageSelectorMainWidget = QtWidgets.QWidget()
        self.ImageSelectorMainWidget.setObjectName("ImageSelectorMainWidget")
        self.ImageSelectorMainLayout = QtWidgets.QHBoxLayout(self.ImageSelectorMainWidget)
        self.ImageSelectorMainLayout.setObjectName("ImageSelectorMainLayout")

        self.ImageSelectorComboBox = QtWidgets.QComboBox()
        self.ImageSelectorComboBox.setObjectName("ImageSelectorComboBox")

        # Threshold controller
        self.ThresholdMainWidget = QtWidgets.QWidget()
        self.ThresholdMainWidget.setObjectName("ThresholdMainWidget")

        self.ThresholdMainLayout = QtWidgets.QHBoxLayout(self.ThresholdMainWidget)
        self.ThresholdMainLayout.setObjectName("ThresholdMainLayout")
        
        self.ThresholdLabel = QtWidgets.QLabel()
        self.ThresholdLabel.setObjectName("ThresholdLabel")
        self.lang.set("advanced", "advanced_predictlabel_main", "ThresholdLabel", self.ThresholdLabel)

        self.ThresholdLineEdit = QtWidgets.QLineEdit()
        self.ThresholdLineEdit.setObjectName("ThresholdLineEdit")


        self.ThresholdButton = QtWidgets.QPushButton()
        self.ThresholdButton.setObjectName("ThresholdButton")
        self.ThresholdButton.setCheckable(True)
        self.ThresholdButton.setEnabled(False)  # Initially disabled until threshold is set
        self.lang.set("advanced", "advanced_predictlabel_main", "ThresholdButton", self.ThresholdButton)

        self.advanced_predictlabel_image_groupbox_HorizontalLine = QtWidgets.QFrame()
        self.advanced_predictlabel_image_groupbox_HorizontalLine.setObjectName("advanced_predictlabel_image_groupbox_HorizontalLine")
        self.advanced_predictlabel_image_groupbox_HorizontalLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.advanced_predictlabel_image_groupbox_HorizontalLine.setFrameShadow(QtWidgets.QFrame.Sunken)


        # Vertical line (Image selection controller <-> Pred map controller)
        self.ResultControlVerticalLine1 = QtWidgets.QFrame()
        self.ResultControlVerticalLine1.setObjectName("ResultControlVerticalLine1")
        self.ResultControlVerticalLine1.setFrameShape(QtWidgets.QFrame.VLine)
        self.ResultControlVerticalLine1.setFrameShadow(QtWidgets.QFrame.Sunken)

        # image display widget
        self.OutputImageWidget = Display_viewer(usescrollbar=False)
        # enable drag & drop inside the image display widget
        self.OutputImageWidget.updateDrag(True)

        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

    def setup_ui(self):
        self.advanced_predictlabel_setting_groupbox.setLayout(self.advanced_predictlabel_setting_vertical)

        self.advanced_predictlabel_setting_horizon.addWidget(self.advanced_predictlabel_setting_start_btn)
        self.advanced_predictlabel_setting_horizon.addWidget(self.advanced_predictlabel_setting_stop_btn)
        
        self.advanced_predictlabel_datalist_global_horizon.addWidget(self.advanced_predictlabel_datalist_global_search_btn)
        self.advanced_predictlabel_datalist_global_horizon.addStretch()
        self.advanced_predictlabel_datalist_global_horizon.addWidget(self.advanced_predictlabel_datalist_global_clear_btn)

        self.advanced_predictlabel_datalist_vertical.addLayout(self.advanced_predictlabel_datalist_global_horizon)
        self.advanced_predictlabel_datalist_vertical.addWidget(self.advanced_predictlabel_datalist_tableview)
        self.advanced_predictlabel_datalist_groupbox.setLayout(self.advanced_predictlabel_datalist_vertical)

        self.advanced_predictlabel_main_vertical.addWidget(self.advanced_predictlabel_setting_groupbox)
        self.advanced_predictlabel_main_vertical.addWidget(self.advanced_predictlabel_datalist_groupbox)
        self.advanced_predictlabel_main_vertical.addLayout(self.advanced_predictlabel_setting_horizon)
        
        # Image results tab widget settings
        self.advanced_predictlabel_status_mainwidgetLayout.addWidget(self.advanced_predictlabel_status_textedit)

        self.ImageSelectorMainLayout.addWidget(self.ImageSelectorComboBox)
        self.ResultControlLayout.addWidget(self.ImageSelectorMainWidget)
        self.ResultControlLayout.addWidget(self.ResultControlVerticalLine1)
        self.ResultControlLayout.addWidget(self.ThresholdMainWidget)
        self.ThresholdMainLayout.addWidget(self.ThresholdLabel)
        self.ThresholdMainLayout.addWidget(self.ThresholdLineEdit)
        self.ThresholdMainLayout.addWidget(self.ThresholdButton)

        self.advanced_predictlabel_status_groupbox_Layout.addWidget(self.advanced_predictlabel_status_textedit)
        self.advanced_predictlabel_status_mainwidgetLayout.addWidget(self.advanced_predictlabel_status_groupbox)
        
        self.advanced_predictlabel_image_groupbox_Layout.addWidget(self.ResultControlWidget, 0, QtCore.Qt.AlignLeft)
        self.advanced_predictlabel_image_groupbox_Layout.addWidget(self.advanced_predictlabel_image_groupbox_HorizontalLine)
        self.advanced_predictlabel_image_groupbox_Layout.addWidget(self.OutputImageWidget)
        self.advanced_predictlabel_image_widget_Layout.addWidget(self.advanced_predictlabel_image_groupbox)
        self.advanced_predictlabel_image_widget_Layout.setContentsMargins(0, 0, 0, 0)

        self.advanced_predictlabel_main_horizon.addLayout(self.advanced_predictlabel_main_vertical)

        self.advancedMain.addTab(self.advanced_predictlabel_status_mainwidget, "Status")
        self.advancedMain.addTab(self.advanced_predictlabel_image_widget, "Image results")
        self.lang.set("advanced", "advanced_predictlabel_main", "statusTab", self.advancedMain)
        self.lang.set("advanced", "advanced_predictlabel_main", "imageResultTab", self.advancedMain)

        self.advanced_predictlabel_main_horizon.addWidget(self.advancedMain)

    def adjust_combo_box_width(self):
        """
        description: Added dynamic width adjustment functionality to automatically resize ImageSelectorComboBox based on its content length
        modified by Chansik Kim 2024.12.16
        """
        font_metrics = self.ImageSelectorComboBox.fontMetrics()
        text_width = 100  # Default minimum width
        if self.ImageSelectorComboBox.count() > 0:
            text_width = max(font_metrics.horizontalAdvance(self.ImageSelectorComboBox.itemText(i)) 
                           for i in range(self.ImageSelectorComboBox.count()))
        
        # Add padding for dropdown arrow and margins
        self.ImageSelectorComboBox.setFixedWidth(text_width + 30)

    def init_function(self):
        """
            Description: Qtablewidget 영역 외 버튼 사용을 위한 signal 정의 부분
            Implement by MyoungHwan(2024.05.13)
            History:
                1. Hyunsu Kim(2025.12.04) - Add signal and slot for image result tab
        """
        self.advanced_predictlabel_datalist_global_search_btn.clicked.connect(lambda : self.button_datalist_event(mode=0, obj=self.advanced_predictlabel_datalist_global_search_btn))
        self.advanced_predictlabel_datalist_global_clear_btn.clicked.connect(lambda : self.button_datalist_event(mode=1, obj=self.advanced_predictlabel_datalist_global_clear_btn))
        self.advanced_predictlabel_setting_start_btn.clicked.connect(lambda : self.button_event(mode=0))
        self.advanced_predictlabel_setting_stop_btn.clicked.connect(lambda : self.button_event(mode=1))
        self.ImageSelectorComboBox.activated.connect(lambda: self.image_signal.emit(self.ImageSelectorComboBox.currentText()))
        self.ThresholdButton.clicked.connect(self.apply_threshold)

    def create_obj(self, idx, obj_type="widget",obj_list=["button:testbtn"], layout="horizon"):
        """
            Description: Qtable UI 생성시 Item 추가를 위한 object 생성 부분
            Implement by MyoungHwan(2024.05.13)
        """
        if obj_type == "item":
            tmp_item = QtWidgets.QTableWidgetItem(obj_list)
            tmp_item.setTextAlignment(QtCore.Qt.AlignCenter)
            return tmp_item
        elif obj_type== "widget":
            tmp_obj_dict_ = {}
            # layout
            tmp_widget = QtWidgets.QWidget()
            if layout=="horizon":
                tmp_layout = QtWidgets.QHBoxLayout()

            for obj_ in obj_list:
                object_, value_ = obj_.split(":")
                if object_ == "button":
                    tmp_btn = QtWidgets.QPushButton()
                    tmp_btn.setObjectName(f"{idx}_tmp_btn")
                    tmp_btn.setText(value_)
                    tmp_obj_dict_["button"] = tmp_btn
                    tmp_layout.addWidget(tmp_btn)
                
                elif object_ == "toggle":
                    tmp_togglebox = AnimatedToggle(
                        pulse_checked_color="transparent",
                        pulse_unchecked_color="transparent"
                    )
                    tmp_togglebox.setObjectName(f"{idx}_tmp_checkbox")
                    tmp_togglebox.setFixedWidth(100)
                    tmp_obj_dict_["toggle"] = tmp_togglebox
                    tmp_layout.addWidget(tmp_togglebox)
                
                elif object_ == "spinbox":
                    minv, maxv, curv = list(map(float, value_.split(",")))
                    tmp_spinbox = QtWidgets.QDoubleSpinBox()
                    tmp_spinbox.setObjectName(f"{idx}_tmp_spinbox")
                    tmp_spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
                    tmp_spinbox.setRange(minv, maxv)
                    tmp_spinbox.setFixedWidth(100)
                    tmp_spinbox.setValue(curv)
                    tmp_spinbox.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["spinbox"] = tmp_spinbox
                    tmp_layout.addWidget(tmp_spinbox)

                elif object_ == "label":
                    tmp_label = QtWidgets.QLabel()
                    tmp_label.setObjectName(f"{idx}_tmp_label")
                    tmp_label.setText(value_)
                    tmp_label.setFixedWidth(200)
                    tmp_obj_dict_["label"] = tmp_label
                    tmp_layout.addWidget(tmp_label)
                
                elif object_ == "lineedit":
                    tmp_lineedit = QtWidgets.QLineEdit()
                    tmp_lineedit.setObjectName(f"{idx}_tmp_lineedit")
                    tmp_lineedit.setReadOnly(True)
                    tmp_lineedit.setDragEnabled(True)
                    tmp_lineedit.setText(value_)
                    tmp_lineedit.setMinimumWidth(0)
                    tmp_lineedit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
                    tmp_lineedit.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["lineedit"] = tmp_lineedit
                    tmp_layout.addWidget(tmp_lineedit, stretch=1)

            tmp_widget.setLayout(tmp_layout)
            tmp_obj_dict_["widget"] = tmp_widget
            return tmp_obj_dict_


    def fill_table(self):
        """
            Description: 기능에 대한 Ui 생성
            Implement by MyoungHwan(2024.05.13)
            Modified by Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
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
            self.advanced_predictlabel_setting_vertical.addLayout(value["obj"])


        self.header_dict_[0]["obj_set"]["button"].clicked.connect(lambda : self.button_setting_event(mode=0 ,obj=self.header_dict_[0]))
        
        self.header_dict_[1]["obj_set"]["spinbox"].valueChanged.connect(lambda value=self.header_dict_[1]["obj_set"]["spinbox"], tmp_idx=1: self.valuechange_event(mode=0, idx=tmp_idx,  value=value,obj=self.header_dict_[1]))

        #object specific setting
        self.header_dict_[2]["obj_set"]["toggle"].setChecked(True)
        
        #object function specific setting(checkbox)
        self.header_dict_[2]["obj_set"]["toggle"].toggled.connect(lambda ch=self.header_dict_[2]["obj_set"]["toggle"], tmp_idx=2 : self.toggle_event(mode=0, idx=tmp_idx, ch=ch, obj=self.header_dict_[3]))
        
        self.header_dict_[3]["obj_set"]["spinbox"].valueChanged.connect(lambda value=self.header_dict_[3]["obj_set"]["spinbox"], tmp_idx=3: self.valuechange_event(mode=1, idx=tmp_idx, value=value,obj=self.header_dict_[3]))

        # 1. model path language set
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_modelpath_label", self.header_dict_[0]["obj_tip"]["label"])
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_modelpath_button", self.header_dict_[0]["obj_set"]["button"])

        # 2. model threshold language set
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_modelthreshold_label", self.header_dict_[1]["obj_tip"]["label"])

        # 3. calibration language set
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_calibration_label", self.header_dict_[2]["obj_tip"]["label"])

        # 4. calibration ratio lanaguage set
        self.lang.set("advanced", "advanced_predictlabel_main", "advanced_predictlabel_calibrationratio_label", self.header_dict_[3]["obj_tip"]["label"])

    def update_predict_image(self, data_name=None):
        """
        @description : Update RGB image in the OutputImagewidget
        @author : Hyunsu Kim (2025.12.04)
        @parameters :
            data_name: Name of the data being processed
        @history :
        """
        imageName = "image_calibration.png"
        for file in self.adv_data_list_info.keys():
            if data_name == file.split("/")[-1]:
                if imageName not in os.listdir(file):
                    imageName = "image.png"
                rgb_data = cv2.imread(file + "/" + imageName, cv2.IMREAD_COLOR)
                rgb_data[self.label[data_name] >= self.abnormalLabel] = [255, 0, 0]  # Mark noise pixels in red
                self.OutputImageWidget.updatePhoto(QtGui.QPixmap(QtGui.QImage(rgb_data, rgb_data.shape[1], rgb_data.shape[0], rgb_data.shape[1] * rgb_data.shape[2], QtGui.QImage.Format_RGB888)), True)

    def apply_threshold(self):
        """
        @description : Apply threshold to the selected hyperspectral data
        @author : Hyunsu Kim (2025.12.04)
        @history :
            1. Yugyeong Hong(2026.02.24) - Refactor message box with util method and language support
        """
        self.ThresholdButton.setEnabled(False)
        if not self.ThresholdLineEdit.text():
            messageBox(mode=MESSAGE_BOX_WARNING, 
                       title=self.lang.get("advanced", "advanced_predictlabel_main", "advancedPredictLabelThresholdErrorTitle"), 
                       text=self.lang.get("advanced", "advanced_predictlabel_main", "advancedPredictLabelThresholdErrorMsg"),
                       buttons = {self.lang.get("main", "messageBox", "msgOk"):"accept"})
            self.ThresholdButton.setEnabled(True)
            self.ThresholdButton.toggle()
            return
        self.advanced_predictlabel_setting_start_btn.setEnabled(False)
        self.advanced_predictlabel_setting_stop_btn.setEnabled(False)
        thrValue = float(self.ThresholdLineEdit.text())
        if thrValue <= 0:
            thrValue = 0
        dataName = self.ImageSelectorComboBox.currentText()
        self.label[dataName] = np.where(self.dist[dataName] < thrValue, self.normalLabel, self.abnormalLabel)
        self.image_signal.emit(dataName)
        self.advanced_predictlabel_setting_start_btn.setEnabled(True)
        self.advanced_predictlabel_setting_stop_btn.setEnabled(True)
        self.ThresholdButton.setEnabled(True)
        self.ThresholdButton.toggle()

    def toggle_event(self, mode, idx, ch, obj=None):
        """
            Description: Qtablewidget 영역 내 체크버튼 사용을 위한 signal 발동 부분
            Implement by MyoungHwan(2024.05.13)
        """
        if mode == 0: # setting mode
            if idx == 2: #calibration toggle
                if ch:
                    if obj["obj_set"]["spinbox"].isEnabled() == 0:
                        obj["obj_set"]["spinbox"].setEnabled(True)
                        obj["obj_set"]["spinbox"].setValue(self.adv_model_info[3]["value"][1])
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

    def valuechange_event(self, mode, idx, value, obj):
        self.adv_model_info[idx]["value"][1] = value


    def button_setting_event(self, mode, obj):
        """
            Description: 기능에 대한 signal 발동 부분
            Implement by MyoungHwan(2024.05.13)
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
            Description: 데이터 리스트업을 위한 UI 생성 부분
            Implement by MyoungHwan(2024.05.13)
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
                    self.advanced_predictlabel_datalist_tableview.setRowCount(cur_data_len + len(add_data_list))
                    
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
                        cur_row_cnt = self.advanced_predictlabel_datalist_tableview.rowCount()
                        for tmp_row in range(cur_row_cnt):
                            tmp_item = self.advanced_predictlabel_datalist_tableview.item(tmp_row,0)
                            if not tmp_item:
                                self.advanced_predictlabel_datalist_tableview.setItem(tmp_row, 0, value["obj_idx"])
                                self.advanced_predictlabel_datalist_tableview.setItem(tmp_row, 1, value["obj_path"])
                                self.advanced_predictlabel_datalist_tableview.setCellWidget(tmp_row, 2, value["obj_set"]["widget"])
                                value["obj_set"]["toggle"].setChecked(True)
                                value["obj_set"]["toggle"].toggled.connect(lambda ch, tmp_row2=key, tmp_value=value : self.toggle_event(mode=1, idx=tmp_row2, ch=ch, obj=tmp_value))
                                break
                    self.adv_data_list_info.update(tmp_data_list_info)

        elif mode == 1: # Clear
            self.clear_event()
            
    
    def button_event(self, mode):
        """
            Description: Qtablewidget 영역 외 푸쉬버튼 사용을 위한 signal 발동 부분
            Implement by MyoungHwan(2024.05.13)
            History:
                1. Hyunsu Kim(2025.12.04) - Add widget control functions for image result tap
                2. Hyeok Yoon(2025.10.31) - Modifying Widgets to supports language function
                3. Yugyeong Hong(2026.02.24) - Refactor message box with util method and language support
        """
        if mode == 0: #start
            if self.worker_id == -1 :
                self.advanced_predictlabel_setting_start_btn.setEnabled(False)
                self.advanced_predictlabel_setting_stop_btn.setEnabled(True)
                self.advanced_predictlabel_setting_groupbox.setEnabled(False)
                self.advanced_predictlabel_datalist_groupbox.setEnabled(False)
                self.ImageSelectorComboBox.clear()
                self.ImageSelectorComboBox.setEnabled(False)
                self.OutputImageWidget.initPhoto()
                self.ThresholdButton.setEnabled(False)
                self.ThresholdLineEdit.clear()
                self.ThresholdLineEdit.setEnabled(False)

                self.advanced_predictlabel_status_textedit.clear()
                mode_string = f"{self.mode}\n{self.dash* 30}"
                self.advanced_predictlabel_status_textedit.appendPlainText(mode_string)
                self.advanced_predictlabel_status_textedit.appendPlainText("Parameter Setting\n")
                totalCount = 0
                for idx, value in enumerate(self.adv_model_info.values()):
                    tmp_type = value["type"]
                    tmp_value = value["value"][1]
                    tmp_string = f"{idx+1}. {tmp_type} : {tmp_value}\n"
                    self.advanced_predictlabel_status_textedit.appendPlainText(tmp_string)
                for _, value in self.adv_data_list_info.items():
                    if value["use"]:
                        totalCount +=1
                self.advanced_predictlabel_status_textedit.appendPlainText(self.dash*30)
                self.advanced_predictlabel_status_textedit.appendPlainText("Predict Data List\n")
                self.advanced_predictlabel_status_textedit.appendPlainText(f"Total: {totalCount}\n")
                self.advanced_predictlabel_status_textedit.appendPlainText(f"Processing Start....\n")
                self.worker_1.staging(self.predict_label_mode)
                self.worker_id = self.worker_1.cur_id
                self.worker_1.start()
            else:
                messageBox(
                    self,
                    mode=MESSAGE_BOX_WARNING,
                    title=self.lang.get("advanced", "advanced_predictlabel_main", "advanced_predictlabel_msg_warning_already_allocated_title"),
                    text=f'{self.lang.get("advanced", "advanced_predictlabel_main", "advanced_predictlabel_msg_warning_already_allocated_message")} Worker ID:{self.worker_id}',
                    buttons = {self.lang.get("main", "messageBox", "msgOk"):"accept"}
                )


        elif mode == 1: #stop
            self.ImageSelectorComboBox.setEnabled(True)
            self.ThresholdButton.setEnabled(True)
            self.ThresholdLineEdit.setEnabled(True)
            response = messageBox(
                mode=MESSAGE_BOX_CONFIRMATION,
                title=self.lang.get("advanced", "advanced_predictlabel_main", "advanced_predictlabel_msg_stop_title"),
                text=self.lang.get("advanced", "advanced_predictlabel_main", "advanced_predictlabel_msg_stop_message"),
                buttons={self.lang.get("main", "messageBox", "msgYes"): "accept", self.lang.get("main", "messageBox", "msgNo"): "reject"}
            )
            if response == "accept":
                self.interrupt_ = True


    def predict_label_mode(self) -> None:
        """
            Description: 학습모델을 통해 리스트업 되어있는 데이터를 예측하여 라벨맵 생성, Noise 추출기능 포함
            Implement by MyoungHwan(2024.05.13)
            History:
                1. Hyunsu Kim(2025.12.04) - Add a signal emit to update images after prediction
        """
        gen = gen_module()
        model_path = self.adv_model_info[0]['value'][1]
        threshold= self.adv_model_info[1]["value"][1]
        calibration = self.header_dict_[2]["obj_set"]["toggle"].isChecked()
        calibration_ratio = self.adv_model_info[3]["value"][1]
        try:
            if model_path == "":
                raise Exception("model path is not invalid")
            model = gen.load_model(model_path)
            
            data_path_list = []
            for key, value in self.adv_data_list_info.items():
                if value["use"]:
                    data_path_list.append(key)
            if len(data_path_list) == 0:
                raise Exception("data path is empty")
            result = self.predict_data(gen=gen, model=model, data_list=data_path_list, threshold=threshold, 
                                            calibration=calibration, calibration_rate=calibration_ratio, 
                                            )
            for cur_value in result:
                tmp_status, tmp_string = cur_value
                self.string_signal.emit(tmp_string)
        except Exception as e:
            self.string_signal.emit(f"Error Occured...{str(e)}\n")
        finally:
            self.string_signal.emit(f"\nProcessing Finish...\n")
            self.image_signal.emit(self.ImageSelectorComboBox.itemText(0))

    def predict_data(self, gen, model, gpu="cuda",
                     data_list="", threshold=1.0, normal_label=2, abnormal_label=3, 
                     calibration=True, calibration_rate=1.0,
                     label="/label.npy", predict_label="/label_predict.npy", precit_dist="/label_dist.npy", predcit_count=200,
                     noise_gen=False, bands=224
                     ):
        with torch.no_grad():
            model.eval()
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
                    width, height, bands = data.shape
                    data = torch.from_numpy(data).float()
                    data = data.to(gpu)
                    data = data.reshape(width*height,bands)
                    dist = model(data).to('cpu').numpy()
                    dist_to_binary = np.where(dist < threshold, normal_label, abnormal_label)
                    if os.path.isfile(file_path+label):
                        tmp_label=np.load(file_path+label).reshape(-1)
                        dist_to_binary = np.where(dist < threshold, tmp_label, tmp_label+predcit_count)
                        np.save(file_path + predict_label, dist_to_binary.reshape(width,height))
                    else:
                        np.save(file_path + predict_label, dist_to_binary.reshape(width,height))
                    np.save(file_path + precit_dist, dist.reshape(width,height))
                    self.dist[file_path.split("/")[-1]] = dist.reshape(width,height)
                    self.label[file_path.split("/")[-1]] = dist_to_binary.reshape(width,height)
                    self.ImageSelectorComboBox.addItem(file_path.split("/")[-1])
                    self.adjust_combo_box_width()
                    yield [True, f"save complete predict({predict_label}) and dist({precit_dist}) result"]
                except Exception as e:
                    tmp_str = f"Error Occured...{str(e)}"
                    self.error_signal.emit(MESSAGE_BOX_WARNING,
                                           self.lang.get("advanced", "advanced_predictlabel_main", "advancedPredictLabelingErrorTitle"),
                                           f'{self.lang.get("advanced", "advanced_predictlabel_main", "advancedPredictLabelingErrorMsg")}{str(e)}',
                                           {self.lang.get("main", "messageBox", "msgOk"):"accept"})
                    yield [False, tmp_str]



    def clear_event(self):
        """
            Description: 데이터 리스트 초기화 하는 부분
            Implement by MyoungHwan(2024.05.13)
        """
        self.advanced_predictlabel_datalist_tableview.clear()
        self.advanced_predictlabel_datalist_tableview.setRowCount(4)
        self.advanced_predictlabel_datalist_tableview.setHorizontalHeaderLabels(["Index", "Data", "Use"])
        self.adv_data_list_info = {}

    def update_status(self, string_):
        self.advanced_predictlabel_status_textedit.appendPlainText(string_)

    def showEvent(self, e):
        pass

    def closeEvent(self, e):
        pass




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = advanced_predictlabel_Form()
    sys.exit(app.exec_())
