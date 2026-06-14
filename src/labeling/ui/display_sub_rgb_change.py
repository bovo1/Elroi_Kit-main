"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

import copy
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSlot
"""
    description
    Modified by MyoungHwan(20240603) : stylesheet명 수정
"""
from constants.constants import *

class Display_rgb_change_Form(QtWidgets.QWidget):
    """Image detail form과 관련된 모든 기능을 처리하기 위한 클래스
    """
    def __init__(self, Sync=None, lang=None):
        super().__init__()
        # self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.init(Sync=Sync, lang=lang)
        self.init_Ui_display_rgb_change(self)
        self.setup_Ui_display_rgb_change(self)
        self.init_Function()

        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        if __name__ == "__main__":
            self.show()

    def init(self, Sync=None, lang=None):
        """Image defail ui 초기 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.lang = lang
        self.Sync = Sync
        self.core_to_display_sub_rgb_change_signal = self.Sync.core_to_display_sub_rgb_change_signal
        self.core_to_display_sub_rgb_change_signal.connect(self.recv_core_to_display_sub_rgb_change)

        self.display_sub_rgb_change_to_core_signal = self.Sync.display_sub_rgb_change_to_core_signal
        self.display_sub_rgb_change_to_display_signal = self.Sync.display_sub_rgb_change_to_display_signal
        self.display_sub_rgb_change_to_graph_sub_signal = self.Sync.display_sub_rgb_change_to_graph_sub_signal
        self.displaySubRgbChangeToGraphSignal = self.Sync.displaySubRgbChangeToGraphSignal

        self.tmp_db = {}
        self.init_status = False # RGB Bands의 설정창 활성화 여부
        self.slicombo_sw = False # Slider 발동 및 combo 박스 스위치, 슬라이더 혹은 콤보박스 설정변경 시 두개다 이벤트 발생하는거 막기위해 사용, 1개만 발동하도록
        self.cur_btn = -1 # 현재 버튼의 위치, 똑같은 버튼 두번 누르는거 방지하기 위함, default -1
        self.LinkForRgbLine = False # RGB 라인과 Slider/Combobox 연동 여부

        self.pen_obj_dict = self.Sync.pen_obj_dict

    def init_Ui_display_rgb_change(self, Form):
        Form.setObjectName("display_rgb_change_form")
        Form.setFixedSize(550,250)
        Form.setWindowFlag(Qt.WindowMinimizeButtonHint, False)

        self.display_rgb_change_main_grid = QtWidgets.QGridLayout(Form)
        self.display_rgb_change_main_grid.setObjectName("display_rgb_change_main_grid")

        self.display_rgb_change_visualization_group = QtWidgets.QGroupBox()
        self.display_rgb_change_visualization_group.setObjectName("display_rgb_change_visualization_group")
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_visualization_group", self.display_rgb_change_visualization_group)

        self.display_rgb_change_rgb_group = QtWidgets.QGroupBox()
        self.display_rgb_change_rgb_group.setObjectName("display_rgb_change_rgb_group")
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_rgb_group", self.display_rgb_change_rgb_group)

        self.display_rgb_change_vbox = QtWidgets.QVBoxLayout()
        self.display_rgb_change_vbox.setObjectName("display_rgb_change_vbox")

        self.display_rgb_change_title_horizon = QtWidgets.QHBoxLayout()
        self.display_rgb_change_title_horizon.setObjectName("display_rgb_change_title_horizon")
        self.display_rgb_change_title_color_label = QtWidgets.QLabel()
        self.display_rgb_change_title_color_label.setAlignment(QtCore.Qt.AlignCenter)
        self.display_rgb_change_title_color_label.setObjectName("display_rgb_change_title_color_label")
        self.display_rgb_change_title_band_range_label = QtWidgets.QLabel()
        self.display_rgb_change_title_band_range_label.setAlignment(QtCore.Qt.AlignCenter)
        self.display_rgb_change_title_band_range_label.setObjectName("display_rgb_change_title_band_range_label")
        self.display_rgb_change_title_band_label = QtWidgets.QLabel()
        self.display_rgb_change_title_band_label.setAlignment(QtCore.Qt.AlignCenter)
        self.display_rgb_change_title_band_label.setObjectName("display_rgb_change_title_band_label")
        
        self.display_rgb_change_red_horizon = QtWidgets.QHBoxLayout()
        self.display_rgb_change_red_horizon.setObjectName("display_rgb_change_red_horizon")
        self.display_rgb_change_red_label = QtWidgets.QLabel()
        self.display_rgb_change_red_label.setAlignment(QtCore.Qt.AlignCenter)
        self.display_rgb_change_red_label.setObjectName("display_rgb_change_red_label")
        self.display_rgb_change_red_range_slider = QtWidgets.QSlider()
        self.display_rgb_change_red_range_slider.setOrientation(QtCore.Qt.Horizontal)
        self.display_rgb_change_red_range_slider.setObjectName("display_rgb_change_red_range_slider")
        self.display_rgb_change_red_range_slider.setTickPosition(2)
        self.display_rgb_change_red_range_slider.setPageStep(10)
        self.display_rgb_change_red_range_slider.setRange(0, 1)
        self.display_rgb_change_red_comboBox = QtWidgets.QComboBox()
        self.display_rgb_change_red_comboBox.setObjectName("display_rgb_change_red_comboBox")

        self.display_rgb_change_green_horizon = QtWidgets.QHBoxLayout()
        self.display_rgb_change_green_horizon.setObjectName("display_rgb_change_green_horizon")
        self.display_rgb_change_green_label = QtWidgets.QLabel()
        self.display_rgb_change_green_label.setAlignment(QtCore.Qt.AlignCenter)
        self.display_rgb_change_green_label.setObjectName("display_rgb_change_green_label")
        self.display_rgb_change_green_range_slider = QtWidgets.QSlider()
        self.display_rgb_change_green_range_slider.setOrientation(QtCore.Qt.Horizontal)
        self.display_rgb_change_green_range_slider.setObjectName("display_rgb_change_green_range_slider")
        self.display_rgb_change_green_range_slider.setTickPosition(2)
        self.display_rgb_change_green_range_slider.setPageStep(10)
        self.display_rgb_change_green_range_slider.setRange(0, 1)
        self.display_rgb_change_green_comboBox = QtWidgets.QComboBox()
        self.display_rgb_change_green_comboBox.setObjectName("display_rgb_change_green_comboBox")

        self.display_rgb_change_blue_horizon = QtWidgets.QHBoxLayout()
        self.display_rgb_change_blue_horizon.setObjectName("display_rgb_change_blue_horizon")
        self.display_rgb_change_blue_label = QtWidgets.QLabel()
        self.display_rgb_change_blue_label.setAlignment(QtCore.Qt.AlignCenter)
        self.display_rgb_change_blue_label.setObjectName("display_rgb_change_blue_label")
        self.display_rgb_change_blue_range_slider = QtWidgets.QSlider()
        self.display_rgb_change_blue_range_slider.setOrientation(QtCore.Qt.Horizontal)
        self.display_rgb_change_blue_range_slider.setObjectName("display_rgb_change_blue_range_slider")
        self.display_rgb_change_blue_range_slider.setTickPosition(2)
        self.display_rgb_change_blue_range_slider.setPageStep(10)
        self.display_rgb_change_blue_range_slider.setRange(0, 1)
        self.display_rgb_change_blue_comboBox = QtWidgets.QComboBox()
        self.display_rgb_change_blue_comboBox.setObjectName("display_rgb_change_blue_comboBox")
        self.display_rgb_change_blue_comboBox.setContentsMargins(10, 0, 10, 0)

        self.display_rgb_change_setting_horizon = QtWidgets.QHBoxLayout()
        self.display_rgb_change_setting_horizon.setObjectName("display_rgb_change_title_horizon")

        self.display_rgb_change_setting_rgb_button = QtWidgets.QPushButton()
        self.display_rgb_change_setting_rgb_button.setObjectName("display_rgb_change_setting_rgb_button")
        self.display_rgb_change_setting_rgb_button.setCheckable(True)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_setting_rgb_button", self.display_rgb_change_setting_rgb_button)

        self.display_rgb_change_setting_default_button = QtWidgets.QPushButton()
        self.display_rgb_change_setting_default_button.setObjectName("display_rgb_change_setting_default_button")
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_setting_default_button", self.display_rgb_change_setting_default_button)
        
        self.display_rgb_change_setting_cmf_button = QtWidgets.QPushButton()
        self.display_rgb_change_setting_cmf_button.setObjectName("display_rgb_change_setting_cmf_button")
        self.display_rgb_change_setting_cmf_button.setCheckable(True)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_setting_cmf_button", self.display_rgb_change_setting_cmf_button)

        self.display_rgb_change_setting_dlcmf_button = QtWidgets.QPushButton()
        self.display_rgb_change_setting_dlcmf_button.setObjectName("display_rgb_change_setting_dlcmf_button")
        self.display_rgb_change_setting_dlcmf_button.setCheckable(True)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_setting_dlcmf_button", self.display_rgb_change_setting_dlcmf_button)

        self.display_rgb_change_reset_horizon = QtWidgets.QHBoxLayout()
        self.display_rgb_change_reset_horizon.setObjectName("display_rgb_change_reset_horizon")

        QtCore.QMetaObject.connectSlotsByName(Form)

    def setup_Ui_display_rgb_change(self, Form):
        Form.setWindowTitle(self.lang.get("labeling", "display_sub_rgb_change", "displayRgbChangeTitle"))
        self.lang.set("labeling", "display_sub_rgb_change", "displayRgbChangeTitle", Form)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_title_color_label", self.display_rgb_change_title_color_label)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_title_band_range_label", self.display_rgb_change_title_band_range_label)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_title_band_label", self.display_rgb_change_title_band_label)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_red_label", self.display_rgb_change_red_label)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_green_label", self.display_rgb_change_green_label)
        self.lang.set("labeling", "display_sub_rgb_change", "display_rgb_change_blue_label", self.display_rgb_change_blue_label)

        """
            description: Added dynamic width adjustment functionality to automatically resize ImageSelectorComboBox based on its content length
            modified by Chansik Kim 2024.12.16
        """
        self.display_rgb_change_title_color_label.setMinimumSize(QtCore.QSize(60, 0))
        self.display_rgb_change_title_color_label.setMaximumSize(QtCore.QSize(60, QT_MAX_SIZE))
        self.display_rgb_change_title_band_range_label.setMinimumSize(QtCore.QSize(250, 0))
        self.display_rgb_change_title_band_range_label.setMaximumSize(QtCore.QSize(250, QT_MAX_SIZE))
        self.display_rgb_change_title_band_label.setMinimumSize(QtCore.QSize(150, 0))
        self.display_rgb_change_title_band_label.setMaximumSize(QtCore.QSize(150, QT_MAX_SIZE))

        self.display_rgb_change_red_label.setMinimumSize(QtCore.QSize(60, 0))
        self.display_rgb_change_red_label.setMaximumSize(QtCore.QSize(60, QT_MAX_SIZE))
        self.display_rgb_change_red_range_slider.setMinimumSize(QtCore.QSize(250, 0))
        self.display_rgb_change_red_range_slider.setMaximumSize(QtCore.QSize(250, QT_MAX_SIZE))
        self.display_rgb_change_red_comboBox.setMinimumSize(QtCore.QSize(150, 0))
        self.display_rgb_change_red_comboBox.setMaximumSize(QtCore.QSize(150, QT_MAX_SIZE))

        self.display_rgb_change_green_label.setMinimumSize(QtCore.QSize(60, 0))
        self.display_rgb_change_green_label.setMaximumSize(QtCore.QSize(60, QT_MAX_SIZE))
        self.display_rgb_change_green_range_slider.setMinimumSize(QtCore.QSize(250, 0))
        self.display_rgb_change_green_range_slider.setMaximumSize(QtCore.QSize(250, QT_MAX_SIZE))
        self.display_rgb_change_green_comboBox.setMinimumSize(QtCore.QSize(150, 0))
        self.display_rgb_change_green_comboBox.setMaximumSize(QtCore.QSize(150, QT_MAX_SIZE))

        self.display_rgb_change_blue_label.setMinimumSize(QtCore.QSize(60, 0))
        self.display_rgb_change_blue_label.setMaximumSize(QtCore.QSize(60, QT_MAX_SIZE))
        self.display_rgb_change_blue_range_slider.setMinimumSize(QtCore.QSize(250, 0))
        self.display_rgb_change_blue_range_slider.setMaximumSize(QtCore.QSize(250, QT_MAX_SIZE))
        self.display_rgb_change_blue_comboBox.setMinimumSize(QtCore.QSize(150, 0))
        self.display_rgb_change_blue_comboBox.setMaximumSize(QtCore.QSize(150, QT_MAX_SIZE))

        self.display_rgb_change_setting_rgb_button.setMinimumSize(QtCore.QSize(100, 30))
        self.display_rgb_change_setting_rgb_button.setMaximumSize(QtCore.QSize(100, 30))
        self.display_rgb_change_setting_cmf_button.setMinimumSize(QtCore.QSize(100, 30))
        self.display_rgb_change_setting_cmf_button.setMaximumSize(QtCore.QSize(100, 30))
        self.display_rgb_change_setting_dlcmf_button.setMinimumSize(QtCore.QSize(100, 30))
        self.display_rgb_change_setting_dlcmf_button.setMaximumSize(QtCore.QSize(100, 30))
        self.display_rgb_change_setting_default_button.setMinimumSize(QtCore.QSize(100, 20))
        self.display_rgb_change_setting_default_button.setMaximumSize(QtCore.QSize(100, 20))

        self.display_rgb_change_title_horizon.addWidget(self.display_rgb_change_title_color_label)
        self.display_rgb_change_title_horizon.addWidget(self.display_rgb_change_title_band_range_label)
        self.display_rgb_change_title_horizon.addWidget(self.display_rgb_change_title_band_label)

        self.display_rgb_change_red_horizon.addWidget(self.display_rgb_change_red_label)
        self.display_rgb_change_red_horizon.addWidget(self.display_rgb_change_red_range_slider)
        self.display_rgb_change_red_horizon.addWidget(self.display_rgb_change_red_comboBox)

        self.display_rgb_change_green_horizon.addWidget(self.display_rgb_change_green_label)
        self.display_rgb_change_green_horizon.addWidget(self.display_rgb_change_green_range_slider)
        self.display_rgb_change_green_horizon.addWidget(self.display_rgb_change_green_comboBox)

        self.display_rgb_change_blue_horizon.addWidget(self.display_rgb_change_blue_label)
        self.display_rgb_change_blue_horizon.addWidget(self.display_rgb_change_blue_range_slider)
        self.display_rgb_change_blue_horizon.addWidget(self.display_rgb_change_blue_comboBox)

        self.display_rgb_change_vbox.addLayout(self.display_rgb_change_title_horizon)
        self.display_rgb_change_vbox.addLayout(self.display_rgb_change_red_horizon)
        self.display_rgb_change_vbox.addLayout(self.display_rgb_change_green_horizon)
        self.display_rgb_change_vbox.addLayout(self.display_rgb_change_blue_horizon)
        self.display_rgb_change_reset_horizon.addWidget(self.display_rgb_change_setting_default_button)
        self.display_rgb_change_vbox.addLayout(self.display_rgb_change_reset_horizon)

    
        self.display_rgb_change_setting_horizon.addWidget(self.display_rgb_change_setting_rgb_button)
        self.display_rgb_change_setting_horizon.addWidget(self.display_rgb_change_setting_cmf_button)
        self.display_rgb_change_setting_horizon.addWidget(self.display_rgb_change_setting_dlcmf_button)

        self.display_rgb_change_visualization_group.setLayout(self.display_rgb_change_setting_horizon)
        self.display_rgb_change_rgb_group.setLayout(self.display_rgb_change_vbox)
        
        self.display_rgb_change_main_grid.addWidget(self.display_rgb_change_visualization_group, 0, 0, 1, 1)
        self.display_rgb_change_main_grid.addWidget(self.display_rgb_change_rgb_group, 1, 0, 1, 1)


    def init_Function(self):
        self.display_rgb_change_red_range_slider.valueChanged.connect(lambda value=self.display_rgb_change_red_range_slider : self.slider_value_change(color_type=SUBRGB_RED, value=value, mode=RGB_SLIDER_CHANGE))
        self.display_rgb_change_green_range_slider.valueChanged.connect(lambda value=self.display_rgb_change_green_range_slider : self.slider_value_change(color_type=SUBRGB_GREEN, value=value, mode=RGB_SLIDER_CHANGE))
        self.display_rgb_change_blue_range_slider.valueChanged.connect(lambda value=self.display_rgb_change_blue_range_slider : self.slider_value_change(color_type=SUBRGB_BLUE, value=value, mode=RGB_SLIDER_CHANGE))

        self.display_rgb_change_red_comboBox.currentIndexChanged.connect(lambda value=self.display_rgb_change_red_comboBox : self.slider_value_change(color_type=SUBRGB_RED, value=value, mode=RGB_COMBOBOX_CHANGE))
        self.display_rgb_change_green_comboBox.currentIndexChanged.connect(lambda value=self.display_rgb_change_green_comboBox : self.slider_value_change(color_type=SUBRGB_GREEN, value=value, mode=RGB_COMBOBOX_CHANGE))
        self.display_rgb_change_blue_comboBox.currentIndexChanged.connect(lambda value=self.display_rgb_change_blue_comboBox : self.slider_value_change(color_type=SUBRGB_BLUE, value=value, mode=RGB_COMBOBOX_CHANGE))
        
        self.display_rgb_change_setting_rgb_button.clicked.connect(lambda ch=self.display_rgb_change_setting_rgb_button : self.button_event(ch=ch, mode=VISUALIZATION_MODE_RGB))
        self.display_rgb_change_setting_cmf_button.clicked.connect(lambda ch=self.display_rgb_change_setting_cmf_button : self.button_event(ch=ch, mode=VISUALIZATION_MODE_CMF))
        self.display_rgb_change_setting_dlcmf_button.clicked.connect(lambda ch=self.display_rgb_change_setting_dlcmf_button : self.button_event(ch=ch, mode=VISUALIZATION_MODE_DLCMF))
        self.display_rgb_change_setting_default_button.clicked.connect(lambda ch=self.display_rgb_change_setting_default_button : self.button_event(ch=ch, mode=3))

    def slider_value_change(self, color_type=None, value=None, mode=0):
        # mode 0일때 콤보박스 값 변경
        # 1일 때 슬라이더 위치 변경
        changed_by = mode
        if self.init_status and not self.slicombo_sw:
            self.slicombo_sw = True
            if changed_by == RGB_SLIDER_CHANGE: # slider 동작시 발동 -> 콤보도 같이 변하게 설정
                if color_type == SUBRGB_RED:
                    self.display_rgb_change_red_comboBox.setCurrentIndex(value)
                elif color_type == SUBRGB_GREEN:
                    self.display_rgb_change_green_comboBox.setCurrentIndex(value)
                elif color_type == SUBRGB_BLUE:
                    self.display_rgb_change_blue_comboBox.setCurrentIndex(value)
            elif changed_by == RGB_COMBOBOX_CHANGE:# 콤보 동작시 발동 -> 슬라이더도 같이 변하게 설정
                if color_type == SUBRGB_RED:
                    self.display_rgb_change_red_range_slider.setValue(value)
                elif color_type == SUBRGB_GREEN:
                    self.display_rgb_change_green_range_slider.setValue(value)
                elif color_type == SUBRGB_BLUE:
                    self.display_rgb_change_blue_range_slider.setValue(value)

            self.tmp_db['hsi_cur_bands'][color_type] = value

            """
                description: Update graph RGB line position in response to slider/combobox change when LinkForRgbLine is True
                author : Hyunsu Kim (2026.04.27)
                History:
                    1. Hyunsu Kim (2026.05.06): Change the tmp_db key from color name string to SUBRGB constants for better consistency and management. Update corresponding code to reflect this change.
            """

            if self.LinkForRgbLine:
                self.displaySubRgbChangeToGraph({"color": color_type, "band": self.tmp_db['hsi_cur_bands'][color_type]})

            tmp_dict={}
            tmp_dict['mode'] = 0
            tmp_dict['hsi_cur_bands'] = self.tmp_db['hsi_cur_bands']
            self.display_sub_rgb_change_to_display(tmp_dict)
            self.slicombo_sw = False

    def button_event(self, ch=None, mode=0):
        #visualization 버튼 클릭시 발생
        if mode == 3: # RGB reset
            self.init_status = False
            red, green, blue = self.tmp_db['hsi_default_bands']
            self.display_rgb_change_red_range_slider.setValue(red)
            self.display_rgb_change_red_comboBox.setCurrentIndex(red)
            self.display_rgb_change_green_range_slider.setValue(green)
            self.display_rgb_change_green_comboBox.setCurrentIndex(green)
            self.display_rgb_change_blue_range_slider.setValue(blue)
            self.display_rgb_change_blue_comboBox.setCurrentIndex(blue)
            tmp_dict={}
            tmp_dict['mode'] = 0
            tmp_dict['hsi_cur_bands'] = [red, green, blue]
            self.tmp_db['hsi_cur_bands'] = [red, green, blue]
            self.display_sub_rgb_change_to_display(tmp_dict)
            self.init_status = True
            """
                description: Update graph RGB line position to default when RGB reset button is clicked
                author : Hyunsu Kim (2026.04.27)
                History:
                    1. Hyunsu Kim (2026.05.06): Change the signal key from color name string to SUBRGB constants for better consistency and management. Update corresponding code to reflect this change.
            """
            self.displaySubRgbChangeToGraph({"color": SUBRGB_RED, "band": red})
            self.displaySubRgbChangeToGraph({"color": SUBRGB_GREEN, "band": green})
            self.displaySubRgbChangeToGraph({"color": SUBRGB_BLUE, "band": blue})
        else:
            if self.cur_btn == mode:
                if mode == VISUALIZATION_MODE_RGB:
                    self.display_rgb_change_setting_rgb_button.setChecked(True)
                elif mode == VISUALIZATION_MODE_CMF:
                    self.display_rgb_change_setting_cmf_button.setChecked(True)
                elif mode == VISUALIZATION_MODE_DLCMF:
                    self.display_rgb_change_setting_dlcmf_button.setChecked(True)
            else:
                self.cur_btn = mode
                self.displaySubRgbChangeToGraph({"currentViewMode":mode})
                if mode == VISUALIZATION_MODE_RGB: # RGB mode
                    self.display_rgb_change_rgb_group.setEnabled(True)
                    self.LinkForRgbLine = True
                    if self.display_rgb_change_setting_cmf_button.isChecked():
                        self.display_rgb_change_setting_cmf_button.toggle()
                    if self.display_rgb_change_setting_dlcmf_button.isChecked():
                        self.display_rgb_change_setting_dlcmf_button.toggle()
                    tmp_dict={}
                    tmp_dict['mode'] = 0
                    tmp_dict['hsi_cur_bands'] = self.tmp_db['hsi_cur_bands']
                    self.display_sub_rgb_change_to_display(tmp_dict)

                    tmp_dict={}
                    tmp_dict['mode'] = 1
                    self.display_sub_rgb_change_to_graph_sub(tmp_dict)

                elif mode == VISUALIZATION_MODE_CMF: # CMF mode
                    self.display_rgb_change_rgb_group.setEnabled(False)
                    self.LinkForRgbLine = False
                    if self.display_rgb_change_setting_rgb_button.isChecked():
                        self.display_rgb_change_setting_rgb_button.toggle()
                    if self.display_rgb_change_setting_dlcmf_button.isChecked():
                        self.display_rgb_change_setting_dlcmf_button.toggle()
                    tmp_dict={}
                    tmp_dict['mode'] = 1
                    self.display_sub_rgb_change_to_display(tmp_dict)

                    tmp_dict={}
                    tmp_dict['mode'] = 0
                    self.display_sub_rgb_change_to_graph_sub(tmp_dict)

                elif mode == VISUALIZATION_MODE_DLCMF: # DLCMF mode
                    self.display_rgb_change_rgb_group.setEnabled(False)
                    self.LinkForRgbLine = False
                    if self.display_rgb_change_setting_rgb_button.isChecked():
                        self.display_rgb_change_setting_rgb_button.toggle()
                    if self.display_rgb_change_setting_cmf_button.isChecked():
                        self.display_rgb_change_setting_cmf_button.toggle()
                    tmp_dict={}
                    tmp_dict['mode'] = 2
                    self.display_sub_rgb_change_to_display(tmp_dict)                

                    tmp_dict={}
                    tmp_dict['mode'] = 0
                    self.display_sub_rgb_change_to_graph_sub(tmp_dict)


    def combobox_clear(self):
        self.display_rgb_change_red_range_slider.setRange(0, 1)
        self.display_rgb_change_green_range_slider.setRange(0, 1)
        self.display_rgb_change_blue_range_slider.setRange(0, 1)
        
        self.display_rgb_change_red_range_slider.setValue(0)
        self.display_rgb_change_green_range_slider.setValue(0)
        self.display_rgb_change_blue_range_slider.setValue(0)

        self.display_rgb_change_red_comboBox.clear()
        self.display_rgb_change_green_comboBox.clear()
        self.display_rgb_change_blue_comboBox.clear()

    @pyqtSlot(dict)
    def recv_core_to_display_sub_rgb_change(self, output):
        # 받는곳, hsi data 업데이트 되면 활성화
        self.init_status = False
        mode = output['mode']
        if mode == "load":
            self.combobox_clear()
            self.displaySubRgbChangeToGraph({"currentViewMode":VISUALIZATION_MODE_RGB})
            self.display_rgb_change_visualization_group.setEnabled(True)
            self.display_rgb_change_rgb_group.setEnabled(True)
            self.display_rgb_change_setting_rgb_button.setChecked(True)
            if self.display_rgb_change_setting_cmf_button.isChecked():
                self.display_rgb_change_setting_cmf_button.toggle()
            if self.display_rgb_change_setting_dlcmf_button.isChecked():
               self.display_rgb_change_setting_dlcmf_button.toggle()
            self.cur_btn = 0

            self.tmp_db['hsi_default_bands'] = copy.deepcopy(output['hsi_default_bands'])
            self.tmp_db['hsi_cur_bands'] = copy.deepcopy(output['hsi_default_bands'])
            self.tmp_db['hsi_wave_length']  =  copy.deepcopy(output['hsi_wave_length'])
            self.tmp_db['hsi_wave_count'] = output['hsi_wave_count']

            self.display_rgb_change_red_range_slider.setRange(0, self.tmp_db['hsi_wave_count']-1)
            self.display_rgb_change_green_range_slider.setRange(0, self.tmp_db['hsi_wave_count']-1)
            self.display_rgb_change_blue_range_slider.setRange(0, self.tmp_db['hsi_wave_count']-1)

            for i in range(self.tmp_db['hsi_wave_count']):
                band_number = i
                wave_number = self.tmp_db['hsi_wave_length'][i]
                tmp_str = f"{band_number}: {wave_number}"
                self.display_rgb_change_red_comboBox.addItem(tmp_str)
                self.display_rgb_change_green_comboBox.addItem(tmp_str)
                self.display_rgb_change_blue_comboBox.addItem(tmp_str)

            red, green, blue = self.tmp_db['hsi_default_bands']
            print(f"HSI default Bands : {self.tmp_db['hsi_default_bands']}")
            self.display_rgb_change_red_range_slider.setValue(red)
            self.display_rgb_change_red_comboBox.setCurrentIndex(red)
            self.display_rgb_change_green_range_slider.setValue(green)
            self.display_rgb_change_green_comboBox.setCurrentIndex(green)
            self.display_rgb_change_blue_range_slider.setValue(blue)
            self.display_rgb_change_blue_comboBox.setCurrentIndex(blue)
            self.init_status = True

            tmp_dict={}
            tmp_dict['mode'] = 0
            tmp_dict['hsi_cur_bands'] = [red, green, blue]
            print("init HSI image")
            self.display_sub_rgb_change_to_display(tmp_dict)
            
        elif mode == "unload":
            self.display_rgb_change_visualization_group.setEnabled(False)
            self.display_rgb_change_rgb_group.setEnabled(False)
            self.init_status = False

        elif mode == "graph":
            """
                description: Change the slider value based on the signal received from the graph, or set the synchronization status based on whether the RGB Graph Support function is enabled.
                author : Hyunsu Kim (2026.04.27)
            """
            self.init_status = True
            if output['type'] == "rgbLines":
                band = output["band"]
                color = output["color"]

                if color == "red":
                    self.display_rgb_change_red_range_slider.setValue(band)
                elif color == "green":
                    self.display_rgb_change_green_range_slider.setValue(band)
                else:
                    self.display_rgb_change_blue_range_slider.setValue(band)
            
            elif output['type'] == "hideRgbLines":
                self.LinkForRgbLine = False

            elif output['type'] == "showRgbLines":
                self.LinkForRgbLine = True
        
    def display_sub_rgb_change_to_display(self, input):
        """display sub rgb에서 display로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 display에 최종적으로 전달된다.
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary

        """
        self.display_sub_rgb_change_to_display_signal.emit(input)

    def display_sub_rgb_change_to_graph_sub(self, input):
        """display sub rgb에서 graph sub로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 graph sub에 최종적으로 전달된다.
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary

        """
        self.display_sub_rgb_change_to_graph_sub_signal.emit(input)

    def displaySubRgbChangeToGraph(self, input):
        """
            description: Function declaration for sending signals from display sub rgb change to graph. The signal is first sent to the core and then finally delivered to the graph.
            parameters
            1. input(dict): dictionary for graph update
        """
        self.displaySubRgbChangeToGraphSignal.emit(input)

    def closeEvent(self, _):
        if self.pen_obj_dict['pen_bright']['opened']:
            self.pen_obj_dict['pen_bright']['obj'].toggle()
            self.pen_obj_dict['pen_bright']['opened'] = False


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Display_rgb_change_Form()
    # ui.setupUi(Form)
    # Form.show()
    sys.exit(app.exec_())
