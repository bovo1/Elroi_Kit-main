"""
    ELROILAB Kit
    Copyright 2024. Elroilab All rights reserved.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from utils.worker import Threading_Worker
from qtwidgets import AnimatedToggle
import spectral
import numpy as np
import os
import torch
import glob
import math

from advanced.stylesheet.stylesheet_adv_pixel_based_labeling_mode import stylesheet
from utils.custom_ui import messageBox
from constants.constants import MESSAGE_BOX_INFORMATION, MESSAGE_BOX_CONFIRMATION, MESSAGE_BOX_WARNING


# ========================================================
# SIGNAL CLASS
# ========================================================
class SignalString(QtCore.QObject):
    """
    @description : Class that defines a string signal
    @author : JiHoon Jung
    """
    string_signal = QtCore.pyqtSignal(str)

# ========================================================
# MAIN WIDGET CLASS : advanced_pixel_based_labeling_Form
# ========================================================
class advanced_pixel_based_labeling_Form(QtWidgets.QWidget):
    """
    @description : Class that defines the advanced settings form for pixel-based labeling mode
    @author : JiHoon Jung
    """
    # ----------------------------------------------------
    # INITIALIZATION (SIGNALS, VARIABLES, UI, LAYOUT, CONNECTIONS)
    # ----------------------------------------------------
    def __init__(self, Sync=None, lang=None) -> None:
        """
        @description : Initializes the widget, UI, variables, and signals
        @author : JiHoon Jung
        @parameters :
            Sync: Synchronization object (default None)
            lang: Language setting (default None)
        """
        super().__init__()
        # 1) Initialize signals and worker
        self._initialize_signals(Sync, lang)
        # 2) Initialize internal variables and parameters
        self._initialize_variables()
        # 3) Create UI widgets
        self._initialize_ui(self)
        # 4) Arrange layouts
        self._initialize_layouts()
        # 5) Connect signals and slots
        self._connect_signals()
        # 6) Fill parameter table
        self._populate_table()

        # Show window if running standalone
        if __name__ == "__main__":
            self.show()

    def _initialize_signals(self, Sync, lang):
        """
        @description : Initializes and connects thread worker and signal object
        @author : JiHoon Jung
        @parameters :
            Sync: Synchronization object
            lang: Language setting
        """
        self.Sync = Sync  # Synchronization object (used as needed)
        self.lang = lang  # Language setting

        # Create worker for background tasks
        self.worker_1 = Threading_Worker()
        # When worker finishes, call _on_thread_complete
        self.worker_1.output.connect(self._on_thread_complete)

        # Create signal for status messages
        self.signal_ = SignalString()
        self.string_signal = self.signal_.string_signal
        # When signal is received, call update_status method
        self.string_signal.connect(self.update_status)

    def _initialize_variables(self):
        """
        @description : Initializes UI parameters and internal variables
        @author : JiHoon Jung
        """
        # Dictionary to store setting item widgets
        self.header_dict_ = {}

        # Labeling option index map
        # 0 : Similarity Mode
        # 1 : Similarity Threshold
        # 2 : Coordinate (COLUMN, ROW)
        # 3 : Labeling number
        # 4 : Calibration toggle
        # 5 : Calibration Ratio
        self.adv_model_info = {
            0: {
                "type": "Similarity Mode",
                "tip": ["label:1. Similarity Mode"],
                "value": ["Area"],
                "obj_list": ["combobox:Area,SAM,Cosine,L2,Chebyshev,Canberra,Jeffrey"]
            },
            1: {
                "type": "Similarity Threshold",
                "tip": ["label:2. Similarity Threshold"],
                "value": [1.0],
                "obj_list": ["spinbox:0,100,0"]
            },
            2: {
                "type": "Coordinate (COLUMN, ROW)",
                "tip": ["label:3. Coordinate (COLUMN, ROW)"],
                "value": [0, 0],
                "obj_list": ["spinbox:0,1,0", "spinbox:0,1,0"]
            },
            3: {
                "type": "Labeling number",
                "tip": ["label:4. Labeling number"],
                "value": [0],
                "obj_list": ["spinbox:0,9999999,0"]
            },
            4: {
                "type": "Calibration",
                "tip": ["label:5. Calibration"],
                "value": [True],
                "obj_list": ["toggle:"]
            },
            5: {
                "type": "Calibration Ratio",
                "tip": ["label:6. Calibration Ratio"],
                "value": [1.0],
                "obj_list": ["spinbox:0.0,1.0,1.0"]
            },
        }

        self.adv_data_list_info = {}  # Store data list information
        self.worker_id = -1           # Current worker ID
        self.dash = "-"               # Log separator
        self.mode = "Pixel-Based Labeling Mode"
        self.interrupt_ = False       # Interrupt flag
        self.signal_sw = True         # Internal signal switch control

    @pyqtSlot(dict)
    def _on_thread_complete(self, output):
        """
        @description : Called when the worker thread completes, updates UI and resets worker ID
        @author : JiHoon Jung
        @parameters :
            output: Output from the worker thread (not used here)
        """
        self.worker_id = -1
        # Untoggle Start button
        self.advanced_pixel_based_labeling_setting_start_btn.toggle()
        # Enable Start button, disable Stop button
        self.advanced_pixel_based_labeling_setting_start_btn.setEnabled(True)
        self.advanced_pixel_based_labeling_setting_stop_btn.setEnabled(False)
        # Enable settings and data list group boxes
        self.advanced_pixel_based_labeling_setting_groupbox.setEnabled(True)
        self.advanced_pixel_based_labeling_datalist_groupbox.setEnabled(True)

    # ----------------------------------------------------
    # UI CREATION & LAYOUT
    # ----------------------------------------------------
    def _initialize_ui(self, MainWindow):
        """
        @description : Creates the necessary widgets and layout containers for MainWindow
        @author : JiHoon Jung
        @parameters :
            MainWindow: Top-level widget object
        @history :
            1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """
        MainWindow.setObjectName("adv_setting_form")
        MainWindow.resize(840, 640)
        MainWindow.setWindowTitle("Advanced Setting")
        MainWindow.setStyleSheet(stylesheet)

        # Main horizontal and vertical layouts
        self.advanced_pixel_based_labeling_main_horizon = QtWidgets.QHBoxLayout(MainWindow)
        self.advanced_pixel_based_labeling_main_vertical = QtWidgets.QVBoxLayout()

        # Setting group box and layout
        self.advanced_pixel_based_labeling_setting_groupbox = QtWidgets.QGroupBox()
        self.advanced_pixel_based_labeling_setting_groupbox.setFixedWidth(933)
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_setting_groupbox", self.advanced_pixel_based_labeling_setting_groupbox)
        self.advanced_pixel_based_labeling_setting_vertical = QtWidgets.QVBoxLayout()

        # Data List group box and layout
        self.advanced_pixel_based_labeling_datalist_groupbox = QtWidgets.QGroupBox()
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_datalist_groupbox", self.advanced_pixel_based_labeling_datalist_groupbox)
        self.advanced_pixel_based_labeling_datalist_vertical = QtWidgets.QVBoxLayout()

        # Data list table
        self.advanced_pixel_based_labeling_datalist_tableview = QtWidgets.QTableWidget()
        self.advanced_pixel_based_labeling_datalist_tableview.setColumnCount(3)
        self.advanced_pixel_based_labeling_datalist_tableview.setRowCount(4)
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_datalist_tableview", self.advanced_pixel_based_labeling_datalist_tableview)
        hdr = self.advanced_pixel_based_labeling_datalist_tableview.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.advanced_pixel_based_labeling_datalist_tableview.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.advanced_pixel_based_labeling_datalist_tableview.setSelectionMode(
            QtWidgets.QAbstractItemView.NoSelection
        )
        vhdr = self.advanced_pixel_based_labeling_datalist_tableview.verticalHeader()
        vhdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        vhdr.hide()

        # “Search” / “Clear” buttons
        self.advanced_pixel_based_labeling_datalist_global_horizon = QtWidgets.QHBoxLayout()
        self.advanced_pixel_based_labeling_datalist_global_search_btn = QtWidgets.QPushButton()
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_datalist_global_search_btn", self.advanced_pixel_based_labeling_datalist_global_search_btn)
        self.advanced_pixel_based_labeling_datalist_global_clear_btn = QtWidgets.QPushButton()
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_datalist_global_clear_btn", self.advanced_pixel_based_labeling_datalist_global_clear_btn)

        # Unify button sizes
        self.advanced_pixel_based_labeling_datalist_global_search_btn.setFixedWidth(75)
        self.advanced_pixel_based_labeling_datalist_global_clear_btn.setFixedWidth(75)

        # Align: Search | (stretch) | Clear
        self.advanced_pixel_based_labeling_datalist_global_horizon.addWidget(
            self.advanced_pixel_based_labeling_datalist_global_search_btn
        )
        self.advanced_pixel_based_labeling_datalist_global_horizon.addStretch()
        self.advanced_pixel_based_labeling_datalist_global_horizon.addWidget(
            self.advanced_pixel_based_labeling_datalist_global_clear_btn
        )

        # Start/Stop buttons
        self.advanced_pixel_based_labeling_setting_horizon = QtWidgets.QHBoxLayout()
        self.advanced_pixel_based_labeling_setting_start_btn = QtWidgets.QPushButton()
        self.advanced_pixel_based_labeling_setting_start_btn.setCheckable(True)
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_setting_start_btn", self.advanced_pixel_based_labeling_setting_start_btn)
        self.advanced_pixel_based_labeling_setting_stop_btn = QtWidgets.QPushButton()
        self.advanced_pixel_based_labeling_setting_stop_btn.setEnabled(False)
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_setting_stop_btn", self.advanced_pixel_based_labeling_setting_stop_btn)

        # Status group box and text edit
        self.advanced_pixel_based_labeling_status_groupbox = QtWidgets.QGroupBox()
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_status_groupbox", self.advanced_pixel_based_labeling_status_groupbox)
        self.advanced_pixel_based_labeling_status_vertical = QtWidgets.QVBoxLayout()
        self.advanced_pixel_based_labeling_status_textedit = QtWidgets.QPlainTextEdit()
        self.advanced_pixel_based_labeling_status_textedit.setReadOnly(True)
        self.advanced_pixel_based_labeling_status_textedit.setUndoRedoEnabled(False)

    def _initialize_layouts(self):
        """
        @description : Arranges the created widgets in appropriate layouts
        @author : JiHoon Jung
        """
        # Configure “Setting” group
        self.advanced_pixel_based_labeling_setting_groupbox.setLayout(
            self.advanced_pixel_based_labeling_setting_vertical
        )
        # Add Start/Stop buttons to horizontal layout
        self.advanced_pixel_based_labeling_setting_horizon.addWidget(
            self.advanced_pixel_based_labeling_setting_start_btn
        )
        self.advanced_pixel_based_labeling_setting_horizon.addWidget(
            self.advanced_pixel_based_labeling_setting_stop_btn
        )

        # Configure “Data List” group
        self.advanced_pixel_based_labeling_datalist_vertical.addLayout(
            self.advanced_pixel_based_labeling_datalist_global_horizon
        )
        self.advanced_pixel_based_labeling_datalist_vertical.addWidget(
            self.advanced_pixel_based_labeling_datalist_tableview
        )
        self.advanced_pixel_based_labeling_datalist_groupbox.setLayout(
            self.advanced_pixel_based_labeling_datalist_vertical
        )

        # Configure “Status” group
        self.advanced_pixel_based_labeling_status_vertical.addWidget(
            self.advanced_pixel_based_labeling_status_textedit
        )
        self.advanced_pixel_based_labeling_status_groupbox.setLayout(
            self.advanced_pixel_based_labeling_status_vertical
        )

        # Place Setting, Data List, and Start/Stop in main vertical layout
        self.advanced_pixel_based_labeling_main_vertical.addWidget(
            self.advanced_pixel_based_labeling_setting_groupbox
        )
        self.advanced_pixel_based_labeling_main_vertical.addWidget(
            self.advanced_pixel_based_labeling_datalist_groupbox
        )
        self.advanced_pixel_based_labeling_main_vertical.addLayout(
            self.advanced_pixel_based_labeling_setting_horizon
        )
        
        # Place left vertical layout and right Status group box in main horizontal layout
        self.advanced_pixel_based_labeling_main_horizon.addLayout(
            self.advanced_pixel_based_labeling_main_vertical
        )
        self.advanced_pixel_based_labeling_main_horizon.addWidget(
            self.advanced_pixel_based_labeling_status_groupbox
        )


    # ----------------------------------------------------
    # SIGNAL CONNECTIONS
    # ----------------------------------------------------
    def _connect_signals(self):
        """
        @description : Connects button clicks and other events using signal-slot mechanism
        @author : JiHoon Jung
        """
        # Connect Data List search/clear button clicks
        self.advanced_pixel_based_labeling_datalist_global_search_btn.clicked.connect(
            lambda: self._on_datalist_event(mode=0)
        )
        self.advanced_pixel_based_labeling_datalist_global_clear_btn.clicked.connect(
            lambda: self._on_datalist_event(mode=1)
        )
        # Connect Start/Stop button clicks
        self.advanced_pixel_based_labeling_setting_start_btn.clicked.connect(
            lambda: self._on_button_event(mode=0)
        )
        self.advanced_pixel_based_labeling_setting_stop_btn.clicked.connect(
            lambda: self._on_button_event(mode=1)
        )

    # ----------------------------------------------------
    # PARAMETER TABLE & WIDGET MANAGEMENT
    # ----------------------------------------------------
    def _populate_table(self):
        """
        @description : Creates and places table items and widgets for parameter settings,
                       and sets the initial state of widgets as needed
        @author : JiHoon Jung
        @history :
            1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
        """

        for idx, info in self.adv_model_info.items():
            # Create tooltip (label) widget and setting (widget)
            self.header_dict_[idx] = {
                "obj_tip": self._create_widget(idx, obj_type="widget", obj_list=info["tip"]),
                "obj_set": self._create_widget(idx, obj_type="widget", obj_list=info["obj_list"])
            }
            # Arrange both widgets in a horizontal layout
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.setContentsMargins(3, 3, 3, 3)
            row_layout.addWidget(self.header_dict_[idx]["obj_tip"]["widget"])
            row_layout.addStretch()
            row_layout.addWidget(self.header_dict_[idx]["obj_set"]["widget"])
            self.advanced_pixel_based_labeling_setting_vertical.addLayout(row_layout)
        
        # Connect “Similarity Mode” combobox change signal
        self.header_dict_[0]["obj_set"]["combobox"].currentTextChanged.connect(
            lambda t: self._on_value_change(idx=0, value=t)
        )

        # Connect “Similarity Threshold” spinbox change signal
        self.header_dict_[1]["obj_set"]["spinbox"][0].valueChanged.connect(
            lambda v: self._on_value_change(idx=1, value=v)
        )

        # Connect two “Coordinate” spinbox change signals
        col_sb, row_sb = self.header_dict_[2]["obj_set"]["spinbox"]
        col_sb.valueChanged.connect(lambda v: self._on_value_change(idx=2, value=v))
        row_sb.valueChanged.connect(lambda v: self._on_value_change(idx=2, value=v))

        # Connect “Labeling number” spinbox change signal
        self.header_dict_[3]["obj_set"]["spinbox"][0].valueChanged.connect(
            lambda v: self._on_value_change(idx=3, value=v)
        )

        # Connect “Calibration” toggle signal
        cal_toggle = self.header_dict_[4]["obj_set"]["toggle"]
        cal_toggle.setChecked(self.adv_model_info[4]["value"][0])
        cal_toggle.toggled.connect(lambda ch: self._on_toggle_event(idx=4, ch=ch))

        # Connect “Calibration Ratio” double spinbox change signal
        cal_ratio_spin = self.header_dict_[5]["obj_set"]["spinbox"][0]
        if isinstance(cal_ratio_spin, QtWidgets.QDoubleSpinBox):
            cal_ratio_spin.setDecimals(2)
            cal_ratio_spin.setSingleStep(0.01)
            cal_ratio_spin.valueChanged.connect(
                lambda v: self._on_value_change(idx=5, value=round(v, 2))
            )

        # 1. similarity mode
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_similaritymode_label", self.header_dict_[0]["obj_tip"]["label"])

        # 2. similarity threshold
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_similaritythreshold_label", self.header_dict_[1]["obj_tip"]["label"])

        # 3. coordinate
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_coordinate_label", self.header_dict_[2]["obj_tip"]["label"])

        # 4. labeling number
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_labelnumber_label", self.header_dict_[3]["obj_tip"]["label"])

        # 5. calibration
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_calibration_label", self.header_dict_[4]["obj_tip"]["label"])

        # 6. calibration ratio
        self.lang.set("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_calibrationratio_label", self.header_dict_[5]["obj_tip"]["label"])

    def _create_widget(self, idx, obj_type="widget", obj_list=None):
        """
        @description : Creates a widget or table item depending on the specified type
        @author : JiHoon Jung
        @parameters :
            idx: Index of the widget to create
            obj_type: "widget" or "item"
            obj_list: List of widget types and parameter information
        """
        if obj_list is None:
            obj_list = ["button:test"]
        result = {}
        if obj_type == "item":
            # Create table item
            item = QtWidgets.QTableWidgetItem(obj_list)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            return item

        # Create composite widget (using HBoxLayout)
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        for spec in obj_list:
            obj, val = spec.split(":")
            if obj == "combobox":
                # Create combobox (e.g. for similarity mode selection)
                cb = QtWidgets.QComboBox()
                cb.addItems(val.split(","))
                cb.setEditable(True)
                cb.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
                cb.lineEdit().setReadOnly(True)
                cb.setFixedWidth(100)
                result["combobox"] = cb
                layout.addWidget(cb)

            elif obj == "spinbox":
                # Separate integer spinbox and double spinbox
                try:
                    mi, ma, cur = map(int, val.split(","))
                    sb = QtWidgets.QSpinBox()
                    sb.setRange(mi, ma)
                    sb.setValue(cur)
                except ValueError:
                    mi, ma, cur = map(float, val.split(","))
                    sb = QtWidgets.QDoubleSpinBox()
                    sb.setDecimals(2)
                    sb.setSingleStep(0.01)
                    sb.setRange(mi, ma)
                    sb.setValue(cur)
                sb.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
                sb.setFixedWidth(100)
                sb.setAlignment(QtCore.Qt.AlignCenter)
                result.setdefault("spinbox", []).append(sb)
                layout.addWidget(sb)

            elif obj == "toggle":
                # Use AnimatedToggle switch (e.g. for calibration toggle)
                tg = AnimatedToggle(
                    pulse_checked_color="transparent",
                    pulse_unchecked_color="transparent"
                )
                tg.setFixedWidth(100)
                result["toggle"] = tg
                layout.addWidget(tg)

            elif obj == "label":
                # Simple label
                lb = QtWidgets.QLabel(val)
                lb.setFixedWidth(lb.width() + 50)
                result["label"] = lb
                layout.addWidget(lb)

            elif obj == "button":
                # Standard button
                bt = QtWidgets.QPushButton(val)
                result["button"] = bt
                layout.addWidget(bt)

            elif obj == "lineedit":
                # Read-only line edit for things like file paths
                le = QtWidgets.QLineEdit(val)
                le.setReadOnly(True)
                le.setDragEnabled(True)
                le.setMinimumWidth(350)
                le.setAlignment(QtCore.Qt.AlignCenter)
                result["lineedit"] = le
                layout.addWidget(le)

        widget.setLayout(layout)
        result["widget"] = widget
        return result

    # ----------------------------------------------------
    # EVENT HANDLERS: VALUE CHANGE, TOGGLE, BUTTON, DATA LIST
    # ----------------------------------------------------
    def _on_value_change(self, idx, value):
        """
        @description : Called when a spinbox or combobox value changes, updates internal variable
        @author : JiHoon Jung
        @parameters :
            idx: Index of the changed setting
            value: New value or text
        """
        if not self.signal_sw:
            return
        self.signal_sw = False
        if idx == 2:
            # Save both coordinate values as one item
            col_val = self.header_dict_[2]["obj_set"]["spinbox"][0].value()
            row_val = self.header_dict_[2]["obj_set"]["spinbox"][1].value()
            self.adv_model_info[idx]["value"] = [col_val, row_val]
        else:
            # Other settings are saved in the first list element
            self.adv_model_info[idx]["value"][0] = value
        self.signal_sw = True

    def _on_toggle_event(self, idx, ch, obj=None):
        """
        @description : Called when a toggle widget changes, handles calibration mode toggle and data list "use" toggle
        @author : JiHoon Jung
        @parameters :
            idx: Index of toggled widget (4 for calibration mode)
            ch: Toggle state (True/False)
            obj: Data list item info (default None)
        """
        if idx == 4:
            # Calibration mode toggle
            self.adv_model_info[idx]["value"][0] = ch
        elif obj is not None:
            # Toggle whether a data list item is used
            obj["use"] = ch

    def _on_datalist_event(self, mode):
        """
        @description : Handles data list search/clear events
        @author : JiHoon Jung
        @parameters :
            mode: 0 for search, 1 for clear
        @note : If mode is 0, opens a file dialog to select directories containing hyperspectral data.
                If mode is 1, clears the current data list and resets the coordinate spinbox range.
        """
        if mode == 0:  # Search
            dlg = QtWidgets.QFileDialog()
            dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
            dlg.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            dlg.findChild(QtWidgets.QListView, "listView").setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )
            dlg.findChild(QtWidgets.QTreeView, "treeView").setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection
            )
            if dlg.exec_():
                bases = dlg.selectedFiles() # List of selected directories
                new_paths = [] # List to store new paths
                max_col, max_row = 0, 0
                for b in bases:
                    for hdr in glob.glob(f"{b}/**/data.hdr", recursive=True):
                        p = hdr.replace("\\", "/").rsplit("/data.hdr", 1)[0]
                        if p not in self.adv_data_list_info:
                            new_paths.append(p)
                            # **Get data shape from hdr file**
                            data_shape = self._get_data_shape_from_hdr(p) # (height, width, bands)
                            if data_shape:
                                c, r = data_shape[1], data_shape[0]
                                if c > max_col: max_col = c
                                if r > max_row: max_row = r
                ## **If no new paths found, show message**
                base_row = len(self.adv_data_list_info) # Current row count
                # **Clear existing data list if any**
                self.advanced_pixel_based_labeling_datalist_tableview.setRowCount(
                    base_row + len(new_paths)
                )
                # **If no new paths found, show message**
                for i, p in enumerate(new_paths): # New paths
                    r = base_row + i # Row index
                    idx_item = self._create_widget(r, obj_type="item", obj_list=str(r)) # Index item
                    path_item = self._create_widget(r, obj_type="item", obj_list=p) # Path item
                    toggle_widget = self._create_widget(r, obj_type="widget", obj_list=["toggle:"]) # Toggle widget
                    self.advanced_pixel_based_labeling_datalist_tableview.setItem(r, 0, idx_item) # Index
                    self.advanced_pixel_based_labeling_datalist_tableview.setItem(r, 1, path_item) # Path
                    self.advanced_pixel_based_labeling_datalist_tableview.setCellWidget(r, 2, toggle_widget["widget"]) # Toggle
                    toggle_widget["toggle"].setChecked(True) # Default to checked
                    # Store data list info
                    self.adv_data_list_info[p] = {
                        "idx": r, "use": True,
                        "obj_idx": idx_item, "obj_path": path_item,
                        "obj_set": toggle_widget,
                    }
                    # **Connect toggle signal to handler**
                    toggle_widget["toggle"].toggled.connect(
                        lambda ch, path=p, info=self.adv_data_list_info[p]:
                        self._on_toggle_event(idx=path, ch=ch, obj=info)
                    )
                # **Update coordinate spinbox range if new data found**
                if max_col > 0 and max_row > 0:
                    self._update_coordinate_spinbox_range(max_col, max_row)
        else:  # Clear
            self._clear_data_list()
            # **Reset coordinate spinbox range to 1,1**
            self._update_coordinate_spinbox_range(1, 1)

    def _get_data_shape_from_hdr(self, folder_path):
        """
        @description : Reads the shape of hyperspectral data from the .hdr file in the specified folder
        @author : JiHoon Jung
        @parameters :
            folder_path: Path to the folder containing the .hdr file
        @return : Tuple of (lines, samples, bands) if successful, None if error occurs
        @note : Uses spectral.io.envi to read the .hdr file
        """
        hdr_path = os.path.join(folder_path, "data.hdr")
        try:
            img = spectral.io.envi.open(hdr_path)
            return img.shape  # (lines, samples, bands)
        except Exception:
            return None

    def _update_coordinate_spinbox_range(self, max_col, max_row):
        """
        @description : Updates the range of the coordinate spinboxes based on the maximum column and row values
        @author : JiHoon Jung
        """
        # Get the spinboxes for column and row from the header dictionary
        col_sb = self.header_dict_[2]["obj_set"]["spinbox"][0]
        row_sb = self.header_dict_[2]["obj_set"]["spinbox"][1]
        # Save previous values before changing range  
        prev_col = col_sb.value()
        prev_row = row_sb.value()
        # Set new range for spinboxes
        col_sb.setRange(0, max_col - 1)
        row_sb.setRange(0, max_row - 1)
        # Reset to 0 if previous value exceeds new max
        if prev_col > (max_col - 1):
            col_sb.setValue(0)
        if prev_row > (max_row - 1):
            row_sb.setValue(0)
        # Update the internal model info with new values
        self.adv_model_info[2]["value"] = [col_sb.value(), row_sb.value()]

    def _clear_data_list(self):
        """
        @description : Initializes the data list
        @author : JiHoon Jung
        """
        self.advanced_pixel_based_labeling_datalist_tableview.clear()
        self.advanced_pixel_based_labeling_datalist_tableview.setRowCount(4)
        self.advanced_pixel_based_labeling_datalist_tableview.setHorizontalHeaderLabels(
            ["Index", "Data", "Use"]
        )
        self.adv_data_list_info.clear()

    def _on_button_event(self, mode):
        """
        @description : Handles Start/Stop button click events
        @author : JiHoon Jung
        @parameters :
            mode: 0 for Start, 1 for Stop
        @history :
            1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
            2. Yugyeong Hong(2026.02.24) : Refactor message box with util method and language support
        """
        if mode == 0:  # Start
            if self.worker_id != -1:
                messageBox(
                    mode=MESSAGE_BOX_WARNING,
                    title=self.lang.get("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_msg_warning_already_allocated_title"),
                    text=f"{self.lang.get('advanced', 'advanced_pixel_based_labeling_main', 'advanced_pixel_based_labeling_msg_warning_already_allocated_message')} Worker ID:{self.worker_id}",
                    buttons = {self.lang.get("main", "messageBox", "msgOk"):"accept"}
                )
                return
            self._start_processing()
        else:  # Stop
            response = messageBox(
                mode=MESSAGE_BOX_CONFIRMATION,
                title=self.lang.get("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_msg_stop_title"),
                text=self.lang.get("advanced", "advanced_pixel_based_labeling_main", "advanced_pixel_based_labeling_msg_stop_message"),
                buttons={self.lang.get("main", "messageBox", "msgYes"): "accept", self.lang.get("main", "messageBox", "msgNo"): "reject"}
            )

            if response == "accept":
                self.interrupt_ = True

    # ----------------------------------------------------
    # PROCESSING CONTROL
    # ----------------------------------------------------
    def _start_processing(self):
        """
        @description : Sets UI state and prints parameters before actual processing, then starts thread task
        @author : JiHoon Jung
        """
        self.interrupt_ = False
        # Toggle buttons/groupboxes enabled/disabled
        self.advanced_pixel_based_labeling_setting_start_btn.setEnabled(False)
        self.advanced_pixel_based_labeling_setting_stop_btn.setEnabled(True)
        self.advanced_pixel_based_labeling_setting_groupbox.setEnabled(False)
        self.advanced_pixel_based_labeling_datalist_groupbox.setEnabled(False)
        
        # Initialize status window and log parameters
        self.advanced_pixel_based_labeling_status_textedit.clear()
        self.advanced_pixel_based_labeling_status_textedit.appendPlainText(
            f"{self.mode}\n{self.dash * 30}\nParameter Setting\n"
        )
        # Print parameter info in status window
        for i, info in self.adv_model_info.items():
            if i == 2:
                c, r = info["value"]
                self.advanced_pixel_based_labeling_status_textedit.appendPlainText(
                    f"{i + 1}. {info['type']} : ({c},{r})"
                )
            else:
                self.advanced_pixel_based_labeling_status_textedit.appendPlainText(
                    f"{i + 1}. {info['type']} : {info['value'][0]}"
                )

        self.advanced_pixel_based_labeling_status_textedit.appendPlainText(self.dash * 30)
        total = sum(
            1 for v in self.adv_data_list_info.values() if v["obj_set"]["toggle"].isChecked()
        )
        self.advanced_pixel_based_labeling_status_textedit.appendPlainText(f"Data List\nTotal: {total}\n")
        self.advanced_pixel_based_labeling_status_textedit.appendPlainText("Processing Start....\n")
        # Output the number of selected data, then start thread
        self.worker_1.staging(self._predict_label_mode)
        self.worker_id = self.worker_1.cur_id
        self.worker_1.start()

    def _predict_label_mode(self) -> None:
        """
        @description : Processes the selected folders in order and runs pixel-based labeling
                    (Called from worker thread)
        @author : JiHoon Jung
        """
        try:
            # 1) Read user-specified coordinate (column, row)
            col = self.header_dict_[2]["obj_set"]["spinbox"][0].value()
            row = self.header_dict_[2]["obj_set"]["spinbox"][1].value()

            # 2) Filter only folders with "Use" toggle checked
            paths = [
                k for k, v in self.adv_data_list_info.items()
                if v["obj_set"]["toggle"].isChecked()
            ]
            if not paths:
                # Raise exception if no data selected
                raise Exception("No data selected.")

            # 3) Process labeling for each folder
            for p in paths:
                if self.interrupt_:
                    # Output message and break loop if interrupted
                    self.string_signal.emit("\nProcess interrupted by user.\n")
                    break
                # Log folder name with separator
                self.string_signal.emit(f"\n{'=' * 100}\nProcessing folder: {p}\n{'=' * 100}")
                # Label for each folder
                self._process_folder(p, row, col)
            
            # 4) Output completion log
            self.string_signal.emit(f"\n{'-' * 50}\nProcessing Complete!\n{'-' * 50}")
        except Exception as e:
            # Output error message if exception occurs
            self.string_signal.emit(f"\nError Occurred: {e}\n{'-' * 50}\n")

    # ----------------------------------------------------
    # DATA LOADING & CALIBRATION
    # ----------------------------------------------------
    def load_hyperspectral_data(self, base, calib=True, rate=1.0):
        """
        @description : Loads ENVI format data and performs calibration if needed, returns torch tensor
        @author : JiHoon Jung
        @parameters :
            base: Folder path where data is stored
            calib: Whether to calibrate (True/False)
            rate: Calibration ratio
        """
        # Load ENVI data
        data = self.load_envi_data(base, "data.hdr", "data.raw")
        if data is None:
            return None
        # If calibration is enabled, load DARKREF/WHITEREF and calibrate
        if calib:
            dark = self.load_reference_data(base, "DARKREF")
            white = self.load_reference_data(base, "WHITEREF")
            data = self.calibrate_data(data, dark, white, rate)
        # Convert NumPy array to CUDA tensor
        return torch.tensor(data, dtype=torch.float32, device="cuda")

    def load_envi_data(self, base, hdr, raw):
        """
        @description : Opens ENVI format .hdr/.raw files and returns NumPy array
        @author : JiHoon Jung
        @parameters :
            base: Data folder path
            hdr: .hdr file name
            raw: .raw file name
        """
        try:
            # Open ENVI data with spectral library
            return spectral.io.envi.open(os.path.join(base, hdr), os.path.join(base, raw)).load()
        except FileNotFoundError as e:
            # Send error message if file not found
            self.string_signal.emit(f"Error loading data: {e}")
            return None

    def load_reference_data(self, base, name):
        """
        @description : Loads the specified reference (DARKREF/WHITEREF) data and returns mean spectrum
        @author : JiHoon Jung
        @parameters :
            base: Folder path containing reference files
            name: "DARKREF" or "WHITEREF"
        """
        ref = self.load_envi_data(base, f"{name}.hdr", f"{name}.raw")
        # If loading succeeds, return mean of bands; otherwise, return None
        return ref.mean(axis=0) if ref is not None else None

    @staticmethod
    def calibrate_data(data, dark, white, rate):
        """
        @description : Performs reflectance calibration using dark and white reference data
        @author : JiHoon Jung
        @parameters :
            data: Original hyperspectral data (H×W×B)
            dark: DARKREF mean spectrum (B)
            white: WHITEREF mean spectrum (B)
            rate: Calibration ratio
        """
        # Normalize and scale to range 0~4095
        norm = (data - dark) / (white - dark)
        return np.clip(norm * 4095.0 * rate, 0, 4095.0).astype(np.float32)


    # ----------------------------------------------------
    # SIMILARITY CALCULATION
    # ----------------------------------------------------
    def calculate_similarity(self, data, ref, mode):
        """
        @description : Spectrum similarity calculation function (Cosine/SAM are improved with weighting)
        @author : JiHoon Jung
        @parameters :
            data : (H, W, B) - Hyperspectral data to compare
            ref  : (B,)      - Reference spectrum
            mode : str       - Similarity mode ("Area", "Cosine", "SAM", "L2", "Chebyshev", "Canberra", "Jeffrey") 
        """
        eps = 1e-12   # Small constant for numerical stability
        # 1) Area mode: Convert the area difference between two spectra to similarity by dividing by total area
        if mode == "Area":
            # Sum of absolute differences for each pixel
            area_diff = torch.sum(torch.abs(data - ref), dim=2)      # (H, W)
            # Expand ref to the same dimension as data for comparison
            ref_expanded = ref.unsqueeze(0).unsqueeze(0)             # (1, 1, B)
            # Sum of the larger values between pixel and reference spectrum (for normalization denominator)
            area_total = torch.sum(torch.maximum(data, ref_expanded), dim=2).clamp_min(eps)
            # Divide the difference by the total, subtract from 1, and convert to 0~100 scale
            sim = (1 - area_diff / area_total) * 100.0
            return sim

        # 2) Cosine / SAM mode: Cosine similarity based
        if mode in ["Cosine", "SAM"]:
            # Convert to float
            data = data.float()
            ref = ref.float()
            # Calculate the L2 norm of each pixel spectrum
            data_norm = torch.linalg.norm(data, dim=2, keepdim=True)  # (H, W, 1)
            ref_norm = torch.linalg.norm(ref)                         # scalar
            # Create unit vectors by dividing by norm
            data_unit = data / (data_norm + torch.finfo(data.dtype).eps)
            ref_unit = ref / (ref_norm + torch.finfo(ref.dtype).eps)
            # Calculate cosine value by pixel-reference dot product, clamp to [-1,1]
            cos_theta = torch.sum(data_unit * ref_unit, dim=2).clamp(-1.0, 1.0)

            if mode == "Cosine":
                weight_cosine = 30.0 # Weight: The higher the value, the more sensitive to small differences
                # Scale cosine value to 0~1, then apply exponential transformation
                cos_scaled = (cos_theta + 1.0) / 2.0
                sim = torch.exp(-weight_cosine * (1.0 - cos_scaled)) * 100.0
                return sim
            else:
                weight_sam = 11.0 # Weight: The higher the value, the more sensitive to small angles
                # SAM: Use angle (acos), then exponential transform
                ang = torch.acos(cos_theta) / math.pi
                sim = torch.exp(-weight_sam * ang) * 100.0
                return sim

        # 3) L2 mode: Similarity based on Euclidean distance
        if mode == "L2":
            # Calculate the spectrum difference for each pixel
            diff = data - ref
            # Calculate L2 distance
            dist = torch.linalg.norm(diff, dim=2)
            # Calculate max distance using overall min/max value of data (for normalization denominator)
            data_min = torch.amin(data)
            data_max = torch.amax(data)
            maxd = torch.sqrt(torch.tensor(data.shape[2], device=data.device)) * (data_max - data_min + eps)
            # Divide the distance by max, subtract from 1, then convert to 0~100 scale
            sim = (1 - dist / maxd).clamp(0, 1) * 100.0
            return sim

        # 4) Chebyshev mode: Similarity based on maximum absolute difference
        if mode == "Chebyshev":
            # Calculate absolute difference per pixel per band
            abs_diff = torch.abs(data - ref)
            # Calculate Chebyshev distance by the maximum value across bands
            dist = torch.amax(abs_diff, dim=2)
            # Normalize by the total data range
            data_min = torch.amin(data)
            data_max = torch.amax(data)
            maxd = (data_max - data_min + eps)
            # Normalize and convert to 0~100 scale
            sim = (1 - dist / maxd).clamp(0, 1) * 100.0
            return sim
        
        # 5) Canberra distance-based similarity
        if mode == "Canberra":
            weight_canb = 1.5  # Weight: The higher the value, the more sensitive to small differences
            # Sum |x - y| / (|x| + |y|) for each band
            # torch.abs(ref) → (B,) → broadcast to (1,1,B)
            ref_e = ref.unsqueeze(0).unsqueeze(0)                                    # (1, 1, B)
            num = torch.abs(data - ref_e)                                            # (H, W, B)
            den = torch.abs(data) + torch.abs(ref_e) + eps                            # (H, W, B)
            canb = torch.sum(num / den, dim=2)                                        # (H, W)
            # Normalize by number of bands, convert to similarity
            B = data.shape[2]
            norm_canb = canb / B                                                      # Normalization (0~1)
            sim = torch.exp(-weight_canb * norm_canb).clamp(0, 1) * 100.0             # Exponential transform
            return sim

        # 6) Jeffrey divergence-based similarity
        if mode == "Jeffrey":
            weight_j = 100.0  # Weight: The higher the value, the more sensitive to small divergence
            # Normalize spectrum with L1 to interpret as distribution
            data_sum = data.sum(dim=2, keepdim=True) + eps                            # (H, W, 1)
            p = data / data_sum                                                        # (H, W, B)
            q = ref / (ref.sum() + eps)                                                # (B,)
            q = q.unsqueeze(0).unsqueeze(0)                                            # (1, 1, B)
            m = 0.5 * (p + q)                                                           # (H, W, B)

            # KL(p||m) + KL(q||m)
            kl_pm = torch.sum(p * torch.log((p + eps) / (m + eps)), dim=2)             # (H, W)
            kl_qm = torch.sum(q * torch.log((q + eps) / (m + eps)), dim=2)             # (H, W)
            jdiv = kl_pm + kl_qm                                                        # (H, W)

            # The smaller the divergence, the more similar; apply exponential transformation
            sim = torch.exp(-weight_j * jdiv).clamp(0, 1) * 100.0                      # Exponential transform
            return sim

        # Exception for unknown modes
        raise ValueError(f"Unknown mode {mode}")

    # ----------------------------------------------------
    # FOLDER DATA PROCESSING
    # ----------------------------------------------------
    def _process_folder(self, path, row, col):
        """
        @description : Load hyperspectral data in the folder and save pixel-based labels using the given coordinate as reference
        @author : JiHoon Jung
        @parameters :
            path: Folder path to process
            row: Selected row coordinate
            col: Selected column coordinate
        """
        # 1) Read parameters
        mode = self.adv_model_info[0]["value"][0]
        thr = self.adv_model_info[1]["value"][0]
        label_id = self.adv_model_info[3]["value"][0]
        calib_on = self.adv_model_info[4]["value"][0]
        calib_rate = self.adv_model_info[5]["value"][0]

        # 2) Compose filename and path for saving
        label_name = f"label_{mode}_thr{thr}_({col},{row}).npy"
        save_fp = os.path.join(path, label_name)

        # 3) Load and calibrate data
        data = self.load_hyperspectral_data(path, calib_on, calib_rate)
        if data is None:
            return
        # Skip if file already exists
        if os.path.exists(save_fp):
            self.string_signal.emit(f"- Skip (exists): {label_name}")
            return
        # Check coordinate validity
        if row >= data.shape[0] or col >= data.shape[1]:
            self.string_signal.emit("- Invalid coordinate")
            return
        
        # 4) Extract reference spectrum (ref) and calculate similarity
        ref = data[row, col]  # row first, col second
        sim = self.calculate_similarity(data, ref, mode)
        # 5) Assign label to pixels above threshold (thr)
        lbl = torch.zeros((data.shape[0], data.shape[1]), device="cuda")
        lbl[sim >= thr] = label_id
        # 6) Save result and log
        np.save(save_fp, lbl.cpu().numpy())
        self.string_signal.emit(f"- Saved: {save_fp}")

    # ----------------------------------------------------
    # STATUS UPDATE & UTILITIES
    # ----------------------------------------------------
    def update_status(self, string_):
        """
        @description : Add a string to the status output window
        @author : JiHoon Jung
        @parameters :
            string_: String to output
        """
        try:
            msg = f"{float(string_):.2f}" if string_.replace(".", "", 1).isdigit() else string_
        except ValueError:
            msg = string_
        self.advanced_pixel_based_labeling_status_textedit.appendPlainText(msg)

    def showEvent(self, e):
        pass  # Override if needed

    def closeEvent(self, e):
        pass  # Override if needed

# ========================================================
# APPLICATION ENTRY POINT
# ========================================================
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = advanced_pixel_based_labeling_Form()
    ui.show()
    sys.exit(app.exec_())