import numpy as np

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from qtwidgets import AnimatedToggle



class graph_sub_Form(QtWidgets.QDialog):
    def __init__(self, Sync=None, lang=None, parent=None) -> None:
        super().__init__()

        self.init(Sync=Sync, lang=lang, parent=parent)
        self.init_ui(self)
        self.setup_ui()
        self.init_function()
        self.init_variable()

        if __name__ == "__main__":
            self.show()
    
    def init(self, Sync=None, lang=None, parent=None):
        self.lang = lang
        self.Sync = Sync
        self.parent = parent
        
        #signal
        self.graph_sub_to_display_signal = self.Sync.graph_sub_to_display_signal
        self.core_to_graph_sub_signal = self.Sync.core_to_graph_sub_signal
        self.core_to_graph_sub_signal.connect(self.recv_from_core)

        # obj_dict
        self.graph_obj_dict = self.Sync.graph_obj_dict
        self.image_control_dict = self.Sync.image_control_dict
        self.Core_DB_Labeling = self.Sync.Core_DB_Labeling


    def init_variable(self):
        """
        """
        self.connect_sw = True # 버튼의 상태를 변경할때 사용, True 사용시 버튼 토글이벤트 발생을 방지하기 위함

    @pyqtSlot(dict)
    def recv_from_core(self, output):
        """
            recv output when image select
        """
        self.connect_sw = True
        from_ = output['from']
        mode = output['mode']
        if from_ == 'image':
            mode_detail = output['mode_detail']
            if mode: #image select
                self.reset_()
                self.setEnabled(True)
                if mode_detail == 1:# calibration mode, 버튼들 초기화 및 활성화
                    self.update_state(_type = 2, _type_2 = 1)
                else:  # no calibration data
                    self.update_state(_type = 1, _type_2 = 0)
                self.update_state(_type = 0)
            else: #image not select
                self.setEnabled(False)
            self.connect_sw = False
        elif from_ == 'display_sub_rgb_change':
            if mode: # graph sub mode enable
                self.graph_sub_adv_group.setEnabled(True)
                self.graph_sub_calib_group.setEnabled(True)
            else: # graph sub mode disable
                self.graph_sub_adv_group.setEnabled(False)
                self.graph_sub_calib_group.setEnabled(False)
            self.connect_sw = False
            


    def init_ui(self, Form):
        Form.setObjectName("graph_sub_form")
        Form.setFixedSize(290, 340)
        self.lang.set("labeling", "graph_sub", "graphSubWindowTitle", Form)
        Form.setEnabled(False)
        # Ensure the settings window always stays on top for improved accessibility and user convenience.
        Form.setWindowModality(QtCore.Qt.ApplicationModal)
        Form.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)
        
        self.graph_sub_main_vertical = QtWidgets.QVBoxLayout(Form)
        self.graph_sub_main_vertical.setObjectName("graph_sub_main_vertical")

        self.graph_sub_calib_group = QtWidgets.QGroupBox()
        self.graph_sub_calib_group.setObjectName("groupBox")
        self.lang.set("labeling", "graph_sub", "graphSubCalibration", self.graph_sub_calib_group)

        self.graph_sub_calib_vertical = QtWidgets.QVBoxLayout(self.graph_sub_calib_group)
        self.graph_sub_calib_vertical.setObjectName("graph_sub_calib_vertical")

        self.graph_sub_calib_mode_label = QtWidgets.QLabel()
        self.graph_sub_calib_mode_label.setObjectName("graph_sub_calib_mode_label")
        self.lang.set("labeling", "graph_sub", "graphSubMode", self.graph_sub_calib_mode_label)
        
        self.graph_sub_calib_mode_toggle = AnimatedToggle(
            pulse_checked_color="transparent",
            pulse_unchecked_color="transparent"
        )
        # self.graph_sub_calib_mode_toggle.setEnabled(False)
        self.graph_sub_calib_mode_toggle.setObjectName("graph_sub_calib_mode_toggle")

        self.graph_sub_calib_mode_horizon = QtWidgets.QHBoxLayout()
        self.graph_sub_calib_mode_horizon.setObjectName("graph_sub_calib_mode_horizon")

        self.graph_sub_calib_ratio_horizon = QtWidgets.QHBoxLayout()
        self.graph_sub_calib_ratio_horizon.setObjectName("graph_sub_calib_ratio_horizon")

        self.graph_sub_calib_ratio_label = QtWidgets.QLabel()
        self.graph_sub_calib_ratio_label.setObjectName("graph_sub_calib_ratio_label")
        self.lang.set("labeling", "graph_sub", "graphSubRatio", self.graph_sub_calib_ratio_label)

        self.graph_sub_calib_apply_btn = QtWidgets.QPushButton()
        self.graph_sub_calib_apply_btn.setObjectName("graph_sub_calib_apply_btn")
        self.lang.set("labeling", "graph_sub", "graphSubApply", self.graph_sub_calib_apply_btn)
        
        self.graph_sub_calib_ratio_spinbox = QtWidgets.QSpinBox()
        self.graph_sub_calib_ratio_spinbox.setObjectName("graph_sub_calib_ratio_spinbox")
        self.graph_sub_calib_ratio_spinbox.setEnabled(False)
        self.graph_sub_calib_ratio_spinbox.setSuffix(' %')
        self.graph_sub_calib_ratio_spinbox.setRange(1,100)
        self.graph_sub_calib_ratio_spinbox.setValue(100)

        self.graph_sub_adv_group = QtWidgets.QGroupBox()
        self.graph_sub_adv_group.setObjectName("graph_sub_adv_group")
        self.lang.set("labeling", "graph_sub", "graphSubAdvanced", self.graph_sub_adv_group)
        
        
        self.graph_sub_adv_vertical = QtWidgets.QVBoxLayout(self.graph_sub_adv_group)
        self.graph_sub_adv_vertical.setObjectName("graph_sub_adv_vertical")

        self.graph_sub_adv_horizon = QtWidgets.QHBoxLayout()
        self.graph_sub_adv_horizon.setObjectName("graph_sub_adv_horizon")

        self.graph_sub_adv_mode_label = QtWidgets.QLabel()
        self.graph_sub_adv_mode_label.setObjectName("graph_sub_adv_mode_label")
        self.lang.set("labeling", "graph_sub","graphSubMode", self.graph_sub_adv_mode_label)

        self.graph_sub_adv_mode_toggle = AnimatedToggle(
            pulse_checked_color="transparent",
            pulse_unchecked_color="transparent"
        )
        self.graph_sub_adv_mode_toggle.setObjectName("graph_sub_adv_mode_toggle")


        # self.graph_sub_combobox_select_color = QtWidgets.QComboBox()
        # self.graph_sub_combobox_select_color.setObjectName("graph_combobox_select_color")
        # self.graph_sub_combobox_select_color.addItem("Random Color View")
        # self.graph_sub_combobox_select_color.addItem("Selective Color View")
        # self.graph_sub_combobox_select_color.addItem("Label Color View")
        # self.graph_sub_combobox_select_color.setCurrentIndex(1)
        # self.graph_sub_combobox_select_color.setEnabled(False)
        
        self.graph_sub_etc_group = QtWidgets.QGroupBox(Form)
        self.graph_sub_etc_group.setObjectName("graph_sub_etc_group")
        self.lang.set("labeling", "graph_sub", "graphSubEtc", self.graph_sub_etc_group)

        self.graph_sub_etc_vertical = QtWidgets.QVBoxLayout(self.graph_sub_etc_group)
        self.graph_sub_etc_vertical.setObjectName("graph_sub_etc_vertical")

        self.graph_sub_etc_save_btn = QtWidgets.QPushButton(self.graph_sub_etc_group)
        self.graph_sub_etc_save_btn.setObjectName("graph_sub_etc_save_btn")
        self.lang.set("labeling", "graph_sub", "graphSubSave", self.graph_sub_etc_save_btn)
        QtCore.QMetaObject.connectSlotsByName(Form)


    def setup_ui(self):
        self.graph_sub_calib_mode_horizon.addWidget(self.graph_sub_calib_mode_label)
        self.graph_sub_calib_mode_horizon.addWidget(self.graph_sub_calib_mode_toggle)
        self.graph_sub_calib_ratio_horizon.addWidget(self.graph_sub_calib_ratio_label)
        self.graph_sub_calib_ratio_horizon.addWidget(self.graph_sub_calib_ratio_spinbox)
        self.graph_sub_calib_vertical.addLayout(self.graph_sub_calib_mode_horizon)
        self.graph_sub_calib_vertical.addLayout(self.graph_sub_calib_ratio_horizon)
        self.graph_sub_calib_vertical.addWidget(self.graph_sub_calib_apply_btn)
        self.graph_sub_main_vertical.addWidget(self.graph_sub_calib_group)

        self.graph_sub_adv_horizon.addWidget(self.graph_sub_adv_mode_label)
        self.graph_sub_adv_horizon.addWidget(self.graph_sub_adv_mode_toggle)

        self.graph_sub_adv_vertical.addLayout(self.graph_sub_adv_horizon)
        self.graph_sub_main_vertical.addWidget(self.graph_sub_adv_group)

        self.graph_sub_etc_vertical.addWidget(self.graph_sub_etc_save_btn)
        self.graph_sub_main_vertical.addWidget(self.graph_sub_etc_group)

    
    def init_function(self):
        self.graph_sub_calib_mode_toggle.clicked.connect(lambda ch = self.graph_sub_calib_mode_toggle: self.graph_sub_mode(ch=ch, mode=1))
        self.graph_sub_calib_apply_btn.clicked.connect(lambda ch = self.graph_sub_calib_apply_btn: self.graph_sub_mode(ch=ch, mode=0))
        self.graph_sub_adv_mode_toggle.clicked.connect(lambda ch = self.graph_sub_calib_mode_toggle: self.graph_sub_mode(ch=ch, mode=2))

    def reset_(self):
        self.graph_sub_calib_ratio_spinbox.setValue(100)
        self.graph_sub_adv_group.setEnabled(True)
        self.graph_sub_calib_group.setEnabled(True)


    def graph_sub_mode(self, ch, mode):
        if self.connect_sw: #before init
            pass
        else: # after init
            #calibration
            if mode == 0: # calibration value apply
                tmp_dict = {}
                tmp_dict['mode'] = 0
                tmp_dict['_type'] = 1
                tmp_dict['value'] = self.graph_sub_calib_ratio_spinbox.value() / 100
                self.graph_sub_to_display(tmp_dict)

            elif mode == 1: # calib on/off
                tmp_dict = {}
                tmp_dict['mode'] = 0
                tmp_dict['value'] = self.graph_sub_calib_ratio_spinbox.value() / 100
                if ch:#on
                    self.graph_sub_calib_ratio_spinbox.setEnabled(True)
                    self.graph_sub_calib_apply_btn.setEnabled(True)
                    tmp_dict['_type'] = 1
                else:#off
                    self.graph_sub_calib_ratio_spinbox.setEnabled(False)
                    self.graph_sub_calib_apply_btn.setEnabled(False)
                    tmp_dict['_type'] = 0
                self.graph_sub_to_display(tmp_dict)

            elif mode == 2:# advanced mode(norm visualization)
                self.connect_sw = True
                tmp_dict = {}
                tmp_dict['mode'] = 1
                tmp_dict['value'] = self.graph_sub_calib_ratio_spinbox.value() / 100
                tmp_dict['calib_mode'] = self.graph_sub_calib_mode_toggle.isChecked()
                if ch: #on
                    self.update_state(_type = 1)
                    tmp_dict['_type'] = 1
                else: #off
                    self.update_state(_type = 2)
                    tmp_dict['_type'] = 0
                self.graph_sub_to_display(tmp_dict)
                self.connect_sw = False
            


    def update_state(self, _type=int, _type_2=int):
        """
            1. _type(int)
                - 0: adv toggle btn OFF
                - 1: calib obj Enable False
                - 2: calib obj Enable True
            2. _type_2(int)
                - 0: calib toggle btn OFF
                - 1: calib toggle btn ON
        """
        if _type == 0:# only init
            if self.graph_sub_adv_mode_toggle.isChecked():
                self.graph_sub_adv_mode_toggle.toggle()
        elif _type == 1:# object off
            self.graph_sub_calib_mode_toggle.setEnabled(False)
            self.graph_sub_calib_ratio_spinbox.setEnabled(False)
            self.graph_sub_calib_apply_btn.setEnabled(False)
        elif _type == 2:# object on
            self.graph_sub_calib_mode_toggle.setEnabled(True)
            self.graph_sub_calib_ratio_spinbox.setEnabled(True)
            self.graph_sub_calib_apply_btn.setEnabled(True)
        

        if _type_2 == 0: #calibration btn on
            if self.graph_sub_calib_mode_toggle.isChecked():
                self.graph_sub_calib_mode_toggle.toggle()
        elif _type_2 == 1: #calibration btn off
            if self.graph_sub_calib_mode_toggle.isChecked() == False:
                self.graph_sub_calib_mode_toggle.toggle()
        
    def graph_sub_to_display(self, input):
        self.graph_sub_to_display_signal.emit(input)

    def closeEvent(self, e):
        if self.parent.graph_setting_temp.isChecked():
            self.parent.graph_setting_temp.toggle()
        
 

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = graph_sub_Form()
    sys.exit(app.exec_())
