"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QFileDialog
import numpy as np

from constants.constants import DATA_DIMENSION, QT_MAX_SIZE, PEN_MODE_ADVANCED_LABELING, MESSAGE_BOX_WARNING, MESSAGE_BOX_INFORMATION
from utils.worker import Threading_Worker
from utils.custom_ui import messageBox
from labeling.module.semi_auto_labeling import semiAutoLabeling

class PenSemiAutoLabelingForm(QtWidgets.QWidget):
    """
        Description: Semi Auto Labeling Class
        Author: Yugyeong Hong (2026.02.04)
    """
    def __init__(self, Pen_Sync, lang, parent):
        super().__init__()
        self.setWindowFlags(Qt.Window | QtCore.Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.init(Sync=Pen_Sync, lang=lang, parent=parent)
        self.initUiLabelMainPenSemiAutoLabeling(self)
        self.setupUiLabelMainPenSemiAutoLabeling()
        self.initFunction()

        if __name__ == "__main__":
            self.show()

    def init(self, Sync=None, lang=None, parent=None):
        """
            Description: Semi Auto Labeling Init Function
            Author: Yugyeong Hong (2026.02.04)
        """
        self.lang = lang
        self.Sync = Sync
        self.parent = parent
        self.worker = Threading_Worker()

        self.coreToSemiAutoLabelingSignal = self.Sync.coreToSemiAutoLabelingSignal
        self.coreToSemiAutoLabelingSignal.connect(self.recieveSignal)
        self.worker.output.connect(self.recvFromThreading)

        self.penControlDict = self.Sync.pen_control_dict
        self.semiAutoLabelingDict = self.Sync.semiAutoLabelingDict
        self.semiAutoLabelingDict['builder'] = semiAutoLabeling()

        # Connect buttons availability method while threading process
        self.worker.started.connect(lambda: self.manageButtons(False))
        self.worker.finished.connect(lambda: self.manageButtons(True))


    def initUiSlider(self, titleKey="", guideKey="", min_=1, max_=100, value=90):
        """
            Description: Initialize a Semi Auto Labeling hyperparameter slider UI and its related widgets
            Author: Yugyeong Hong
            Parameters
                1. titleKey: Key used to retrieve the hyperparameter title from the language dictionary
                2. guideKey: Key used to retrieve the hyperparameter guide from the language dictionary
                3. min_: Minimum value of the slider
                4. max_: Maximum value of the slider
                5. value: Initial value of the slider

        """
        parameterWidget = QtWidgets.QWidget()
        parameterWidget.setObjectName(f"semi_{titleKey}_widget")

        parameterLabel = QtWidgets.QLabel()
        self.lang.set("labeling", "penSubSemiAutoLabeling", titleKey, parameterLabel)

        guideLabel = QtWidgets.QLabel()
        self.lang.set("labeling", "penSubSemiAutoLabeling", guideKey, guideLabel)

        parameterWidgetEdit = QtWidgets.QSpinBox()
        parameterWidgetEdit.setMaximumSize(40, QT_MAX_SIZE)
        parameterWidgetEdit.setRange(1,100)
        parameterWidgetEdit.setValue(value)
        parameterWidgetEdit.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)

        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(min_, max_)
        slider.setSingleStep(1)
        slider.setPageStep(5)
        slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        slider.setTickInterval(5)
        slider.setValue(value)

        sliderTitleHorizon = QtWidgets.QHBoxLayout()
        sliderTitleHorizon.setContentsMargins(0,0,0,0)
        sliderTitleHorizon.setSpacing(8)
        sliderTitleHorizon.addWidget(parameterLabel)
        sliderTitleHorizon.addWidget(parameterWidgetEdit)

        sliderVertical = QtWidgets.QVBoxLayout(parameterWidget)
        sliderVertical.setContentsMargins(0,0,0,0)
        sliderVertical.setSpacing(2)
        sliderVertical.addLayout(sliderTitleHorizon)
        sliderVertical.setSpacing(2)
        sliderVertical.addWidget(guideLabel)
        sliderVertical.setSpacing(4)
        sliderVertical.addWidget(slider)

        # Synchronization of slider and line edit
        slider.valueChanged.connect(lambda val, e=parameterWidgetEdit: (
            QtCore.QSignalBlocker(e), e.setValue(val)
        ))

        def editToSlider(s=slider, e=parameterWidgetEdit):
            txt = e.text().strip()
            if txt == "":
                return
            s.setValue(int(txt))

        parameterWidgetEdit.editingFinished.connect(editToSlider)

        return parameterWidget, slider, parameterWidgetEdit


    def initUiLabelMainPenSemiAutoLabeling(self, Form):
        """
            Description:Semi Auto Labeling Init UI
            Author: Yugyeong Hong (2026.02.04)
        """
        Form.setObjectName("PenSemiAutoLabelingForm")
        Form.resize(200, 200)

        self.penMainGrid = QtWidgets.QVBoxLayout(Form)
        self.penMainGrid.setObjectName("penMainGrid")

        # ================================= Build Endmember =============================
        self.penEndmmberTitleWidget = QtWidgets.QWidget()
        self.penEndmmberTitleWidget.setObjectName("penEndmemberTitleWidget")
        self.penEndmmberTitleWidget.setFixedHeight(24)

        self.penEndmemberTitleHorizon = QtWidgets.QHBoxLayout(self.penEndmmberTitleWidget)
        self.penEndmemberTitleHorizon.setContentsMargins(4, 2, 4, 2)
        self.penEndmemberTitleHorizon.setObjectName("penEndmemberTitleHorizon")
        self.penEndmemberTitleLabel = QtWidgets.QLabel()
        self.penEndmemberTitleLabel.setObjectName("penEndmemberTitleLabel")
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penEndmemberTitleLabel", self.penEndmemberTitleLabel)

        # Load Directory
        self.penEndmemberImageHorizon = QtWidgets.QHBoxLayout()
        self.penEndmemberImageHorizon.setObjectName("penEndmemberImageHorizon")

        self.normalDirectoryLoadBtn = QtWidgets.QPushButton()
        imageAddIcon = QtGui.QIcon()
        imageAddIcon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_add.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.normalDirectoryLoadBtn.setIcon(imageAddIcon)
        self.normalDirectoryLoadBtn.setObjectName("normalDirectoryLoadBtn")
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penNormalDirectoryLoadBtn", self.normalDirectoryLoadBtn)

        self.fileAddBtn = QtWidgets.QPushButton()
        fileAddIcon = QtGui.QIcon()
        fileAddIcon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_load.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.fileAddBtn.setIcon(fileAddIcon)
        self.fileAddBtn.setObjectName("fileAddBtn")
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penEndmemberFileLoadBtn", self.fileAddBtn)


        self.penEndmemberImageLineEdit = QtWidgets.QLineEdit()
        self.penEndmemberImageLineEdit.setObjectName("penEndmemberImageLineEdit")
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penEndmemberImageLoad", self.penEndmemberImageLineEdit)
        self.penEndmemberImageLineEdit.setReadOnly(True)

        self.penEndmemberImageHorizon.addWidget(self.penEndmemberImageLineEdit)
        self.penEndmemberImageHorizon.addWidget(self.normalDirectoryLoadBtn)
        self.penEndmemberImageHorizon.addWidget(self.fileAddBtn)

        #Endmember parameters
        self.penEndmemberParameterHLayout = QtWidgets.QHBoxLayout()
        self.penEndmemberParameterHLayout.setObjectName("penEndmemberParameterHLayout")

        self.penEndmemberParameterVLayout = QtWidgets.QVBoxLayout()
        self.penEndmemberParameterVLayout.setObjectName("penEndmemberParameterVLayout")

        # Dimension parameter
        self.penEndmemberParamDLabel = QtWidgets.QLabel()
        self.penEndmemberParamDLabel.setObjectName("penEndmemberParamDLabel")
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penEndmemberParamDLabel", self.penEndmemberParamDLabel)
        self.penEndmemberParamDSpinBox = QtWidgets.QSpinBox()
        self.penEndmemberParamDSpinBox.setMaximumSize(QtCore.QSize(40, QT_MAX_SIZE))
        self.penEndmemberParamDSpinBox.setRange(1,224)
        self.penEndmemberParamDSpinBox.setValue(4)
        self.penEndmemberParamDSpinBox.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)
        self.penEndmemberParamDSpinBox.setObjectName("penEndmemberParamDSpinBox")

        # Cluster K parameter
        self.penEndmemberParamKLabel = QtWidgets.QLabel()
        self.penEndmemberParamKLabel.setObjectName("penEndmemberParamKLabel")
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penEndmemberParamKLabel", self.penEndmemberParamKLabel)
        self.penEndmemberParamKSpinBox = QtWidgets.QSpinBox()
        self.penEndmemberParamKSpinBox.setMaximumSize(QtCore.QSize(40, QT_MAX_SIZE))
        self.penEndmemberParamKSpinBox.setRange(1, 999)
        self.penEndmemberParamKSpinBox.setValue(8)
        self.penEndmemberParamKSpinBox.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)
        self.penEndmemberParamKSpinBox.setObjectName("penEndmemberParamKSpinBox")

        self.penEndmemberBuildingLabel = QtWidgets.QLabel()
        self.penEndmemberBuildingLabel.setObjectName("penEndmemberBuildingLabel")
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penEndmemberDisabledLabel", self.penEndmemberBuildingLabel)

        # Build button
        self.penEndmemberBuildBtn = QtWidgets.QPushButton()
        self.penEndmemberBuildBtn.setObjectName("penEndmemberBuildBtn")
        self.penEndmemberBuildBtn.setMinimumHeight(30)
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penEndmemberBuildBtn", self.penEndmemberBuildBtn)


        # ================================= Labeling Parameters  =============================
        self.penSemiAutoLabelingTitleWidget = QtWidgets.QWidget()
        self.penSemiAutoLabelingTitleWidget.setObjectName("penSemiAutoLabelingTitleWidget")
        self.penSemiAutoLabelingTitleWidget.setFixedHeight(24)

        self.penSemiAutoLabelingTitleHorizon = QtWidgets.QHBoxLayout(self.penSemiAutoLabelingTitleWidget)
        self.penSemiAutoLabelingTitleHorizon.setContentsMargins(4, 2, 4, 2)
        self.penSemiAutoLabelingTitleHorizon.setObjectName("penSemiAutoLabelingTitleHorizon")

        self.penSemiAutoLabelingTitleLabel = QtWidgets.QLabel()
        self.penSemiAutoLabelingTitleLabel.setObjectName("penSemiAutoLabelingTitleLabel")
        self.lang.set("labeling","penSubSemiAutoLabeling", "penSemiAutoLabelingTitleLabel", self.penSemiAutoLabelingTitleLabel )

        self.penSemiAutoLabelingVertical = QtWidgets.QVBoxLayout()
        self.penSemiAutoLabelingVertical.setObjectName("penSemiAutoLabelingVertical")

        self.pWidget, self.pSlider, self.pEdit = self.initUiSlider(titleKey="penSemiAutoLabelingStrictness", guideKey="penSemiAutoLabelingStrictnessGuide")
        self.qWidget, self.qSlider, self.qEdit = self.initUiSlider(titleKey="penSemiAutoLabelingTolerance", guideKey="penSemiAutoLabelingToleranceGuide")

        # Apply button
        self.penSemiAutoApplyBtn = QtWidgets.QPushButton()
        self.penSemiAutoApplyBtn.setObjectName("penSemiAutoApplyBtn")
        self.penSemiAutoApplyBtn.setMinimumHeight(30)
        self.lang.set("labeling", "penSubSemiAutoLabeling", "penSemiAutoApplyBtn", self.penSemiAutoApplyBtn)


    def setupUiLabelMainPenSemiAutoLabeling(self):
        """
            Description: Semi Auto Labeling UI setup Function
            Author: Yugyeong Hong (2026.02.04)
        """

        self.penEndmemberParameterHLayout.addWidget(self.penEndmemberParamDLabel)
        self.penEndmemberParameterHLayout.addWidget(self.penEndmemberParamDSpinBox)
        self.penEndmemberParameterHLayout.addStretch(1)
        self.penEndmemberParameterHLayout.addWidget(self.penEndmemberParamKLabel)
        self.penEndmemberParameterHLayout.addWidget(self.penEndmemberParamKSpinBox)

        self.penEndmemberTitleHorizon.addWidget(self.penEndmemberTitleLabel)
        self.penSemiAutoLabelingTitleHorizon.addWidget(self.penSemiAutoLabelingTitleLabel)
        self.penSemiAutoLabelingVertical.addWidget(self.pWidget)
        self.penSemiAutoLabelingVertical.addWidget(self.qWidget)

        self.penMainGrid.setContentsMargins(6,6,6,6)
        self.penMainGrid.setSpacing(6)
        self.penMainGrid.addWidget(self.penEndmmberTitleWidget)
        self.penMainGrid.addLayout(self.penEndmemberImageHorizon)
        self.penMainGrid.addLayout(self.penEndmemberParameterHLayout)
        self.penMainGrid.addWidget(self.penEndmemberBuildingLabel)
        self.penMainGrid.addWidget(self.penEndmemberBuildBtn)
        self.penMainGrid.addSpacing(10)
        self.penMainGrid.addWidget(self.penSemiAutoLabelingTitleWidget)
        self.penMainGrid.addLayout(self.penSemiAutoLabelingVertical)
        self.penMainGrid.addWidget(self.penSemiAutoApplyBtn)

    def initFunction(self):
        """
            Description: Initialize Semi Auto Labeling UI signal connections
            Author: Yugyeong Hong (2026.02.04)
        """

        self.normalDirectoryLoadBtn.clicked.connect(self.loadNormalDirectory)
        self.fileAddBtn.clicked.connect(self.loadEndmember)
        self.penEndmemberBuildBtn.clicked.connect(self.buildEndmember)
        self.penSemiAutoApplyBtn.clicked.connect(self.onApplyClicked)
        self.pSlider.sliderReleased.connect(lambda: self.penControlDict.update(penSemiStrictness=self.pSlider.value()))
        self.qSlider.sliderReleased.connect(lambda: self.penControlDict.update(penSemiTolerance=self.qSlider.value()))

    def onApplyClicked(self):
        """
            description : Apply Semi Auto Labeling with current parameters and loaded endmember
            author : Hyunsu Kim (2026.05.19)
            hisotry:
                1. Hyunsu Kim(2026.06.04): Modified to show menu checkbox status and activate main window after closing the form when apply button is clicked, for better user experience
        """
        if 'kEndmember' not in self.semiAutoLabelingDict:
            messageBox(mode=MESSAGE_BOX_WARNING,
                       title=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberTitleLabel"),
                       text=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberDisabledLabel"),
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
            return
        # Build aMap if not yet built for current image data
        if self.semiAutoLabelingDict.get('aMap') is None:
            if 'data' in self.semiAutoLabelingDict:
                self.buildAmap()
            if self.semiAutoLabelingDict.get('aMap') is None:
                return
        self.parent.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = True
        self.parent.pen_obj_dict['penAdvancedLabeling']['pixelBased'] = False
        self.parent.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(True)
        self.parent.pen_obj_dict['penAdvancedLabeling']['opened'] = False
        self.parent.pen_obj_dict['penAdvancedLabeling']['onMode'] = 'semiAuto'
        if self.parent.actionPixelBased.isChecked():
            self.parent.actionPixelBased.setChecked(False)
        self.parent.actionSemiAuto.setChecked(True)
        self.parent.pen_mode(ch=True, mode=PEN_MODE_ADVANCED_LABELING)
        self.close()
        QtCore.QTimer.singleShot(0, self.parent.activateWindow)

    def closeEvent(self, event):
        if self.parent.pen_obj_dict['penAdvancedLabeling']['pixelBased']:
            self.parent.pen_obj_dict['penAdvancedLabeling']['opened'] = False
        elif not (self.parent.pen_obj_dict['penAdvancedLabeling']['semiAuto'] or self.parent.pen_obj_dict['penAdvancedLabeling']['pixelBased']):
            onMode = self.parent.pen_obj_dict['penAdvancedLabeling']['onMode']
            self.parent.pen_obj_dict['penAdvancedLabeling']['opened'] = False
            self.parent.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = False
            if onMode == 'pixelBased':
                self.parent.pen_obj_dict['penAdvancedLabeling']['pixelBased'] = True
                self.parent.actionPixelBased.setChecked(True)
            elif onMode == 'semiAuto':
                self.parent.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = True
                self.parent.actionSemiAuto.setChecked(True)
            else:
                self.parent.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(False)
        self.close()

    def manageButtons(self, enable):
        """
            Description: Control button availability
            Author: Yugyeong Hong(2026.02.26)
            History:
                1. Hyunsu Kim (2026.05.19) : Add enabling/disabling of apply button in Semi Auto Labeling mode
        """
        self.parent.pen_obj_dict['penAdvancedLabeling']['obj'].setEnabled(enable)
        self.normalDirectoryLoadBtn.setEnabled(enable)
        self.fileAddBtn.setEnabled(enable)
        self.penEndmemberBuildBtn.setEnabled(enable)
        self.penSemiAutoApplyBtn.setEnabled(enable)

    def loadNormalDirectory(self):
        """
            Description: Open dialog to load normal data
            Author: Yugyeong Hong
        """
        title = self.lang.get("labeling", "penSubSemiAutoLabeling", "penNormalDirectoryLoadBtn")
        dirPath = QFileDialog.getExistingDirectory(parent=self, caption=title[1], directory="")
        if dirPath:
            self.penEndmemberImageLineEdit.setText(dirPath)
            self.semiAutoLabelingDict['dirPath'] = dirPath

    def loadEndmember(self):
        """
            Description: Enable or disable UI buttons
            Author: Yugyeong Hong (2026.02.04)
            History:
                - Hyunsu Kim (2026.03.23) : Modify logic and message when an invalid endmember file is loaded
                - Hyunsu Kim (2026.04.24) : Change endmember file load button name to "penEndmemberFileLoadBtn" for translation in language file
        """
        title = self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberFileLoadBtn")
        self.filePath, _ = QFileDialog.getOpenFileName(parent=self, caption=title[1], directory="", filter="NumPy file (*.npy)")
        if self.filePath:
            try:
                npyFile = np.load(self.filePath, allow_pickle=False).astype(np.float32)

                if npyFile.ndim != 2 or npyFile.shape[1] != DATA_DIMENSION:
                    messageBox(mode=MESSAGE_BOX_WARNING, 
                               title=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberTitleLabel"),
                               text=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberDimensionWarning"),
                               buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
                else:
                    self.penEndmemberImageLineEdit.setText(self.filePath)
                    self.semiAutoLabelingDict['kEndmember'] = npyFile
                    messageBox(mode=MESSAGE_BOX_INFORMATION, 
                               title=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberTitleLabel"),
                               text=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberSavedInMemory"),
                               buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
                    self.penEndmemberBuildingLabel.setText(self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberAvailableLabel"))
                    self.semiAutoLabelingDict['dirPath'] = self.filePath
                    self.buildAmap()
            except Exception as e:
                messageBox(mode=MESSAGE_BOX_WARNING,
                           title=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberTitleLabel"),
                           text=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberFileErrorMsg") + str(e),
                           buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})


    def buildEndmember(self):
        """
             Description: Build Endmember from the loaded normal data
             Author: Yugyeong Hong (2026.02.04)
        """

        self.clusterK = int(self.penEndmemberParamKSpinBox.text())
        self.pcaDim = int(self.penEndmemberParamDSpinBox.text())

        if 'dirPath' in self.semiAutoLabelingDict:
            normalDirPath = Path(self.semiAutoLabelingDict['dirPath'])
            checkDir = ["data.raw", "data.hdr", "label.npy"]
            missing_files = [checkFile for checkFile in checkDir if not (normalDirPath / checkFile).exists()]

            if not missing_files:
                self.penEndmemberBuildingLabel.setText(self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberBuilding"))

                self.worker.staging(self.endmemberWorker)
                self.worker.start()
            else:
                messageBox(mode=MESSAGE_BOX_WARNING,
                           title=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberTitleLabel"),
                           text=f'{self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberNormalDataRequiredError")} {missing_files}',
                           buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
        else:
            messageBox(mode=MESSAGE_BOX_WARNING,
                       title=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberTitleLabel"),
                       text=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberNormalDataLoadErrorMsg"),
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})

    def endmemberWorker(self) -> None:
            """
                Description: Wrapper method to use Threading Worker
                Author: Yugyeong Hong (2026.02.26)
            """
            result = self.semiAutoLabelingDict['builder'].buildEndmember(dirPath=self.semiAutoLabelingDict['dirPath'], clusterK=self.clusterK, pcaDim=self.pcaDim)
            self.worker.output_dict.update(result)
            self.semiAutoLabelingDict["kEndmember"] = result['kEndmember']
    
    def buildAmap(self):
        """
            Description: Build Amap using the endmember stored in memory
            Author: Yugyeong Hong (2026.02.04)
        """
        self.semiAutoLabelingDict["aMap"] = self.semiAutoLabelingDict['builder'].aMap(self.semiAutoLabelingDict['kEndmember'], self.semiAutoLabelingDict['data'])
        if self.semiAutoLabelingDict["aMap"] is None:
            # Deactivate semi auto labeling pen
            self.parent.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(False)
            messageBox(mode=MESSAGE_BOX_WARNING,
                       title=self.lang.get("labeling", "penSubSemiAutoLabeling", "penSemiAutoLabelingWarning"),
                       text=self.lang.get("labeling", "penSubSemiAutoLabeling", "penAmapBuildingError"),
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
    

    @pyqtSlot(dict)
    def recvFromThreading(self, output):
        if output.get("status") == "success":
            messageBox(mode=MESSAGE_BOX_INFORMATION,
                       title=self.lang.get("labeling","penSubSemiAutoLabeling","penEndmemberSaveTitleLabel"),
                       text=f"{self.lang.get('labeling','penSubSemiAutoLabeling','penEndmemberSavePath')} {self.semiAutoLabelingDict['dirPath']}",
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
            self.buildAmap()
        else:
            err = output.get("status")
            messageBox(mode=0,
                       title=self.lang.get("labeling","penSubSemiAutoLabeling","penEndmemberTitleLabel"),
                       text=f'{self.lang.get("labeling","penSubSemiAutoLabeling","penEndmemberBuildErrorMsg")} {err}',
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})

        key = "penEndmemberAvailableLabel" if 'kEndmember' in self.semiAutoLabelingDict else "penEndmemberDisabledLabel"
        txt = self.lang.get("labeling", "penSubSemiAutoLabeling", key)
        self.penEndmemberBuildingLabel.setText(txt)


    @pyqtSlot(dict)
    def recieveSignal(self, receivedDict):
        """
            Description: Recieved Signals
            Author: Yugyeong Hong (2026.02.04)
        """
        from_ = receivedDict['from']
        if from_ == 'pen':
            if 'kEndmember' in self.semiAutoLabelingDict:
                if self.semiAutoLabelingDict['aMap'] is None:
                    self.buildAmap()
            else:
                messageBox(mode=MESSAGE_BOX_INFORMATION,
                           title=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberTitleLabel"),
                           text=self.lang.get("labeling", "penSubSemiAutoLabeling", "penEndmemberDisabledLabel"),
                           buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
                # Deactivate semi auto labeling pen; form stays open for endmember build
                self.parent.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(False)
                self.parent.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = False

        elif from_ == 'image':
            self.semiAutoLabelingDict['data'] = receivedDict['data']
            self.semiAutoLabelingDict['aMap'] = None

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui=PenSemiAutoLabelingForm()
    sys.exit(app.exec_())
