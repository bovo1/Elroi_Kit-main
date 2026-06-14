import os
import copy
import pyqtgraph
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer
from qtwidgets import AnimatedToggle

from sklearn.metrics import confusion_matrix

from utils.viewer import Display_viewer
from constants.constants import *

class Result_Form(QtWidgets.QWidget):
    def __init__(self, Sync, lang) -> None:
        super().__init__()
        self.lang = lang
        self.init(Sync=Sync)
        self.init_ui(self)
        self.setup_ui()
        self.init_params()
        self.init_function()

        self.plot_updator = QTimer()
        self.plot_updator.setInterval(1000)
        self.plot_updator.timeout.connect(self.update_plot)

        self.is_anomaly_detection = False

    def init(self, Sync=None):
        # Sync
        self.dataset_shared_dict = Sync.dataset_shared_dict
        self.hyperparameter_shared_dict = Sync.hyperparameter_shared_dict
        Sync.result_signal.connect(self.result_signal_receiver)
    
    def init_params(self):
        # reset control ui
        self.is_anomaly_detection = False
        self.change_control_ui(self.is_anomaly_detection)

        self.train_loss = []
        self.val_loss = []
        self.abnormal_avg_f1score = []
        self.image_names = []
        self.origin_images = []
        self.current_pred_image = None
        self.pred_images = []
        self.pred_thresholds = 0.0
        self.label_images = []
        self.abnormal_scores = None
        self.labels = None
        self.best_threshold = 0.0
        self.current_threshold = None
        self.position_indices = None
        self.save_path = None
        self.fpMask = None
        self.fnMask = None
        self.gtMask = None
        self.trainFeatureDistHist = {}
        self.testFeatureDistHist = {}
        # self.cm = None
        
        self.prev_train_loss_length = 0
        self.prev_val_loss_length = 0
        self.prev_abnormal_avg_f1score_length = 0

        self.clearGraph()
        self.OutputImageWidget.initPhoto(QtGui.QPixmap("./ico/labeling/logo/background.jpg"), init=True, dragmode=1)
        self.OutputImageWidget.updateDrag(mode=1)
        self.ThresholdLineEdit.setText("")
        self.ThresholdScoreLabel.setText("")
        self.init_combobox()


    def init_ui(self, Form):
        Form.setObjectName("Result_Form")
        Form.setWindowTitle("Result_Form")
                
        self.FormLayout = QtWidgets.QVBoxLayout(Form)
        self.FormLayout.setObjectName("FormLayout")

        # Use tabs so only one (plot or image) is visible at a time.
        self.OutputMain = QtWidgets.QTabWidget(Form)
        self.OutputMain.setObjectName("OutputMain")
        
        self.OutputPlotMainWidget = QtWidgets.QWidget()
        self.OutputPlotMainWidget.setObjectName("OutputPlotMainWidget")

        self.OutputPlotMainWidgetLayout = QtWidgets.QVBoxLayout(self.OutputPlotMainWidget)
        self.OutputPlotMainWidgetLayout.setObjectName("OutputPlotMainWidgetLayout")

        self.OutputImageMainWidget = QtWidgets.QWidget()
        self.OutputImageMainWidget.setObjectName("OutputImageMainWidget")

        self.OutputImageMainWidgetLayout = QtWidgets.QVBoxLayout(self.OutputImageMainWidget)
        self.OutputImageMainWidgetLayout.setObjectName("OutputImageMainWidgetLayout")

        self.OutputPlotGroupBox = QtWidgets.QGroupBox(self.OutputPlotMainWidget)
        self.OutputPlotGroupBox.setObjectName("OutputPlotGroupBox")

        self.OutputPlotGroupBoxLayout = QtWidgets.QVBoxLayout(self.OutputPlotGroupBox)
        self.OutputPlotGroupBoxLayout.setObjectName("OutputPlotGroupBoxLayout")

        self.OutputImageGroupBox = QtWidgets.QGroupBox(self.OutputImageMainWidget)
        self.OutputImageGroupBox.setObjectName("OutputImageGroupBox")

        self.OutputImageGroupBoxLayout = QtWidgets.QVBoxLayout(self.OutputImageGroupBox)
        self.OutputImageGroupBoxLayout.setObjectName("OutputImageGroupBoxLayout")

        # Result controller - [Image selection controller, Threshold controller]
        self.ResultControlWidget = QtWidgets.QWidget()
        self.ResultControlWidget.setObjectName("ResultControlWidget")

        self.ResultControlLayout = QtWidgets.QHBoxLayout(self.ResultControlWidget)
        self.ResultControlLayout.setObjectName("ResultControlLayout")

        # Image selection controller
        self.ImageSelectorMainWidget = QtWidgets.QWidget()
        self.ImageSelectorMainWidget.setObjectName("ImageSelectorMainWidget")
        self.ResultControlLayout.addWidget(self.ImageSelectorMainWidget)

        self.ImageSelectorMainLayout = QtWidgets.QHBoxLayout(self.ImageSelectorMainWidget)
        self.ImageSelectorMainLayout.setObjectName("ImageSelectorMainLayout")

        self.ImageSelectorComboBox = QtWidgets.QComboBox()
        self.ImageSelectorComboBox.setObjectName("ImageSelectorComboBox")

        # Vertical line (Image selection controller <-> Pred map controller)
        self.ResultControlVerticalLine1 = QtWidgets.QFrame()
        self.ResultControlVerticalLine1.setObjectName("ResultControlVerticalLine1")
        self.ResultControlVerticalLine1.setFrameShape(QtWidgets.QFrame.VLine)
        self.ResultControlVerticalLine1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.ResultControlLayout.addWidget(self.ResultControlVerticalLine1)

        # Pred map controller
        self.PredictionMapLabel = QtWidgets.QLabel()
        self.PredictionMapLabel.setObjectName("PredictionMapLabel")
        self.ResultControlLayout.addWidget(self.PredictionMapLabel)

        self.PredictionMapToggle = AnimatedToggle(
            pulse_checked_color="transparent",
            pulse_unchecked_color="transparent"
        )
        self.PredictionMapToggle.setObjectName("PredictionMapToggle")
        self.PredictionMapToggle.setChecked(True)
        self.ResultControlLayout.addWidget(self.PredictionMapToggle)

        # Vertical line (Pred map controller <-> Error map controller)
        self.ResultControlVerticalLineErr = QtWidgets.QFrame()
        self.ResultControlVerticalLineErr.setObjectName("ResultControlVerticalLineErr")
        self.ResultControlVerticalLineErr.setFrameShape(QtWidgets.QFrame.VLine)
        self.ResultControlVerticalLineErr.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.ResultControlLayout.addWidget(self.ResultControlVerticalLineErr)

        # Error map controller (FP/FN overlay)
        self.FpFnMapLabel = QtWidgets.QLabel()
        self.FpFnMapLabel.setObjectName("FpFnMapLabel")
        self.ResultControlLayout.addWidget(self.FpFnMapLabel)

        self.FpFnMapToggle = AnimatedToggle(
            pulse_checked_color="transparent",
            pulse_unchecked_color="transparent"
        )
        self.FpFnMapToggle.setObjectName("FpFnMapToggle")
        self.FpFnMapToggle.setChecked(False)
        self.ResultControlLayout.addWidget(self.FpFnMapToggle)

        # Vertical line (Pred map controller <-> Threshold controller)
        self.ResultControlVerticalLine2 = QtWidgets.QFrame()
        self.ResultControlVerticalLine2.setObjectName("ResultControlVerticalLine2")
        self.ResultControlVerticalLine2.setFrameShape(QtWidgets.QFrame.VLine)
        self.ResultControlVerticalLine2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.ResultControlLayout.addWidget(self.ResultControlVerticalLine2)

        # Threshold controller
        self.ThresholdMainWidget = QtWidgets.QWidget()
        self.ThresholdMainWidget.setObjectName("ThresholdMainWidget")
        self.ResultControlLayout.addWidget(self.ThresholdMainWidget)

        self.ThresholdMainLayout = QtWidgets.QHBoxLayout(self.ThresholdMainWidget)
        self.ThresholdMainLayout.setObjectName("ThresholdMainLayout")
        
        self.ThresholdLabel = QtWidgets.QLabel()
        self.ThresholdLabel.setObjectName("ThresholdLabel")
        self.ThresholdMainLayout.addWidget(self.ThresholdLabel)
        
        self.ThresholdLineEdit = QtWidgets.QLineEdit()
        self.ThresholdLineEdit.setObjectName("ThresholdLineEdit")
        self.ThresholdMainLayout.addWidget(self.ThresholdLineEdit)

        self.ThresholdButton = QtWidgets.QPushButton()
        self.ThresholdButton.setObjectName("ThresholdButton")
        self.ThresholdMainLayout.addWidget(self.ThresholdButton)

        self.ThresholdScoreLabel = QtWidgets.QLabel()
        self.ThresholdScoreLabel.setObjectName("ThresholdScoreLabel")
        self.ThresholdMainLayout.addWidget(self.ThresholdScoreLabel)

        # Image View
        # self.OutputImageWidget = SelfImageView()
        self.OutputImageWidget = Display_viewer(usescrollbar=False)

        # Plot View
        self.OutputPlotWidget = QtWidgets.QWidget()
        self.OutputPlotGridLayout = QtWidgets.QGridLayout(self.OutputPlotWidget)
        self.OutputPlotGridLayout.setContentsMargins(0, 0, 0, 0)
        self.OutputPlotGridLayout.setHorizontalSpacing(10)
        self.OutputPlotGridLayout.setVerticalSpacing(10)

    def setup_ui(self):
        # Language Settings
        self.lang.set("training", "result_main", "OutputPlotGroupBox", self.OutputPlotGroupBox)
        self.lang.set("training", "result_main", "OutputImageGroupBox", self.OutputImageGroupBox)
        self.lang.set("training", "result_main", "update_result_text", self.update_result_text)
        self.lang.set("training", "result_main", "PredictionMapLabel", self.PredictionMapLabel)
        self.lang.set("training", "result_main", "FpFnMapLabel", self.FpFnMapLabel)
        self.lang.set("training", "result_main", "ThresholdLabel", self.ThresholdLabel)
        self.lang.set("training", "result_main", "ThresholdButton", self.ThresholdButton)

        # ======================= Plot Area =======================
        # Plot View Settings
        """
            @description: Set up the plot area with 4 different plots (Loss, F1-Score, Train Feature Distance Distribution, Test Feature Distance Distribution) arranged in a 2x2 grid layout. Each plot is customized with titles, axis labels, grid lines, legends, and interaction settings to provide a clear and informative visualization of training results.
            @author: Hyunsu Kim (2026.03.10)
            @history:
                - Modified by Hyunsu Kim (2026.03.19): 
                    - Changed from GraphicsLayoutWidget to QGridLayout for smooth graph size adjustment
                    - Set the plotwidget's right-click menu to be available for View all function
                - Modified by Hyunsu Kim (2026.04.24):
                    - Modify the Train, Val legend names of Loss plot for translation in language file
        """
        style = {"color": "w", "font-size": "15px"}
        plotBackground = pyqtgraph.mkColor(83, 83, 83)

        # Loss Plot
        self.LossPlot = pyqtgraph.PlotWidget()
        self.LossPlot.setBackground(plotBackground)
        self.LossPlot.setLabel("left", "Loss", **style)
        self.LossPlot.getAxis("left").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.LossPlot.setLabel("bottom", "Epochs", **style)
        self.LossPlot.getAxis("bottom").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.LossPlot.showGrid(x=True, y=True)
        self.LossPlot.setMenuEnabled(False)
        self.LossPlot.setMouseEnabled(x=False, y=False)
        lossLegend = self.LossPlot.addLegend(labelTextColor=pyqtgraph.mkColor("w"))
        lossLegend.setOffset(1)
        self.TrainLossPlot = self.LossPlot.plot(pen=pyqtgraph.mkPen(pyqtgraph.mkColor(255, 0, 0, 250), width=2), name=self.lang.get("training", "result_main", "LossPlotlegendTrain"))
        self.ValLossPlot = self.LossPlot.plot(pen=pyqtgraph.mkPen(pyqtgraph.mkColor(0, 255, 0, 150), width=2), name=self.lang.get("training", "result_main", "LossPlotlegendVal"))
        self.lang.set("training", "result_main", "LossPlotlegendTrain", self.TrainLossPlot)
        self.lang.set("training", "result_main", "LossPlotlegendVal", self.ValLossPlot)
        
        # Feature Distance Distribution to Center C (DA/PE)
        self.trainFeatureDistPlot = pyqtgraph.PlotWidget()
        self.trainFeatureDistPlot.setBackground(plotBackground)
        self.trainFeatureDistPlot.setLabel("left", "Probability", **style)
        self.trainFeatureDistPlot.getAxis("left").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.trainFeatureDistPlot.setLabel("bottom", "Feature Distance", **style)
        self.trainFeatureDistPlot.getAxis("bottom").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.trainFeatureDistPlot.showGrid(x=True, y=True)
        self.trainFeatureDistPlot.setMenuEnabled(True)
        self.trainFeatureDistPlot.setMouseEnabled(x=False, y=False)
        self.trainFeatureDistPlot.getViewBox().setLimits(yMin=0)
        self.trainFeatureDistPlot.getViewBox().setLimits(xMin=0)
        self.trainFeatureDistPlot.getViewBox().setLimits(yMax=1)
        trainFeatureLegend = self.trainFeatureDistPlot.addLegend(labelTextColor=pyqtgraph.mkColor("w"))
        trainFeatureLegend.setOffset((-10, 10))
        # F1 Plot
        self.F1Plot = pyqtgraph.PlotWidget()
        self.F1Plot.setBackground(plotBackground)
        self.F1Plot.setLabel("left", "F1-Score", **style)
        self.F1Plot.getAxis("left").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.F1Plot.setLabel("bottom", "Epochs", **style)
        self.F1Plot.getAxis("bottom").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.F1Plot.showGrid(x=True, y=True)
        self.F1Plot.setMenuEnabled(False)
        self.F1Plot.setMouseEnabled(x=False, y=False)
        self.ValAvgF1Plot = self.F1Plot.plot(pen=pyqtgraph.mkPen(pyqtgraph.mkColor(255, 255, 255, 255), width=2), name="F1-Score")

        # Feature Distance Distribution to Center C (DA/PE)
        self.testFeatureDistPlot = pyqtgraph.PlotWidget()
        self.testFeatureDistPlot.setBackground(plotBackground)
        self.testFeatureDistPlot.setLabel("left", "Probability", **style)
        self.testFeatureDistPlot.getAxis("left").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.testFeatureDistPlot.setLabel("bottom", "Feature Distance", **style)
        self.testFeatureDistPlot.getAxis("bottom").setTextPen(pyqtgraph.mkPen("w", width=2))
        self.testFeatureDistPlot.showGrid(x=True, y=True)
        self.testFeatureDistPlot.setMenuEnabled(True)
        self.testFeatureDistPlot.setMouseEnabled(x=False, y=False)
        self.testFeatureDistPlot.getViewBox().setLimits(yMin=0)
        self.testFeatureDistPlot.getViewBox().setLimits(xMin=0)
        self.testFeatureDistPlot.getViewBox().setLimits(yMax=1)
        testFeatureLegend = self.testFeatureDistPlot.addLegend(labelTextColor=pyqtgraph.mkColor("w"))
        testFeatureLegend.setOffset((-10, 10))

        self.OutputPlotGridLayout.addWidget(self.LossPlot, 0, 0)
        self.OutputPlotGridLayout.addWidget(self.trainFeatureDistPlot, 0, 1)
        self.OutputPlotGridLayout.addWidget(self.F1Plot, 1, 0)
        self.OutputPlotGridLayout.addWidget(self.testFeatureDistPlot, 1, 1)
        self.OutputPlotGridLayout.setColumnStretch(0, 1)
        self.OutputPlotGridLayout.setColumnStretch(1, 1)
        self.OutputPlotGridLayout.setRowStretch(0, 1)
        self.OutputPlotGridLayout.setRowStretch(1, 1)

        self.OutputPlotGroupBoxLayout.addWidget(self.OutputPlotWidget)
        # ======================= Plot Area =======================
        # Image selector control settings
        self.ImageSelectorMainLayout.addWidget(self.ImageSelectorComboBox)

        # Threshold control settings
        self.ThresholdButton.setFixedWidth(70)
        self.ThresholdLineEdit.setFixedWidth(100)
        self.ThresholdLineEdit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("([0-9]*[.])?[0-9]+([eE][-+]?\d+)?")))
        self.ThresholdMainWidget.setVisible(False)
        self.ResultControlVerticalLine2.setVisible(False)
        
        # ==========================================
        # Add ResultControlWidget
        self.OutputImageGroupBoxLayout.addWidget(self.ResultControlWidget, 0, QtCore.Qt.AlignLeft)
        
        # Horizontal line (ResultControllerWidget <-> OutputImageWidget)
        self.OutputImageGroupBoxHorizontalLine1 = QtWidgets.QFrame()
        self.OutputImageGroupBoxHorizontalLine1.setObjectName("OutputImageGroupBoxHorizontalLine1")
        self.OutputImageGroupBoxHorizontalLine1.setFrameShape(QtWidgets.QFrame.HLine)
        self.OutputImageGroupBoxHorizontalLine1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.OutputImageGroupBoxLayout.addWidget(self.OutputImageGroupBoxHorizontalLine1)
        
        # Add OutputImageWidget
        self.OutputImageGroupBoxLayout.addWidget(self.OutputImageWidget)
        # ==========================================

        self.OutputPlotMainWidgetLayout.addWidget(self.OutputPlotGroupBox)
        self.OutputPlotMainWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.OutputImageMainWidgetLayout.addWidget(self.OutputImageGroupBox)
        self.OutputImageMainWidgetLayout.setContentsMargins(0, 0, 0, 0)

        # Tabs: Plot / Image
        self.OutputMain.addTab(self.OutputPlotMainWidget, "Plot")
        self.OutputMain.addTab(self.OutputImageMainWidget, "Image")
        self.lang.set("training", "result_main", "plotTab", self.OutputMain)
        self.lang.set("training", "result_main", "imageTab", self.OutputMain)
        # Default to Image tab for quick inspection
        self.OutputMain.setCurrentWidget(self.OutputImageMainWidget)
        self.FormLayout.addWidget(self.OutputMain)
    
    def init_function(self):
        self.PredictionMapToggle.clicked.connect(lambda: self.show_selected_image(self.ImageSelectorComboBox.currentIndex(), self.PredictionMapToggle.isChecked(), self.FpFnMapToggle.isChecked(), True))
        self.FpFnMapToggle.clicked.connect(lambda: self.show_selected_image(self.ImageSelectorComboBox.currentIndex(), self.PredictionMapToggle.isChecked(), self.FpFnMapToggle.isChecked(), True))
        self.ThresholdButton.clicked.connect(lambda: self.show_updated_pred_image(self.ImageSelectorComboBox.currentIndex(), float(self.ThresholdLineEdit.text()), self.PredictionMapToggle.isChecked(), self.FpFnMapToggle.isChecked()))
        self.ThresholdLineEdit.editingFinished.connect(self.ThresholdButton.click)
        # Connect multiple callbacks to combobox index change:
        # 1. Update displayed image based on new selection
        # 2. Adjust combobox width to fit content
        self.ImageSelectorComboBox.currentIndexChanged.connect(lambda: (
            self.show_selected_image(self.ImageSelectorComboBox.currentIndex(), self.PredictionMapToggle.isChecked(), self.FpFnMapToggle.isChecked(), True), 
            self.adjust_combo_box_width()
        ))

    def update_result_text(self):
        """
            @history:
                - Modified by Hyunsu Kim (2026.03.19):
                    - Add best threshold information to the titles of feature distance distribution plots
                    - Add the condition to update the feature distance distribution plot title
        """
        self.style = {"color": "w", "font-size": "15px"}
        self.LossPlot.setTitle(self.lang.get("training", "result_main", "LossPlotTitle"), **self.style)
        self.F1Plot.setTitle(self.lang.get("training", "result_main", "F1PlotTitle"), **self.style)

        self.trainFeatureDistPlot.setTitle(self.lang.get("training", "result_main", "trainFeatureDistPlotTitle"), **self.style)
        self.testFeatureDistPlot.setTitle(self.lang.get("training", "result_main", "testFeatureDistPlotTitle"), **self.style)

        if self.trainFeatureDistHist or self.testFeatureDistHist:
            self.clearGraph()
            self.updateDistPlots()
            return

    def update_plot(self):
        if self.train_loss != []:
            if len(self.train_loss) != self.prev_train_loss_length:
                self.prev_train_loss_length = len(self.train_loss)
                self.TrainLossPlot.setData(self.train_loss)
        if self.val_loss != []:
            if len(self.val_loss) != self.prev_val_loss_length:
                self.prev_val_loss_length = len(self.val_loss)
                self.ValLossPlot.setData(self.val_loss)
        if self.abnormal_avg_f1score != []:
            if len(self.abnormal_avg_f1score) != self.prev_abnormal_avg_f1score_length:
                self.prev_abnormal_avg_f1score_length = len(self.abnormal_avg_f1score)
                self.ValAvgF1Plot.setData(self.abnormal_avg_f1score)

    def init_combobox(self):
        self.ImageSelectorComboBox.clear()

    def init_combobox_item_list(self, is_load):
        if not is_load:
            for test_data_path in self.dataset_shared_dict["test"].keys():
                if self.dataset_shared_dict["test"][test_data_path][0] and self.dataset_shared_dict["test"][test_data_path][1] != 0:
                    self.image_names.append(test_data_path.split("\\")[-1] if os.name == "nt" else test_data_path.split("/")[-1])
            self.ImageSelectorComboBox.addItems(self.image_names)
            self.adjust_combo_box_width()

    def init_images_anomaly_detection(self, origin_images):
        for i in range(len(origin_images)):
            self.pred_images.append(self.get_pred_image(i, self.best_threshold))

    def adjust_combo_box_width(self):
        """
        description: Added dynamic width adjustment functionality to automatically resize ImageSelectorComboBox based on its content length
        modified by Chansik Kim 2024.12.16
        """
        font_metrics = self.ImageSelectorComboBox.fontMetrics()
        text_width = 100  # Default minimum width
        if self.ImageSelectorComboBox.count() > 0:
            text_width = max(font_metrics.horizontalAdvance(self.ImageSelectorComboBox.itemText(i)) 
                           for i in range(self.ImageSelectorComboBox.count()))
        
        # Add padding for dropdown arrow and margins
        self.ImageSelectorComboBox.setFixedWidth(text_width + 30)

    def change_control_ui(self, is_anomaly_detection:bool):
        if is_anomaly_detection:
            self.ThresholdMainWidget.setVisible(True)
            self.ResultControlVerticalLine2.setVisible(True)
            self.ResultControlVerticalLineErr.setVisible(True)
            self.FpFnMapLabel.setVisible(True)
            self.FpFnMapToggle.setVisible(True)
            self.FpFnMapToggle.setEnabled(False)
            self.ThresholdLineEdit.setText(f"{self.pred_thresholds:.3f}")
        else:
            self.ThresholdMainWidget.setVisible(False)
            self.ResultControlVerticalLine2.setVisible(False)
            self.ResultControlVerticalLineErr.setVisible(False)
            self.FpFnMapLabel.setVisible(False)
            self.FpFnMapToggle.setVisible(False)

    def changeToggle(self):
        """
            @description : Change the enabled/disabled state of PredictionMapToggle and FpFnMapToggle to ensure only one can be active at a time, 
                            preventing conflicting overlays when viewing images. 
                            If PredictionMapToggle is checked, disable FpFnMapToggle and vice versa. 
                            If neither is checked, enable both toggles for user selection.
            @author : Hyunsu Kim (2026.03.10)
        """
        if self.PredictionMapToggle.isChecked():
            self.FpFnMapToggle.setChecked(False)
            self.FpFnMapToggle.setEnabled(False)
        else:
            self.FpFnMapToggle.setEnabled(True)

        if self.FpFnMapToggle.isChecked():
            self.PredictionMapToggle.setChecked(False)
            self.PredictionMapToggle.setEnabled(False)
        else:
            self.PredictionMapToggle.setEnabled(True)

    def clearGraph(self):
        """
            @description : Clear Feature Distance plots in the graph.
            @author : Hyunsu Kim (2026.03.20)
        """
        self.trainFeatureDistPlot.clear()
        self.testFeatureDistPlot.clear()

    def plotHistStep(self, plotItem, edges, data, pen, name, brush=None):
        """
            @description : Utility function to plot step histogram (for feature distance distribution) with optional fill and legend entry
            @author : Hyunsu Kim (2026.03.10)
            @parameter :
                - plotItem: pyqtgraph PlotItem to plot on
                - edges: array-like, bin edges for the histogram (length N+1 for N bins)
                - data: array-like, probability values for each bin (length N)
                - pen: pyqtgraph pen for the line color/style
                - name: str, legend entry name (if None, no legend entry)
                - brush: pyqtgraph brush for filling under the step curve (if None, no fill)
        """
        # pyqtgraph stepMode=True expects len(x) == len(y) + 1
        if edges.size == data.size:
            # Treat given x as bin centers; synthesize a final edge.
            lastStep = float(edges[-1] - edges[-2]) if edges.size >= 2 else 1.0
            edges = np.r_[edges, edges[-1] + lastStep]
        elif edges.size != data.size + 1:
            return
        
        # Plot the step histogram with optional fill and legend entry
        plotItem.plot(
            edges,
            data,
            stepMode=True,
            fillLevel=0,
            brush=brush,
            pen=pyqtgraph.mkPen(None),
            name=None,
        )
        plotItem.plot(
            edges,
            data,
            stepMode=True,
            fillLevel=0,
            brush=None,
            pen=pen,
            name=name,
        )

    def updateDistPlots(self):
        """
            @description : Update feature distance distribution plots for both train and test sets using the latest histograms from the trainer, including best threshold and FP/FN counts in the titles
            @author : Hyunsu Kim (2026.03.10)
            @history:
                - Modified by Hyunsu Kim (2026.03.19):
                    - Move plotwidget legend and Add information about sample counts, data mean and std in the legend
                    - Set to plot only when data exists
                    - Change the plot title
        """
        # add legends
        trainFeatureLegend = self.trainFeatureDistPlot.addLegend(labelTextColor=pyqtgraph.mkColor("w"))
        testFeatureLegend = self.testFeatureDistPlot.addLegend(labelTextColor=pyqtgraph.mkColor("w"))
        trainFeatureLegend.setOffset((-10, 10))
        testFeatureLegend.setOffset((-10, 10))

        featureDistHists = [self.trainFeatureDistHist, self.testFeatureDistHist]
        featurePlots = [self.trainFeatureDistPlot, self.testFeatureDistPlot]
        titles = [
            self.lang.get("training", "result_main", "trainFeatureDistPlotTitle"),
            self.lang.get("training", "result_main", "testFeatureDistPlotTitle"),
        ]

        # Feature distance distribution (+ best threshold)
        for featureDistHist, featurePlot, title in zip(featureDistHists, featurePlots, titles):
            if featureDistHist:
                edges = featureDistHist.get("edges")
                normal = featureDistHist.get("normal")
                abnormal = featureDistHist.get("abnormal")
                bestThreshold = featureDistHist.get("best_thr")
                normalMean = featureDistHist.get("normalMean")
                abnormalMean = featureDistHist.get("abnormalMean")
                normalStd = featureDistHist.get("normalStd")
                abnormalStd = featureDistHist.get("abnormalStd")
                normalCount = featureDistHist.get("normalCount")
                abnormalCount = featureDistHist.get("abnormalCount")

                normalLegend = "Normal" if normalMean is None and normalStd is None else f"Normal (Sample: {normalCount}, Mean: {normalMean:.3f}, Std: {normalStd:.3f})"
                abnormalLegend = "Abnormal" if abnormalMean is None and abnormalStd is None else f"Abnormal (Sample: {abnormalCount}, Mean: {abnormalMean:.3f}, Std: {abnormalStd:.3f})"

                # Setting labels, title with best threshold and FP/FN counts, and axis ranges
                featurePlot.setLabel("left", "Probability")
                if bestThreshold is None:
                    featurePlot.setTitle(title + "None", **self.style)
                else:
                    featurePlot.setTitle(title + f"{bestThreshold:.3f}", **self.style)
                edges = np.asarray(edges)
                featurePlot.setXRange(float(edges[0]), float(edges[-1]), padding=0.02)
                featurePlot.enableAutoRange(axis="y", enable=True)

                # Plot normal and abnormal distributions as step histograms with fill and legend entries
                if normal is not None:
                    normal = normal / normal.sum()
                    self.plotHistStep(
                        featurePlot,
                        edges,
                        normal,
                        pen=pyqtgraph.mkPen(pyqtgraph.mkColor(GRAPH_PEN_GREEN), width=2),
                        name=normalLegend,
                        brush=pyqtgraph.mkBrush(GRAPH_BRUSH_GREEN),
                    )
                if abnormal is not None:
                    abnormal = abnormal / abnormal.sum()
                    self.plotHistStep(
                        featurePlot,
                        edges,
                        abnormal,
                        pen=pyqtgraph.mkPen(pyqtgraph.mkColor(GRAPH_PEN_RED), width=2),
                        name=abnormalLegend,
                        brush=pyqtgraph.mkBrush(GRAPH_BRUSH_RED),
                    )

                if bestThreshold is not None:
                    thrPen = pyqtgraph.mkPen(pyqtgraph.mkColor(GRAPH_LINE), width=2, style=QtCore.Qt.DashLine)
                    featurePlot.addItem(pyqtgraph.InfiniteLine(pos=bestThreshold, angle=90, pen=thrPen))

    def show_selected_image(self, image_index:int, show_pred_map:bool, showErrorMap:bool, fitinview:bool):
        """
            @description : Display the selected image in the OutputImageWidget based on the current state of the PredictionMapToggle.
            @parameter :
                - image_index: Index of the selected image from the combobox.
                - show_pred_map: Boolean indicating whether to show the prediction map overlay (red highlights for anomalies).
                - showErrorMap: Boolean indicating whether to show the FP/FN error map overlay.
                - fitinview: Boolean indicating whether to fit the image to the view after updating.
            @history:
                - Modified by Chansik Kim (2025.03.21) : Update inference image with new threshold only for anomaly detection task
                - Modified by Hyunsu Kim (2026.03.10) : Add a FP/FN toggle for displaying the FP/FN map overlay
                - Modified by Hyunsu Kim (2026.03.19) : Add a condition to prevent displaying previously saved fp/fn images when retraining the classification model.
        """
        if image_index == -1: return
        image = None

        self.changeToggle()

        if self.is_anomaly_detection:
            threshold_txt = float(self.ThresholdLineEdit.text())
            threshold = threshold_txt if threshold_txt != 0.0 else self.best_threshold
            self.update_pred_image(image_index, threshold)
            self.getFpFnMask(image_index, threshold)
            self.ThresholdLineEdit.setText(f"{self.pred_thresholds:.3f}")
        else:
            showErrorMap = False

        if show_pred_map:
            if self.pred_images != []:
                image = self.pred_images[image_index]#.transpose(1, 0, 2)
        else:
            """
                @description : When toggling off the prediction map, if the error map is enabled, 
                                show the error map instead of the original image to allow users to see FP/FN overlays without the red prediction overlay.
                @author : Hyunsu Kim (2026.03.10)
            """
            if showErrorMap:
                image = self.getFpFnImage(image_index)
            else:
                if self.origin_images != []:
                    image = self.origin_images[image_index]
        
        if image is not None:
            self.OutputImageWidget.updatePhoto(QtGui.QPixmap(QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)), fitinview)

    def getFpFnImage(self, image_index:int):
        """
            @description : Generate an image with FP/FN error regions highlighted, 
                            optionally overlaying on the original image with GT regions highlighted in yellow. 
            @author : Hyunsu Kim (2026.03.10)
            @history:
                - Modified by Hyunsu Kim (2026.03.19):
                    - Delete an unnecessary condition for gtMask
        """
        if image_index == -1: return
        image = None

        if self.origin_images != []:
            image = copy.deepcopy(self.origin_images[image_index])

            # 1) Labeled(GT) region: 50% transparent yellow
            if self.gtMask is not None:
                gtMask = self.gtMask
                base = image.astype(np.float32)
                yellow = np.array(GROUND_LABEL, dtype=np.float32)
                base[gtMask] = base[gtMask] * (1.0 - OPACITY_ALPHA) + yellow * OPACITY_ALPHA
                image = base.astype(np.uint8)

            # 2) FP/FN overlays (opaque)
            if self.fpMask is not None:
                fpMask = self.fpMask
                image[fpMask] = FP_LABEL  # False Positives in Red
            if self.fnMask is not None:
                fnMask = self.fnMask
                image[fnMask] = FN_LABEL  # False Negatives in Blue

        return image

    def getFpFnMask(self, imageIndex, bestThr):
        """
            @description : Generate boolean masks for False Positive (FP) and False Negative (FN) pixel locations based on the current prediction threshold, 
                            which can be used for overlaying error regions on the original image. 
            @author : Hyunsu Kim (2026.03.10)
            @parameter :
                - imageIndex: int, index of the image for which to compute FP/FN masks
                - bestThr: float, threshold for classifying pixels as abnormal or normal based on abnormal scores, used to determine FP/FN conditions
        """
        # -------------------------------
        #   - FP(과검출): pred=abnormal(DATA_ABNORMAL) & gt=normal(DATA_NORMAL)
        #   - FN(미검출): pred=normal(DATA_NORMAL) & gt=abnormal(DATA_ABNORMAL)
        # -------------------------------
        preds = np.where(self.abnormal_scores < bestThr, DATA_NORMAL, DATA_ABNORMAL)
        fpPixels = (preds == DATA_ABNORMAL) & (self.labels == DATA_NORMAL)
        fnPixels = (preds == DATA_NORMAL) & (self.labels == DATA_ABNORMAL)
        gtPixels = (self.labels != DATA_IGNORED)

        try:
            # Sample-level arrays (length N): which image each sample belongs to, and its (x,y) pixel coordinate.
            imageIndice = self.position_indices[:, 0]
            xCoordinateAll = self.position_indices[:, 1]
            yCoordinateAll = self.position_indices[:, 2]
            
            # Initialize empty masks for the current image
            img = self.origin_images[imageIndex]
            height, width, _ = np.shape(img)
            fpImage = np.zeros((height, width), dtype=bool)
            fnImage = np.zeros((height, width), dtype=bool)
            gtImage = np.zeros((height, width), dtype=bool)

            # Find the samples that belong to the current image and update the FP/FN/GT masks accordingly
            selectedImage = (imageIndice == imageIndex)
            if selectedImage is not None:
                xCoordinate = xCoordinateAll[selectedImage]
                yCoordinate = yCoordinateAll[selectedImage]

                fpPixel = fpPixels[selectedImage]
                fnPixel = fnPixels[selectedImage]
                gtPixel = gtPixels[selectedImage]

                if np.any(fpPixel):
                    fpImage[xCoordinate[fpPixel], yCoordinate[fpPixel]] = True
                if np.any(fnPixel):
                    fnImage[xCoordinate[fnPixel], yCoordinate[fnPixel]] = True
                if np.any(gtPixel):
                    gtImage[xCoordinate[gtPixel], yCoordinate[gtPixel]] = True

                self.fpMask = fpImage
                self.fnMask = fnImage
                self.gtMask = gtImage

        except Exception as e:
            print("get Error in getFpFnMask:", e)


    def show_updated_pred_image(self, image_index:int, threshold:float, show_pred_map:bool, showErrorMap:bool):
        self.update_pred_image(image_index, threshold)
        self.show_selected_image(image_index, show_pred_map, showErrorMap, True)

    def update_pred_image(self, image_index, threshold):
        self.pred_images[image_index] = self.get_pred_image(image_index, threshold)
        self.pred_thresholds = threshold

    def get_pred_image(self, image_index, threshold):
        """
        Description:
        Generate an image with abnormal regions highlighted in red.

        Args:
            image_index (int): Index of the target image.
            threshold (float): Threshold for detecting abnormal regions.

        Returns:
            np.ndarray: Original image with abnormal regions (scores >= threshold) highlighted in red ([255, 0, 0]).
        
        modified by Chansik Kim 2024.12.17

        History:
            - Modified by Hyunsu Kim (2026.05.12): Modified to create a temporary mask of the correct size and overwrite the eval mask if the eval_mask size does not match.
        """
        origin_image = np.copy(self.origin_images[image_index])
        w, h, _ = origin_image.shape
        indices = self.position_indices[:, 0]
        indices = np.where(np.array(indices) == image_index)
        abnormal_scores = self.abnormal_scores[indices]
        eval_mask = abnormal_scores >= threshold
        if eval_mask.size != w * h:
            temp = np.zeros(w * h, dtype=bool)
            temp[self.position_indices[indices,1] * h + self.position_indices[indices,2]] = eval_mask
            eval_mask = temp
        origin_image[eval_mask.reshape(w, h)] = [255, 0, 0]
        return origin_image

    def get_scores(self, preds, labels, eps=1e-9) -> str:
        preds = preds.reshape([-1])
        labels = labels.reshape([-1])
        unique_labels = np.unique(labels)

        cm = confusion_matrix(labels, preds, labels=unique_labels)
        recall = (np.diag(cm)/(np.sum(cm, axis=1)+eps))[-1]
        precision = (np.diag(cm)/(np.sum(cm, axis=0)+eps))[-1]
        F1score = (2.0*np.diag(cm)/(np.sum(cm, axis=0)+np.sum(cm, axis=1)+eps))[-1]
        
        return f"Prec: {precision:.3f}, Rec: {recall:.3f}, F1: {F1score:.3f}"

    def result_signal_receiver(self, _dict):        
        if "current_model_type" in _dict:
            self.current_model_type = _dict["current_model_type"]
        # loss and f1 score
        if "train_loss" in _dict:
            self.train_loss.append(_dict["train_loss"])
        if "val_loss" in _dict:
            self.val_loss.append(_dict["val_loss"])
        if "abnormal_avg_f1score" in _dict:
            self.abnormal_avg_f1score.append(_dict["abnormal_avg_f1score"])
        if "train_loss" in _dict or "val_loss" in _dict or "abnormal_avg_f1score" in _dict:
            self.plot_updator.start() # plot update start
        # images, abnormal scores and labels
        if "origin_images" in _dict:
            self.origin_images = copy.deepcopy(_dict["origin_images"])
        if "pred_images" in _dict:
            self.pred_images = copy.deepcopy(_dict["pred_images"])
        if "label_images" in _dict:
            self.label_images = copy.deepcopy(_dict["label_images"])
        if "abnormal_scores" in _dict:
            self.abnormal_scores = copy.deepcopy(_dict["abnormal_scores"])
        if "labels" in _dict:
            self.labels = copy.deepcopy(_dict["labels"])
        if "bestThreshold" in _dict:
            self.best_threshold = _dict["bestThreshold"]
        if "trainFeatureDistHist" in _dict:
            self.trainFeatureDistHist = copy.deepcopy(_dict["trainFeatureDistHist"])
        if "testFeatureDistHist" in _dict:
            self.testFeatureDistHist = copy.deepcopy(_dict["testFeatureDistHist"])
        if "position_indices" in _dict:
            self.position_indices = np.copy(_dict["position_indices"])
        if "save_path" in _dict:
            self.save_path = _dict["save_path"]
        if "results" in _dict:
            self.results = _dict["results"]
        if "init" in _dict:
            self.init_params()
            self.trainFeatureDistPlot.setMouseEnabled(x=False, y=False)
            self.testFeatureDistPlot.setMouseEnabled(x=False, y=False)
        if "is_classification" in _dict:
            self.is_anomaly_detection = False
            self.change_control_ui(self.is_anomaly_detection) # set to specific type of task
            self.show_selected_image(0, self.PredictionMapToggle.isChecked(), self.FpFnMapToggle.isChecked(), True)
            self.init_combobox_item_list(False)
        if "is_anomaly_detection" in _dict:
            self.is_anomaly_detection = True
            self.change_control_ui(self.is_anomaly_detection) # set to specific type of task
            self.pred_thresholds = self.best_threshold
            self.init_images_anomaly_detection(self.origin_images)
            self.updateDistPlots()
            self.trainFeatureDistPlot.setMouseEnabled(x=True, y=True)
            self.testFeatureDistPlot.setMouseEnabled(x=True, y=True)
            self.show_selected_image(0, self.PredictionMapToggle.isChecked(), self.FpFnMapToggle.isChecked(), True)
            self.init_combobox_item_list(False)
        if ("is_classification" in _dict or "is_anomaly_detection" in _dict) and self.plot_updator.isActive():
            self.plot_updator.stop()
