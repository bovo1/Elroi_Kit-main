"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from PyQt5 import QtCore, QtWidgets
from constants.constants import DRAWING_SUB_MODE_RECTANGLE_DEFAULT, DRAWING_SUB_MODE_RECTANGLE_SAL

class penRectangleSubMenu(QtWidgets.QMenu):
    """
        @ Description: Class for the rectangle sub menu
        @ Author: GaEun Hwang (2026.05.28)
    """
    def __init__(self, sync=None, lang=None, parent=None):
        super().__init__(parent)
        self.init(sync, lang)
        self.initUI()
        self.setupUI()
        self.setLanguage()

    def init(self, sync, lang):
        self.sync = sync
        self.lang = lang
    
    def initUI(self):
        """
            @ Description: A function to initialize the UI components of the rectangle sub menu.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.defaultModeAction = QtWidgets.QAction("")
        self.defaultModeAction.setData(DRAWING_SUB_MODE_RECTANGLE_DEFAULT)
        self.SALModeAction = QtWidgets.QAction("")
        self.SALModeAction.setData(DRAWING_SUB_MODE_RECTANGLE_SAL)
        
        self.actionGroup = QtWidgets.QActionGroup(self)
    
    def initFunction(self):
        self.defaultModeAction.triggered.connect(lambda mode: self.modeChanged(mode=self.defaultModeAction.data()))
        self.SALModeAction.triggered.connect(lambda mode: self.modeChanged(mode=self.SALModeAction.data()))
    
    def setupUI(self):
        """
            @ Description: A function to set up the UI components of the rectangle sub menu.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.addAction(self.defaultModeAction)
        self.addAction(self.SALModeAction)
        
        self.actionGroup.addAction(self.defaultModeAction)
        self.actionGroup.addAction(self.SALModeAction)
        
        for action in self.actionGroup.actions():
            action.setCheckable(True)
        self.actionGroup.setExclusive(True)

    def setLanguage(self):
        """
            @ Description: A function to set the language of the rectangle sub menu.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.lang.set("labeling", "penSubRectangle", "penRectangleModeDefault", self.defaultModeAction)
        self.lang.set("labeling", "penSubRectangle", "penRectangleModeSAL", self.SALModeAction)
    
    def getCheckedMode(self):
        """
            @ Description: A function to get the currently checked mode in the rectangle sub menu.
            @ Author: GaEun Hwang (2026.05.28)
        """
        return self.actionGroup.checkedAction()

class penRectangleSALForm(QtWidgets.QWidget):
    """
        @ Description: Class for the rectangle SAL settings form
        @ Author: GaEun Hwang (2026.05.28)
    """
    def __init__(self, sync, lang):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.init(Sync=sync, lang=lang)
        self.initUi()
        self.setupUi()
        self.setLanguage()
        self.initFunction()
    
    def init(self, Sync, lang):
        self.sync = Sync
        self.lang = lang

        self.penObjDict = self.sync.pen_obj_dict
        self.initializeSettings = {}

    def initUi(self):
        """
            @ Description: A function to initialize the UI components of the rectangle SAL settings form.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.gridLayout = QtWidgets.QGridLayout()
        self.mainTitleWidget = QtWidgets.QWidget()
        self.mainTitleWidget.setObjectName("mainTitleWidget")

        self.mainTitleHorizontalLayout = QtWidgets.QHBoxLayout(self.mainTitleWidget)
        self.mainTitleHorizontalLayout.setObjectName("mainTitleHorizontalLayout")

        self.mainTitleLabel = QtWidgets.QLabel("")
        self.mainTitleLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mainTitleLabel.setObjectName("mainTitleLabel")
        self.mainTitleHorizontalLayout.addWidget(self.mainTitleLabel)

        self.standardNormalSpectrumLabel = QtWidgets.QLabel("")
        self.standardNormalSpectrumLabel.setObjectName("standardNormalSpectrumLabel")
        self.standardNormalSpectrumComboBox = QtWidgets.QComboBox()
        self.standardNormalSpectrumComboBox.setObjectName("standardNormalSpectrumComboBox")
        self.standardNormalSpectrumComboBox.addItems(["Negative", "Positive"])
        self.standardNormalSpectrumComboBox.setCurrentIndex(0)
        
        self.kernelTypeLabel = QtWidgets.QLabel("")
        self.kernelTypeLabel.setObjectName("kernelTypeLabel")
        self.kernelTypeComboBox = QtWidgets.QComboBox()
        self.kernelTypeComboBox.setObjectName("kernelTypeComboBox")
        self.kernelTypeComboBox.addItems(["Not Use", "Expand", "Reduce"])
        self.kernelTypeComboBox.setCurrentIndex(0)

        self.kernelSizeLabel = QtWidgets.QLabel("")
        self.kernelSizeLabel.setObjectName("kernelSizeLabel")
        self.kernelSizeSpinBox = QtWidgets.QSpinBox()
        self.kernelSizeSpinBox.setObjectName("kernelSizeSpinBox")
        self.kernelSizeSpinBox.setRange(3, 11)
        self.kernelSizeSpinBox.setSingleStep(2)
        self.kernelSizeSpinBox.setEnabled(False)

        self.applyButton = QtWidgets.QPushButton("")
        self.applyButton.setObjectName("applyButton")

        # store the initial settings to restore them later
        self.initializeSettings = self.getSALSettings()

    def setupUi(self):
        """
            @ Description: A function to set up the UI components of the rectangle SAL settings form.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.setLayout(self.gridLayout)
        self.gridLayout.setContentsMargins(10, 5, 10, 10)
        self.gridLayout.addWidget(self.mainTitleWidget, 0, 0, 1, 2)
        self.gridLayout.addWidget(self.standardNormalSpectrumLabel, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.standardNormalSpectrumComboBox, 1, 1, 1, 1)
        self.gridLayout.addWidget(self.kernelTypeLabel, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.kernelTypeComboBox, 2, 1, 1, 1)
        self.gridLayout.addWidget(self.kernelSizeLabel, 3, 0, 1, 1)
        self.gridLayout.addWidget(self.kernelSizeSpinBox, 3, 1, 1, 1)
        self.gridLayout.addWidget(self.applyButton, 4, 0, 1, 2)

    def setLanguage(self):
        """
            @ Description: A function to set the language of the rectangle SAL settings form.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.lang.set("labeling", "penSubRectangle", "penRectangleTitle", self.mainTitleLabel)
        self.lang.set("labeling", "penSubRectangle", "standardNormalSpectrumLabel", self.standardNormalSpectrumLabel)
        self.lang.set("labeling", "penSubRectangle", "standardNormalSpectrumComboBox", self.standardNormalSpectrumComboBox)
        self.lang.set("labeling", "penSubRectangle", "kernelTypeLabel", self.kernelTypeLabel)
        self.lang.set("labeling", "penSubRectangle", "kernelTypeComboBox", self.kernelTypeComboBox)
        self.lang.set("labeling", "penSubRectangle", "kernelSizeLabel", self.kernelSizeLabel)
        self.lang.set("labeling", "penSubRectangle", "applyButton", self.applyButton)

    def initFunction(self):
        """
            @ Description: A function to initialize the functions of the rectangle SAL settings form.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.kernelSizeSpinBox.valueChanged.connect(self.kernelSizeChanged)
        self.kernelTypeComboBox.currentIndexChanged.connect(self.kernelTypeChanged)
        self.applyButton.clicked.connect(self.applySALSettings)

    def kernelSizeChanged(self):
        """
            @ Description: A function to handle the event when the kernel size is changed.
            @ Author: GaEun Hwang (2026.05.29)
        """
        self.kernelSizeSpinBox.blockSignals(True)
        if self.kernelSizeSpinBox.value() % 2 == 0:
            self.kernelSizeSpinBox.setValue(max(self.kernelSizeSpinBox.value() - 1, self.kernelSizeSpinBox.minimum()))
        self.kernelSizeSpinBox.blockSignals(False)

    def kernelTypeChanged(self):
        """
            @ Description: A function to handle the event when the kernel type is changed.
            @ Author: GaEun Hwang (2026.05.28)
        """
        if self.kernelTypeComboBox.currentIndex() == 0: # Not Use
            self.kernelSizeSpinBox.setEnabled(False)
        else:
            self.kernelSizeSpinBox.setEnabled(True)

    def applySALSettings(self):
        """
            @ Description: A function to apply the SAL settings when the apply button is clicked.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.penObjDict['pen_rectangle']['settings'] = self.getSALSettings()
        self.close()
        self.penObjDict['pen_rectangle']['opened'] = False
        if not self.penObjDict['pen_rectangle']['obj'].isChecked():
            self.penObjDict['pen_rectangle']['obj'].click()

    def getSALSettings(self):
        """
            @ Description: A function to get the current SAL settings from the form.
            @ Author: GaEun Hwang (2026.05.28)
        """
        return {
            "standardNormalSpectrum": self.standardNormalSpectrumComboBox.currentIndex(),
            "kernelType": self.kernelTypeComboBox.currentIndex(),
            "kernelSize": self.kernelSizeSpinBox.value()
        }

    def close(self):
        """
            @ Description: A function to handle the event when the rectangle SAL settings form is closed.
            @ Author: GaEun Hwang (2026.05.29)
        """
        super().close()
        # restore previous settings if changes were not applied
        if self.penObjDict['pen_rectangle']['settings'] is not None:
            if self.penObjDict['pen_rectangle']['settings'] != self.getSALSettings():
                self.standardNormalSpectrumComboBox.setCurrentIndex(self.penObjDict['pen_rectangle']['settings']['standardNormalSpectrum'])
                self.kernelTypeComboBox.setCurrentIndex(self.penObjDict['pen_rectangle']['settings']['kernelType'])
                self.kernelSizeSpinBox.setValue(self.penObjDict['pen_rectangle']['settings']['kernelSize'])
        else:
            # if there were no previous settings, just reset to default
            self.standardNormalSpectrumComboBox.setCurrentIndex(self.initializeSettings['standardNormalSpectrum'])
            self.kernelTypeComboBox.setCurrentIndex(self.initializeSettings['kernelType'])
            self.kernelSizeSpinBox.setValue(self.initializeSettings['kernelSize'])