"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from PyQt5 import QtGui, QtWidgets, QtCore
from pyqtgraph import exporters
from utils.custom_ui import messageBox
from utils.custom_item import customGraphMatplotlibExporter
from constants.constants import MESSAGE_BOX_ERROR, GRAPH_EXPORT_SETTINGS

class graphExportForm(QtWidgets.QDialog):
    """
        @description : graph export setting dialog for customizing export parameters and exporting graph in different formats
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
            @description : initialize graph export form with default and user settings
            @author : GaEun Hwang (2026.04.10)
        """
        self.lang = lang
        self.Sync = Sync

        self.defaultSetting = {
            "width": None,
            "height": None,
            "dpi": GRAPH_EXPORT_SETTINGS["defaultDpi"],
            "backgroundColor": GRAPH_EXPORT_SETTINGS["defaultBackgroundColor"],
            "axisColor": GRAPH_EXPORT_SETTINGS["defaultAxisColor"],
            "gridOpacity": GRAPH_EXPORT_SETTINGS["defaultGridOpacity"],
            "csvPrecision": GRAPH_EXPORT_SETTINGS["defaultCsvPrecision"]
        }

        self.userSetting = {
            "width": None,
            "height": None,
        }
        self.exportPlotWidget = None

    def initUi(self):
        """
            @description : initialize UI components for graph export form
            @author : GaEun Hwang (2026.04.10)
        """
        self.setObjectName("graphExportForm")
        self.setWindowTitle("Graph Export Setting")
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.setWindowFlag(QtCore.Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self.exportVlayout = QtWidgets.QVBoxLayout(self)
        self.exportFormatGroupBox = QtWidgets.QGroupBox("Export Format")
        self.exportFormatHlayout = QtWidgets.QHBoxLayout()
        self.exportFormatGroupBox.setLayout(self.exportFormatHlayout)
        self.exportFormatGroupBox.setFixedHeight(80)
   
        self.exportParameterGroupBox = QtWidgets.QGroupBox("Export Parameter")
        self.exportParameterGroupBox_Hlayout = QtWidgets.QHBoxLayout()
        self.exportParameterGroupBox.setLayout(self.exportParameterGroupBox_Hlayout)
        self.exportParameterStackedWidget = QtWidgets.QStackedWidget()

        self.buttonHlayout = QtWidgets.QHBoxLayout()
        self.copyButton = QtWidgets.QPushButton("Copy")
        self.exportButton = QtWidgets.QPushButton("Export")

        self.setDefaultButtonIcon = QtGui.QIcon()
        self.setDefaultButtonIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_clear_white.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        self.setDefaultButtonIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_clear_disabled.png"), QtGui.QIcon.Mode.Disabled, QtGui.QIcon.State.Off)

    def exportFormatUi(self):
        """
            @description : initialize UI components for export format selection
            @author : GaEun Hwang (2026.04.10)
        """
        self.exportFormatList = QtWidgets.QTreeWidget()
        self.exportFormatList.setHeaderHidden(True)
        self.formatMatplotlib = QtWidgets.QTreeWidgetItem(["Image File"])
        self.formatCsv = QtWidgets.QTreeWidgetItem(["CSV File"])
        self.exportFormatHlayout.addWidget(self.exportFormatList)

        self.exportFormatList.addTopLevelItem(self.formatMatplotlib)
        self.exportFormatList.addTopLevelItem(self.formatCsv)
    
    def matplotlibExportParameterUi(self):
        """
            @description : initialize UI components for matplotlib export parameters
            @author : GaEun Hwang (2026.04.10)
        """
        self.exportMatplotlibParameterWidget = QtWidgets.QWidget()
        self.exportMatplotlibParameterLayout = QtWidgets.QFormLayout()
        
        self.exportMatplotlibWidthLabel = QtWidgets.QLabel("Width")
        self.exportMatplotlibWidthHlayout = QtWidgets.QHBoxLayout()
        self.exportMatplotlibWidthSpinBox = QtWidgets.QSpinBox()
        self.exportMatplotlibWidthSpinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.exportMatplotlibWidthSpinBox.setRange(*GRAPH_EXPORT_SETTINGS["sizeRange"])

        self.exportMatplotlibWidthDefaultBtn = QtWidgets.QPushButton()
        self.exportMatplotlibWidthDefaultBtn.setIcon(self.setDefaultButtonIcon)
        
        self.exportMatplotlibHeightLabel = QtWidgets.QLabel("Height")
        self.exportMatplotlibHeightHlayout = QtWidgets.QHBoxLayout()
        self.exportMatplotlibHeightSpinBox = QtWidgets.QSpinBox()
        self.exportMatplotlibHeightSpinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.exportMatplotlibHeightSpinBox.setRange(*GRAPH_EXPORT_SETTINGS["sizeRange"])
        self.exportMatplotlibHeightDefaultBtn = QtWidgets.QPushButton()
        self.exportMatplotlibHeightDefaultBtn.setIcon(self.setDefaultButtonIcon)
    
        self.exportMatplotlibDpiLabel = QtWidgets.QLabel("DPI")
        self.exportMatplotlibDpiHlayout = QtWidgets.QHBoxLayout()
        self.exportMatplotlibDpiSpinBox = QtWidgets.QSpinBox()
        self.exportMatplotlibDpiSpinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.exportMatplotlibDpiSpinBox.setRange(*GRAPH_EXPORT_SETTINGS["dpiRange"])
        self.exportMatplotlibDpiDefaultBtn = QtWidgets.QPushButton()
        self.exportMatplotlibDpiDefaultBtn.setIcon(self.setDefaultButtonIcon)

        self.exportMatplotlibColorBoxLabel = QtWidgets.QLabel("Background Color")
        self.exportMatplotlibColorBoxHlayout = QtWidgets.QHBoxLayout()
        self.exportMatplotlibColorBox = QtWidgets.QPushButton()
        self.exportMatplotlibColorBox.setStyleSheet(f"background-color: {self.defaultSetting['backgroundColor']};")
        self.exportMatplotlibColorBoxDefaultBtn = QtWidgets.QPushButton()
        self.exportMatplotlibColorBoxDefaultBtn.setIcon(self.setDefaultButtonIcon)

        self.exportMatplotlibAxisColorBoxLabel = QtWidgets.QLabel("Axis Color")
        self.exportMatplotlibAxisColorBoxHlayout = QtWidgets.QHBoxLayout()
        self.exportMatplotlibAxisColorBox = QtWidgets.QPushButton()
        self.exportMatplotlibAxisColorBox.setStyleSheet(f"background-color: {self.defaultSetting['axisColor']};")
        self.exportMatplotlibAxisColorBoxDefaultBtn = QtWidgets.QPushButton()
        self.exportMatplotlibAxisColorBoxDefaultBtn.setIcon(self.setDefaultButtonIcon)

        self.exportMatplotlibGridLayout = QtWidgets.QGridLayout()   
        self.exportMatplotlibXGridLabel = QtWidgets.QLabel("X Grid")
        self.exportMatplotlibXGridCheckBox = QtWidgets.QCheckBox()
        self.exportMatplotlibYGridLabel = QtWidgets.QLabel("Y Grid")
        self.exportMatplotlibYGridCheckBox = QtWidgets.QCheckBox()
        self.exportMatplotlibGridOpacitySlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.exportMatplotlibGridOpacitySlider.setRange(*GRAPH_EXPORT_SETTINGS["gridOpacityRange"])
        self.exportMatplotlibGridOpacitySlider.setValue(self.defaultSetting["gridOpacity"])
        self.exportMatplotlibGridOpacitySlider.setFixedWidth(100)
        self.exportMatplotlibGridOpacitySpinBox = QtWidgets.QSpinBox()
        self.exportMatplotlibGridOpacitySpinBox.setRange(*GRAPH_EXPORT_SETTINGS["gridOpacityRange"])
        self.exportMatplotlibGridOpacitySpinBox.setValue(self.defaultSetting["gridOpacity"])
        self.exportMatplotlibGridOpacitySpinBox.setSuffix("%")
        
        self.exportMatplotlibWidthHlayout.addWidget(self.exportMatplotlibWidthSpinBox)
        self.exportMatplotlibWidthHlayout.addWidget(self.exportMatplotlibWidthDefaultBtn)
        self.exportMatplotlibWidthHlayout.setStretch(0, 1)
        
        self.exportMatplotlibHeightHlayout.addWidget(self.exportMatplotlibHeightSpinBox)
        self.exportMatplotlibHeightHlayout.addWidget(self.exportMatplotlibHeightDefaultBtn)
        self.exportMatplotlibHeightHlayout.setStretch(0, 1)
        
        self.exportMatplotlibDpiHlayout.addWidget(self.exportMatplotlibDpiSpinBox)
        self.exportMatplotlibDpiHlayout.addWidget(self.exportMatplotlibDpiDefaultBtn)
        self.exportMatplotlibDpiHlayout.setStretch(0, 1)
        
        self.exportMatplotlibColorBoxHlayout.addWidget(self.exportMatplotlibColorBox)
        self.exportMatplotlibColorBoxHlayout.addWidget(self.exportMatplotlibColorBoxDefaultBtn)
        self.exportMatplotlibColorBoxHlayout.setStretch(0, 1)

        self.exportMatplotlibAxisColorBoxHlayout.addWidget(self.exportMatplotlibAxisColorBox)
        self.exportMatplotlibAxisColorBoxHlayout.addWidget(self.exportMatplotlibAxisColorBoxDefaultBtn)
        self.exportMatplotlibAxisColorBoxHlayout.setStretch(0, 1)

        self.exportMatplotlibGridLayout.addWidget(self.exportMatplotlibXGridLabel, 0, 0)
        self.exportMatplotlibGridLayout.addWidget(self.exportMatplotlibXGridCheckBox, 0, 1)
        self.exportMatplotlibGridLayout.addWidget(self.exportMatplotlibYGridLabel, 1, 0)
        self.exportMatplotlibGridLayout.addWidget(self.exportMatplotlibYGridCheckBox, 1, 1)
        self.exportMatplotlibGridLayout.addWidget(self.exportMatplotlibGridOpacitySlider, 0, 2, 2, 1)
        self.exportMatplotlibGridLayout.addWidget(self.exportMatplotlibGridOpacitySpinBox, 0, 3, 2, 1)

        self.exportMatplotlibParameterLayout.addRow(self.exportMatplotlibWidthLabel, self.exportMatplotlibWidthHlayout)
        self.exportMatplotlibParameterLayout.addRow(self.exportMatplotlibHeightLabel, self.exportMatplotlibHeightHlayout)
        self.exportMatplotlibParameterLayout.addRow(self.exportMatplotlibDpiLabel, self.exportMatplotlibDpiHlayout)
        self.exportMatplotlibParameterLayout.addRow(self.exportMatplotlibColorBoxLabel, self.exportMatplotlibColorBoxHlayout)
        self.exportMatplotlibParameterLayout.addRow(self.exportMatplotlibAxisColorBoxLabel, self.exportMatplotlibAxisColorBoxHlayout)
        self.exportMatplotlibParameterLayout.addRow(self.exportMatplotlibGridLayout)

        self.exportMatplotlibParameterWidget.setLayout(self.exportMatplotlibParameterLayout)

        return self.exportMatplotlibParameterWidget
    
    def csvExportParameterUi(self):
        """
            @description : initialize UI components for CSV export parameters
            @author : GaEun Hwang (2026.04.10)
        """
        self.exportCsvParameterWidget = QtWidgets.QWidget()
        self.exportCsvParameterLayout = QtWidgets.QFormLayout()
        
        self.exportCsvSeperatorLabel = QtWidgets.QLabel("Separator")
        self.exportCsvSeperatorComboBox = QtWidgets.QComboBox()
        self.exportCsvSeperatorComboBox.addItems(["comma", "tab"])

        # precision is for number of digits, if precision is 6, 1234.56789 will be exported as 1234.56 
        self.exportCsvPrecisionLabel = QtWidgets.QLabel("Precision")
        self.exportCsvPrecisionSpinBox = QtWidgets.QSpinBox()
        self.exportCsvPrecisionSpinBox.setRange(*GRAPH_EXPORT_SETTINGS["csvPrecisionRange"])
        self.exportCsvPrecisionSpinBox.setValue(self.defaultSetting["csvPrecision"])

        self.exportCsvColumnModeLabel = QtWidgets.QLabel("Column Mode")
        self.exportCsvColumnModeComboBox = QtWidgets.QComboBox()
        self.exportCsvColumnModeComboBox.addItems(["(x,y) per plot", "(x,y,y,y) for all plots"])

        self.exportCsvParameterWidget.setLayout(self.exportCsvParameterLayout)
        self.exportCsvParameterLayout.addRow(self.exportCsvSeperatorLabel, self.exportCsvSeperatorComboBox)
        self.exportCsvParameterLayout.addRow(self.exportCsvPrecisionLabel, self.exportCsvPrecisionSpinBox)
        self.exportCsvParameterLayout.addRow(self.exportCsvColumnModeLabel, self.exportCsvColumnModeComboBox)

        return self.exportCsvParameterWidget

    def setupUi(self):
        """
            @description : setup UI components for graph export form
            @author : GaEun Hwang (2026.04.10)
        """
        self.exportFormatUi()
        self.exportParameterStackedWidget.addWidget(self.matplotlibExportParameterUi())
        self.exportParameterStackedWidget.addWidget(self.csvExportParameterUi())

        self.exportParameterGroupBox_Hlayout.addWidget(self.exportParameterStackedWidget)

        self.buttonHlayout.addWidget(self.copyButton)
        self.buttonHlayout.addWidget(self.exportButton)

        self.exportVlayout.addWidget(self.exportFormatGroupBox)
        self.exportVlayout.addWidget(self.exportParameterGroupBox)
        self.exportVlayout.addLayout(self.buttonHlayout)

        self.formatMatplotlib.setSelected(True)
        
        # adjust size of the dialog based on its content and set fixed size to prevent resizing
        self.adjustSize()
        self.setFixedSize(self.size())

    def setLanguage(self):
        """
            @description : set language for UI components in graph export form
            @author : GaEun Hwang (2026.04.10)
        """
        # title and group box, button
        self.lang.set("labeling", "graphExport", "graphExportWindowTitle", self)
        self.lang.set("labeling", "graphExport", "graphExportFormat", self.exportFormatGroupBox)
        self.lang.set("labeling", "graphExport", "graphExportParameter", self.exportParameterGroupBox)
        self.lang.set("labeling", "graphExport", "graphExportCopy", self.copyButton)
        self.lang.set("labeling", "graphExport", "graphExportSave", self.exportButton)
        # matplotlib export parameter
        self.lang.set("labeling", "graphExport", "graphExportParameterWidth", self.exportMatplotlibWidthLabel)
        self.lang.set("labeling", "graphExport", "graphExportParameterSetDefault", self.exportMatplotlibWidthDefaultBtn)
        self.lang.set("labeling", "graphExport", "graphExportParameterHeight", self.exportMatplotlibHeightLabel)
        self.lang.set("labeling", "graphExport", "graphExportParameterSetDefault", self.exportMatplotlibHeightDefaultBtn)
        self.lang.set("labeling", "graphExport", "graphExportParameterDPI", self.exportMatplotlibDpiLabel)
        self.lang.set("labeling", "graphExport", "graphExportParameterSetDefault", self.exportMatplotlibDpiDefaultBtn)
        self.lang.set("labeling", "graphExport", "graphExportParameterBackgroundColor", self.exportMatplotlibColorBoxLabel)
        self.lang.set("labeling", "graphExport", "graphExportParameterSetDefault", self.exportMatplotlibColorBoxDefaultBtn)
        self.lang.set("labeling", "graphExport", "graphExportParameterAxisColor", self.exportMatplotlibAxisColorBoxLabel)
        self.lang.set("labeling", "graphExport", "graphExportParameterSetDefault", self.exportMatplotlibAxisColorBoxDefaultBtn)
        self.lang.set("labeling", "graphExport", "graphExportParameterXAxis", self.exportMatplotlibXGridLabel)
        self.lang.set("labeling", "graphExport", "graphExportParameterYAxis", self.exportMatplotlibYGridLabel)
        # csv export parameter
        self.lang.set("labeling", "graphExport", "graphExportParameterSeperator", self.exportCsvSeperatorLabel)
        self.lang.set("labeling", "graphExport", "graphExportParameterPrecision", self.exportCsvPrecisionLabel)
        self.lang.set("labeling", "graphExport", "graphExportParameterColumnMode", self.exportCsvColumnModeLabel)

    def setFunction(self):
        """
            @description : set functions for UI interactions in graph export form
            @author : GaEun Hwang (2026.04.10)
        """
        self.exportFormatList.itemClicked.connect(self.changeExportFormat)

        self.exportMatplotlibWidthSpinBox.editingFinished.connect(lambda : self.userSetting.update({"width": self.exportMatplotlibWidthSpinBox.value()}))
        self.exportMatplotlibWidthDefaultBtn.clicked.connect(lambda : self.resetToDefaultSetting(self.exportMatplotlibWidthSpinBox))
        
        self.exportMatplotlibHeightSpinBox.editingFinished.connect(lambda : self.userSetting.update({"height": self.exportMatplotlibHeightSpinBox.value()}))
        self.exportMatplotlibHeightDefaultBtn.clicked.connect(lambda : self.resetToDefaultSetting(self.exportMatplotlibHeightSpinBox))
        
        self.exportMatplotlibDpiDefaultBtn.clicked.connect(lambda : self.resetToDefaultSetting(self.exportMatplotlibDpiSpinBox))
        
        self.exportMatplotlibColorBox.clicked.connect(lambda : self.changeColor(self.exportMatplotlibColorBox))
        self.exportMatplotlibColorBoxDefaultBtn.clicked.connect(lambda : self.resetToDefaultSetting(self.exportMatplotlibColorBox))
        
        self.exportMatplotlibAxisColorBox.clicked.connect(lambda : self.changeColor(self.exportMatplotlibAxisColorBox))
        self.exportMatplotlibAxisColorBoxDefaultBtn.clicked.connect(lambda : self.resetToDefaultSetting(self.exportMatplotlibAxisColorBox))

        self.exportMatplotlibGridOpacitySlider.valueChanged.connect(lambda value: self.exportMatplotlibGridOpacitySpinBox.setValue(value))
        self.exportMatplotlibGridOpacitySpinBox.valueChanged.connect(lambda value: self.exportMatplotlibGridOpacitySlider.setValue(value))

        self.copyButton.clicked.connect(lambda: self.exportResult(copy=True))
        self.exportButton.clicked.connect(lambda: self.exportResult(copy=False))

    def show_(self, exportPlotWidget):
        """
            @description : show graph export form with current plot widget and initialize export parameters based on default and user settings
            @author : GaEun Hwang (2026.04.10)
        """
        self.exportPlotWidget = exportPlotWidget
        self.defaultSetting["width"] = str(exportPlotWidget.width())
        self.defaultSetting["height"] = str(exportPlotWidget.height())
    
        defaultSettingBindings = [
            (self.exportMatplotlibWidthSpinBox, "width"),
            (self.exportMatplotlibHeightSpinBox, "height"),
        ]
        for widget, value in defaultSettingBindings:
            if isinstance(widget, QtWidgets.QSpinBox):
                if self.userSetting[value] is None:  # if user setting is not set, use default setting
                    widget.setValue(int(self.defaultSetting[value]))
                else:
                    widget.setValue(int(self.userSetting[value]))
    
        self.show()

    def changeExportFormat(self, item):
        """
            @description : change export parameter UI based on selected export format
            @author : GaEun Hwang (2026.04.10)
        """
        if item == self.formatMatplotlib:
            self.exportParameterStackedWidget.setCurrentWidget(self.exportMatplotlibParameterWidget)
            self.copyButton.setEnabled(True)
        elif item == self.formatCsv:
            self.exportParameterStackedWidget.setCurrentWidget(self.exportCsvParameterWidget)
            self.copyButton.setEnabled(False)
    
    def changeColor(self, item):
        """
            @description : open color dialog and change button background color based on selected color with alpha channel support
            @author : GaEun Hwang (2026.04.10)
        """
        color = QtWidgets.QColorDialog.getColor(options=QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            item.setStyleSheet(f"background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()});")
    
    def resetToDefaultSetting(self, item):
        """
            @description : reset export parameter to default setting based on which default button is clicked
            @author : GaEun Hwang (2026.04.10)
        """
        if item == self.exportMatplotlibWidthSpinBox:
            item.setValue(int(self.defaultSetting["width"]))
            self.userSetting["width"] = None
        elif item == self.exportMatplotlibHeightSpinBox:
            item.setValue(int(self.defaultSetting["height"]))
            self.userSetting["height"] = None
        elif item == self.exportMatplotlibColorBox:
            item.setStyleSheet(f"background-color: {self.defaultSetting['backgroundColor']};")
        elif item == self.exportMatplotlibDpiSpinBox:
            item.setValue(int(self.defaultSetting["dpi"]))
        elif item == self.exportMatplotlibAxisColorBox:
            item.setStyleSheet(f"background-color: {self.defaultSetting['axisColor']};")

    def exportResult(self, copy):
        """
            @description : export graph based on selected format and parameters, if copy is True, copy the result to clipboard instead of saving as file
            @author : GaEun Hwang (2026.04.10)
        """
        if self.exportFormatList.currentItem() == self.formatMatplotlib:
            self.exporter = customGraphMatplotlibExporter(self.exportPlotWidget.getPlotItem(), parent=self)
            self.exporter.matplotlibWindow.setWindowTitle(self.lang.get("labeling", "graphExport", "graphExportWindowTitle"))
            # update exporter parameters based on UI component values
            self.exporter.params.update({
                "width": int(self.exportMatplotlibWidthSpinBox.value()),
                "height": int(self.exportMatplotlibHeightSpinBox.value()),
                "dpi": int(self.exportMatplotlibDpiSpinBox.value()),
                "backgroundColor": self.exportMatplotlibColorBox.palette().button().color(),
                "axisColor": self.exportMatplotlibAxisColorBox.palette().button().color(),
                "xGridEnabled": self.exportMatplotlibXGridCheckBox.isChecked(),
                "yGridEnabled": self.exportMatplotlibYGridCheckBox.isChecked(),
                "gridOpacity": self.exportMatplotlibGridOpacitySpinBox.value(),
            })
            self.exporter.export(copy=copy)

        elif self.exportFormatList.currentItem() == self.formatCsv:
            if self.exportPlotWidget.getPlotItem().listDataItems():
                self.exporter = exporters.CSVExporter(self.exportPlotWidget.getPlotItem())
                self.exporter.parameters()["separator"] = self.exportCsvSeperatorComboBox.currentText()
                self.exporter.parameters()["precision"] = self.exportCsvPrecisionSpinBox.value()
                self.exporter.parameters()["columnMode"] = self.exportCsvColumnModeComboBox.currentText()
                self.exporter.export()
            else:
                messageBox(mode=MESSAGE_BOX_ERROR, title=self.lang.get("labeling", "graphExport", "graphExportErrorTitle"), text=self.lang.get("labeling", "graphExport", "graphExportCsvErrorMessage"))
                return