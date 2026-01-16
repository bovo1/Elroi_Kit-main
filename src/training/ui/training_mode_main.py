from PyQt5 import QtCore, QtWidgets

from .dataset_main import Dataset_Form
from .hyperparameter_main import Hyperparameter_Form
from .run_main import Run_Form
from .result_main import Result_Form

from training.stylesheet.stylesheet_training_mode_main import stylesheet

class Train_Main(QtWidgets.QMainWindow):
    def __init__(self, Sync, lang) -> None:
        super().__init__()
        self.lang = lang
        self.init(Sync=Sync)
        self.init_ui(self)
        self.setup_ui(self)

    def init(self, Sync=None):
        self.Sync = Sync
        # Sync.training_main_signal.connect(self.training_main_signal_receiver)

    def init_ui(self, MainWindow):
        MainWindow.setObjectName("Train_MainWindow")
        MainWindow.setWindowTitle("Train Main Window")
        MainWindow.setStyleSheet(stylesheet)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        self.TrainMain = QtWidgets.QTabWidget(self.centralwidget)
        self.TrainMain.setObjectName("TrainMain")

        self.DatasetsTab = Dataset_Form(self.Sync, self.lang)
        self.DatasetsTab.setObjectName("DatasetsTab")

        self.HyperparametersTab = Hyperparameter_Form(self.Sync, self.lang)
        self.HyperparametersTab.setObjectName("HyperparametersTab")

        self.RunTab = Run_Form(self.Sync, self.lang)
        self.RunTab.setObjectName("RunTab")

        self.ResultTab = Result_Form(self.Sync, self.lang)
        self.ResultTab.setObjectName("ResultTab")

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def setup_ui(self, MainWindow):
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.gridLayout.addWidget(self.TrainMain, 0, 1, 1, 1)
        self.gridLayout.setContentsMargins(0, 6, 0, 6)

        self.TrainMain.addTab(self.DatasetsTab, "")
        self.TrainMain.addTab(self.HyperparametersTab, "")
        self.TrainMain.addTab(self.RunTab, "")
        self.TrainMain.addTab(self.ResultTab, "")
        self.TrainMain.setCurrentIndex(0)
        self.lang.set("training", "training_mode_main", "DatasetsTab", self.TrainMain)
        self.lang.set("training", "training_mode_main", "HyperparametersTab", self.TrainMain)
        self.lang.set("training", "training_mode_main", "RunTab", self.TrainMain)
        self.lang.set("training", "training_mode_main", "ResultTab", self.TrainMain)