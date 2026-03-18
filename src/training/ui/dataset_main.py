import os
import json
import copy
import spectral
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFileDialog, QListView, QTreeView, QAbstractItemView

from training.stylesheet.stylesheet_dataset_main import stylesheet

from utils.shared import config_path
from utils.custom_ui import messageBox
from constants.constants import MESSAGE_BOX_INFORMATION

class DatasetFrame(QtWidgets.QFrame):
    def __init__(self, dataset_type, dataset_form):
        super().__init__()
        self.setAcceptDrops(True)
        self.dataset_type = dataset_type
        self.dataset_form = dataset_form
    
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        self.dataset_form.add_dataset(self.dataset_type, True, None, [u.toLocalFile() for u in event.mimeData().urls()], False)

class PropLineEdit(QtWidgets.QLineEdit):
    def __init__(self, dataset_form, dataset_type, path=None):
        super().__init__()
        self.dataset_form = dataset_form
        self.dataset_type = dataset_type
        self.path = path

        self.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("^(0(\.\d{1,3})?|1(\.0{1,3})?)$")))
        self.setAlignment(QtCore.Qt.AlignCenter)

    def focusOutEvent(self, event):
        str_value = self.text()
        float_value = float(str_value)
        self.setText(str_value)
        self.dataset_form.default_prop[self.dataset_type] = float_value
        if self.path:
            self.dataset_form.update_prop(self.dataset_type, self.path, float_value)
        else:
            self.dataset_form.update_all_prop(self.dataset_type, float_value)
        return super().focusOutEvent(event)

