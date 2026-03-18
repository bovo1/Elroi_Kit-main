"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from qtwidgets import AnimatedToggle
from PyQt5.QtWidgets import QMessageBox

class custom_qtablewidget(QtWidgets.QTableWidget):
    def __init__(self, obj_name="tablewidget_obj_name" , col=3, row=4, fontsize=10):
        super().__init__()
        """
            @Description: Qtablewidget을 상속받아 커스텀 UI 생성을 위한 클래스
            @Author: MyoungHwan (2024.10.29)
            @Parameters
                1. obj_name(str): 정의할 object name
                2. col: 초기 column 수
                3. row: 초기 row 수
                4. fontsize: table에 표시할 font에 대한 크기 지정
            @History
                1. Modified by MyoungHwan(24.12.05): fontsize 관련 코드 추가
                2. Modified by MyoungHwan(25.06.13): Fix scroll position moves irregularly when deleting a specific row in a CustomUI table.
        """
        self.setObjectName(obj_name)
        self.col = col
        self.row = row
        self.fontsize = fontsize
        # Modified by MyoungHwan(25.06.13): Fix scroll position moves irregularly when deleting a specific row in a CustomUI table.
        self.scrollbar = self.verticalScrollBar()
        
        self.__default__()
        self.__setting_column__()
        self.__setting_header__()
        self.__setting_row__()

    def __default__(self):
        """
            @description: Qtable UI 생성시 초기설정
            @author: MyoungHwan (2024.11.07)
        """
        self.setDragEnabled(False)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setFocusPolicy(Qt.NoFocus)
        fontsize = QFont()
        fontsize.setPointSize(self.fontsize)
        self.setFont(fontsize) #qtable default fontsize 지정

    def __setting_column__(self):
        """
            @description: Qtable UI 생성시 초기설정할 coloumn 수
            @author: MyoungHwan (2024.10.29)
        """
        self.setColumnCount(self.col)

    def __setting_header__(self):
        """
            @description: Qtable UI 생성시 초기설정할 Header 설정
            @author: MyoungHwan (2024.11.07)
        """
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionsClickable(False)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.verticalHeader().hide()

    def __setting_row__(self):
        """
            @description: Qtable UI 생성시 초기설정할 Row 수
            @author: MyoungHwan (2024.10.29)
        """
        self.setRowCount(self.row)

    def setting_headerlabels(self, labels):
        """
            @description: Qtableview 헤더 설정을 위한 라벨 지정
            @author: MyoungHwan (2024.10.29)
            @parameters
                1. labels(list): tableview 헤더에 설정할 리스트,
                    설정된 컬럼수와 맞지 않을경우, 일부항목이 제외될 수 있으며, None으로 대체될 수 있음
        """
        if len(labels) < self.col:
            tmp_cnt = self.col - len(labels)
            for _ in range(tmp_cnt):
                labels.append("None")
        else:
            labels = labels[:self.col]
        self.setHorizontalHeaderLabels(labels)

    def create_obj(self, idx, obj_type="widget",obj_list=["button:testbtn"], layout="horizon"):
        """
            @Description: Qtable UI 생성시 Item 추가를 위한 object 생성 부분
            @Author: MyoungHwan (2024.10.29)
            @Parameters
                1. obj_type(str): tableview cell에 넣기위해 item 혹은 widget 형식으로 넣기위한 항목
                    - item
                    - widget
                2. obj_list(list): obj_type에 들어갈 widget 형식
                    - button: ["button:이름"]
                    - toggle: ["toggle"]
                    - spinbox: ["spinbox:min,max,cur"], 정수형 spinbox
                    - doublespinbox: ["spinbox:min,max,cur"], 실수형 spinbox
                    - label: ["label:이름"]
                    - lineedit: ["lineedit:이름"]
                    - combobox: ["combobox:항목1,항목2,항목3"]
                3. layout: widget을 구성하기 위한 layout
                    - horizon
            @Return
                obj_type이 item 일경우 item 형식으로 반환
                obj_type이 widget 일경우 widget 형식으로 반환
                
            @History
                1. Modified by MyoungHwan(24.12.05): qtableitem 관련 코드 수정
                2. Modified by GaEun Hwang(25.09.29): Set lineedit and select button to have no focus for label selection shortcut key
        """
        if obj_type == "item":
            tmp_qitem = QtWidgets.QTableWidgetItem()
            tmp_qitem.setData(Qt.DisplayRole, obj_list) # table cell에 표시할 데이터 정의
            tmp_qitem.setTextAlignment(QtCore.Qt.AlignCenter)
            return tmp_qitem
        elif obj_type== "widget":
            tmp_obj_dict_ = {}
            # layout
            tmp_qwidget = QtWidgets.QWidget()
            if layout=="horizon":
                tmp_qlayout = QtWidgets.QHBoxLayout()

            for obj_ in obj_list:
                object_, value_ = obj_.split(":")
                if object_ == "button":
                    tmp_qbtn = QtWidgets.QPushButton()
                    tmp_qbtn.setObjectName(f"{idx}_tmp_qbtn")
                    tmp_qbtn.setText(value_)
                    tmp_obj_dict_["button"] = tmp_qbtn
                    tmp_qlayout.addWidget(tmp_qbtn)
                
                elif object_ == "toggle":
                    tmp_qtogglebox = AnimatedToggle(
                        pulse_checked_color="transparent",
                        pulse_unchecked_color="transparent"
                    )
                    tmp_qtogglebox.setObjectName(f"{idx}_tmp_qtogglebox")
                    tmp_qtogglebox.setFixedWidth(100)
                    tmp_obj_dict_["toggle"] = tmp_qtogglebox
                    tmp_qlayout.addWidget(tmp_qtogglebox)
                
                elif object_ == "spinbox":
                    minv, maxv, curv = list(map(int, value_.split(",")))
                    tmp_qspinbox = QtWidgets.QSpinBox()
                    tmp_qspinbox.setObjectName(f"{idx}_tmp_qspinbox")
                    tmp_qspinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
                    tmp_qspinbox.setRange(minv, maxv)
                    tmp_qspinbox.setFixedWidth(100)
                    tmp_qspinbox.setValue(curv)
                    tmp_qspinbox.setSingleStep(2)
                    tmp_qspinbox.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["spinbox"] = tmp_qspinbox
                    tmp_qlayout.addWidget(tmp_qspinbox)

                elif object_ == "doublespinbox":
                    minv, maxv, curv = list(map(float, value_.split(",")))
                    tmp_qdoublespinbox = QtWidgets.QDoubleSpinBox()
                    tmp_qdoublespinbox.setObjectName(f"{idx}_tmp_qdoublespinbox")
                    tmp_qdoublespinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
                    tmp_qdoublespinbox.setRange(minv, maxv)
                    tmp_qdoublespinbox.setFixedWidth(100)
                    tmp_qdoublespinbox.setValue(curv)
                    tmp_qdoublespinbox.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["spinbox"] = tmp_qdoublespinbox
                    tmp_qlayout.addWidget(tmp_qdoublespinbox)

                elif object_ == "label":
                    tmp_qlabel = QtWidgets.QLabel()
                    tmp_qlabel.setObjectName(f"{idx}_tmp_qlabel")
                    tmp_qlabel.setText(value_)
                    tmp_qlabel.setFixedWidth(tmp_qlabel.sizeHint().width() + 50)
                    tmp_obj_dict_["label"] = tmp_qlabel
                    tmp_qlayout.addWidget(tmp_qlabel)
                
                elif object_ == "lineedit":
                    tmp_qlineedit = QtWidgets.QLineEdit()
                    """
                        description : remove focus policy for lineedit because to fix bug not changing label name
                        author : GaEun Hwang (2025.10.29)
                    """
                    tmp_qlineedit.setObjectName(f"{idx}_tmp_qlineedit")
                    tmp_qlineedit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
                    tmp_qlineedit.setReadOnly(True)
                    tmp_qlineedit.setDragEnabled(True)
                    tmp_qlineedit.setText(value_)
                    tmp_qlineedit.setMinimumWidth(30)
                    tmp_qlineedit.setAlignment(QtCore.Qt.AlignCenter)
                    tmp_obj_dict_["lineedit"] = tmp_qlineedit
                    tmp_qlayout.addWidget(tmp_qlineedit)
                
                elif object_ == "combobox":
                    combo_qitems = value_.split(",")
                    tmp_qcombobox = QtWidgets.QComboBox()
                    tmp_qcombobox.setObjectName(f"{idx}_tmp_qcombobox")
                    tmp_qcombobox.addItems(combo_qitems)
                    tmp_obj_dict_["combobox"] = tmp_qcombobox
                    tmp_qlayout.addWidget(tmp_qcombobox)

            tmp_qwidget.setLayout(tmp_qlayout)
            tmp_obj_dict_["widget"] = tmp_qwidget
            return tmp_obj_dict_
    
    # Modified by MyoungHwan(25.06.13): Fix scroll position moves irregularly when deleting a specific row in a CustomUI table.
    def removeRow_(self, cur_row):
        cur_pos = self.scrollbar.value()
        self.removeRow(cur_row)
        self.scrollbar.setValue(cur_pos)


