import os
import glob

import numpy as np
from sklearn.cluster import KMeans
import pyqtgraph as pg
import json
from PyQt5 import QtCore, QtWidgets, QtGui
from utils.viewer import Display_viewer
from utils.custom_ui import custom_qtablewidget, ReDockOnCloseDockWidget
import cv2
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import cdist  

from constants.constants import *

from utils.worker import Threading_Worker
from utils.custom_ui import messageBox
from advanced.stylesheet.stylesheet_adv_label_correction_mode import stylesheet

if __name__ == "__main__" :
    from adv_gen_module import gen_module
else:
    from .adv_gen_module import gen_module

# ======================================================
# SIGNAL CLASS
# ======================================================
class SignalString(QtCore.QObject):
    """
    @description : Signal class for transmitting string messages and progress updates
    @author : JiHoon Jung
    @history : 
        1. Hyunsu Kim(2025.06.13) : Added update_signal for image results tab updates 
        2. Hyunsu Kim(2026.02.12) : Modified docstring for image results tab updates without thread
    """
    string_signal = QtCore.pyqtSignal(str)   # For status messages
    progress_signal = QtCore.pyqtSignal(int) # For progress bar updates
    update_signal = QtCore.pyqtSignal(np.ndarray, str)   # For image results tab updates

# ======================================================
# MAIN WIDGET CLASS : advanced_label_correction_Form
# ======================================================
class advanced_label_correction_Form(QtWidgets.QWidget):
    """
    @description : Widget for advanced label correction settings and workflow
    @author : JiHoon Jung
    """
    # --------------------------------------------------
    # Initialization: signals, variables, UI, layout, connections, table setup
    # --------------------------------------------------
    def __init__(self, Sync=None, lang=None) -> None:
        """
        @description : Initialize widget, UI, variables, and signals
        @author : Hyunsu Kim
        @parameters :
            Sync: synchronization object (default None)
            lang: language setting (default None)
        """
        super().__init__()
        self.init(Sync, lang)
        self.init_variable()
        self.init_ui(self)
        self.setup_ui()
        self.init_function()
        self.fill_table()

        # Show form if executed as main module
        if __name__ == "__main__":
            self.show()

    def init(self, Sync, lang):
        """
        @description : Initialize and connect thread worker and signal objects
        @author : Hyunsu Kim
        @parameters :
            Sync: synchronization object
            lang: language setting
        @history :
            1. Hyunsu Kim : Add thread worker to use in image results tab
            2. Hyunsu Kim(2026.02.12) : Remove thread worker for image results tab to update without thread
        """
        self.Sync = Sync
        self.lang = lang
        # Threading_Worker for background execution
        self.worker_1 = Threading_Worker()
        # Connect thread complete callback
        self.worker_1.output.connect(lambda : self.recv_from_threading(mode = LABEL_CORRECTION_MODE_WORKER_1))

        # Create signals for status and progress updates
        self.signal_ = SignalString()
        self.string_signal = self.signal_.string_signal
        self.progress_signal = self.signal_.progress_signal
        self.update_signal = self.signal_.update_signal
        # Connect signal handlers
        self.string_signal.connect(self.update_status)
        self.progress_signal.connect(self.update_progress)
        self.update_signal.connect(self.update_rgb_image)

    def init_variable(self):
        """
        @description : Initialize UI parameters and internal variables
        @author : Hyunsu Kim
        @history :
            1. Hyunsu Kim(2025.06.13) : Added variables for image results tab
            2. Hyunsu Kim(2026.02.09) : Added randomSeed variable and analysis variables for KMeans reproducibility and live plot rendering
            3. Hyunsu Kim(2026.02.12) : Add variables for handling image results tab updates without thread
            4. Hyunsu Kim(2026.02.13) : Add variable for tooltips for similarity mode options
        """
        # Dictionary for parameter headers and widget references
        self.header_dict_ = {}
        # Label correction options and metadata
        self.adv_model_info = {
            0: {"type": "Similarity Mode",
                "tip": ["label:1. Similarity Mode"],
                "value": ["Area"],
                "obj_list": ["combobox:Area,SAM,Cosine,L2,Chebyshev,Canberra,Jeffrey"]},
            1: {"type": "Similarity Threshold",
                "tip": ["label:2. Similarity Threshold"],
                "value": [1.0],
                "obj_list": ["doublespinbox:0.0,100.0,0.0"]},
            2: {"type": "Calibration",
                "tip": ["label:3. Calibration"],
                "value": [True],
                "obj_list": ["toggle:"]},
            3: {"type": "Calibration Ratio",
                "tip": ["label:4. Calibration Ratio"],
                "value": [1.0],
                "obj_list": ["doublespinbox:0.0,1.0,1.0"]},
            4: {"type": "Label Source",
                "tip": ["label:5. Label Source"],
                "value": ["Create"],
                "obj_list": ["combobox:Create,Overwrite"]},
            5: {"type": "Cluster Count (KMeans)",
                "tip": ["label:6. Cluster Count (min - 2, max - 15, recommended 8)"],
                "value": [5],
                "obj_list": ["spinbox:2,15,5"]},
        }
        self.adv_data_list_info = {}  # Selected data list info
        self.worker_id = -1           # Current worker ID
        self.dash = "-"               # Separator string for logs
        self.mode = "Label Correction Mode"
        self.interrupt_ = False       # Interrupt flag
        self.signal_sw = True         # Signal protection flag
        # Initialize variables related to image results tab
        self.apply_threshold_change = False # Flag to apply threshold changes
        self.thr = -1                 # Threshold value for image results
        self.total_nonzero_pixel = {} # Dictionary to store total non-zero pixels for each image
        self.update_total_nonzero_pixel = {} # Dictionary to store updated non-zero pixels for each image
        self.rgb_image = {}           # Dictionary to store RGB images for each image
        self.randomSeed = 42
        self.label = {}
        self.data = {}
        self.similarity = {}
        self.refLabel = {}
        self.workingDone = {}
        self.updateImage = {}            # Dictionary to store updated RGB images for live updates in image results tab
        self.normalLabelColor = {} 
        # Diagnostics plot data for live PyQtGraph rendering
        self.similarityHistData = {}            # {data_name: {centers, counts, vmin, vmax, thr, method}}
        self.spectrumBeforeAfterData = {}      # {data_name: {bands, mb, sb, ma, sa, method}}
        self.similarity_tooltips = [
            "Area 기반 유사도 (마스크/영역 크기 비교, 스케일 차이 민감)",
            "SAM 스펙트럼 각도 기반 유사도 (조도 변화에 강건, 패턴 형태 중심)", 
            "Cosine 방향 기반 유사도 (SAM과 유사)", 
            "L2 거리 (밝기 차이, 이상치에 민감, 가장 직관적)", 
            "Chebyshev 거리 (최대 차이 기준, 특정 파장대의 급격한 차이에 민감)", 
            "Canberra 거리 (파장별 상대적 비율 차이, 저신호 영역에 민감)", 
            "Jeffrey divergence 기반 거리 (통계적 분포 차이, 패턴 차이 정밀 반영)", 
        ]

    # --------------------------------------------------
    # UI Widget Creation and Style Setup
    # --------------------------------------------------
    def init_ui(self, mainWindow):
        """
        @description : Create widgets and containers needed for mainWindow
        @author : Hyunsu Kim
        @parameters :
            mainWindow: top-level widget object
        @history :
            1. Hyunsu Kim(2025.06.13) : Add image results tab widget and related widgets
            2. Hyunsu Kim(2025.09.04) : enable drag & drop inside the image display widget
            3. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
            4. Hyunsu Kim(2026.02.09) : Modify data list table widget to use custom_qtablewidget and Add analysis plot widgets in image results tab
        """
        mainWindow.setObjectName("adv_setting_form")
        mainWindow.resize(LABEL_CORRECTION_WINDOW_WIDTH, LABEL_CORRECTION_WINDOW_HEIGHT)
        mainWindow.setWindowTitle("Advanced Setting")
        mainWindow.setStyleSheet(stylesheet)  # Custom CSS stylesheet

        # Main horizontal/vertical layouts
        self.advanced_label_correction_main_horizon = QtWidgets.QHBoxLayout(mainWindow)
        self.advanced_label_correction_main_vertical = QtWidgets.QVBoxLayout()

        # "Setting" groupbox and layout
        self.advanced_label_correction_setting_groupbox = QtWidgets.QGroupBox()
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_setting_groupbox", self.advanced_label_correction_setting_groupbox)
        self.advanced_label_correction_setting_vertical = QtWidgets.QVBoxLayout()

        # "Data List" groupbox and layout
        self.advanced_label_correction_datalist_groupbox = QtWidgets.QGroupBox()
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_datalist_groupbox", self.advanced_label_correction_datalist_groupbox)
        self.advanced_label_correction_datalist_vertical = QtWidgets.QVBoxLayout()

        # Data list tableview setup
        self.advanced_label_correction_datalist_tableview = custom_qtablewidget(obj_name="advanced_label_correction_datalist_tableview", col=3, row=4)
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_datalist_tableview", self.advanced_label_correction_datalist_tableview)
        self.advanced_label_correction_datalist_tableview_setting_header_labels = ["Index", "Data", "Use"]
        self.advanced_label_correction_datalist_tableview.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.advanced_label_correction_datalist_tableview.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.create_obj = self.advanced_label_correction_datalist_tableview.create_obj
       
        # "Search" / "Clear" buttons and layout
        self.advanced_label_correction_datalist_global_horizon = QtWidgets.QHBoxLayout()
        self.advanced_label_correction_datalist_global_search_btn = QtWidgets.QPushButton()
        self.advanced_label_correction_datalist_global_search_btn.setObjectName(
            "advanced_label_correction_datalist_global_search_btn")
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_datalist_global_search_btn", self.advanced_label_correction_datalist_global_search_btn)
        self.advanced_label_correction_datalist_global_clear_btn = QtWidgets.QPushButton()
        self.advanced_label_correction_datalist_global_clear_btn.setObjectName(
            "advanced_label_correction_datalist_global_clear_btn")
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_datalist_global_clear_btn", self.advanced_label_correction_datalist_global_clear_btn)

        # Start/Stop buttons
        self.advanced_label_correction_setting_horizon = QtWidgets.QHBoxLayout()
        self.advanced_label_correction_setting_start_btn = QtWidgets.QPushButton()
        self.advanced_label_correction_setting_start_btn.setObjectName(
            "advanced_label_correction_setting_start_btn")
        self.advanced_label_correction_setting_start_btn.setCheckable(True)
        self.advanced_label_correction_setting_start_btn.resize(150, 150)
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_setting_start_btn", self.advanced_label_correction_setting_start_btn)

        self.advanced_label_correction_setting_stop_btn = QtWidgets.QPushButton()
        self.advanced_label_correction_setting_stop_btn.setObjectName(
            "advanced_label_correction_setting_stop_btn")
        self.advanced_label_correction_setting_stop_btn.setEnabled(False)
        self.advanced_label_correction_setting_stop_btn.resize(150, 150)
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_setting_stop_btn", self.advanced_label_correction_setting_stop_btn)

        # Main widget for advanced label correction status
        self.advanced_label_correction_status_mainwidget = QtWidgets.QWidget()
        self.advanced_label_correction_status_mainwidget.setObjectName("advanced_label_correction_status_mainwidget")
        self.advanced_label_correction_status_mainwidgetLayout = QtWidgets.QVBoxLayout(self.advanced_label_correction_status_mainwidget)
        self.advanced_label_correction_status_mainwidgetLayout.setObjectName("advanced_label_correction_status_mainwidgetLayout")

        # Status output window and progress bar
        self.advanced_label_correction_status_groupbox = QtWidgets.QGroupBox()
        self.advanced_label_correction_status_groupbox.setObjectName(
            "advanced_label_correction_status_groupbox")
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_status_groupbox", self.advanced_label_correction_status_groupbox)
        self.advanced_label_correction_status_groupbox_Layout = QtWidgets.QVBoxLayout(self.advanced_label_correction_status_groupbox)
        self.advanced_label_correction_status_groupbox_Layout.setObjectName(
            "advanced_label_correction_status_groupbox_Layout")
        self.advanced_label_correction_status_textedit = QtWidgets.QPlainTextEdit()
        self.advanced_label_correction_status_textedit.setReadOnly(True)
        self.advanced_label_correction_status_textedit.setUndoRedoEnabled(False)

        # Image results tab widget and related widgets
        self.advancedMain = QtWidgets.QTabWidget()
        self.advancedMain.setObjectName("advancedMain")

        self.advanced_label_correction_image_widget = QtWidgets.QWidget()
        self.advanced_label_correction_image_widget.setObjectName("advanced_label_correction_image_widget")

        self.advanced_label_correction_image_widget_Layout = QtWidgets.QVBoxLayout(self.advanced_label_correction_image_widget)
        self.advanced_label_correction_image_widget_Layout.setObjectName("advanced_label_correction_image_widget_Layout")

        self.advanced_label_correction_image_groupbox = QtWidgets.QGroupBox(self.advanced_label_correction_image_widget)
        self.advanced_label_correction_image_groupbox.setObjectName("advanced_label_correction_image_groupbox")
        self.advanced_label_correction_image_groupbox_Layout = QtWidgets.QVBoxLayout(self.advanced_label_correction_image_groupbox)
        self.advanced_label_correction_image_groupbox_Layout.setObjectName("advanced_label_correction_image_groupbox_Layout")

        self.resultControlWidget = QtWidgets.QWidget()
        self.resultControlWidget.setObjectName("resultControlWidget")

        self.resultControlLayout = QtWidgets.QHBoxLayout(self.resultControlWidget)
        self.resultControlLayout.setObjectName("resultControlLayout")

        # Image selection controller
        self.imageSelectorMainWidget = QtWidgets.QWidget()
        self.imageSelectorMainWidget.setObjectName("imageSelectorMainWidget")

        self.imageSelectorMainLayout = QtWidgets.QHBoxLayout(self.imageSelectorMainWidget)
        self.imageSelectorMainLayout.setObjectName("imageSelectorMainLayout")

        self.imageSelectorComboBox = QtWidgets.QComboBox()
        self.imageSelectorComboBox.setObjectName("imageSelectorComboBox")

        self.advanced_label_correction_image_groupbox_HorizontalLine = QtWidgets.QFrame()
        self.advanced_label_correction_image_groupbox_HorizontalLine.setObjectName("advanced_label_correction_image_groupbox_HorizontalLine")
        self.advanced_label_correction_image_groupbox_HorizontalLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.advanced_label_correction_image_groupbox_HorizontalLine.setFrameShadow(QtWidgets.QFrame.Sunken)

        # Vertical line (Image selection controller <-> Pred map controller)
        self.resultControlVerticalLine1 = QtWidgets.QFrame()
        self.resultControlVerticalLine1.setObjectName("resultControlVerticalLine1")
        self.resultControlVerticalLine1.setFrameShape(QtWidgets.QFrame.VLine)
        self.resultControlVerticalLine1.setFrameShadow(QtWidgets.QFrame.Sunken)

        # Threshold controller
        self.thresholdMainWidget = QtWidgets.QWidget()
        self.thresholdMainWidget.setObjectName("thresholdMainWidget")

        self.thresholdMainLayout = QtWidgets.QHBoxLayout(self.thresholdMainWidget)
        self.thresholdMainLayout.setObjectName("thresholdMainLayout")
        
        self.thresholdLabel = QtWidgets.QLabel()
        self.thresholdLabel.setObjectName("thresholdLabel")
        self.lang.set("advanced", "advanced_label_correction_main", "thresholdLabel", self.thresholdLabel)

        self.thresholdLineEdit = QtWidgets.QLineEdit()
        self.thresholdLineEdit.setObjectName("thresholdLineEdit")

        self.thresholdButton = QtWidgets.QPushButton()
        self.thresholdButton.setObjectName("thresholdButton")
        self.thresholdButton.setCheckable(True)
        self.thresholdButton.setEnabled(False)  # Initially disabled until threshold is set
        self.lang.set("advanced", "advanced_label_correction_main", "thresholdButton", self.thresholdButton)

        # Reduced Pixel controller
        self.reducedPixelMainWidget = QtWidgets.QWidget()
        self.reducedPixelMainWidget.setObjectName("reducedPixelMainWidget")

        self.reducedPixelMainLayout = QtWidgets.QHBoxLayout(self.reducedPixelMainWidget)
        self.reducedPixelMainLayout.setObjectName("reducedPixelMainLayout")
        self.reducedPixelLabel = QtWidgets.QLabel()
        self.reducedPixelLabel.setObjectName("reducedPixelLabel") 
        self.lang.set("advanced", "advanced_label_correction_main", "reducedPixelLabel", self.reducedPixelLabel)

        self.reducedPixelValue = QtWidgets.QLabel("0 (0 %)")
        self.reducedPixelValue.setObjectName("reducedPixelValue")  

        # Image + diagnostics view (splitter)
        self.outputImageBox = QtWidgets.QGroupBox("Image Results")
        self.outputImageLayout = QtWidgets.QVBoxLayout(self.outputImageBox)
        self.outputImageWidget = Display_viewer(usescrollbar=False)
        self.outputImageWidget.updateDrag(True)
        self.outputImageWidget.setBackgroundBrush(pg.mkColor(RESULT_BACKGROUD_COLOR))

        # Split vertically on screen (left/right)
        self.outputSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.outputSplitter.setObjectName("outputSplitter")
        # Outer border around both diagnostic plots
        self.analysisGroupBox = QtWidgets.QGroupBox("Analysis")
        self.analysisGroupBox.setObjectName("analysisGroupBox")

        self.analysisGroupBoxLayout = QtWidgets.QVBoxLayout(self.analysisGroupBox)
        self.analysisGroupBoxLayout.setContentsMargins(4, 4, 4, 4)

        self.analysisWidget = QtWidgets.QWidget()
        self.analysisWidget.setObjectName("analysisWidget")
        self.analysisLayout = QtWidgets.QVBoxLayout(self.analysisWidget)
        self.analysisLayout.setContentsMargins(0, 0, 0, 0)

        # Dockable analysis (only plots): embed a QMainWindow as a dock host.
        self.analysisDockHost = QtWidgets.QMainWindow()
        self.analysisDockHost.setObjectName("analysisDockHost")
        self.analysisDockHost.setDockOptions(
            QtWidgets.QMainWindow.AllowTabbedDocks
            | QtWidgets.QMainWindow.AnimatedDocks
            | QtWidgets.QMainWindow.AllowNestedDocks
        )
        self.analysisDockHost.setTabPosition(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea,
            QtWidgets.QTabWidget.North,
        )

        # Plot viewers (dock contents)
        self.histPlotViewer = pg.PlotWidget()
        self.histPlotViewer.setMinimumHeight(160)
        self.histPlotViewer.setBackground(pg.mkColor(RESULT_BACKGROUD_COLOR))
        self.histPlotViewer.setLabel("left", "Count", color="w", **{"font-size": "12px"})
        self.histPlotViewer.setLabel("bottom", "Similarity score", color="w", **{"font-size": "12px"})
        self.histPlotViewer.getAxis("left").setTextPen(pg.mkPen("w", width=2))
        self.histPlotViewer.getAxis("bottom").setTextPen(pg.mkPen("w", width=2))
        self.histPlotViewer.showGrid(x=True, y=True, alpha=0.25)
        self.histPlotViewer.setMouseEnabled(x=False, y=True)
        self.histPlotViewer.getViewBox().setLimits(yMin=0)

        self.beforeAfterPlotViewer = pg.PlotWidget()
        self.beforeAfterPlotViewer.setMinimumHeight(160)
        self.beforeAfterPlotViewer.setBackground(pg.mkColor(RESULT_BACKGROUD_COLOR))
        self.beforeAfterPlotViewer.setLabel("left", "Value", color="w", **{"font-size": "12px"})
        self.beforeAfterPlotViewer.setLabel("bottom", "Band", color="w", **{"font-size": "12px"})
        self.beforeAfterPlotViewer.getAxis("left").setTextPen(pg.mkPen("w", width=2))
        self.beforeAfterPlotViewer.getAxis("bottom").setTextPen(pg.mkPen("w", width=2))
        self.beforeAfterPlotViewer.showGrid(x=True, y=True, alpha=0.25)
        self.beforeAfterPlotViewer.setMouseEnabled(x=False, y=True)
        self.beforeAfterPlotViewer.getViewBox().setLimits(yMin=0)

        self.histPlotDock = ReDockOnCloseDockWidget("Similarity Histogram", self.analysisDockHost)
        self.histPlotDock.setObjectName("histPlotDock")
        self.histPlotDock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable # move widgets between dock areas
            | QtWidgets.QDockWidget.DockWidgetFloatable # detach widgets as independent widnows
            | QtWidgets.QDockWidget.DockWidgetClosable # close widgets
        )

        self.beforeAfterPlotDock = ReDockOnCloseDockWidget("Before/After Distribution", self.analysisDockHost)
        self.beforeAfterPlotDock.setObjectName("beforeAfterPlotDock")
        self.beforeAfterPlotDock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable # move widgets between dock areas
            | QtWidgets.QDockWidget.DockWidgetFloatable # detach widgets as independent widnows
            | QtWidgets.QDockWidget.DockWidgetClosable # dock widgets can be closed
        )

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

    # --------------------------------------------------
    # Layout Configuration
    # --------------------------------------------------
    def setup_ui(self):
        """
        @description : Arrange created widgets in the proper layouts
        @author : Hyunsu Kim
        @history :
            1. Hyunsu Kim(2025.06.13) : Add image results tab layout and widgets, modify status widget layout
            2. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
            3. Hyunsu Kim(2026.02.09) : Modify data list table layout to use custom_qtablewidget and Add analysis plot widgets in image results tab
            4. Hyunsu Kim(2026.02.13) : Add validator for handling threshold input
        """
        # Assign vertical layout to "Setting" groupbox
        self.advanced_label_correction_setting_groupbox.setLayout(self.advanced_label_correction_setting_vertical)
        # Add Start/Stop buttons to horizontal layout
        self.advanced_label_correction_setting_horizon.addWidget(self.advanced_label_correction_setting_start_btn)
        self.advanced_label_correction_setting_horizon.addWidget(self.advanced_label_correction_setting_stop_btn)

        self.advanced_label_correction_datalist_global_horizon.addWidget(self.advanced_label_correction_datalist_global_search_btn)
        self.advanced_label_correction_datalist_global_horizon.addStretch()
        self.advanced_label_correction_datalist_global_horizon.addWidget(self.advanced_label_correction_datalist_global_clear_btn)

        # Add search buttons and table to "Data List" groupbox
        self.advanced_label_correction_datalist_vertical.addLayout(self.advanced_label_correction_datalist_global_horizon)
        self.advanced_label_correction_datalist_vertical.addWidget(self.advanced_label_correction_datalist_tableview)
        self.advanced_label_correction_datalist_groupbox.setLayout(self.advanced_label_correction_datalist_vertical)

        # Add Setting, Data List, and Start/Stop to main vertical layout
        self.advanced_label_correction_main_vertical.addWidget(
            self.advanced_label_correction_setting_groupbox)
        self.advanced_label_correction_main_vertical.addWidget(
            self.advanced_label_correction_datalist_groupbox)
        self.advanced_label_correction_main_vertical.addLayout(
            self.advanced_label_correction_setting_horizon)

        # Add status textedit and progress bar to status main widget layout
        self.advanced_label_correction_status_groupbox_Layout.addWidget(self.advanced_label_correction_status_textedit)
        self.advanced_label_correction_status_groupbox_Layout.addWidget(self.progress_bar)

        validator = QtGui.QDoubleValidator()
        validator.setBottom(0.0)
        validator.setTop(100.0)
        self.thresholdLineEdit.setValidator(validator)

        # Image results tab widget settings
        self.resultControlLayout.addWidget(self.imageSelectorMainWidget)
        self.resultControlLayout.addWidget(self.resultControlVerticalLine1)
        self.resultControlLayout.addWidget(self.thresholdMainWidget)
        self.resultControlLayout.addWidget(self.reducedPixelMainWidget)
        self.thresholdMainLayout.addWidget(self.thresholdLabel)
        self.thresholdMainLayout.addWidget(self.thresholdLineEdit)
        self.thresholdMainLayout.addWidget(self.thresholdButton)
        self.reducedPixelMainLayout.addWidget(self.reducedPixelLabel)
        self.reducedPixelMainLayout.addWidget(self.reducedPixelValue)
        self.imageSelectorMainLayout.addWidget(self.imageSelectorComboBox)
        # Keep the control bar compact; let the splitter take remaining space.
        self.resultControlLayout.setContentsMargins(0, 0, 0, 0)
        self.resultControlWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.advanced_label_correction_image_groupbox_Layout.addWidget(self.resultControlWidget, 0, QtCore.Qt.AlignLeft)
        self.advanced_label_correction_image_groupbox_Layout.addWidget(self.advanced_label_correction_image_groupbox_HorizontalLine)
        self.outputImageLayout.addWidget(self.outputImageWidget)
        self.outputSplitter.addWidget(self.outputImageBox)

        self.histPlotDock.setWidget(self.histPlotViewer)
        self.beforeAfterPlotDock.setWidget(self.beforeAfterPlotViewer)
        self.analysisDockHost.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.histPlotDock)
        # Split top/bottom (like a vertical splitter inside the dock area)
        self.analysisDockHost.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.beforeAfterPlotDock)
        self.analysisDockHost.splitDockWidget(self.histPlotDock, self.beforeAfterPlotDock, QtCore.Qt.Vertical)

        self.analysisGroupBoxLayout.addWidget(self.analysisDockHost)
        self.analysisLayout.addWidget(self.analysisGroupBox)

        # analysisDockHost is already added to analysisLayout in init_ui
        self.outputSplitter.addWidget(self.analysisWidget)
        self.outputSplitter.setStretchFactor(0, 3)
        self.outputSplitter.setStretchFactor(1, 2)

        # Placing the status window and image results window in the final main layout
        self.advanced_label_correction_status_mainwidgetLayout.addWidget(self.advanced_label_correction_status_groupbox)
        self.advanced_label_correction_image_widget_Layout.addWidget(self.advanced_label_correction_image_groupbox)
        self.advanced_label_correction_image_widget_Layout.setContentsMargins(0, 0, 0, 0)
        self.advanced_label_correction_image_groupbox_Layout.addWidget(self.outputSplitter)
        # Ensure outputSplitter gets all extra vertical space.
        self.advanced_label_correction_image_groupbox_Layout.setStretch(0, 0)
        self.advanced_label_correction_image_groupbox_Layout.setStretch(1, 0)
        self.advanced_label_correction_image_groupbox_Layout.setStretch(2, 1)
        self.advanced_label_correction_main_horizon.addLayout(self.advanced_label_correction_main_vertical)
        self.advancedMain.addTab(self.advanced_label_correction_status_mainwidget, "Status")
        self.advancedMain.addTab(self.advanced_label_correction_image_widget, "Image results")
        self.lang.set("advanced", "advanced_label_correction_main", "statusTab", self.advancedMain)
        self.lang.set("advanced", "advanced_label_correction_main", "imageResultTab", self.advancedMain)
        self.advanced_label_correction_main_horizon.addWidget(self.advancedMain)

    def adjust_combo_box_width(self):
        """
        description: Added dynamic width adjustment functionality to automatically resize imageSelectorComboBox based on its content length
        modified by Chansik Kim 2024.12.16
        """
        font_metrics = self.imageSelectorComboBox.fontMetrics()
        text_width = 100  # Default minimum width
        if self.imageSelectorComboBox.count() > 0:
            text_width = max(font_metrics.horizontalAdvance(self.imageSelectorComboBox.itemText(i)) 
                           for i in range(self.imageSelectorComboBox.count()))
        
        # Add padding for dropdown arrow and margins
        self.imageSelectorComboBox.setFixedWidth(text_width + 30)

    # --------------------------------------------------
    # Signal-Slot Connections
    # --------------------------------------------------
    def init_function(self):
        """
        @description : Connect buttons and other widgets to their event handlers
        @author : Hyunsu Kim
        @history :
            1. Hyunsu Kim(2025.06.13) : Add connections for image results tab widgets
            2. Hyunsu Kim(2026.02.12) : Add connection for handling image size changes via splitter movement
        """
        self.advanced_label_correction_datalist_global_search_btn.clicked.connect(
            lambda: self.button_event(mode=LABEL_CORRECTION_DATALIST))
        self.advanced_label_correction_datalist_global_clear_btn.clicked.connect(
            lambda: self.button_event(mode=LABEL_CORRECTION_CLEAR))
        self.advanced_label_correction_setting_start_btn.clicked.connect(
            lambda: self.button_event(mode=LABEL_CORRECTION_START))
        self.advanced_label_correction_setting_stop_btn.clicked.connect(
            lambda: self.button_event(mode=LABEL_CORRECTION_STOP))
        self.imageSelectorComboBox.activated.connect(lambda: self.update_rgb_image(rgb_image=self.rgb_image[self.imageSelectorComboBox.currentText()], data_name=self.imageSelectorComboBox.currentText()))
        self.thresholdButton.clicked.connect(lambda: self.button_event(mode=LABEL_CORRECTION_THRESHOLD))
        self.outputSplitter.splitterMoved.connect(lambda pos, index: self.outputImageWidget.fitInView())

    # --------------------------------------------------
    # Parameter Table Creation and Initialization
    # --------------------------------------------------
    def fill_table(self):
        """
        @description : Create widgets and items for parameter settings and set initial state
        @author : Hyunsu Kim
        @history :
            1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
            2. Hyunsu Kim(2026.02.09) : Modify double spinbox in parameter setting to use custom_qtablewidget
            3. Hyunsu Kim(2026.02.13) : Add tooltips for similarity mode options
        """
        for idx, info in self.adv_model_info.items():
            # Create tooltip(label) and parameter setting widgets
            self.header_dict_[idx] = {
                "obj_tip": self.create_obj(idx, obj_type="widget", obj_list=info["tip"]),
                "obj_set": self.create_obj(idx, obj_type="widget", obj_list=info["obj_list"])
            }
            if idx == 0:
                # Set tooltip for similarity mode combobox
                combobox_widget = self.header_dict_[idx]["obj_set"]["combobox"]
                for i in range(combobox_widget.count()):
                    combobox_widget.setItemData(i, self.similarity_tooltips[i], QtCore.Qt.ToolTipRole)
            if idx == 5:
                # Set spinbox range for cluster count
                spinbox_widget = self.header_dict_[idx]["obj_set"]["spinbox"]
                spinbox_widget.setMinimum(2)
                spinbox_widget.setMaximum(15)
            if info["obj_list"][0].startswith("doublespinbox:"):
                self.header_dict_[idx]["obj_set"]["spinbox"].setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
            # Add both widgets to a horizontal container
            container = QtWidgets.QHBoxLayout()
            container.setContentsMargins(3, 3, 3, 3)
            container.addWidget(self.header_dict_[idx]["obj_tip"]["widget"])
            container.addStretch()
            container.addWidget(self.header_dict_[idx]["obj_set"]["widget"])
            self.header_dict_[idx]['obj'] = container
            self.advanced_label_correction_setting_vertical.addLayout(container)

        # Set initial state and signal connection for "Calibration" toggle
        calibration_toggle = self.header_dict_[2]["obj_set"]["toggle"]
        calibration_toggle.setChecked(self.adv_model_info[2]["value"][0])
        calibration_toggle.toggled.connect(lambda state: self.toggle_event(idx=2, ch=state))

        # Set initial value and signal connection for "Calibration Ratio" spinbox
        ratio_spinbox = self.header_dict_[3]["obj_set"]["spinbox"]
        ratio_spinbox.setDecimals(2)
        ratio_spinbox.setValue(round(self.adv_model_info[3]["value"][0], 2))
        ratio_spinbox.setSingleStep(0.01)
        ratio_spinbox.valueChanged.connect(lambda val: self.valuechange_event(idx=3, value=round(val, 2)))


        # 1. similarity mode
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_similaritymode_label", self.header_dict_[0]["obj_tip"]["label"])

        # 2. similarity threshold
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_similaritythreshold_label", self.header_dict_[1]["obj_tip"]["label"])

        # 3. calibration
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_calibration_label", self.header_dict_[2]["obj_tip"]["label"])

        # 4. calibration ratio
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_calibrationratio_label", self.header_dict_[3]["obj_tip"]["label"])

        # 5. label source
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_labelsource_label", self.header_dict_[4]["obj_tip"]["label"])
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_labelsource_combobox", self.header_dict_[4]["obj_set"]["combobox"])

    # --------------------------------------------------
    # Toggle Event Handling (Calibration Mode & Data List "Use" Toggle)
    # --------------------------------------------------
    def toggle_event(self, idx, ch, obj=None):
        """
        @description : Called when a toggle widget is changed; handles calibration mode and data list usage toggle.
        @author : Hyunsu Kim
        @parameters :
            idx: Index of the toggled widget (2 is calibration mode)
            ch: Toggle state (True/False)
            obj: Data list item info (default None)
        """
        if idx == 2:
            # Calibration mode toggle
            self.adv_model_info[idx]["value"][0] = ch
            msg = "Calibration enabled.\n" if ch else "Calibration disabled.\n"
            self.string_signal.emit(msg)
        else:
            # Data list "Use" toggle
            if idx in self.adv_data_list_info:
                self.adv_data_list_info[idx]["use"] = ch

    # --------------------------------------------------
    # Value Change Event Handling (Spinbox)
    # --------------------------------------------------
    def valuechange_event(self, idx, value):
        """
        @description : Called when a spinbox value is changed; updates internal variable.
        @author : Hyunsu Kim
        @parameters :
            idx: Index of the changed spinbox
            value: New value
        @history :
            1. Hyunsu Kim(2025.09.23) : Remove unnecessary if statements
        """
        self.adv_model_info[idx]["value"][0] = value

    # --------------------------------------------------
    # Status Update and Progress Bar Handling
    # --------------------------------------------------
    def update_status(self, string_):
        """
        @description : Append string to the status output pane.
        @author : Hyunsu Kim
        @parameters :
            string_: String to output
        @history :
            1. Hyunsu Kim(2025.09.23) : Remove unnecessary try-except statements
        """
        self.advanced_label_correction_status_textedit.appendPlainText(string_)

    def update_progress(self, value):
        """
        @description : Update the progress bar value.
        @author : Hyunsu Kim
        @parameters :
            value: Progress bar value (0~100)
        """
        self.progress_bar.setValue(value)

    # --------------------------------------------------
    # Restore UI State After Worker Thread Completion
    # --------------------------------------------------
    def recv_from_threading(self, mode):
        """
        @description : Restore UI state after worker thread completes.
        @author : Hyunsu Kim
        @parameters :
            output: Result of thread work
        @history :
            1. Hyunsu Kim(2025.06.13) : Added mode parameter to handle image results tab updates
            2. Hyunsu Kim(2025.09.23) : Remove image results tab updates
        """
        if mode == LABEL_CORRECTION_MODE_WORKER_1:
            self.worker_id = -1
            if self.advanced_label_correction_setting_start_btn.isChecked():
                self.advanced_label_correction_setting_start_btn.toggle()
            self.advanced_label_correction_setting_start_btn.setEnabled(True)
            self.advanced_label_correction_setting_stop_btn.setEnabled(False)
            self.advanced_label_correction_setting_groupbox.setEnabled(True)
            self.advanced_label_correction_datalist_groupbox.setEnabled(True)
            self.imageSelectorComboBox.setEnabled(True)
            self.thresholdButton.setEnabled(True)
            self.progress_signal.emit(0)
            self.progress_bar.hide()

    # --------------------------------------------------
    # Start/Stop Button Event Handling
    # --------------------------------------------------
    def button_event(self, mode):
        """
        @description : Handle Start/Stop button click events.
        @author : Hyunsu Kim
        @parameters :
            mode: 0 for start, 1 for stop
        @history :
            1. Hyunsu Kim
             - The mode value is one of LABEL_CORRECTION_START, LABEL_CORRECTION_STOP, or LABEL_CORRECTION_THRESHOLD.
             - LABEL_CORRECTION_START: Start label calibration
             - LABEL_CORRECTION_STOP: Stop label calibration
             - LABEL_CORRECTION_THRESHOLD: Apply similarity threshold
             - using string signal to print messages in the status output window
            2. Hyunsu Kim(2025.09.04) : Prevent simultaneous use of the start button and threshold button
            3. Hyunsu Kim(2025.09.23) : reset Image Results tab when starting label correction
            4. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
            5. Hyunsu Kim(2026.02.09) : 
                - when stopping label correction, toggle off the start button if it's still checked
                - when starting label correction or applying threshold, clear previous analysis plot data
                - merge button datalist event and button event
            6. Hyunsu Kim(2026.02.13) : Change the processing to not use thread when pressing the apply button
            7. Yugyeong Hong(2026.02.14) : Refactor message box with util method and language support
            8. Hyunsu Kim(2026.03.13) : Correct the button event to update the UI state After apply_threshold function
        """
        if mode == LABEL_CORRECTION_START:  # Start
            # Disable UI buttons and groups
            self.interrupt_ = False
            self.advanced_label_correction_setting_start_btn.setEnabled(False)
            self.advanced_label_correction_setting_stop_btn.setEnabled(True)
            self.advanced_label_correction_setting_groupbox.setEnabled(False)
            self.advanced_label_correction_datalist_groupbox.setEnabled(False)
            self.imageSelectorComboBox.clear()
            self.imageSelectorComboBox.setEnabled(False)
            self.thresholdButton.setEnabled(False)
            self.outputImageWidget.initPhoto()
            self.advanced_label_correction_status_textedit.clear()
            self.histPlotViewer.clear()
            self.beforeAfterPlotViewer.clear()
            self.thresholdLineEdit.setText("0")
            for _, data in self.adv_data_list_info.items():
                data["wrongProcess"] = False

            # Print current parameter settings in the output window
            header = f"{self.mode}\n{self.dash * 30}"
            self.string_signal.emit(header)
            self.string_signal.emit("Parameter Setting\n")
            for idx, info in self.adv_model_info.items():
                param_type = info["type"]
                obj_set = self.header_dict_[idx]["obj_set"]
                if "spinbox" in obj_set:
                    val = obj_set["spinbox"].value()
                elif "toggle" in obj_set:
                    val = obj_set["toggle"].isChecked()
                elif "combobox" in obj_set:
                    val = obj_set["combobox"].currentText()
                else:
                    val = "(unknown type)"
                self.string_signal.emit(
                    f"{idx+1}. {param_type} : {val}\n"
                )
            self.string_signal.emit(self.dash * 30)
            self.string_signal.emit("Data List\n")

            # Print number of selected datasets
            selected_count = sum(
                1 for v in self.adv_data_list_info.values() if v["obj_set"]["toggle"].isChecked()
            )
            self.string_signal.emit(f"Total: {selected_count}\n")
            self.string_signal.emit("Processing Start....\n")

            # Show progress bar and launch background work
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            for dataPath, data in self.adv_data_list_info.items():
                self.workingDone[dataPath] = False

            self.worker_1.staging(self.correct_label_mode)
            self.worker_id = self.worker_1.cur_id
            self.worker_1.start()
        elif mode == LABEL_CORRECTION_STOP: # Stop
            # Confirm stop with dialog
            response = messageBox(mode=MESSAGE_BOX_CONFIRMATION, 
                          title=self.lang.get("advanced", "advanced_label_correction_main", "advanced_label_correction_msg_stop_title"), 
                          text=self.lang.get("advanced", "advanced_label_correction_main", "advanced_label_correction_msg_stop_message"),
                          buttons={self.lang.get("main", "messageBox", "msgYes"): "accept", self.lang.get("main", "messageBox", "msgNo"): "reject"})
            if response == "accept":
                self.interrupt_ = True
                self.worker_id = -1
                if self.advanced_label_correction_setting_start_btn.isChecked():
                    self.advanced_label_correction_setting_start_btn.toggle()
                self.advanced_label_correction_setting_start_btn.setEnabled(True)
                self.advanced_label_correction_setting_stop_btn.setEnabled(False)
                self.advanced_label_correction_setting_groupbox.setEnabled(True)
                self.advanced_label_correction_datalist_groupbox.setEnabled(True)
                firstDonePath = next((data_path for data_path, done in self.workingDone.items() if done), None)
                if firstDonePath is not None:
                    data_name = firstDonePath.split("/")[-1]
                    self.update_rgb_image(rgb_image=self.rgb_image[data_name], data_name=data_name)
                self.string_signal.emit(f"\n{'-' * 50}\nProcess stopped by user.\n{'-' * 50}")
        # Image results function works when button is clicked
        elif mode == LABEL_CORRECTION_THRESHOLD:
                self.interrupt_ = False
                self.beforeAfterPlotViewer.clear()
                self.advanced_label_correction_setting_start_btn.setEnabled(False)
                self.imageSelectorComboBox.setEnabled(False)
                self.thresholdButton.setEnabled(False)
                self.advanced_label_correction_datalist_global_clear_btn.setEnabled(False)
                finishApplyThr = self.apply_threshold()
                if finishApplyThr:
                    self.apply_threshold_change = False
                else:
                    self.string_signal.emit("error occured doing apply_threshold.\n")
                if self.thresholdButton.isChecked():
                    self.thresholdButton.toggle()
                self.thresholdButton.setEnabled(True)
                self.advanced_label_correction_setting_start_btn.setEnabled(True)
                self.advanced_label_correction_datalist_global_clear_btn.setEnabled(True)
                self.imageSelectorComboBox.setEnabled(True)
        elif mode == LABEL_CORRECTION_DATALIST:  # Directory add
            file_dialog = QtWidgets.QFileDialog()
            file_dialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
            file_dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            file_dialog.findChild(QtWidgets.QListView, 'listView').setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection)
            file_dialog.findChild(QtWidgets.QTreeView, 'treeView').setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection)

            if file_dialog.exec_():
                bases = file_dialog.selectedFiles()
                new_paths = []
                # For each selected folder, search for data.hdr files
                for base in bases:
                    for hdr in glob.glob(f"{base}/**/data.hdr", recursive=True):
                        path = hdr.replace("\\", "/").rsplit("/data.hdr", 1)[0]
                        if path not in self.adv_data_list_info:
                            new_paths.append(path)

                base_row = len(self.adv_data_list_info)
                self.advanced_label_correction_datalist_tableview.setRowCount(
                    base_row + len(new_paths))

                for i, p in enumerate(new_paths):
                    r = base_row + i
                    # Add index and path info to table
                    idx_item = self.create_obj(r, obj_type="item", obj_list=str(r))
                    path_item = self.create_obj(r, obj_type="item", obj_list=p)
                    toggle_widget = self.create_obj(r, obj_type="widget", obj_list=["toggle:"])
                    self.advanced_label_correction_datalist_tableview.setItem(r, 0, idx_item)
                    self.advanced_label_correction_datalist_tableview.setItem(r, 1, path_item)
                    self.advanced_label_correction_datalist_tableview.setCellWidget(r, 2, toggle_widget["widget"])
                    toggle_widget["toggle"].setChecked(True)
                    self.adv_data_list_info[p] = {
                        "idx": r,
                        "use": True,
                        "obj_idx": idx_item,
                        "obj_path": path_item,
                        "obj_set": toggle_widget,
                        "wrongProcess": False
                    }
                    # Connect toggle event to handler
                    toggle_widget["toggle"].toggled.connect(
                        lambda ch, path=p, info=self.adv_data_list_info[p]:
                        self.toggle_event(idx=path, ch=ch, obj=info)
                    )
        elif mode == LABEL_CORRECTION_CLEAR:
            # Clear: reset table and internal info
            self.advanced_label_correction_datalist_tableview.clear()
            self.advanced_label_correction_datalist_tableview.setting_headerlabels(["Index", "Data", "Use"])
            self.adv_data_list_info.clear()
            """
            clear the image results tab data
            """
            self.imageSelectorComboBox.clear()
            self.rgb_image.clear()
            self.update_total_nonzero_pixel.clear()
            self.total_nonzero_pixel.clear()
            self.similarityHistData.clear()
            self.spectrumBeforeAfterData.clear()
            self.apply_threshold_change = False
            self.thr = -1
            self.reducedPixelValue.setText("0 (0 %)")  # Reset reduced pixel value display
            self.outputImageWidget.initPhoto()
            self.histPlotViewer.clear()
            self.beforeAfterPlotViewer.clear()
            self.thresholdLineEdit.setText("0")

    # --------------------------------------------------
    # Main Label Correction Processing (Worker Thread)
    # --------------------------------------------------
    def correct_label_mode(self) -> None:
        """
        @description : Sequentially process selected folders and run label correction.
                       (Called from worker thread)
        @author : Hyunsu Kim
        @history :
            1. Hyunsu Kim (2025.06.17)
              - add folder name to imageSelectorComboBox
              - Displaying the first result via update_signal
              - process parameter for image results tab
            2. Hyunsu Kim (2025.10.17)
              - add check variable for wrong process
              - Update to the first image among the data excluding the image in which the error occurred
            3. Hyunsu Kim (2026.02.09)
              - Add gen module instance creation for data loading
            4. Hyunsu Kim (2026.02.12)
              - Change the parameters sent to the signal to use the image results tab feature without using threads.
        """
        try:
            self.gen = gen_module()
            # Extract only the data paths with "Use" toggled on
            data_path_list = [
                key for key, val in self.adv_data_list_info.items()
                if val["obj_set"]["toggle"].isChecked()
            ]
            self.wrongProcess = [False for _ in range(len(data_path_list))]
            if not data_path_list:
                raise Exception("No data selected for processing. Please check 'Use' toggles.")

            # Process each folder
            for pathIndex, data_path in enumerate(data_path_list):
                if self.interrupt_:
                    self.string_signal.emit("\nProcess interrupted by user.\n")
                    break
                header = f"\n{'=' * 100}\nProcessing folder: {data_path}\n{'=' * 100}"
                self.string_signal.emit(header)
                self.correct_data(data_path, pathIndex=pathIndex, gen=self.gen)
                # Add to combo box after processing folder
                if self.wrongProcess[pathIndex] == False and self.imageSelectorComboBox.findText(data_path.split("/")[-1]) == -1:
                    self.imageSelectorComboBox.addItem(data_path.split("/")[-1])
                    self.adjust_combo_box_width()
                if self.wrongProcess[pathIndex]:
                    self.adv_data_list_info[data_path]["wrongProcess"] = True
                if self.interrupt_:
                    self.string_signal.emit("\nProcess interrupted by user after folder process.\n")
                    break

            if not self.interrupt_:
                self.string_signal.emit(f"\n{'-' * 50}\nProcessing Complete!\n{'-' * 50}")
                # Displaying the first result via update_signal
                for data_path, info in self.adv_data_list_info.items():
                    if info["wrongProcess"] == False and self.imageSelectorComboBox.findText(data_path.split("/")[-1]) != -1:
                        data_name = data_path.split("/")[-1]
                        self.update_signal.emit(self.updateImage[data_name], data_name)
                        self.thresholdLineEdit.setText("0")  # Reset threshold input
                        break
        except Exception as e:
            self.string_signal.emit(f"\nError Occurred: {str(e)}\n{'-' * 50}\n")

    def correct_data(self, data_path: str, threshold = -1, pathIndex = -1, gen=None):
        """
        @description : Load hyperspectral data and perform label correction.
        @author : Hyunsu Kim
        @parameters :
             - data_path: Path to the folder containing hyperspectral data
             - threshold: Similarity threshold to use (-1 to use default from UI)
             - pathIndex: Index of the data path in the processing list
             - gen: gen_module instance for data loading
        @history :
            1. Hyunsu Kim (2025.06.17) : add process parameter for image select box
            2. Hyunsu Kim (2025.10.17) : Set wrongProcess to True if an error occurs during the process
            3. Hyunsu Kim (2026.02.09) : 
                - Modify to use gen module instance for data loading
                - Improving how features work using clustering
            4. Hyunsu Kim (2026.02.12) :
                - Change the variable to use the image results tab feature without using threads.
        """
        try:
            # data load, kmeans fit, find closet pixels, calculate similarity, update label & save results, finish
            totalSteps = 6 
            # number of clusters for k-means
            clusters = self.header_dict_[5]["obj_set"]["spinbox"].value()
            cal_on = self.header_dict_[2]["obj_set"]["toggle"].isChecked()
            cal_rate = self.header_dict_[3]["obj_set"]["spinbox"].value()
            data_name = data_path.split("/")[-1]
            self.data[data_name] = gen.load_data(data_path, calibration=cal_on, calibration_rate=cal_rate)
            width, height, _ = self.data[data_name].shape
            if self.data[data_name] is None:
                self.wrongProcess[pathIndex] = True
                self.string_signal.emit(f"  - Data loading failed for {data_path}.\n")
                return

            # Load label as a 2D map (width, height)
            if os.path.isfile(data_path + "/label.npy"):
                self.label[data_name] = np.load(data_path + "/label.npy")
            else:
                # Initialize empty label map (width, height)
                self.label[data_name] = np.zeros((width, height), dtype=np.int16)

            if np.isin(self.label[data_name], NORMAL_LABELS).any() == False:
                self.wrongProcess[pathIndex] = True
                self.string_signal.emit(f"  - No reference pixels found in {data_name}. Skip.\n")
                return
            if np.where(self.label[data_name] >= DATA_ABNORMAL)[0].size > 0:
                self.wrongProcess[pathIndex] = True
                self.string_signal.emit(f"  - abnormal pixels found in {data_name}. Skip.\n")
                return
            self.total_nonzero_pixel[data_name] = np.count_nonzero(self.label[data_name])
            self.rgb_image[data_name], self.normalLabelColor[data_name] = self.load_rgb_data(data_path)  # create an RGB image based on the label for visualization
            self.updateImage[data_name] = self.rgb_image[data_name].copy()  # Store a copy of the original RGB image for updates
            if self.interrupt_:
                self.wrongProcess[pathIndex] = True
                self.string_signal.emit("  - Process interrupted before starting.\n")
                return

            method = self.header_dict_[0]["obj_set"]["combobox"].currentText()  # String: similarity method
            # If no threshold is specified, use spinbox value
            if threshold != -1:
                thr = threshold
            else:
                thr = self.header_dict_[1]["obj_set"]["spinbox"].value()     # Float: similarity threshold
            self.string_signal.emit(f"  - Similarity = {method}, Threshold = {thr}")
            curStep = 1
            self.progress_signal.emit(int(curStep / totalSteps * 100))

            refData = self.data[data_name][np.where(self.label[data_name] >= 1)] # (N_ref, B), spectra of reference pixels
            coords = np.argwhere((self.label[data_name] >= 1)) # (N_ref, 2), coordinates of reference pixels
            self.refLabel[data_name] = coords[:, 0] * height + coords[:, 1]  # (N_ref,), flat indices of reference pixels

            kmeans = KMeans(init="k-means++", n_clusters=clusters, random_state=self.randomSeed).fit(refData)

            if self.interrupt_:
                self.wrongProcess[pathIndex] = True
                self.string_signal.emit("  - Process interrupted during k-means fitting.\n")
                return
            
            curStep = 2
            self.progress_signal.emit(int(curStep / totalSteps * 100))
            dists = kmeans.transform(refData)
            labels = kmeans.predict(refData)
            closetPixels = []
            for idx in range(clusters):
                idxCluster = np.where(labels == idx)[0]
                closet = idxCluster[np.argmin(dists[idxCluster, idx])]
                closetPixels.append(closet)
            closetPixel = refData[closetPixels]
            
            if self.interrupt_:
                self.wrongProcess[pathIndex] = True
                self.string_signal.emit("  - Process interrupted during finding closest pixels.\n")
                return

            curStep = 3
            self.progress_signal.emit(int(curStep / totalSteps * 100))

            self.similarity[data_name] = np.zeros((width * height), dtype=np.float32)  # (width*height,), flattened similarity map
            dists = self.calculate_similarity(closetPixel, refData, mode=method)
            self.similarity[data_name][self.refLabel[data_name]] = np.max(dists, axis=0)  # Fill similarity scores for reference pixels

            if self.interrupt_:
                self.wrongProcess[pathIndex] = True
                self.string_signal.emit("  - Process interrupted during similarity calculation.\n")
                return

            curStep = 4
            self.progress_signal.emit(int(curStep / totalSteps * 100))

            labelAfterRemoval = self.label[data_name].copy()
            labelAfterRemoval[np.where(self.similarity[data_name].reshape(width, height) >= thr)] = 0          # Final label update: set label=0 for all removed pixels
            self.update_total_nonzero_pixel[data_name] = np.count_nonzero(labelAfterRemoval) # Update the number of non-zero pixels in the label after process processing
            
            self.updateImage[data_name][np.where(labelAfterRemoval > 0)] = self.normalLabelColor[data_name]
            # Save histogram of similarity scores (based on initially labeled pixels)
            self.similarityHistogram(
                data_name=data_name,
                similarityFlat=self.similarity[data_name],
                labeledFlatIdx=self.refLabel[data_name],
                method=method,
                thr=thr
            )

            # Save before/after distribution (similarity score distribution of labeled pixels)
            self.similarityBeforeAfterDistribution(
                data_name=data_name,
                before=self.data[data_name][np.where(self.label[data_name] > 0)],
                after=self.data[data_name][np.where(labelAfterRemoval > 0)],
                method=method
            )

            if self.interrupt_:
                self.wrongProcess[pathIndex] = True
                self.string_signal.emit("  - Process interrupted during label update.\n")
                return
            
            curStep = 5
            self.progress_signal.emit(int(curStep / totalSteps * 100))
            if not self.interrupt_:
                # Prevent saving labels and outputting status messages when updating in the image results tab
                if self.apply_threshold_change == False:
                    curStep = totalSteps
                    self.progress_signal.emit(int(curStep / totalSteps * 100))
                    if self.header_dict_[4]["obj_set"]["combobox"].currentText() == "Create":
                        np.save(data_path + f"/label_similarity_{method}_{thr}.npy", labelAfterRemoval)
                    else:
                        np.save(data_path + "/label.npy", labelAfterRemoval)

                self.workingDone[data_path] = True
                self.string_signal.emit("  - Folder processing completed.\n")
            else:
                # Prevent outputting status messages when updating in the image results tab
                if self.apply_threshold_change == False:
                    self.wrongProcess[pathIndex] = True
                    self.string_signal.emit("  - Folder processing interrupted.\n")
        except Exception as e:
            self.wrongProcess[pathIndex] = True
            self.string_signal.emit(f"  - Error during processing: {str(e)}\n")

    # --------------------------------------------------
    # Similarity Computation Function
    # --------------------------------------------------
    def calculate_similarity(self, refs, targets, mode):
        """
        @description : Compute similarity matrix (R x N) between reference (refs) and target (targets) spectra.
        @author : Hyunsu Kim
        @parameters :
            refs: Array of reference spectra (R, B)
            targets: Array of target spectra (N, B)
            mode: One of "Area", "Cosine", "SAM", "L2", "Chebyshev", "Canberra", "Jeffrey"
        """
        eps = 1e-10  # Small constant for numerical stability
        # 1) Area mode: Sum of absolute differences between spectra, normalized
        if mode == "Area":
            # Broadcast refs and targets to (R, N, B) for batch difference computation
            diff = np.abs(refs[:, None, :] - targets[None, :, :])  # data shape : (R, N, B)
            max_ = np.maximum(refs[:, None, :], targets[None, :, :])  # data shape : (R, N, B)
            max_vals = np.max(max_, axis=-1)  # data shape : (R, N)
            max_ = max_vals * refs.shape[1] 
            # Sum over bands, normalize, invert, and scale to [0, 100]
            sim = (1 - diff.sum(-1) / max_) * 100.0  # data shape : (R, N)
            return sim

        # 2) Cosine mode: Cosine similarity between spectra
        if mode == "Cosine":
            # Scale cosine value to [0, 1] and apply exponential to emphasize sharp transitions
            similarity = cosine_similarity(refs, targets)
            return similarity * 100.0
        
        # 3) SAM mode: Spectral Angle Mapper similarity
        if mode == "SAM":
            refs_norm = refs / (np.linalg.norm(refs, axis=1, keepdims=True) + eps)   # data shape : (R, B)
            tgt_norm = targets / (np.linalg.norm(targets, axis=1, keepdims=True) + eps)  # data shape : (N, B)
            cos_theta = np.matmul(refs_norm, tgt_norm.T)  # data shape : (R, N)
            cos_theta = np.clip(cos_theta, -1.0, 1.0)
            theta = np.arccos(cos_theta)
            max_theta = np.pi / 2
            ang = 1.0 - (theta / max_theta)
            return ang * 100.0

        # 3) L2 mode: Euclidean distance similarity
        if mode == "L2":
            # Use cdist for fast pairwise L2 computation (R, N)
            dist = cdist(refs, targets, metric='euclidean')
            # Define max possible distance from band count and data range
            maxd = np.sqrt(np.sum(np.maximum(refs[:, None, :], targets[None, :, :]) ** 2, axis=2))
            # Normalize and invert to get similarity in [0, 100]
            return ((1 - dist / maxd)) * 100.0

        # 4) Chebyshev mode: Maximum absolute band difference (L-infinity norm)
        if mode == "Chebyshev":
            # Take maximum absolute difference across bands (R, N)
            dist = np.max(np.abs(refs[:, None, :] - targets[None, :, :]), axis=2)
            max_dist = np.max(np.maximum(refs[:, None, :], targets[None, :, :]), axis=2)
            return ((1 - dist / max_dist)) * 100.0

        # 5) Canberra mode: Sum of per-band |x-y|/(|x|+|y|) differences
        if mode == "Canberra":
            num = np.abs(refs[:, None, :] - targets[None, :, :])         # data shape : (R, N, B)
            den = refs[:, None, :] + targets[None, :, :]  # data shape : (R, N, B)
            canb = np.sum(num / den, axis=-1)   
            max_d = np.max(np.maximum(np.abs(refs[:, None, :]) / (refs[:, None, :] + targets[None, :, :]), np.abs(targets[None, :, :]) / (refs[:, None, :] + targets[None, :, :])), axis=-1)
            B = refs.shape[1]
            # Canberra distance per pair lies in [0, B]. Normalize to [0,1] and invert to similarity.
            dist = canb / (max_d * B) # data shape : (R, N)
            sim = (1.0 - dist) * 100.0                         # similarity in [0, 100]
            return sim

        # 6) Jeffrey mode: Symmetric KL divergence similarity
        if mode == "Jeffrey":
            # Normalize spectra as probability distributions
            p_exp = refs[:, None, :]  # data shape : (R, 1, B)
            q_exp = targets[None, :, :]  # data shape : (1, N, B)
            # Jeffreys divergence: KL(p||q) + KL(q||p) for each (R, N) pair
            kl_pq = p_exp * np.log((p_exp + eps) / (q_exp + eps))
            kl_qp = q_exp * np.log((q_exp + eps) / (p_exp + eps))
            jdiv = np.sum(kl_pq + kl_qp, axis=-1)  # data shape : (R, N)
            max_jdiv = np.max(kl_pq + kl_qp, axis=-1)
            # Divergence → similarity in [0, 100] without extra weight parameter
            sim = (1.0 - jdiv / (max_jdiv * refs.shape[1])) * 100.0
            return sim

        # Raise error if unknown mode
        raise ValueError(f"Unknown similarity mode: {mode}")
    
    def similarityHistogram(
        self,
        data_name: str,
        similarityFlat: np.ndarray,
        labeledFlatIdx: np.ndarray,
        method: str,
        thr: float,
        bins: int = 100,
    ) -> None:
        """
        @description : Save histogram of similarity scores for analysis.
        @author : Hyunsu Kim
        @parameters :
            data_name: Dataset display name
            similarityFlat: Flattened similarity scores (width*height,)
            labeledFlatIdx: Flat indices for pixels considered (e.g., initially label>=1). If None, uses all pixels.
            method: Similarity metric name
            thr: Threshold used
            bins: Number of histogram bins in [min(values), max(values)]
        """
        values = similarityFlat[labeledFlatIdx]

        # Build histogram data based on actual range
        vmin = np.min(values)
        vmax = np.max(values)
        if vmax == vmin:
            # Avoid zero-width bins
            vmax = vmin + 1e-6

        edges = np.linspace(vmin, vmax, bins + 1, dtype=np.float32)
        counts, binEdges = np.histogram(values, bins=edges)

        # Save data for live PyQtGraph plot
        centers = (binEdges[:-1] + binEdges[1:]) / 2.0
        self.similarityHistData[data_name] = {
            "centers": centers,
            "counts": counts,
            "vmin": vmin,
            "vmax": vmax,
            "thr": thr,
            "method": str(method),
        }

    def similarityBeforeAfterDistribution(
        self,
        data_name: str,
        before: np.ndarray,
        after: np.ndarray,
        method: str
    ) -> None:
        """
            @description : Save median and p5–p95 band spectrum comparison (Before vs After).
            @author : Hyunsu Kim
            @parameters :
                data_name: Dataset display name
                before: Spectra of pixels before removal (N_before, B)
                after: Spectra of pixels after removal (N_after, B)
                method: Similarity metric name
            @history :
                1. Hyunsu Kim (2026.02.12) : Modified to use percentile and median instead of standard deviation to properly analyze indicators.
        """
        bands = np.arange(before.shape[1], dtype=np.float32)

        # Robust summary for multi-modal / heavy-tail distributions
        medianBefore = np.median(before, axis=0)
        p05Before, p95Before = np.percentile(before, [5, 95], axis=0)

        # after can be empty (all pixels removed). In that case, plot BEFORE only.
        medianAfter = None
        p05After = None
        p95After = None
        if after is not None and after.size > 0:
            medianAfter = np.median(after, axis=0)
            p05After, p95After = np.percentile(after, [5, 95], axis=0)

        self.spectrumBeforeAfterData[data_name] = {
            "bands": bands,
            "medianBefore": medianBefore,
            "p05Before": p05Before,
            "p95Before": p95Before,
            "medianAfter": medianAfter,
            "p05After": p05After,
            "p95After": p95After,
            "method": str(method),
        }

    def load_rgb_data(self, data_path):
        """
        @description : Load RGB image from given folder and apply color according to label
        @author : Hyunsu Kim
        @parameters :
            data_path: Folder path where data is saved
        @history :
                1. Hyunsu Kim (2026.02.12) : Modified to load RGB image and normal label color for using image results tab
        """
        rgb_data_name = 'image_calibration.png'
        if rgb_data_name not in os.listdir(data_path):
            rgb_data_name = 'image.png'
        rgb_data = cv2.imread(data_path + "/" + rgb_data_name, cv2.IMREAD_COLOR)

        with open(data_path + "/data.json", "r") as f:
            data_rgb_info = json.load(f)
        label_info = data_rgb_info["label_info"]
        normalLabelColor = label_info[str(NORMAL_LABELS[1])]["label_color"]
        
        return rgb_data, normalLabelColor

    def update_rgb_image(self, rgb_image=None, data_name=None):
        """
        @description : Update RGB image and reduced pixel value in the outputImagewidget
        @author : Hyunsu Kim
        @parameters :
            data_name: Name of the data being processed
            rgb_image: RGB image data to be displayed
        @history :
            1. Hyunsu Kim (2026.02.09) : Add the analysis result of the selected data
            2. Hyunsu Kim (2026.02.12) : ADD the parameter to use the image results tab feature without using threads.
        """
        reduced_pixel = self.total_nonzero_pixel[data_name] - self.update_total_nonzero_pixel[data_name]
        self.reducedPixelValue.setText(f"{reduced_pixel} ({reduced_pixel / self.total_nonzero_pixel[data_name] * 100:.2f} %)")
        self.outputImageWidget.updatePhoto(QtGui.QPixmap(QtGui.QImage(rgb_image, rgb_image.shape[1], \
                                                                      rgb_image.shape[0], QtGui.QImage.Format_RGB888)), True)

        # Update diagnostics plots for the selected dataset
        self.updateAnalysisPlots(data_name)


    def updateAnalysisPlots(self, data_name: str):
        """
            @description : Update analysis plots (similarity histogram and before/after spectrum)
            @author : Hyunsu Kim
            @parameters :
                data_name: Name of the data being processed
            @history :
                1. Hyunsu Kim (2026.02.12) :
                    - Remove unnecessary if statements and Use Constants for plot colors
        """
        # --- Similarity histogram (PyQtGraph) ---
        histPlot = getattr(self, "histPlotViewer", None)
        if histPlot is not None:
            histPlot.clear()
            hist = self.similarityHistData.get(data_name)
            width = float(hist["centers"][1] - hist["centers"][0])
            bar = pg.BarGraphItem(
                x=hist["centers"],
                height=hist["counts"],
                width=width * 0.95,
                brush=pg.mkBrush(HISTOGRAM_BAR_BRUSH_COLOR),
                pen=pg.mkPen(HISTOGRAM_BAR_PEN_COLOR, width=1),
            )
            histPlot.addItem(bar)

            thr = hist.get("thr", None)
            if thr is not None:
                histPlot.addItem(
                    pg.InfiniteLine(
                        pos=float(thr),
                        angle=90,
                        pen=pg.mkPen(HISTOGRAM_BAR_THR_COLOR, width=2),
                    )
                )

            vmin = float(hist.get("vmin", float(np.min(hist["centers"]))))
            vmax = float(hist.get("vmax", float(np.max(hist["centers"]))))
            histPlot.setXRange(vmin, vmax)
            ymax = float(np.max(hist["counts"]))
            histPlot.setYRange(0.0, max(1.0, ymax * 1.05))

        # --- Spectrum before/after (PyQtGraph) ---
        specPlot = getattr(self, "beforeAfterPlotViewer", None)
        if specPlot is not None:
            specPlot.clear()
            spec = self.spectrumBeforeAfterData.get(data_name)
            # legend (re-create if missing)
            if getattr(specPlot.plotItem, "legend", None) is None:
                specPlot.addLegend(labelTextColor=pg.mkColor("w"))
            else:
                specPlot.plotItem.legend.clear()
            if spec is not None:
                bands = np.asarray(spec.get("bands", []), dtype=np.float32)

            beforePen = pg.mkPen(pg.mkColor(DISTRIBUTION_BEFORE_PEN_COLOR))
            afterPen = pg.mkPen(pg.mkColor(DISTRIBUTION_AFTER_PEN_COLOR))
            beforeBrush = pg.mkBrush(DISTRIBUTION_BEFORE_BRUSH_COLOR)
            afterBrush = pg.mkBrush(DISTRIBUTION_AFTER_BRUSH_COLOR)
            beforeMedianPen = pg.mkPen(pg.mkColor(DISTRIBUTION_BEFORE_MEDIAN_COLOR), width=2)
            afterMedianPen = pg.mkPen(pg.mkColor(DISTRIBUTION_AFTER_MEDIAN_COLOR), width=2)

            # BEFORE
            medB = spec.get("medianBefore", None)
            p05B = spec.get("p05Before", None)
            p95B = spec.get("p95Before", None)
            
            medB = np.asarray(medB, dtype=np.float32)
            p05B = np.asarray(p05B, dtype=np.float32)
            p95B = np.asarray(p95B, dtype=np.float32)
            upperCurveB = specPlot.plot(bands, p95B, pen=beforePen)
            lowerCurveB = specPlot.plot(bands, p05B, pen=beforePen)
            specPlot.addItem(pg.FillBetweenItem(upperCurveB, lowerCurveB, brush=beforeBrush))
            specPlot.plot(bands, medB, pen=beforeMedianPen, name="Before median")

            # AFTER (can be None if all pixels removed)
            medA = spec.get("medianAfter", None)
            p05A = spec.get("p05After", None)
            p95A = spec.get("p95After", None)
            if medA is not None and p05A is not None and p95A is not None:
                medA = np.asarray(medA, dtype=np.float32)
                p05A = np.asarray(p05A, dtype=np.float32)
                p95A = np.asarray(p95A, dtype=np.float32)
                upperCurveA = specPlot.plot(bands, p95A, pen=afterPen)
                lowerCurveA = specPlot.plot(bands, p05A, pen=afterPen)
                specPlot.addItem(pg.FillBetweenItem(upperCurveA, lowerCurveA, brush=afterBrush))
                specPlot.plot(bands, medA, pen=afterMedianPen, name="After median")

            specPlot.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)
        
    def resizeEvent(self, e):
        """
            @description : Handle window resize events; PyQtGraph auto-manages view, so no manual adjustment needed.
            @author : Hyunsu Kim
        """
        super().resizeEvent(e)
        # PyQtGraph plots auto-manage their view; nothing required here.
        
    def apply_threshold(self):
        """
        @description : Apply threshold to the selected hyperspectral data
        @author : Hyunsu Kim
        @history :
            1. Hyunsu Kim (2025.10.17) : Add check for use toggle value in data list and process success check
            2. Hyunsu Kim (2026.02.12) : Add calculations and variables to update the image results tab using existing data without threads.
            3. Hyunsu Kim (2026.03.13) : Correct the if statement to check labelAfterRemoval > 0
        """
        try:
            self.apply_threshold_change = True
            threshold = float(self.thresholdLineEdit.text())
            data_path = ""
            if threshold < 0:
                threshold = 0
            elif threshold > 100:
                threshold = 100
            self.thresholdLineEdit.setText(str(threshold))
            for key, value in self.adv_data_list_info.items():
                data_name = key.split("/")[-1]
                if data_name == self.imageSelectorComboBox.currentText() and value["wrongProcess"] == False:
                    labelAfterRemoval = self.label[data_name].copy()
                    updateImage = self.rgb_image[data_name].copy()
                    labelAfterRemoval[np.where(self.similarity[data_name].reshape(labelAfterRemoval.shape[0], labelAfterRemoval.shape[1]) >= threshold)] = 0
                    self.update_total_nonzero_pixel[data_name] = np.count_nonzero(labelAfterRemoval)
                    self.similarityHistData[data_name]["thr"] = threshold
                    medianAfter = None
                    p05After = None
                    p95After = None
                    if np.any(labelAfterRemoval > 0):
                        medianAfter = np.median(self.data[data_name][np.where(labelAfterRemoval > 0)], axis=0)
                        p05After, p95After = np.percentile(self.data[data_name][np.where(labelAfterRemoval > 0)], [5, 95], axis=0)
                    self.spectrumBeforeAfterData[data_name]["medianAfter"] = medianAfter
                    self.spectrumBeforeAfterData[data_name]["p05After"] = p05After
                    self.spectrumBeforeAfterData[data_name]["p95After"] = p95After
                    updateImage[np.where(labelAfterRemoval > 0)] = self.normalLabelColor[data_name]
                    self.update_signal.emit(updateImage, data_name)
            return True
        except:
            return False

# ======================================================
# MAIN EXECUTION
# ======================================================
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = advanced_label_correction_Form()
    ui.show()
    sys.exit(app.exec_())
