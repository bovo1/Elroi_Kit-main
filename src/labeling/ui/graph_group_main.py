"""
    ELROILAB Kit

    Copyright 2025. Elroilab All rights reserved.
"""

import random

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtCore import pyqtSlot
from constants.constants import *

from utils.custom_ui import custom_qtablewidget, custom_qheaderview, messageBox

gen_color = lambda : [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]
iconSize = 30

from labeling.stylesheet.stylesheet_label_main import stylesheet

class graphGroupForm(QtWidgets.QWidget):
    """
        Description: Graph Group UI Class
        Autror: GaEun Hwang (2025.12.05)
    """
    def __init__(self, Sync, lang):
        super().__init__()    
        self.init(Sync, lang)
        self.initVariables()
        self.initUiGraphList(self)
        self.initFunction()
        self.setupUiGraphList()
    
    def init(self, Sync, lang):
        """
            Description: Graph Group UI Init Function
            Author: GaEun Hwang (2025.12.05)
        """
        self.Sync = Sync
        self.lang = lang

        self.coreToGraphGroupSignal = self.Sync.coreToGraphGroupSignal
        self.coreToGraphGroupSignal.connect(self.recieveSignal)
        self.labelToGraphGroup = self.Sync.labelToGraphGroupSignal
        self.graphGroupToGraph = self.Sync.graphGroupToGraphSignal
        self.graphGroupToDisplay = self.Sync.graphGroupToDisplaySignal

        self.displayControlDict = self.Sync.display_control_dict
        self.graphObjDict = self.Sync.graph_obj_dict
        self.graphGroupDict = self.Sync.graphGroupDict
        self.labelViewGraphGroupDict = self.Sync.labelViewGraphGroupDict
        self.graphControlDict = self.Sync.graph_control_dict
        self.labelObjDict = self.Sync.label_obj_dict
        self.labelControlDict = self.Sync.label_control_dict
    
    def initVariables(self):
        """
            Description: Graph Group Variables Init Function
            Author: GaEun Hwang (2025.12.05)
        """
        self.headerShowState = True
        self.labelHeaderShowState = True
        self.graphIndex = 0
        # using button Group is more easier to manage button
        self.buttonGroup = QtWidgets.QButtonGroup()
        # make exclusive True to allow only one button to be selected
        self.buttonGroup.setExclusive(True)

    def initUiGraphList(self, form):
        """
            Description: Graph Group UI Init Function
            Author: GaEun Hwang (2025.12.05)
        """
        form.setStyleSheet(stylesheet)

        self.gridLayout = QtWidgets.QGridLayout(form)
        self.gridLayout.setObjectName("gridLayout")

        self.topHorizonLayout = QtWidgets.QHBoxLayout()
        self.topHorizonLayout.setObjectName("topHorizonLayout")

        self.tableStackWidget = QtWidgets.QStackedWidget()
        self.tableStackWidget.setObjectName("tableStackWidget")

        self.graphGroupAddBtn = QtWidgets.QPushButton()
        icongraphGroupAddBtn = QtGui.QIcon()
        icongraphGroupAddBtn.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_group_add_white.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        icongraphGroupAddBtn.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_group_add_gray.png"), QtGui.QIcon.Mode.Disabled, QtGui.QIcon.State.Off)
        self.graphGroupAddBtn.setIcon(icongraphGroupAddBtn)
        self.graphGroupAddBtn.setObjectName("graphGroupAddBtn")
        self.lang.set("labeling", "graphGroupMain", "graphGroupAdd", self.graphGroupAddBtn)

        self.graphGroupClearBtn = QtWidgets.QPushButton()
        icongraphGroupClearBtn = QtGui.QIcon()
        icongraphGroupClearBtn.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_group_clear_white.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        icongraphGroupClearBtn.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_group_clear_gray.png"), QtGui.QIcon.Mode.Disabled, QtGui.QIcon.State.Off)
        self.graphGroupClearBtn.setIcon(icongraphGroupClearBtn)
        self.graphGroupClearBtn.setObjectName("graphGroupClearBtn")
        self.lang.set("labeling", "graphGroupMain", "graphGroupClear", self.graphGroupClearBtn)

        self.labelViewGraphBtn = QtWidgets.QPushButton()
        iconlabelViewGraphBtn = QtGui.QIcon()
        iconlabelViewGraphBtn.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_labelView_white.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        iconlabelViewGraphBtn.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_labelView_yellow.png"), QtGui.QIcon.Mode.Active, QtGui.QIcon.State.On)
        iconlabelViewGraphBtn.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_labelView_gray.png"), QtGui.QIcon.Mode.Disabled, QtGui.QIcon.State.Off)
        self.labelViewGraphBtn.setIcon(iconlabelViewGraphBtn)
        self.labelViewGraphBtn.setCheckable(True)
        self.labelViewGraphBtn.setObjectName("labelViewGraphBtn")
        self.lang.set("labeling", "graphGroupMain", "convertGraphGroupView", self.labelViewGraphBtn)

        # =================================Selective View Table=============================
        self.graphGroupTable = custom_qtablewidget(obj_name="graphGroupTable", col=5,row=0)
        self.graphGroupTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.graphGroupTable.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.graphGroupTable_headerlabels = ["", "Show", "Color", "Name", ""]
        self.graphGroupTable.setting_headerlabels(labels=self.graphGroupTable_headerlabels)

        customHeader = custom_qheaderview(obj_name="graphGroupTable_custom_headerview")
        customHeader.set_clickable_sections([1])

        self.graphGroupTable.setHorizontalHeader(customHeader)
        self.graphGroupTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.graphGroupTable.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.graphGroupTable.horizontalHeader().setSectionsClickable(True)
        self.graphGroupTable.horizontalHeader().setHighlightSections(False)
        # ==================================================================================

        # =================================Label View Table=================================
        self.labelViewGraphGroupTable = custom_qtablewidget(obj_name="labelViewGraphGroupTable", col=3,row=0)
        self.labelViewGraphGroupTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.labelViewGraphGroupTable.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.labelViewGraphGroupTable_headerlabels = ["Show", "Color", "Name"]
        self.labelViewGraphGroupTable.setting_headerlabels(labels=self.labelViewGraphGroupTable_headerlabels)

        labelViewCustomHeader = custom_qheaderview(obj_name="labelViewGraphGroupTable_custom_headerview")
        labelViewCustomHeader.set_clickable_sections([0])

        self.labelViewGraphGroupTable.setHorizontalHeader(labelViewCustomHeader)
        self.labelViewGraphGroupTable.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.labelViewGraphGroupTable.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.labelViewGraphGroupTable.horizontalHeader().setSectionsClickable(True)
        self.labelViewGraphGroupTable.horizontalHeader().setHighlightSections(False)
        # ===================================================================================

        QtCore.QMetaObject.connectSlotsByName(form)
    
    def setupUiGraphList(self):
        """
            Description: Graph Group UI setup Function
            Author: GaEun Hwang (2025.12.05)
        """
        self.graphGroupAddBtn.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        self.graphGroupAddBtn.setMaximumSize(QtCore.QSize(iconSize, iconSize))
        self.graphGroupClearBtn.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        self.graphGroupClearBtn.setMaximumSize(QtCore.QSize(iconSize, iconSize))
        self.labelViewGraphBtn.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        self.labelViewGraphBtn.setMaximumSize(QtCore.QSize(iconSize, iconSize))

        self.gridLayout.setContentsMargins(5, 5, 5, 5)
        self.gridLayout.addLayout(self.topHorizonLayout, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.tableStackWidget, 1, 0, 1, 1)
        self.tableStackWidget.addWidget(self.graphGroupTable)
        self.tableStackWidget.addWidget(self.labelViewGraphGroupTable)
        self.tableStackWidget.setCurrentWidget(self.graphGroupTable)

        self.topHorizonLayout.addWidget(self.graphGroupAddBtn)
        self.topHorizonLayout.addWidget(self.graphGroupClearBtn)
        self.topHorizonLayout.addStretch(1)
        self.topHorizonLayout.addWidget(self.labelViewGraphBtn)

    def initFunction(self):
        """
            Description: Graph Group UI Function Init Function
            Author: GaEun Hwang (2025.12.05)
        """
        self.graphGroupAddBtn.clicked.connect(lambda : self.addGraphGroup(color=gen_color()))
        self.graphGroupClearBtn.clicked.connect(lambda : self.removeAllGraphGroup())
        self.labelViewGraphBtn.clicked.connect(lambda : self.convertGraphView())
        self.graphGroupTable.horizontalHeader().sectionClicked.connect(lambda : self.hideAllGraphGroup())
        self.labelViewGraphGroupTable.horizontalHeader().sectionClicked.connect(lambda : self.hideAllGraphGroup(labelView=True))
        self.buttonGroup.buttonClicked[int].connect(self.selectGraphGroup)

    def addGraphGroup(self, color=[255,255,255], name="Graph"):
        """
            Description: Add a new selective view graph group
            Author: GaEun Hwang (2025.12.05)
        """
        graphGroupIdx = self.graphGroupTable.rowCount()
        graphGroupName = f"{name}_{self.graphIndex}"
        self.graphGroupTable.insertRow(graphGroupIdx)

        # Select Widget
        graphGroupSelectWidget = self.graphGroupTable.create_obj(self.graphIndex, obj_type="widget", obj_list=["button:"])
        graphGroupSelectWidgetButton = graphGroupSelectWidget['button']
        graphGroupSelectWidgetButton.setObjectName("graphGroupSelectWidgetButton")
        graphGroupSelectWidgetButton.setCheckable(True)
        graphGroupSelectWidgetIcon = QtGui.QIcon()
        graphGroupSelectWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_select_off.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        graphGroupSelectWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_select_on.png"), QtGui.QIcon.Mode.Active, QtGui.QIcon.State.On)
        graphGroupSelectWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_select_off.png"), QtGui.QIcon.Mode.Active, QtGui.QIcon.State.Off)
        graphGroupSelectWidgetButton.setIcon(graphGroupSelectWidgetIcon)
        graphGroupSelectWidgetButton.setProperty("index", self.graphIndex)
        graphGroupSelectWidgetButton.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupSelectWidgetButton.setMaximumSize(QtCore.QSize(iconSize, iconSize))
        self.buttonGroup.addButton(graphGroupSelectWidgetButton, self.graphIndex)

        # Hide Widget
        graphGroupHideWidget = self.graphGroupTable.create_obj(self.graphIndex, obj_type="widget", obj_list=["button:"])
        graphGroupHideWidgetButton = graphGroupHideWidget['button']
        graphGroupHideWidgetButton.setObjectName("graphGroupHideWidgetButton")
        graphGroupHideWidgetButton.setCheckable(True)
        graphGroupHideWidgetButton.setChecked(True)
        graphGroupHideWidgetIcon = QtGui.QIcon()
        graphGroupHideWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_show.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        graphGroupHideWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_hide.png"), QtGui.QIcon.Mode.Active, QtGui.QIcon.State.Off)
        graphGroupHideWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_show.png"), QtGui.QIcon.Mode.Active, QtGui.QIcon.State.On)
        graphGroupHideWidgetButton.setIcon(graphGroupHideWidgetIcon)
        graphGroupHideWidgetButton.setProperty("index", self.graphIndex)
        graphGroupHideWidgetButton.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupHideWidgetButton.setMaximumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupHideWidgetButton.toggled.connect(lambda : self.hideGraphGroup(cnt=graphGroupHideWidgetButton.property("index")))

        # Color Widget
        graphGroupColorWidget = self.graphGroupTable.create_obj(self.graphIndex, obj_type="widget", obj_list=["button:"])
        graphGroupColorWidgetButton = graphGroupColorWidget['button']
        graphGroupColorWidgetButton.setObjectName("graphGroupColorWidgetButton")
        graphGroupColorWidgetButton.setProperty("index", self.graphIndex)
        graphGroupColorWidgetButton.setStyleSheet(f"background-color: rgb({color[0]}, {color[1]}, {color[2]}); border: 1px solid black;")
        graphGroupColorWidgetButton.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupColorWidgetButton.setMaximumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupColorWidgetButton.clicked.connect(lambda : self.selectGraphGroupColor(cnt=graphGroupColorWidgetButton.property("index")))

        # Name Widget
        graphGroupNameWidget = self.graphGroupTable.create_obj(self.graphIndex, obj_type="widget", obj_list=[f"lineedit:{graphGroupName}"])
        graphGroupNameWidgetLineEdit = graphGroupNameWidget['lineedit']
        graphGroupNameWidgetLineEdit.setObjectName("graphGroupNameWidgetLineEdit")
        graphGroupNameWidgetLineEdit.setMinimumWidth(50)
        graphGroupNameWidgetLineEdit.setReadOnly(False)
        graphGroupNameWidgetLineEdit.setProperty("index", self.graphIndex)
        graphGroupNameWidgetLineEdit.textChanged[str].connect(lambda : self.changeGraphGroupName(cnt=graphGroupIdx, txt=graphGroupNameWidgetLineEdit.text()))

        # Remove Widget
        graphGroupRemoveWidget = self.graphGroupTable.create_obj(self.graphIndex, obj_type="widget", obj_list=["button:"])
        graphGroupRemoveWidgetButton = graphGroupRemoveWidget['button']
        graphGroupRemoveWidgetButton.setObjectName("graphGroupRemoveWidgetButton")
        graphGroupRemoveWidgetButton.setCheckable(True)
        graphGroupRemoveWidgetButtonIcon = QtGui.QIcon()
        graphGroupRemoveWidgetButtonIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_remove.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        graphGroupRemoveWidgetButton.setIcon(graphGroupRemoveWidgetButtonIcon)
        graphGroupRemoveWidgetButton.setProperty("index", self.graphIndex)
        graphGroupRemoveWidgetButton.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupRemoveWidgetButton.setMaximumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupRemoveWidgetButton.clicked.connect(lambda : self.removeGraphGroup(item=graphGroupRemoveWidgetButton, cnt=graphGroupRemoveWidgetButton.property("index")))

        self.graphGroupTable.setCellWidget(graphGroupIdx, 0, graphGroupSelectWidget['widget'])
        self.graphGroupTable.setCellWidget(graphGroupIdx, 1, graphGroupHideWidget['widget'])
        self.graphGroupTable.setCellWidget(graphGroupIdx, 2, graphGroupColorWidget['widget'])
        self.graphGroupTable.setCellWidget(graphGroupIdx, 3, graphGroupNameWidget['widget'])
        self.graphGroupTable.setCellWidget(graphGroupIdx, 4, graphGroupRemoveWidget['widget'])

        self.graphGroupDict[self.graphIndex] = {
            "name": graphGroupName,
            "hide": True,
            "color": color,
            "objects": {
                "selectBtn": graphGroupSelectWidgetButton,
                "hideBtn": graphGroupHideWidgetButton,
                "colorBtn": graphGroupColorWidgetButton,
                "nameLineEdit": graphGroupNameWidgetLineEdit,
                "removeBtn": graphGroupRemoveWidgetButton
            },
            "coordinates": {}
        }
        self.graphIndex += 1

    def addLabelViewGraphGroup(self, labelClass, color=[255,255,255], name="Graph"):
        """
            Description: Add a new label view graph group
            Author: GaEun Hwang (2025.12.05)
        """
        graphGroupIdx = self.labelViewGraphGroupTable.rowCount()
        graphGroupName = f"{name}"
        self.labelViewGraphGroupTable.insertRow(graphGroupIdx)

        graphGroupHideWidget = self.labelViewGraphGroupTable.create_obj(labelClass, obj_type="widget", obj_list=["button:"])
        graphGroupHideWidgetButton = graphGroupHideWidget['button']
        graphGroupHideWidgetButton.setObjectName("labelViewGraphGroupHideWidgetButton")
        graphGroupHideWidgetButton.setCheckable(True)
        graphGroupHideWidgetButton.setChecked(True)
        graphGroupHideWidgetIcon = QtGui.QIcon()
        graphGroupHideWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_show.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
        graphGroupHideWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_hide.png"), QtGui.QIcon.Mode.Active, QtGui.QIcon.State.Off)
        graphGroupHideWidgetIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_show.png"), QtGui.QIcon.Mode.Active, QtGui.QIcon.State.On)
        graphGroupHideWidgetButton.setIcon(graphGroupHideWidgetIcon)
        graphGroupHideWidgetButton.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupHideWidgetButton.setMaximumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupHideWidgetButton.setProperty("labelClass", labelClass)
        graphGroupHideWidgetButton.toggled.connect(lambda : self.hideGraphGroup(cnt=graphGroupHideWidgetButton.property("labelClass"), labelView=True))

        graphGroupColorWidget = self.labelViewGraphGroupTable.create_obj(labelClass, obj_type="widget", obj_list=["button:"])
        graphGroupColorWidgetButton = graphGroupColorWidget['button']
        graphGroupColorWidgetButton.setObjectName("labelViewGraphGroupColorWidgetButton")
        graphGroupColorWidgetButton.setProperty("color", color)
        graphGroupColorWidgetButton.setStyleSheet(f"background-color: rgb({color[0]}, {color[1]}, {color[2]}); border: 1px solid black;")
        graphGroupColorWidgetButton.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        graphGroupColorWidgetButton.setMaximumSize(QtCore.QSize(iconSize, iconSize))

        graphGroupNameWidget = self.labelViewGraphGroupTable.create_obj(labelClass, obj_type="widget", obj_list=[f"lineedit:{graphGroupName}"])
        graphGroupNameWidgetLineEdit = graphGroupNameWidget['lineedit']
        graphGroupNameWidgetLineEdit.setObjectName("labelViewGraphGroupNameWidgetLineEdit")
        graphGroupNameWidgetLineEdit.setMinimumWidth(50)
        graphGroupNameWidgetLineEdit.setReadOnly(True)

        self.labelViewGraphGroupTable.setCellWidget(graphGroupIdx, 0, graphGroupHideWidget['widget'])
        self.labelViewGraphGroupTable.setCellWidget(graphGroupIdx, 1, graphGroupColorWidget['widget'])
        self.labelViewGraphGroupTable.setCellWidget(graphGroupIdx, 2, graphGroupNameWidget['widget'])

        self.labelViewGraphGroupDict[labelClass] = {
            "name": graphGroupName,
            "hide": True,
            "color": color,
            "objects": {
                "hideBtn": graphGroupHideWidgetButton,
                "colorBtn": graphGroupColorWidgetButton,
                "nameLineEdit": graphGroupNameWidgetLineEdit,
            },
            "coordinates": {}
        }

    def selectGraphGroup(self, cnt, emit=True):
        """
            Description: Select a graph group
            Author: GaEun Hwang (2025.12.08)
        """
        # setExclusive is needed to allow checking/unchecking the button
        # button group is not allow none selected state when exclusive is True
        self.buttonGroup.setExclusive(False)
        if self.graphControlDict['selectedGraphGroup'] == cnt:
            self.graphControlDict['oldSelectedGraphGroup'] = self.graphControlDict['selectedGraphGroup']
            self.graphControlDict['selectedGraphGroup'] = GRAPH_GROUP_NONE
            self.graphGroupDict[cnt]['objects']['selectBtn'].setChecked(False)
            self.graphObjDict['graph_check']['obj'].setChecked(False)
            self.graphObjDict['graph_eraser']['obj'].setChecked(False)
            if self.graphObjDict['graph_linedrawing']['obj'].isChecked() == True:
                self.graphObjDict['graph_linedrawing']['obj'].click()
        
        elif self.graphControlDict['selectedGraphGroup'] != cnt:
            self.graphControlDict['oldSelectedGraphGroup'] = self.graphControlDict['selectedGraphGroup']
            self.graphControlDict['selectedGraphGroup'] = cnt
            self.graphGroupDict[cnt]['objects']['selectBtn'].setChecked(True)
            if self.graphObjDict['graph_check']['obj'].isChecked() == False:
                self.graphObjDict['graph_check']['obj'].setChecked(True)
                if self.graphObjDict['graph_eraser']['obj'].isChecked() == True:
                    self.graphObjDict['graph_eraser']['obj'].setChecked(False)
            # line drawing on
            if self.graphObjDict['graph_linedrawing']['obj'].isChecked() == False:
                self.graphObjDict['graph_linedrawing']['obj'].click()
            # if selected, scroll to the selected row
            tableIdx = self.graphGroupTable.model().index(cnt, 0)
            self.graphGroupTable.scrollTo(tableIdx, QtWidgets.QAbstractItemView.PositionAtCenter)
        self.buttonGroup.setExclusive(True)

        if emit == True:
            emitDict = {
                "mode": GRAPH_GROUP_SELECT
            }
            self.graphGroupToDisplay.emit(emitDict)

    def hideGraphGroup(self, cnt, labelView=False):
        """
            Description: Hide a graph group
            Author: GaEun Hwang (2025.12.05)
        """
        if labelView == False:
            self.graphGroupDict[cnt]["hide"] = not self.graphGroupDict[cnt]["hide"]
            emitDict = {
                "mode": GRAPH_DISPLAY_PARTIAL,
                "view": "selective",
                "index": cnt,
                "hideState": self.graphGroupDict[cnt]["hide"]
            }
        else:
            self.labelViewGraphGroupDict[cnt]['hide'] = not self.labelViewGraphGroupDict[cnt]["hide"]
            emitDict = {
                "mode": GRAPH_DISPLAY_PARTIAL,
                "view": "label",
                "index": cnt,
                "hideState": self.labelViewGraphGroupDict[cnt]["hide"]
            }
        self.graphGroupToGraph.emit(emitDict)
        self.graphGroupToDisplay.emit(emitDict)

    def hideAllGraphGroup(self, labelView=False):
        """
            Description: Hide all graph groups
            Author: GaEun Hwang (2025.12.05)
        """
        if labelView == False:
            self.headerShowState = not self.headerShowState
            for graphGroup in self.graphGroupDict.values():
                if self.headerShowState:
                    # True -> Show
                    graphGroup["objects"]["hideBtn"].setChecked(True)
                else:
                    # False -> Hide
                    graphGroup["objects"]["hideBtn"].setChecked(False)

            emitDict = {
                "mode": GRAPH_DISPLAY_ALL,
                "view": "selective",
                "hideState": self.headerShowState
            }
        else:
            self.labelHeaderShowState = not self.labelHeaderShowState
            for graphGroup in self.labelViewGraphGroupDict.values():
                if self.labelHeaderShowState:
                    # True -> Show
                    graphGroup["objects"]["hideBtn"].setChecked(True)
                else:
                    # False -> Hide
                    graphGroup["objects"]["hideBtn"].setChecked(False)

            emitDict = {
                "mode": GRAPH_DISPLAY_ALL,
                "view": "label",
                "hideState": self.labelHeaderShowState
            }
        self.graphGroupToGraph.emit(emitDict)
        self.graphGroupToDisplay.emit(emitDict)

    def selectGraphGroupColor(self, cnt, color=None):
        """
            Description: Select a color for a graph group
            Author: GaEun Hwang (2025.12.05)
        """
        if color == None:
            # if color is none, it means clicked color button in selective graph table
            color = QColorDialog.getColor()            
            if color.isValid():
                r, g, b, _ = color.getRgb()
                self.graphGroupDict[cnt]["objects"]["colorBtn"].setProperty("color", [r, g, b])
                self.graphGroupDict[cnt]["objects"]["colorBtn"].setStyleSheet(f"background-color: rgb({r}, {g}, {b}); border: 1px solid black;")
                self.graphGroupDict[cnt]["color"] = [r, g, b]

                emitDict = {
                    "mode": GRAPH_GROUP_COLOR_CHANGE,
                    "index": cnt,
                    "color": color
                }
                self.graphGroupToGraph.emit(emitDict)
                self.graphGroupToDisplay.emit(emitDict)
        else:
            # if color is not none, it means changing color from label class
            self.labelViewGraphGroupDict[cnt]['objects']['colorBtn'].setProperty("color", color)
            self.labelViewGraphGroupDict[cnt]['objects']['colorBtn'].setStyleSheet(f"background-color: rgb({color[0]}, {color[1]}, {color[2]}); border: 1px solid black;")
            self.labelViewGraphGroupDict[cnt]['color'] = color

            emitDict = {
                "mode": GRAPH_GROUP_COLOR_CHANGE,
                "index": cnt,
                "color": color,
                "label": True
            }
            self.graphGroupToGraph.emit(emitDict)

    def changeGraphGroupName(self, cnt, txt, labelClass=False):
        """
            Description: Change the name of a graph group
            Author: GaEun Hwang (2025.12.05)
        """
        if labelClass == False:
            self.graphGroupDict[cnt]["objects"]["nameLineEdit"].setText(txt)
            self.graphGroupDict[cnt]["name"] = txt
        else:
            self.labelViewGraphGroupDict[cnt]["objects"]["nameLineEdit"].setText(txt)
            self.labelViewGraphGroupDict[cnt]["name"] = txt

    def removeGraphGroup(self, item, cnt):
        """
            Description: remove a graph group
            Author: GaEun Hwang (2025.12.05)
            History:
                Yugyeong Hong(2026.02.25): Refactor message box with util method and language support
        """
        if self.graphGroupTable.rowCount() <= 1:
            messageBox(mode=MESSAGE_BOX_WARNING,
                       title=self.lang.get("main", "messageBox", "msgWarning"),
                       text=self.lang.get("labeling", "graphGroupMain", "graphGroupWarningMsg"),
                       buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
            return
        # calculate the row index of the item to be removed
        indexRow = self.graphGroupTable.indexAt(item.parent().pos()).row()
        self.graphGroupTable.removeRow(indexRow)
        # if the removed graph group is selected, deselect it
        if cnt == self.graphControlDict['selectedGraphGroup']:
            self.graphControlDict['selectedGraphGroup'] = GRAPH_GROUP_NONE
        
        # remove graph coordinates from label view graph groups
        # reason: when checked graph in selective view, the graph coordinates are added to label view too.
        # and pixel checked in label view also added to selective view (new) graph group.
        for graphKey in self.graphGroupDict[cnt]["coordinates"].keys():
            for labelGraph in self.labelViewGraphGroupDict.values():
                if graphKey in labelGraph["coordinates"]:
                    del labelGraph["coordinates"][graphKey]

        emitDict = {
            "mode": GRAPH_GROUP_REMOVE,
            "index": cnt,
            "label": False
        }
        self.graphGroupToGraph.emit(emitDict)
        self.graphGroupToDisplay.emit(emitDict)
        
    def removeAllGraphGroup(self):
        """
            Description: remove all graph group
            Author: GaEun Hwang (2025.12.05)
        """
        emitDict = {
            "mode": GRAPH_GROUP_REMOVE_ALL
        }
        self.graphGroupToGraph.emit(emitDict)
        self.graphGroupToDisplay.emit(emitDict)
        self.clear()

    def convertGraphView(self):
        """
            Description: convert graph view mode
            Author: GaEun Hwang (2025.12.05)
        """
        if self.labelViewGraphBtn.isChecked() == True:
            # convert selective view -> label view
            self.graphControlDict['graph_view_mode'] = GRAPH_VIEW_MODE_LABEL_COLOR
            # when convert to label view, disable add/clear button. 
            # label view graph groups are managed by label classes.
            # if add/delete/clear/[color, name, number] change in label class, label view graph groups are updated.
            self.graphGroupAddBtn.setEnabled(False)
            self.graphGroupClearBtn.setEnabled(False)
            self.tableStackWidget.setCurrentWidget(self.labelViewGraphGroupTable)
            tempColor = gen_color()
            # add temporary graph group to selective view because when user check graph in label view and convert back to selective view
            self.addGraphGroup(color=tempColor)
            # if graph group is hidden, click hide button to show all graph groups before converting
            for graphGroup in self.graphGroupDict.values():
                if graphGroup["hide"] == False:
                    graphGroup["objects"]["hideBtn"].click()

            emitDict = {
                "mode": GRAPH_GROUP_CONVERT_LABEL_VIEW,
                "tempGraphIndex": self.graphIndex-1,
                "tempColor": tempColor
            }
            self.graphGroupToGraph.emit(emitDict)
            self.graphGroupToDisplay.emit(emitDict)
        else:
            # convert label view -> selective view
            self.graphControlDict['graph_view_mode'] = GRAPH_VIEW_MODE_SELECTIVE_COLOR
            self.tableStackWidget.setCurrentWidget(self.graphGroupTable)
            self.graphGroupAddBtn.setEnabled(True)
            self.graphGroupClearBtn.setEnabled(True)
            # remove temporary graph group if temporary graph group has no coordinates
            if len(self.graphGroupDict[self.graphIndex-1]["coordinates"].keys()) == 0:
                item = self.graphGroupDict[self.graphIndex-1]["objects"]["removeBtn"]
                self.removeGraphGroup(item=item, cnt=self.graphIndex-1)
            for graphGroup in self.labelViewGraphGroupDict.values():
                if graphGroup["hide"] == False:
                    graphGroup["objects"]["hideBtn"].click()
            emitDict = {
                "mode": GRAPH_GROUP_CONVERT_SELECTIVE_VIEW,
            }
            self.graphGroupToGraph.emit(emitDict)
            self.graphGroupToDisplay.emit(emitDict)

    def clearLabelTable(self):
        """
            Description: clear label view graph group table
            Author: GaEun Hwang (2025.12.05)
        """
        self.labelViewGraphGroupTable.setRowCount(0)
        self.labelViewGraphGroupDict.clear()
        # this function is called when overall graph groups are cleared
        # so uncheck label view button if it is checked
        if self.labelViewGraphBtn.isChecked() == True:
            self.labelViewGraphBtn.toggle()
        for labelClass, labelInfo in self.labelObjDict.items():
            color = labelInfo['color']
            name = labelInfo['name']
            self.addLabelViewGraphGroup(labelClass=labelClass, color=color, name=name)

    def clear(self):
        """
            Description: clear all graph groups
            Author: GaEun Hwang (2025.12.05)
        """
        self.graphControlDict['selectedGraphGroup'] = GRAPH_GROUP_NONE
        self.graphControlDict['oldSelectedGraphGroup'] = GRAPH_GROUP_NONE
        self.graphIndex = 0
        self.clearLabelTable()
        self.graphGroupTable.setRowCount(0)
        self.graphGroupDict.clear()
        self.addGraphGroup(color=gen_color())
        self.tableStackWidget.setCurrentWidget(self.graphGroupTable)
        if self.graphGroupAddBtn.isEnabled() == False:
            self.graphGroupAddBtn.setEnabled(True)
        if self.graphGroupClearBtn.isEnabled() == False:
            self.graphGroupClearBtn.setEnabled(True)
        self.graphControlDict['graph_view_mode'] = GRAPH_VIEW_MODE_SELECTIVE_COLOR

    @pyqtSlot(dict)
    def recieveSignal(self, receivedDict):
        """
            Description: Receive signal from other components
            Author: GaEun Hwang (2025.12.05)
        """
        from_ = receivedDict["from"]
        # IMAGE
        if from_ == "image":
            self.clear()

        # LABEL
        elif from_ == "label":
            mode = receivedDict["mode"]
            if mode == ADD_LABEL_GRAPH_GROUP:
                # when a new label is added in label class, add a new label view graph group
                labelClass = receivedDict["labelNumber"]
                color = receivedDict["labelColor"]
                name = receivedDict["labelName"]
                self.addLabelViewGraphGroup(labelClass=labelClass, color=color, name=name)

            elif mode == SELECT_LABEL_CLASS:
                # when select a label class in label class list, deselect graph group in selective view
                if self.graphControlDict['selectedGraphGroup'] != GRAPH_GROUP_NONE:
                    self.selectGraphGroup(self.graphControlDict['selectedGraphGroup'], emit=False)

            elif mode == CHANGE_LABEL_GRAPH_GROUP_NUMBER:
                # when change label class number in label class list, update label view graph group dict
                labelClass = receivedDict["labelNumber"]
                newLabelClass = receivedDict["newLabelNumber"]
                labelClassInfo = self.labelViewGraphGroupDict.pop(labelClass)
                self.labelViewGraphGroupDict[newLabelClass] = labelClassInfo
                self.labelViewGraphGroupDict[newLabelClass]["objects"]["hideBtn"].setProperty("labelClass", newLabelClass)

            elif mode == CHANGE_LABEL_GRAPH_GROUP_COLOR:
                # when change label class color in label class list, update label view graph group color
                labelClass = receivedDict["labelNumber"]
                color = receivedDict["labelColor"]
                self.selectGraphGroupColor(labelClass, color)

            elif mode == CHANGE_LABEL_GRAPH_GROUP_NAME:
                # when change label class name in label class list, update label view graph group name
                labelClass = receivedDict["labelNumber"]
                name = receivedDict["labelName"]
                self.changeGraphGroupName(labelClass, name, True)
                
                emitDict = {"mode": CHANGE_LABEL_GRAPH_GROUP_NAME,
                            "index": labelClass,
                            "name": name}
                self.graphGroupToGraph.emit(emitDict)
            
            elif mode == REMOVE_LABEL_CLASS:
                # when remove a label class in label class list, remove the corresponding label view graph group
                labelClass = receivedDict["labelNumber"]
                indexRow = self.labelViewGraphGroupTable.indexAt(self.labelViewGraphGroupDict[labelClass]["objects"]["hideBtn"].parent().pos()).row()
                self.labelViewGraphGroupTable.removeRow(indexRow)
                removedLabelItem = self.labelViewGraphGroupDict.pop(labelClass)
                self.labelViewGraphGroupDict[0]["coordinates"].update(removedLabelItem["coordinates"])
                emitDict = {"mode": GRAPH_GROUP_REMOVE,
                            "index": labelClass,
                            "label": True,
                            "removedLabelItem": removedLabelItem}
                self.graphGroupToGraph.emit(emitDict)
            
            elif mode == MERGE_LABEL:
                # when labels are merged in label class list
                sourceLabelClass = receivedDict["beforeLabelNumber"]
                targetLabelClass = receivedDict["afterLabelNumber"]
                
                # update label graph table
                indexRow = self.labelViewGraphGroupTable.indexAt(self.labelViewGraphGroupDict[sourceLabelClass]["objects"]["hideBtn"].parent().pos()).row()
                self.labelViewGraphGroupTable.removeRow(indexRow)
                # update label view graph group dict
                removedLabelItem = self.labelViewGraphGroupDict.pop(sourceLabelClass)
                self.labelViewGraphGroupDict[targetLabelClass]["coordinates"].update(removedLabelItem["coordinates"])
                
                # send signal to graph
                emitDict = {}
                emitDict["mode"] = MERGE_LABEL
                emitDict["labelClass"] = targetLabelClass
                emitDict["color"] = self.labelViewGraphGroupDict[targetLabelClass]["color"]
                self.graphGroupToGraph.emit(emitDict)

        # DISPLAY
        elif from_ == "display":
            mode = receivedDict["mode"]
            if mode == CHECK_GRAPH_POINT:
                # when a graph point is checked, update graph group dict and label view graph group dict
                point = receivedDict["point"]
                data = receivedDict["data"]
                selectiveGraphIdx = receivedDict["selectiveGraphIdx"]
                selectiveColor = receivedDict["selectiveColor"]
                labelClass = receivedDict["labelClass"]
                labelColor = receivedDict["labelColor"]
                self.graphGroupDict[selectiveGraphIdx]["coordinates"][point] = {"line": None, "scatter": None, "data": data}
                self.labelViewGraphGroupDict[labelClass]["coordinates"][point] = {"line": None, "scatter": None, "data": data}

                emitDict = {
                    "mode": GRAPH_GROUP_DRAW_GRAPH,
                    "point": point,
                    "data": data,
                    "color": [selectiveColor, labelColor],
                    "selectiveGraphIdx": selectiveGraphIdx,
                    "labelClass": labelClass,
                    "shape": receivedDict["shape"]
                }
                self.graphGroupToGraph.emit(emitDict)

            elif mode == REMOVE_GRAPH_POINT:
                # when a graph point is removed, update graph group dict and label view graph group dict
                emitDict = {
                    "mode": GRAPH_GROUP_REMOVE_GRAPH,
                    "removedSelectiveGraph": receivedDict["removedSelectiveGraph"],
                    "removedLabelGraph": receivedDict["removedLabelGraph"],
                    "point": receivedDict["point"],
                }
                self.graphGroupToGraph.emit(emitDict)
                del self.graphGroupDict[receivedDict["removedSelectiveGraph"]]["coordinates"][receivedDict["point"]]
                del self.labelViewGraphGroupDict[receivedDict["removedLabelGraph"]]["coordinates"][receivedDict["point"]]

            elif mode == SELECT_LABEL_PEN:
                # when label pen is selected, deselect graph group in selective view
                if self.graphControlDict['selectedGraphGroup'] != GRAPH_GROUP_NONE:
                    self.selectGraphGroup(self.graphControlDict['selectedGraphGroup'], emit=False)
                
        # GRAPH
        elif from_ == "graph":
            mode = receivedDict["mode"]
            # when graph object is checked/unchecked, update selected graph group accordingly
            if mode in [GRAPH_CHECK_ON, GRAPH_CHECK_OFF]:
                if self.graphControlDict["selectedGraphGroup"] == GRAPH_GROUP_NONE:
                    if self.graphControlDict["oldSelectedGraphGroup"] == GRAPH_GROUP_NONE:
                        self.selectGraphGroup(0)
                    else:
                        self.selectGraphGroup(self.graphControlDict["oldSelectedGraphGroup"])
                else:
                    if mode == GRAPH_CHECK_OFF:
                        self.selectGraphGroup(self.graphControlDict["selectedGraphGroup"])
            # graph eraser on/off -> unselect graph group if any is selected
            elif mode in [GRAPH_ERASE_ON, GRAPH_ERASE_OFF]:
                eraserState = True if mode == GRAPH_ERASE_ON else False
                graphPreviewState = self.graphObjDict['graph_linedrawing']['obj'].isChecked()
                if self.graphControlDict["selectedGraphGroup"] != GRAPH_GROUP_NONE:
                    self.selectGraphGroup(self.graphControlDict["selectedGraphGroup"])
                    self.graphObjDict['graph_eraser']['obj'].setChecked(eraserState)
                    if graphPreviewState != self.graphObjDict['graph_linedrawing']['obj'].isChecked():
                        self.graphObjDict['graph_linedrawing']['obj'].click()