class custom_qheaderview(QtWidgets.QHeaderView):
    def __init__(self, obj_name="HeaderView_obj_name"):
        super().__init__(Qt.Horizontal, None)
        """
            @Description: Qtablewidget header에 대한 커스텀사용을 위한 HeaderView 클래스
                - 특정 Header column만 클릭가능하도록 custom class 생성
            @Author: MyoungHwan (2024.12.13)
            @Parameters
                1. obj_name: Headerview object name 지정
        """
        self.setObjectName(obj_name)

    def set_clickable_sections(self, sections):
        """
            @Description: 클릭 가능한 Header column 리스트 설정
            @Author: MyoungHwan (2024.12.13)
            @Parameters
                1. sections(List): 클릭 가능한 column 리스트 지정
        """
        self.clickable_sections = sections

    def mousePressEvent(self, event):
        """
            @Description: 마우스 클릭 이벤트 재정의
                - 클릭 가능한 Header column list 외 클릭 불가능하도록 설정
            @Author: MyoungHwan (2024.12.13)
        """
        pos = event.pos()
        section = self.logicalIndexAt(pos)  # 클릭된 column 확인
        if section not in self.clickable_sections:
            return  # 클릭된 column이 리스트에 존재하지 않을경우 ignore
        super().mousePressEvent(event)  # 클릭된 column이 리스트에 존재하지 않을경우 ignore

