from PyQt5 import QtCore, QtGui, QtWidgets


class label_sub_ess_option_Form(QtWidgets.QWidget):
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
        self.global_sw = True
        self.specific_sw = True
        self.global_value = 1

        self.label_center_dict = {}

    def init_ui(self, Form):
        Form.setObjectName("ESS_Setting_Form")
        Form.resize(318, 199)
        Form.setWindowTitle("ESS Setting")
        # Ensure the settings window always stays on top for improved accessibility and user convenience.
        Form.setWindowModality(QtCore.Qt.ApplicationModal)
        Form.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)
        
        self.label_sub_ess_main_vertical = QtWidgets.QVBoxLayout(Form)
        self.label_sub_ess_main_vertical.setObjectName("label_sub_ess_main_vertical")

        self.label_sub_ess_sub_global_groupbox = QtWidgets.QGroupBox()
        self.label_sub_ess_sub_global_groupbox.setObjectName("label_sub_ess_sub_global_groupbox")
        self.label_sub_ess_sub_global_groupbox.setTitle("Global Setting")

        self.label_sub_ess_sub_global_vertical = QtWidgets.QVBoxLayout()
        self.label_sub_ess_sub_global_vertical.setObjectName("label_sub_ess_sub_global_vertical")

        self.label_sub_ess_sub_global_horizon = QtWidgets.QHBoxLayout()
        self.label_sub_ess_sub_global_horizon.setObjectName("label_sub_ess_sub_global_horizon")        

        self.label_sub_ess_sub_global_label = QtWidgets.QLabel()
        self.label_sub_ess_sub_global_label.setObjectName("label_sub_ess_sub_global_label")
        self.label_sub_ess_sub_global_label.setText("Specific Sparse Spectrum")

        self.label_sub_ess_sub_global_null_label = QtWidgets.QLabel()
        self.label_sub_ess_sub_global_null_label.setObjectName("label_sub_ess_sub_global_null_label")
        self.label_sub_ess_sub_global_null_label.setText("")

        self.label_sub_ess_sub_global_spin = QtWidgets.QSpinBox()
        self.label_sub_ess_sub_global_spin.setObjectName("label_sub_ess_sub_global_spin")
        self.label_sub_ess_sub_global_spin.setRange(1,100)
        self.label_sub_ess_sub_global_spin.setValue(self.global_value)

        self.label_sub_ess_sub_global_apply_btn = QtWidgets.QPushButton()
        self.label_sub_ess_sub_global_apply_btn.setObjectName("label_sub_ess_sub_global_apply_btn")
        self.label_sub_ess_sub_global_apply_btn.setText("Apply")


        self.label_sub_ess_sub_specific_groupbox = QtWidgets.QGroupBox()
        self.label_sub_ess_sub_specific_groupbox.setObjectName("label_sub_ess_sub_specific_groupbox")
        self.label_sub_ess_sub_specific_groupbox.setTitle("Specific Setting")

        self.label_sub_ess_sub_specific_vertical = QtWidgets.QVBoxLayout()
        self.label_sub_ess_sub_specific_vertical.setObjectName("label_sub_ess_sub_specific_vertical")

        self.label_sub_ess_sub_specific_horizon = QtWidgets.QHBoxLayout()
        self.label_sub_ess_sub_specific_horizon.setObjectName("label_sub_ess_sub_specific_horizon")

        self.label_sub_ess_sub_specific_label = QtWidgets.QLabel()
        self.label_sub_ess_sub_specific_label.setObjectName("label_sub_ess_sub_specific_label")
        self.label_sub_ess_sub_specific_label.setText("Specific Sparse Spectrum")

        self.label_sub_ess_sub_specific_combo = QtWidgets.QComboBox()
        self.label_sub_ess_sub_specific_combo.setObjectName("label_sub_ess_sub_specific_combo")
        self.label_sub_ess_sub_specific_combo.addItem(f"Select Label")

        self.label_sub_ess_sub_specific_spin = QtWidgets.QSpinBox()
        self.label_sub_ess_sub_specific_spin.setObjectName("label_sub_ess_sub_specific_spin")
        self.label_sub_ess_sub_specific_spin.setRange(1,100)
        self.label_sub_ess_sub_specific_spin.setValue(self.global_value)

        self.label_sub_ess_sub_specific_apply_btn = QtWidgets.QPushButton()
        self.label_sub_ess_sub_specific_apply_btn.setObjectName("label_sub_ess_sub_specific_apply_btn")
        self.label_sub_ess_sub_specific_apply_btn.setText("Apply")

        self.label_sub_ess_sub_specific_horizon_2 = QtWidgets.QHBoxLayout()
        self.label_sub_ess_sub_specific_horizon_2.setObjectName("label_sub_ess_sub_specific_horizon_2")

        self.label_sub_ess_sub_specific_checkbox = QtWidgets.QCheckBox()
        self.label_sub_ess_sub_specific_checkbox.setText("Include Spectrum")
        self.label_sub_ess_sub_specific_checkbox.setIconSize(QtCore.QSize(16, 16))
        self.label_sub_ess_sub_specific_checkbox.setObjectName("label_sub_ess_sub_specific_checkbox")

        self.label_sub_ess_sub_setting_view_label = QtWidgets.QLabel()
        self.label_sub_ess_sub_setting_view_label.setObjectName("label_sub_ess_sub_setting_view_label")
        self.label_sub_ess_sub_setting_view_label.setText("")

        self.label_sub_ess_sub_btn_horizon = QtWidgets.QHBoxLayout()
        self.label_sub_ess_sub_btn_horizon.setObjectName("label_sub_ess_sub_btn_horizon")

        self.label_sub_ess_sub_default_btn = QtWidgets.QPushButton()
        self.label_sub_ess_sub_default_btn.setObjectName("label_sub_ess_sub_default_btn")
        self.label_sub_ess_sub_default_btn.setText("Default")

        self.label_sub_ess_sub_ok_btn = QtWidgets.QPushButton()
        self.label_sub_ess_sub_ok_btn.setObjectName("label_sub_ess_sub_ok_btn")
        self.label_sub_ess_sub_ok_btn.setText("Save && Exit")

    def setup_ui(self):

        self.label_sub_ess_sub_global_horizon.addWidget(self.label_sub_ess_sub_global_label)
        self.label_sub_ess_sub_global_horizon.addWidget(self.label_sub_ess_sub_global_spin)
        self.label_sub_ess_sub_global_horizon.addWidget(self.label_sub_ess_sub_global_apply_btn)
        self.label_sub_ess_sub_global_vertical.addLayout(self.label_sub_ess_sub_global_horizon)

        self.label_sub_ess_sub_specific_horizon.addWidget(self.label_sub_ess_sub_specific_combo)
        self.label_sub_ess_sub_specific_horizon.addWidget(self.label_sub_ess_sub_specific_checkbox)
        self.label_sub_ess_sub_specific_horizon_2.addWidget(self.label_sub_ess_sub_specific_label)
        self.label_sub_ess_sub_specific_horizon_2.addWidget(self.label_sub_ess_sub_specific_spin)
        self.label_sub_ess_sub_specific_horizon_2.addWidget(self.label_sub_ess_sub_specific_apply_btn)
        self.label_sub_ess_sub_specific_vertical.addLayout(self.label_sub_ess_sub_specific_horizon)
        self.label_sub_ess_sub_specific_vertical.addLayout(self.label_sub_ess_sub_specific_horizon_2)

        self.label_sub_ess_sub_global_groupbox.setLayout(self.label_sub_ess_sub_global_vertical)
        self.label_sub_ess_sub_specific_groupbox.setLayout(self.label_sub_ess_sub_specific_vertical)

        self.label_sub_ess_main_vertical.addWidget(self.label_sub_ess_sub_global_groupbox)
        self.label_sub_ess_main_vertical.addWidget(self.label_sub_ess_sub_specific_groupbox)

        self.label_sub_ess_sub_btn_horizon.addWidget(self.label_sub_ess_sub_default_btn)
        self.label_sub_ess_sub_btn_horizon.addWidget(self.label_sub_ess_sub_ok_btn)

        self.label_sub_ess_main_vertical.addLayout(self.label_sub_ess_sub_btn_horizon)

    def init_function(self):
        self.label_sub_ess_sub_global_spin.valueChanged.connect(lambda value=self.label_sub_ess_sub_global_spin : self.global_value_change(mode=0, value=value))
        self.label_sub_ess_sub_global_apply_btn.clicked.connect(lambda ch=self.label_sub_ess_sub_global_apply_btn : self.button_event(mode=0,ch=ch ))

        self.label_sub_ess_sub_specific_combo.currentIndexChanged.connect(lambda value=self.label_sub_ess_sub_specific_combo : self.specific_value_change(mode=0, value=value))
        self.label_sub_ess_sub_specific_apply_btn.clicked.connect(lambda ch=self.label_sub_ess_sub_specific_apply_btn : self.button_event(mode=1,ch=ch ))
        self.label_sub_ess_sub_specific_checkbox.clicked.connect(lambda ch=self.label_sub_ess_sub_specific_checkbox : self.button_event(mode=4,ch=ch ))

        self.label_sub_ess_sub_default_btn.clicked.connect(lambda ch=self.label_sub_ess_sub_default_btn : self.button_event(mode=2,ch=ch ))
        self.label_sub_ess_sub_ok_btn.clicked.connect(lambda ch=self.label_sub_ess_sub_ok_btn : self.button_event(mode=3, ch=ch))

    def global_value_change(self, mode, value):
        if mode == 0:
            pass

    def specific_value_change(self, mode, value):
        if self.specific_sw:
            if mode == 0: # combo
                self.specific_sw = False
                label_num = self.label_order_list[value]
                center_num = self.label_center_dict[label_num]['change']
                include_spectrum = self.label_obj_dict[label_num]['include_spectrum']
                self.label_sub_ess_sub_specific_spin.setValue(center_num)
                if include_spectrum:
                    self.label_sub_ess_sub_specific_checkbox.setChecked(True)
                else:
                    self.label_sub_ess_sub_specific_checkbox.setChecked(False)
                self.specific_sw = True
            elif mode == 1:
                pass

    def button_event(self, mode, ch):
        if self.specific_sw:
            if mode == 0: # global apply
                self.global_value = self.label_sub_ess_sub_global_spin.value()
                for key in self.label_obj_dict.keys():
                    self.label_center_dict[key]['change'] = self.global_value

                cur_idx = self.label_sub_ess_sub_specific_combo.currentIndex()
                label_num = self.label_order_list[cur_idx]
                center_num = self.label_center_dict[label_num]['change']
                self.label_sub_ess_sub_specific_spin.setValue(center_num)

            elif mode == 1: # specific apply
                value = self.label_sub_ess_sub_specific_spin.value()
                cur_idx = self.label_sub_ess_sub_specific_combo.currentIndex()
                label_num = self.label_order_list[cur_idx]
                self.label_center_dict[label_num]['change'] = value

                self.label_obj_dict[label_num]['include_spectrum'] = int(self.label_sub_ess_sub_specific_checkbox.isChecked())

            elif mode == 2: #Default btn
                for key in self.label_obj_dict.keys():
                    self.label_center_dict[key]['change']  = self.label_obj_dict[key]['center_num_origin']
                    self.label_obj_dict[key]['include_spectrum'] = 0

                cur_idx = self.label_sub_ess_sub_specific_combo.currentIndex()
                label_num = self.label_order_list[cur_idx]
                center_num = self.label_center_dict[label_num]['change']
                self.label_sub_ess_sub_specific_spin.setValue(center_num)
                self.label_sub_ess_sub_specific_checkbox.setChecked(False)

            elif mode == 3: #SAVE btn
                for key in self.label_obj_dict.keys():
                    self.label_obj_dict[key]['center_num'] = self.label_center_dict[key]['change']
                self.close()


    def showEvent(self, e):
        self.specific_sw = False
        self.global_sw = False
        
        self.label_sub_ess_sub_global_spin.setValue(self.global_value)
        self.label_sub_ess_sub_specific_combo.clear()
        self.label_center_dict = {}

        for key in self.label_obj_dict.keys():
            self.label_center_dict[key] = {
                "origin" : self.label_obj_dict[key]['center_num'],
                "change" : self.label_obj_dict[key]['center_num'],
            }

        self.label_order_list = sorted(list(self.label_obj_dict.keys()))
        for label_num in self.label_order_list:
            self.label_sub_ess_sub_specific_combo.addItem(f"Label: {str(label_num)}")
        self.label_sub_ess_sub_specific_combo.setCurrentIndex(0)
        label_number = self.label_order_list[0]
        self.label_sub_ess_sub_specific_spin.setValue(self.label_obj_dict[label_number]['center_num'])    
        include_spectrum = self.label_obj_dict[label_number]['include_spectrum']
        if include_spectrum:
            self.label_sub_ess_sub_specific_checkbox.setChecked(True)
        else:
            self.label_sub_ess_sub_specific_checkbox.setChecked(False)

        self.global_sw = True
        self.specific_sw = True

    def closeEvent(self, e):
        self.parent.label_sub_anly_ess_option_btn.setEnabled(True)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = label_sub_ess_option_Form()
    sys.exit(app.exec_())
