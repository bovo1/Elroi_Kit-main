"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets

from .graph_export import graphExportForm

class graphOptionForm(QtWidgets.QMenu):
    """
        @description : graph option menu for graph plot settings and export options
        @author : GaEun Hwang (2026.04.10)
    """
    def __init__(self, Sync=None, lang=None, parent=None) -> None:
        super().__init__(parent)

        self.init(Sync=Sync, lang=lang)
        self.initUi()
        self.setupUi()
        self.setLanguage()
        self.setFunction()
    
    def init(self, Sync=None, lang=None):
        """
            @description : initialize graph option menu properties
            @author : GaEun Hwang (2026.04.10)
        """
        self.lang = lang
        self.Sync = Sync

        self.graphOptionToGraphSignal = self.Sync.graphOptionToGraphSignal
        self.graphExportForm = graphExportForm(Sync=self.Sync, lang=self.lang, parent=self.parent())

    def initUi(self):
        """
            @description : initialize UI components for graph option menu
            @author : GaEun Hwang (2026.04.10)
        """
        self.setObjectName("graph_option_form")
        
        # graph options
        self.graphPlotSettingDefaultViewAction = QtWidgets.QAction("Default View")
        self.graphPlotSettingOptionGrid = QtWidgets.QMenu("Grid", self)

        self.graphPlotSettingOptionGridWidgetAction = QtWidgets.QWidgetAction(self.graphPlotSettingOptionGrid)
        self.graphPlotSettingExport = QtWidgets.QAction("Export")

        self.gridOptionWidget = QtWidgets.QWidget()
        self.gridOptionFormLayout = QtWidgets.QFormLayout()
        
        self.xGridCheckBox = QtWidgets.QCheckBox()
        self.xGridCheckBox.setCheckable(True)
        self.xGridLabel = QtWidgets.QLabel("X Axis")
        
        self.yGridCheckBox = QtWidgets.QCheckBox()
        self.yGridCheckBox.setCheckable(True)
        self.yGridLabel = QtWidgets.QLabel("Y Axis")
        
        self.gridOpacityHlayout = QtWidgets.QHBoxLayout()
        self.gridOpacityLabel = QtWidgets.QLabel("Opacity")
        self.gridOpacitySlider = QtWidgets.QSlider(Qt.Horizontal)
        self.gridOpacityValueLabel = QtWidgets.QLabel("")

    def setLanguage(self):
        """
            @description : set language for graph option menu UI components
            @author : GaEun Hwang (2026.04.10)
        """
        self.lang.set("labeling", "graphOption", "graphOptionDefaultView", self.graphPlotSettingDefaultViewAction)
        self.lang.set("labeling", "graphOption", "graphOptionGrid", self.graphPlotSettingOptionGrid)
        self.lang.set("labeling", "graphOption", "graphOptionGridX", self.xGridLabel)
        self.lang.set("labeling", "graphOption", "graphOptionGridY", self.yGridLabel)
        self.lang.set("labeling", "graphOption", "graphOptionGridOpacity", self.gridOpacityLabel)
        self.lang.set("labeling", "graphOption", "graphOptionExport", self.graphPlotSettingExport)
        
    def setupUi(self):
        """
            @description : setup UI components for graph option menu and add actions to menu
            @author : GaEun Hwang (2026.04.10)
        """
        self.graphPlotSettingOptionGridWidgetAction.setDefaultWidget(self.gridOptionWidget)
        self.addAction(self.graphPlotSettingDefaultViewAction)
        self.addMenu(self.graphPlotSettingOptionGrid)
        
        self.gridOptionFormLayout.addRow(self.xGridLabel, self.xGridCheckBox)
        self.gridOptionFormLayout.addRow(self.yGridLabel, self.yGridCheckBox)
        
        self.gridOpacitySlider.setRange(0, 100)
        self.gridOpacitySlider.setValue(70)
        self.gridOpacityValueLabel.setText(f"{self.gridOpacitySlider.value()}%")
        self.gridOpacityHlayout.addWidget(self.gridOpacitySlider)
        self.gridOpacityHlayout.addWidget(self.gridOpacityValueLabel)
        self.gridOptionFormLayout.addRow(self.gridOpacityLabel, self.gridOpacityHlayout)

        self.gridOptionWidget.setLayout(self.gridOptionFormLayout)
        self.graphPlotSettingOptionGrid.addAction(self.graphPlotSettingOptionGridWidgetAction)
        self.addAction(self.graphPlotSettingExport)
    
    def setFunction(self):
        """
            @description : set functions for UI interactions in graph option menu
            @author : GaEun Hwang (2026.04.10)
        """
        self.graphPlotSettingDefaultViewAction.triggered.connect(lambda : self.graphOptionToGraphSignal.emit({"DefaultView": {}}))
        self.xGridCheckBox.stateChanged.connect(lambda state: self.graphOptionToGraphSignal.emit({"Grid": {"axis": "x", "state": state}}))
        self.yGridCheckBox.stateChanged.connect(lambda state: self.graphOptionToGraphSignal.emit({"Grid": {"axis": "y", "state": state}}))
        self.gridOpacitySlider.valueChanged.connect(self.changeGridOpacity)
        self.graphPlotSettingExport.triggered.connect(self.showExportForm)

    def changeGridOpacity(self):
        """
            @description : emit signal to graph to change grid opacity using slider value and update opacity value label
            @author : GaEun Hwang (2026.04.10)
        """
        self.graphOptionToGraphSignal.emit({"Grid": {"opacity": self.gridOpacitySlider.value()}})
        self.gridOpacityValueLabel.setText(f"{self.gridOpacitySlider.value()}%")

    def showExportForm(self):
        """
            @description : show export form and send current plot widget
            @author : GaEun Hwang (2026.04.10)
        """
        exportPlotWidget = self.parent().graphStackWidget.currentWidget()
        self.graphExportForm.show_(exportPlotWidget)