class ReDockOnCloseDockWidget(QtWidgets.QDockWidget):
    """
        @description: 
            When user wants to separate a dock into a floating window, give it a comfortable size and standard window buttons.
            When user clicks X on a floating dock, re-dock instead of hiding it.
        @author : Hyunsu Kim (2026.02.09)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Give floating docks a comfortable default size and standard window buttons.
        self.preferred_floating_size = QtCore.QSize(900, 700)
        try:
            self.topLevelChanged.connect(self.on_top_level_changed)
        except Exception:
            pass

    def setPreferredFloatingSize(self, w: int, h: int) -> None:
        self.preferred_floating_size = QtCore.QSize(int(w), int(h))

    def on_top_level_changed(self, floating: bool) -> None:
        if not floating:
            return
        try:
            # Ensure the floating dock has normal window controls (min/max buttons).
            self.setWindowFlags(
                self.windowFlags()
                | Qt.WindowMinimizeButtonHint
                | Qt.WindowMaximizeButtonHint
            )
            self.show()
            # If it's tiny, expand to a reasonable starting size.
            if self.width() < self.preferred_floating_size.width() or self.height() < self.preferred_floating_size.height():
                self.resize(self.preferred_floating_size)
        except Exception:
            pass

    def closeEvent(self, event):
        event.ignore()
        try:
            # If floating, dock back to its last dock position.
            if self.isFloating():
                self.setFloating(False)
            # If it was hidden by any means, restore.
            mw = self.parent()
            if isinstance(mw, QtWidgets.QMainWindow):
                mw.restoreDockWidget(self)
        except Exception:
            pass
        self.show()
        self.raise_()


def messageBox(mode=None, title=None, text=None, buttons=None):
    """
        Description:A wrapper function for QMessageBox to simplify the process of creating message boxes
        Parameters:
            mode: The type of message box (e.g., "information", "warning")
            title: The title of the message box
            text: The main text content of the message box
            buttons: A dictionary where keys are button texts and values are their roles ("accept" or "reject")
                    example: buttons={"Yes": "accept", "No": "reject"}
        Returns:
            response(str): Role of the clicked button
        Author: Yugyeong Hong(2026.02.24)
    """
    box = QMessageBox()
    box.setWindowTitle(title)
    box.setText(text)

    iconMapping = {
        "information": QMessageBox.Information,
        "warning": QMessageBox.Warning,
        "confirmation": QMessageBox.Question,
        "error" : QMessageBox.Critical
    }

    box.setIcon(iconMapping.get(mode, QMessageBox.NoIcon))

    buttonRoles = {
        "accept": QMessageBox.AcceptRole, # ex) for "OK" or "Yes"
        "reject": QMessageBox.RejectRole, # ex) for "No" or "Cancel"
        "ignore": QMessageBox.ActionRole
    }

    buttonRoleMap = {}
    # Add buttons based on the provided dictionary as many as needed
    if buttons is None:
        box.addButton("Ok", QMessageBox.AcceptRole)
    else:
        for buttonText, role in buttons.items():
            btn = box.addButton(buttonText, buttonRoles.get(role, QMessageBox.NoRole))
            buttonRoleMap[btn] = role
    box.exec_()
    clicked = box.clickedButton()
    return buttonRoleMap.get(clicked)