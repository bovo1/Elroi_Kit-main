"""
    ELROILAB Kit
 
    Copyright 2024. Elroilab All rights reserved.
"""

import os
import json
import torch
import numpy as np

from copy import deepcopy
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFileDialog
from qtwidgets import AnimatedToggle

# model_type: (Model 1 -> PLSDA), (Model 2 -> DDCNN), (Model 3 -> SSGCA), (Model 4 -> DSAD), (Model 5 -> PA2E)
from training.module.hyperparameters import DA, DN, PD, PE, SC
from utils.shared import temp_path, config_path
from training.stylesheet.stylesheet_hyperparameter_main import stylesheet

"""
description: hyperparameter UI Widget
author : HyeokYoon
modified by HyeokYoon (20240219)

recently works
- removed verbose option and related parameters
"""
class Hyperparameter_Form(QtWidgets.QWidget):
    def __init__(self, Sync, lang) -> None:
        super().__init__()
        self.lang = lang
        self.init(Sync=Sync)
        self.init_ui(self)
        self.setup_ui()
        self.init_hyperparameter_layout() # hyperparameter settings groupbox

        # init cuda status
        self.init_cuda_status(Sync=Sync)
        self.init_function(Sync=Sync)
        self.change_path_status(self.current_model_type)
        self.change_load_ref_status(self.current_model_type)

    def init(self, Sync=None):
        # path
        self.default_save_path = temp_path # root path for saving
        if not os.path.exists(self.default_save_path):
            os.mkdir(self.default_save_path)
        
        # cuda available
        self.cuda_is_available = torch.cuda.is_available()

        # settings
        # Set DA as the default model
        self.hyperparameter_shared_dict = {
            "current_model_type": "DA",
            "show_video": False,
            "modelDescription": "",
            "PD": {
                "model_name": "PLSDA",
                "model_index": 0, # for combobox
                "params_dict": PD.hyperparameter_dict,
                "cuda_supported": True,
                "use_cuda": True,
                "cuda_device": 0,
                "save_path": self.default_save_path,
                "load_path": "",
                "load_type": ["el (*.el)"],
                "load_ref_path": "",
                "use_load_ref": False
            },
            "DN": {
                "model_name": "DDCNN",
                "model_index": 1, # for combobox
                "params_dict": DN.hyperparameter_dict,
                "cuda_supported": True,
                "use_cuda": True,
                "cuda_device": 0,
                "save_path": self.default_save_path,
                "load_path": "",
                "load_type": ["el (*.el)"],
                "load_ref_path": "",
                "use_load_ref": False
            },
            "SC": {
                "model_name": "SSGCA",
                "model_index": 2, # for combobox
                "params_dict": SC.hyperparameter_dict,
                "cuda_supported": True,
                "use_cuda": True,
                "cuda_device": 0,
                "save_path": self.default_save_path,
                "load_path": "",
                "load_type": ["el (*.el)"],
                "load_ref_path": "",
                "use_load_ref": False
            },
            "DA": {
                "model_name": "DSAD",
                "model_index": 3, # for combobox
                "params_dict": DA.hyperparameter_dict,
                "cuda_supported": True,
                "use_cuda": True,
                "cuda_device": 0,
                "save_path": self.default_save_path,
                "load_path": "",
                "load_type": ["el (*.el)"],
                "load_ref_path": "",
                "use_load_ref": False
            },
            "PE": {
                "model_name": "PA2Ev2",
                "model_index": 4, # for combobox
                "params_dict": PE.hyperparameter_dict,
                "cuda_supported": True,
                "use_cuda": True,
                "cuda_device": 0,
                "save_path": self.default_save_path,
                "load_path": "",
                "load_type": ["el (*.el)"],
                "load_ref_path": "",
                "use_load_ref": False
            }
        }

        self.hyperparameter_default = deepcopy(self.hyperparameter_shared_dict)

        # Sync
        Sync.hyperparameter_shared_dict = self.hyperparameter_shared_dict
        Sync.hyperparameter_signal.connect(self.hyperparameter_signal_receiver)
        self.metadata_shared_dict = Sync.metadata_shared_dict
        self.config = Sync.config
        self.init_config()

        self.current_model_type = self.hyperparameter_shared_dict["current_model_type"]

    def init_hyperparameter_layout(self):
        self.add_hyperparameter_layout(self.current_model_type)

    def init_ui(self, Form):
        Form.setObjectName("Hyperparameter_Form")
        Form.setWindowTitle("Hyperparameter_Form")
        Form.setStyleSheet(stylesheet)
        self.FormLayout = QtWidgets.QVBoxLayout(Form)
        self.FormLayout.setObjectName("FormLayout")
        
        # =============== Icon Area ===============
        self.icon_save_load = QIcon()
        self.icon_save_load.addPixmap(QPixmap("ico/training/folder/folder_save_load.png"), QIcon.Normal, QIcon.Off)

        # =============== Common Settings Form Area ===============
        self.MainSettingsGroupBox = QtWidgets.QVBoxLayout()
        self.MainSettingsGroupBox.setObjectName("MainSettingsGroupBox")

        self.CommonSettingsGroupBox = QtWidgets.QGroupBox(Form)
        self.CommonSettingsGroupBox.setObjectName("CommonSettingsGroupBox")

        self.GlobalButtonContainer = QtWidgets.QWidget()
        self.GlobalButtonContainer.setObjectName("GlobalButtonContainer")

        self.GlobalButtonContainerLayout = QtWidgets.QHBoxLayout(self.GlobalButtonContainer)
        self.GlobalButtonContainerLayout.setObjectName("GlobalButtonContainerLayout")

        self.ParameterResetPushButton = QtWidgets.QPushButton(self.CommonSettingsGroupBox)
        self.ParameterResetPushButton.setObjectName("ParameterResetPushButton")

        self.ParameterLoadPushButton = QtWidgets.QPushButton(self.CommonSettingsGroupBox)
        self.ParameterLoadPushButton.setObjectName("ParameterLoadPushButton")

        self.CommonSettingsGroupBoxLayout = QtWidgets.QHBoxLayout(self.CommonSettingsGroupBox)
        self.CommonSettingsGroupBoxLayout.setObjectName("CommonSettingsGroupBoxLayout")

        self.CommonSettingsLeftMainWidget = QtWidgets.QWidget(self.CommonSettingsGroupBox)
        self.CommonSettingsLeftMainWidget.setObjectName("CommonSettingsLeftMainWidget")

        self.CommonSettingsLeftMainWidgetLayout = QtWidgets.QVBoxLayout(self.CommonSettingsLeftMainWidget)
        self.CommonSettingsLeftMainWidgetLayout.setObjectName("CommonSettingsLeftMainWidgetLayout")

        self.CommonSettingsModelWidget = QtWidgets.QWidget(self.CommonSettingsLeftMainWidget)
        self.CommonSettingsModelWidget.setObjectName("CommonSettingsModelWidget")

        self.CommonSettingsModelWidgetLayout = QtWidgets.QHBoxLayout(self.CommonSettingsModelWidget)
        self.CommonSettingsModelWidgetLayout.setObjectName("CommonSettingsModelWidgetLayout")

        self.CommonSettingsModelLabel = QtWidgets.QLabel(self.CommonSettingsModelWidget)
        self.CommonSettingsModelLabel.setObjectName("CommonSettingsModelLabel")

        self.CommonSettingsModelComboBox = QtWidgets.QComboBox(self.CommonSettingsModelWidget)
        self.CommonSettingsModelComboBox.setObjectName("CommonSettingsModelComboBox")

        self.CommonSettingsSavePathWidget = QtWidgets.QWidget(self.CommonSettingsLeftMainWidget)
        self.CommonSettingsSavePathWidget.setObjectName("CommonSettingsSavePathWidget")

        self.CommonSettingsSavePathWidgetLayout = QtWidgets.QHBoxLayout(self.CommonSettingsSavePathWidget)
        self.CommonSettingsSavePathWidgetLayout.setObjectName("CommonSettingsSavePathWidgetLayout")

        self.CommonSettingsSavePathLabel = QtWidgets.QLabel(self.CommonSettingsSavePathWidget)
        self.CommonSettingsSavePathLabel.setObjectName("CommonSettingsSavePathLabel")

        self.CommonSettingsSavePathLineEdit = QtWidgets.QLineEdit(self.CommonSettingsSavePathWidget)
        self.CommonSettingsSavePathLineEdit.setObjectName("CommonSettingsSavePathLineEdit")

        self.CommonSettingsSavePathPushButton = QtWidgets.QPushButton(self.CommonSettingsSavePathWidget)
        self.CommonSettingsSavePathPushButton.setObjectName("CommonSettingsSavePathPushButton")

        self.CommonSettingsLoadPathWidget = QtWidgets.QWidget(self.CommonSettingsLeftMainWidget)
        self.CommonSettingsLoadPathWidget.setObjectName("CommonSettingsLoadPathWidget")

        self.CommonSettingsLoadPathWidgetLayout = QtWidgets.QHBoxLayout(self.CommonSettingsLoadPathWidget)
        self.CommonSettingsLoadPathWidgetLayout.setObjectName("CommonSettingsLoadPathWidgetLayout")

        self.CommonSettingsLoadPathLabel = QtWidgets.QLabel(self.CommonSettingsLoadPathWidget)
        self.CommonSettingsLoadPathLabel.setObjectName("CommonSettingsLoadPathLabel")

        self.CommonSettingsLoadPathLineEdit = QtWidgets.QLineEdit(self.CommonSettingsLoadPathWidget)
        self.CommonSettingsLoadPathLineEdit.setObjectName("CommonSettingsLoadPathLineEdit")

        self.CommonSettingsLoadPathPushButton = QtWidgets.QPushButton(self.CommonSettingsLoadPathWidget)
        self.CommonSettingsLoadPathPushButton.setObjectName("CommonSettingsLoadPathPushButton")

        self.CommonSettingsLoadRefPathWidget = QtWidgets.QWidget(self.CommonSettingsLeftMainWidget)
        self.CommonSettingsLoadRefPathWidget.setObjectName("CommonSettingsLoadRefPathWidget")

        self.CommonSettingsLoadRefPathWidgetLayout = QtWidgets.QHBoxLayout(self.CommonSettingsLoadRefPathWidget)
        self.CommonSettingsLoadRefPathWidgetLayout.setObjectName("CommonSettingsLoadRefPathWidgetLayout")

        self.CommonSettingsLoadRefPathLabel = QtWidgets.QLabel(self.CommonSettingsLoadRefPathWidget)
        self.CommonSettingsLoadRefPathLabel.setObjectName("CommonSettingsLoadRefPathLabel")

        self.CommonSettingsLoadRefPathLineEdit = QtWidgets.QLineEdit(self.CommonSettingsLoadRefPathWidget)
        self.CommonSettingsLoadRefPathLineEdit.setObjectName("CommonSettingsLoadRefPathLineEdit")

        self.CommonSettingsLoadRefPathPushButton = QtWidgets.QPushButton(self.CommonSettingsLoadRefPathWidget)
        self.CommonSettingsLoadRefPathPushButton.setObjectName("CommonSettingsLoadRefPathPushButton")

        self.CommonSettingsLoadRefPathToggle = AnimatedToggle(
            pulse_checked_color="transparent",
            pulse_unchecked_color="transparent"
        )
        self.CommonSettingsLoadRefPathToggle.setObjectName("CommonSettingsLoadRefPathToggle")

        # for model description
        self.CommonSettingsModelDescriptionWidget = QtWidgets.QWidget(self.CommonSettingsLeftMainWidget)
        self.CommonSettingsModelDescriptionWidget.setObjectName("CommonSettingsModelDescriptionWidget")

        self.CommonSettingsModelDescriptionWidgetLayout = QtWidgets.QHBoxLayout(self.CommonSettingsModelDescriptionWidget)
        self.CommonSettingsModelDescriptionWidgetLayout.setObjectName("CommonSettingsModelDescriptionWidgetLayout")

        self.CommonSettingsModelDescriptionLabel = QtWidgets.QLabel(self.CommonSettingsModelDescriptionWidget)
        self.CommonSettingsModelDescriptionLabel.setObjectName("CommonSettingsModelDescriptionLabel")

        self.CommonSettingsModelDescriptionLineEdit = QtWidgets.QLineEdit(self.CommonSettingsModelDescriptionWidget)
        self.CommonSettingsModelDescriptionLineEdit.setObjectName("CommonSettingsModelDescriptionLineEdit")

        self.vline = QtWidgets.QFrame(self.CommonSettingsGroupBox)
        self.vline.setObjectName("vline")

        self.CommonSettingsRightMainWidget = QtWidgets.QWidget(self.CommonSettingsGroupBox)
        self.CommonSettingsRightMainWidget.setObjectName("CommonSettingsRightMainWidget")

        self.CommonSettingsRightMainLayout = QtWidgets.QVBoxLayout(self.CommonSettingsRightMainWidget)
        self.CommonSettingsRightMainLayout.setObjectName("CommonSettingsRightMainLayout")

        self.CommonSettingsGPUUseWidget = QtWidgets.QWidget(self.CommonSettingsRightMainWidget)
        self.CommonSettingsGPUUseWidget.setObjectName("CommonSettingsGPUUseWidget")

        self.CommonSettingsGPUUseWidgetLayout = QtWidgets.QHBoxLayout(self.CommonSettingsGPUUseWidget)
        self.CommonSettingsGPUUseWidgetLayout.setObjectName("CommonSettingsGPUUseWidgetLayout")

        self.CommonSettingsGPUUseLabel = QtWidgets.QLabel(self.CommonSettingsGPUUseWidget)
        self.CommonSettingsGPUUseLabel.setObjectName("CommonSettingsGPUUseLabel")

        self.CommonSettingsGPUToggle = AnimatedToggle(
            pulse_checked_color="transparent",
            pulse_unchecked_color="transparent"
        )
        self.CommonSettingsGPUToggle.setObjectName("CommonSettingsGPUToggle")

        self.CommonSettingsGPUDeviceWidget = QtWidgets.QWidget(self.CommonSettingsRightMainWidget)
        self.CommonSettingsGPUDeviceWidget.setObjectName("CommonSettingsGPUDeviceWidget")
        
        self.CommonSettingsGPUDeviceWidgetLayout = QtWidgets.QHBoxLayout(self.CommonSettingsGPUDeviceWidget)
        self.CommonSettingsGPUDeviceWidgetLayout.setObjectName("CommonSettingsGPUDeviceWidgetLayout")

        self.CommonSettingsGPUDeviceLabel = QtWidgets.QLabel(self.CommonSettingsGPUDeviceWidget)
        self.CommonSettingsGPUDeviceLabel.setObjectName("CommonSettingsGPUDeviceLabel")

        self.CommonSettingsGPUDeviceComboBox = QtWidgets.QComboBox(self.CommonSettingsGPUDeviceWidget)
        self.CommonSettingsGPUDeviceComboBox.setObjectName("CommonSettingsGPUDeviceComboBox")
        
        self.hline = QtWidgets.QFrame(self.CommonSettingsRightMainWidget)
        self.hline.setObjectName("hline")

        self.CommonSettingsVideoWidget = QtWidgets.QWidget(self.CommonSettingsRightMainWidget)
        self.CommonSettingsVideoWidget.setObjectName("CommonSettingsVideoWidget")
        self.CommonSettingsVideoWidget.hide()
        
        self.CommonSettingsVideoWidgetLayout = QtWidgets.QHBoxLayout(self.CommonSettingsVideoWidget)
        self.CommonSettingsVideoWidgetLayout.setObjectName("CommonSettingsVideoWidgetLayout")

        self.CommonSettingsVideoLabel = QtWidgets.QLabel(self.CommonSettingsVideoWidget)
        self.CommonSettingsVideoLabel.setObjectName("CommonSettingsVideoLabel")

        self.CommonSettingsVideoToggle = AnimatedToggle(
            pulse_checked_color="transparent",
            pulse_unchecked_color="transparent"
        )
        self.CommonSettingsVideoToggle.setObjectName("CommonSettingsVideoToggle")

        # =============== Hyperparameter Settings Form Area ===============
        self.ParameterSettingsGroupBox = QtWidgets.QGroupBox(Form)
        self.ParameterSettingsGroupBox.setObjectName("ParameterSettingsGroupBox")

        self.ParameterSettingsGroupBoxLayout = QtWidgets.QVBoxLayout(self.ParameterSettingsGroupBox)
        self.ParameterSettingsGroupBoxLayout.setObjectName("ParameterSettingsGroupBoxLayout")

        self.ParameterSettingsScrollArea = QtWidgets.QScrollArea(self.ParameterSettingsGroupBox)
        self.ParameterSettingsScrollArea.setObjectName("ParameterSettingsScrollArea")

        self.ParameterSettingsMainWidget = QtWidgets.QWidget(self.ParameterSettingsScrollArea)
        self.ParameterSettingsMainWidget.setObjectName("ParameterSettingsMainWidget")
        
        self.ParameterSettingsMainWidgetLayout = QtWidgets.QVBoxLayout(self.ParameterSettingsMainWidget)
        self.ParameterSettingsMainWidgetLayout.setObjectName("ParameterSettingsMainWidgetLayout")

        self.ParameterSettingsSubWidget = QtWidgets.QWidget(self.ParameterSettingsMainWidget)
        self.ParameterSettingsSubWidget.setObjectName("ParameterSettingsSubWidget")

        self.ParameterSettingsSubWidgetLayout = QtWidgets.QVBoxLayout(self.ParameterSettingsSubWidget)
        self.ParameterSettingsSubWidgetLayout.setObjectName("ParameterSettingsSubWidgetLayout")

        QtCore.QMetaObject.connectSlotsByName(Form)

    def setup_ui(self):
        # =============== Common Settings Form Area ===============
        self.CommonSettingsLoadRefPathToggle.setChecked(self.hyperparameter_shared_dict[self.current_model_type]["use_load_ref"])

        # =============== Default Settings ===============
        self.CommonSettingsGPUUseWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.CommonSettingsGPUDeviceWidgetLayout.setContentsMargins(0, 10, 0, 10)
        self.CommonSettingsVideoWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.CommonSettingsModelLabel.setFixedWidth(130)
        self.CommonSettingsSavePathLabel.setFixedWidth(130)
        self.CommonSettingsLoadPathLabel.setFixedWidth(130)
        self.CommonSettingsLoadRefPathLabel.setFixedWidth(130)
        self.CommonSettingsModelDescriptionLabel.setFixedWidth(130)
        self.CommonSettingsGPUUseLabel.setFixedWidth(100)
        self.CommonSettingsGPUDeviceLabel.setFixedWidth(100)
        self.CommonSettingsVideoLabel.setFixedWidth(100)

        self.CommonSettingsGPUDeviceComboBox.setFixedWidth(300)

        # model list
        model_list = []; list_counter = 0
        for key in self.hyperparameter_shared_dict.keys():
            if type(self.hyperparameter_shared_dict[key]) == dict:
                list_counter += 1
                model_list.append(f"{list_counter}: {key}")

        self.CommonSettingsModelComboBox.addItems(model_list)
        self.CommonSettingsModelComboBox.setCurrentIndex(self.hyperparameter_shared_dict[self.current_model_type]["model_index"])

        self.CommonSettingsSavePathPushButton.setFixedWidth(25)
        self.CommonSettingsSavePathPushButton.setIcon(self.icon_save_load)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsSavePathPushButton", self.CommonSettingsSavePathPushButton)

        self.CommonSettingsLoadPathPushButton.setFixedWidth(25)
        self.CommonSettingsLoadPathPushButton.setIcon(self.icon_save_load)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsLoadPathPushButton", self.CommonSettingsLoadPathPushButton)

        self.CommonSettingsLoadRefPathPushButton.setFixedWidth(25)
        self.CommonSettingsLoadRefPathPushButton.setIcon(self.icon_save_load)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsLoadRefPathPushButton", self.CommonSettingsLoadRefPathPushButton)

        self.CommonSettingsSavePathLineEdit.setReadOnly(True)
        self.CommonSettingsSavePathLineEdit.setText(self.default_save_path)
        self.CommonSettingsSavePathLineEdit.setToolTip(self.default_save_path)

        self.CommonSettingsLoadPathLineEdit.setReadOnly(True)
        self.CommonSettingsLoadRefPathLineEdit.setReadOnly(True)

        self.vline.setFrameShape(QtWidgets.QFrame.VLine)
        self.vline.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.CommonSettingsGroupBox.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)

        # =============== Add Widgets or Layout ===============
        self.CommonSettingsGroupBoxLayout.setStretch(0, 1)
        self.CommonSettingsGroupBoxLayout.addWidget(self.CommonSettingsLeftMainWidget)
        self.CommonSettingsGroupBoxLayout.addWidget(self.vline)
        self.CommonSettingsGroupBoxLayout.addWidget(self.CommonSettingsRightMainWidget, 0, QtCore.Qt.AlignTop)

        # Left Area
        self.CommonSettingsModelWidgetLayout.addWidget(self.CommonSettingsModelLabel)
        self.CommonSettingsModelWidgetLayout.addWidget(self.CommonSettingsModelComboBox)

        self.CommonSettingsSavePathWidgetLayout.addWidget(self.CommonSettingsSavePathLabel)
        self.CommonSettingsSavePathWidgetLayout.addWidget(self.CommonSettingsSavePathLineEdit)
        self.CommonSettingsSavePathWidgetLayout.addWidget(self.CommonSettingsSavePathPushButton)

        self.CommonSettingsLoadPathWidgetLayout.addWidget(self.CommonSettingsLoadPathLabel)
        self.CommonSettingsLoadPathWidgetLayout.addWidget(self.CommonSettingsLoadPathLineEdit)
        self.CommonSettingsLoadPathWidgetLayout.addWidget(self.CommonSettingsLoadPathPushButton)

        self.CommonSettingsLoadRefPathWidgetLayout.addWidget(self.CommonSettingsLoadRefPathLabel)
        self.CommonSettingsLoadRefPathWidgetLayout.addWidget(self.CommonSettingsLoadRefPathLineEdit)
        self.CommonSettingsLoadRefPathWidgetLayout.addWidget(self.CommonSettingsLoadRefPathPushButton)
        self.CommonSettingsLoadRefPathWidgetLayout.addWidget(self.CommonSettingsLoadRefPathToggle)

        self.CommonSettingsModelDescriptionWidgetLayout.addWidget(self.CommonSettingsModelDescriptionLabel)
        self.CommonSettingsModelDescriptionWidgetLayout.addWidget(self.CommonSettingsModelDescriptionLineEdit)

        self.CommonSettingsLeftMainWidgetLayout.addWidget(self.CommonSettingsModelWidget, 0, QtCore.Qt.AlignLeft)
        self.CommonSettingsLeftMainWidgetLayout.addWidget(self.CommonSettingsSavePathWidget)
        self.CommonSettingsLeftMainWidgetLayout.addWidget(self.CommonSettingsLoadPathWidget)
        self.CommonSettingsLeftMainWidgetLayout.addWidget(self.CommonSettingsLoadRefPathWidget)
        self.CommonSettingsLeftMainWidgetLayout.addWidget(self.CommonSettingsModelDescriptionWidget)
        
        # Right Area
        self.CommonSettingsGPUUseWidgetLayout.addWidget(self.CommonSettingsGPUUseLabel)
        self.CommonSettingsGPUUseWidgetLayout.addWidget(self.CommonSettingsGPUToggle)

        self.CommonSettingsGPUDeviceWidgetLayout.addWidget(self.CommonSettingsGPUDeviceLabel)
        self.CommonSettingsGPUDeviceWidgetLayout.addWidget(self.CommonSettingsGPUDeviceComboBox)

        self.CommonSettingsVideoWidgetLayout.addWidget(self.CommonSettingsVideoLabel)
        self.CommonSettingsVideoWidgetLayout.addWidget(self.CommonSettingsVideoToggle)
        self.CommonSettingsVideoToggle.setChecked(self.hyperparameter_shared_dict["show_video"])

        self.hline.setFrameShape(QtWidgets.QFrame.HLine)
        self.hline.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.CommonSettingsRightMainLayout.addWidget(self.CommonSettingsGPUUseWidget, 0, QtCore.Qt.AlignLeft)
        self.CommonSettingsRightMainLayout.addWidget(self.CommonSettingsGPUDeviceWidget, 0, QtCore.Qt.AlignLeft)
        self.CommonSettingsRightMainLayout.addWidget(self.hline)
        self.CommonSettingsRightMainLayout.addWidget(self.CommonSettingsVideoWidget, 0, QtCore.Qt.AlignLeft)

        self.GlobalButtonContainerLayout.addWidget(self.ParameterLoadPushButton)
        self.GlobalButtonContainerLayout.addWidget(self.ParameterResetPushButton)
        self.GlobalButtonContainerLayout.setContentsMargins(0, 0, 0, 0)

        self.MainSettingsGroupBox.addWidget(self.GlobalButtonContainer, 0, QtCore.Qt.AlignRight)
        self.MainSettingsGroupBox.addWidget(self.CommonSettingsGroupBox)

        self.FormLayout.addLayout(self.MainSettingsGroupBox)

        # =============== Hyperparameter Settings Form Area ===============

        # =============== Default Settings ===============
        self.ParameterSettingsScrollArea.setWidgetResizable(True)

        # =============== Add Widgets or Layout ===============
        self.ParameterSettingsScrollArea.setWidget(self.ParameterSettingsMainWidget)
        self.ParameterSettingsGroupBoxLayout.addWidget(self.ParameterSettingsScrollArea)
        self.ParameterSettingsMainWidgetLayout.addWidget(self.ParameterSettingsSubWidget)
        
        self.FormLayout.addWidget(self.ParameterSettingsGroupBox)

        self.lang.set("training", "hyperparameter_main", "CommonSettingsGroupBox", self.CommonSettingsGroupBox)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsModelLabel", self.CommonSettingsModelLabel)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsSavePathLabel", self.CommonSettingsSavePathLabel)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsLoadPathLabel", self.CommonSettingsLoadPathLabel)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsLoadRefPathLabel", self.CommonSettingsLoadRefPathLabel)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsModelDescriptionLabel", self.CommonSettingsModelDescriptionLabel)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsGPUUseLabel", self.CommonSettingsGPUUseLabel)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsGPUDeviceLabel", self.CommonSettingsGPUDeviceLabel)
        self.lang.set("training", "hyperparameter_main", "CommonSettingsVideoLabel", self.CommonSettingsVideoLabel)
        self.lang.set("training", "hyperparameter_main", "ParameterSettingsGroupBox", self.ParameterSettingsGroupBox)
        self.lang.set("training", "hyperparameter_main", "ParameterResetPushButton", self.ParameterResetPushButton)
        self.lang.set("training", "hyperparameter_main", "ParameterLoadPushButton", self.ParameterLoadPushButton)

    def init_function(self, Sync=None):
        # Common Settings Event
        self.CommonSettingsModelComboBox.currentIndexChanged.connect(lambda: self.change_hyperparameter_layout(self.CommonSettingsModelComboBox.currentText().split(": ")[-1]))
        self.CommonSettingsSavePathPushButton.clicked.connect(lambda: self.add_path_status(self.CommonSettingsModelComboBox.currentText().split(": ")[-1], "save"))
        self.CommonSettingsLoadPathPushButton.clicked.connect(lambda: self.add_path_status(self.CommonSettingsModelComboBox.currentText().split(": ")[-1], "load"))
        self.CommonSettingsLoadRefPathPushButton.clicked.connect(lambda: self.add_path_status(self.CommonSettingsModelComboBox.currentText().split(": ")[-1], "load_ref"))
        self.CommonSettingsLoadRefPathToggle.clicked.connect(lambda: self.update_load_ref_status(self.CommonSettingsModelComboBox.currentText().split(": ")[-1], self.CommonSettingsLoadRefPathToggle.isChecked()))
        self.CommonSettingsGPUToggle.clicked.connect(lambda: self.update_cuda_status(self.CommonSettingsModelComboBox.currentText().split(": ")[-1], self.CommonSettingsGPUToggle.isChecked(), self.CommonSettingsGPUDeviceComboBox.currentIndex()))
        self.CommonSettingsGPUDeviceComboBox.currentIndexChanged.connect(lambda: self.update_cuda_status(self.CommonSettingsModelComboBox.currentText().split(": ")[-1], self.CommonSettingsGPUToggle.isChecked(), self.CommonSettingsGPUDeviceComboBox.currentIndex()))
        self.CommonSettingsVideoToggle.clicked.connect(lambda: self.update_show_video(self.CommonSettingsVideoToggle.isChecked()))
        self.CommonSettingsModelDescriptionLineEdit.textChanged.connect(lambda: self.update_model_description(self.CommonSettingsModelDescriptionLineEdit.text(), Sync=Sync))
        self.ParameterResetPushButton.clicked.connect(lambda: self.reset_hyperparameter())
        self.ParameterLoadPushButton.clicked.connect(lambda: self.load_config(True))
    
    def init_cuda_status(self, Sync=None):
        self.available_cuda_list = self.get_device_list()
        self.CommonSettingsGPUDeviceComboBox.addItems(self.available_cuda_list)
        self.change_cuda_status(self.current_model_type)
        self.hyperparameter_shared_dict["deviceName"] = self.CommonSettingsGPUDeviceComboBox.currentText()
        Sync.hyperparameter_shared_dict = self.hyperparameter_shared_dict

    def get_device_list(self):
        if self.cuda_is_available:
            gpu_list = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
        else:
            gpu_list = ["CUDA is Not Available"]
        return gpu_list

    def get_sub_layout(self, model_type:str):
        sub_layout = QtWidgets.QVBoxLayout()

        # get group dictionary
        hyperparameter_group_dict = self.hyperparameter_shared_dict[model_type]["params_dict"]
        hyperparameter_group_key_list = hyperparameter_group_dict.keys()
        
        # loop for groupbox
        for hyperparameter_group_key in hyperparameter_group_key_list:
            # get parameter dictionary
            hyperparameter_parameter_dict = hyperparameter_group_dict[hyperparameter_group_key]

            # get sub groupbox
            sub_groupbox = QtWidgets.QGroupBox(title=self.lang.get("training", "hyperparameter_main", self.hyperparameter_shared_dict[model_type]["params_dict"][hyperparameter_group_key]["name"]))
            sub_groupbox.setObjectName(hyperparameter_group_key)
            self.lang.set("training", "hyperparameter_main", self.hyperparameter_shared_dict[model_type]["params_dict"][hyperparameter_group_key]["name"], sub_groupbox)
            sub_groupbox_layout = QtWidgets.QVBoxLayout(sub_groupbox)

            # loop for sub widgets
            for hyperparameter_sub_group_key in hyperparameter_parameter_dict.keys():
                hyperparameter_parameter_component = hyperparameter_parameter_dict[hyperparameter_sub_group_key]
                # ignore this line when ui is not dict type or invisible
                if type(hyperparameter_parameter_component) != dict or not hyperparameter_parameter_component["visible"]:
                    continue

                # get sub widget and layout
                # These widgets are component of groupbox and follow bellow roles
                # ui position -> | label[1] | input widget[2] | description[3] |
                sub_widget = QtWidgets.QWidget()
                sub_widget.setObjectName(hyperparameter_sub_group_key)
                sub_widget_layout = QtWidgets.QHBoxLayout(sub_widget)
                sub_widget_layout.setContentsMargins(0, 5, 0, 5)

                if hyperparameter_parameter_component["type"] == bool:
                    sub_widget_layout.setContentsMargins(0, 0, 0, 0) # toggle has too large margin

                # ========================= label [1] =========================
                sub_label = QtWidgets.QLabel(text=hyperparameter_parameter_component["name"])
                sub_widget_layout.addWidget(sub_label)

                # ========================= input widget [2] =========================
                sub_input_widget = self.get_sub_input_widget(hyperparameter_group_key, hyperparameter_sub_group_key, hyperparameter_parameter_component)
                sub_widget_layout.addWidget(sub_input_widget)

                # ========================= description [3] =========================
                description = QtWidgets.QLabel(text=self.lang.get("training", "hyperparameter_description", hyperparameter_sub_group_key))
                self.lang.set("training", "hyperparameter_description", hyperparameter_sub_group_key, description)
                description.setContentsMargins(15, 0, 0, 0)
                sub_widget_layout.addWidget(description)

                if hyperparameter_parameter_component["type"] == bool:
                    sub_input_widget.setFixedWidth(100)
                    sub_label.setFixedWidth(330)
                else:
                    sub_input_widget.setFixedWidth(160)
                    sub_label.setFixedWidth(270)

                # add to groupbox of them
                sub_groupbox_layout.addWidget(sub_widget, 0, QtCore.Qt.AlignLeft)

            # add groupbox to sub layout
            sub_layout.addWidget(sub_groupbox, 0, QtCore.Qt.AlignTop)

        return sub_layout
    
    def get_sub_input_widget(self, hyperparameter_group_key, hyperparameter_sub_group_key, hyperparameter_parameter_dict:dict):
        # ==================================== bool type (toggle) ====================================
        if hyperparameter_parameter_dict["type"] == bool:
            # get toggle
            sub_input_widget = AnimatedToggle(
                pulse_checked_color="transparent",
                pulse_unchecked_color="transparent"
            )
            sub_input_widget.setContentsMargins(60, 0, 0, 0)

            if hyperparameter_parameter_dict["value"]:
                sub_input_widget.setChecked(True)
            else:
                sub_input_widget.setChecked(False)

            # set signal
            sub_input_widget.clicked.connect(lambda: self.update_hyperparameter(hyperparameter_group_key, hyperparameter_sub_group_key, hyperparameter_parameter_dict, sub_input_widget.isChecked()))
        
        # ==================================== int or float type (editline) ====================================
        elif hyperparameter_parameter_dict["type"] == int or hyperparameter_parameter_dict["type"] == float:
            # rewrite focus out event function
            class _QLineEdit(QtWidgets.QLineEdit):
                def __init__(self, hyperparameter_main, hyperparameter_parameter_dict):
                    super().__init__()
                    self.hyperparameter_main = hyperparameter_main
                    self.hyperparameter_parameter_dict = hyperparameter_parameter_dict
                    self.setText(self.get_scientific_notation(hyperparameter_parameter_dict["value"], float_point=4, int_point=6))
                
                def focusOutEvent(self, event):
                    input_text_value = self.text()
                    if input_text_value == "" or input_text_value == "-":
                        input_text_value = str(self.hyperparameter_parameter_dict["value"])

                    # int
                    if self.hyperparameter_parameter_dict["type"] == int:
                        input_value = int(input_text_value)
                        # check length of text and change to scientific notification
                        self.setText(self.get_scientific_notation(input_value, float_point=4, int_point=6))
                    # float
                    else:
                        try:
                            input_value = float(input_text_value)
                            if self.hyperparameter_parameter_dict["none_zero"] and input_value == 0.0:
                                input_value = self.hyperparameter_parameter_dict["none_zero_value"]
                        except:
                            input_value = self.hyperparameter_parameter_dict["value"]
                        # check length of text and change to scientific notification
                        self.setText(self.get_scientific_notation(input_value, float_point=4, int_point=6))
                    
                    self.hyperparameter_parameter_dict["value"] = input_value
                    self.hyperparameter_main.save_config()
                    return super().focusOutEvent(event)
                
                def get_scientific_notation(self, input_value, float_point=4, int_point=6):
                    if "scientific_notation" in self.hyperparameter_parameter_dict:
                        if self.hyperparameter_parameter_dict["scientific_notation"] and len(str(input_value).split(".")[-1]) > float_point or len(str(input_value)) > int_point:
                            return f"{input_value:.1e}"
                        else:
                            return str(input_value)    
                    else:
                        return str(input_value)

            # get editline
            sub_input_widget = _QLineEdit(self, hyperparameter_parameter_dict)
            sub_input_widget.setMaxLength(7)
            sub_input_widget.setAlignment(QtCore.Qt.AlignCenter)

        # ==================================== list type (editline or combobox) ====================================
        elif hyperparameter_parameter_dict["type"] == list:
            # if hyperparameter_value type (is int or float) list then allow multiple input with by separate token
            if hyperparameter_parameter_dict["editable"]:
                # rewrite focus out event function
                class _QLineEdit(QtWidgets.QLineEdit):
                    def __init__(self, hyperparameter_main, hyperparameter_parameter_dict):
                        super().__init__()
                        self.hyperparameter_main = hyperparameter_main
                        self.hyperparameter_parameter_dict = hyperparameter_parameter_dict
                        self.setText(",".join(map(str, hyperparameter_parameter_dict["value"])))
                    
                    def focusOutEvent(self, event):
                        input_text_value =  self.text()
                        ignored_label_list = []
                        for input_value in input_text_value.split(","):
                            if input_value == "":
                                continue
                            ignored_label_list.append(int(input_value))

                        if input_text_value == "":
                            ignored_label_list = self.hyperparameter_parameter_dict["value"]

                        ignored_label_list = sorted(set(ignored_label_list))
                        self.setText(",".join(map(str, ignored_label_list)))
                        self.hyperparameter_parameter_dict["value"] = ignored_label_list
                        self.hyperparameter_main.save_config()
                        return super().focusOutEvent(event)
                
                # get editline
                sub_input_widget = _QLineEdit(self, hyperparameter_parameter_dict)
                sub_input_widget.setAlignment(QtCore.Qt.AlignCenter)
            else:
                sub_input_widget = QtWidgets.QComboBox()
                sub_input_widget.addItems(list(map(str, hyperparameter_parameter_dict["data"])))
                sub_input_widget.setCurrentIndex(hyperparameter_parameter_dict["value"])
                sub_input_widget.currentIndexChanged.connect(lambda: self.update_hyperparameter(hyperparameter_group_key, hyperparameter_sub_group_key, hyperparameter_parameter_dict, sub_input_widget.currentIndex()))
        
        # TODO
        # DSAD AE Load
        # elif hyperparameter_parameter_dict["type"] == object:
        #     sub_input_widget = QtWidgets.QWidget()
        #     sub_input_layout = QtWidgets.QHBoxLayout(sub_input_widget)
        #     sub_button_widget = QtWidgets.QPushButton()
        #     sub_line_edit_widget = QtWidgets.QLineEdit()

        #     sub_button_widget.setText("···")
        #     sub_button_widget.setFixedWidth(20)

        #     sub_line_edit_widget.setText(hyperparameter_parameter_dict["value"])
        #     sub_line_edit_widget.setReadOnly(True)

        #     sub_input_layout.setContentsMargins(0, 0, 0, 0)

        #     sub_input_layout.addWidget(sub_line_edit_widget)
        #     sub_input_layout.addWidget(sub_button_widget)

        #     sub_button_widget.clicked.connect(lambda: self.add_path_status(sub_line_edit_widget, "DSAD", "ae_load"))

        # ==================================== sub configuration ====================================
        # set validator
        if "regex" in hyperparameter_parameter_dict:
            sub_input_widget.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp(hyperparameter_parameter_dict["regex"])))
        
        # set disabled
        if "disabled" in hyperparameter_parameter_dict:
            if hyperparameter_parameter_dict["disabled"]:
                sub_input_widget.setDisabled(True)
                sub_input_widget.setStyleSheet("background-color: gray;")

        return sub_input_widget

    def update_hyperparameter(self, group_key:str, sub_group_key:str, hyperparameter_parameter_dict:dict, value):
        hyperparameter_parameter_dict["value"] = value

        self.hyperparameter_validator(self.current_model_type, group_key, sub_group_key, value, ui_update=True)

        # save config
        self.save_config()
    
    def reset_hyperparameter(self):
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Information)
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        msgbox.setWindowTitle(self.lang.get("training", "hyperparameter_main", "hyperparameter_reset_info_title"))
        msgbox.setText(self.lang.get("training", "hyperparameter_main", "hyperparameter_reset_info_msg"))
        answer = msgbox.exec_()
        if answer == QMessageBox.Yes:
            hyperparameter_default = deepcopy(self.hyperparameter_default)
            for key in hyperparameter_default.keys():
                self.hyperparameter_shared_dict[key] = hyperparameter_default[key]
            self.CommonSettingsModelComboBox.setCurrentIndex(0)
            self.CommonSettingsSavePathLineEdit.setText(self.hyperparameter_shared_dict[self.current_model_type]["save_path"]) # save path
            self.CommonSettingsLoadPathLineEdit.setText(self.hyperparameter_shared_dict[self.current_model_type]["load_path"]) # load path
            self.CommonSettingsLoadRefPathLineEdit.setText(self.hyperparameter_shared_dict[self.current_model_type]["load_ref_path"]) # ref path
            self.CommonSettingsVideoToggle.setChecked(self.hyperparameter_shared_dict["show_video"])

            self.init_cuda_status()
            self.save_config()

    # ============================== add methods ==============================
    def add_hyperparameter_layout(self, model_type:str):
        self.ParameterSettingsSubWidgetLayout.addLayout(self.get_sub_layout(model_type))

    # Common Settings
    def add_path_status(self, model_type:str, path_type:str):
        # filedialog
        if path_type == "save" or path_type == "load_ref":
            key = "save_path" if path_type == "save" else "load_ref_path"
            file_dialog = QFileDialog(directory=self.hyperparameter_shared_dict[model_type][key])
            file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
            file_dialog.setFileMode(QFileDialog.DirectoryOnly)
            # get save path
            if file_dialog.exec_():
                path = file_dialog.selectedFiles()[0]
                # PyQt file dialog return the posix path style
                if os.name == "nt":
                    path = path.replace("/", "\\")

                self.hyperparameter_shared_dict[model_type][key] = path

                if path_type == "save":
                    self.CommonSettingsSavePathLineEdit.setText(path)
                    self.CommonSettingsSavePathLineEdit.setToolTip(path)
                else:
                    ref_list = []
                    for x in ["WHITEREF.hdr", "WHITEREF.raw", "DARKREF.hdr", "DARKREF.raw"]:                        
                        _x = os.path.join(path, x)
                        if not os.path.exists(_x):
                            ref_list.append(f"{self.lang.get('training', 'hyperparameter_main', 'hyperparameter_file_error_missing_msg')} '{x}' > {_x}")

                    if ref_list != []:
                        msgbox = QMessageBox()
                        msgbox.setIcon(QMessageBox.Information)
                        msgbox.setStandardButtons(QMessageBox.Ok)
                        msgbox.setWindowTitle(self.lang.get("training", "hyperparameter_main", "hyperparameter_file_error_title"))
                        msgbox.setText("\n".join(ref_list))
                        msgbox_widget = QtWidgets.QWidget()
                        msgbox_widget.setFixedWidth(int(10 * max((len(x)) for x in ref_list)))
                        msgbox.layout().addWidget(msgbox_widget, 3, 0, 1, 3)
                        msgbox.exec_()
                        return

                    self.CommonSettingsLoadRefPathLineEdit.setText(path)
                    self.CommonSettingsLoadRefPathLineEdit.setToolTip(path)

        elif path_type == "load":
            file_dialog = QFileDialog(directory=self.hyperparameter_shared_dict[model_type]["load_path"])
            file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
            file_dialog.setNameFilters(self.hyperparameter_shared_dict[model_type]["load_type"])
            # get load path
            if file_dialog.exec_():
                load_path = file_dialog.selectedFiles()[0]
                # PyQt file dialog return the posix path style
                if os.name == "nt":
                    load_path = load_path.replace("/", "\\")
                self.hyperparameter_shared_dict[model_type]["load_path"] = load_path
                self.CommonSettingsLoadPathLineEdit.setText(load_path)
                self.CommonSettingsLoadPathLineEdit.setToolTip(load_path)
        else:
            raise Exception("Not supported path type")
            
        self.save_config()

    def get_object(self, group_key, sub_group_key, object_index=2):
        for group_number in range(self.ParameterSettingsSubWidgetLayout.itemAt(0).count()):
            if self.ParameterSettingsSubWidgetLayout.itemAt(0).itemAt(group_number).widget().objectName() == group_key:
                for sub_group in self.ParameterSettingsSubWidgetLayout.itemAt(0).itemAt(group_number).widget().children():
                    if sub_group.objectName() == sub_group_key:
                        return sub_group.children()[object_index]

    # ============================== change methods ==============================
    def change_hyperparameter_layout(self, model_type:str):
        # update common settings status
        self.change_model_type(model_type)
        self.change_path_status(model_type)
        self.change_load_ref_status(model_type)
        self.change_cuda_status(model_type)

        # update
        self.update_hyperparameter_layout(model_type)

        # save config
        self.save_config()

    def change_model_type(self, model_type:str):
        self.hyperparameter_shared_dict["current_model_type"] = model_type
        self.current_model_type = model_type

    def change_path_status(self, model_type:str):
        self.CommonSettingsSavePathLineEdit.setText(self.hyperparameter_shared_dict[model_type]["save_path"])
        self.CommonSettingsSavePathLineEdit.setToolTip(self.hyperparameter_shared_dict[model_type]["save_path"])
        self.CommonSettingsLoadPathLineEdit.setText(self.hyperparameter_shared_dict[model_type]["load_path"])
        self.CommonSettingsLoadPathLineEdit.setToolTip(self.hyperparameter_shared_dict[model_type]["load_path"])
        self.CommonSettingsLoadRefPathLineEdit.setText(self.hyperparameter_shared_dict[model_type]["load_ref_path"])
        self.CommonSettingsLoadRefPathLineEdit.setToolTip(self.hyperparameter_shared_dict[model_type]["load_ref_path"])
        
    def change_cuda_status(self, model_type):
        if self.cuda_is_available and self.hyperparameter_shared_dict[model_type]["cuda_supported"]:
            self.CommonSettingsGPUDeviceComboBox.setItemText(0, self.available_cuda_list[0])
            self.CommonSettingsGPUToggle.setChecked(self.hyperparameter_shared_dict[model_type]["use_cuda"])
            self.CommonSettingsGPUToggle.setDisabled(False)
            self.CommonSettingsGPUDeviceComboBox.setCurrentIndex(self.hyperparameter_shared_dict[model_type]["cuda_device"])
            self.CommonSettingsGPUDeviceComboBox.setDisabled(False)
        else:
            self.CommonSettingsGPUDeviceComboBox.setItemText(0, f"{model_type} does not supported CUDA")
            self.CommonSettingsGPUToggle.setChecked(False)
            self.CommonSettingsGPUToggle.setDisabled(True)
            self.CommonSettingsGPUDeviceComboBox.setDisabled(True)
    
    def change_load_ref_status(self, model_type):
        self.CommonSettingsLoadRefPathToggle.setChecked(self.hyperparameter_shared_dict[model_type]["use_load_ref"])
        if self.hyperparameter_shared_dict[model_type]["use_load_ref"]:
            self.CommonSettingsLoadRefPathLineEdit.setStyleSheet("QLineEdit{color: white;}")
            self.CommonSettingsLoadRefPathPushButton.setDisabled(False)
        else:
            self.CommonSettingsLoadRefPathLineEdit.setStyleSheet("QLineEdit{color: gray;}")
            self.CommonSettingsLoadRefPathPushButton.setDisabled(True)

    # ============================== update methods ==============================
    def update_hyperparameter_layout(self, model_type):
        # TODO
        # re-organize this part
        self.lang.pop("training", "hyperparameter_description")
        self.lang.pop("training", "hyperparameter_main", "loader")
        self.lang.pop("training", "hyperparameter_main", "main_trainer")
        self.lang.pop("training", "hyperparameter_main", "sub_da_trainer")
        self.lang.pop("training", "hyperparameter_main", "sub_pa2e_trainer")

        for i in self.ParameterSettingsSubWidgetLayout.children():
            [i.itemAt(j).widget().deleteLater() for j in range(i.count())]
            i.deleteLater()
        
        # rebuild hyperparameter settings layout
        self.add_hyperparameter_layout(model_type)

    def update_cuda_status(self, model_type:str, use_cuda:bool, device_index:int):
        self.hyperparameter_shared_dict[model_type]["use_cuda"] = use_cuda
        self.hyperparameter_shared_dict[model_type]["cuda_device"] = device_index
        self.save_config()

    def update_show_video(self, show_video:bool):
        self.hyperparameter_shared_dict["show_video"] = show_video
        self.save_config()

    def update_load_ref_status(self, model_type:str, use_load_ref:bool):
        self.hyperparameter_shared_dict[model_type]["use_load_ref"] = use_load_ref
        if use_load_ref:
            self.CommonSettingsLoadRefPathLineEdit.setStyleSheet("QLineEdit{color: white;}")
            self.CommonSettingsLoadRefPathPushButton.setDisabled(False)
        else:
            self.CommonSettingsLoadRefPathLineEdit.setStyleSheet("QLineEdit{color: gray;}")
            self.CommonSettingsLoadRefPathPushButton.setDisabled(True)
        self.save_config()
    
    def update_model_description(self, modelDescription:str, Sync=None ):
        """
        description: update model description in common settings
        author: Hyunsu kim (2025.10.16)
        """
        self.hyperparameter_shared_dict["modelDescription"] = modelDescription
        Sync.hyperparameter_shared_dict = self.hyperparameter_shared_dict
        self.save_config()

    def init_config(self):
        if len(self.config["hyperparameters"].keys()) == 0: # default config (write)
            self.save_config()
        else:
            self.load_config()

    def save_config(self):
        for item_type in self.hyperparameter_shared_dict.keys():
            # params dict =======================================================================================
            if type(self.hyperparameter_shared_dict[item_type]) != dict:
                self.config["hyperparameters"][item_type] = self.hyperparameter_shared_dict[item_type]
            else:
                # Model (keys)
                if item_type not in self.config["hyperparameters"]:
                    self.config["hyperparameters"][item_type] = {}

                for group_key in self.hyperparameter_shared_dict[item_type]["params_dict"].keys(): # group (not shared)
                    group_name = self.hyperparameter_shared_dict[item_type]["params_dict"][group_key]["name"]
                    # Group (keys)
                    if group_key not in self.config["hyperparameters"][item_type]:
                        self.config["hyperparameters"][item_type][group_name] = {}

                    for sub_group_key in self.hyperparameter_shared_dict[item_type]["params_dict"][group_key].keys(): # sub_group (shared)
                        if type(self.hyperparameter_shared_dict[item_type]["params_dict"][group_key][sub_group_key]) == dict:
                            if self.hyperparameter_shared_dict[item_type]["params_dict"][group_key][sub_group_key]["visible"]:
                                self.config["hyperparameters"][item_type][group_name][sub_group_key] = self.hyperparameter_shared_dict[item_type]["params_dict"][group_key][sub_group_key]["value"]
                
                self.config["hyperparameters"][item_type]["save_path"] = self.hyperparameter_shared_dict[item_type]["save_path"]
                self.config["hyperparameters"][item_type]["load_path"] = self.hyperparameter_shared_dict[item_type]["load_path"]
                self.config["hyperparameters"][item_type]["load_ref_path"] = self.hyperparameter_shared_dict[item_type]["load_ref_path"]
                self.config["hyperparameters"][item_type]["use_load_ref"] = self.hyperparameter_shared_dict[item_type]["use_load_ref"]
            # params dict =======================================================================================

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def update_hyperparameter_shared_dict(self):
        for item_type in self.config["hyperparameters"].keys():
            try:
                # params dict =======================================================================================
                if type(self.config["hyperparameters"][item_type]) != dict:
                    self.hyperparameter_shared_dict[item_type] = self.config["hyperparameters"][item_type]
                else:
                    # print(self.hyperparameter_shared_dict[item_type]["params_dict"].keys())
                    for group_key in self.hyperparameter_shared_dict[item_type]["params_dict"].keys(): # group (not shared)
                        group_name = self.hyperparameter_shared_dict[item_type]["params_dict"][group_key]["name"]
                        for sub_group_key in self.hyperparameter_shared_dict[item_type]["params_dict"][group_key].keys(): # sub_group (shared)
                            if type(self.hyperparameter_shared_dict[item_type]["params_dict"][group_key][sub_group_key]) == dict:
                                if self.hyperparameter_shared_dict[item_type]["params_dict"][group_key][sub_group_key]["visible"]:
                                    value = self.config["hyperparameters"][item_type][group_name][sub_group_key]
                                    self.hyperparameter_shared_dict[item_type]["params_dict"][group_key][sub_group_key]["value"] = value
                                    self.hyperparameter_validator(item_type, group_key, sub_group_key, value)
                        
                        self.hyperparameter_shared_dict[item_type]["save_path"] = self.config["hyperparameters"][item_type]["save_path"]
                        self.hyperparameter_shared_dict[item_type]["load_path"] = self.config["hyperparameters"][item_type]["load_path"]
                        self.hyperparameter_shared_dict[item_type]["load_ref_path"] = self.config["hyperparameters"][item_type]["load_ref_path"]
                        self.hyperparameter_shared_dict[item_type]["use_load_ref"] = self.config["hyperparameters"][item_type]["use_load_ref"]
                # params dict =======================================================================================
            except:
                pass
                # self.save_config() # rewrite, if something is wrong
    
    def load_config(self, load_from_user:bool=False):
        if load_from_user:
            file_dialog = QFileDialog()
            file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
            file_dialog.setNameFilters(["json (*.json)"])
            if file_dialog.exec_():
                load_path = file_dialog.selectedFiles()[0]
                with open(load_path, "r", encoding="utf-8") as f:
                    self.config = json.loads(f.read())
                    self.update_hyperparameter_shared_dict()
                    current_model_type = self.hyperparameter_shared_dict["current_model_type"] # get current model type
                    self.CommonSettingsModelComboBox.setCurrentIndex(self.hyperparameter_shared_dict[current_model_type]["model_index"]) # set index
                    self.change_hyperparameter_layout(current_model_type) # update ui
        else:
            self.update_hyperparameter_shared_dict()

    def hyperparameter_validator(self, model_type, group_key, sub_group_key, value, ui_update=False):
        if sub_group_key == "binary":
            self.hyperparameter_shared_dict[model_type]["params_dict"]["loader"]["ignored"]["disabled"] = value
            if ui_update:
                temp_object = self.get_object("loader", "ignored")
                temp_object.setDisabled(value)
                temp_object.setStyleSheet("background-color: gray;" if value else "background-color: transparent;")

    def hyperparameter_signal_receiver(self, _dict):
        if "disabled" in _dict:
            self.ParameterResetPushButton.setDisabled(_dict["disabled"])
            self.CommonSettingsGroupBox.setDisabled(_dict["disabled"])
            self.ParameterSettingsMainWidget.setDisabled(_dict["disabled"])
    