"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""


from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot
import spectral
import numpy as np
import os
import glob
import time
import json
from enum import Enum, auto

from utils.custom_ui import custom_qtablewidget, custom_qheaderview
from utils.worker import Threading_Worker
from constants.constants import ADV_LABEL_AGGREGATION_WINDOW_SIZE, ADV_LABEL_AGGREGATION_BUTTON_SIZE, ADV_LABEL_AGGREGATION_GROUPBOX_MINIMUM_WIDTH, ADV_LABEL_AGGREGATION_LINEEDIT_MINIMUM_WIDTH, MESSAGE_BOX_CONFIRMATION, MESSAGE_BOX_INFORMATION
from advanced.ui.adv_gen_module import gen_module
from utils.custom_ui import messageBox
class eventMode(Enum):
    """
        @description: Enum class for event modes
        @author : GaEun Hwang (26.01.26)
    """
    SEARCH_DATA = auto()
    CLEAR_DATA = auto()
    START = auto()
    STOP = auto()
    SELECT_SAVEPATH = auto()
    USE_COMMON_REFERENCE = auto()
    SELECT_COMMON_REFERENCE_PATH = auto()
    USE_DATA = auto()

class signal_(QtCore.QObject):
    string_signal = QtCore.pyqtSignal(str)

class advanced_label_aggregation_Form(QtWidgets.QWidget):
    def __init__(self, Sync=None, lang=None):
        super().__init__()
        self.init(Sync=Sync, lang=lang)
        self.init_variable()
        self.init_ui(self)
        self.setup_ui()
        self.init_function()
        self.fill_table()
        if __name__ == "__main__":
            self.show()

    def init(self, Sync=None, lang=None):
        self.Sync = Sync
        self.lang = lang

        self.worker_1 = Threading_Worker()
        self.worker_1.output.connect(self.recv_from_threading)
        
        self.signal_ = signal_()
        self.string_signal = self.signal_.string_signal
        self.string_signal.connect(self.updateTextStatus)

    def init_variable(self):
        """
            @description: Initial variable declaration part
            @author : JiHoon
            @parameters
                - self.adv_model_info: Information about function setting
                    camera: hyperspectra type
                    fileName: Information about the data
                    savePath: Path to save generated data
                    commonReferencePath: Path to copy Common Reference data
                - self.adv_data_list_info: Dictionary storing the list of data(contain objects)
                - self.worker_id: Thread ID
                - self.dash: Special character to display in Qplaintextedit
                - self.mode: Name of the function
            @history :
                1. GaEun Hwang(26.01.23): 
                    - Combine & Modify Dictionary(adv_model_info + header_dict)
                    - Remove 'Calibration On/Off' and 'Calibration Ratio' options and Add 'commonReferencePath'.
                    - Add seperatedData dictionary to store separated data
                    - Modify mode name to 'Label Aggregation Mode'
        """

        self.adv_model_info = {
            "camera": # VNIR/NIR Select
                {
                    "tip":["label:1. Hyperspectra"],    # tip is name(label) for would be created object
                    "objList":["combobox:VNIR,NIR"],    # obj_list is object type and its option for would be created object
                    "objTip": None,               # objTip is created tip object
                    "objSetting": None,      # objSetting is created setting object
                    "layout": None         # layout is layout contains objTip and objSetting
                },          
            "fileName": # File Name
                {
                    "tip": ["label:2. File Name"],
                    "objList": ["lineedit:"],
                    "objTip": None,
                    "objSetting": None,
                    "layout": None
                },
            "savePath": # Save Path
                {
                    "tip":["label:3. Save Path"],
                    "objList":["lineedit:placeHolderText", "lineedit:path", "button:Search"],
                    "objTip": None,
                    "objSetting": None,
                    "layout": None
                },           
            "useCommonReference": # Use Common Reference
                {
                    "tip":["label:4. Use Common Reference"],
                    "objList":["toggle:"],
                    "objTip": None,
                    "objSetting": None,
                    "layout": None
                },
            "commonReferencePath": # Reference Path
                {
                    "tip":["label:5. Common Reference Path"],
                    "objList":["lineedit:placeHolderText", "lineedit:path", "button:Search"],
                    "objTip": None,
                    "objSetting": None,
                    "layout": None
                }
        }
        self.adv_data_list_info = {}
        self.seperatedData = {}
        self.jsonInfo = {}

        self.worker_id = None
        self.thread_interrupted = False
        self.dash = "-"
        self.mode = "Label Aggregation Mode"

    @pyqtSlot(dict)
    def recv_from_threading(self):
        """
            @description: Recv threading process result
            @author : JiHoon
        """
        self.worker_id = None
        self.thread_interrupted = False
        self.setIdleSettingUi()

    def init_ui(self, MainWindow):
        """
            @description: Initial UI variable declaration part
            @author : JiHoon
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
                2. GaEun Hwang(26.01.23): 
                    - Use custom_qtablewidget, custom_qheaderview
        """
        MainWindow.setObjectName("adv_setting_form")
        MainWindow.resize(*ADV_LABEL_AGGREGATION_WINDOW_SIZE)
        MainWindow.setWindowTitle("Advanced Setting")

        self.advanced_label_aggregation_main_horizon = QtWidgets.QHBoxLayout(MainWindow)
        self.advanced_label_aggregation_main_horizon.setObjectName("advanced_label_aggregation_main_horizon")

        self.advanced_label_aggregation_main_vertical = QtWidgets.QVBoxLayout()
        self.advanced_label_aggregation_main_vertical.setObjectName("advanced_label_aggregation_main_vertical")

        self.advanced_label_aggregation_setting_groupbox = QtWidgets.QGroupBox()
        self.advanced_label_aggregation_setting_groupbox.setMinimumWidth(ADV_LABEL_AGGREGATION_GROUPBOX_MINIMUM_WIDTH)
        self.advanced_label_aggregation_setting_groupbox.setObjectName("advanced_label_aggregation_setting_groupbox")
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_setting_groupbox", self.advanced_label_aggregation_setting_groupbox)

        self.advanced_label_aggregation_setting_vertical = QtWidgets.QVBoxLayout()
        self.advanced_label_aggregation_setting_vertical.setObjectName("advanced_label_aggregation_setting_vertical")

        self.advanced_label_aggregation_datalist_groupbox = QtWidgets.QGroupBox()
        self.advanced_label_aggregation_datalist_groupbox.setMinimumWidth(ADV_LABEL_AGGREGATION_GROUPBOX_MINIMUM_WIDTH)
        self.advanced_label_aggregation_datalist_groupbox.setObjectName("advanced_label_aggregation_datalist_groupbox")
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_datalist_groupbox", self.advanced_label_aggregation_datalist_groupbox)

        self.advanced_label_aggregation_datalist_vertical = QtWidgets.QVBoxLayout()
        self.advanced_label_aggregation_datalist_vertical.setObjectName("advanced_label_aggregation_datalist_vertical")

        self.advanced_label_aggregation_datalist_tableview = custom_qtablewidget(obj_name="advanced_label_aggregation_datalist_tableview")
        self.advanced_label_aggregation_datalist_tableview.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.advanced_label_aggregation_datalist_tableview.setDragEnabled(False)
        self.advanced_label_aggregation_datalist_tableview.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.advanced_label_aggregation_datalist_tableview.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.advanced_label_aggregation_datalist_tableview.verticalHeader().hide()
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_datalist_tableview", self.advanced_label_aggregation_datalist_tableview)
        
        self.advanced_label_aggregation_datalist_tableview_header = custom_qheaderview(obj_name="advanced_label_aggregation_datalist_tableview_header")
        self.advanced_label_aggregation_datalist_tableview.setHorizontalHeader(self.advanced_label_aggregation_datalist_tableview_header)
        self.advanced_label_aggregation_datalist_tableview_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.advanced_label_aggregation_datalist_tableview_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

        self.advanced_label_aggregation_datalist_global_horizon = QtWidgets.QHBoxLayout()
        self.advanced_label_aggregation_datalist_global_horizon.setObjectName("advanced_label_aggregation_datalist_global_horizon")
        self.advanced_label_aggregation_datalist_global_search_btn = QtWidgets.QPushButton()
        self.advanced_label_aggregation_datalist_global_search_btn.setProperty("property", "outline")
        self.advanced_label_aggregation_datalist_global_search_btn.setObjectName("advanced_label_aggregation_datalist_global_search_btn")
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_datalist_global_search_btn", self.advanced_label_aggregation_datalist_global_search_btn)
        self.advanced_label_aggregation_datalist_global_clear_btn = QtWidgets.QPushButton()
        self.advanced_label_aggregation_datalist_global_clear_btn.setObjectName("advanced_label_aggregation_datalist_global_clear_btn")
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_datalist_global_clear_btn", self.advanced_label_aggregation_datalist_global_clear_btn)
    
        self.advanced_label_aggregation_setting_horizon = QtWidgets.QHBoxLayout()
        self.advanced_label_aggregation_setting_horizon.setObjectName("advanced_label_aggregation_setting_horizon")

        self.advanced_label_aggregation_setting_start_btn = QtWidgets.QPushButton()
        self.advanced_label_aggregation_setting_start_btn.setObjectName("advanced_label_aggregation_setting_start_btn")
        self.advanced_label_aggregation_setting_start_btn.resize(*ADV_LABEL_AGGREGATION_BUTTON_SIZE)
        self.advanced_label_aggregation_setting_start_btn.setCheckable(True)
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_setting_start_btn", self.advanced_label_aggregation_setting_start_btn)

        self.advanced_label_aggregation_setting_stop_btn = QtWidgets.QPushButton()
        self.advanced_label_aggregation_setting_stop_btn.setObjectName("advanced_label_aggregation_setting_stop_btn")
        self.advanced_label_aggregation_setting_stop_btn.resize(*ADV_LABEL_AGGREGATION_BUTTON_SIZE)
        self.advanced_label_aggregation_setting_stop_btn.setEnabled(False)
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_setting_stop_btn", self.advanced_label_aggregation_setting_stop_btn)

        self.advanced_label_aggregation_status_vertical = QtWidgets.QVBoxLayout()
        self.advanced_label_aggregation_status_vertical.setObjectName("advanced_label_aggregation_status_vertical")
        self.advanced_label_aggregation_status_groupbox = QtWidgets.QGroupBox()
        self.advanced_label_aggregation_status_groupbox.setObjectName("advanced_label_aggregation_status_groupbox")
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_status_groupbox", self.advanced_label_aggregation_status_groupbox)

        self.advanced_label_aggregation_status_textedit = QtWidgets.QPlainTextEdit()
        self.advanced_label_aggregation_status_textedit.setReadOnly(True)
        self.advanced_label_aggregation_status_textedit.setUndoRedoEnabled(False)

    def setup_ui(self):
        """
            @description: Set layout/widget of UI objects
            @author : JiHoon
        """
        self.advanced_label_aggregation_setting_groupbox.setLayout(self.advanced_label_aggregation_setting_vertical)

        self.advanced_label_aggregation_setting_horizon.addWidget(self.advanced_label_aggregation_setting_start_btn)
        self.advanced_label_aggregation_setting_horizon.addWidget(self.advanced_label_aggregation_setting_stop_btn)
        
        self.advanced_label_aggregation_datalist_global_horizon.addWidget(self.advanced_label_aggregation_datalist_global_search_btn)
        self.advanced_label_aggregation_datalist_global_horizon.addStretch()
        self.advanced_label_aggregation_datalist_global_horizon.addWidget(self.advanced_label_aggregation_datalist_global_clear_btn)

        self.advanced_label_aggregation_datalist_vertical.addLayout(self.advanced_label_aggregation_datalist_global_horizon)
        self.advanced_label_aggregation_datalist_vertical.addWidget(self.advanced_label_aggregation_datalist_tableview)
        self.advanced_label_aggregation_datalist_groupbox.setLayout(self.advanced_label_aggregation_datalist_vertical)

        self.advanced_label_aggregation_main_vertical.addWidget(self.advanced_label_aggregation_setting_groupbox)
        self.advanced_label_aggregation_main_vertical.addWidget(self.advanced_label_aggregation_datalist_groupbox)
        self.advanced_label_aggregation_main_vertical.addLayout(self.advanced_label_aggregation_setting_horizon)

        self.advanced_label_aggregation_status_vertical.addWidget(self.advanced_label_aggregation_status_textedit)
        self.advanced_label_aggregation_status_groupbox.setLayout(self.advanced_label_aggregation_status_vertical)

        self.advanced_label_aggregation_main_horizon.addLayout(self.advanced_label_aggregation_main_vertical, 1)
        self.advanced_label_aggregation_main_horizon.addWidget(self.advanced_label_aggregation_status_groupbox, 1)

    def init_function(self):
        """
            @description: Define signals for buttons outside the custom_qtablewidget area
            @author : Jihoon
            @history :
                1. GaEun Hwang(26.01.23): 
                    - Modify button Event connections
        """
        self.advanced_label_aggregation_datalist_global_search_btn.clicked.connect(lambda: self.buttonEvent(eventMode.SEARCH_DATA))
        self.advanced_label_aggregation_datalist_global_clear_btn.clicked.connect(lambda: self.buttonEvent(eventMode.CLEAR_DATA))
        self.advanced_label_aggregation_setting_start_btn.clicked.connect(lambda: self.buttonEvent(eventMode.START))
        self.advanced_label_aggregation_setting_stop_btn.clicked.connect(lambda: self.buttonEvent(eventMode.STOP))

    def fill_table(self):
        """
        @description: Generate UI objects based on the adv_model_info dictionary
        @author : Jihoon
        @history :
            1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
            2. GaEun Hwang(26.01.23): 
                - Use create_obj function of custom_qtablewidget
                - Remove Calibration On/Off, Calibration ratio options
        """
        for idx, value in self.adv_model_info.items():
            self.adv_model_info[idx]["objTip"] = self.advanced_label_aggregation_datalist_tableview.create_obj(idx, obj_type="widget", obj_list=value["tip"])
            self.adv_model_info[idx]["objSetting"] = self.advanced_label_aggregation_datalist_tableview.create_obj(idx, obj_type="widget", obj_list=value["objList"])
            self.adv_model_info[idx]["objTip"]["widget"].setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)

            for child in self.adv_model_info[idx]["objSetting"]["widget"].children():
                # Set minimum width for QLineEdit objects
                if child.__class__ == QtWidgets.QLineEdit:
                    child.setMinimumWidth(ADV_LABEL_AGGREGATION_LINEEDIT_MINIMUM_WIDTH)

                elif child.__class__ == QtWidgets.QPushButton:
                    # Fix button size
                    child.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)

            horizonLayout = QtWidgets.QHBoxLayout()
            horizonLayout.setContentsMargins(3, 3, 3, 3)
            horizonLayout.addWidget(self.adv_model_info[idx]["objTip"]["widget"])
            horizonLayout.addStretch()
            horizonLayout.addWidget(self.adv_model_info[idx]["objSetting"]["widget"])
            self.adv_model_info[idx]['layout'] = horizonLayout

        for row, value in enumerate(self.adv_model_info.values()):
            self.advanced_label_aggregation_setting_vertical.addLayout(value["layout"])

        self.adv_model_info["fileName"]["objSetting"]["lineedit"].setReadOnly(False)
        self.adv_model_info["commonReferencePath"]["objSetting"]["lineedit"].setEnabled(False)
        self.adv_model_info["commonReferencePath"]["objSetting"]["button"].setEnabled(False)

        self.adv_model_info["savePath"]["objSetting"]["button"].clicked.connect(lambda: self.buttonEvent(eventMode.SELECT_SAVEPATH))
        self.adv_model_info["useCommonReference"]["objSetting"]["toggle"].toggled.connect(lambda: self.toggleEvent(eventMode.USE_COMMON_REFERENCE))
        self.adv_model_info["commonReferencePath"]["objSetting"]["button"].clicked.connect(lambda: self.buttonEvent(eventMode.SELECT_COMMON_REFERENCE_PATH))

        # 1. Hyperspectral
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_hyperspectral_label", self.adv_model_info["camera"]["objTip"]["label"])

        # 2. File Name
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_filename_label", self.adv_model_info["fileName"]["objTip"]["label"])

        # 3. Save Path
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_savepath_label", self.adv_model_info["savePath"]["objTip"]["label"])
        self.lang.set("advanced", "advanced_label_aggregation_main", "advancedLabelAggregationSavePath", self.adv_model_info["savePath"]["objSetting"]["lineedit"])
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_savepath_button", self.adv_model_info["savePath"]["objSetting"]["button"])
        
        # 4. Use Common Reference
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_useCommonReference_label", self.adv_model_info["useCommonReference"]["objTip"]["label"])

        # 5. Common Reference Path
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_commonReferencePath_label", self.adv_model_info["commonReferencePath"]["objTip"]["label"])
        self.lang.set("advanced", "advanced_label_aggregation_main", "advancedLabelAggregationCommonReferencePathLine", self.adv_model_info["commonReferencePath"]["objSetting"]["lineedit"])
        self.lang.set("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_commonReferencePath_button", self.adv_model_info["commonReferencePath"]["objSetting"]["button"])

    def setIdleSettingUi(self):
        """
            @description: Set UI to idle state
            @author: GaEun Hwang (2026.01.23)
        """
        self.advanced_label_aggregation_setting_start_btn.toggle()
        self.advanced_label_aggregation_setting_start_btn.setEnabled(True)
        self.advanced_label_aggregation_setting_stop_btn.setEnabled(False)
        self.advanced_label_aggregation_setting_groupbox.setEnabled(True)
        self.advanced_label_aggregation_datalist_groupbox.setEnabled(True)

    def lockSettingUi(self):
        """
            @description: Lock UI during processing
            @author: GaEun Hwang (2026.01.23)
        """
        self.advanced_label_aggregation_setting_start_btn.setEnabled(False)
        self.advanced_label_aggregation_setting_stop_btn.setEnabled(True)
        self.advanced_label_aggregation_setting_groupbox.setEnabled(False)
        self.advanced_label_aggregation_datalist_groupbox.setEnabled(False)

    def toggleEvent(self, mode, idx=None):
        """
            @description: Event function for toggle button signal
            @author : Jihoon
            @history :
                1. GaEun Hwang(26.01.23): 
                    - Remove conditional statement about calibration option
                    - Add common reference option
        """
        if mode == eventMode.USE_COMMON_REFERENCE:
            if self.adv_model_info["useCommonReference"]["objSetting"]["toggle"].isChecked():
                self.adv_model_info["commonReferencePath"]["objSetting"]["lineedit"].setEnabled(True)
                self.adv_model_info["commonReferencePath"]["objSetting"]["button"].setEnabled(True)
            else:
                self.adv_model_info["commonReferencePath"]["objSetting"]["lineedit"].setEnabled(False)
                self.adv_model_info["commonReferencePath"]["objSetting"]["button"].setEnabled(False)
        
        elif mode == eventMode.USE_DATA:
            if self.adv_data_list_info[idx]["objSetting"]["toggle"].isChecked():
                self.adv_data_list_info[idx]["use"] = True
            else:
                self.adv_data_list_info[idx]["use"] = False

    def buttonEvent(self, mode):
        """
            @description: Event function for button signal
            @author: Jihoon
            @history :
                1. Hyeok Yoon(2025.10.31) : Modifying Widgets to supports language function
                2. GaEun Hwang(26.01.23): 
                    - Combine each button event function into one function
                    - Modify mode(digit) type to string type for better readability
                3. Yugyeong Hong(26.02.24): Refactor message box with util method and language support 
        """
        if mode in {eventMode.SELECT_SAVEPATH, eventMode.SELECT_COMMON_REFERENCE_PATH, eventMode.SEARCH_DATA}:
            # define QFileDialog for folder selection
            if mode == eventMode.SELECT_SAVEPATH:
                title = self.lang.get("advanced", "advanced_label_aggregation_main", "advancedLabelAggregationFindSavePath")
            elif mode == eventMode.SELECT_COMMON_REFERENCE_PATH:
                title = self.lang.get("advanced", "advanced_label_aggregation_main", "advancedLabelAggregationCommonReferenceLoadPath")
            elif mode == eventMode.SEARCH_DATA:
                title = self.lang.get("advanced", "advanced_main", "advancedAddDataTitle")
            fileDialog = QtWidgets.QFileDialog(caption=title)
            fileDialog.setFileMode(QtWidgets.QFileDialog.FileMode.DirectoryOnly)
            fileDialog.setOption(QtWidgets.QFileDialog.Option.DontUseNativeDialog, True)
            fileDialog.setOption(QtWidgets.QFileDialog.Option.DontUseCustomDirectoryIcons, True)
            fileDialog.setOption(QtWidgets.QFileDialog.Option.ShowDirsOnly, True)
            
            if mode == eventMode.SELECT_SAVEPATH:
                if fileDialog.exec_():
                    fname = fileDialog.selectedFiles()[0]
                    if fname:
                        self.adv_model_info["savePath"]["objSetting"]["lineedit"].setText(fname)
                        self.adv_model_info["savePath"]["objSetting"]["lineedit"].setToolTip(fname)
            
            elif mode == eventMode.SELECT_COMMON_REFERENCE_PATH:
                if fileDialog.exec_():
                    fname = fileDialog.selectedFiles()[0]
                    if fname:
                        self.adv_model_info["commonReferencePath"]["objSetting"]["lineedit"].setText(fname)
                        self.adv_model_info["commonReferencePath"]["objSetting"]["lineedit"].setToolTip(fname)

            elif mode == eventMode.SEARCH_DATA:
                # set file dialog selection mode to extended selection for multiple folder selection
                fileDialog.findChild(QtWidgets.QListView, 'listView').setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
                fileDialog.findChild(QtWidgets.QTreeView, 'treeView').setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
                if fileDialog.exec_():
                    filePaths = fileDialog.selectedFiles()
                    if filePaths:
                        currentTableRow = len(self.adv_data_list_info.keys())
                        existingPaths = set(self.adv_data_list_info.keys())
                        # addedDataDict is a temporary dictionary to store added data information
                        addedDataDict = {}
                        # search data.hdr files in selected folders and their subfolders using glob
                        for path in filePaths:
                            dataPath = f"{path}/**/data.hdr"
                            for dataPath in sorted(glob.glob(dataPath, recursive=True), key=len):
                                dataDir = dataPath.replace("\\","/").split("/data.hdr", 1)[0]
                                if dataDir in existingPaths:
                                    print(f"data path already exists: {dataDir}")
                                    continue
                                addedDataDict[dataDir] = {}
                            self.advanced_label_aggregation_datalist_tableview.setRowCount(currentTableRow + len(addedDataDict))

                        # create object for DataList using addedDataDict
                        for idx, key in enumerate(addedDataDict.keys()):
                            index = currentTableRow + idx
                            # create object using create_obj function
                            addedDataDict[key] = {
                                "idx":index,
                                "use":True,
                                "obj_idx":self.advanced_label_aggregation_datalist_tableview.create_obj(index, obj_type="item", obj_list=str(index)),
                                "obj_path":self.advanced_label_aggregation_datalist_tableview.create_obj(index, obj_type="item", obj_list=key),
                                "objSetting":self.advanced_label_aggregation_datalist_tableview.create_obj(index, obj_type="widget", obj_list=["toggle:"])
                            }
                            # set object in tableview
                            if not self.advanced_label_aggregation_datalist_tableview.item(index, 0):
                                self.advanced_label_aggregation_datalist_tableview.setItem(index, 0, addedDataDict[key]["obj_idx"])
                                self.advanced_label_aggregation_datalist_tableview.setItem(index, 1, addedDataDict[key]["obj_path"])
                                self.advanced_label_aggregation_datalist_tableview.setCellWidget(index, 2, addedDataDict[key]["objSetting"]["widget"])

                                addedDataDict[key]["objSetting"]["toggle"].setChecked(True)
                                addedDataDict[key]["objSetting"]["toggle"].toggled.connect(lambda checked, key=key: self.toggleEvent(eventMode.USE_DATA, key))
                        self.adv_data_list_info.update(addedDataDict)

        elif mode == eventMode.CLEAR_DATA:
            self.clearDataTable()
        
        elif mode == eventMode.START:
            if self.worker_id is None:
                # Lock UI during processing
                self.lockSettingUi()

                # Clear textedit 
                self.advanced_label_aggregation_status_textedit.clear()
                
                self.advanced_label_aggregation_status_textedit.appendPlainText(f"{self.mode}\n{self.dash * 100}")
                self.advanced_label_aggregation_status_textedit.appendPlainText("\nParameter Setting:\n")

                # Print parameter settings
                for idx in self.adv_model_info.keys():
                    parameterType = self.adv_model_info[idx]["objTip"]["label"].text()

                    if idx == "camera":  # ComboBox (Hyperspectral Type)
                        value = self.adv_model_info["camera"]["objSetting"]["combobox"].currentText()
                    elif idx == "fileName":  # LineEdit (File Name)
                        value = self.adv_model_info["fileName"]["objSetting"]["lineedit"].text()
                    elif idx == "savePath":  # LineEdit (Save Path)
                        value = self.adv_model_info["savePath"]["objSetting"]["lineedit"].text()
                    elif idx == "useCommonReference":  # Toggle (Use Common Reference)
                        value = self.adv_model_info["useCommonReference"]["objSetting"]["toggle"].isChecked()
                    elif idx == "commonReferencePath":  # LineEdit (Reference Path)
                        if not self.adv_model_info["useCommonReference"]["objSetting"]["toggle"].isChecked():
                            value = "None"
                        else:
                            value = self.adv_model_info["commonReferencePath"]["objSetting"]["lineedit"].text()

                    parameterString = f"{parameterType}: {value}"
                    self.advanced_label_aggregation_status_textedit.appendPlainText(parameterString)
                self.advanced_label_aggregation_status_textedit.appendPlainText(f"\n{self.dash * 100}")

                # Start processing
                self.worker_1.staging(self.labelAggregation)
                self.worker_id = self.worker_1.cur_id
                self.worker_1.start()
            
            else:
                # prevents re-entering the start routine if it is triggered again while a worker is already running
                # This can happen due to rapid repeated clicks or unexpected external calls
                messageBox(mode=MESSAGE_BOX_INFORMATION,
                           title=self.lang.get("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_msg_warning_already_allocated_title"), 
                           text=f'{self.lang.get("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_msg_warning_already_allocated_message")} Worker ID: {self.worker_id}', 
                           buttons={self.lang.get("advanced", "messageBox", "msgOk"): "accept"})

        elif mode == eventMode.STOP:
            response = messageBox(mode=MESSAGE_BOX_CONFIRMATION, 
                                  title=self.lang.get("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_msg_stop_title"), 
                                  text=self.lang.get("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_msg_stop_message"), 
                                  buttons={self.lang.get("main", "messageBox", "msgYes"): "accept", self.lang.get("main", "messageBox", "msgNo"): "reject"})
            if response == "accept":
                self.thread_interrupted = True

    def checkStopRequest(self):
        """
            @description: Check if there is a stop request from the user and handle it by emitting a message and raising an exception to stop the process
            @author: GaEun Hwang (2026.03.18)
        """
        if self.thread_interrupted:
            self.string_signal.emit("Process Stopped...")
            raise InterruptedError("Stop Requested")

    def labelAggregation(self) -> None:
        """
            @description: Main function for label aggregation mode
            @author : JiHoon
            @history:
                1. GaEun Hwang(26.01.23): 
                    - Wrapped main function with try-except for thread interruption handling
                    - Add checkStopRequest() calls at strategic points
                    - Add confirmParameter() to validate parameters before processing
                    - Add seperateData() to separate normal and abnormal data
        """
        try:
            self.gen = gen_module()
            hyperspectralType = self.adv_model_info["camera"]["objSetting"]["combobox"].currentText()
            fileName = self.adv_model_info["fileName"]["objSetting"]["lineedit"].text()
            save_path = self.adv_model_info["savePath"]["objSetting"]["lineedit"].text()
            useCommonReference = self.adv_model_info["useCommonReference"]["objSetting"]["toggle"].isChecked()
            commonReferencePath = self.adv_model_info["commonReferencePath"]["objSetting"]["lineedit"].text() if useCommonReference else None
            savePath = []
            dataPath = [key for key, value in self.adv_data_list_info.items() if value["use"]]
            
            # check thread interruption before start each processing
            self.checkStopRequest()
            # confirm parameter and dataset validity
            self.confirmParameter(hyperspectralType, save_path, commonReferencePath, dataPath)
            self.string_signal.emit(f"Start Aggregation...\n")
            self.string_signal.emit(f"Total data paths to process: {len(dataPath)}\n")
            
            self.checkStopRequest()
            # separate data to normal and abnormal
            self.seperateData(dataPath, commonReferencePath)
            normalDataDict = self.seperatedData["normal"]
            abnormalDataDict = self.seperatedData["abnormal"]
            self.string_signal.emit(f"Total normal data: {len(normalDataDict['data'])}\n")
            self.string_signal.emit(f"Total abnormal data: {len(abnormalDataDict['data'])}\n")

            self.checkStopRequest()
            # create merged data
            if len(normalDataDict["data"]) != 0:
                # generate merged normal data
                # send checkThreadInterruption function to gen_merge_raw function for interruption handling during processing
                savePath.extend(self.gen.gen_merge_raw(save_path, normalDataDict["data"], normalDataDict["label"],
                                                    normalDataDict["ref"], fileName+"_normal", hyperspectralType))
            
            self.checkStopRequest()
            if len(abnormalDataDict["data"]) != 0:
                savePath.extend(self.gen.gen_merge_raw(save_path, abnormalDataDict["data"], abnormalDataDict["label"],
                                                    abnormalDataDict["ref"], fileName+"_abnormal", hyperspectralType))

            self.checkStopRequest()
            for path in savePath:
                # save data.json each merged data
                self.saveJsonData(path, fileName)

            self.string_signal.emit(f"Finish Aggregation...\n")
            self.string_signal.emit(f"{self.dash * 100}\n")
            self.string_signal.emit(f"Saved at {savePath}\n")
        
        except InterruptedError as e:
            print(f"Label aggregation process was interrupted: {e}")
            return

        except Exception as e:
            print(f"Error occurred during label aggregation: {e}")
            return

    def confirmParameter(self, hyperspectralType, savePath, commonReferencePath, dataPath):
        """
            @description: Confirm parameter & Dataset validity
            @author : GaEun Hwang (26.01.23)
        """
        # Get sample, band info using gen_hdr_info function
        # sample and band, files will be used to check dataset validity
        sample = str(self.gen.gen_hdr_info(hyperspectralType).get("samples"))
        band = str(self.gen.gen_hdr_info(hyperspectralType).get("bands"))
        files = ["data.raw", "data.hdr", "WHITEREF.raw", "WHITEREF.hdr", "DARKREF.raw", "DARKREF.hdr", "label.npy", "data.json"]

        # Check Save Path
        if not os.path.isdir(savePath):
            self.abort(f"\nCheck your Save path at '{savePath}'\n")

        # Check Common Reference Path and file is valid
        if commonReferencePath is not None:
            for refName in ("WHITEREF", "DARKREF"):
                rawPath = os.path.join(commonReferencePath, f"{refName}.raw")
                hdrPath = os.path.join(commonReferencePath, f"{refName}.hdr")
                # check file is exist
                if not os.path.isfile(rawPath) or not os.path.isfile(hdrPath):
                    self.abort(f"\nMissing {refName} file at '{commonReferencePath}'\n")
                refHdr = spectral.io.envi.read_envi_header(hdrPath)
                # check file type is matched with hyperspectral type using samples and bands info
                if refHdr.get("samples") != sample or refHdr.get("bands") != band:
                    self.abort(f"\n{refName} is not {hyperspectralType} data. Check your common reference at '{commonReferencePath}'\n")
        
        # Check files(data, reference, label, json) dataset
        if len(dataPath) != 0:
            for path in dataPath:
                # before start processing each data, check thread interruption
                for file in files:
                    # Check file is exist
                    if not os.path.isfile(os.path.join(path, file)):
                        self.abort(f"\nMissing {file} file at '{path}'\n")
                # Check file type is matched with hyperspectral type
                hdr = spectral.io.envi.read_envi_header(os.path.join(path, "data.hdr"))
                whiteRefHdr = spectral.io.envi.read_envi_header(os.path.join(path, "WHITEREF.hdr"))
                darkRefHdr = spectral.io.envi.read_envi_header(os.path.join(path, "DARKREF.hdr"))
                label = np.load(os.path.join(path, "label.npy"))

                # Check data is matched with hyperspectral type using samples and bands info
                if hdr.get("samples") != sample and hdr.get("bands") != band:
                    self.abort(f"\nDataset contains not {hyperspectralType} data. Check your data at '{path}'\n")
                if whiteRefHdr.get("samples") != sample and whiteRefHdr.get("bands") != band:
                    self.abort(f"\nWHITEREF is not {hyperspectralType} data. Check your WHITEREF at '{path}'\n")
                if darkRefHdr.get("samples") != sample and darkRefHdr.get("bands") != band:
                    self.abort(f"\nDARKREF is not {hyperspectralType} data. Check your DARKREF at '{path}'\n")
                elif label.shape[1] != int(sample):
                    self.abort(f"\nLabel shape is not matched with data shape. Check your label at '{path}'\n")
        else:
            self.abort("\nData path is not set.\n")

    def seperateData(self, dataPath, commonReferencePath):
        """
            @description: Separate data to normal and abnormal
            @author: GaEun Hwang (26.01.23)
        """
        self.seperatedData["normal"] = {"data": [], "label": [], "ref": []}
        self.seperatedData["abnormal"] = {"data": [], "label": [], "ref": []}
        self.jsonInfo = {}

        for index, path in enumerate(dataPath, start=1):
            # before start processing each data, check thread interruption
            self.string_signal.emit(f"[{index}/{len(dataPath)}] {path}\n")            
            label = np.load(path + "/label.npy")
            raw = spectral.io.envi.open(path + "/data.hdr", path + "/data.raw").load()

            # save label info from data.json -> it will be used when saving data.json for merged data
            jsonInfo = json.load(open(path + "/data.json", 'r', encoding='utf-8'))
            for key, value in jsonInfo["label_info"].items():
                self.jsonInfo[key] = {"label_name": value["label_name"], 
                                    "label_color": value["label_color"]}
            
            # if use common reference, change reference path
            if commonReferencePath is not None:
                path = commonReferencePath

            # use reference mean(axis=0)
            whiteRef = spectral.io.envi.open(path + "/WHITEREF.hdr", path + "/WHITEREF.raw").load().mean(axis=0)
            darkRef = spectral.io.envi.open(path + "/DARKREF.hdr", path + "/DARKREF.raw").load().mean(axis=0)

            normalIndex = np.where((label == 1) | (label == 2))
            abnormalIndex = np.where(label >= 3)

            # extract data
            normalRaw, normalWhiteRef, normalDarkRef, normalLabel = self.extractDataUsingIndex(raw, whiteRef, darkRef, label, normalIndex)
            abnormalRaw, abnormalWhiteRef, abnormalDarkRef, abnormalLabel = self.extractDataUsingIndex(raw, whiteRef, darkRef, label, abnormalIndex)

            self.seperatedData["normal"]["data"].append(normalRaw)
            self.seperatedData["normal"]["label"].append(normalLabel)
            self.seperatedData["normal"]["ref"].append((normalWhiteRef, normalDarkRef))

            self.seperatedData["abnormal"]["data"].append(abnormalRaw)
            self.seperatedData["abnormal"]["label"].append(abnormalLabel)
            self.seperatedData["abnormal"]["ref"].append((abnormalWhiteRef, abnormalDarkRef))

        self.seperatedData["normal"]["data"] = np.concatenate(self.seperatedData["normal"]["data"], axis=0)
        self.seperatedData["normal"]["label"] = np.concatenate(self.seperatedData["normal"]["label"], axis=0)
        normalWhiteRefs = [ref[0] for ref in self.seperatedData["normal"]["ref"]]
        normalDarkRefs = [ref[1] for ref in self.seperatedData["normal"]["ref"]]
        self.seperatedData["normal"]["ref"] = (np.concatenate(normalWhiteRefs, axis=0),np.concatenate(normalDarkRefs, axis=0))
        
        self.seperatedData["abnormal"]["data"] = np.concatenate(self.seperatedData["abnormal"]["data"], axis=0)
        self.seperatedData["abnormal"]["label"] = np.concatenate(self.seperatedData["abnormal"]["label"], axis=0)
        abnormalWhiteRefs = [ref[0] for ref in self.seperatedData["abnormal"]["ref"]]
        abnormalDarkRefs = [ref[1] for ref in self.seperatedData["abnormal"]["ref"]]
        self.seperatedData["abnormal"]["ref"] = (np.concatenate(abnormalWhiteRefs, axis=0),np.concatenate(abnormalDarkRefs, axis=0))

    def extractDataUsingIndex(self, dataRaw, whiteRef, darkRef, label, index):
        """
            @description: Extract data(data.raw, WHITEREF.raw, DARKREF.raw, label.npy) using index
            @author: GaEun Hwang (26.02.04)
        """
        extractedDataRaw = dataRaw[index]
        extractedWhiteRef = whiteRef[index[1]]
        extractedDarkRef = darkRef[index[1]]
        extractedLabel = label[index]

        return extractedDataRaw, extractedWhiteRef, extractedDarkRef, extractedLabel

    def saveJsonData(self, savePath, fileName):
        """
            @description: Save data.json about merged data
            @author: GaEun Hwang (26.01.30)
        """
        # before start processing, check thread interruption
        time_ = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(time.time()))
        label = np.unique(np.load(savePath + "/label.npy")).astype(str)

        jsonDict = {
            "data_info": fileName,
            "time": time_,
            "label_info": {}
        }
        # if label exists in self.jsonInfo, save label info to jsonDict
        for key in self.jsonInfo.keys():
            if key in label: 
                jsonDict["label_info"][key] = {
                    "label_name": self.jsonInfo[key]["label_name"],
                    "label_color": self.jsonInfo[key]["label_color"]
                }
        with open(savePath +'/data.json', 'w', encoding='utf-8') as fp:
            json.dump(jsonDict, fp,indent="\t", ensure_ascii=False)

    def clearDataTable(self):
        """
            @description: clear data list in tableview
            @author : Jihoon
        """
        self.advanced_label_aggregation_datalist_tableview.clear()
        self.advanced_label_aggregation_datalist_tableview.setRowCount(4)
        self.advanced_label_aggregation_datalist_tableview.setHorizontalHeaderLabels(self.lang.get("advanced", "advanced_label_aggregation_main", "advanced_label_aggregation_datalist_tableview")[1])
        self.adv_data_list_info = {}

    def updateTextStatus(self, string):
        """
            @description: Add text to the textedit for status update
            @author : JiHoon
        """
        self.advanced_label_aggregation_status_textedit.appendPlainText(string)

    def abort(self, message):
        """
            @description: Abort the process with an error message
            @author : GaEun Hwang (26.01.23)
        """
        self.string_signal.emit(f"[ERROR]{message}")
        raise Exception(message)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    ui = advanced_label_aggregation_Form()
    sys.exit(app.exec_())
