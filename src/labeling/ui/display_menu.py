"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from PyQt5 import QtCore, QtWidgets
from labeling.ui.pen_sub_rectangle import penRectangleSubMenu
from constants.constants import DRAWING_SUB_MODE_RECTANGLE_DEFAULT, DRAWING_SUB_MODE_RECTANGLE_SAL

class displayMenu(QtWidgets.QMenu):
    """
        @ Description: Class for the display menu that appears when right-clicking on the display.
        @ Author: GaEun Hwang (2026.05.28)
    """
    def __init__(self, parent=None, sync=None, lang=None):
        super(displayMenu, self).__init__(parent)
        self.init(sync, lang)    
        self.initUI()
        self.setupUI()
        self.setLanguage()
        self.initFunction()
    
    def init(self, sync, lang):
        self.sync = sync
        self.lang = lang
        
        self.displayMenuToDisplaySignal = self.sync.displayMenuToDisplaySignal
        self.displayMenuToPenSignal = self.sync.displayMenuToPenSignal
        
        self.coreToDisplayMenuSignal = self.sync.coreToDisplayMenuSignal
        self.coreToDisplayMenuSignal.connect(self.receiveSignal)
        
        self.displayMenuControlDict = self.sync.displayMenuControlDict
        self.openedPos = None

        self.clickedLabelClass = None
        self.clickedLabelName = None
    
    def initUI(self):
        """
            @ Description: A function to initialize the UI components of the display menu.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.removeLabelAction = QtWidgets.QAction("")
        self.controlLabelOpacityAction = QtWidgets.QAction("")

        self.rectangleModeMenu = penRectangleSubMenu(sync=self.sync, lang=self.lang, parent=self)
        self.rectangleModeMenu.setTitle("")
    
    def setupUI(self):
        """
            @ Description: A function to set up the UI components of the display menu.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.addAction(self.removeLabelAction)
        self.addAction(self.controlLabelOpacityAction)
        self.addMenu(self.rectangleModeMenu)

    def setLanguage(self):
        """
            @ Description: A function to set the language of the display menu.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.lang.set("labeling", "displayMenu", "displayMenuRemoveLabel", self.removeLabelAction)
        self.lang.set("labeling", "displayMenu", "displayMenuControlLabelOpacity", self.controlLabelOpacityAction)
        self.lang.set("labeling", "displayMenu", "displayMenuRectangleMode", self.rectangleModeMenu)
        self.lang.set("labeling", "penSubRectangle", "penRectangleModeDefault", self.rectangleModeMenu.defaultModeAction)
        self.lang.set("labeling", "penSubRectangle", "penRectangleModeSAL", self.rectangleModeMenu.SALModeAction)

    def initFunction(self):
        """
            @ Description: A function to initialize the functions of the display menu.
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.removeLabelAction.triggered.connect(self.removeLabel)
        self.controlLabelOpacityAction.triggered.connect(self.adjustLabelOpacity)
        # self.labelOpacitySlider.valueChanged.connect(self.labelOpacitySpinBox.setValue)
        # self.labelOpacitySpinBox.valueChanged.connect(self.labelOpacitySlider.setValue)
        # self.labelOpacitySpinBox.valueChanged.connect(self.adjustLabelOpacity)

        for action in self.rectangleModeMenu.actions():
            action.triggered.connect(self.changeRectangleMode)

    def removeLabel(self):
        """
            @ Description : A function to send signal to remove the label of the object at the opened position.
            @ Author: GaEun Hwang (2026.05.28)
        """
        emitDict = {'mode': 'removeLabel', 'pos': self.openedPos}
        self.displayMenuToDisplaySignal.emit(emitDict)

    def adjustLabelOpacity(self):
        """
            @ Description : A function to send signal to adjust the opacity of the same class label of the object at the opened position.
            @ Author: GaEun Hwang (2026.05.28)
        """
        emitDict = {'mode': 'adjustLabelOpacity', 'labelClass': self.clickedLabelClass}
        self.displayMenuToPenSignal.emit(emitDict)
    
    def changeRectangleMode(self):
        """
            @ Description : A function to send signal to change the rectangle drawing mode.
            @ Author: GaEun Hwang (2026.05.28)
        """
        checkedRectangleMode = self.rectangleModeMenu.getCheckedMode()
        emitDict = {'mode': 'changeRectangleMode', 'penType': 'pen_rectangle', 'changedMode': checkedRectangleMode}
        self.displayMenuToPenSignal.emit(emitDict)

    def show_(self, globalPos, pos_xy):
        """
            @ Description : A function to show the display menu
            @ Author: GaEun Hwang (2026.05.28)
        """
        self.openedPos = pos_xy
        # move the open position for stable use
        showPos = QtCore.QPoint(int(globalPos.x()) + 5, int(globalPos.y()) + 5)
        selected = self.exec_(showPos)
        self.displayMenuControlDict['opened'] = True if selected is None else False
    
    @QtCore.pyqtSlot(dict)
    def receiveSignal(self, input):
        """
            @ Description : A function to receive signals
            @ Author: GaEun Hwang (2026.05.28)
        """
        from_ = input['from']
        if from_ == 'display':
            self.clickedLabelClass = input['labelClass']
            self.clickedLabelName = input['labelName']

        elif from_ == 'pen':
            penType = input['penType']
            if penType == 'pen_rectangle':
                mode = input['mode']
                if mode == DRAWING_SUB_MODE_RECTANGLE_DEFAULT:
                    self.rectangleModeMenu.defaultModeAction.setChecked(True)
                elif mode == DRAWING_SUB_MODE_RECTANGLE_SAL:
                    self.rectangleModeMenu.SALModeAction.setChecked(True)