"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
from constants.constants import PIXEL_BASED_LABELING_DEFAULT_WIDTH, PIXEL_BASED_LABELING_SELECTED_WIDTH, PIXEL_BASED_LABELING_BRUSH_COLOR, PIXEL_BASED_LABELING_PEN_COLOR, HISTOGRAM_BAR_BRUSH_COLOR, HISTOGRAM_BAR_PEN_COLOR


class SimilarityMapWindow(QtWidgets.QWidget):
    """
        Description: Similarity Map Histogram Window for Pixel Based Labeling
          - Shows histogram of similarity values
          - InfiniteLine for threshold selection
          - Similarity mode selector
          - Apply button to apply labeling with current threshold
        Author: Hyunsu Kim (2026.05.19)
    """

    def __init__(self, Sync, lang, pixelBasedLabelingDict, parent=None):
        super().__init__()
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)
        self.lang = lang
        self.Sync = Sync
        self.pixelBasedLabelingDict = pixelBasedLabelingDict
        self.parent = parent
        self.similarityModes = ["SAM", "Chebyshev", "GLE", "Cosine", "L2", "Area", "Canberra", "Jeffrey"]
        self.similarityMap = None
        self.histogramYMax = None

        self.similarityToCoreSignal = self.Sync.similarityToCoreSignal
        self.signalBlocked = False
        self.redrawBlocked = False

        self.initUi()
        self.setupUi()
        self.initFunction()

    def initUi(self):
        """
          description : Initialize UI elements and layout for similarity map window
          author : Hyunsu Kim (2026.05.19)
        """
        self.setObjectName("SimilarityMapWindow")
        self.setWindowTitle(self.lang.get("labeling", "penSubSimilarityMap", "windowTitle"))
        self.lang.set("labeling", "penSubSimilarityMap", "windowTitle", self)
        self.setFixedSize(600, 430)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(8, 8, 8, 8)
        self.mainLayout.setSpacing(8)

        # Histogram plot
        self.plotWidget = pg.PlotWidget()
        self.plotWidget.setObjectName("similarityHistogramPlot")
        self.plotWidget.setBackground((83, 83, 83))
        self.plotWidget.setLabel('bottom', self.lang.get("labeling", "penSubSimilarityMap", "xAxisLabel"))
        self.plotWidget.setLabel('left', self.lang.get("labeling", "penSubSimilarityMap", "yAxisLabel"))
        self.plotWidget.getPlotItem().getViewBox().setLimits(yMin=0, xMin=0, xMax=105)
        self.histogramLegend = self.plotWidget.getPlotItem().addLegend(offset=(-10, 10), labelTextColor=pg.mkColor("w"))
        self.histogramLegend.mouseDragEvent = lambda ev: None 

        # Threshold InfiniteLine
        threshold = self.pixelBasedLabelingDict['threshold']
        self.thresholdLine = pg.InfiniteLine(
            pos=threshold,
            angle=90,
            pen=pg.mkPen('r', width=PIXEL_BASED_LABELING_DEFAULT_WIDTH),
            hoverPen=pg.mkPen('r', width=PIXEL_BASED_LABELING_SELECTED_WIDTH),
            movable=True,
            label=self.lang.get("labeling", "penSubSimilarityMap", "thresholdLineLabel") + "={value:.2f}",
            bounds=(0, 100)
        )
        self.thresholdLine.setZValue(10)
        self.plotWidget.addItem(self.thresholdLine)

        self.histogramGroupBox = QtWidgets.QGroupBox()
        self.histogramGroupBox.setObjectName("similarityHistogramGroupBox")
        self.histogramGroupBox.setTitle(self.lang.get("labeling", "penSubSimilarityMap", "similarityHistogramGroupBox"))
        self.lang.set("labeling", "penSubSimilarityMap", "similarityHistogramGroupBox", self.histogramGroupBox)

        self.histogramGroupLayout = QtWidgets.QVBoxLayout()
        self.histogramGroupLayout.setContentsMargins(4, 4, 4, 4)

        self.parametersGroupBox = QtWidgets.QGroupBox()
        self.parametersGroupBox.setObjectName("parametersGroupBox")
        self.parametersGroupBox.setTitle(self.lang.get("labeling", "penSubSimilarityMap", "parametersGroupBox"))
        self.lang.set("labeling", "penSubSimilarityMap", "parametersGroupBox", self.parametersGroupBox)

        self.parametersLayout = QtWidgets.QHBoxLayout()
        self.parametersLayout.setContentsMargins(8, 8, 8, 8)
        self.parametersLayout.setSpacing(12)

        # Similarity mode selector
        self.modeLabel = QtWidgets.QLabel(self.lang.get("labeling", "penSubSimilarityMap", "modeLabel"))
        self.lang.set("labeling", "penSubSimilarityMap", "modeLabel", self.modeLabel)
        self.similarityModeCombobox = QtWidgets.QComboBox()
        self.similarityModeCombobox.setObjectName("similarityModeCombo")
        self.similarityModeCombobox.addItems(self.similarityModes)
        self.similarityModeCombobox.setFixedWidth(90)

        currentMode = self.pixelBasedLabelingDict['similarityMode']
        idx = self.similarityModeCombobox.findText(currentMode)
        if idx >= 0:
            self.similarityModeCombobox.setCurrentIndex(idx)

        # Threshold control
        self.thresholdLabel = QtWidgets.QLabel(self.lang.get("labeling", "penSubSimilarityMap", "thresholdLabel"))
        self.lang.set("labeling", "penSubSimilarityMap", "thresholdLabel", self.thresholdLabel)
        self.thresholdSpinBox = QtWidgets.QDoubleSpinBox()
        self.thresholdSpinBox.setObjectName("similarityThresholdSpinBox")
        self.thresholdSpinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.thresholdSpinBox.setRange(0.00, 100.00)
        self.thresholdSpinBox.setDecimals(2)
        self.thresholdSpinBox.setSingleStep(0.01)
        self.thresholdSpinBox.setFixedWidth(80)
        self.thresholdSpinBox.setValue(threshold)
        self.thresholdSpinBox.setAlignment(Qt.AlignCenter)

        # Current label + Apply
        self.applyButton = QtWidgets.QPushButton(self.lang.get("labeling", "penSubSimilarityMap", "applyButton"))
        self.applyButton.setObjectName("similarityApplyButton")
        self.lang.set("labeling", "penSubSimilarityMap", "applyButton", self.applyButton)
        self.applyButton.setFixedWidth(80)

        self.resetButton = QtWidgets.QPushButton(self.lang.get("labeling", "penSubSimilarityMap", "resetButton"))
        self.resetButton.setObjectName("similarityDefaultButton")
        self.lang.set("labeling", "penSubSimilarityMap", "resetButton", self.resetButton)
        self.resetButton.setFixedWidth(80)

    def setupUi(self):
        """
          description : Set up the layout of UI elements in the similarity map window
          author : Hyunsu Kim (2026.05.19)
        """
        self.histogramGroupLayout.addWidget(self.plotWidget)
        self.histogramGroupBox.setLayout(self.histogramGroupLayout)
        self.mainLayout.addWidget(self.histogramGroupBox)

        self.parametersLayout.addWidget(self.modeLabel)
        self.parametersLayout.addWidget(self.similarityModeCombobox)
        self.parametersLayout.addStretch()
        self.parametersLayout.addWidget(self.thresholdLabel)
        self.parametersLayout.addWidget(self.thresholdSpinBox)
        self.parametersLayout.addStretch()
        self.parametersLayout.addWidget(self.resetButton)
        self.parametersLayout.addStretch()
        self.parametersLayout.addWidget(self.applyButton)

        self.parametersGroupBox.setLayout(self.parametersLayout)
        self.mainLayout.addWidget(self.parametersGroupBox)

    def initFunction(self):
        """
          description : Initialize function connections for UI elements in the similarity map window
          author : Hyunsu Kim (2026.05.19)
        """
        self.thresholdLine.sigPositionChanged.connect(self.onThresholdLineChanged)
        self.thresholdSpinBox.valueChanged.connect(self.onThresholdSpinBoxChanged)
        self.similarityModeCombobox.currentTextChanged.connect(self.onModeChanged)
        self.applyButton.clicked.connect(self.onApplyClicked)
        self.plotWidget.getPlotItem().getViewBox().sigXRangeChanged.connect(self.onXRangeChanged)
        self.resetButton.clicked.connect(self.onDefaultClicked)

    def onThresholdLineChanged(self):
        """
            description : Sync threshold value between InfiniteLine and SpinBox, and send threshold change signal to core
            author : Hyunsu Kim (2026.05.19)
        """
        if self.signalBlocked:
            return
        self.signalBlocked = True
        value = self.thresholdLine.value()
        self.thresholdSpinBox.setValue(value)
        self.pixelBasedLabelingDict["threshold"] = value
        self.similarityToCore({'mode': 'thresholdChanged', 'threshold': value})
        self.signalBlocked = False

    def onThresholdSpinBoxChanged(self, value):
        """
            description : Sync threshold value between SpinBox and InfiniteLine, and send threshold change signal to core
            author : Hyunsu Kim (2026.05.19)
            parameters:
                value: The new threshold value from the SpinBox
        """
        if self.signalBlocked:
            return
        self.signalBlocked = True
        self.thresholdLine.setValue(value)
        self.pixelBasedLabelingDict["threshold"] = value
        self.similarityToCore({'mode': 'thresholdChanged', 'threshold': value})
        self.signalBlocked = False

    def onModeChanged(self, mode):
        """
            description : Handle changes in similarity mode and send mode change signal to core
            author : Hyunsu Kim (2026.05.19)
            parameters:
                mode: The new similarity mode selected by the user
        """
        self.pixelBasedLabelingDict["similarityMode"] = mode
        self.similarityToCore({'mode': 'modeChanged', 'similarity_mode': mode})

    def onApplyClicked(self):
        """
            description : Handle Apply button click, sending apply labeling signal to core with current threshold
            author : Hyunsu Kim (2026.05.19)
            history:
                1. Hyunsu Kim(2026.06.04): Modified to activate main window after closing the form when apply button is clicked, for better user experience
        """
        self.similarityToCore({'mode': 'applyLabeling', 'threshold': self.thresholdSpinBox.value()})
        self.close()
        QtCore.QTimer.singleShot(0, self.parent.activateWindow)

    def updateHistogram(self, similarityMap):
        """
            description : Update histogram with new similarity map data and set InfiniteLine initial position to the mean of the similarity map
            author : Hyunsu Kim (2026.05.19)
            parameters:
                similarityMap: 2D numpy array of similarity values (0-100 range)
            History:
                1. Regenerate histogram based on x-axis range when user zooms in/out by Hyunsu Kim (2026.05.22)
                2. Set Y-axis maximum to 10% above the highest histogram bar for better visualization by Hyunsu Kim (2026.06.05)
        """
        self.similarityMap = similarityMap

        values = similarityMap.flatten()
        values = values[~np.isnan(values)]  # exclude labeled pixels (NaN)

        self.histogramValues = values

        xMin, xMax = np.min(values), np.max(values)
        globalY, _ = np.histogram(values, bins=100, range=(xMin, xMax))
        self.histogramYMax = np.max(globalY) * 1.1
        self.plotWidget.getPlotItem().getViewBox().setLimits(yMax=self.histogramYMax)

        # Set threshold to mean of similarity map
        meanValue = np.mean(values)
        self.setThreshold(meanValue)

        self.drawHistogram(xMin, xMax, setRange=True)

    def onXRangeChanged(self, view, xRange):
        """
            description : Redraw histogram with finer bins when user zooms into a specific x-axis range
            author : Hyunsu Kim (2026.05.22)
        """
        if self.redrawBlocked:
            return
        xMin, xMax = xRange
        self.drawHistogram(xMin, xMax)

    def drawHistogram(self, xMin, xMax, setRange=False):
        """
            description : Draw histogram bars for the given x range with 100 bins
            author : Hyunsu Kim (2026.05.22)
            history:
                1. Limit histogram bar heights to 10% above the maximum count for better visualization by Hyunsu Kim (2026.06.05)
        """
        self.redrawBlocked = True # Prevent recursive redraws when adjusting x range
        self.plotWidget.clear()

        if xMax <= xMin:
            self.redrawBlocked = False
            return
        
        self.plotWidget.addItem(self.thresholdLine)
        y, x = np.histogram(self.histogramValues, bins=100, range=(xMin, xMax))
        y = np.minimum(y, self.histogramYMax / 1.1)
        self.histogramLegend.clear()
        self.histogramLegend.addItem(pg.PlotDataItem(pen=pg.mkPen("g"), brush=pg.mkBrush("g")), self.lang.get("labeling", "penSubSimilarityMap", "histogramLegendLabel"))
        self.plotWidget.plot(x, y, stepMode='center', fillLevel=0,
                           fillOutline=True, brush=pg.mkBrush(PIXEL_BASED_LABELING_BRUSH_COLOR),
                           pen=pg.mkPen(PIXEL_BASED_LABELING_PEN_COLOR, width=1))
        if setRange:
            self.plotWidget.setXRange(xMin, xMax + 1, padding=0)
        self.plotWidget.setYRange(0, np.max(y) * 1.1, padding=0)
        self.redrawBlocked = False

    def setThreshold(self, value):
        """
            description : Set threshold line and spinbox position programmatically
            author : Hyunsu Kim (2026.05.19)
            parameters:
                value: The new threshold value to set
        """
        self.signalBlocked = True
        self.thresholdLine.setValue(value)
        self.thresholdSpinBox.setValue(value)
        self.signalBlocked = False
        self.pixelBasedLabelingDict["threshold"] = value
        self.pixelBasedLabelingDict["modeDefaultThreshold"] = value
        self.similarityToCore({'mode': 'thresholdChanged', 'threshold': value})

    def onDefaultClicked(self):
        """
            description : Handle Default button click, resetting threshold to default value for current mode
            author : Hyunsu Kim (2026.05.29)
        """
        defaultThreshold = self.pixelBasedLabelingDict['modeDefaultThreshold']
        self.setThreshold(defaultThreshold)
        self.updateHistogram(self.similarityMap)

    def similarityToCore(self, input):
        """
            description : Send similarity map related signals to core
            author : Hyunsu Kim (2026.05.19)
        """
        self.similarityToCoreSignal.emit(input)

    def closeEvent(self, event):
        self.similarityToCore({'mode': 'windowClosed'})
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        # Sync mode from dict
        currentMode = self.pixelBasedLabelingDict['similarityMode']
        idx = self.similarityModeCombobox.findText(currentMode)
        if idx >= 0:
            self.similarityModeCombobox.setCurrentIndex(idx)
