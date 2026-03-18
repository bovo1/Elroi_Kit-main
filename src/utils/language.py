import os
import json
import types

from PyQt5 import QtWidgets
from pyqtgraph import PlotWidget
from utils.shared import resource_path

class Language():
    def __init__(self):
        self.language_dict = {}
        self.component_dict = {}

    def set(self, main_key, sub_key, name, value, **kwargs):
        if not main_key in self.component_dict:
            self.component_dict[main_key] = {}
        if not sub_key in self.component_dict[main_key]:
            self.component_dict[main_key][sub_key] = {}
        if not name in self.component_dict[main_key][sub_key]:
            self.component_dict[main_key][sub_key][name] = []
        
        if name in self.component_dict[main_key][sub_key]:
            self.component_dict[main_key][sub_key][name].append(value)
        else:
            self.component_dict[main_key][sub_key][name] = [value]

    def pop(self, main_key, sub_key, name=None):
        if name is None:
            if sub_key in self.component_dict[main_key]:
                self.component_dict[main_key].pop(sub_key)
        else:
            if name in self.component_dict[main_key][sub_key]:
                self.component_dict[main_key][sub_key].pop(name)
        
    def get(self, main_key, sub_key, name):
        try:
            return self.language_dict[main_key][sub_key][name]
        except:
            pass

    def apply(self, language: str = "en"):
        with open(os.path.join(resource_path, f"language/{language}.json"), "r", encoding="UTF-8") as f:
            self.language_dict = json.load(f)
        for main_key in self.language_dict:
            if main_key in self.component_dict:
                for sub_key in self.language_dict[main_key]:
                    if sub_key in self.component_dict[main_key]:
                        for name in self.language_dict[main_key][sub_key]:
                            if name in self.component_dict[main_key][sub_key]:
                                component = self.component_dict[main_key][sub_key][name]
                                value = self.language_dict[main_key][sub_key][name]
                                # print(component, value)

                                for _component in component:
                                    """
                                        @history :
                                            1. Yugyeong Hong(2026.03.13) : Add language parsing type for QCheckBox
                                    """
                                    if isinstance(_component, QtWidgets.QAction) or isinstance(_component, QtWidgets.QLabel) or isinstance(_component, QtWidgets.QCheckBox):
                                        _component.setText(value)

                                    if isinstance(_component, QtWidgets.QMenu) or isinstance(_component, QtWidgets.QGroupBox):
                                        # print(f"{component.objectName()}: {component}")
                                        _component.setTitle(value)
                                    
                                    """
                                        @history :
                                            1. Yugyeong Hong(2026.03.10) : Add language parsing type for QDialog
                                    """
                                    if isinstance(_component, QtWidgets.QToolBar) or isinstance(_component, QtWidgets.QDialog):
                                        _component.setWindowTitle(value)

                                    if isinstance(_component, QtWidgets.QPushButton):
                                        _component.setText(value[0])
                                        _component.setToolTip(value[1])
                                    
                                    if isinstance(_component, QtWidgets.QTabWidget):
                                        _component.setTabText(value[0], value[1])
                                    
                                    """
                                        @history :
                                            1. Hyeok Yoon(2025.10.31) : Modifying the separated combobox parsing type to one list
                                    """
                                    if isinstance(_component, QtWidgets.QComboBox):
                                        for i in range(len(value)):
                                            _component.setItemText(i, value[i])
                                        
                                    if isinstance(_component, PlotWidget):
                                        _component.plotItem.titleLabel.setText(value[0])
                                        _component.plotItem.setLabel("left", value[1])
                                        _component.plotItem.setLabel("bottom", value[2])

                                    """
                                        @history :
                                            1. Hyeok Yoon(2025.10.31) : Add language parsing option for QTableWidget
                                    """
                                    if isinstance(_component, QtWidgets.QTableWidget):
                                        if value[0] == "horizontal":
                                            _component.setHorizontalHeaderLabels(value[1])
                                        elif value[0] == "vertical":
                                            _component.setVerticalHeaderLabels(value[1])

                                    if isinstance(_component, types.MethodType):
                                        _component()
                                    
                                    if isinstance(_component, QtWidgets.QLineEdit):
                                        _component.setPlaceholderText(value)