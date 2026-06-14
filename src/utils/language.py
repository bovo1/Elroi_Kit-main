import os
import json
import types

from PyQt5 import QtWidgets
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QTreeWidgetItem
from pyqtgraph import PlotWidget
import pyqtgraph as pg
from utils.custom_item import customScatterItem
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

    def changePlotLegend(self, plot_item, name):
        """
            description : change legend of plot item
                parameters : plot_item - plot item to change legend, name - legend name to change
            author : Hyunsu Kim (2026.04.24)
        """
        plot_item.opts['name'] = name
        view_box = plot_item.getViewBox()
        if view_box is not None:
            legend = getattr(view_box.parentItem(), "legend", None)
            if legend is not None:
                legend_label = legend.getLabel(plot_item)
                if legend_label is not None:
                    legend_label.setText(name)

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
                                    if (isinstance(_component, QtWidgets.QToolBar) or isinstance(_component, QtWidgets.QDialog) or (isinstance(_component, QtWidgets.QWidget) and _component.isWindow())) and isinstance(value, str):
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

                                    """
                                        @history :
                                            1. Hyunsu Kim(2026.04.21) : Add language parsing option for QLineEdit, QDockWidget, PlotCurveItem, QStandardItem, QTreeWidgetItem
                                    """
                                    if isinstance(_component, QtWidgets.QLineEdit):
                                        _component.setPlaceholderText(value)

                                    if isinstance(_component, QtWidgets.QDockWidget):
                                        _component.setWindowTitle(value)
                                        
                                    if isinstance(_component, pg.PlotCurveItem) or isinstance(_component, customScatterItem):
                                        self.changePlotLegend(_component, value)

                                    if isinstance(_component, QStandardItem):
                                        _component.setText(value)

                                    if isinstance(_component, QTreeWidgetItem):
                                        _component.setText(0, value)

                                    if isinstance(_component, pg.PlotDataItem):
                                        self.changePlotLegend(_component, value)