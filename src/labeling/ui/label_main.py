"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""
import random
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QColorDialog, QInputDialog, QMessageBox, QFileDialog
from PyQt5.QtCore import pyqtSlot, Qt
from constants.constants import *
if __name__ == "__main__" :
    from label_sub import label_sub_Form
else:
    from .label_sub import label_sub_Form

from utils.custom_ui import custom_qtablewidget, custom_qheaderview

## generate random color
gen_color = lambda : [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

from labeling.stylesheet.stylesheet_label_main import stylesheet

class Labellist_Form(QtWidgets.QWidget):
    """Label과 관련된 모든 기능을 처리하기 위한 클래스이다.
    """
    def __init__(self, Sync, lang):
        super().__init__()    
        self.init(Sync, lang)
        self.init_variable()
        self.init_Ui_label_main(self)
        self.init_Function()
        self.init_sub_Function()
        self.setup_Ui_label_main()
        if __name__ == "__main__":
            self.show()

    def init(self, Sync, lang):
        """Label 리스트 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.	Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.lang = lang
        self.Sync = Sync
        self.label_to_core_signal = self.Sync.label_to_core_signal
        self.label_to_display_signal = self.Sync.label_to_display_signal
        self.labelToGraphGroupSignal = self.Sync.labelToGraphGroupSignal
        self.label_image_to_display_signal = self.Sync.label_image_to_display_signal
        self.label_to_pen_style_signal = self.Sync.label_to_pen_style_signal
        self.core_to_label_signal = self.Sync.core_to_label_signal
        self.core_to_label_signal.connect(self.recv_from_core)

        self.label_obj_dict = self.Sync.label_obj_dict
        self.label_control_dict = self.Sync.label_control_dict
        self.core_obj_dict = self.Sync.core_obj_dict
        self.display_control_dict = self.Sync.display_control_dict
        self.sub_widget_dict = self.Sync.sub_widget_dict

    def init_variable(self):
        """
            @Description : 라벨 UI에서 사용할 변수 선언
            @Author : MyoungHwan
        """
        # Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        self.label_show_status = set()
        self.label_hide_sw = True

    @pyqtSlot(dict)
    def recv_from_core(self, output):
        """
            @Description : 라벨 리스트 업데이트를 위해 signal을 통해 실시간으로 정보를 업데이트하기 위한 함수이다. 이미지 load 후 라벨리스트를 업로드 한다.
            @Author : MyoungHwan
            @Parameters
                1.	output(dict): 라벨 리스트를 생성하기 위한 라벨 정보(라벨번호, 라벨 컬러)
            @History
                1. Modified by MyoungHwan(20240411) : data.json에 존재하는 라벨정보와 매핑안되는 이슈 개선
                2. Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        """
        # print("recv_from_core")
        # print(output)
        recv_from = output['from']
        if recv_from == 'image':
            mode = output['mode']
            if mode == 'load':
                if 'image_info' in output:
                    self.image_info = output['image_info']
                if 'image_number' in output:
                    self.image_number = output['image_number']
                self.all_label_remove()
                """
                    description
                    Modified by MyoungHwan(20240529) : data.json 에서 호출된 딕셔너리 정보 매핑코드 수정
                """
                label_list_dict = output['label_dict']
                for key_, value in label_list_dict.items():
                    label_name = value["label_name"]
                    label_color = value["label_color"]
                    self.create_label(label_num=key_, label_name=label_name, label_color=label_color, mode=1)

                #pen 적용을 위한 시그널
                tmp_dict = {}
                tmp_dict['mode'] = 'reset'
                self.label_to_pen_style(tmp_dict)


            elif mode == 'unchecked':
                if 'image_info' in output:
                    self.image_info = output['image_info']
                if 'image_number' in output:
                    self.image_number = output['image_number']
                self.all_label_remove()

        elif recv_from == 'core':
            mode = output['mode']
            if mode == 'load saved class data':
                self.prev_label_number = output['label_number_list']
                self.prev_label_name = output['label_name_list']
                # Added by GaEun Hwang (2025.06.05) : Add label color list
                self.prev_label_color = output['label_color_list']

                if self.prev_label_number and self.prev_label_name and self.prev_label_color:
                    self.load_prev_label.setEnabled(True)

    def init_Ui_label_main(self, Form):
        """Label 리스트 UI 생성을 위한 초기 선언문이다.
                Parmeters
                1.	Form(object): PyQt widget object
        """
        Form.setObjectName("label_Form")
        Form.setWindowTitle("label list Form")
        # Form.resize(1030, 717)
        Form.setStyleSheet(stylesheet)

        self.grid_main_window = QtWidgets.QGridLayout(Form)
        self.grid_main_window.setObjectName("grid_main_window")

        self.label_list_top_setting_horizon = QtWidgets.QHBoxLayout()
        self.label_list_top_setting_horizon.setObjectName("label_list_top_setting_horizon")
        
        self.label_list_add = QtWidgets.QPushButton()
        icon_label_list_add = QtGui.QIcon()
        icon_label_list_add.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_list_add.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.label_list_add.setIcon(icon_label_list_add)
        self.label_list_add.setObjectName("label_list_add")
        self.lang.set("labeling", "label_main", "label_list_add", self.label_list_add)

        self.label_list_clear = QtWidgets.QPushButton()
        icon_label_clear = QtGui.QIcon()
        icon_label_clear.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.label_list_clear.setIcon(icon_label_clear)
        self.label_list_clear.setObjectName("label_list_clear")
        self.lang.set("labeling", "label_main", "label_list_clear", self.label_list_clear)

        self.label_list_resorting = QtWidgets.QPushButton()
        icon_label_resorting = QtGui.QIcon()
        icon_label_resorting.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_resorting.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.label_list_resorting.setIcon(icon_label_resorting)
        self.label_list_resorting.setObjectName("label_list_resorting")
        self.lang.set("labeling", "label_main", "label_list_resorting", self.label_list_resorting)

        self.save_label = QtWidgets.QPushButton()
        icon_save_label = QtGui.QIcon()
        icon_save_label.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/save_label_on.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.save_label.setIcon(icon_save_label)
        self.save_label.setObjectName("save_label")
        self.lang.set("labeling", "label_main", "save_label", self.save_label)
        self.save_label.setShortcut("Ctrl+Shift+D")

        self.load_label = QtWidgets.QPushButton()
        icon_load_label = QtGui.QIcon()
        icon_load_label.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_load.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.load_label.setIcon(icon_load_label)
        self.load_label.setObjectName("load_label")
        self.lang.set("labeling", "label_main", "load_label", self.load_label)

        self.load_prev_label = QtWidgets.QPushButton()
        icon_load_prev_label = QtGui.QIcon()
        icon_load_prev_label.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/load_prev_label_on.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_load_prev_label.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/load_prev_label_off.png"), QtGui.QIcon.Disabled)
        self.load_prev_label.setIcon(icon_load_prev_label)
        self.load_prev_label.setDisabled(True)
        self.load_prev_label.setObjectName("load_prev_label")
        self.lang.set("labeling", "label_main", "load_prev_label", self.load_prev_label)

        self.label_list_setting = QtWidgets.QPushButton()
        icon_label_setting_icon = QtGui.QIcon()
        icon_label_setting_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_setting.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_label_setting_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_setting_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon_label_setting_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_setting_disabled.png"), QtGui.QIcon.Disabled)
        self.label_list_setting.setIcon(icon_label_setting_icon)
        self.label_list_setting.setObjectName("label_list_setting")
        self.label_list_setting.setCheckable(True)
        # self.lang.set("labeling", "label_main", "label_list_resorting", self.label_list_resorting)

        # Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        self.label_list_table = custom_qtablewidget(obj_name="label_list_table", col=6,row=0)
        self.label_list_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.label_list_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.label_list_table_headerlabels = ["", "Show", "Class", "Color", "Name",""]
        self.label_list_table.setting_headerlabels(labels=self.label_list_table_headerlabels)

        custom_header = custom_qheaderview(obj_name="label_list_table_custom_headerview")
        custom_header.set_clickable_sections([1])
        self.label_list_table_create_obj = self.label_list_table.create_obj

        self.label_list_table.setHorizontalHeader(custom_header)
        self.label_list_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.label_list_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        self.label_list_table.horizontalHeader().setSectionsClickable(True)
        self.label_list_table.horizontalHeader().setHighlightSections(False)


        QtCore.QMetaObject.connectSlotsByName(Form)

    def setup_Ui_label_main(self):
        """
            @Description : 초기화된 Label 리스트의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
            @Author : MyoungHwan
            @Parameters
            @History
                1. Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        """
        self.label_list_add.setMinimumSize(QtCore.QSize(30, 30))
        self.label_list_add.setMaximumSize(QtCore.QSize(30, 30))
        self.label_list_clear.setMinimumSize(QtCore.QSize(30, 30))
        self.label_list_clear.setMaximumSize(QtCore.QSize(30, 30))
        self.label_list_resorting.setMinimumSize(QtCore.QSize(30, 30))
        self.label_list_resorting.setMaximumSize(QtCore.QSize(30, 30))
        self.save_label.setMinimumSize(QtCore.QSize(30, 30))
        self.save_label.setMaximumSize(QtCore.QSize(30, 30))
        self.load_label.setMinimumSize(QtCore.QSize(30, 30))
        self.load_label.setMaximumSize(QtCore.QSize(30, 30))
        self.load_prev_label.setMinimumSize(QtCore.QSize(30, 30))
        self.load_prev_label.setMaximumSize(QtCore.QSize(30, 30))
        self.label_list_setting.setMinimumSize(QtCore.QSize(30, 30))
        self.label_list_setting.setMaximumSize(QtCore.QSize(30, 30))
        
        self.grid_main_window.setContentsMargins(6, 6, 6, 6)
        
        self.label_list_top_setting_horizon.addWidget(self.label_list_add)
        self.label_list_top_setting_horizon.addWidget(self.label_list_resorting)
        self.label_list_top_setting_horizon.addWidget(self.label_list_clear)
        self.label_list_top_setting_horizon.addWidget(self.save_label)
        self.label_list_top_setting_horizon.addStretch(1)
        self.label_list_top_setting_horizon.addWidget(self.load_label)
        self.label_list_top_setting_horizon.addWidget(self.load_prev_label)
        self.label_list_top_setting_horizon.addWidget(self.label_list_setting)

        self.grid_main_window.addLayout(self.label_list_top_setting_horizon, 0, 0, 1, 1)
        self.grid_main_window.addWidget(self.label_list_table, 1, 0, 1, 1)


    def init_Function(self):
        """
            @Description: Label 리스트에 존재하는 기능들에 대한 connect 함수를 정의한다.
            @Autorh: MyoungHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        """
        # Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        self.label_list_add.clicked.connect(lambda : self.label_add())
        self.label_list_clear.clicked.connect(lambda : self.all_label_remove(mode=1))
        self.label_list_resorting.clicked.connect(self.sorting_label_list)
        self.save_label.clicked.connect(self.save_label_class)
        self.load_label.clicked.connect(self.load_label_class)
        self.load_prev_label.clicked.connect(lambda : self.labels_add_using_prev_data())
        self.label_list_setting.clicked.connect(lambda ch=self.label_list_setting: self.label_sub_setting(ch=ch))
        self.label_list_table.itemClicked.connect(lambda ch=self.label_list_table: self.label_number_change(ch=ch))
        self.label_list_table.horizontalHeader().sectionClicked.connect(self.label_header_select_event)

    def label_header_select_event(self, idx):
        """
            @Description: Header column 선택시 발동하는 기능
            @Author: MyoungHwan (2024.12.13)
            @Parameters
                1. idx(int): column 번호
        """
        if idx == 1:
            self.label_hide_all()

    def init_sub_Function(self):
        self.label_sub_Form = label_sub_Form(Sync=self.Sync, lang=self.lang, parent=self)
        self.sub_widget_dict['label_sub_form'] = self.label_sub_Form

    def label_add(self):
        self.create_label(label_color=gen_color())

    def load_label_class(self):
        """
            Description: function to load saved label file(.npy)
            Author: Hyunsu Kim
        """
        image_number = self.image_number
        path = self.image_info['image_label_path'] if 'image_label_path' in self.image_info else self.image_info['label_path']
        fname = QFileDialog.getOpenFileName(self, 'Load_sal Label File', path, filter='*.npy')

        if len(fname[0]) > 0:
            tmp_dict = {}
            tmp_dict['from'] = 'label'
            tmp_dict['mode'] = 'modify'
            tmp_dict['type'] = 'image'
            tmp_dict['type_detail'] = 'detail'
            tmp_dict['type_detail_2'] = 1
            tmp_dict['select_image_number'] = image_number
            tmp_dict['file_path'] = fname[0]
            self.label_to_core(tmp_dict)

        tmp_dict = {}
        tmp_dict['mode'] = 'show'
        self.label_image_to_display(tmp_dict)
    
    def save_label_class(self):
        tmp_dict = {}
        tmp_dict['mode'] = 'save_label_class'
        self.label_to_core(tmp_dict)

    def labels_add_using_prev_data(self):
        """
            @ Description: function to apply saved label class information at the time you want
            @ Author: GaEun Hwang
        """
        self.check_and_add_label(self.prev_label_number, self.prev_label_name, self.prev_label_color)

    def check_and_add_label(self, number_list, name_list, color_list):
        """
            @ Description: check loaded label class in current label table and add class if not exist
            @ Author: GaEun Hwang
            @ Parameters
                1. number_list(int): saved label class number list
                2. name_list(str): saved label class name list
            @ History
                1. Added by GaEun Hwang(2025.06.05): Add color_list
        """
        label_number_list = number_list
        label_name_list = name_list
        label_color_list = color_list
        exist_label_number_dict = {}
        add_class_dict = {}
        override_dict = {}

        # If label Class exists, check the existing label class and add not exist label class
        for i in range(self.label_list_table.rowCount()):
            exist_label_number_widget = self.label_list_table.item(i, 2)
            exist_label_number_dict[int(exist_label_number_widget.text())] = exist_label_number_widget

        # If the number of label name and label number is matched, add label class
        if len(label_name_list) == len(label_number_list):
            for number, name, color in zip(label_number_list, label_name_list, label_color_list):
                if number not in exist_label_number_dict:
                    add_class_dict[number] = {"name": name, "color": color}
                else:
                    # If the label class you want to add already exist, change the label class name
                    item_widget = exist_label_number_dict[number]
                    item_row = self.label_list_table.indexFromItem(item_widget).row()
                    name_widget = self.label_list_table.cellWidget(item_row, 4)            
                    name_widget = name_widget.findChild(QtWidgets.QLineEdit)
                    color_widget = self.label_list_table.cellWidget(item_row, 3)
                    color_widget = color_widget.findChild(QtWidgets.QPushButton)

                    # If class number is same and class name is not same
                    if name != name_widget.text() or color_widget.property("color") != color:
                        override_dict[number] = {"name":name, "name_widget":name_widget, "color":color, "color_widget":color_widget}

            if override_dict:
                feedback_msg = (f"{list(override_dict.keys())} " + (self.lang.get("labeling", "label_main", "load_prev_label_warning_msg")))
                feedback = self.feedback_(title=self.lang.get("labeling", "label_main", "load_prev_label_warning_title"), msg=feedback_msg)
                for k,v in override_dict.items():
                    if feedback == QMessageBox.Yes:
                        v['name_widget'].setText(v['name'])
                        v['color_widget'].setStyleSheet(f"background-color: rgb({v['color'][0]}, {v['color'][1]}, {v['color'][2]});  border: 1px solid black;")
                        v['color_widget'].setProperty("color", v['color'])
                        self.label_name_change(v['name'], k)
                        self.label_color_select(cnt=k, obj=v['color_widget'], selected_color=v['color'])
                    elif feedback == QMessageBox.No:
                        break
                    else:
                        return
            for k,v in add_class_dict.items():
                self.create_label(label_num=k, label_name=v['name'], label_color=v['color'])

    def create_label(self, label_num = -1, label_name="", label_color = [255,255,255] ,mode= 0):
        """
            @Description: recv_from_core(output)에서 Label 리스트를 업데이트 하거나 Label 추가버튼을 클릭할 경우 Label UI object를 생성하기 위한 기능 정의문이다. 
            @Author: MyoungHwan
            @Parameters
                1.	label_num(int): Label 생성시 정의하기 위한 클래스 번호, 명시할 경우 명시한 번호로 지정되고 명시하지 않은 경우 count 변수에 의해 순차적으로 지정된다.
                2.  label_name(str): label name 지정
                3.	label_color(list): Label 생성시 정의하기 위한 color, 랜덤으로 생성된다.
                4.	mode(int)
                        - 0 : 새로운 Label 생성
                        - 1 : label.npy에 존재하는 Label을 기준으로 생성
            @History
                1. Modified by MyoungHwan (2024.09.06): Label Opacity 기능을 사용하기 위한 변수 추가
                2. Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        """
        # Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        if label_num == -1:
            result = 1
            while True:
                if result in self.label_obj_dict.keys():
                    result += 1
                else:
                    break
            label_num = result

        if label_name == "":
            label_name = f"Label_{label_num}"

        cur_row = self.label_list_table.rowCount()
        self.label_list_table.insertRow(cur_row)

        label_list_select_widget = self.label_list_table_create_obj(label_num, obj_type="widget", obj_list=["button:"])
        label_list_select_widget_button = label_list_select_widget['button']
        label_list_select_widget_button.setObjectName("label_list_select_widget_button")
        label_list_select_widget_button.setCheckable(True)
        label_list_select_icon = QtGui.QIcon()
        label_list_select_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_check_off.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        label_list_select_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_check_on.png"), QtGui.QIcon.Active, QtGui.QIcon.On)	 
        label_list_select_widget_button.setIcon(label_list_select_icon)
        label_list_select_widget_button.setMinimumSize(QtCore.QSize(30, 30))
        label_list_select_widget_button.setMaximumSize(QtCore.QSize(30, 30))
        label_list_select_widget_button.toggled.connect(lambda ch=label_list_select_widget_button, cnt=label_num: self.label_select(ch, cnt=cnt))
        self.label_list_table.setCellWidget(cur_row, 0, label_list_select_widget['widget'])

        label_list_hide_widget = self.label_list_table_create_obj(label_num, obj_type="widget", obj_list=["button:"])
        label_list_hide_widget_button = label_list_hide_widget['button']
        label_list_hide_widget_button.setObjectName("label_list_hide_widget_button")
        label_list_hide_widget_button.setCheckable(True)
        label_list_hide_icon = QtGui.QIcon()
        label_list_hide_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_hide.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        label_list_hide_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_hide.png"), QtGui.QIcon.Active, QtGui.QIcon.Off)
        label_list_hide_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_show.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        label_list_hide_widget_button.setIcon(label_list_hide_icon)
        label_list_hide_widget_button.setMinimumSize(QtCore.QSize(30, 30))
        label_list_hide_widget_button.setMaximumSize(QtCore.QSize(30, 30))
        label_list_hide_widget_button.toggled.connect(lambda : self.label_hide(cnt=label_num))
        self.label_list_table.setCellWidget(cur_row, 1, label_list_hide_widget['widget'])

        label_list_number_item = self.label_list_table_create_obj(label_num, obj_type="item", obj_list=label_num)
        self.label_list_table.setItem(cur_row, 2, label_list_number_item)

        label_list_color_widget = self.label_list_table_create_obj(label_num, obj_type="widget", obj_list=["button:"])
        label_list_color_widget_button = label_list_color_widget['button']
        label_list_color_widget_button.setObjectName("label_list_color_widget_button")
        label_list_color_widget_button.setProperty("color", label_color)
        label_list_color_widget_button.setStyleSheet(f"background-color: rgb({label_color[0]}, {label_color[1]}, {label_color[2]}); border: 1px solid black;")
        label_list_color_widget_button.setMinimumSize(QtCore.QSize(30, 30))
        label_list_color_widget_button.setMaximumSize(QtCore.QSize(30, 30))
        label_list_color_widget_button.clicked.connect(lambda : self.label_color_select(cnt=label_num , obj= label_list_color_widget_button, selected_color=None))
        self.label_list_table.setCellWidget(cur_row, 3, label_list_color_widget['widget'])

        label_list_name_widget = self.label_list_table_create_obj(label_num, obj_type="widget", obj_list=[f"lineedit:{label_name}"])
        label_list_name_widget_lineedit = label_list_name_widget['lineedit']
        label_list_name_widget_lineedit.setObjectName("label_list_name_widget_lineedit")
        label_list_name_widget_lineedit.setMinimumWidth(50)
        label_list_name_widget_lineedit.setReadOnly(False)
        label_list_name_widget_lineedit.textChanged[str].connect(lambda : self.label_name_change(txt=label_list_name_widget_lineedit.text(), cnt=label_num ))
        self.label_list_table.setCellWidget(cur_row, 4, label_list_name_widget['widget'])

        label_list_remove_widget = self.label_list_table_create_obj(label_num, obj_type="widget", obj_list=["button:"])
        label_list_remove_widget_button = label_list_remove_widget['button']
        label_list_remove_widget_button.setObjectName("label_list_remove_widget_button")
        label_list_remove_widget_button.setCheckable(True)
        label_list_remove_icon = QtGui.QIcon()
        label_list_remove_icon.addPixmap(QtGui.QPixmap("ico/labeling/labelbox/label_list_remove.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        label_list_remove_widget_button.setIcon(label_list_remove_icon)
        label_list_remove_widget_button.setMinimumSize(QtCore.QSize(30, 30))
        label_list_remove_widget_button.setMaximumSize(QtCore.QSize(30, 30))
        label_list_remove_widget_button.clicked.connect(lambda : self.select_label_remove(obj=label_list_remove_widget_button, cnt=label_num))
        self.label_list_table.setCellWidget(cur_row, 5, label_list_remove_widget['widget'])

        tmp_dict = {}
        tmp_dict['mode'] = 'create'
        tmp_dict['type'] = 'label'

        # create
        if mode == 0:
            tmp_dict['type_detail'] = 'new'
        # load
        else:
            tmp_dict['type_detail'] = 'load'
        tmp_dict['label_number'] = label_num
        tmp_dict['label_name'] = label_name
        tmp_dict['label_color'] = label_color
        self.label_to_core(tmp_dict)

        """
            Description: Label Opacity 기능을 사용하기 위한 변수 추가
            Modified by MyoungHwan(2024.09.06)
        """
        # Improvemented by MyoungHwan (2024.12.13): Label main Ui 구조 수정
        # abel_obj_dict 구조 수정
        self.label_obj_dict[label_num] ={
            'number': label_num,
            'color': label_color,
            'name': label_name,
            'label_color_alpha':1.0,
            'label_color_alpha_origin':1.0,
            'center_num': 1,
            'center_num_origin': 1,
            'include_spectrum':0,
            'obj_dict':{
                'select':label_list_select_widget_button,
                'show':label_list_hide_widget_button,
                'number':label_list_number_item,
                'color':label_list_color_widget_button,
                'name':label_list_name_widget_lineedit,
                'remove':label_list_remove_widget_button,
            }
        }

        # if label created, send signal to graph group
        emitDict = {
            "mode": ADD_LABEL_GRAPH_GROUP,
            "labelNumber": label_num,
            "labelName": label_name,
            "labelColor": label_color
        }
        self.labelToGraphGroupSignal.emit(emitDict)

        if mode == 0:
            #pen 적용을 위한 시그널
            tmp_dict = {}
            tmp_dict['mode'] = 'reset'
            self.label_to_pen_style(tmp_dict)

    def label_select(self, ch, cnt):
        """
            @Description: 특정 라벨 선택 시 발동되는 함수이다. 선택될 경우 Core DB, display에 상태 및 리스트를 업데이트하기 위한 시그널을 보낸다.
            @Author: MyoungHwan
            @Parameters
                1.	ch(bool)
                        - True : 라벨 선택 시
                        - False : 선택 해제 시
                2.	cnt(int): 선택한 라벨 클래스 번호
            @History
                1. Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                2. Improvemented by GaEun Hwang (2025.09.29): When selecting a label using shortcut, if the label is not visible, make it visible

        """
        if self.label_control_dict['label_control_sw']:
            if ch:
                self.core_obj_dict['status_labeling_status'].setText(f"Label: {cnt} [{self.label_obj_dict[cnt]['name']}]")
                self.label_control_dict['select_main_label_number'] = cnt
                self.label_control_dict['label_control_sw'] = False
                for label in self.label_obj_dict.keys():
                    if label != cnt:
                        # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                        if self.label_obj_dict[label]['obj_dict']['select'].isChecked():
                            self.label_obj_dict[label]['obj_dict']['select'].toggle()

                labelKeyList = list(self.label_obj_dict.keys())
                selectedNumberIndex = labelKeyList.index(cnt)
                # Make the selected label visible in the table
                tableIdx = self.label_list_table.model().index(selectedNumberIndex, 0)
                self.label_list_table.scrollTo(tableIdx, QtWidgets.QAbstractItemView.PositionAtCenter)
                self.label_control_dict['label_control_sw'] = True

                #display 적용을 위한 시그널
                tmp_dict = {}
                tmp_dict['mode'] = 'status'
                self.label_to_display(tmp_dict)

                # when label selected, send signal to graph group
                emitDict = {}
                emitDict["mode"] = SELECT_LABEL_CLASS
                self.labelToGraphGroupSignal.emit(emitDict)

            else:
                #disable
                if self.label_control_dict['select_main_label_number'] == cnt :
                    self.core_obj_dict['status_labeling_status'].setText(f"Label: ")
                    self.label_control_dict['old_select_label_number'] = cnt
                    self.label_control_dict['select_main_label_number'] = -1
                    self.label_control_dict['label_control_sw'] = False
                    for label in self.label_obj_dict.keys():
                        if label != cnt:
                            # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                            if self.label_obj_dict[label]['obj_dict']['select'].isChecked():
                                self.label_obj_dict[label]['obj_dict']['select'].toggle()
                    self.label_control_dict['label_control_sw'] = True

                    #display 적용을 위한 시그널
                    tmp_dict = {}
                    tmp_dict['mode'] = 'status'
                    self.label_to_display(tmp_dict)

            if self.label_obj_dict[cnt]['obj_dict']['select'].hasFocus():
                self.label_obj_dict[cnt]['obj_dict']['select'].clearFocus()

            #pen 적용을 위한 시그널
            tmp_dict = {}
            tmp_dict['mode'] = 'select'
            tmp_dict['type'] = 'main'
            self.label_to_pen_style(tmp_dict)
          
    def label_hide_all(self):
        """
            @Description: 모든 라벨 Show/Hide 기능
            @Author: MyoungHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13): all label show/hide 기능 및 label_obj_dict key 구조 수정
        """
        # Improvemented by MyoungHwan (2024.12.13): all label show/hide 기능 및 label_obj_dict key 구조 수정

        self.label_hide_sw = False # 라벨 show 함수 발동안되게 임시로 지정
        if len(self.label_show_status): # All label Hide
            for label_num in self.label_obj_dict.keys():
                if self.label_obj_dict[label_num]['obj_dict']['show'].isChecked():
                    self.label_obj_dict[label_num]['obj_dict']['show'].toggle()
            self.label_show_status = set()
            status = False
        else: # All label Show
            for label_num in self.label_obj_dict.keys():
                if self.label_obj_dict[label_num]['obj_dict']['show'].isChecked() == False:
                    self.label_obj_dict[label_num]['obj_dict']['show'].toggle()
            self.label_show_status = set(self.label_obj_dict.keys())
            status = True

        #display 적용을 위한 시그널
        tmp_dict = {}
        tmp_dict['mode'] = 'all_hide_show'
        tmp_dict['toggle'] = status
        self.label_to_display(tmp_dict)

        self.label_hide_sw = True
   
    def label_hide(self, cnt=None):
        """
            @Description: 선택한 라벨에 대해 display에 표시하거나 숨김
            @Author: MyoungHwan
            @Parameters
                1.	cnt(int): 선택한 라벨 번호
            @History
                1. Improvemented by MyoungHwan (2024.12.13): label show/hide 기능 및 label_obj_dict key 구조 수정
        """
        if self.label_hide_sw:
            # Improvemented by MyoungHwan (2024.12.13): label show/hide 기능 및 label_obj_dict key 구조 수정
            if self.label_obj_dict[cnt]['obj_dict']['show'].isChecked(): # hide -> show
                self.label_show_status.add(cnt)
            else:
                self.label_show_status.discard(cnt)
            # If hide Item has focus, not working select label using shortcut
            if self.label_obj_dict[cnt]['obj_dict']['show'].hasFocus():
                self.label_obj_dict[cnt]['obj_dict']['show'].clearFocus()

            #display 적용을 위한 시그널
            tmp_dict = {}
            tmp_dict['mode'] = 'hide'
            tmp_dict['label_number'] = cnt
            self.label_to_display(tmp_dict)


    def label_number_change(self, ch):
        """
            @Description: 기존 라벨 지우고 새로운 라벨에 이전 정보 복사, 새로운 라벨번호가 이미 존재할 경우 불가
            @Author: MyoungHwan
            @Parameters
                1.	cnt(int): 선택한 라벨 번호
            @History
                1. Improvemented by MyoungHwan (2024.12.13): label 번호 변경에 따른 동작 코드 수정
                2. Improvemented by GaEun Hwang (2025.09.29): When changing the label number, update status bar with label name 
        """
        # Improvemented by MyoungHwan (2024.12.13): label 번호 변경에 따른 동작 코드 수정
        row, col = ch.row(), ch.column()
        old_label = int(self.label_list_table.item(row, col).text())
        new_label, ok = QInputDialog.getInt(self, 'Input', 'Input change label number:',min=0)
        if ok: 
            if new_label not in self.label_obj_dict.keys():# 없는 경우
                self.label_obj_dict[new_label] = self.label_obj_dict.pop(old_label)

                #select btn
                self.label_obj_dict[new_label]['obj_dict']['select'].toggled.disconnect()
                self.label_obj_dict[new_label]['obj_dict']['select'].toggled.connect(lambda ch=self.label_obj_dict[new_label]['obj_dict']['select']: self.label_select(ch, cnt=new_label))

                #hide btn
                self.label_obj_dict[new_label]['obj_dict']['show'].toggled.disconnect()
                self.label_obj_dict[new_label]['obj_dict']['show'].toggled.connect(lambda : self.label_hide(cnt=new_label))

                #new_label change
                self.label_obj_dict[new_label]['number'] = new_label
                self.label_obj_dict[new_label]['obj_dict']['number'].setData(Qt.DisplayRole, new_label)

                #color change btn
                self.label_obj_dict[new_label]['obj_dict']['color'].clicked.disconnect()
                self.label_obj_dict[new_label]['obj_dict']['color'].clicked.connect(lambda : self.label_color_select(cnt=new_label , obj= self.label_obj_dict[new_label]['obj_dict']['color'], selected_color=None))

                # #name change btn
                self.label_obj_dict[new_label]['obj_dict']['name'].textChanged[str].disconnect()
                self.label_obj_dict[new_label]['obj_dict']['name'].textChanged[str].connect(lambda : self.label_name_change(txt=self.label_obj_dict[new_label]['obj_dict']['name'].text(), cnt=new_label))

                #label select delete btn
                self.label_obj_dict[new_label]['obj_dict']['remove'].clicked.disconnect()
                self.label_obj_dict[new_label]['obj_dict']['remove'].clicked.connect(lambda : self.select_label_remove(obj=self.label_obj_dict[new_label]['obj_dict']['remove'], cnt=new_label))

                tmp_dict = {}
                tmp_dict['mode'] = 'modify'
                tmp_dict['type'] = 'label'
                tmp_dict['type_detail'] = 'number'
                tmp_dict['label_number'] = new_label
                tmp_dict['label_old_number'] = old_label
                self.label_to_core(tmp_dict)

                tmp_dict = {}
                tmp_dict['mode'] = 'number'
                tmp_dict['old_label_number'] = old_label
                tmp_dict['new_label_number'] = new_label
                self.label_to_display(tmp_dict)

                # when label number changed, send signal to graph group
                emitDict = {}
                emitDict['mode'] = CHANGE_LABEL_GRAPH_GROUP_NUMBER
                emitDict['labelNumber'] = old_label
                emitDict['newLabelNumber'] = new_label
                self.labelToGraphGroupSignal.emit(emitDict)
            
                if old_label == 0:
                    self.create_label(label_num = old_label, mode=0)

                if self.label_control_dict['select_main_label_number'] == old_label:
                    self.label_control_dict['select_main_label_number'] = new_label
                if self.label_control_dict['select_sub_label_number'] == old_label:
                    self.label_control_dict['select_sub_label_number'] = new_label

                self.label_show_status.discard(old_label)
                self.label_show_status.add(new_label)
                                
                #pen 적용을 위한 시그널
                tmp_dict = {}
                tmp_dict['mode'] = 'reset'
                self.label_to_pen_style(tmp_dict)
                self.core_obj_dict['status_labeling_status'].setText(f"Label: {new_label} [{self.label_obj_dict[new_label]['name']}]")
                # When changing to a number that does not exist, label_obj_dict's order is changed.
                # So, resorting is needed for select label using shortcut correctly.
                self.label_list_resorting.click()

            elif old_label == new_label:
                """
                    Description: Prevent a chanage to same class
                    Author : Hyeok Yoon (2025.11.06)
                """
                self.warning_(self.lang.get("labeling", "label_main", "load_prev_label_merge_same_warning_title"), self.lang.get("labeling", "label_main", "load_prev_label_merge_same_warning_msg"))
            else:
                """
                    Description: Label merging part, This part trying to merging new_label to old_label
                    Author : Hyeok Yoon (2025.11.06)
                """
                feedback = self.feedback_(self.lang.get("labeling", "label_main", "load_prev_label_merge_warning_title"), self.lang.get("labeling", "label_main", "load_prev_label_merge_warning_msg"), "yes_no")
                if feedback == QMessageBox.Yes:
                    tmp_dict = {}
                    tmp_dict['mode'] = 'modify'
                    tmp_dict['type'] = 'label'
                    tmp_dict['type_detail'] = 'number'
                    tmp_dict['label_number'] = new_label
                    tmp_dict['label_old_number'] = old_label
                    self.label_to_core(tmp_dict)

                    tmp_dict['mode'] = 'number'
                    tmp_dict['old_label_number'] = old_label
                    tmp_dict['new_label_number'] = new_label
                    self.label_to_display(tmp_dict)

                    tmp_dict['mode'] = 'color'
                    tmp_dict['label_number'] = new_label
                    self.label_to_display(tmp_dict)

                    if not self.label_obj_dict[new_label]['obj_dict']['select'].isChecked() and self.label_obj_dict[old_label]['obj_dict']['select'].isChecked():
                        self.label_obj_dict[new_label]['obj_dict']['select'].click()

                    if old_label == 0:
                        self.create_label(label_num = old_label, mode=0)

                    self.label_control_dict['select_main_label_number'] = new_label
                    self.label_control_dict['select_sub_label_number'] = new_label

                    self.label_show_status.discard(old_label)
                    self.label_list_table.removeRow_(row)
                    if old_label != 0: del self.label_obj_dict[old_label]
                    
                    #pen 적용을 위한 시그널
                    tmp_dict = {}
                    tmp_dict['mode'] = 'reset'
                    self.label_to_pen_style(tmp_dict)
                    self.core_obj_dict['status_labeling_status'].setText(f"Label: {new_label} [{self.label_obj_dict[new_label]['name']}]")

                    emitDict = {}
                    emitDict['mode'] = MERGE_LABEL
                    emitDict['beforeLabelNumber'] = old_label
                    emitDict['afterLabelNumber'] = new_label
                    self.labelToGraphGroupSignal.emit(emitDict)

    def label_color_select(self, cnt=None, obj=None , selected_color=None):
        """
            @Description: 선택 라벨 컬러변경, display도 반영
            @Author: MyoungHwan
            @Parameters
                1.	cnt(int): 선택한 라벨 번호
                2.	obj(object): 선택한 라벨 object
                3.  selected_color(list): selected color
            @History
                1. Improvemented by MyoungHwan (2024.12.13): label 색상 변경에 따른 동작 코드 수정
                2. Modified by GaEun Hwang (2025.06.05): Modify branching behavior based on selected_color value
                3. Modified by MyoungHwan (2025.06.17): Modify pen sub sytle signal type (reset -> select, main)
        """
        color = None
        if selected_color == None:
            col = QColorDialog.getColor()
            if col.isValid():
                r, g, b, _ = col.getRgb()
                color = [r,g,b]
                hexcol = "{:02X}{:02X}{:02X}".format(r,g,b)
                obj.setStyleSheet("background-color: #%s; border: 1px solid black;" % hexcol)
                self.label_obj_dict[cnt]['color']=color
        else:
            color = selected_color
            self.label_obj_dict[cnt]['color'] = color

        """
            Description: Added code to send color update information to DB 
            Modified by MyoungHwan (2024.09.06) 
        """
        if color is not None:
            tmp_dict = {}
            tmp_dict['mode'] = 'modify'
            tmp_dict['type'] = 'label'
            tmp_dict['type_detail'] = 'color'
            tmp_dict['label_number'] = cnt
            tmp_dict['label_color'] = color
            self.label_to_core(tmp_dict)

            #display 적용을 위한 시그널
            tmp_dict = {}
            tmp_dict['mode'] = 'color'
            tmp_dict['label_number'] = cnt
            self.label_to_display(tmp_dict)

            #pen 적용을 위한 시그널
            # Modified by MyoungHwan (2025.06.17): Modify pen sub sytle signal type (reset -> select, main)
            tmp_dict = {}
            tmp_dict['mode'] = 'select'
            tmp_dict['type'] = 'main'
            self.label_to_pen_style(tmp_dict)

            # when label color changed, send signal to graph group
            emitDict = {}
            emitDict['mode'] = CHANGE_LABEL_GRAPH_GROUP_COLOR
            emitDict['labelNumber'] = cnt
            emitDict['labelColor'] = color
            self.labelToGraphGroupSignal.emit(emitDict)
        # If color Item has focus, not working select label using shortcut
        if self.label_obj_dict[cnt]['obj_dict']['color'].hasFocus():
            self.label_obj_dict[cnt]['obj_dict']['color'].clearFocus()

    def label_name_change(self, txt="", cnt=None):
        """선택 라벨 이름 변경
                Parameters
                1.	txt(str): 변경하고자 하는 이름
                2.	cnt(int): 선택한 라벨 번호

                @ History
                    1. Improvemented by GaEun Hwang (2025.09.29): When changing the label name, update status bar with label name

        """
        self.label_obj_dict[cnt]['name'] = txt
        
        tmp_dict = {}
        tmp_dict['mode'] = 'modify'
        tmp_dict['type'] = 'label'
        tmp_dict['type_detail'] = 'name'
        tmp_dict['label_number'] = cnt
        tmp_dict['label_name'] = txt
        self.label_to_core(tmp_dict)
        
        # when label name changed, send signal to graph group
        emitDict = {}
        emitDict['mode'] = CHANGE_LABEL_GRAPH_GROUP_NAME
        emitDict['labelNumber'] = cnt
        emitDict['labelName'] = txt
        self.labelToGraphGroupSignal.emit(emitDict)

        self.core_obj_dict['status_labeling_status'].setText(f"Label: {cnt} [{self.label_obj_dict[cnt]['name']}]")

    def warning_(self, title="", msg="", info=None):
        warning_msgBox = QMessageBox()
        warning_msgBox.setIcon(QMessageBox.Information)
        warning_msgBox.setText(msg)
        warning_msgBox.setWindowTitle(title)
        warning_msgBox.setStandardButtons(QMessageBox.Ok)
        returnValue = warning_msgBox.exec_()

    """
        Description: Add type argument to distinguish yes_no and yes_no_cancel option
        Modified by Hyeok Yoon (2025.11.06)
    """
    def feedback_(self, title="", msg="", type="yes_no_cancel", info=None):
        feedback_msgBox = QMessageBox()
        feedback_msgBox.setIcon(QMessageBox.Question)
        feedback_msgBox.setText(msg)
        feedback_msgBox.setWindowTitle(title)
        if type == "yes_no":
            feedback_msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        elif type == "yes_no_cancel":
            feedback_msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        feedback = feedback_msgBox.exec_()

        return feedback

    def select_label_remove(self, obj, cnt):
        """
            @Description: 선택 라벨 삭제 Core DB에도 업데이트
            @Author: MyoungHwan
            @Parameters
                1.	cnt(int): 선택한 라벨 번호
                2.	obj(object): 선택한 라벨 object
            @History
                1. Improvemented by MyoungHwan (2024.12.13): label 삭제 동작 코드 수정
                2. Modified by MyoungHwan(25.06.13): Fix scroll position moves irregularly when deleting a specific row in a CustomUI table.

        """
        delete_check = True

        if cnt == 0:
            self.warning_(title=self.lang.get("labeling", "label_main", "label_index_error_title"), msg=self.lang.get("labeling", "label_main", "label_index_remove_zero_error_msg"))
            delete_check = False

        elif len(self.label_obj_dict.keys()) == 1:
            print(f"Can not remove last index!")
            self.warning_(title=self.lang.get("labeling", "label_main", "label_index_error_title"), msg=self.lang.get("labeling", "label_main", "label_index_remove_last_error_msg"))
            delete_check = False

        if delete_check:
            # Improvemented by MyoungHwan (2024.12.13): label 삭제 동작 코드 수정
            pos = obj.mapTo(self.label_list_table, obj.rect().topLeft())
            cur_row = self.label_list_table.indexAt(pos).row()
            # Modified by MyoungHwan(25.06.13): Fix scroll position moves irregularly when deleting a specific row in a CustomUI table.
            self.label_list_table.removeRow_(cur_row)
            self.label_show_status.discard(cnt)
            del self.label_obj_dict[cnt]
            
            if self.label_control_dict['select_main_label_number'] == cnt:
                self.label_control_dict['select_main_label_number'] = -1
                self.display_control_dict['drawing_mode'] = -1
            if self.label_control_dict['select_sub_label_number'] == cnt:
                self.label_control_dict['select_sub_label_number'] = -1

            tmp_dict = {}
            tmp_dict['mode'] = 'delete'
            tmp_dict['type'] = 'label'
            tmp_dict['select_type'] = 'one'
            tmp_dict['label_number'] = cnt
            self.label_to_core(tmp_dict)

            #display 적용을 위한 시그널
            tmp_dict = {}
            tmp_dict['mode'] = 'show'
            tmp_dict['type'] = 'select_remove'
            tmp_dict['label_number'] = cnt
            self.label_to_display(tmp_dict)

            # when label removed, send signal to graph group
            emitDict = {}
            emitDict['mode'] = REMOVE_LABEL_CLASS
            emitDict['labelNumber'] = cnt
            self.labelToGraphGroupSignal.emit(emitDict)
            
            #pen 적용을 위한 시그널
            tmp_dict = {}
            tmp_dict['mode'] = 'reset'
            self.label_to_pen_style(tmp_dict)

    def all_label_remove(self, mode=0):
        """
            @Description: 존재하는 모든 라벨 삭제, 제거 후 새로운 default(0) 라벨 생성
            @Author: MyoungHwan
            @Parameters
                1.	mode(int)
                    - 0 : 리셋 모드
                    - 1 : 모든 라벨 삭제 및 Core DB 업데이트
            @History
                1. Improvemented by MyoungHwan (2024.12.13): all label 삭제 동작 코드 수정

        """
        # Improvemented by MyoungHwan (2024.12.13): all label 삭제 동작 코드 수정
        self.clear_data_list()
        self.label_list_table.clear()
        self.label_list_table.setRowCount(0)
        self.label_list_table.setting_headerlabels(labels=self.label_list_table_headerlabels)

        self.label_show_status = set()
 
        if mode == 1:
            self.label_control_dict['select_main_label_number'] = -1
            self.label_control_dict['select_sub_label_number'] = -1
            # 저장된 모든 라벨정보 삭제 
            tmp_dict = {}
            tmp_dict['mode'] = 'delete'
            tmp_dict['type'] = 'label'
            tmp_dict['select_type'] = 'all'
            self.label_to_core(tmp_dict)

            self.create_label(label_num=0, mode=0)

            #display 적용을 위한 시그널
            tmp_dict = {}
            tmp_dict['mode'] = 'show'
            tmp_dict['type'] = 'reset'
            self.label_to_display(tmp_dict)
            
        #pen 적용을 위한 시그널
        tmp_dict = {}
        tmp_dict['mode'] = 'reset'
        self.label_to_pen_style(tmp_dict)

    def sorting_label_list(self):
        """
            @Description: sorting label
            @Author: MyoungHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13): Label sorting 기능 수정
                2. Improvemented by GaEun Hwang (2025.10.17): when sorting label list, self.label_obj_dict is also sorted
        """
        self.label_list_table.sortItems(2, QtCore.Qt.AscendingOrder)
        sortedLabelItems = sorted(self.label_obj_dict.items())
        self.label_obj_dict.clear()
        for key, value in sortedLabelItems:
            self.label_obj_dict[key] = value

    def clear_data_list(self):
        """호출한 데이터들의 리스트를 초기화하기 위한 함수.
        """
        #delete label object, 메모리 주소를 그대로 보존하기 위해 del 사용, 초기화 x
        for key in list(self.label_obj_dict.keys()):
            del self.label_obj_dict[key]
        
    def label_sub_setting(self, ch):
        if ch:
            self.label_sub_Form.show()
        else:
            self.label_sub_Form.close()


    def label_to_core(self, input):
        """label에서 core로 시그널을 보내기 위한 함수 선언문이다. Core DB에 대한 값을 업데이트하거나 조정하기 위한 함수로 쓰인다.
                Parameters
                1.	input(dict): Core DB업데이트를 위한 dictionary

        """
        self.label_to_core_signal.emit(input)

    def label_image_to_display(self, input):
        """label에서 display로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 display에 최종적으로 전달된다. 선택한 이미지로 display를 업데이트 하기위해 사용
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary

        """
        self.label_image_to_display_signal.emit(input)

    def label_to_display(self, input):
        """label에서 display로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 display에 최종적으로 전달된다. 선택한 이미지로 display를 업데이트 하기위해 사용
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary

        """
        self.label_to_display_signal.emit(input)

    def label_to_pen_style(self, input):
        """label에서 pen style로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 pen style에 최종적으로 전달된다. 선택한 라벨번호에 대한 업데이트 하기위해 사용
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary

        """
        self.label_to_pen_style_signal.emit(input)
        
    

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Labellist_Form()
    # ui.init_Ui_label_main(Form)
    # Form.show()
    sys.exit(app.exec_())
