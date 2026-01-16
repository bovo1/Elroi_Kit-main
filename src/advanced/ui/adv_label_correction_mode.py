import os
import glob
import math
import concurrent.futures

import numpy as np
import torch
import json
from torch.cuda.amp import autocast
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
import spectral
from utils.viewer import Display_viewer
import cv2

from constants.constants import LABEL_CORRECTION_MODE_WORKER_1, LABEL_CORRECTION_MODE_WORKER_2, LABEL_CORRECTION_START, \
LABEL_CORRECTION_STOP, LABEL_CORRECTION_CLEAR, LABEL_CORRECTION_DATALIST, LABEL_CORRECTION_THRESHOLD, LABEL_IGNORED

from utils.worker import Threading_Worker
from qtwidgets import AnimatedToggle
from advanced.stylesheet.stylesheet_adv_label_correction_mode import stylesheet

# Replace autocast with nullcontext if CUDA/AMP is unavailable
# FP16 autocasting is only available with CUDA
if not torch.cuda.is_available():  
    from contextlib import nullcontext 
    autocast = nullcontext

# ======================================================
# SIGNAL CLASS
# ======================================================
class SignalString(QtCore.QObject):
    """
    @description : Signal class for transmitting string messages and progress updates
    @author : JiHoon Jung
    @history : 
        1. Hyunsu Kim(2025.06.13) : Added update_signal for image results tab updates 
    """
    string_signal = QtCore.pyqtSignal(str)   # For status messages
    progress_signal = QtCore.pyqtSignal(int) # For progress bar updates
    update_signal = QtCore.pyqtSignal(str)   # For image results tab updates

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
        @author : JiHoon Jung
        @parameters :
            Sync: synchronization object (default None)
            lang: language setting (default None)
        """
        super().__init__()
        # 1) Initialize signals and worker
        self._initialize_signals(Sync, lang)
        # 2) Initialize internal parameters and state
        self._initialize_variables()
        # 3) Create UI widgets
        self._initialize_ui(self)
        # 4) Setup layout
        self._initialize_layouts()
        # 5) Connect signals and slots
        self._connect_signals()
        # 6) Populate parameter table
        self._populate_table()

        # Thread pool and device setup for background data loading
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        # Use GPU if available, else CPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Show form if executed as main module
        if __name__ == "__main__":
            self.show()

    def _initialize_signals(self, Sync, lang):
        """
        @description : Initialize and connect thread worker and signal objects
        @author : JiHoon Jung
        @parameters :
            Sync: synchronization object
            lang: language setting
        @history :
            1. Hyunsu Kim : Add thread worker to use in image results tab
        """
        self.Sync = Sync
        self.lang = lang
        # Threading_Worker for background execution
        self.worker_1 = Threading_Worker()
        self.worker_2 = Threading_Worker()
        # Connect thread complete callback
        self.worker_1.output.connect(lambda : self._on_thread_complete(mode = LABEL_CORRECTION_MODE_WORKER_1))
        self.worker_2.output.connect(lambda : self._on_thread_complete(mode = LABEL_CORRECTION_MODE_WORKER_2))

        # Create signals for status and progress updates
        self.signal_ = SignalString()
        self.string_signal = self.signal_.string_signal
        self.progress_signal = self.signal_.progress_signal
        self.update_signal = self.signal_.update_signal
        # Connect signal handlers
        self.string_signal.connect(self.update_status)
        self.progress_signal.connect(self._update_progress)
        self.update_signal.connect(self.update_rgb_image)

    def _initialize_variables(self):
        """
        @description : Initialize UI parameters and internal variables
        @author : JiHoon Jung
        @history :
            1. Hyunsu Kim(2025.06.13) : Added variables for image results tab
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
                "obj_list": ["spinbox:0,100,0"]},
            2: {"type": "Calibration",
                "tip": ["label:3. Calibration"],
                "value": [True],
                "obj_list": ["toggle:"]},
            3: {"type": "Calibration Ratio",
                "tip": ["label:4. Calibration Ratio"],
                "value": [1.0],
                "obj_list": ["spinbox:0.0,1.0,1.0"]},
            4: {"type": "Label Source",
                "tip": ["label:5. Label Source"],
                "value": ["Create"],
                "obj_list": ["combobox:Create,Overwrite"]},
        }
        self.adv_data_list_info = {}  # Selected data list info
        self.worker_id = -1           # Current worker ID
        self.worker_id2 = -1          # Worker ID for image results tab
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
        self.wrong_process = False

    # --------------------------------------------------
    # UI Widget Creation and Style Setup
    # --------------------------------------------------
    def _initialize_ui(self, MainWindow):
        """
        @description : Create widgets and containers needed for MainWindow
        @author : JiHoon Jung
        @parameters :
            MainWindow: top-level widget object
        @history :
            1. Hyunsu Kim(2025.06.13) : Add image results tab widget and related widgets
            2. Hyunsu Kim(2025.09.04) : enable drag & drop inside the image display widget
            3. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        MainWindow.setObjectName("adv_setting_form")
        MainWindow.resize(840, 640)
        MainWindow.setWindowTitle("Advanced Setting")
        MainWindow.setStyleSheet(stylesheet)  # Custom CSS stylesheet

        # Main horizontal/vertical layouts
        self.advanced_label_correction_main_horizon = QtWidgets.QHBoxLayout(MainWindow)
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
        self.advanced_label_correction_datalist_tableview = QtWidgets.QTableWidget()
        self.advanced_label_correction_datalist_tableview.setColumnCount(3)
        self.advanced_label_correction_datalist_tableview.setRowCount(4)
        self.lang.set("advanced", "advanced_label_correction_main", "advanced_label_correction_datalist_tableview", self.advanced_label_correction_datalist_tableview)
        header = self.advanced_label_correction_datalist_tableview.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.advanced_label_correction_datalist_tableview.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.advanced_label_correction_datalist_tableview.setDragEnabled(False)
        self.advanced_label_correction_datalist_tableview.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        vheader = self.advanced_label_correction_datalist_tableview.verticalHeader()
        vheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        vheader.hide()

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
        self.advanced_label_correction_datalist_global_horizon.addWidget(
            self.advanced_label_correction_datalist_global_search_btn)
        self.advanced_label_correction_datalist_global_horizon.addStretch()
        self.advanced_label_correction_datalist_global_horizon.addWidget(
            self.advanced_label_correction_datalist_global_clear_btn)

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

        self.ResultControlWidget = QtWidgets.QWidget()
        self.ResultControlWidget.setObjectName("ResultControlWidget")

        self.ResultControlLayout = QtWidgets.QHBoxLayout(self.ResultControlWidget)
        self.ResultControlLayout.setObjectName("ResultControlLayout")

        # Image selection controller
        self.ImageSelectorMainWidget = QtWidgets.QWidget()
        self.ImageSelectorMainWidget.setObjectName("ImageSelectorMainWidget")

        self.ImageSelectorMainLayout = QtWidgets.QHBoxLayout(self.ImageSelectorMainWidget)
        self.ImageSelectorMainLayout.setObjectName("ImageSelectorMainLayout")

        self.ImageSelectorComboBox = QtWidgets.QComboBox()
        self.ImageSelectorComboBox.setObjectName("ImageSelectorComboBox")

        self.advanced_label_correction_image_groupbox_HorizontalLine = QtWidgets.QFrame()
        self.advanced_label_correction_image_groupbox_HorizontalLine.setObjectName("advanced_label_correction_image_groupbox_HorizontalLine")
        self.advanced_label_correction_image_groupbox_HorizontalLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.advanced_label_correction_image_groupbox_HorizontalLine.setFrameShadow(QtWidgets.QFrame.Sunken)

        # Vertical line (Image selection controller <-> Pred map controller)
        self.ResultControlVerticalLine1 = QtWidgets.QFrame()
        self.ResultControlVerticalLine1.setObjectName("ResultControlVerticalLine1")
        self.ResultControlVerticalLine1.setFrameShape(QtWidgets.QFrame.VLine)
        self.ResultControlVerticalLine1.setFrameShadow(QtWidgets.QFrame.Sunken)

        # Threshold controller
        self.ThresholdMainWidget = QtWidgets.QWidget()
        self.ThresholdMainWidget.setObjectName("ThresholdMainWidget")

        self.ThresholdMainLayout = QtWidgets.QHBoxLayout(self.ThresholdMainWidget)
        self.ThresholdMainLayout.setObjectName("ThresholdMainLayout")
        
        self.ThresholdLabel = QtWidgets.QLabel()
        self.ThresholdLabel.setObjectName("ThresholdLabel")
        self.lang.set("advanced", "advanced_label_correction_main", "ThresholdLabel", self.ThresholdLabel)

        self.ThresholdLineEdit = QtWidgets.QLineEdit()
        self.ThresholdLineEdit.setObjectName("ThresholdLineEdit")

        intValidator = QtGui.QIntValidator(0, 100)
        self.ThresholdLineEdit.setValidator(intValidator)

        self.ThresholdButton = QtWidgets.QPushButton()
        self.ThresholdButton.setObjectName("ThresholdButton")
        self.ThresholdButton.setCheckable(True)
        self.ThresholdButton.setEnabled(False)  # Initially disabled until threshold is set
        self.lang.set("advanced", "advanced_label_correction_main", "ThresholdButton", self.ThresholdButton)

        # Reduced Pixel controller
        self.ReducedPixelMainWidget = QtWidgets.QWidget()
        self.ReducedPixelMainWidget.setObjectName("ReducedPixelMainWidget")

        self.ReducedPixelMainLayout = QtWidgets.QHBoxLayout(self.ReducedPixelMainWidget)
        self.ReducedPixelMainLayout.setObjectName("ReducedPixelMainLayout")
        self.ReducedPixelLabel = QtWidgets.QLabel()
        self.ReducedPixelLabel.setObjectName("ReducedPixelLabel") 
        self.lang.set("advanced", "advanced_label_correction_main", "ReducedPixelLabel", self.ReducedPixelLabel)

        self.ReducedPixelValue = QtWidgets.QLabel("0 (0 %)")
        self.ReducedPixelValue.setObjectName("ReducedPixelValue")  

        # image display widget
        self.OutputImageWidget = Display_viewer(usescrollbar=False)
        # enable drag & drop inside the image display widget
        self.OutputImageWidget.updateDrag(True)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        # Custom progress bar style
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                color: white;
                border: 1px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #778899;
            }
        """)


    # --------------------------------------------------
    # Layout Configuration
    # --------------------------------------------------
    def _initialize_layouts(self):
        """
        @description : Arrange created widgets in the proper layouts
        @author : JiHoon Jung
        @history :
            1. Hyunsu Kim(2025.06.13) : Add image results tab layout and widgets, modify status widget layout
            2. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        # Assign vertical layout to "Setting" groupbox
        self.advanced_label_correction_setting_groupbox.setLayout(self.advanced_label_correction_setting_vertical)
        # Add Start/Stop buttons to horizontal layout
        self.advanced_label_correction_setting_horizon.addWidget(self.advanced_label_correction_setting_start_btn)
        self.advanced_label_correction_setting_horizon.addWidget(self.advanced_label_correction_setting_stop_btn)

        # Add search buttons and table to "Data List" groupbox
        self.advanced_label_correction_datalist_vertical.addLayout(
            self.advanced_label_correction_datalist_global_horizon)
        self.advanced_label_correction_datalist_vertical.addWidget(
            self.advanced_label_correction_datalist_tableview)
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

        # Image results tab widget settings
        self.ResultControlLayout.addWidget(self.ImageSelectorMainWidget)
        self.ResultControlLayout.addWidget(self.ResultControlVerticalLine1)
        self.ResultControlLayout.addWidget(self.ThresholdMainWidget)
        self.ResultControlLayout.addWidget(self.ReducedPixelMainWidget)
        self.ThresholdMainLayout.addWidget(self.ThresholdLabel)
        self.ThresholdMainLayout.addWidget(self.ThresholdLineEdit)
        self.ThresholdMainLayout.addWidget(self.ThresholdButton)
        self.ReducedPixelMainLayout.addWidget(self.ReducedPixelLabel)
        self.ReducedPixelMainLayout.addWidget(self.ReducedPixelValue)
        self.ImageSelectorMainLayout.addWidget(self.ImageSelectorComboBox)
        self.advanced_label_correction_image_groupbox_Layout.addWidget(self.ResultControlWidget, 0, QtCore.Qt.AlignLeft)
        self.advanced_label_correction_image_groupbox_Layout.addWidget(self.advanced_label_correction_image_groupbox_HorizontalLine)

        # Placing the status window and image results window in the final main layout
        self.advanced_label_correction_status_mainwidgetLayout.addWidget(self.advanced_label_correction_status_groupbox)
        self.advanced_label_correction_image_groupbox_Layout.addWidget(self.OutputImageWidget)
        self.advanced_label_correction_image_widget_Layout.addWidget(self.advanced_label_correction_image_groupbox)
        self.advanced_label_correction_image_widget_Layout.setContentsMargins(0, 0, 0, 0)
        self.advanced_label_correction_main_horizon.addLayout(self.advanced_label_correction_main_vertical)
        self.advancedMain.addTab(self.advanced_label_correction_status_mainwidget, "Status")
        self.advancedMain.addTab(self.advanced_label_correction_image_widget, "Image results")
        self.lang.set("advanced", "advanced_label_correction_main", "statusTab", self.advancedMain)
        self.lang.set("advanced", "advanced_label_correction_main", "imageResultTab", self.advancedMain)
        self.advanced_label_correction_main_horizon.addWidget(self.advancedMain)

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

    # --------------------------------------------------
    # Signal-Slot Connections
    # --------------------------------------------------
    def _connect_signals(self):
        """
        @description : Connect buttons and other widgets to their event handlers
        @author : JiHoon Jung
        @history :
            1. Hyunsu Kim(2025.06.13) : Add connections for image results tab widgets
        """
        self.advanced_label_correction_datalist_global_search_btn.clicked.connect(
            lambda: self._on_datalist_event(mode=LABEL_CORRECTION_DATALIST))
        self.advanced_label_correction_datalist_global_clear_btn.clicked.connect(
            lambda: self._on_datalist_event(mode=LABEL_CORRECTION_CLEAR))
        self.advanced_label_correction_setting_start_btn.clicked.connect(
            lambda: self._on_button_event(mode=LABEL_CORRECTION_START))
        self.advanced_label_correction_setting_stop_btn.clicked.connect(
            lambda: self._on_button_event(mode=LABEL_CORRECTION_STOP))
        self.ImageSelectorComboBox.activated.connect(lambda: self.update_rgb_image(self.ImageSelectorComboBox.currentText()))
        self.ThresholdButton.clicked.connect(lambda: self._on_button_event(mode=LABEL_CORRECTION_THRESHOLD))

    # --------------------------------------------------
    # Parameter Table Creation and Initialization
    # --------------------------------------------------
    def _populate_table(self):
        """
        @description : Create widgets and items for parameter settings and set initial state
        @author : JiHoon Jung
        @history :
            1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        for idx, info in self.adv_model_info.items():
            # Create tooltip(label) and parameter setting widgets
            self.header_dict_[idx] = {
                "obj_tip": self._create_widget(idx, obj_type="widget", obj_list=info["tip"]),
                "obj_set": self._create_widget(idx, obj_type="widget", obj_list=info["obj_list"])
            }
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
        calibration_toggle.toggled.connect(lambda state: self._on_toggle_event(idx=2, ch=state))

        # Set initial value and signal connection for "Calibration Ratio" spinbox
        ratio_spinbox = self.header_dict_[3]["obj_set"]["spinbox"]
        ratio_spinbox.setDecimals(2)
        ratio_spinbox.setValue(round(self.adv_model_info[3]["value"][0], 2))
        ratio_spinbox.setSingleStep(0.01)
        ratio_spinbox.valueChanged.connect(lambda val: self._on_value_change(idx=3, value=round(val, 2)))


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
    # Widget Creation Helper
    # --------------------------------------------------
    def _create_widget(self, idx, obj_type="widget", obj_list=None):
        """
        @description : Create widgets or table items as specified by type
        @author : JiHoon Jung
        @parameters :
            idx: index of the widget to create
            obj_type: "widget" or "item"
            obj_list: list of widget type and parameter info
        """
        if obj_list is None:
            obj_list = ["button:test"]
        result = {}
        if obj_type == "item":
            # Table item
            item = QtWidgets.QTableWidgetItem(obj_list)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            return item

        # Composite widget: add multiple components to a HBox layout
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        for spec in obj_list:
            obj, val = spec.split(":")
            if obj == "button":
                btn = QtWidgets.QPushButton(val)
                btn.setObjectName(f"{idx}_btn")
                result["button"] = btn
                layout.addWidget(btn)

            elif obj == "toggle":
                toggle = AnimatedToggle(
                    pulse_checked_color="transparent",
                    pulse_unchecked_color="transparent"
                )
                toggle.setObjectName(f"{idx}_toggle")
                toggle.setFixedWidth(100)
                result["toggle"] = toggle
                layout.addWidget(toggle)

            elif obj == "spinbox":
                try:
                    minv, maxv, curv = list(map(int, val.split(",")))
                    sb = QtWidgets.QSpinBox()
                    sb.setRange(minv, maxv)
                    sb.setValue(curv)
                    sb.setFixedWidth(100)
                    sb.setAlignment(QtCore.Qt.AlignCenter)
                    sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
                    result.setdefault("spinbox", []).append(sb)
                    layout.addWidget(sb)
                except ValueError:
                    minv, maxv, curv = list(map(float, val.split(",")))
                    dsb = QtWidgets.QDoubleSpinBox()
                    dsb.setRange(minv, maxv)
                    dsb.setValue(curv)
                    dsb.setFixedWidth(100)
                    dsb.setDecimals(2)
                    dsb.setSingleStep(0.01)
                    dsb.setAlignment(QtCore.Qt.AlignCenter)
                    result["spinbox"] = dsb
                    layout.addWidget(dsb)
            
            elif obj == "label":
                lbl = QtWidgets.QLabel(val)
                lbl.setObjectName(f"{idx}_lbl")
                result["label"] = lbl
                layout.addWidget(lbl)
            
            elif obj == "lineedit":
                le = QtWidgets.QLineEdit(val)
                le.setReadOnly(True)
                le.setMinimumWidth(350)
                le.setAlignment(QtCore.Qt.AlignCenter)
                result["lineedit"] = le
                layout.addWidget(le)

            elif obj == "combobox":
                items = val.split(",")
                cb = QtWidgets.QComboBox()
                cb.addItems(items)
                cb.setFixedWidth(100)
                cb.setEditable(True)
                cb.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
                cb.lineEdit().setReadOnly(True)
                result["combobox"] = cb
                layout.addWidget(cb)
        widget.setLayout(layout)
        result["widget"] = widget
        return result

    # --------------------------------------------------
    # Toggle Event Handling (Calibration Mode & Data List "Use" Toggle)
    # --------------------------------------------------
    def _on_toggle_event(self, idx, ch, obj=None):
        """
        @description : Called when a toggle widget is changed; handles calibration mode and data list usage toggle.
        @author : JiHoon Jung
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
    def _on_value_change(self, idx, value):
        """
        @description : Called when a spinbox value is changed; updates internal variable.
        @author : JiHoon Jung
        @parameters :
            idx: Index of the changed spinbox
            value: New value
        """
        if self.signal_sw and self.adv_model_info[idx]["value"][0] != value:
            self.signal_sw = False
            self.adv_model_info[idx]["value"][0] = value
            self.signal_sw = True

    # --------------------------------------------------
    # Data List Event Handling (Search/Clear)
    # --------------------------------------------------
    def _on_datalist_event(self, mode):
        """
        @description : Handles events for searching/clearing the data list.
        @author : JiHoon Jung
        @parameters :
            mode: 0 for add folder, 1 for clear list
        @history :
            1. Hyunsu Kim(2025.06.13) : Added mode parameter to handle image results tab updates and modify constants
            2. Hyunsu Kim(2025.06.17) : clear the image results tab data when clearing the data list
        """
        if mode == LABEL_CORRECTION_DATALIST:  # Directory add
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
                    idx_item = self._create_widget(r, obj_type="item", obj_list=str(r))
                    path_item = self._create_widget(r, obj_type="item", obj_list=p)
                    toggle_widget = self._create_widget(r, obj_type="widget", obj_list=["toggle:"])
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
                        "wrong_process": False
                    }
                    # Connect toggle event to handler
                    toggle_widget["toggle"].toggled.connect(
                        lambda ch, path=p, info=self.adv_data_list_info[p]:
                        self._on_toggle_event(idx=path, ch=ch, obj=info)
                    )
        else:
            # Clear: reset table and internal info
            self.advanced_label_correction_datalist_tableview.clear()
            self.advanced_label_correction_datalist_tableview.setRowCount(4)
            self.advanced_label_correction_datalist_tableview.setHorizontalHeaderLabels(
                ["Index", "Data", "Use"])
            self.adv_data_list_info.clear()
            """
               clear the image results tab data
            """
            self.ImageSelectorComboBox.clear()
            self.rgb_image.clear()
            self.update_total_nonzero_pixel.clear()
            self.total_nonzero_pixel.clear()
            self.apply_threshold_change = False
            self.thr = -1
            self.worker_id2 = -1
            self.ReducedPixelValue.setText("0 (0 %)")  # Reset reduced pixel value display
            self.OutputImageWidget.initPhoto()
            self.ThresholdLineEdit.setText("0")

    # --------------------------------------------------
    # Status Update and Progress Bar Handling
    # --------------------------------------------------
    def update_status(self, string_):
        """
        @description : Append string to the status output pane.
        @author : JiHoon Jung
        @parameters :
            string_: String to output
        """
        try:
            msg = f"{float(string_):.2f}" if string_.replace('.', '', 1).isdigit() else string_
        except ValueError:
            msg = string_
        self.advanced_label_correction_status_textedit.appendPlainText(msg)

    def _update_progress(self, value):
        """
        @description : Update the progress bar value.
        @author : JiHoon Jung
        @parameters :
            value: Progress bar value (0~100)
        """
        self.progress_bar.setValue(value)

    # --------------------------------------------------
    # Restore UI State After Worker Thread Completion
    # --------------------------------------------------
    def _on_thread_complete(self, mode):
        """
        @description : Restore UI state after worker thread completes.
        @author : JiHoon Jung
        @parameters :
            output: Result of thread work
        @history :
            1. Hyunsu Kim(2025.06.13) : Added mode parameter to handle image results tab updates
        """
        if mode == LABEL_CORRECTION_MODE_WORKER_1:
            self.worker_id = -1
            self.advanced_label_correction_setting_start_btn.toggle()
            self.advanced_label_correction_setting_start_btn.setEnabled(True)
            self.advanced_label_correction_setting_stop_btn.setEnabled(False)
            self.advanced_label_correction_setting_groupbox.setEnabled(True)
            self.advanced_label_correction_datalist_groupbox.setEnabled(True)
            self.ImageSelectorComboBox.setEnabled(True)
            self.ThresholdButton.setEnabled(True)
            self.progress_signal.emit(0)
            self.progress_bar.hide()
        # Update UI when image results function operation is completed
        elif mode == LABEL_CORRECTION_MODE_WORKER_2:
            self.ThresholdButton.toggle()
            self.ThresholdButton.setEnabled(True)
            self.advanced_label_correction_setting_start_btn.setEnabled(True)
            self.advanced_label_correction_datalist_global_clear_btn.setEnabled(True)
            self.ImageSelectorComboBox.setEnabled(True)
            self.worker_id2 = -1
            self.apply_threshold_change = False

    # --------------------------------------------------
    # Start/Stop Button Event Handling
    # --------------------------------------------------
    def _on_button_event(self, mode):
        """
        @description : Handle Start/Stop button click events.
        @author : JiHoon Jung
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
        """
        if mode == LABEL_CORRECTION_START:  # Start
            # Warn if work is already running
            if self.worker_id != -1:
                QtWidgets.QMessageBox.information(
                    self,
                    self.lang.get(
                        "advanced", "advanced_label_correction_main", "advanced_label_correction_msg_warning_already_allocated_title"),
                        f"{self.lang.get('advanced', 'advanced_label_correction_main', 'advanced_label_correction_msg_warning_already_allocated_title')} Worker ID:{self.worker_id}"
                    )
                return

            # Disable UI buttons and groups
            self.interrupt_ = False
            self.advanced_label_correction_setting_start_btn.setEnabled(False)
            self.advanced_label_correction_setting_stop_btn.setEnabled(True)
            self.advanced_label_correction_setting_groupbox.setEnabled(False)
            self.advanced_label_correction_datalist_groupbox.setEnabled(False)
            self.ImageSelectorComboBox.clear()
            self.ImageSelectorComboBox.setEnabled(False)
            self.ThresholdButton.setEnabled(False)
            self.OutputImageWidget.initPhoto()
            self.ReducedPixelLabel.setText("Reduced Pixel : ")
            self.ReducedPixelValue.setText("0 (0 %)")
            self.advanced_label_correction_status_textedit.clear()

            # Print current parameter settings in the output window
            header = f"{self.mode}\n{self.dash * 30}"
            self.string_signal.emit(header)
            self.string_signal.emit("Parameter Setting\n")
            for idx, info in self.adv_model_info.items():
                param_type = info["type"]
                obj_set = self.header_dict_[idx]["obj_set"]
                if "spinbox" in obj_set:
                    val = obj_set["spinbox"]
                    val = val[0].value() if isinstance(val, list) else val.value()
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

            self.worker_1.staging(self._predict_label_mode)
            self.worker_id = self.worker_1.cur_id
            self.worker_1.start()
        elif mode == LABEL_CORRECTION_STOP: # Stop
            # Confirm stop with dialog
            if self._yes_no_message(
                self.lang.get("advanced", "advanced_label_correction_main", "advanced_label_correction_msg_stop_title"),
                self.lang.get("advanced", "advanced_label_correction_main", "advanced_label_correction_msg_stop_message")
            ):
                self.interrupt_ = True
                self.worker_id = -1
                self.advanced_label_correction_setting_start_btn.setEnabled(True)
                self.advanced_label_correction_setting_stop_btn.setEnabled(False)
                self.advanced_label_correction_setting_groupbox.setEnabled(True)
                self.advanced_label_correction_datalist_groupbox.setEnabled(True)
                if len(self.rgb_image):
                    data_name = next(iter(self.rgb_image.keys()))
                    self.OutputImageWidget.updatePhoto(QtGui.QPixmap(QtGui.QImage(self.rgb_image[data_name], self.rgb_image[data_name].shape[1], self.rgb_image[data_name].shape[0], QtGui.QImage.Format_RGB888)), True)
                self.string_signal.emit(f"\n{'-' * 50}\nProcess stopped by user.\n{'-' * 50}")
        # Image results function works when button is clicked
        elif mode == LABEL_CORRECTION_THRESHOLD:
            if self.worker_id2 == -1:
                self.interrupt_ = False
                self.advanced_label_correction_setting_start_btn.setEnabled(False)
                self.ImageSelectorComboBox.setEnabled(False)
                self.ThresholdButton.setEnabled(False)
                self.advanced_label_correction_datalist_global_clear_btn.setEnabled(False)
                self.worker_2.staging(self.apply_threshold)
                self.worker_id2 = self.worker_2.cur_id
                self.worker_2.start()
    # --------------------------------------------------
    # Yes/No Message Box Utility
    # --------------------------------------------------
    def _yes_no_message(self, title, message):
        """
        @description : Show a Yes/No message box and return the user's choice.
        @author : JiHoon Jung
        @parameters :
            title: Message box title
            message: Message box content
        """
        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Warning)  # Warning icon
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.No)
        msgbox.setWindowTitle(title)
        msgbox.setText(message)
        return msgbox.exec_() == QtWidgets.QMessageBox.Yes

    # --------------------------------------------------
    # Main Label Correction Processing (Worker Thread)
    # --------------------------------------------------
    def _predict_label_mode(self) -> None:
        """
        @description : Sequentially process selected folders and run label correction.
                       (Called from worker thread)
        @author : JiHoon Jung
        @history :
            1. Hyunsu Kim (2025.06.17)
              - add folder name to ImageSelectorComboBox
              - Displaying the first result via update_signal
              - process parameter for image results tab
            2. Hyunsu Kim (2025.10.17)
              - add check variable for wrong process
              - Update to the first image among the data excluding the image in which the error occurred
        """
        try:
            # Extract only the data paths with "Use" toggled on
            data_path_list = [
                key for key, val in self.adv_data_list_info.items()
                if val["obj_set"]["toggle"].isChecked()
            ]
            self.wrong_process = [False for _ in range(len(data_path_list))]
            if not data_path_list:
                raise Exception("No data selected for processing. Please check 'Use' toggles.")

            # Process each folder
            for pathIndex, data_path in enumerate(data_path_list):
                if self.interrupt_:
                    self.string_signal.emit("\nProcess interrupted by user.\n")
                    break
                header = f"\n{'=' * 100}\nProcessing folder: {data_path}\n{'=' * 100}"
                self.string_signal.emit(header)
                self._process_folder(data_path, pathIndex=pathIndex)
                # Add to combo box after processing folder
                if self.wrong_process[pathIndex] == False and self.ImageSelectorComboBox.findText(data_path.split("/")[-1]) == -1:
                    self.ImageSelectorComboBox.addItem(data_path.split("/")[-1])
                    self.adjust_combo_box_width()
                if self.wrong_process[pathIndex]:
                    self.adv_data_list_info[data_path]["wrong_process"] = True
                if self.interrupt_:
                    self.string_signal.emit("\nProcess interrupted by user after folder process.\n")
                    break

            if not self.interrupt_:
                self.string_signal.emit(f"\n{'-' * 50}\nProcessing Complete!\n{'-' * 50}")
                # Displaying the first result via update_signal
                for data_path, info in self.adv_data_list_info.items():
                    if info["wrong_process"] == False:
                        data_name = data_path.split("/")[-1]
                        self.signal_.update_signal.emit(data_name)
                        self.ThresholdLineEdit.setText("0")  # Reset threshold input
                        break
        except Exception as e:
            self.string_signal.emit(f"\nError Occurred: {str(e)}\n{'-' * 50}\n")

    def _process_folder(self, data_path: str, threshold = -1, pathIndex = -1) -> None:
        """
        @description : Load hyperspectral data and perform label correction.
        @author : JiHoon Jung
        @parameters :
            data_path: Path to the folder containing hyperspectral data
        @history :
            1. Hyunsu Kim (2025.06.17) : add process parameter for image select box
            2. Hyunsu Kim (2025.10.17) : Set wrong_process to True if an error occurs during the process
        """
        cal_on = self.adv_model_info[2]["value"][0]  # Calibration mode (on/off) for preprocessing the data
        cal_rate = self.adv_model_info[3]["value"][0]  # Calibration rate or parameter value
        data = self.load_hyperspectral_data(data_path, cal_on, cal_rate)  # Hyperspectral data data (H, W, B)
        if data is None:
            self.wrong_process[pathIndex] = True
            self.string_signal.emit(f"  - Data loading failed for {data_path}.\n")
            return

        label = self.load_or_initialize_label(data_path, data.shape[:2])  # 2D label mask (H, W)
        data_name = data_path.split("/")[-1]
        if label is None:
            self.wrong_process[pathIndex] = True
            return
        else: # Store non-zero number of labels
            if np.isin(label.cpu().numpy(), [1, 2]).any() == False:
                self.wrong_process[pathIndex] = True
                self.string_signal.emit(f"  - No reference pixels found in {data_name}. Skip.\n")
                return
            self.total_nonzero_pixel[data_name] = np.count_nonzero(label.cpu().numpy())

        H, W = label.shape                 # H: image height (pixels), W: image width (pixels)
        B = data.shape[-1]                 # B: number of spectral bands (channels) per pixel

        coords = torch.nonzero((label == 1) | (label == 2), as_tuple=False).to(self.device)
        # coords: (N_ref, 2), pixel coordinates (row, col) where label is 1 or 2 (reference pixels)
        if coords.numel() == 0:
            self.wrong_process = True
            self.string_signal.emit("  - No pixels with label 1/2. Skip.\n")
            return

        method = self.header_dict_[0]["obj_set"]["combobox"].currentText()  # String: similarity metric/method
        # If no threshold is specified, use spinbox value
        if threshold != -1:
            thr = threshold
        else:
            thr = self.header_dict_[1]["obj_set"]["spinbox"][0].value()     # Float: similarity threshold
        self.string_signal.emit(f"  - Similarity = {method}, Threshold = {thr}")
        self.progress_signal.emit(0)

        # Precompute all labeled pixels (label>=1) as coordinates and their flat indices for the whole process
        all_labeled_coords = torch.nonzero(label >= 1, as_tuple=False).to(self.device)  # (N_labeled, 2), all labeled pixels
        all_labeled_flat = all_labeled_coords[:, 0] * W + all_labeled_coords[:, 1]      # (N_labeled,), flat indices for labeled pixels
        marked_for_removal = torch.zeros(H * W, dtype=torch.bool, device=self.device)    # (H*W,), mask: True if pixel is to be removed
        data_flat = data.reshape(-1, B)          # (H*W, B), pixel spectra flattened for fast indexing
        label_flat = label.reshape(-1)           # (H*W,), 1D version of the label mask

        batch_size = 256                         # Number of reference pixels to process per batch
        total_refs = coords.size(0)              # Total number of reference pixels (label==1 or 2) 
        processed = 0                            # Counter for processed reference pixels

        while batch_size >= 8:
            try:
                for batch_start in range(0, total_refs, batch_size):
                    if self.interrupt_:
                        self.wrong_process = True
                        self.string_signal.emit("  - User interrupt detected. Stopping batch.\n")
                        return
                    torch.cuda.empty_cache()

                    batch_end = min(batch_start + batch_size, total_refs)  # End index for this batch (exclusive) 
                    
                    ref_batch = coords[batch_start:batch_end]              # (batch, 2), reference coordinates for this batch
                    ref_flat_idx = ref_batch[:, 0] * W + ref_batch[:, 1]   # (batch,), flat indices for batch refs

                    valid_ref_mask = ~marked_for_removal[ref_flat_idx]     # (batch,), True for valid refs not yet removed
                    ref_batch = ref_batch[valid_ref_mask]                  # (<=batch, 2), valid ref coordinates
                    ref_flat_idx = ref_flat_idx[valid_ref_mask]            # (<=batch,), valid ref indices

                    if ref_batch.numel() == 0:
                        processed += (batch_end - batch_start)
                        self.progress_signal.emit(int(processed / total_refs * 100))
                        continue

                    ref_indices = torch.arange(batch_start, batch_end, device=self.device)[valid_ref_mask]
                    # ref_indices: (<=batch,), batch indices of valid references in this batch
                    min_idx = ref_indices[-1] + 1 if ref_indices.numel() > 0 else batch_end
                    # min_idx: Int, for slicing to avoid redundant comparisons (targets only after this index)

                    # === Target selection: only consider labeled pixels (label>=1) after min_idx, and not marked for removal ===
                    target_coords = all_labeled_coords[min_idx:]           # (N_target, 2), candidate target coordinates
                    tgt_flat_idx = all_labeled_flat[min_idx:]              # (N_target,), candidate target flat indices
                    valid_tgt_mask = ~marked_for_removal[tgt_flat_idx]     # (N_target,), True for valid targets
                    target_coords = target_coords[valid_tgt_mask]          # (N_valid_targets, 2), coordinates of valid targets
                    tgt_flat_idx = tgt_flat_idx[valid_tgt_mask]            # (N_valid_targets,), flat indices of valid targets

                    if target_coords.numel() == 0:
                        processed += (batch_end - batch_start)
                        self.progress_signal.emit(int(processed / total_refs * 100))
                        continue

                    ref_spectra = data_flat[ref_flat_idx]                  # (n_refs, B), spectra for current batch refs
                    target_spectra = data_flat[tgt_flat_idx]               # (n_targets, B), spectra for valid target pixels

                    if self.interrupt_:
                        self.wrong_process = True
                        self.string_signal.emit("  - User interrupt detected. Exiting before batch similarity.\n")
                        return

                    # Compute similarity between refs and targets
                    with autocast():
                        sim_ref_target = self.calculate_batch_similarity(ref_spectra, target_spectra, method)
                    # sim_ref_target: (n_refs, n_targets), similarity values

                    del_target_mask = torch.any(sim_ref_target >= thr, dim=0)  # (n_targets,), True if any ref is too similar
                    del_tgt_flat = tgt_flat_idx[del_target_mask]               # (n_del_targets,), indices to be marked for removal
                    marked_for_removal[del_tgt_flat] = True                   # Mark those targets for removal

                    # Intra-batch redundancy: remove refs in this batch that are too similar to each other
                    with autocast():
                        sim_ref_ref = self.calculate_batch_similarity(ref_spectra, ref_spectra, method)
                    # sim_ref_ref: (n_refs, n_refs), similarity between refs

                    R = sim_ref_ref.size(0)                                   # Number of references in this batch
                    if R > 1:
                        tri_i, tri_j = torch.triu_indices(R, R, offset=1, device=self.device)
                        # tri_i, tri_j: indices for upper triangle (no self-comparison)
                        sim_upper = sim_ref_ref[tri_i, tri_j]                # (num_upper,), upper triangle values
                        remove_pair_mask = sim_upper >= thr                  # (num_upper,), True if similarity is high
                        del_ref_j_indices = tri_j[remove_pair_mask]          # Indices in this batch of refs to remove
                        if del_ref_j_indices.numel() > 0:
                            unique_j = del_ref_j_indices.unique()            # Unique indices to avoid double marking
                            del_ref_flat = ref_flat_idx[unique_j]            # Final flat indices to mark for removal
                            marked_for_removal[del_ref_flat] = True

                    processed += (batch_end - batch_start)
                    self.progress_signal.emit(int(processed / total_refs * 100))

                break  # All batches processed

            except RuntimeError as e:
                if "out of memory" in str(e):
                    self.string_signal.emit(f"CUDA OOM detected at batch_size={batch_size}. Reducing batch size and retrying.")
                    batch_size //= 2
                    self.string_signal.emit(f"New batch_size set to {batch_size}.")
                    torch.cuda.empty_cache()
                    processed = 0
                    continue
                else:
                    raise e

        if batch_size < 8:
            self.wrong_process = True
            self.string_signal.emit("Batch size too small, stopping processing due to memory constraints.")
            return

        label_flat[marked_for_removal] = 0  # Final label update: set label=0 for all removed pixels
        self.update_total_nonzero_pixel[data_name] = np.count_nonzero(label_flat.cpu().numpy()) # Update the number of non-zero pixels in the label after process processing
        label_reshape = label_flat.reshape(H, W)                                                # Reshape the label back to its original 2D shape
        self.rgb_image[data_name] = self.load_rgb_data(data_path, label_reshape.cpu().numpy())  # create an RGB image

        if not self.interrupt_:
            # Prevent saving labels and outputting status messages when updating in the image results tab
            if self.apply_threshold_change == False:
                self.progress_signal.emit(100)
                self.save_label(data_path, label)
            self.string_signal.emit("  - Folder processing completed.\n")
        else:
            # Prevent outputting status messages when updating in the image results tab
            if self.apply_threshold_change == False:
                self.wrong_process = True
                self.string_signal.emit("  - Folder processing interrupted.\n")



    # --------------------------------------------------
    # Batch Similarity Computation Function
    # --------------------------------------------------
    def calculate_batch_similarity(self, refs: torch.Tensor, targets: torch.Tensor, mode: str) -> torch.Tensor:
        """
        @description : Compute similarity matrix (R x N) between reference (refs) and target (targets) spectra.
        @author : JiHoon Jung
        @parameters :
            refs: Tensor of reference spectra (R, B)
            targets: Tensor of target spectra (N, B)
            mode: One of "Area", "Cosine", "SAM", "L2", "Chebyshev", "Canberra", "Jeffrey"
        """
        eps = 1e-12  # Small constant for numerical stability
        # 1) Area mode: Sum of absolute differences between spectra, normalized
        if mode == "Area":
            # Broadcast refs and targets to (R, N, B) for batch difference computation
            diff = torch.abs(refs[:, None, :] - targets[None, :, :])  # (R, N, B)
            max_ = torch.maximum(refs[:, None, :], targets[None, :, :])  # (R, N, B)
            # Sum over bands, normalize, invert, and scale to [0, 100]
            sim = (1 - diff.sum(-1) / (max_.sum(-1).clamp_min(eps))) * 100.0  # (R, N)
            return sim

        # 2) Cosine/SAM mode: Cosine similarity or Spectral Angle Mapper (SAM)
        if mode in ["Cosine", "SAM"]:
            refs = refs.float()
            targets = targets.float()
            # Normalize each spectrum to unit norm
            refs_norm = refs / (torch.linalg.norm(refs, dim=1, keepdim=True) + eps)   # (R, B)
            tgt_norm = targets / (torch.linalg.norm(targets, dim=1, keepdim=True) + eps)  # (N, B)
            # Compute cosine similarity matrix, clamp for safe arccos
            cos_sim = torch.matmul(refs_norm, tgt_norm.T).clamp(-1.0, 1.0)  # (R, N)

            if mode == "Cosine":
                weight_cosine = 30.0  # Larger value increases sensitivity to small differences
                # Scale cosine value to [0, 1] and apply exponential to emphasize sharp transitions
                cos_scaled = (cos_sim + 1.0) / 2.0
                return (torch.exp(-weight_cosine * (1.0 - cos_scaled)) * 100.0)
            else:
                weight_sam = 11.0  # Higher value increases sensitivity for small angular differences
                # SAM: Use angle (arccos), normalized by pi, then exponentiate
                ang = torch.acos(cos_sim) / math.pi
                return (torch.exp(-weight_sam * ang) * 100.0)

        # 3) L2 mode: Euclidean distance similarity
        if mode == "L2":
            # Use cdist for fast pairwise L2 computation (R, N)
            dist = torch.cdist(refs, targets, p=2)  # (R, N)
            # Define max possible distance from band count and data range
            maxd = math.sqrt(refs.size(1)) * (targets.max() - targets.min() + eps)
            # Normalize and invert to get similarity in [0, 100]
            return ((1 - dist / maxd).clamp(0, 1)) * 100.0

        # 4) Chebyshev mode: Maximum absolute band difference (L-infinity norm)
        if mode == "Chebyshev":
            # Take maximum absolute difference across bands (R, N)
            dist = torch.amax(torch.abs(refs[:, None, :] - targets[None, :, :]), dim=2)
            maxd = targets.max() - targets.min() + eps
            return ((1 - dist / maxd).clamp(0, 1)) * 100.0

        # 5) Canberra mode: Sum of per-band |x-y|/(|x|+|y|) differences
        if mode == "Canberra":
            weight_canb = 2.0  # Sensitivity factor
            num = torch.abs(refs[:, None, :] - targets[None, :, :])         # (R, N, B)
            den = torch.abs(refs[:, None, :]) + torch.abs(targets[None, :, :]) + eps  # (R, N, B)
            canb = num.div(den).sum(-1)                                     # (R, N)
            B = refs.size(1)
            norm_canb = canb / B
            sim = torch.exp(-weight_canb * norm_canb).clamp(0, 1) * 100.0
            return sim

        # 6) Jeffrey mode: Symmetric KL divergence similarity
        if mode == "Jeffrey":
            weight = 100.0  # Higher value increases sensitivity to small divergences
            # Normalize spectra as probability distributions
            p = refs / (refs.sum(dim=1, keepdim=True) + eps)  # (R, B)
            q = targets / (targets.sum(dim=1, keepdim=True) + eps)  # (N, B)
            # Expand for (R, N, B) broadcasted computation
            p_exp = p[:, None, :]  # (R, 1, B)
            q_exp = q[None, :, :]  # (1, N, B)
            m = 0.5 * (p_exp + q_exp)  # (R, N, B)
            # KL(p||m) + KL(q||m) for each (R, N) pair
            kl_pm = (p_exp * torch.log((p_exp + eps) / (m + eps))).sum(-1)
            kl_qm = (q_exp * torch.log((q_exp + eps) / (m + eps))).sum(-1)
            jdiv = kl_pm + kl_qm
            # Exponential scaling, clamp, and convert to percentage
            return torch.exp(-weight * jdiv).clamp(0, 1) * 100.0

        # Raise error if unknown mode
        raise ValueError(f"Unknown similarity mode: {mode}")

    def load_rgb_data(self, data_path, label):
        """
        @description : Load RGB image from given folder and apply color according to label
        @author : Hyunsu Kim
        @parameters :
            data_path: Folder path where data is saved
            label: Label array to apply colors
        @history :
        """
        rgb_data_name = 'image_calibration.png'
        if rgb_data_name not in os.listdir(data_path):
            rgb_data_name = 'image.png'
        rgb_data = cv2.imread(data_path + "/" + rgb_data_name, cv2.IMREAD_COLOR)

        with open(data_path + "/data.json", "r") as f:
            data_rgb_info = json.load(f)
        label_info = data_rgb_info["label_info"]
        label_number = label_info.keys()
        for num in label_number:
            if int(num) == LABEL_IGNORED:
                continue
            indices = np.where(label == int(num))
            rgb_data[indices] = label_info[num]["label_color"]

        return rgb_data

    def update_rgb_image(self, data_name=None):
        """
        @description : Update RGB image and reduced pixel value in the OutputImagewidget
        @author : Hyunsu Kim
        @parameters :
            data_name: Name of the data being processed
        @history :
        """
        reduced_pixel = self.total_nonzero_pixel[data_name] - self.update_total_nonzero_pixel[data_name]
        self.ReducedPixelValue.setText(f"{reduced_pixel} ({reduced_pixel / self.total_nonzero_pixel[data_name] * 100:.2f} %)")
        self.OutputImageWidget.updatePhoto(QtGui.QPixmap(QtGui.QImage(self.rgb_image[data_name], self.rgb_image[data_name].shape[1], self.rgb_image[data_name].shape[0], QtGui.QImage.Format_RGB888)), True)
        
    def apply_threshold(self) -> None:
        """
        @description : Apply threshold to the selected hyperspectral data
        @author : Hyunsu Kim
        @history :
            1. Hyunsu Kim (2025.10.17) : Add check for use toggle value in data list and process success check
        """
        try:
            if self.worker_id2 == -1:
                return
            self.apply_threshold_change = True
            threshold = int(self.ThresholdLineEdit.text())
            if threshold < 0:
                threshold = 0
            elif threshold > 100:
                threshold = 100
            self.ThresholdLineEdit.setText(str(threshold))
            for key, value in self.adv_data_list_info.items():
                if value["idx"] == self.ImageSelectorComboBox.currentIndex() and value["use"] == True and value["wrong_process"] == False:
                    self._process_folder(key, threshold=threshold)
                    data_name = key.split("/")[-1]
                    self.signal_.update_signal.emit(data_name)
        except:
            self.string_signal.emit("  - Error occurred while applying threshold.\n")
            self._on_thread_complete(LABEL_CORRECTION_MODE_WORKER_2)
            return

    # --------------------------------------------------
    # Hyperspectral Data Loading and Calibration
    # --------------------------------------------------
    def load_hyperspectral_data(self, data_path, cal=True, rate=1.0):
        """
        @description : Load ENVI format hyperspectral data, perform calibration if requested, and return as Torch tensor.
        @author : JiHoon Jung
        @parameters :
            data_path: Path to folder containing the data
            cal: Whether to perform calibration (True/False)
            rate: Calibration scale factor
        """
        # Launch ENVI data loading in the background
        f = self.executor.submit(self.load_envi_data, data_path, "data.hdr", "data.raw")
        data = f.result()
        if data is None:
            return None

        if cal:
            # Load mean DARKREF and WHITEREF reference spectra and apply calibration
            dark = self.load_reference_data(data_path, "DARKREF")
            white = self.load_reference_data(data_path, "WHITEREF")
            if dark is not None and white is not None:
                data = self.calibrate_data(data, dark, white, rate)

        # Convert to Torch tensor and move to GPU (if available)
        return torch.from_numpy(data).float().pin_memory().to(self.device, non_blocking=True)

    def load_envi_data(self, base, hdr, raw):
        """
        @description : Open ENVI .hdr/.raw files and return as NumPy array.
        @author : JiHoon Jung
        @parameters :
            base: Path to data folder
            hdr: .hdr filename
            raw: .raw filename
        """
        try:
            img = spectral.io.envi.open(os.path.join(base, hdr), os.path.join(base, raw))
            # On first load, save wavelength info for later use
            if not hasattr(self, "wavelengths") or self.wavelengths is None:
                self.wavelengths = [float(w) for w in img.metadata.get("wavelength", [])]
            return img.load()
        except FileNotFoundError as e:
            self.string_signal.emit(f"Error loading data: {e}")
            return None

    def load_reference_data(self, base, name):
        """
        @description : Load the specified reference (DARKREF/WHITEREF) and return mean spectrum.
        @author : JiHoon Jung
        @parameters :
            base: Folder with reference files
            name: "DARKREF" or "WHITEREF"
        """
        ref = self.load_envi_data(base, f"{name}.hdr", f"{name}.raw")
        # If present, return mean spectrum across H/W (shape: B)
        return ref.mean(axis=0) if ref is not None else None

    @staticmethod
    def calibrate_data(data: np.ndarray, dark: np.ndarray, white: np.ndarray, rate: float):
        """
        @description : Apply reflectance calibration using dark and white reference spectra.
        @author : JiHoon Jung
        @parameters :
            data: Raw hyperspectral data (H, W, B)
            dark: DARKREF mean spectrum (B)
            white: WHITEREF mean spectrum (B)
            rate: Calibration scaling factor
        """
        # Normalize: (data - dark) / (white - dark), scale to [0, 4095]
        norm = (data - dark) / (white - dark)
        return np.clip(norm * 4095.0 * rate, 0, 4095.0).astype(np.float32)

    # --------------------------------------------------
    # Label Saving and Initialization Functions
    # --------------------------------------------------
    def save_label(self, data_path, label: torch.Tensor):
        """
        @description : Save or overwrite processed label file.
        @author : JiHoon Jung
        @parameters :
            data_path: Folder to save the label file
            label: Tensor to save
        @history :
            1. Hyeok Yoon(2025.10.31) : Modifying "if logic" compare string to index
        """
        mode = self.header_dict_[0]["obj_set"]["combobox"].currentText()
        thr = self.header_dict_[1]["obj_set"]["spinbox"][0].value()
        idx = self.header_dict_[4]["obj_set"]["combobox"].currentIndex() # get index not a string

        fname = f"label_similarity_{mode}_{thr}.npy"
        save_path = os.path.join(data_path, fname)

        # comparing index not a string
        if idx == 1: # Overwrite
            # Overwrite label.npy and notify
            np.save(os.path.join(data_path, "label.npy"), label.cpu().numpy())
            self.string_signal.emit("  - Label file overwritten at 'label.npy'.")
        else:  # Create new file if it doesn't already exist
            if os.path.exists(save_path):
                return
            np.save(save_path, label.cpu().numpy())
            self.string_signal.emit(f"  - Label file saved to '{save_path}'.")

    def load_or_initialize_label(self, data_path, shape):
        """
        @description : Load existing label file or initialize with zeros if not found.
        @author : JiHoon Jung
        @parameters :
            data_path: Folder containing label file
            shape: Shape of label to initialize (H, W)
        @history :
            1. Hyunsu Kim : Load label.npy directly if threshold change is applied
            2. Hyeok Yoon(2025.10.31) : Modifying "if logic" compare string to index
        """
        mode = self.header_dict_[0]["obj_set"]["combobox"].currentText()
        thr = self.header_dict_[1]["obj_set"]["spinbox"][0].value()
        idx = self.header_dict_[4]["obj_set"]["combobox"].currentIndex() # get index not a string

        fname = f"label_similarity_{mode}_{thr}.npy"
        save_path = os.path.join(data_path, fname)
        label_path = os.path.join(data_path, "label.npy")

        # If threshold change is applied, load label.npy directly
        if self.apply_threshold_change:
            return torch.tensor(np.load(label_path), device=self.device)

        # comparing index not a string
        if idx == 1: # Overwrite
            # Overwrite mode: prefer label.npy
            if os.path.exists(label_path):
                self.string_signal.emit(f"  - Found: {label_path}")
                return torch.tensor(np.load(label_path),
                                    device=self.device, requires_grad=False)
            else:
                self.string_signal.emit("  - No label.npy, initializing zeros.\n")
                return torch.zeros(shape, dtype=torch.int16, device=self.device)
        else:  # Create mode
            # If already processed, skip
            if os.path.exists(save_path):
                self.string_signal.emit(f"  - '{save_path}' already exists.\n")
                return torch.tensor(np.load(label_path),
                                    device=self.device)
            # If label.npy exists, load it
            if os.path.exists(label_path):
                self.string_signal.emit(f"  - Found: {label_path}")
                return torch.tensor(np.load(label_path),
                                    device=self.device, requires_grad=False)
            # Otherwise, initialize with zeros
            self.string_signal.emit("  - No existing label, initializing zeros.\n")
            return torch.zeros(shape, dtype=torch.int16, device=self.device)

    # --------------------------------------------------
    # On Close: Shutdown Thread Pool Executor
    # --------------------------------------------------
    def closeEvent(self, e):
        """
        @description : Called on window close; shuts down executor.
        @author : JiHoon Jung
        @parameters :
            e: Event object
        """
        self.executor.shutdown(wait=False)

# ======================================================
# MAIN EXECUTION
# ======================================================
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = advanced_label_correction_Form()
    ui.show()
    sys.exit(app.exec_())
