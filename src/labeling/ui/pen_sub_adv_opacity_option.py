from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from labeling.stylesheet.stylesheet_pen_sub_adv_opacity_option import stylesheet
"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

class pen_sub_adv_opacity_option_Form(QtWidgets.QDialog):
    def __init__(self, Sync=None, lang=None, parent=None) -> None:
        super().__init__()
        self.init(Sync=Sync, lang=lang, parent=parent)
        self.init_variable()
        self.init_ui(self)
        self.setup_ui()
        self.init_function()
        if __name__ == "__main__":
            self.show()

    def init(self, Sync=None, lang=None, parent=None):
        self.Sync = Sync
        self.lang = lang
        self.parent = parent

        self.label_obj_dict = self.parent.label_obj_dict

    def init_variable(self):
        """
            @description: 초기 변수 선언부분
            @author : MyoungHwan (2024.09.06)
            @parameters
                - self.global_sw: global 옵션 발동시 동시처리를 방지하기 위한 스위칭 변수
                - self.global_value: 투명도 값을 일괄적으로 처리하기 위한 global 변수
                - self.specific_sw: specific 옵션 발동시 동시처리를 방지하기 위한 스위칭 변수
                - self.label_opcaity_dict: 라벨별 투명도에 대한 정보를 딕셔너리형태로 저장
        """
        self.global_sw = True
        self.specific_sw = True
        self.global_value = 100
        self.label_opcaity_dict = {}

    def init_ui(self, Form):
        """
            @description: 초기 UI 선언부분
            @author : MyoungHwan (2024.09.06)
        """
        Form.setObjectName("adv_opacity_setting_form")
        Form.setFixedSize(318, 240)
        self.lang.set("labeling","penSubOpacity", "penOpacityTitle", Form) 
        # Ensure the settings window always stays on top for improved accessibility and user convenience.
        Form.setWindowModality(QtCore.Qt.ApplicationModal)
        Form.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)
        Form.setStyleSheet(stylesheet)
        
        self.pen_sub_adv_opacity_main_vertical = QtWidgets.QVBoxLayout(Form)
        self.pen_sub_adv_opacity_main_vertical.setObjectName("pen_sub_adv_opacity_main_vertical")

        self.pen_sub_adv_opacity_sub_global_groupbox = QtWidgets.QGroupBox()
        self.pen_sub_adv_opacity_sub_global_groupbox.setObjectName("pen_sub_adv_opacity_sub_global_groupbox")
        self.lang.set("labeling","penSubOpacity", "penOpacityGlobalSetting", self.pen_sub_adv_opacity_sub_global_groupbox)

        self.pen_sub_adv_opacity_sub_global_vertical = QtWidgets.QVBoxLayout()
        self.pen_sub_adv_opacity_sub_global_vertical.setObjectName("pen_sub_adv_opacity_sub_global_vertical")

        self.pen_sub_adv_opacity_sub_global_horizon = QtWidgets.QHBoxLayout()
        self.pen_sub_adv_opacity_sub_global_horizon.setObjectName("pen_sub_adv_opacity_sub_global_horizon") 

        self.pen_sub_adv_opacity_sub_global_horizon_2 = QtWidgets.QHBoxLayout()
        self.pen_sub_adv_opacity_sub_global_horizon_2.setObjectName("pen_sub_adv_opacity_sub_global_horizon_2")

        self.pen_sub_adv_opacity_sub_global_horizon_3 = QtWidgets.QHBoxLayout()
        self.pen_sub_adv_opacity_sub_global_horizon_3.setObjectName("pen_sub_adv_opacity_sub_global_horizon_3") 

        self.pen_sub_adv_opacity_sub_global_label = QtWidgets.QLabel()
        self.pen_sub_adv_opacity_sub_global_label.setObjectName("pen_sub_adv_opacity_sub_global_label")
        self.lang.set("labeling","penSubOpacity","penOpacityRatio", self.pen_sub_adv_opacity_sub_global_label)
                      
        self.pen_sub_adv_opacity_sub_global_spin = QtWidgets.QSpinBox()
        self.pen_sub_adv_opacity_sub_global_spin.setObjectName("pen_sub_adv_opacity_sub_global_spin")
        self.pen_sub_adv_opacity_sub_global_spin.setRange(0, 100)
        self.pen_sub_adv_opacity_sub_global_spin.setValue(self.global_value)
        self.pen_sub_adv_opacity_sub_global_spin.setSingleStep(5)
        self.pen_sub_adv_opacity_sub_global_spin.setSuffix(" %")

        self.pen_sub_adv_opacity_sub_global_slider = QtWidgets.QSlider()
        self.pen_sub_adv_opacity_sub_global_slider.setObjectName("pen_sub_adv_opacity_sub_global_spin_slider")
        self.pen_sub_adv_opacity_sub_global_slider.setOrientation(QtCore.Qt.Horizontal)
        self.pen_sub_adv_opacity_sub_global_slider.setPageStep(5)
        self.pen_sub_adv_opacity_sub_global_slider.setValue(self.global_value)
        self.pen_sub_adv_opacity_sub_global_slider.setRange(0, 100)

        self.pen_sub_adv_opacity_sub_global_default_btn = QtWidgets.QPushButton()
        self.pen_sub_adv_opacity_sub_global_default_btn.setObjectName("pen_sub_adv_opacity_sub_global_default_btn")
        self.lang.set("labeling","penSubOpacity","penOpacityDefault", self.pen_sub_adv_opacity_sub_global_default_btn)

        self.pen_sub_adv_opacity_sub_global_apply_btn = QtWidgets.QPushButton()
        self.pen_sub_adv_opacity_sub_global_apply_btn.setObjectName("pen_sub_adv_opacity_sub_global_apply_btn")
        self.lang.set("labeling","penSubOpacity", "penOpacityApply", self.pen_sub_adv_opacity_sub_global_apply_btn)

        self.pen_sub_adv_opacity_sub_specific_groupbox = QtWidgets.QGroupBox()
        self.pen_sub_adv_opacity_sub_specific_groupbox.setObjectName("pen_sub_adv_opacity_sub_specific_groupbox")
        self.lang.set("labeling","penSubOpacity", "penOpacitySpecificTitle", self.pen_sub_adv_opacity_sub_specific_groupbox)

        self.pen_sub_adv_opacity_sub_specific_vertical = QtWidgets.QVBoxLayout()
        self.pen_sub_adv_opacity_sub_specific_vertical.setObjectName("pen_sub_adv_opacity_sub_specific_vertical")

        self.pen_sub_adv_opacity_sub_specific_horizon = QtWidgets.QHBoxLayout()
        self.pen_sub_adv_opacity_sub_specific_horizon.setObjectName("pen_sub_adv_opacity_sub_specific_horizon")

        self.pen_sub_adv_opacity_sub_specific_horizon_2 = QtWidgets.QHBoxLayout()
        self.pen_sub_adv_opacity_sub_specific_horizon_2.setObjectName("pen_sub_adv_opacity_sub_specific_horizon_2")

        self.pen_sub_adv_opacity_sub_specific_horizon_3 = QtWidgets.QHBoxLayout()
        self.pen_sub_adv_opacity_sub_specific_horizon_3.setObjectName("pen_sub_adv_opacity_sub_specific_horizon_3")

        self.pen_sub_adv_opacity_sub_specific_label = QtWidgets.QLabel()
        self.pen_sub_adv_opacity_sub_specific_label.setObjectName("pen_sub_adv_opacity_sub_specific_label")
        self.lang.set("labeling","penSubOpacity","penOpacityRatio",self.pen_sub_adv_opacity_sub_specific_label)

        self.pen_sub_adv_opacity_sub_specific_combo = QtWidgets.QComboBox()
        self.pen_sub_adv_opacity_sub_specific_combo.setObjectName("pen_sub_adv_opacity_sub_specific_combo")
        self.pen_sub_adv_opacity_sub_specific_combo.addItem(f"Select Label")

        self.pen_sub_adv_opacity_sub_specific_spin = QtWidgets.QSpinBox()
        self.pen_sub_adv_opacity_sub_specific_spin.setObjectName("pen_sub_adv_opacity_sub_specific_spin")
        self.pen_sub_adv_opacity_sub_specific_spin.setRange(0, 100)
        self.pen_sub_adv_opacity_sub_specific_spin.setValue(self.global_value)
        self.pen_sub_adv_opacity_sub_specific_spin.setSingleStep(5)
        self.pen_sub_adv_opacity_sub_specific_spin.setSuffix(" %")

        self.pen_sub_adv_opacity_sub_specific_slider = QtWidgets.QSlider()
        self.pen_sub_adv_opacity_sub_specific_slider.setObjectName("pen_sub_adv_opacity_sub_specific_slider")
        self.pen_sub_adv_opacity_sub_specific_slider.setOrientation(QtCore.Qt.Horizontal)
        self.pen_sub_adv_opacity_sub_specific_slider.setPageStep(5)
        self.pen_sub_adv_opacity_sub_specific_slider.setRange(0, 100)
        self.pen_sub_adv_opacity_sub_specific_slider.setValue(self.global_value)

        self.pen_sub_adv_opacity_sub_specific_default_btn = QtWidgets.QPushButton()
        self.pen_sub_adv_opacity_sub_specific_default_btn.setObjectName("pen_sub_adv_opacity_sub_specific_default_btn")
        self.lang.set("labeling","penSubOpacity", "penOpacityDefault", self.pen_sub_adv_opacity_sub_specific_default_btn)
        
        self.pen_sub_adv_opacity_sub_specific_apply_btn = QtWidgets.QPushButton()
        self.pen_sub_adv_opacity_sub_specific_apply_btn.setObjectName("pen_sub_adv_opacity_sub_specific_apply_btn")
        self.lang.set("labeling","penSubOpacity", "penOpacityApply", self.pen_sub_adv_opacity_sub_specific_apply_btn)

        self.pen_sub_adv_opacity_sub_setting_view_label = QtWidgets.QLabel()
        self.pen_sub_adv_opacity_sub_setting_view_label.setObjectName("pen_sub_adv_opacity_sub_setting_view_label")
        self.pen_sub_adv_opacity_sub_setting_view_label.setText("")

        self.pen_sub_adv_opacity_sub_btn_horizon = QtWidgets.QHBoxLayout()
        self.pen_sub_adv_opacity_sub_btn_horizon.setObjectName("pen_sub_adv_opacity_sub_btn_horizon")


    def setup_ui(self):
        """
            @description: 초기 UI 선언에 대한 설정 부분
            @author : MyoungHwan (2024.09.06)
        """
        self.pen_sub_adv_opacity_sub_global_horizon.addWidget(self.pen_sub_adv_opacity_sub_global_label)
        self.pen_sub_adv_opacity_sub_global_horizon_2.addWidget(self.pen_sub_adv_opacity_sub_global_slider)
        self.pen_sub_adv_opacity_sub_global_horizon_2.addWidget(self.pen_sub_adv_opacity_sub_global_spin)
        self.pen_sub_adv_opacity_sub_global_horizon_3.addWidget(self.pen_sub_adv_opacity_sub_global_default_btn)
        self.pen_sub_adv_opacity_sub_global_horizon_3.addWidget(self.pen_sub_adv_opacity_sub_global_apply_btn)
        self.pen_sub_adv_opacity_sub_global_vertical.addLayout(self.pen_sub_adv_opacity_sub_global_horizon)
        self.pen_sub_adv_opacity_sub_global_vertical.addLayout(self.pen_sub_adv_opacity_sub_global_horizon_2)
        self.pen_sub_adv_opacity_sub_global_vertical.addLayout(self.pen_sub_adv_opacity_sub_global_horizon_3)

        self.pen_sub_adv_opacity_sub_specific_horizon.addWidget(self.pen_sub_adv_opacity_sub_specific_label)
        self.pen_sub_adv_opacity_sub_specific_horizon.addWidget(self.pen_sub_adv_opacity_sub_specific_combo)
        self.pen_sub_adv_opacity_sub_specific_horizon_2.addWidget(self.pen_sub_adv_opacity_sub_specific_slider)
        self.pen_sub_adv_opacity_sub_specific_horizon_2.addWidget(self.pen_sub_adv_opacity_sub_specific_spin)
        self.pen_sub_adv_opacity_sub_specific_horizon_3.addWidget(self.pen_sub_adv_opacity_sub_specific_default_btn)
        self.pen_sub_adv_opacity_sub_specific_horizon_3.addWidget(self.pen_sub_adv_opacity_sub_specific_apply_btn)
        self.pen_sub_adv_opacity_sub_specific_vertical.addLayout(self.pen_sub_adv_opacity_sub_specific_horizon)
        self.pen_sub_adv_opacity_sub_specific_vertical.addLayout(self.pen_sub_adv_opacity_sub_specific_horizon_2)
        self.pen_sub_adv_opacity_sub_specific_vertical.addLayout(self.pen_sub_adv_opacity_sub_specific_horizon_3)

        self.pen_sub_adv_opacity_sub_global_groupbox.setLayout(self.pen_sub_adv_opacity_sub_global_vertical)
        self.pen_sub_adv_opacity_sub_specific_groupbox.setLayout(self.pen_sub_adv_opacity_sub_specific_vertical)

        self.pen_sub_adv_opacity_main_vertical.addWidget(self.pen_sub_adv_opacity_sub_global_groupbox)
        self.pen_sub_adv_opacity_main_vertical.addWidget(self.pen_sub_adv_opacity_sub_specific_groupbox)


    def init_function(self):
        """
            @description: UI 내부 버튼 사용에 대한 signal 정의 부분
            @author : MyoungHwan (2024.09.06)
        """
        self.pen_sub_adv_opacity_sub_global_default_btn.clicked.connect(lambda ch=self.pen_sub_adv_opacity_sub_global_default_btn : self.button_event(mode=0,ch=ch ))
        self.pen_sub_adv_opacity_sub_global_apply_btn.clicked.connect(lambda ch=self.pen_sub_adv_opacity_sub_global_apply_btn : self.button_event(mode=1,ch=ch ))
        self.pen_sub_adv_opacity_sub_global_spin.valueChanged.connect(lambda value=self.pen_sub_adv_opacity_sub_global_spin : self.global_value_change(mode=0, value=value))
        self.pen_sub_adv_opacity_sub_global_slider.valueChanged.connect(lambda value=self.pen_sub_adv_opacity_sub_global_slider : self.global_value_change(mode=1, value=value))

        self.pen_sub_adv_opacity_sub_specific_default_btn.clicked.connect(lambda ch=self.pen_sub_adv_opacity_sub_specific_default_btn : self.button_event(mode=2,ch=ch ))
        self.pen_sub_adv_opacity_sub_specific_apply_btn.clicked.connect(lambda ch=self.pen_sub_adv_opacity_sub_specific_apply_btn : self.button_event(mode=3,ch=ch ))
        self.pen_sub_adv_opacity_sub_specific_combo.currentIndexChanged.connect(lambda value=self.pen_sub_adv_opacity_sub_specific_combo : self.specific_value_change(mode=0, value=value))
        self.pen_sub_adv_opacity_sub_specific_spin.valueChanged.connect(lambda value=self.pen_sub_adv_opacity_sub_specific_spin : self.specific_value_change(mode=1, value=value))
        self.pen_sub_adv_opacity_sub_specific_slider.valueChanged.connect(lambda value=self.pen_sub_adv_opacity_sub_specific_slider : self.specific_value_change(mode=2, value=value))


    def global_value_change(self, mode, value):
        """
            @description: Global 옵션들을 사용하기 위한 함수
            @author : MyoungHwan (2024.09.06)
        """
        if self.specific_sw:
            self.specific_sw = False
            if mode == 0:
                self.pen_sub_adv_opacity_sub_global_slider.setValue(value)
            elif mode == 1:
                self.pen_sub_adv_opacity_sub_global_spin.setValue(value)
            tmp_dict = {}
            tmp_dict['mode'] = 'preview_global'
            tmp_dict["value"] = value / 100
            self.parent.pen_opacity_to_display(tmp_dict)
            self.specific_sw = True

    def specific_value_change(self, mode, value):
        """
            @description: Specific 옵션들을 사용하기 위한 함수
            @author : MyoungHwan (2024.09.06)
        """
        if self.specific_sw:
            self.specific_sw = False
            if mode == 0: # combo
                label_num = self.label_order_list[value]
                cur_value = self.label_opcaity_dict[label_num]['change'] * 100
                self.pen_sub_adv_opacity_sub_specific_spin.setValue(cur_value)
                self.pen_sub_adv_opacity_sub_specific_slider.setValue(cur_value)
            elif mode == 1:
                self.pen_sub_adv_opacity_sub_specific_slider.setValue(value)
            elif mode == 2:
                self.pen_sub_adv_opacity_sub_specific_spin.setValue(value)
            
            if mode in [1,2]:
                cur_idx = self.pen_sub_adv_opacity_sub_specific_combo.currentIndex()
                label_num = self.label_order_list[cur_idx]
                tmp_dict = {}
                tmp_dict['mode'] = 'preview_specific'
                tmp_dict['label_list'] = label_num
                tmp_dict["value"] = value / 100
                self.parent.pen_opacity_to_display(tmp_dict)
            self.specific_sw = True

    def button_event(self, mode, ch):
        """
            @description: Global/Specific 버튼들을 사용하기 위한 함수
            @author : MyoungHwan (2024.09.06)
        """
        if self.specific_sw:
            self.specific_sw = False
            if mode == 0: #Default btn
                self.global_value = 100
                self.pen_sub_adv_opacity_sub_global_spin.setValue(self.global_value)
                self.pen_sub_adv_opacity_sub_global_slider.setValue(self.global_value)

                tmp_dict = {}
                tmp_dict['mode'] = 'preview_global'
                tmp_dict["value"] = self.global_value / 100
                self.parent.pen_opacity_to_display(tmp_dict)

            elif mode == 1: # global apply
                self.global_value = self.pen_sub_adv_opacity_sub_global_spin.value()
                for key in self.label_obj_dict.keys():
                    self.label_opcaity_dict[key]['change'] = self.global_value / 100
                self.pen_sub_adv_opacity_sub_specific_spin.setValue(self.global_value)
                self.pen_sub_adv_opacity_sub_specific_slider.setValue(self.global_value)

            elif mode == 2: #specific Default btn
                cur_idx = self.pen_sub_adv_opacity_sub_specific_combo.currentIndex()
                label_num = self.label_order_list[cur_idx]
                self.label_opcaity_dict[label_num]['change']  = self.global_value / 100
                self.pen_sub_adv_opacity_sub_specific_spin.setValue(self.global_value)
                self.pen_sub_adv_opacity_sub_specific_slider.setValue(self.global_value)
                tmp_dict = {}
                tmp_dict['mode'] = 'preview_specific'
                tmp_dict['label_list'] = label_num
                tmp_dict["value"] = self.global_value / 100
                self.parent.pen_opacity_to_display(tmp_dict)

            
            elif mode == 3: # specific apply
                value = self.pen_sub_adv_opacity_sub_specific_spin.value()
                cur_idx = self.pen_sub_adv_opacity_sub_specific_combo.currentIndex()
                label_num = self.label_order_list[cur_idx]
                self.label_opcaity_dict[label_num]['change'] = value / 100


            if mode not in [0,2]:
                tmp_change_key_list = []
                for key in self.label_obj_dict.keys():
                    if self.label_opcaity_dict[key]['change'] != self.label_opcaity_dict[key]['origin']:
                        self.label_opcaity_dict[key]['origin'] = self.label_opcaity_dict[key]['change']
                        self.label_obj_dict[key]['label_color_alpha'] = self.label_opcaity_dict[key]['change']
                        tmp_change_key_list.append(key)

                tmp_dict = {}
                tmp_dict['mode'] = 'opacity'
                tmp_dict['label_list'] = tmp_change_key_list
                self.parent.pen_opacity_to_display(tmp_dict)
            
            self.specific_sw = True


    def showEvent(self, e):
        """
            @description: 초기 UI 활성화때 발동되는 함수
            @author : MyoungHwan (2024.09.06)
            @history
                1. Modified by MyoungHwan (2024.09.10): Modify parent Ui close to hide
        """
        self.specific_sw = False
        self.global_sw = False
        
        self.global_value = 100
        self.pen_sub_adv_opacity_sub_global_spin.setValue(self.global_value)
        self.pen_sub_adv_opacity_sub_global_slider.setValue(self.global_value)
        self.pen_sub_adv_opacity_sub_specific_combo.clear()
        self.label_opcaity_dict = {}

        for key in self.label_obj_dict.keys():
            self.label_opcaity_dict[key] = {
                "origin" : self.label_obj_dict[key]['label_color_alpha'],
                "change" : self.label_obj_dict[key]['label_color_alpha'],
            }

        self.label_order_list = sorted(list(self.label_obj_dict.keys()))
        for label_num in self.label_order_list:
            self.pen_sub_adv_opacity_sub_specific_combo.addItem(f'{self.lang.get("labeling", "penSubOpacity", "penOpacityLabel")}: {str(label_num)}')
        self.pen_sub_adv_opacity_sub_specific_combo.setCurrentIndex(0)
        self.pen_sub_adv_opacity_sub_specific_spin.setValue(self.label_opcaity_dict[self.label_order_list[0]]['origin']*100)
        self.pen_sub_adv_opacity_sub_specific_slider.setValue(self.label_opcaity_dict[self.label_order_list[0]]['origin']*100)


        self.global_sw = True
        self.specific_sw = True
        """
            Description: Modify parent Ui close to hide
            Modified by MyoungHwan (2024.09.10)
        """
        # self.parent.hide()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)

    def closeEvent(self, e):
        """
            @description: UI 닫을때 발동되는 함수
            @author : MyoungHwan (2024.09.06)
            @history
                1. Modified by MyoungHwan (2024.09.10): Modify parent Ui close to hide
        """
        if self.isActiveWindow():
            tmp_dict = {}
            tmp_dict['mode'] = 'close'
            self.parent.pen_opacity_to_display(tmp_dict)
            self.parent.pen_obj_dict['pen_opacity']['opened'] = False
            self.parent.pen_obj_dict['pen_opacity']['obj'].toggle()
            self.parent.show()




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = pen_sub_adv_opacity_option_Form()
    sys.exit(app.exec_())
