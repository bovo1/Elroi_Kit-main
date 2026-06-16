"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""


import os
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget, QStackedWidget
from pyqtgraph import PlotWidget
from constants.constants import *
from labeling.module.graph_adv_option import setSavitzkyGolay, setGaussian
from utils.custom_item import customScatterItem
from labeling.module.advanced_analysis import visualizerLDA
from utils.custom_ui import messageBox

if __name__ == "__main__" :
    from graph_sub import graph_sub_Form
    from .graph_option import graphOptionForm
else:
    from .graph_sub import graph_sub_Form
    from .graph_option import graphOptionForm

class Graph_Form(QtWidgets.QWidget):
    """Graph와 관련된 모든 기능을 처리하기 위한 클래스
    """
    def __init__(self, Sync, lang) -> None:
        super().__init__()
        self.init(Sync, lang)
        self.init_Ui_label_graph_display(self)
        self.init_function()
        self.init_sub_function()
        self.setup_Ui_label_graph_display()
        self.setMouseTracking(True)

        if __name__ == "__main__":
            self.show()


    @pyqtSlot(dict)
    def recv_from_core(self, output):
        """그래프 리스트 업데이트를 위해 signal을 통해 실시간으로 정보를 업데이트하기 위한 함수이다.
            그래프를 표시하기 위해 HSI 데이터와 좌표를 받는다.
                Parameters
                1.	output(dict): 라벨 리스트를 생성하기 위한 라벨 정보(라벨번호, 라벨 컬러)
                    - output['mode']
                        0 : Core_DB에 저장하고 그래프에 영구적으로 표시해주기 위한
                        1 : Core_DB에 저장하지 않고 그래프에 임시로 보여주기 위한 모드
                        2 : 그래프에 표시된 plot을 제거
                    - output['point']: 그래프 업데이트를 위한 좌표
                    - output['color']: 그래프 업데이트 시 표시할 색
                    - output['shape']: 이미지의 shape
                    - output['point_data']: 좌표에 대한 hsi 데이터
                    - output['graph_number']: 그래프 저장할 번호
                History
                    1. Hyunsu Kim (2026.04.27): Add graph RGB Lines show/hide and position update function in response to signal from display_sub_rgb_change.py
                    2. Hyunsu Kim (2026.05.06): Change the rgbLinesWidget key from color name string to SUBRGB constants for better consistency and management. Update corresponding code to reflect this change.
                    
        """
        from_ = output['from']
        if from_ == 'image':
            if output['mode'] == 'unchecked':
                for obj_name in list(self.graph_obj_dict.keys()):
                    if obj_name not in ["graph_color"]:
                        self.graph_obj_dict[obj_name]['obj'].setChecked(False)
                self.clear_graph_list()
                self.clearLDAGraph()
            else:
                self.clear_graph_list()
                if self.graphRgb.isChecked():
                    self.graphRgb.setChecked(False)
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_RED])
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_GREEN])
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_BLUE])
                # when currentgraphmode is LDA, clear_graph_list function only clear the graph points that user added in LDA graph widget.
                # create a clearLDAGraph function to reset the entire LDA graph when the image is changed or released.
                self.clearLDAGraph()
                self.select_image_number = output['image_number']
                self.select_image_name = output['data_name']
                self.save_path = output['save_path']
                self.hsi_metadata = output['hsi_metadata']
                if 'wavelength' in self.hsi_metadata:
                    self.hsi_metadata['wavelength'] = list(map(float, self.hsi_metadata['wavelength']))
                    # Store minWavelength/maxWavelength values for making RGB line bounds and setting x-axis range of graph plot widget
                    minWavelength = self.hsi_metadata['wavelength'][0]
                    maxWavelength = self.hsi_metadata['wavelength'][-1]
                    self.graph_plot_widget.setXRange(minWavelength, maxWavelength, padding=0.05)

                    # Set bounds for RGB lines on the x-axis
                    for idx, color in enumerate(RGB):
                        self.rgbLinesWidget[color].setBounds((minWavelength - 0.05, maxWavelength + 0.05))
                        if 'default band' in self.hsi_metadata:
                            self.rgbLinesWidget[color].setValue(self.hsi_metadata['wavelength'][int(self.hsi_metadata['default band'][idx])])

                    # Connect move events for RGB lines
                    self.rgbLinesWidget[SUBRGB_RED].sigDragged.connect(lambda:self.rgbLineMove(self.rgbLinesWidget[SUBRGB_RED], "red"))
                    self.rgbLinesWidget[SUBRGB_GREEN].sigDragged.connect(lambda:self.rgbLineMove(self.rgbLinesWidget[SUBRGB_GREEN], "green"))
                    self.rgbLinesWidget[SUBRGB_BLUE].sigDragged.connect(lambda:self.rgbLineMove(self.rgbLinesWidget[SUBRGB_BLUE], "blue"))
                    
                else:
                    self.hsi_metadata['wavelength'] = list(range(224))
                    for color in RGB:
                        self.rgbLinesWidget[color].setBounds((0, 223))

        elif from_ == 'display':
            mode = output['mode']
            if mode == GRAPH_DISPLAY_PREVIEW:
                cur_y, cur_x= output['point']
                tmp_hsi_spectral = output['point_data']
                # applycurrentgraphfilter function return original data if graph filter is not active
                tmp_hsi_spectral = self.applyCurrentGraphFilter(tmp_hsi_spectral)
                hsi_width, hsi_height, hsi_wavelength = output['shape']
                # 그래프에 표시
                if len(tmp_hsi_spectral):
                    if cur_y < hsi_width or cur_x < hsi_height:
                        # when current graph mode is basic(graph_plot_widget)
                        if self.graphStackWidget.currentWidget() == self.graph_plot_widget:
                            if self.graph_control_dict['graph_line_preview']:
                                self.line_graph_preview.setData(self.hsi_metadata['wavelength'], tmp_hsi_spectral)
                        # when current graph mode is LDA mode.
                        elif self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                            if self.graph_control_dict['graph_line_preview']:
                                modelOutTmpHsiSpectral = self.visualizerLDA.transformSpectralData(tmp_hsi_spectral)
                                self.scatterGraphPreview.setData(x=[modelOutTmpHsiSpectral[0,0]], y=[modelOutTmpHsiSpectral[0,1]])

        elif from_ == "graphGroup":
            # Draw
            if output["mode"] == GRAPH_GROUP_DRAW_GRAPH:
                point = output["point"]
                point_y, point_x = point[0], point[1]
                spectralData = output["data"]
                color = output["color"]
                selectiveGraphIdx = output["selectiveGraphIdx"]
                labelClass = output["labelClass"]
                imageShape = output["shape"]
                if len(spectralData):
                    if point_y < imageShape[1] and point_x < imageShape[0]:
                        self.drawGraph(point, spectralData, color, selectiveGraphIdx, labelClass)

            # Hide/Show partial
            elif output["mode"] == GRAPH_DISPLAY_PARTIAL:
                groupIdx = output['index']
                view = output['view']
                hideState = output['hideState']
                self.hideGraph(hideState, groupIdx, True, (view=="label"))

            # Hide/Show all
            elif output["mode"] == GRAPH_DISPLAY_ALL:
                hideState = output['hideState']
                view = output['view']
                self.hideGraph(hideState, -1, False, (view=="label"))
            
            # Change color
            elif output["mode"] == GRAPH_GROUP_COLOR_CHANGE:
                groupIdx = output['index']
                color = output['color']
                label = output.get("label", False)
                self.changeGraphGroupColor(color, groupIdx, label)
            
            # Remove group
            elif output["mode"] == GRAPH_GROUP_REMOVE:
                groupIdx = output['index']
                isLabel = output["label"]
                removedLabelItem = output.get("removedLabelItem", None)
                self.removeGraphGroup(groupIdx, isLabel, removedLabelItem)
            
            #Remove group
            elif output["mode"] == GRAPH_GROUP_REMOVE_ALL:
                self.clear_graph_list()
                self.graph_check.setChecked(False)
                self.graph_eraser.setChecked(False)

            # Remove graph
            elif output["mode"] == GRAPH_GROUP_REMOVE_GRAPH:
                selectiveIdx = output["removedSelectiveGraph"]
                labelIdx = output["removedLabelGraph"]
                point = output["point"]
                self.removeGraph(selectiveIdx, labelIdx, point)

            # Convert View
            elif output["mode"] == GRAPH_GROUP_CONVERT_LABEL_VIEW:
                self.convertGraphView(output["mode"])
            elif output["mode"] == GRAPH_GROUP_CONVERT_SELECTIVE_VIEW:
                self.convertGraphView(output["mode"])

            # Merge label
            elif output["mode"] == MERGE_LABEL:
                # change graph color
                color = output['color']
                if self.graph_control_dict['graph_view_mode'] == GRAPH_VIEW_MODE_LABEL_COLOR:
                    self.changeGraphGroupColor(color, output["labelClass"], True)

        elif from_ == "display_sub_rgb_change":
            """
                Description : Disable graphRgb and remove RGB lines in view-1 and view-2 modes and update RGB line position when RGB line is visible.
                Author: Hyunsu Kim (2026.04.23)
            """
            # Enable the RGB icon only in RGB view mode
            if "currentViewMode" in output and self.select_image_number != IMAGE_UNSELECTED:
                if output['currentViewMode'] == VISUALIZATION_MODE_RGB:
                    self.graphRgb.setEnabled(True)
                else:
                    if self.graphRgb.isChecked():
                        self.graphRgb.setChecked(False)
                    self.graphRgb.setEnabled(False)
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_RED])
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_GREEN])
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_BLUE])
                pass
            else:
                # Update RGB line value to match the slider/combobox value
                band = output["band"]
                color = output["color"]
                self.rgbLinesWidget[color].setValue(self.hsi_metadata['wavelength'][band])

    @pyqtSlot(dict)
    def recieveFromGraphOptionMenu(self, output):
        """
            @description : receive signals from graph option menu and perform corresponding actions on graph based on the received signal
            @author : GaEun Hwang (2026.04.10)
        """
        if "DefaultView" in output:
            if self.graphStackWidget.currentWidget() == self.graph_plot_widget:
                self.graph_plot_widget.setYRange(*self.graphYRange, padding=0.05)
            elif self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                self.ldaGraphPlotWidget.plotItem.getViewBox().autoRange()
        
        elif "Grid" in output:
            if "axis" in output["Grid"] and "state" in output["Grid"]:
                axis = output["Grid"]["axis"]
                state = output["Grid"]["state"]
                self.graphStackWidget.currentWidget().getPlotItem().showGrid(x=state if axis=="x" else None, y=state if axis=="y" else None)
            elif "opacity" in output["Grid"]:
                opacity = output["Grid"]["opacity"]
                self.graphStackWidget.currentWidget().getPlotItem().showGrid(alpha=opacity/100)

    def init(self, Sync=None, lang=None):
        """graph 리스트 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.	Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.lang = lang
        self.Sync = Sync
        self.core_to_graph_signal = self.Sync.core_to_graph_signal
        self.core_to_graph_signal.connect(self.recv_from_core)
        self.graph_to_core_signal = self.Sync.graph_to_core_signal
        self.graphOptionToGraphSignal = self.Sync.graphOptionToGraphSignal
        self.graphOptionToGraphSignal.connect(self.recieveFromGraphOptionMenu)
        self.graph_to_display_signal = self.Sync.graph_to_display_signal
        self.graphToGraphGroupSignal = self.Sync.graphToGraphGroupSignal
        self.graphToDisplaySubRgbChangeSignal = self.Sync.graphToDisplaySubRgbChangeSignal
        self.graph_control_dict = self.Sync.graph_control_dict
        self.display_control_dict = self.Sync.display_control_dict
        self.sub_widget_dict = self.Sync.sub_widget_dict
        self.graph_legend_count = 0
        self.select_image_number = IMAGE_UNSELECTED
        self.select_image_name = ""
        self.save_path =""
        self.graphNoneMode = self.lang.get("labeling", "graph_main", "graphNoneMode")

        """
            Description: Setting graph preview always top and remove transparency
            Modified by MyoungHwan (2024.09.06)
            History:
                1. Modified by Hyunsu Kim (2026.04.24): change graph preview name to "graphPreview" and "scatterPreview" for translation in language file
        """
        #legend option
        self.line_graph_preview = pg.PlotCurveItem(name=self.lang.get("labeling", "graph_main", "graphPreview"))
        self.lang.set("labeling", "graph_main", "graphPreview", self.line_graph_preview)
        self.line_graph_preview_pen_color = pg.mkPen(QtGui.QColor(255,255,0),width=1.5)
        self.line_graph_preview.setPen(self.line_graph_preview_pen_color)
        self.line_graph_preview.setZValue(1)
        self.scatterGraphPreview = customScatterItem(name=self.lang.get("labeling", "graph_main", "scatterPreview"))
        self.lang.set("labeling", "graph_main", "scatterPreview", self.scatterGraphPreview)
        self.scatterGraphPreview.setSize(10)
        self.scatterGraphPreview.setPen(pg.mkPen(QtGui.QColor(0,0,0)))
        self.scatterGraphPreview.setBrush(pg.mkBrush(QtGui.QColor(255,255,0)))
        self.scatterGraphPreview.setZValue(1)

        self.old_line = []

        self.graph_obj_dict = self.Sync.graph_obj_dict
        self.graph_point_number_dict = {}
        self.graph_point_dict = {}

        self.graphGroupDict = self.Sync.graphGroupDict
        self.labelViewGraphGroupDict = self.Sync.labelViewGraphGroupDict

        self.Core_DB_Labeling = self.Sync.Core_DB_Labeling
        self.image_control_dict = self.Sync.image_control_dict
        self.label_obj_dict = self.Sync.label_obj_dict
        
        # graph info
        self.graphYRange = (0, 5000)
        self.currentFilterMode = self.graphNoneMode
        self.originGraphData = {}

        # visualizer for data to lda data
        self.visualizerLDA = visualizerLDA()

        """
             Description: Initialize RGB line widgets and pens for normal and selected states.
             Modified by Hyunsu Kim (2026.04.23)
        """
        self.rgbLinesWidget = {}
        self.rgbLinePens = {
            "red": pg.mkPen('r', width=RGB_LINE_DEFAULT_WIDTH),
            "green": pg.mkPen('g', width=RGB_LINE_DEFAULT_WIDTH),
            "blue": pg.mkPen('b', width=RGB_LINE_DEFAULT_WIDTH),
        }
        self.rgbLineSelectedPens = {
            "red": pg.mkPen('r', width=RGB_LINE_SELECTED_WIDTH),
            "green": pg.mkPen('g', width=RGB_LINE_SELECTED_WIDTH),
            "blue": pg.mkPen('b', width=RGB_LINE_SELECTED_WIDTH),
        }

    def init_Ui_label_graph_display(self, Form):
        """
            description: graph 리스트 UI 생성을 위한 초기 선언문이다.
                Parmeters
                1.	Form(object): PyQt widget object
                History:
                    2025.12.05 - remove graph hide widget, color combobox widget for better mangement by GaEun Hwang
                    2026.04.23 - Add RGB line widget initialization for graph display by Hyunsu Kim
        """
        Form.setObjectName("graph_form")
        Form.setWindowTitle("graph_form")

        self.graph_main_vertical = QVBoxLayout(Form)
        self.graph_main_vertical.setObjectName("graph_main_vertical")
        self.graph_main_horizon = QHBoxLayout()
        self.graph_main_horizon.setObjectName("graph_main_horizon")
        self.graph_main_setting_list_top_horizon = QtWidgets.QHBoxLayout()
        self.graph_main_setting_list_top_horizon.setObjectName("graph_main_setting_list_top_horizon")

        self.graph_check = QtWidgets.QPushButton()
        self.graph_check.setCheckable(True)
        graph_check_icon = QtGui.QIcon()
        graph_check_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_check_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        graph_check_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_check_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        graph_check_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_check_disabled.png"), QtGui.QIcon.Disabled)
        self.graph_check.setIcon(graph_check_icon)
        self.graph_check.setObjectName("graph_check")
        self.lang.set("labeling", "graph_main", "graph_check", self.graph_check)

        self.graph_eraser = QtWidgets.QPushButton()
        graph_eraser_icon = QtGui.QIcon()
        graph_eraser_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_eraser_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        graph_eraser_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_eraser_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        graph_eraser_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_eraser_disabled.png"), QtGui.QIcon.Disabled)
        self.graph_eraser.setIcon(graph_eraser_icon)
        self.graph_eraser.setObjectName("graph_eraser")
        self.graph_eraser.setCheckable(True)
        self.lang.set("labeling", "graph_main", "graph_eraser", self.graph_eraser)

        self.graph_clear = QtWidgets.QPushButton()
        graph_clear_icon = QtGui.QIcon()
        graph_clear_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_clear_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        graph_clear_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_clear_disabled.png"), QtGui.QIcon.Disabled)
        self.graph_clear.setIcon(graph_clear_icon)
        self.graph_clear.setObjectName("graph_clear")
        self.lang.set("labeling", "graph_main", "graph_clear", self.graph_clear)

        self.graphRgb = QtWidgets.QPushButton()
        graphRgbIcon = QtGui.QIcon()
        graphRgbIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_rgb_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        graphRgbIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_rgb_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        graphRgbIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_rgb_disabled.png"), QtGui.QIcon.Disabled)
        self.graphRgb.setIcon(graphRgbIcon)
        self.graphRgb.setObjectName("graphRgb")
        self.graphRgb.setCheckable(True)
        self.lang.set("labeling", "graph_main", "graphRgb", self.graphRgb)
        
        self.graph_setting = QtWidgets.QPushButton()
        graph_setting_icon = QtGui.QIcon()
        graph_setting_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_setting_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        graph_setting_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_setting_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        graph_setting_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_setting_disabled.png"), QtGui.QIcon.Disabled)
        self.graph_setting.setIcon(graph_setting_icon)
        self.graph_setting.setObjectName("graph_setting")
        self.graph_setting.setCheckable(True)
        self.lang.set("labeling", "graph_main", "graph_setting", self.graph_setting)

        self.graph_plot_widget = PlotWidget()
        self.graph_plot_widget.setObjectName("graph_plot_widget")
        self.graph_plot_widget.setBackground(QtGui.QColor(83, 83, 83))        
        self.graph_plot_widget.addLegend()
        self.graph_plot_widget.getPlotItem().setMenuEnabled(False)

        self.ldaGraphPlotWidget = PlotWidget()
        self.ldaGraphPlotWidget.setObjectName("ldaGraphPlotWidget")
        self.ldaGraphPlotWidget.setBackground(QtGui.QColor(83, 83, 83))
        self.ldaGraphPlotWidget.addLegend()
        self.ldaGraphPlotWidget.getPlotItem().setMenuEnabled(False)

        # create stacked widget for stack plotwidget
        """
            Description: change QStackedLayout to QStackedWidget for easier management of stacked widgets.
            Modified by GaEun Hwang (2024.09.30)
        """
        self.graphStackWidget = QStackedWidget()
        self.graphStackWidget.addWidget(self.graph_plot_widget)
        self.graphStackWidget.addWidget(self.ldaGraphPlotWidget)
        self.graphStackWidget.setCurrentWidget(self.graph_plot_widget)

        self.graph_legend_main = QWidget()
        self.graph_legend_main.setObjectName("graph_legend_main")

        self.graph_legend_vertical = QVBoxLayout(self.graph_legend_main)
        self.graph_legend_vertical.setObjectName("graph_legend_vertical")

        self.graph_legend_list = QListWidget()
        self.graph_legend_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.graph_legend_buttons_horizon = QHBoxLayout()
        self.graph_legend_buttons_horizon.setObjectName("graph_legend_buttons_horizon")

        self.graph_legend_buttons_all_check = QPushButton()
        self.graph_legend_buttons_all_check.setObjectName("graph_legend_buttons_all_check")
        graph_legend_buttons_all_check_icon= QtGui.QIcon()
        graph_legend_buttons_all_check_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphbox/graph_select_off.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        graph_legend_buttons_all_check_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphbox/graph_select_on.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.graph_legend_buttons_all_check.setIcon(graph_legend_buttons_all_check_icon)
        self.graph_legend_buttons_all_check.setCheckable(True)
        self.graph_legend_buttons_all_check.setChecked(True)

        self.graph_legend_buttons_select_delete = QPushButton()
        self.graph_legend_buttons_select_delete.setObjectName("graph_legend_buttons_select_delete")
        graph_legend_buttons_select_delete_icon= QtGui.QIcon()
        graph_legend_buttons_select_delete_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphbox/graph_remove.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.graph_legend_buttons_select_delete.setIcon(graph_legend_buttons_select_delete_icon)
        self.graph_legend_buttons_select_delete.setEnabled(False)

        self.graph_main_setting_list_sub_horizon = QtWidgets.QHBoxLayout()
        self.graph_main_setting_list_sub_horizon.setObjectName("graph_main_setting_list_sub_horizon")

        self.graph_linedrawing = QtWidgets.QPushButton()
        self.graph_linedrawing.setText("")
        self.graph_linedrawing.setCheckable(True)
        graph_linedrawing_icon = QtGui.QIcon()
        graph_linedrawing_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_hide.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        graph_linedrawing_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_show.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        graph_linedrawing_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_show_disabled.png"), QtGui.QIcon.Disabled)
        self.graph_linedrawing.setIcon(graph_linedrawing_icon)
        self.graph_linedrawing.setObjectName("graph_linedrawing")
        self.lang.set("labeling", "graph_main", "graph_linedrawing", self.graph_linedrawing)

        self.ldaGraphRefitBtn = QtWidgets.QPushButton()
        self.ldaGraphRefitBtn.setObjectName("ldaGraphRefitBtn")
        self.lang.set("labeling", "graph_main", "ldaGraphRefit", self.ldaGraphRefitBtn)
        ldaGraphRefitBtn_icon = QtGui.QIcon()
        ldaGraphRefitBtn_icon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_lda_refit_btn.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.ldaGraphRefitBtn.setIcon(ldaGraphRefitBtn_icon)
        self.ldaGraphRefitBtn.setVisible(False)

        self.graphComboboxSelectAdvOption = QtWidgets.QComboBox()
        self.graphComboboxSelectAdvOption.setObjectName("graphComboboxSelectAdvOption")
        self.graphComboboxSelectAdvOption.addItem(self.graphNoneMode)
        self.graphComboboxSelectAdvOption.addItem(GRAPH_FILTER_SAVITZKY_GOLAY)
        self.graphComboboxSelectAdvOption.addItem(GRAPH_FILTER_GAUSSIAN)
        self.graphComboboxSelectAdvOption.addItem(GRAPH_FILTER_LDA)
        self.graphComboboxSelectAdvOption.setCurrentIndex(0)
        self.lang.set("labeling", "graph_main", "graphNoneMode", self.graphComboboxSelectAdvOption.model().item(0))

        self.graphMenu = graphOptionForm(Sync=self.Sync, lang=self.lang, parent=self)

        self.rgbLinesWidget[SUBRGB_RED] = pg.InfiniteLine(angle=90, pen=self.rgbLinePens["red"], hoverPen=self.rgbLineSelectedPens["red"], movable=True)
        self.rgbLinesWidget[SUBRGB_GREEN] = pg.InfiniteLine(angle=90, pen=self.rgbLinePens["green"], hoverPen=self.rgbLineSelectedPens["green"], movable=True)
        self.rgbLinesWidget[SUBRGB_BLUE] = pg.InfiniteLine(angle=90, pen=self.rgbLinePens["blue"], hoverPen=self.rgbLineSelectedPens["blue"], movable=True)
        for line in self.rgbLinesWidget.values():
            line.setZValue(10)

        QtCore.QMetaObject.connectSlotsByName(Form)


    def setup_Ui_label_graph_display(self):
        """초기화된 graph 리스트의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
        """
        # self.graph_widget.setMinimumSize(QtCore.QSize(350, 300))
        # self.graph_widget.setMaximumSize(QtCore.QSize(350, 300))
        self.graph_legend_list.setMinimumSize(QtCore.QSize(100, 0))
        # self.graph_legend_list.setMaximumSize(QtCore.QSize(100, QT_MAX_SIZE))
        self.graph_legend_main.setMinimumSize(QtCore.QSize(120, 0))
        # self.graph_legend_main.setMaximumSize(QtCore.QSize(120, QT_MAX_SIZE))
        
        
        self.graph_main_setting_list_top_horizon.addWidget(self.graph_linedrawing)
        self.graph_main_setting_list_top_horizon.addWidget(self.graph_check)
        self.graph_main_setting_list_top_horizon.addWidget(self.graph_eraser)
        self.graph_main_setting_list_top_horizon.addWidget(self.graph_clear)
        self.graph_main_setting_list_top_horizon.addWidget(self.graphRgb)
        self.graph_main_setting_list_top_horizon.addStretch(1)
        self.graph_main_setting_list_top_horizon.addWidget(self.graph_setting)

        self.graph_main_setting_list_sub_horizon.addStretch(1)
        self.graph_main_setting_list_sub_horizon.addWidget(self.ldaGraphRefitBtn)
        self.graph_main_setting_list_sub_horizon.addWidget(self.graphComboboxSelectAdvOption)

        """
            description: add self.graphStackWidget instead of self.graph_plot_widget for to allow graph widget to change contextually.
            modified by GaEun Hwang (2025.09.30)
        """
        self.graph_main_horizon.addWidget(self.graphStackWidget)
        self.graph_main_horizon.setContentsMargins(0,0,0,0)

        self.graph_main_vertical.addLayout(self.graph_main_setting_list_top_horizon)
        self.graph_main_vertical.addLayout(self.graph_main_setting_list_sub_horizon)
        self.graph_main_vertical.addLayout(self.graph_main_horizon)
        
        self.graph_legend_buttons_horizon.addWidget(self.graph_legend_buttons_all_check)
        self.graph_legend_buttons_horizon.addWidget(self.graph_legend_buttons_select_delete)

        self.graph_legend_vertical.addWidget(self.graph_legend_list)
        self.graph_legend_vertical.addLayout(self.graph_legend_buttons_horizon)
        self.styles = {'color':'White', 'font-size':'15px'}

        # self.graph_plot_widget setting
        self.graph_plot_widget.setTitle("", font='80px')
        # self.graph_plot_widget.plotItem.setMouseEnabled(y=False)
        self.graph_plot_widget.plotItem.setLimits(yMin=-10)
        self.graph_plot_widget.plotItem.setMouseEnabled(x=False)
        self.graph_plot_widget.setLabel('left', '', **self.styles)
        self.graph_plot_widget.setLabel('bottom', '', **self.styles)
        self.graph_plot_widget.setXRange(0, 224, padding=0.05)
        self.graph_plot_widget.setYRange(*self.graphYRange, padding=0.05)
        self.lang.set("labeling", "graph_main", "graph_plot_widget", self.graph_plot_widget)

        # self.ldaGraphPlotWidget setting
        self.ldaGraphPlotWidget.setTitle("", font='80px')
        self.ldaGraphPlotWidget.setLabel('left', '', **self.styles)
        self.ldaGraphPlotWidget.setLabel('bottom', '', **self.styles)
        self.lang.set("labeling", "graph_main", "ldaGraphPlotWidget", self.ldaGraphPlotWidget)

        self.graph_obj_dict['graph_check']={
            'obj':self.graph_check
        }
        self.graph_obj_dict['graph_eraser']={
            'obj':self.graph_eraser
        }
        self.graph_obj_dict['graphRgb']={
            'obj':self.graphRgb
        }
        self.graph_obj_dict['graph_clear']={
            'obj':self.graph_clear
        }
        self.graph_obj_dict['graph_linedrawing']={
            'obj':self.graph_linedrawing
        }
        self.graph_obj_dict['graph_sub'] = {
            'obj' : self.graph_setting,
            'opened' : False,
            'sub_form' : self.graph_sub_form
        }

            
    def init_function(self):
        """그래프 기능들에 대한 connect 함수를 정의한다.
        """
        self.graph_check.clicked.connect(lambda ch = self.graph_check: self.graph_mode(ch=ch, mode=GRAPH_DRAW))
        self.graph_eraser.clicked.connect(lambda ch = self.graph_eraser: self.graph_mode(ch=ch, mode=GRAPH_ERASE))
        self.graphRgb.clicked.connect(lambda ch=self.graphRgb: self.graph_mode(ch=ch, mode=GRAPH_RGB))
        self.graph_clear.clicked.connect(lambda: self.graph_mode(mode=GRAPH_CLEAR))
        self.graph_setting.clicked.connect(lambda ch = self.graph_setting: self.graph_mode(ch=ch, mode=GRAPH_DISPLAY_SUB_FORM))
        self.graph_linedrawing.clicked.connect(lambda ch = self.graph_linedrawing: self.graph_mode(ch=ch, mode=GRAPH_DISPLAY_PREVIEW))
        self.graph_legend_list.itemClicked.connect(lambda item = self.graph_legend_list : self.select_graph_line(item=item))
        self.graph_legend_buttons_all_check.clicked.connect(lambda ch=self.graph_legend_buttons_all_check: self.select_graph_all(ch=ch))
        self.graph_legend_buttons_select_delete.clicked.connect(self.select_graph_delete)
        self.ldaGraphRefitBtn.clicked.connect(lambda : self.refitLdaGraph())
        self.graphComboboxSelectAdvOption.currentTextChanged.connect(lambda value=self.graphComboboxSelectAdvOption : self.statechangeGraphAdvOptionCombobox(value=value))

    def init_sub_function(self):
        self.graph_sub_form = graph_sub_Form(Sync=self.Sync, lang=self.lang, parent=self)
        self.sub_widget_dict['graph_sub_form'] = self.graph_sub_form

    def rgbLineMove(self, movedLine, mode="red"):
        """
            Description: Event handler connected to RGB Lines widgets to control comboboxes and sliders in display_sub_rgb_change
            Author: Hyunsu Kim (2026.04.23)
            Parameters:
                movedLine: the RGB line widget selected and moved by the user
                mode: color of the moved line, to identify which line is moved among the three RGB lines
        """
        rgbLineValue = movedLine.value() # Get wavelength of moved line

        # Find the band index closest to the selected wavelength
        wavelength = np.array(self.hsi_metadata['wavelength'], dtype=float)
        band = np.abs(wavelength - rgbLineValue).argmin()

        tmpDict = {}
        tmpDict['color'] = mode
        tmpDict['band'] = int(band)
        tmpDict['mode'] = 'graph'
        tmpDict['type'] = 'rgbLines'
        # Send signal to display_sub_rgb_change
        self.graphToDisplaySubRgbChangeSignal.emit(tmpDict)

    def checkLdaAvailability(self, labelMatrix):
        """
            @description : check if lda model can be fitted
            @author : GaEun Hwang (2025.09.23)
        """
        uniqueLabel, counts = np.unique(labelMatrix, return_counts=True)
        pixelCount = dict(zip(uniqueLabel, counts))
        isPixelCountSufficient = all(count >= 2 for label, count in pixelCount.items() if label != 0) # class 0 is unlabeled area
        # check if labelMatrix has at least 3 classes and each class has at least 2 pixels
        if len(pixelCount) > 3 and isPixelCountSufficient:
            return True
        else:
            return False
    
    def refitLdaGraph(self):
        """
            @description : refit lda model
            @author : GaEun Hwang (2025.09.04)
            @history :
                Yugyeong Hong(2026.02.25) - Refactor message box with util method and language support
        """
        select_image_number = self.image_control_dict['select_image_number']
        labelList = self.Core_DB_Labeling['image_list'][select_image_number]['label_list']
        label = self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label']
        raw = self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_raw']
        if self.checkLdaAvailability(label):
            self.ldaData, self.ldaScaler, self.ldaModel = self.visualizerLDA.fitModel(raw, label)
            self.ldaGraphPlotWidget.clear()
            self.plotLDAGraph(self.ldaData, label, labelList)
        else:
            messageBox(mode=MESSAGE_BOX_INFORMATION,
                       title=self.lang.get("main", "messageBox", "msgInformation"),
                       text=self.lang.get("labeling", "graph_main", "ldaRequirementMsg"),
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
        # uncheck button, to allow re-click
        self.ldaGraphRefitBtn.setChecked(False)
    
    def convertLDAItem(self, graphDict):
        """
            description: convert graphItem to scatterItem for LDA graph plotting
            author: GaEun Hwang (2025.12.05)
        """
        scatterItems = []
        for graphGroup in graphDict.values():
            color = graphGroup['color']
            for key, graphInfo in graphGroup["coordinates"].items():
                xCoord, yCoord = key[0], key[1]
                # coordTips is pixel coordinates.
                coordTips = [f"({yCoord}, {xCoord})"]
                modelOutHsiSpectral = self.visualizerLDA.transformSpectralData(graphInfo["data"])
                scatterItem = self.visualizerLDA.makePlotItem(modelOutHsiSpectral, pen=pg.mkPen([0, 0, 0]), brush=pg.mkBrush(*color), data=coordTips)
                graphInfo["scatter"] = scatterItem
                scatterItems.append(scatterItem)
        return scatterItems  
    
    def plotLDAGraph(self, ldaData, label, labelList):
        """
            @description : plot lda Graph
            @author : GaEun Hwang (2025.09.04)
            @history :
                2025.12.05 - modify to add existing graph points to LDA graph according to view mode by GaEun Hwang
        """
        # create scatteritem for plotting labeling information for a image on LDA graph
        scatterItems = self.visualizerLDA.makePlotItems(ldaData, label, labelList)
        
        # if point exist in graph_plot_widget, draw point in LDA graph.
        graphItems = self.graph_plot_widget.getPlotItem().listDataItems()
        if len(graphItems) > 0:
            if self.graph_control_dict['graph_view_mode'] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
                # if graph group is hide, convert show
                for graphGroup in self.graphGroupDict.values():
                    if graphGroup["hide"] == False:
                        graphGroup["objects"]["hideBtn"].click()
                selectiveScatterItem = self.convertLDAItem(self.graphGroupDict)
                scatterItems.extend(selectiveScatterItem)
            else:
                # if graph group is hide, convert show
                for graphGroup in self.labelViewGraphGroupDict.values():
                    if graphGroup["hide"] == False:
                        graphGroup["objects"]["hideBtn"].click()
                labelScatterItem = self.convertLDAItem(self.labelViewGraphGroupDict)
                scatterItems.extend(labelScatterItem)

        for scatterItem in scatterItems:
            self.ldaGraphPlotWidget.addItem(scatterItem)
        if self.graph_obj_dict['graph_linedrawing']['obj'].isChecked() or self.graph_obj_dict['graph_check']['obj'].isChecked() or self.graph_obj_dict['graph_eraser']['obj'].isChecked():
            self.ldaGraphPlotWidget.addItem(self.scatterGraphPreview)
        self.ldaGraphPlotWidget.autoRange()
        self.graphStackWidget.setCurrentWidget(self.ldaGraphPlotWidget)

    def statechangeGraphAdvOptionCombobox(self, value):
        """
            @description : change combobox state
            @author : GaEun Hwang (2025.09.04)
            @history :
                2025.12.05 - modify to apply graph filter to existing graph points according to view mode by GaEun Hwang
                Yugyeong Hong(2026.02.25) - Refactor message box with util method and language support
        """
        # only proceed if the current filter mode is different value
        if self.currentFilterMode != value:
            if self.currentFilterMode == self.graphNoneMode and value != self.graphNoneMode:
                self.line_graph_preview.setData()

            # when currentfiltermode is changed LDA to another filtermode, initialize graph and make ldarefitbtn to invisible
            elif self.currentFilterMode == GRAPH_FILTER_LDA and value != GRAPH_FILTER_LDA:
                self.ldaGraphRefitBtn.setVisible(False)
                self.ldaGraphPlotWidget.clear()
                self.graphStackWidget.setCurrentWidget(self.graph_plot_widget)

            if value == self.graphNoneMode:
                # to restore filtered preview graph to original graph
                for graphGroup in self.graphGroupDict.values():
                    for graphInfo in graphGroup["coordinates"].values():
                        originalData = graphInfo["data"]
                        graphInfo["line"].setData(x=graphInfo["line"].xData, y=originalData)

                for graphGroup in self.labelViewGraphGroupDict.values():
                    for graphInfo in graphGroup["coordinates"].values():
                        originalData = graphInfo["data"]
                        graphInfo["line"].setData(x=graphInfo["line"].xData, y=originalData)

                self.line_graph_preview.setData()
                self.currentFilterMode = value

            elif value == GRAPH_FILTER_LDA:
                select_image_number = self.image_control_dict['select_image_number']
                labelList = self.Core_DB_Labeling['image_list'][select_image_number]['label_list']
                label = self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label']
                # check if labelMatrix has at least 3 classes and each class has at least 2 pixels
                if self.checkLdaAvailability(label):
                    # reason why the number of class is more than 3,
                    # the number of discriminant vector is usually the number of classes - 1
                    # if the number of class is less than 3, impossible to plot the graph in 2D
                    raw = self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_raw']
                    self.ldaData, self.ldaScaler, self.ldaModel = self.visualizerLDA.fitModel(raw, label)
                    # if before filtermode is not None, restore original graph
                    self.plotLDAGraph(self.ldaData, label, labelList)
                    self.ldaGraphRefitBtn.setVisible(True)
                    self.currentFilterMode = value

                else:
                    messageBox(mode=MESSAGE_BOX_INFORMATION,
                                title=self.lang.get("main", "messageBox", "msgInformation"),
                                text=self.lang.get("labeling", "graph_main", "ldaRequirementMsg"),
                                buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
                    # turn filtermode back to previous
                    self.graphComboboxSelectAdvOption.setCurrentText(self.currentFilterMode)

            else:
                # when changed filter mode to another filter mode
                # applycurrentgraphfilter function needs updated self.currentfiltermode
                self.currentFilterMode = value
                for graphGroup in self.graphGroupDict.values():
                    for graphInfo in graphGroup["coordinates"].values():
                        originalData = graphInfo["data"]
                        filteredData = self.applyCurrentGraphFilter(originalData)
                        graphInfo["line"].setData(x=graphInfo["line"].xData, y=filteredData)

                for graphGroup in self.labelViewGraphGroupDict.values():
                    for graphInfo in graphGroup["coordinates"].values():
                        originalData = graphInfo["data"]
                        filteredData = self.applyCurrentGraphFilter(originalData)
                        graphInfo["line"].setData(x=graphInfo["line"].xData, y=filteredData)

    def applyCurrentGraphFilter(self, data):
        """
            @description : return filtered data according to current graph filter
            @author : GaEun Hwang (2025.09.04)
        """
        if self.currentFilterMode == GRAPH_FILTER_SAVITZKY_GOLAY:
            return setSavitzkyGolay(data)
        elif self.currentFilterMode == GRAPH_FILTER_GAUSSIAN:
            return setGaussian(data)

        return data
                    
    def select_graph_all(self, ch):
        """그래프 리스트에 존재하는 모든 포인트를 선택하거나 해제하는 함수이다.
            현재는 사용 안함 (202305112119)
            Parameters
                1. ch(bool)
                    - True : 모든 포인트 선택
                    - False : 모든 포인트 선택 해제
        """
        number_list = list(self.graph_point_number_dict.keys())
        for number in number_list:
            point = self.graph_point_number_dict[number]
            # Fixed by improve self.graph_point_dict structure to transform into dictionary type from list.
            legend_index = self.graph_point_dict[point]["graph_number"]
            line = self.graph_point_dict[point]["line"]
            item = self.graph_legend_list.findItems(f"{legend_index}",Qt.MatchExactly)[0]
            if ch:
                if self.graph_point_dict[point]["visible"] == 0:
                    item.setCheckState(Qt.Checked)
                    self.graph_point_dict[point]["visible"] = 1
                    self.graph_plot_widget.addItem(line)
            else:
                if self.graph_point_dict[point]["visible"] == 1:
                    item.setCheckState(Qt.Unchecked)
                    self.graph_point_dict[point]["visible"] = 0
                    self.graph_plot_widget.removeItem(line)
            
        tmp_dict = {}
        tmp_dict['type'] = "all_select"
        tmp_dict['checked'] = ch
        self.graph_to_display(tmp_dict)
                
    def select_graph_delete(self):
        """그래프 리스트 레전드에서 하나의 포인트를 선택 후 삭제버튼을 통해 제거하는 함수이다.
            현재는 사용 안함 (202305112119)
        """
        try:
            if self.graph_legend_list.currentItem().isSelected():
                select_num = int(self.graph_legend_list.currentItem().data(0))
                point = self.graph_point_number_dict[select_num]
                # Fixed by improve self.graph_point_dict structure to transform into dictionary type from list.
                legend_index = self.graph_point_dict[point]["graph_number"]
                line = self.graph_point_dict[point]["line"]
                items = self.graph_legend_list.findItems(f"{legend_index}",Qt.MatchExactly)
                for item in items:
                    row_value = self.graph_legend_list.row(item)
                
                self.graph_plot_widget.removeItem(line)
                self.graph_legend_list.takeItem(row_value)
                del self.graph_point_dict[point]
                del self.graph_point_number_dict[legend_index]

                tmp_dict = {}
                tmp_dict['type'] = "select_delete"
                tmp_dict['number'] = select_num
                self.graph_to_display(tmp_dict)
        except AttributeError:
            print("Select graph point")

    def select_graph_line(self,item=None):
        """그래프 리스트 레전드에서 선택된 포인트에 대한 그래프 라인의 하이라이트를 강조해주는 함수이다.
            현재는 사용 안함 (202305112119)
                Parameters
                1. item(object): 리스트에서 선택된 포인트의 object
        """
        self.graph_legend_buttons_select_delete.setEnabled(True) # 아이템 클릭되어있는 경우 활성화

        print('item clicked!')
        if item.checkState(): # check 되어 있는 경우 하이라이트 라인
            self.update_old_line()
            select_num = int(item.data(0))
            point = self.graph_point_number_dict[select_num]
            # Fixed by improve self.graph_point_dict structure to transform into dictionary type from list.
            line = self.graph_point_dict[point]["line"]
            showed = self.graph_point_dict[point]["visible"]
            color = self.graph_point_dict[point]["random_color"]
            if showed == 0: # 그래프에 그려지지 않은 상태일 경우 다시 그리기
                self.graph_plot_widget.addItem(line)
                self.graph_point_dict[point]["visible"] = 1

                tmp_dict = {}
                tmp_dict['type'] = "checked"
                tmp_dict['number'] = select_num
                self.graph_to_display(tmp_dict)

            if item.isSelected():
                highlight_pen = pg.mkPen(QtGui.QColor(color[0],color[1],color[2]),width=4)
                line.setPen(highlight_pen)
                self.old_line = [line, color]

                
        else: # check 안되어 있으면 라인 없애기
            select_num = int(item.data(0))
            point = self.graph_point_number_dict[select_num]
            # Fixed by improve self.graph_point_dict structure to transform into dictionary type from list.
            line = self.graph_point_dict[point]["line"]
            self.graph_point_dict[point]["visible"] = 0
            self.graph_plot_widget.removeItem(line)
            self.old_line = []
            tmp_dict = {}
            tmp_dict['type'] = "unchecked"
            tmp_dict['number'] = select_num
            self.graph_to_display(tmp_dict)
            
    
    def update_old_line(self):
        """그래프 리스트 레전드에서 이전에 선택된 하이라이팅된 포인터를 다시 원래대로 수정해주는 함수이다.
            현재는 사용 안함 (202305112119)
        """
        if self.old_line:
            old_line, old_color = self.old_line
            original_pen = pg.mkPen(QtGui.QColor(old_color[0],old_color[1],old_color[2]),width=1.5)
            old_line.setPen(original_pen)
            
    def update_graph_list_item(self, txt="", color=[], point=""):
        """그래프 리스트 레전드에 아이템을 추가하기 위한 함수이다.
                Parameters
                1. txt(str): 아이템에 추가할 번호
                2. color(list): 아이템에 추가할 색
        """
        item = QListWidgetItem()
        item.setCheckState(Qt.Checked)
        item.setData(0, txt)
        item.setData(1, QtGui.QColor(color[0],color[1],color[2]))
        item.setData(2, point)
        self.graph_legend_list.addItem(item)

    def update_graph_preview(self):
        """
            Description: graph preview line을 업데이트 하기 위한 기능
            update data - 202305111452
            Development by MyoungHwan
            Modified by MyoungHwan(20240226)

            History: 
                2025.09.04 - change appropriate graph preview item with check current graph widget by GaEun Hwang
                2025.12.05 - modify code because removed "line preview stat list" in graph_control_dict for readability by GaEun Hwang
        """
        previewItemControl = self.graph_control_dict['graph_line_preview']
        if previewItemControl:
            self.graph_plot_widget.addItem(self.line_graph_preview)
            self.ldaGraphPlotWidget.addItem(self.scatterGraphPreview)
        else:
            self.graph_plot_widget.removeItem(self.line_graph_preview)
            self.ldaGraphPlotWidget.removeItem(self.scatterGraphPreview)

    def clear_graph_list(self):
        """
            description: Function to initialize the graph list. All data for the graph is initialized.
                development by MyoungHwan
            History:
                2025.09.04 - clear self.originGraphData and if current graph widget is LDA widget, clear added graph point item by user
                2025.12.05 - modify logic to remove scatter item when current graph widget is LDA graph widget by GaEun Hwang
                2026.04.23 - modify to consider RGB line widget when clear graph list by Hyunsu Kim
        """
        self.graph_plot_widget.clear()
        self.line_graph_preview.clear()

        if self.graphRgb.isChecked():
            self.graph_plot_widget.addItem(self.rgbLinesWidget[SUBRGB_RED])
            self.graph_plot_widget.addItem(self.rgbLinesWidget[SUBRGB_GREEN])
            self.graph_plot_widget.addItem(self.rgbLinesWidget[SUBRGB_BLUE])

        # if currentgraphmode is LDA, don't clear original LDA graph
        # only remove graphs in graph_point_dict
        # Reason: users may want to reset their clicked points while keeping the background LDA scatter visible.
        if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
            for graphInfo in self.graphGroupDict.values():
                for item in graphInfo["coordinates"].values():
                    self.ldaGraphPlotWidget.removeItem(item["scatter"])
            for graphInfo in self.labelViewGraphGroupDict.values():
                for item in graphInfo["coordinates"].values():
                    self.ldaGraphPlotWidget.removeItem(item["scatter"])
            
            self.scatterGraphPreview.setData()

        """
            Description: remove unused function (graph legend listup)
            Modified by MyoungHwan (2024.02.05)
        """
        # self.graph_legend_list.clear()
        for graph in self.graphGroupDict.values():
            graph['coordinates'].clear()
        
        for graph in self.labelViewGraphGroupDict.values():
            graph['coordinates'].clear()

        self.graph_control_dict['graph_line_preview'] = self.graph_obj_dict['graph_linedrawing']['obj'].isChecked()

        if self.graph_control_dict['graph_line_preview']:
            self.graph_plot_widget.addItem(self.line_graph_preview)

    def clearLDAGraph(self):
        """
            @description : clear LDA graph plot and repair default graph setting
            @author : GaEun Hwang (2025.09.04)
        """
        self.ldaGraphPlotWidget.clear()
        self.graphStackWidget.setCurrentWidget(self.graph_plot_widget)
        self.graphComboboxSelectAdvOption.setCurrentText(self.graphNoneMode)
        self.ldaGraphRefitBtn.setVisible(False)
    
    def drawGraph(self, point, spectralData, color, selectiveGraphIdx, labelClass):
        """
            description: draw graph line according to current graph view mode
            author: GaEun Hwang (2025.12.05)
        """
        point_y, point_x = point[0], point[1]
        filteredSpectralData = self.applyCurrentGraphFilter(spectralData)

        selectiveColor, labelColor = color[0], color[1]
        # reason to determine current color is line color is selected according to current view mode 
        if self.graph_control_dict["graph_view_mode"] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
            currentColor = selectiveColor
        else:
            currentColor = labelColor
        lineItem = pg.PlotCurveItem()
        lineItem.setPen(pg.mkPen(QtGui.QColor(currentColor[0],currentColor[1],currentColor[2]),width=1.5))
        lineItem.setData(self.hsi_metadata['wavelength'], filteredSpectralData)

        # store line item in both graph group dicts for easier access later
        # line graph in label view dict color will changed when convert view mode
        self.graphGroupDict[selectiveGraphIdx]["coordinates"][point]["line"] = lineItem
        self.labelViewGraphGroupDict[labelClass]["coordinates"][point]["line"] = lineItem

        self.graph_plot_widget.addItem(lineItem)
        if self.graph_control_dict["graph_view_mode"] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
            if self.graphGroupDict[selectiveGraphIdx]['hide'] == False:
                lineItem.setVisible(False)
        else:
            if self.labelViewGraphGroupDict[labelClass]['hide'] == False:
                lineItem.setVisible(False)

        # when current graph widget is LDA graph widget, draw scatter item
        # scatter item is stored in each graph group dict according to view mode
        if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
            modelOutTmpHsiSpectral = self.visualizerLDA.transformSpectralData(spectralData)
            coordTips = [f"({point_x}, {point_y})"]
            scatterItem = self.visualizerLDA.makePlotItem(
                modelOutTmpHsiSpectral, hoverable=True, data=coordTips,
                pen=pg.mkPen(0,0,0), brush=pg.mkBrush(currentColor[0],currentColor[1],currentColor[2]))
            
            self.ldaGraphPlotWidget.addItem(scatterItem)
            if self.graph_control_dict['graph_view_mode'] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
                if self.graphGroupDict[selectiveGraphIdx]['hide'] == False:
                    scatterItem.setVisible(False)
            else:
                if self.labelViewGraphGroupDict[labelClass]['hide'] == False:
                    scatterItem.setVisible(False)
            if self.graph_control_dict["graph_view_mode"] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
                self.graphGroupDict[selectiveGraphIdx]["coordinates"][point]["scatter"] = scatterItem
            else:
                self.labelViewGraphGroupDict[labelClass]["coordinates"][point]["scatter"] = scatterItem

    def removeGraphGroup(self, index:int, labelClass=False, removedLabelItem=None):
        """
            description: remove graph group according to current graph view mode
            author: GaEun Hwang (2025.12.05)
        """
        if labelClass and removedLabelItem is not None:
            removedLabelLineItem = [item["line"] for item in removedLabelItem["coordinates"].values()]
            color = self.labelViewGraphGroupDict[0]['color']
            for lineItem in removedLabelLineItem:
                lineItem.setPen(pg.mkPen(QtGui.QColor(color[0],color[1],color[2]),width=1.5))
            # when current graph widget is LDA graph widget, not remove each scatter item do refitLDA
            if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                self.refitLdaGraph()
        else:
            items = [item["line"] for item in self.graphGroupDict[index]["coordinates"].values()]
            for item in items:
                self.graph_plot_widget.removeItem(item)
            del self.graphGroupDict[index]

            if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                self.refitLdaGraph()
    
    def removeGraph(self, selectiveIndex, labelIndex, point):
        """
            description: remove each graph according to current graph view mode
            author: GaEun Hwang (2025.12.05)
        """
        item = self.graphGroupDict[selectiveIndex]["coordinates"][point]["line"]
        self.graph_plot_widget.removeItem(item)
        item = self.labelViewGraphGroupDict[labelIndex]["coordinates"][point]["line"]
        self.graph_plot_widget.removeItem(item)

        if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
            if self.graph_control_dict["graph_view_mode"] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
                scatterItem = self.graphGroupDict[selectiveIndex]["coordinates"][point]["scatter"]
            else:
                scatterItem = self.labelViewGraphGroupDict[labelIndex]["coordinates"][point]["scatter"]
            self.ldaGraphPlotWidget.removeItem(scatterItem)

    def hideGraph(self, hideState:bool, index:int, partial:bool=True, labelView:bool=False):
        """
            description: hide graph group or all graph group according to current graph view mode
            author: GaEun Hwang (2025.12.05)
        """
        if partial == True:
            items = []
            if labelView == False:
                if self.graphStackWidget.currentWidget() == self.graph_plot_widget:
                    for item in self.graphGroupDict[index]["coordinates"].values():
                        items.append(item["line"])
                elif self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                    for item in self.graphGroupDict[index]["coordinates"].values():
                        items.append(item["scatter"])
            else:
                if self.graphStackWidget.currentWidget() == self.graph_plot_widget:
                    for item in self.labelViewGraphGroupDict[index]["coordinates"].values():
                        items.append(item["line"])
                elif self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                    for item in self.labelViewGraphGroupDict[index]["coordinates"].values():
                        items.append(item["scatter"])
        else:
            items = []
            if labelView == False:
                for graphGroup in self.graphGroupDict.values():
                    for item in graphGroup["coordinates"].values():
                        items.append(item["line"])

                if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                    for graphGroup in self.graphGroupDict.values():
                        for item in graphGroup["coordinates"].values():
                            items.append(item["scatter"])
            else:
                for graphGroup in self.labelViewGraphGroupDict.values():
                    for item in graphGroup["coordinates"].values():
                        items.append(item["line"])
                if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                    for graphGroup in self.labelViewGraphGroupDict.values():
                        for item in graphGroup["coordinates"].values():
                            items.append(item["scatter"])

        for item in items:
            item.setVisible(hideState)
    
    def changeGraphGroupColor(self, color, index:int, label=False):
        """
            description: change graph group color according to current graph view mode
            author: GaEun Hwang (2025.12.05)
        """
        lineItems = []
        scatterItems = []
        if self.graph_control_dict["graph_view_mode"] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
            if label == False:
                for item in self.graphGroupDict[index]["coordinates"].values():
                    lineItems.append(item["line"])
                    scatterItems.append(item["scatter"])
        else:
            for item in self.labelViewGraphGroupDict[index]["coordinates"].values():
                lineItems.append(item["line"])
                scatterItems.append(item["scatter"])

        for lineItem in lineItems:
            lineItem.setPen(pg.mkPen(color, width=1.5))

        if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
            # (label == True) -> label class color change
            if label == True:
                self.refitLdaGraph()
            else:
                for scatterItem in scatterItems:
                    scatterItem.setBrush(pg.mkBrush(color))

    def convertGraphView(self, viewMode):
        """
            description: convert graph view mode
            author: GaEun Hwang (2025.12.05)
        """
        if viewMode == GRAPH_GROUP_CONVERT_LABEL_VIEW:
            for graphGroup in self.labelViewGraphGroupDict.values():
                color = graphGroup['color']
                for item in graphGroup["coordinates"].values():
                    item["line"].setPen(pg.mkPen(*color), width=1.5)

            # scatter is different object between labelViewGraphGroupDict and graphGroupDict
            # reason: LDAmodel, Scaler is need to transform coordinates to plot LDA Graph. but those are created when fitmodel function is called.
            # so refit LDA graph is needed to remove previous scatter items and create new scatter items according to current view mode's graph group dict.
            if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                self.refitLdaGraph()

        elif viewMode == GRAPH_GROUP_CONVERT_SELECTIVE_VIEW:
            for graphGroup in self.graphGroupDict.values():
                color = graphGroup['color']
                for item in graphGroup["coordinates"].values():
                    item["line"].setPen(pg.mkPen(*color), width=1.5)

            if self.graphStackWidget.currentWidget() == self.ldaGraphPlotWidget:
                self.refitLdaGraph()

    def graph_mode(self,ch=None ,mode=0):
        """
            descripton: function for using the graph function. When the button is clicked, Core_DB is updated and the value is passed to the display.
            development by MyoungHwan
                Parameters
                1.  ch(bool)
                    - True : enable select
                    - False : disable select
                2.  mode(int)
                    - GRAPH_DISPLAY_PREVIEW(2) : graph preview display on/off
                    - GRAPH_DISPLAY_SUB_FORM(3) : graph sub form display on/off
                    - GRAPH_SETTING(4) : graph setting display on/off
                    - GRAPH_DRAW(5) : graph draw mode, if ch is True, draw on graph
                    - GRAPH_ERASE(6) : graph erase mode, if ch is True, erase on graph
                    - GRAPH_CLEAR(7) : graph clear mode, click to clear graph on plot widget
            History:
                2025.12.05 - modify code for graph group and readability by GaEun Hwang
                2026.04.23 - Add code for RGB line display mode by Hyunsu Kim
        """
        if self.graph_control_dict['graph_control_sw']:
            # print(f"graph mode {ch}, {mode}")
            emitDict = {}
            if mode == GRAPH_DRAW:
                #draw mode
                if self.graph_obj_dict['graph_eraser']['obj'].isChecked(): 
                    self.graph_obj_dict['graph_eraser']['obj'].toggle()
                if ch:
                    type_detail = "draw"
                    emitDict['mode'] = GRAPH_CHECK_ON
                else:
                    type_detail = "None"
                    emitDict['mode'] = GRAPH_CHECK_OFF
                self.graphToGraphGroupSignal.emit(emitDict)
                self.update_graph_preview()
                    
            elif mode == GRAPH_ERASE:
                if self.graph_obj_dict['graph_check']['obj'].isChecked():
                    self.graph_obj_dict['graph_check']['obj'].toggle()
                #erase mode
                if ch:
                    type_detail = "erase"
                    emitDict['mode'] = GRAPH_ERASE_ON
                else:
                    type_detail = "None"
                    emitDict['mode'] = GRAPH_ERASE_OFF
                self.graphToGraphGroupSignal.emit(emitDict)
                self.update_graph_preview()

            elif mode == GRAPH_RGB:
                # Add RGB line widgets when activated else remove
                if ch:
                    type_detail = "showRgbLines"
                    self.graph_plot_widget.addItem(self.rgbLinesWidget[SUBRGB_RED])
                    self.graph_plot_widget.addItem(self.rgbLinesWidget[SUBRGB_GREEN])
                    self.graph_plot_widget.addItem(self.rgbLinesWidget[SUBRGB_BLUE])
                    tmp_dict = {}
                    tmp_dict['mode'] = 'graph'
                    tmp_dict['type'] = "showRgbLines"
                    self.graphToDisplaySubRgbChangeSignal.emit(tmp_dict)
                else:
                    type_detail = "hideRgbLines"
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_RED])
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_GREEN])
                    self.graph_plot_widget.removeItem(self.rgbLinesWidget[SUBRGB_BLUE])
                    tmp_dict = {}
                    tmp_dict['mode'] = 'graph'
                    tmp_dict['type'] = "hideRgbLines"
                    self.graphToDisplaySubRgbChangeSignal.emit(tmp_dict)

            elif mode == GRAPH_CLEAR:
                #all clear mode
                type_detail = "clear"
                self.clear_graph_list()

            elif mode == GRAPH_DISPLAY_PREVIEW:
                #hide
                self.graph_control_dict['graph_line_preview'] = self.graph_obj_dict['graph_linedrawing']['obj'].isChecked()
                if ch:# test mode
                    type_detail = "show_preview_linedrawing"
                else: # show mode
                    type_detail = "hide_preview_linedrawing"
                self.update_graph_preview()

            elif mode == GRAPH_DISPLAY_SUB_FORM:
                type_detail = "graph_sub_form"
                if ch:
                    self.graph_sub_form.show()
                else:
                    self.graph_sub_form.close()

            tmp_dict = {}
            tmp_dict['type'] = type_detail
            self.graph_to_display(tmp_dict)

    def mousePressEvent(self, e):
        """마우스 클릭시 활성화 되는 함수이다.
            현재는 사용 안함 (202305112119)
            그래프 리스트 레전드에서 특정 아이템이 선택되어 있는 경우 해재
        """
        if e.button() == QtCore.Qt.LeftButton:
            try:
                if self.graph_legend_list.currentItem().isSelected():
                    self.graph_legend_list.currentItem().setSelected(False)
                    self.graph_legend_buttons_select_delete.setEnabled(False)
                    self.update_old_line()
            except:
                pass
        elif e.button() == QtCore.Qt.MouseButton.RightButton:
            self.graphMenu.exec_(e.globalPos())


    def graph_to_core(self, input):
        """graph에서 core로 시그널을 보내기 위한 함수 선언문이다. Core DB에 대한 값을 업데이트하거나 조정하기 위한 함수로 쓰인다.
                Parameters
                1.	input(dict): Core DB업데이트를 위한 dictionary
        """
        self.graph_to_core_signal.emit(input)

    def graph_to_display(self, input):
        """graph에서 display로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 display에 최종적으로 전달된다.
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary

        """
        self.graph_to_display_signal.emit(input)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Graph_Form()
    # ui.setupUi(Form)
    # Form.show()
    sys.exit(app.exec_())