# dataset_type: train, val, test
class Dataset_Form(QtWidgets.QWidget):
    def __init__(self, Sync, lang) -> None:
        super().__init__()
        self.lang = lang
        self.init(Sync=Sync)
        self.init_ui(self)
        self.setup_ui()
        self.init_function()
        self.init_config()

        self.lang.set("training", "dataset_main", "update_dataset_text", self.update_dataset_text)

    def init(self, Sync=None):
        self.valid_items = ["data.raw", "data.hdr", "label.npy"]
        self.last_path = ""
        self.default_prop = {
            "train": 0.4,
            "val": 0.1,
            "test": 1.0
        }
        self.metadata_shared_dict = {
            "wavelength": ""
        }
        self.dataset_layout_dict = {
            "train": {}, # path: [is_use, prop]
            "val": {},
            "test": {}
        }
        self.dataset_shared_dict = {
            "train": {},
            "val": {},
            "test": {},
        }
        
        Sync.dataset_shared_dict = self.dataset_shared_dict
        Sync.metadata_shared_dict = self.metadata_shared_dict
        Sync.dataset_signal.connect(self.dataset_signal_receiver)
        self.hyperparameter_signal = Sync.hyperparameter_signal

        self.config = Sync.config
        self._config = copy.deepcopy(Sync.config)

    def init_ui(self, Form):
        Form.setObjectName("Dataset_Form")
        Form.setWindowTitle("Dataset_Form")
        Form.setStyleSheet(stylesheet)
        self.MainFormLayout = QtWidgets.QVBoxLayout(Form)
        self.MainFormLayout.setObjectName("MainFormLayout")

        self.SubFormCommonLayout = QtWidgets.QHBoxLayout()
        self.SubFormCommonLayout.setObjectName("SubFormCommonLayout")

        self.SubFormLayout = QtWidgets.QHBoxLayout()
        self.SubFormLayout.setObjectName("FormLayout")
        
        # =============== Icon Area ===============
        self.icon_add = QIcon()
        self.icon_add.addPixmap(QPixmap("ico/training/folder/folder_add.png"), QIcon.Normal, QIcon.Off)

        self.icon_add_all = QIcon()
        self.icon_add_all.addPixmap(QPixmap("ico/training/folder/folder_add_all.png"), QIcon.Normal, QIcon.Off)

        self.icon_clear = QIcon()
        self.icon_clear.addPixmap(QPixmap("ico/training/folder/folder_clear.png"), QIcon.Normal, QIcon.Off)

        self.icon_clear_all = QIcon()
        self.icon_clear_all.addPixmap(QPixmap("ico/training/folder/folder_clear_all.png"), QIcon.Normal, QIcon.Off)

        self.icon_remove = QIcon()
        self.icon_remove.addPixmap(QPixmap("ico/training/folder/folder_remove.png"), QIcon.Normal, QIcon.Off)

        self.icon_checkbox = QIcon()
        self.icon_checkbox.addPixmap(QPixmap("ico/training/checkbox/check_off.png"), QIcon.Normal, QIcon.Off)
        self.icon_checkbox.addPixmap(QPixmap("ico/training/checkbox/check_on.png"), QIcon.Active, QIcon.On)\

        # =============== Training Form Area ===============
        self.TrainingFrame = DatasetFrame("train", self)
        self.TrainingFrame.setObjectName("TrainingFrame")

        self.TrainingFrameLayout = QtWidgets.QVBoxLayout(self.TrainingFrame)
        self.TrainingFrameLayout.setObjectName("TrainingFrameLayout")

        self.TrainingInfoLayout = QtWidgets.QHBoxLayout()
        self.TrainingInfoLayout.setObjectName("TrainingInfoLayout")

        self.TrainingInfoLabel = QtWidgets.QLabel(self.TrainingFrame)
        self.TrainingInfoLabel.setObjectName("TrainingInfoLabel")

        self.TrainingUseAllButton = QtWidgets.QPushButton(self.TrainingFrame)
        self.TrainingUseAllButton.setObjectName("TrainingUseAllButton")

        self.TrainingAddButton = QtWidgets.QPushButton(self.TrainingFrame)
        self.TrainingAddButton.setObjectName("TrainingAddButton")

        self.TrainingResetButton = QtWidgets.QPushButton(self.TrainingFrame)
        self.TrainingResetButton.setObjectName("TrainingResetButton")

        self.TrainingScrollArea = QtWidgets.QScrollArea(self.TrainingFrame)
        self.TrainingScrollArea.setObjectName("TrainingScrollArea")

        self.TrainingWidget = QtWidgets.QWidget()
        self.TrainingWidget.setObjectName("TrainingWidget")

        self.TrainingWidgetLayout = QtWidgets.QVBoxLayout(self.TrainingWidget)
        self.TrainingWidgetLayout.setObjectName("TrainingWidgetLayout")

        self.TrainingSubLabelWidget = QtWidgets.QWidget(self.TrainingWidget)
        self.TrainingSubLabelWidget.setObjectName("TrainingSubLabelWidget")

        self.TrainingSubLabelWidgetLayout = QtWidgets.QHBoxLayout(self.TrainingSubLabelWidget)
        self.TrainingSubLabelWidgetLayout.setObjectName("TrainingSubLabelWidgetLayout")

        self.TrainingUseLabel = QtWidgets.QLabel(self.TrainingSubLabelWidget)
        self.TrainingUseLabel.setObjectName("TrainingUseLabel")

        self.TrainingPathLabel = QtWidgets.QLabel(self.TrainingSubLabelWidget)
        self.TrainingPathLabel.setObjectName("TrainingPathLabel")

        self.TrainingPropLabel = QtWidgets.QLabel(self.TrainingSubLabelWidget)
        self.TrainingPropLabel.setObjectName("TrainingPropLabel")
        
        self.TrainingRemoveLabel = QtWidgets.QLabel(self.TrainingSubLabelWidget)
        self.TrainingRemoveLabel.setObjectName("TrainingRemoveLabel")
        
        self.TrainingSubInputWidget = QtWidgets.QWidget(self.TrainingWidget)
        self.TrainingSubInputWidget.setObjectName("TrainingSubInputWidget")

        self.TrainingSubInputWidgetLayout = QtWidgets.QHBoxLayout(self.TrainingSubInputWidget)
        self.TrainingSubInputWidgetLayout.setObjectName("TrainingSubInputWidgetLayout")

        self.TrainingInputPathLabel = QtWidgets.QLabel(self.TrainingSubInputWidget) # use for spacing
        self.TrainingInputPathLabel.setObjectName("TrainingInputPathLabel")

        self.TrainingAllProp = PropLineEdit(self, "train")
        self.TrainingAllProp.setObjectName("TrainingAllProp")

        self.TrainingSubFrame = QtWidgets.QFrame(self.TrainingWidget)
        self.TrainingSubFrame.setObjectName("TrainingSubFrame")

        self.TrainingSubFrameLayout = QtWidgets.QVBoxLayout(self.TrainingSubFrame)
        self.TrainingSubFrameLayout.setObjectName("TrainingSubFrameLayout")

        # =============== Validation Form Area ===============
        self.ValidatioinFrame = DatasetFrame("val", self)
        self.ValidatioinFrame.setObjectName("ValidatioinFrame")

        self.ValidationFrameLayout = QtWidgets.QVBoxLayout(self.ValidatioinFrame)
        self.ValidationFrameLayout.setObjectName("ValidationFrameLayout")

        self.ValidationInfoLayout = QtWidgets.QHBoxLayout()
        self.ValidationInfoLayout.setObjectName("ValidationInfoLayout")

        self.ValidationInfoLabel = QtWidgets.QLabel(self.ValidatioinFrame)
        self.ValidationInfoLabel.setObjectName("ValidationInfoLabel")

        self.ValidationUseAllButton = QtWidgets.QPushButton(self.ValidatioinFrame)
        self.ValidationUseAllButton.setObjectName("ValidationUseAllButton")

        self.ValidationAddButton = QtWidgets.QPushButton(self.ValidatioinFrame)
        self.ValidationAddButton.setObjectName("ValidationAddButton")

        self.ValidationResetButton = QtWidgets.QPushButton(self.ValidatioinFrame)
        self.ValidationResetButton.setObjectName("ValidationResetButton")

        self.ValidationScrollArea = QtWidgets.QScrollArea(self.ValidatioinFrame)
        self.ValidationScrollArea.setObjectName("ValidationScrollArea")

        self.ValidationWidget = QtWidgets.QWidget()
        self.ValidationWidget.setObjectName("ValidationWidget")

        self.ValidationWidgetLayout = QtWidgets.QVBoxLayout(self.ValidationWidget)
        self.ValidationWidgetLayout.setObjectName("ValidationWidgetLayout")

        self.ValidationSubLabelWidget = QtWidgets.QWidget(self.ValidationWidget)
        self.ValidationSubLabelWidget.setObjectName("ValidationSubLabelWidget")

        self.ValidationSubLabelWidgetLayout = QtWidgets.QHBoxLayout(self.ValidationSubLabelWidget)
        self.ValidationSubLabelWidgetLayout.setObjectName("ValidationSubLabelWidgetLayout")

        self.ValidationUseLabel = QtWidgets.QLabel(self.ValidationSubLabelWidget)
        self.ValidationUseLabel.setObjectName("ValidationUseLabel")

        self.ValidationPathLabel = QtWidgets.QLabel(self.ValidationSubLabelWidget)
        self.ValidationPathLabel.setObjectName("ValidationPathLabel")
    
        self.ValidationPropLabel = QtWidgets.QLabel(self.ValidationSubLabelWidget)
        self.ValidationPropLabel.setObjectName("ValidationPropLabel")

        self.ValidationRemoveLabel = QtWidgets.QLabel(self.ValidationSubLabelWidget)
        self.ValidationRemoveLabel.setObjectName("ValidationRemoveLabel")

        self.ValidationSubInputWidget = QtWidgets.QWidget(self.ValidationWidget)
        self.ValidationSubInputWidget.setObjectName("ValidationSubInputWidget")

        self.ValidationSubInputWidgetLayout = QtWidgets.QHBoxLayout(self.ValidationSubInputWidget)
        self.ValidationSubInputWidgetLayout.setObjectName("ValidationSubInputWidgetLayout")

        self.ValidationInputPathLabel = QtWidgets.QLabel(self.ValidationSubInputWidget) # use for spacing
        self.ValidationInputPathLabel.setObjectName("ValidationInputPathLabel")

        self.ValidationAllProp = PropLineEdit(self, "val")
        self.ValidationAllProp.setObjectName("ValidationAllProp")

        self.ValidationSubFrame = QtWidgets.QFrame(self.ValidationWidget)
        self.ValidationSubFrame.setObjectName("ValidationSubFrame")

        self.ValidationSubFrameLayout = QtWidgets.QVBoxLayout(self.ValidationSubFrame)
        self.ValidationSubFrameLayout.setObjectName("ValidationSubFrameLayout")

        # =============== Test Form Area ===============
        self.TestFrame = DatasetFrame("test", self)
        self.TestFrame.setObjectName("TestFrame")

        self.TestFrameLayout = QtWidgets.QVBoxLayout(self.TestFrame)
        self.TestFrameLayout.setObjectName("TestFrameLayout")

        self.TestInfoLayout = QtWidgets.QHBoxLayout()
        self.TestInfoLayout.setObjectName("TestInfoLayout")

        self.TestInfoLabel = QtWidgets.QLabel(self.TestFrame)
        self.TestInfoLabel.setObjectName("TestInfoLabel")

        self.TestUseAllButton = QtWidgets.QPushButton(self.TestFrame)
        self.TestUseAllButton.setObjectName("TestUseAllButton")

        self.TestAddButton = QtWidgets.QPushButton(self.TestFrame)
        self.TestAddButton.setObjectName("TestAddButton")

        self.TestResetButton = QtWidgets.QPushButton(self.TestFrame)
        self.TestResetButton.setObjectName("TestResetButton")

        self.TestScrollArea = QtWidgets.QScrollArea(self.TestFrame)
        self.TestScrollArea.setObjectName("TestScrollArea")

        self.TestWidget = QtWidgets.QWidget()
        self.TestWidget.setObjectName("TestWidget")

        self.TestWidgetLayout = QtWidgets.QVBoxLayout(self.TestWidget)
        self.TestWidgetLayout.setObjectName("TestWidgetLayout")
        
        self.TestSubLabelWidget = QtWidgets.QWidget(self.TestWidget)
        self.TestSubLabelWidget.setObjectName("TestSubLabelWidget")

        self.TestSubLabelWidgetLayout = QtWidgets.QHBoxLayout(self.TestSubLabelWidget)
        self.TestSubLabelWidgetLayout.setObjectName("TestSubLabelWidgetLayout")

        self.TestUseLabel = QtWidgets.QLabel(self.TestSubLabelWidget)
        self.TestUseLabel.setObjectName("TestUseLabel")

        self.TestPathLabel = QtWidgets.QLabel(self.TestSubLabelWidget)
        self.TestPathLabel.setObjectName("TestPathLabel")

        self.TestPropLabel = QtWidgets.QLabel(self.TestSubLabelWidget)
        self.TestPropLabel.setObjectName("TestPropLabel")

        self.TestRemoveLabel = QtWidgets.QLabel(self.TestSubLabelWidget)
        self.TestRemoveLabel.setObjectName("TestRemoveLabel")

        self.TestSubInputWidget = QtWidgets.QWidget(self.TestWidget)
        self.TestSubInputWidget.setObjectName("TestSubInputWidget")

        self.TestSubInputWidgetLayout = QtWidgets.QHBoxLayout(self.TestSubInputWidget)
        self.TestSubInputWidgetLayout.setObjectName("TestSubInputWidgetLayout")

        self.TestInputPathLabel = QtWidgets.QLabel(self.TestSubInputWidget) # use for spacing
        self.TestInputPathLabel.setObjectName("TestInputPathLabel")

        self.TestAllProp = PropLineEdit(self, "test")
        self.TestAllProp.setObjectName("TestAllProp")

        self.TestSubFrame = QtWidgets.QFrame(self.TestWidget)
        self.TestSubFrame.setObjectName("TestSubFrame")

        self.TestSubFrameLayout = QtWidgets.QVBoxLayout(self.TestSubFrame)
        self.TestSubFrameLayout.setObjectName("TestSubFrameLayout")

        self.LoadAllButton = QtWidgets.QPushButton()
        self.LoadAllButton.setObjectName("LoadAllButton")

        self.ClearAllButton = QtWidgets.QPushButton()
        self.ClearAllButton.setObjectName("ClearAllButton")

        # load used dataset settings (path, porp, ...)
        self.LoadConfigButton = QtWidgets.QPushButton()
        self.LoadConfigButton.setObjectName("LoadConfigButton")

        QtCore.QMetaObject.connectSlotsByName(Form)

    def setup_ui(self):     
        # =============== Training Form Area ===============
        self.TrainingFrame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.TrainingFrame.setFrameShadow(QtWidgets.QFrame.Raised)

        # Training Layout
        self.TrainingInfoLayout.addWidget(self.TrainingInfoLabel)

        self.TrainingAddButton.setIcon(self.icon_add)
        self.TrainingInfoLayout.addWidget(self.TrainingAddButton)
        self.lang.set("training", "dataset_main", "TrainingAddButton", self.TrainingAddButton)

        self.TrainingInfoLayout.setStretch(0, 1)
        self.TrainingFrameLayout.addLayout(self.TrainingInfoLayout)

        self.TrainingUseAllButton.setIcon(self.icon_checkbox)
        self.TrainingUseAllButton.setCheckable(True)
        self.TrainingUseAllButton.setChecked(True)
        self.TrainingUseAllButton.setDisabled(True)
        self.lang.set("training", "dataset_main", "TrainingUseAllButton", self.TrainingUseAllButton)

        self.TrainingAllProp.setFixedWidth(40)
        self.TrainingAllProp.setText(str(self.default_prop["train"]))

        self.TrainingScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.TrainingScrollArea.setWidgetResizable(True)

        self.TrainingUseLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.TrainingUseLabel.setFixedWidth(30)
        self.TrainingPathLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.TrainingPropLabel.setFixedWidth(35)
        self.TrainingPropLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.TrainingRemoveLabel.setFixedWidth(55)
        self.TrainingRemoveLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.TrainingInputPathLabel.setText("-")
        self.TrainingInputPathLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.TrainingResetButton.setIcon(self.icon_remove)
        self.lang.set("training", "dataset_main", "TrainingResetButton", self.TrainingResetButton)

        self.TrainingSubLabelWidgetLayout.addWidget(self.TrainingUseLabel)
        self.TrainingSubLabelWidgetLayout.addWidget(self.TrainingPathLabel, 1)
        self.TrainingSubLabelWidgetLayout.addWidget(self.TrainingPropLabel)
        self.TrainingSubLabelWidgetLayout.addWidget(self.TrainingRemoveLabel)

        _, _, _, bottom = self.TrainingSubInputWidgetLayout.getContentsMargins()
        self.TrainingSubInputWidgetLayout.setContentsMargins(10, 0, 23, bottom)
        self.TrainingSubInputWidgetLayout.setSpacing(15)
        self.TrainingSubInputWidgetLayout.addWidget(self.TrainingUseAllButton)
        self.TrainingSubInputWidgetLayout.addWidget(self.TrainingInputPathLabel, 1)
        self.TrainingSubInputWidgetLayout.addWidget(self.TrainingAllProp)
        self.TrainingSubInputWidgetLayout.addWidget(self.TrainingResetButton)

        self.TrainingWidgetLayout.addWidget(self.TrainingSubLabelWidget)
        self.TrainingWidgetLayout.addWidget(self.TrainingSubInputWidget)
        self.TrainingWidgetLayout.addWidget(self.TrainingSubFrame, 1, QtCore.Qt.AlignTop)
        self.TrainingWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.TrainingScrollArea.setWidget(self.TrainingWidget)
        self.TrainingFrameLayout.addWidget(self.TrainingScrollArea)
        self.SubFormLayout.addWidget(self.TrainingFrame)
        
        # =============== Validation Form Area ===============
        self.ValidatioinFrame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.ValidatioinFrame.setFrameShadow(QtWidgets.QFrame.Raised)

        # Validation Layout
        self.ValidationInfoLayout.addWidget(self.ValidationInfoLabel)

        self.ValidationAddButton.setIcon(self.icon_add)
        self.ValidationInfoLayout.addWidget(self.ValidationAddButton)
        self.lang.set("training", "dataset_main", "ValidationAddButton", self.ValidationAddButton)

        self.ValidationInfoLayout.setStretch(0, 1)
        self.ValidationFrameLayout.addLayout(self.ValidationInfoLayout)

        self.ValidationUseAllButton.setIcon(self.icon_checkbox)
        self.ValidationUseAllButton.setCheckable(True)
        self.ValidationUseAllButton.setChecked(True)
        self.ValidationUseAllButton.setDisabled(True)
        self.lang.set("training", "dataset_main", "ValidationUseAllButton", self.ValidationUseAllButton)

        self.ValidationAllProp.setFixedWidth(40)
        self.ValidationAllProp.setText(str(self.default_prop["val"]))

        self.ValidationResetButton.setIcon(self.icon_remove)
        self.lang.set("training", "dataset_main", "ValidationResetButton", self.ValidationResetButton)

        self.ValidationScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.ValidationScrollArea.setWidgetResizable(True)

        self.ValidationUseLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.ValidationUseLabel.setFixedWidth(30)
        self.ValidationPathLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.ValidationPropLabel.setFixedWidth(35)
        self.ValidationPropLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.ValidationRemoveLabel.setFixedWidth(55)
        self.ValidationRemoveLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.ValidationInputPathLabel.setText("-")
        self.ValidationInputPathLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.ValidationSubLabelWidgetLayout.addWidget(self.ValidationUseLabel)
        self.ValidationSubLabelWidgetLayout.addWidget(self.ValidationPathLabel, 1)
        self.ValidationSubLabelWidgetLayout.addWidget(self.ValidationPropLabel)
        self.ValidationSubLabelWidgetLayout.addWidget(self.ValidationRemoveLabel)

        _, _, _, bottom = self.ValidationSubInputWidgetLayout.getContentsMargins()
        self.ValidationSubInputWidgetLayout.setContentsMargins(10, 0, 23, bottom)
        self.ValidationSubInputWidgetLayout.setSpacing(15)
        self.ValidationSubInputWidgetLayout.addWidget(self.ValidationUseAllButton)
        self.ValidationSubInputWidgetLayout.addWidget(self.ValidationInputPathLabel, 1)
        self.ValidationSubInputWidgetLayout.addWidget(self.ValidationAllProp)
        self.ValidationSubInputWidgetLayout.addWidget(self.ValidationResetButton)

        self.ValidationWidgetLayout.addWidget(self.ValidationSubLabelWidget)
        self.ValidationWidgetLayout.addWidget(self.ValidationSubInputWidget)
        self.ValidationWidgetLayout.addWidget(self.ValidationSubFrame, 1, QtCore.Qt.AlignTop)
        self.ValidationWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.ValidationScrollArea.setWidget(self.ValidationWidget)
        self.ValidationFrameLayout.addWidget(self.ValidationScrollArea)
        self.SubFormLayout.addWidget(self.ValidatioinFrame)

        # =============== Test Form Area ===============
        self.TestFrame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.TestFrame.setFrameShadow(QtWidgets.QFrame.Raised)

        # Test Layout
        self.TestInfoLayout.addWidget(self.TestInfoLabel)

        self.TestAddButton.setIcon(self.icon_add)
        self.TestInfoLayout.addWidget(self.TestAddButton)
        self.lang.set("training", "dataset_main", "TestAddButton", self.TestAddButton)

        self.TestInfoLayout.setStretch(0, 1)
        self.TestFrameLayout.addLayout(self.TestInfoLayout)

        self.TestUseAllButton.setIcon(self.icon_checkbox)
        self.TestUseAllButton.setCheckable(True)
        self.TestUseAllButton.setChecked(True)
        self.TestUseAllButton.setDisabled(True)
        self.lang.set("training", "dataset_main", "TestUseAllButton", self.TestUseAllButton)

        self.TestAllProp.setFixedWidth(40)
        self.TestAllProp.setText(str(self.default_prop["test"]))

        self.TestResetButton.setIcon(self.icon_remove)
        self.lang.set("training", "dataset_main", "TestResetButton", self.TestResetButton)

        self.TestScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.TestScrollArea.setWidgetResizable(True)
        
        self.TestUseLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.TestUseLabel.setFixedWidth(30)
        self.TestPathLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.TestPropLabel.setFixedWidth(35)
        self.TestPropLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.TestRemoveLabel.setFixedWidth(55)
        self.TestRemoveLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.TestInputPathLabel.setText("-")
        self.TestInputPathLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.TestSubLabelWidgetLayout.addWidget(self.TestUseLabel)
        self.TestSubLabelWidgetLayout.addWidget(self.TestPathLabel, 1)
        self.TestSubLabelWidgetLayout.addWidget(self.TestPropLabel)
        self.TestSubLabelWidgetLayout.addWidget(self.TestRemoveLabel)
        
        _, _, _, bottom = self.TestSubInputWidgetLayout.getContentsMargins()
        self.TestSubInputWidgetLayout.setContentsMargins(10, 0, 23, bottom)
        self.TestSubInputWidgetLayout.setSpacing(15)
        self.TestSubInputWidgetLayout.addWidget(self.TestUseAllButton)
        self.TestSubInputWidgetLayout.addWidget(self.TestInputPathLabel, 1)
        self.TestSubInputWidgetLayout.addWidget(self.TestAllProp)
        self.TestSubInputWidgetLayout.addWidget(self.TestResetButton)

        self.TestWidgetLayout.addWidget(self.TestSubLabelWidget)
        self.TestWidgetLayout.addWidget(self.TestSubInputWidget)
        self.TestWidgetLayout.addWidget(self.TestSubFrame, 1, QtCore.Qt.AlignTop)
        self.TestWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.TestScrollArea.setWidget(self.TestWidget)
        self.TestFrameLayout.addWidget(self.TestScrollArea)
        self.SubFormLayout.addWidget(self.TestFrame)

        self.lang.set("training", "dataset_main", "LoadAllButton", self.LoadAllButton)
        self.LoadAllButton.setIcon(self.icon_add_all)
        self.LoadAllButton.clicked.connect(lambda: self.add_all_dataset(True))

        self.lang.set("training", "dataset_main", "ClearAllButton", self.ClearAllButton)
        self.ClearAllButton.setIcon(self.icon_clear_all)
        self.ClearAllButton.clicked.connect(lambda: self.reset_all_dataset())

        self.lang.set("training", "dataset_main", "LoadConfigButton", self.LoadConfigButton)
        self.LoadConfigButton.clicked.connect(lambda: self.load_config(True))

        self.SubFormCommonLayout.addWidget(self.LoadAllButton, 0, QtCore.Qt.AlignLeft)
        self.SubFormCommonLayout.addWidget(self.ClearAllButton, 0, QtCore.Qt.AlignLeft)
        self.SubFormCommonLayout.addWidget(self.LoadConfigButton, 1, QtCore.Qt.AlignRight)

        self.MainFormLayout.addLayout(self.SubFormCommonLayout)
        self.MainFormLayout.addLayout(self.SubFormLayout)

    def update_dataset_text(self):
        self.TrainingInfoLabel.setText(f"{self.lang.get('training', 'dataset_main', 'TrainingInfoLabelBase')} ({self.lang.get('training', 'dataset_main', 'InfoLabelTotal')}: {sum([self.dataset_shared_dict['train'][train_path][0] for train_path in self.dataset_shared_dict['train'].keys()])}, {self.lang.get('training', 'dataset_main', 'InfoLabelUse')}: {len(self.dataset_shared_dict['train'])})")
        self.ValidationInfoLabel.setText(f"{self.lang.get('training', 'dataset_main', 'ValidationInfoLabelBase')} ({self.lang.get('training', 'dataset_main', 'InfoLabelTotal')}: {sum([self.dataset_shared_dict['val'][val_path][0] for val_path in self.dataset_shared_dict['val'].keys()])}, {self.lang.get('training', 'dataset_main', 'InfoLabelUse')}: {len(self.dataset_shared_dict['val'])})")
        self.TestInfoLabel.setText(f"{self.lang.get('training', 'dataset_main', 'TestInfoLabelBase')} ({self.lang.get('training', 'dataset_main', 'InfoLabelTotal')}: {sum([self.dataset_shared_dict['test'][test_path][0] for test_path in self.dataset_shared_dict['test'].keys()])}, {self.lang.get('training', 'dataset_main', 'InfoLabelUse')}: {len(self.dataset_shared_dict['test'])})")
        
        self.TrainingUseLabel.setText(self.lang.get("training", "dataset_main", "UseLabel"))
        self.TrainingPathLabel.setText(self.lang.get("training", "dataset_main", "PathLabel"))
        self.TrainingRemoveLabel.setText(self.lang.get("training", "dataset_main", "RemoveLabel"))
        self.TrainingPropLabel.setText(self.lang.get("training", "dataset_main", "PropLabel"))
        
        self.ValidationUseLabel.setText(self.lang.get("training", "dataset_main", "UseLabel"))
        self.ValidationPathLabel.setText(self.lang.get("training", "dataset_main", "PathLabel"))
        self.ValidationRemoveLabel.setText(self.lang.get("training", "dataset_main", "RemoveLabel"))
        self.ValidationPropLabel.setText(self.lang.get("training", "dataset_main", "PropLabel"))
        
        self.TestUseLabel.setText(self.lang.get("training", "dataset_main", "UseLabel"))
        self.TestPathLabel.setText(self.lang.get("training", "dataset_main", "PathLabel"))
        self.TestRemoveLabel.setText(self.lang.get("training", "dataset_main", "RemoveLabel"))
        self.TestPropLabel.setText(self.lang.get("training", "dataset_main", "PropLabel"))

    def init_function(self):
        # Event for Use All Button
        self.TrainingUseAllButton.clicked.connect(lambda: self.select_all_dataset("train", self.TrainingUseAllButton.isChecked()))
        self.ValidationUseAllButton.clicked.connect(lambda: self.select_all_dataset("val", self.ValidationUseAllButton.isChecked()))
        self.TestUseAllButton.clicked.connect(lambda: self.select_all_dataset("test", self.TestUseAllButton.isChecked()))

        # Event for Add Button
        self.TrainingAddButton.clicked.connect(lambda: self.add_dataset("train", True))
        self.ValidationAddButton.clicked.connect(lambda: self.add_dataset("val", True))
        self.TestAddButton.clicked.connect(lambda: self.add_dataset("test", True))

        # Event for Reset Button
        self.TrainingResetButton.clicked.connect(lambda: self.reset_dataset("train"))
        self.ValidationResetButton.clicked.connect(lambda: self.reset_dataset("val"))
        self.TestResetButton.clicked.connect(lambda: self.reset_dataset("test"))

    def get_sub_layout(self, dataset_type:str, path:str, is_use:bool=False, prop:float=0.1):
        sub_layout = QtWidgets.QHBoxLayout()
        sub_layout.setContentsMargins(1, -1, 14, -1)
        sub_layout.setSpacing(15)

        # use checkbox
        use_checkbox = QtWidgets.QPushButton()
        use_checkbox.setText("")
        use_checkbox.setCheckable(True)
        use_checkbox.setIcon(self.icon_checkbox)
        use_checkbox.clicked.connect(lambda: self.select_dataset(dataset_type, path, use_checkbox.isChecked()))
        sub_layout.addWidget(use_checkbox)

        # path editline
        path_editline = QtWidgets.QLineEdit()
        path_editline.setReadOnly(True)
        path_editline.setText(path)
        path_editline.setToolTip(path)
        path_editline.setStyleSheet("QLineEdit{color: gray;}")
        sub_layout.addWidget(path_editline)

        # proportion editline
        proportion_editline = PropLineEdit(self, dataset_type, path)
        proportion_editline.setFixedWidth(40)
        proportion_editline.setText(str(prop))
        sub_layout.addWidget(proportion_editline)

        # remove button
        remove_button = QtWidgets.QPushButton()
        remove_button.setText("")
        remove_button.setIcon(self.icon_remove)
        remove_button.clicked.connect(lambda: self.remove_dataset(dataset_type, path))
        sub_layout.addWidget(remove_button)

        if is_use:
            use_checkbox.setChecked(True)
            path_editline.setStyleSheet("QLineEdit{color: white;}")

        return sub_layout
    
    def get_path_list(self):
        path_list = []
        # execute file dialog and get the selected path list
        file_dialog = QFileDialog(directory=self.last_path)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.findChild(QListView, 'listView').setSelectionMode(QAbstractItemView.ExtendedSelection)
        file_dialog.findChild(QTreeView, 'treeView').setSelectionMode(QAbstractItemView.ExtendedSelection)
        if file_dialog.exec_():
            path_list = file_dialog.selectedFiles()
            
            # last_path
            self.last_path = path_list[0]
            if os.name == "nt":
                self.last_path = path_list[0].replace("/", "\\")
            return path_list
        else:
            return None

    def add_dataset(self, dataset_type:str, is_use:bool=False, prop=None, path_list=None, ignore_message=False):
        path_list = path_list if path_list else self.get_path_list()
        invalid_message_list = []
        if path_list != None:
            for path in path_list:
                # PyQt file dialog return the posix path style
                if os.name == "nt":
                    path = path.replace("/", "\\")

                # get valid path list and invalid path list
                valid_path_list, invalid_path_dict = self.get_valid_path(dataset_type, path, self.valid_items)
                # valid path procedure
                for valid_path in valid_path_list:
                    if valid_path not in self.dataset_layout_dict[dataset_type]:
                        # get new sub-layout
                        prop = prop if prop else self.default_prop[dataset_type]
                        sub_layout = self.get_sub_layout(dataset_type, valid_path, is_use, prop)
                        self.dataset_layout_dict[dataset_type][valid_path] = {"sub_layout": sub_layout}
                        self.dataset_shared_dict[dataset_type][valid_path] = [True if is_use else False, prop]

                        if dataset_type == "train":
                            self.TrainingSubFrameLayout.addLayout(sub_layout)
                        elif dataset_type == "val":
                            self.ValidationSubFrameLayout.addLayout(sub_layout)
                        elif dataset_type == "test":
                            self.TestSubFrameLayout.addLayout(sub_layout)
                        else:
                            raise Exception("Not supported dataset type")
                
                if not ignore_message:
                    # invalid path procedure
                    for invalid_path in invalid_path_dict.keys():
                        if invalid_path_dict[invalid_path]["type"] == "wavelength": # not matched wavelength
                            invalid_message_list.append(f"{self.lang.get('training', 'dataset_main', 'dataset_file_error_wavelength_msg')} {invalid_path}")
                        if invalid_path_dict[invalid_path]["type"] == "path":
                            invalid_message_list.append(f"{self.lang.get('training', 'dataset_main', 'dataset_path_error_not_exists_msg')} {invalid_path}")
                        if invalid_path_dict[invalid_path]["type"] == "files": # files not found 'data.raw, data.hdr, label.npy'
                            missing_item_list = invalid_path_dict[invalid_path]["value"]
                            invalid_message_list.append(f"{self.lang.get('training', 'dataset_main', 'dataset_file_error_missing_msg')} '{', '.join(missing_item_list)}' > {invalid_path}")

            if not ignore_message:
                # messagebox
                """
                    History
                        Yugyeong Hong(2026.02.25): Refactor message box with util method and language support
                """
                if invalid_message_list != []:
                    messageBox(mode=MESSAGE_BOX_INFORMATION,
                               title=self.lang.get("training", "dataset_main", "dataset_file_error_title"),
                               text="\n".join(invalid_message_list),
                               buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
            # update dataset info
            if path_list != []:
                self.update_dataset(dataset_type)
    
    def add_all_dataset(self, is_use:bool=False, path_list=None, ignore_message=False):
        path_list = path_list if path_list else self.get_path_list()
        if path_list:
            [self.add_dataset(dataset_type, is_use, None, path_list, _ignore_message) for dataset_type, _ignore_message in zip(["train", "val", "test"], [ignore_message, True, True])]

    def remove_dataset(self, dataset_type:str, path:str=None):
        sub_layout = None
        # get current sub-layout
        if path in self.dataset_shared_dict[dataset_type]:
            sub_layout = self.dataset_layout_dict[dataset_type].pop(path)["sub_layout"]
            self.dataset_shared_dict[dataset_type].pop(path)
        else:
            raise Exception("Not supported dataset type")

        # remove layout
        if sub_layout != None:
            [sub_layout.itemAt(i).widget().deleteLater() for i in range(sub_layout.count())]
            sub_layout.deleteLater()
        
        # update dataset info
        self.update_dataset(dataset_type)

    def select_dataset(self, dataset_type:str, path:str, is_checked:bool):
        if path in self.dataset_shared_dict[dataset_type]:
            self.dataset_shared_dict[dataset_type][path][0] = is_checked  
            for pos in range(self.dataset_layout_dict[dataset_type][path]["sub_layout"].count()):
                if is_checked:
                    self.dataset_layout_dict[dataset_type][path]["sub_layout"].itemAt(pos).widget().setStyleSheet("QLineEdit{color: white;}")
                else:
                    self.dataset_layout_dict[dataset_type][path]["sub_layout"].itemAt(pos).widget().setStyleSheet("QLineEdit{color: gray;}")

        # update dataset info
        self.update_dataset(dataset_type)
    
    def select_all_dataset(self, dataset_type:str, is_checked:bool):
        assert dataset_type in ["train", "val", "test"], "Not supported dataset type"
        for path in self.dataset_shared_dict[dataset_type].keys():
            self.dataset_shared_dict[dataset_type][path][0] = is_checked
            for pos in range(self.dataset_layout_dict[dataset_type][path]["sub_layout"].count()):
                if is_checked:
                    self.dataset_layout_dict[dataset_type][path]["sub_layout"].itemAt(pos).widget().setStyleSheet("QLineEdit{color: white;}")
                else:
                    self.dataset_layout_dict[dataset_type][path]["sub_layout"].itemAt(pos).widget().setStyleSheet("QLineEdit{color: gray;}")
            self.dataset_layout_dict[dataset_type][path]["sub_layout"].itemAt(0).widget().setChecked(is_checked)

        # update dataset info
        self.update_dataset(dataset_type)
    
    def update_prop(self, dataset_type:str, path:str, value:float):
        assert dataset_type in ["train", "val", "test"], "Not supported dataset type"
        if path in self.dataset_shared_dict[dataset_type]:
            self.dataset_shared_dict[dataset_type][path][1] = value
        
        # update dataset info
        self.update_dataset(dataset_type)
    
    def update_all_prop(self, dataset_type:str, value:float):
        assert dataset_type in ["train", "val", "test"], "Not supported dataset type"
        for path in self.dataset_shared_dict[dataset_type].keys():
            self.dataset_shared_dict[dataset_type][path][1] = value
            self.dataset_layout_dict[dataset_type][path]["sub_layout"].itemAt(2).widget().setText(str(value))
        
        # update dataset info
        self.update_dataset(dataset_type)

    def reset_dataset(self, dataset_type:str):
        assert dataset_type in ["train", "val", "test"], "Not supported dataset type"
        
        # remove dataset
        for path in list(self.dataset_shared_dict[dataset_type].keys()):
            self.remove_dataset(dataset_type, path)
        
        # reset use all button
        # if dataset_type == "train":
        #     self.TrainingUseAllButton.setChecked(False)
        # elif dataset_type == "val":
        #     self.ValidationUseAllButton.setChecked(False)
        # elif dataset_type == "test":
        #     self.TestUseAllButton.setChecked(False)
        # else:
        #     raise Exception("Not supported dataset type")

        # update dataset info
        self.update_dataset(dataset_type)
    
    def reset_all_dataset(self):
        # remove dataset
        [self.reset_dataset(path) for path in ["train", "val", "test"]]

    def update_dataset(self, dataset_type:str):
        # update innter function for train, val, test ui
        def _update_dataset(dataset_type:str):
            if dataset_type == "train":
                total_length = len(self.dataset_shared_dict['train'])
                num_train_use = sum([self.dataset_shared_dict["train"][train_path][0] for train_path in self.dataset_shared_dict["train"].keys()])
                self.TrainingInfoLabel.setText(f"{self.lang.get('training', 'dataset_main', 'TrainingInfoLabelBase')} ({self.lang.get('training', 'dataset_main', 'InfoLabelTotal')}: {total_length}, {self.lang.get('training', 'dataset_main', 'InfoLabelUse')}: {num_train_use})")
                if total_length == 0:
                    self.TrainingUseAllButton.setChecked(False)
                    self.TrainingUseAllButton.setDisabled(True)
                else:
                    self.TrainingUseAllButton.setDisabled(False)
            elif dataset_type == "val":
                total_length = len(self.dataset_shared_dict['val'])
                num_val_use = sum([self.dataset_shared_dict["val"][val_path][0] for val_path in self.dataset_shared_dict["val"].keys()])
                self.ValidationInfoLabel.setText(f"{self.lang.get('training', 'dataset_main', 'ValidationInfoLabelBase')} ({self.lang.get('training', 'dataset_main', 'InfoLabelTotal')}: {total_length}, {self.lang.get('training', 'dataset_main', 'InfoLabelUse')}: {num_val_use})")
                if total_length == 0:
                    self.ValidationUseAllButton.setChecked(False)
                    self.ValidationUseAllButton.setDisabled(True)
                else:
                    self.ValidationUseAllButton.setDisabled(False)
            elif dataset_type == "test":
                total_length = len(self.dataset_shared_dict['test'])
                num_test_use = sum([self.dataset_shared_dict["test"][test_path][0] for test_path in self.dataset_shared_dict["test"].keys()])
                self.TestInfoLabel.setText(f"{self.lang.get('training', 'dataset_main', 'TestInfoLabelBase')} ({self.lang.get('training', 'dataset_main', 'InfoLabelTotal')}: {total_length}, {self.lang.get('training', 'dataset_main', 'InfoLabelUse')}: {num_test_use})")
                if total_length == 0:
                    self.TestUseAllButton.setChecked(False)
                    self.TestUseAllButton.setDisabled(True)
                else:
                    self.TestUseAllButton.setDisabled(False)
        # update UI
        if dataset_type == "all":
            [_update_dataset(_dataset_type) for _dataset_type in ["train", "val", "test"]]
        else:
            _update_dataset(dataset_type)

        if len(self.dataset_shared_dict['train']) + len(self.dataset_shared_dict['val']) + len(self.dataset_shared_dict['test']) == 0:
            self.metadata_shared_dict["wavelength"] = ""

        self.hyperparameter_signal.emit({"metadata": self.metadata_shared_dict})

        self.save_config()

    def get_valid_path(self, dataset_type:str, root_path:str, valid_items:list):
        valid_path_list = []
        invalid_path_dict = {}
        items = valid_items.copy()
        if dataset_type == "test": items.remove("label.npy")
        # get root and sub directory
        if os.path.exists(root_path):        
            if os.path.isdir(root_path):
                for path in [root_path] + [_path.path for _path in os.scandir(root_path) if _path.is_dir()]:
                    not_exist_items = set(items) - set(os.listdir(path))
                    exist_items = set(items) & set(os.listdir(path))
                    if len(not_exist_items) == len(items): # ignore
                        continue
                    elif len(exist_items) == len(items): # exist
                        data = spectral.io.envi.open(os.path.join(path, "data.hdr"), os.path.join(path, "data.raw"))
                        wavelength = data.bands.centers # wavelength
                        if self.metadata_shared_dict["wavelength"]:
                            if self.metadata_shared_dict["wavelength"] == wavelength:
                                valid_path_list.append(path)
                            else:
                                invalid_path_dict[path] = {"type": "wavelength"}
                        else:
                            valid_path_list.append(path)
                            self.metadata_shared_dict["wavelength"] = wavelength
                    else: # not exist
                        invalid_path_dict[path] = {"type": "files", "value": list(not_exist_items)}
        else:
            invalid_path_dict[root_path] = {"type": "path", "value": root_path}

        return valid_path_list, invalid_path_dict

    def init_config(self):
        if len(self._config["datasets"].keys()) == 0:
            self.save_config()
        else:
            self.load_config()

    def save_config(self):
        with open(config_path, "w", encoding="utf-8") as f:
            self.config["datasets"] = copy.deepcopy(self.dataset_shared_dict)
            self.config["datasets"]["last_path"] = self.last_path
            self.config["datasets"]["metadata"] = copy.deepcopy(self.metadata_shared_dict)
            self.config["datasets"]["default_prop"] = copy.deepcopy(self.default_prop)
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def load_config(self, load_from_user:bool=False):
            ignore_message = True
            try:
                if load_from_user:
                    file_dialog = QFileDialog(directory=self.last_path)
                    file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
                    file_dialog.setNameFilters(["json (*.json)"])
                    if file_dialog.exec_():
                        load_path = file_dialog.selectedFiles()[0]
                        with open(load_path, "r", encoding="utf-8") as f:
                            self._config = json.loads(f.read())
                            self.reset_all_dataset()
                            ignore_message = False

                self.last_path = self._config["datasets"].pop("last_path")
                if not os.path.exists(self.last_path):
                    self.last_path = ""

                # load metadata
                metadata = self._config["datasets"].pop("metadata")
                for metadata_key in metadata.keys():
                    self.metadata_shared_dict[metadata_key] = metadata[metadata_key]
                
                # load default prop
                default_prop = self._config["datasets"].pop("default_prop")
                for default_prop_key in default_prop.keys():
                    self.default_prop[default_prop_key] = default_prop[default_prop_key]
                    self.TrainingAllProp.setText(str(self.default_prop["train"]))
                    self.ValidationAllProp.setText(str(self.default_prop["val"]))
                    self.TestAllProp.setText(str(self.default_prop["test"]))

                # add ui
                for dataset_type in self._config["datasets"].keys(): # dataset_type (train, val, test)
                    for path in self._config["datasets"][dataset_type].keys():
                        try:
                            self.add_dataset(dataset_type, self._config["datasets"][dataset_type][path][0], self._config["datasets"][dataset_type][path][1], [path], ignore_message) # load
                        except:
                            pass
            except:
                self.save_config()
    
    def dataset_signal_receiver(self, _dict):
        if "disabled" in _dict:
            self.setDisabled(_dict["disabled"])