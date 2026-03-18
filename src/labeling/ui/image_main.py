"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView, QFileDialog, QListView, QTreeView, QWidget
from constants.constants import MESSAGE_BOX_WARNING
from labeling.stylesheet.stylesheet_image_main import stylesheet
if __name__ == "__main__" :
    from image_sub_detail import Image_detail_Form
else:
    from .image_sub_detail import Image_detail_Form

from utils.custom_ui import custom_qtablewidget, messageBox
from labeling.stylesheet.stylesheet_image_main import stylesheet

class Image_Form(QWidget):
    """Image와 관련된 모든 기능을 처리하기 위한 클래스
    """

    def __init__(self, Sync, lang) -> None:
        super().__init__()
        self.init(Sync, lang)
        self.init_Ui_image_main(self)
        self.init_Function()
        self.init_variable()
        self.setup_Ui_image_main()

        self.image_detail_form = Image_detail_Form(Sync, self, self.lang)

        if __name__ == "__main__":
            self.show()

    def init(self, Sync=None, lang=None):
        """Image 리스트 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.Sync = Sync
        self.lang = lang
        self.image_to_core_signal = self.Sync.image_to_core_signal
        self.image_to_label_signal = self.Sync.image_to_label_signal
        self.image_to_label_sub_signal = self.Sync.image_to_label_sub_signal
        self.image_to_display_signal = self.Sync.image_to_display_signal
        self.image_to_display_sub_rgb_change_signal = self.Sync.image_to_display_sub_rgb_change_signal
        self.image_to_labeling_mode_main_signal = self.Sync.image_to_labeling_mode_main_signal
        self.imageToGraphGroupSignal = self.Sync.imageToGraphGroupSignal
        self.image_to_graph_signal  = self.Sync.image_to_graph_signal
        self.image_to_graph_sub_signal = self.Sync.image_to_graph_sub_signal
        self.imageToSemiAutoLabelingSignal = self.Sync.imageToSemiAutoLabelingSignal

        self.core_obj_dict = self.Sync.core_obj_dict
        self.image_obj_dict = self.Sync.image_obj_dict
        self.image_control_dict = self.Sync.image_control_dict

    
    def init_variable(self):
        """
            @Description: Image Main UI에서 사용되는 변수를 초기화 하는 함수
            @Author: MyoungHwan
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
                2. Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
        """
        self.image_number = 1
        self.data_list = []
        self.connect_sw = True

    def init_Ui_image_main(self, Form):
        """
            @Description: Image 리스트 UI 생성을 위한 초기 선언문이다.
            @Author: MyoungHwan
            @Parmeters
                1. Form(object): PyQt widget object
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        """
        Form.setObjectName("image_Form")
        Form.setWindowTitle("image list Form")
        Form.setStyleSheet(stylesheet)
        
        self.image_list_main_grid = QtWidgets.QGridLayout(Form)
        self.image_list_main_grid.setObjectName("image_list_main_grid")

        self.image_list_setting_horizon = QtWidgets.QHBoxLayout()
        self.image_list_setting_horizon.setObjectName("image_list_setting_horizon")

        self.image_add = QtWidgets.QPushButton()
        image_add_icon = QtGui.QIcon()
        image_add_icon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_add.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.image_add.setIcon(image_add_icon)
        self.image_add.setObjectName("image_add")
        self.lang.set("labeling", "image_main", "image_add", self.image_add)

        self.image_clear = QtWidgets.QPushButton()
        image_clear_icon = QtGui.QIcon()
        image_clear_icon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_clear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.image_clear.setIcon(image_clear_icon)
        self.image_clear.setObjectName("image_clear")
        self.lang.set("labeling", "image_main", "image_clear", self.image_clear)

        self.image_dir = QtWidgets.QLineEdit()
        self.image_dir.setReadOnly(True)
        self.image_dir.setObjectName("image_dir")

        self.image_setting = QtWidgets.QPushButton()
        image_setting_icon = QtGui.QIcon()
        image_setting_icon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_setting.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        image_setting_icon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_setting_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.image_setting.setIcon(image_setting_icon)
        self.image_setting.setObjectName("image_setting")
        self.image_setting.setCheckable(True)
        self.lang.set("labeling", "image_main", "image_setting", self.image_setting)

        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        # custom qtablewidet을 이용하여 UI 생성
        self.image_list_table = custom_qtablewidget(obj_name="image_list_table", col=4,row=0)
        self.image_list_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.image_list_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.image_list_table_headerlabels = ["", "Num", "Name", " "]
        self.image_list_table.setting_headerlabels(labels=self.image_list_table_headerlabels)
        self.image_list_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch) # 2번 header 최대너비로 resize
        self.image_list_table_create_obj = self.image_list_table.create_obj

        QtCore.QMetaObject.connectSlotsByName(Form)

    def setup_Ui_image_main(self):
        """
            @Description: 초기화된 widget 및 layout 디자인 정의함수
            @Author: MyoungHwan
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        """
        self.image_clear.setMinimumSize(QtCore.QSize(30, 30))
        self.image_clear.setMaximumSize(QtCore.QSize(30, 30))
        self.image_list_main_grid.setContentsMargins(6, 6, 6, 6)

        self.image_list_setting_horizon.addWidget(self.image_add)
        self.image_list_setting_horizon.addWidget(self.image_clear)
        self.image_list_setting_horizon.addWidget(self.image_dir)
        self.image_list_setting_horizon.addWidget(self.image_setting)

        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        self.image_list_main_grid.addLayout(self.image_list_setting_horizon, 0, 0, 1, 1)
        self.image_list_main_grid.addWidget(self.image_list_table, 1, 0, 1, 1)


    def init_Function(self):
        """
            @Description: Image 리스트에 존재하는 기능들에 대한 connect 함수를 정의한다.
            @Author: MyoungHwan
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        """
        self.image_add.clicked.connect(self.create_imagelist)
        self.image_clear.clicked.connect(lambda : self.image_list_remove_function(mode=0))
        self.image_setting.clicked.connect(lambda ch=self.image_setting : self.image_main_to_sub(ch=ch))

    def create_imagelist(self):
        """
            @Description: Image 리스트 업데이트를 위한 생성 함수이다. 
            @Author: MyoungHwan
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
                2. Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
                3. Yugyeong Hong(2026.02.25): Refactor message box with util method and language support
        """
        fname = []
        file_dialog = QFileDialog()
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.findChild(QListView, 'listView').setSelectionMode(QAbstractItemView.ExtendedSelection)
        file_dialog.findChild(QTreeView, 'treeView').setSelectionMode(QAbstractItemView.ExtendedSelection)
        if file_dialog.exec_():
            fname = file_dialog.selectedFiles()
        # print(fname)
        if fname:
            tmp_exist_data_list = []
            tmp_wrong_data_list = []

            # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
            # 데이터 로딩 구조 개선
            self.image_dir.setText(os.path.split(fname[0])[0])
            for full_path in fname:
                #데이터 로딩을 위한 raw 파일 검증
                if os.path.isfile(full_path + '/data.raw') and os.path.isfile(full_path + '/data.hdr'):
                    pass
                else:
                    tmp_wrong_data_list.append(full_path)
                    continue
                if full_path not in self.data_list:#이미 포함되어있는 항목인지 체크
                    self.data_list.append(full_path)
                    self.create_imagelist_object(self.image_number, full_path)
                    self.image_number += 1
                else:
                    tmp_exist_data_list.append(full_path)
                    continue
            if len(tmp_wrong_data_list):
                messageBox(mode=MESSAGE_BOX_WARNING,
                           title=self.lang.get("main", "messageBox", "msgWarning"),
                           text=f'{self.lang.get("main", "image_main", "image_load_error_msg_wrong")}\n'+"".join([f"{l}\n" for l in tmp_wrong_data_list]),
                           buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
            if len(tmp_exist_data_list):
                messageBox(mode=MESSAGE_BOX_WARNING,
                           title=self.lang.get("main", "messageBox", "msgWarning"),
                           text=f'{self.lang.get("labeling", "image_main", "image_load_error_msg_already")}\n'+"".join([f"{l}\n" for l in tmp_exist_data_list]),
                           buttons={self.lang.get("main", "messageBox", "msgOk"): "accept"})
        
        # Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
        self.image_detail_form.update_data_list()


    def create_imagelist_object(self, image_number, full_path):
        """"
            @Description: create_imagelist() 선언 뒤 각 데이터들의 이름과 경로를 받아 데이터 리스트 UI를 생성하고 Core DB에 데이터를 저장한다.
            @Author: MyoungHwan
            @Parameters
                1.	path(str): 데이터가 존재하는 경로
                2.	folder_name(str): 데이터 이름
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        """
        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        path, file_name = os.path.split(full_path)
        cur_row = self.image_list_table.rowCount()
        self.image_list_table.insertRow(cur_row)

        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        list_select_button_dict = self.image_list_table_create_obj(image_number, obj_type="widget", obj_list=["button:"])
        image_list_select_icon = QtGui.QIcon()
        image_list_select_icon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_check_off.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        image_list_select_icon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_check_on.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        list_select_button = list_select_button_dict['button']
        list_select_button.setIcon(image_list_select_icon)
        list_select_button.setObjectName("list_select_button")
        list_select_button.setCheckable(True)
        self.image_list_table.setCellWidget(cur_row, 0, list_select_button_dict['widget'])
        list_select_button.clicked.connect(lambda ch=list_select_button, cnt=image_number: self.image_select(ch, cnt=cnt))

        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        # Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
        image_list_number_item = self.image_list_table_create_obj(image_number, obj_type="item", obj_list=f"{image_number}")
        self.image_list_table.setItem(cur_row, 1, image_list_number_item)

        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        image_list_name_lineedit_dict = self.image_list_table_create_obj(image_number, obj_type="widget", obj_list=[f"lineedit:{file_name}"])
        image_list_name_lineedit = image_list_name_lineedit_dict['lineedit']
        image_list_name_lineedit.setReadOnly(True)
        image_list_name_lineedit.setDragEnabled(True)
        self.image_list_table.setCellWidget(cur_row, 2, image_list_name_lineedit_dict['widget'])

        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        image_list_remove_button_dict = self.image_list_table_create_obj(image_number, obj_type="widget", obj_list=["button:"])
        image_list_remove_icon = QtGui.QIcon()
        image_list_remove_icon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_remove.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        image_list_remove_button = image_list_remove_button_dict['button']
        image_list_remove_button.setIcon(image_list_remove_icon)
        image_list_remove_button.setObjectName(f"image_list_remove_button_button_{image_number}")
        self.image_list_table.setCellWidget(cur_row, 3, image_list_remove_button_dict['widget'])
        image_list_remove_button.clicked.connect(lambda : self.image_list_remove_function(cnt=image_number, mode=1))

        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        # core db에 데이터 정보 저장
        # Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
        tmp_dict = {}
        tmp_dict['mode'] = 'create'
        tmp_dict['type'] = 'image'
        tmp_dict['image_number'] = image_number
        tmp_dict['image_name'] = file_name
        tmp_dict['image_path'] = path
        tmp_dict['label_name'] = 'label.npy'
        tmp_dict['raw_name'] = 'data.raw'
        self.image_to_core(tmp_dict)

        # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        # Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
        # image_obj_dict 내부 구조 개선
        self.image_obj_dict[image_number] ={
            'number':image_number,
            'name': file_name,
            'path': path,
            'full_path':full_path,
            'label_path' : f"{path}/{file_name}/label.npy",
            'raw_path' : f"{path}/{file_name}/data.raw",
            'obj_dict':{
                'select':list_select_button,
                'number':image_list_number_item,
                'name':image_list_name_lineedit,
                'remove':image_list_remove_button
            }
        }
    def image_select(self, ch, cnt):
        """
            @Description: 특정 이미지 선택 시 발동되는 함수이다. 이미지가 선택될 경우 Core DB, Label, display에 상태 및 리스트를 업데이트하기 위한 시그널을 보낸다.
            @Parameters
                1.	ch(bool)
                        - True : 이미지 선택 시
                        - False : 선택 해제 시
                2.  cnt(int): 선택한 이미지 번호
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        """
        if self.connect_sw:
            if self.image_control_dict['select_image_number'] == -1:
                """
                    1. Update date : 202305091453
                    아무것도 선택되지 않았을때
                """
                tmp_txt = self.image_obj_dict[cnt]["name"]
                self.core_obj_dict['status_image_status'][1].setText(tmp_txt)
                self.image_control_dict['select_image_number'] = cnt

                #labeing mode main 에 시그널 전달
                tmp_dict = {}
                tmp_dict['mode'] = 1
                tmp_dict['image_number'] = cnt
                self.image_to_labeling_mode_main(tmp_dict)
                
                # label list에 시그널 전달
                tmp_dict = {}
                tmp_dict['mode'] = 'load'
                tmp_dict['image_info'] = self.image_obj_dict[cnt]
                tmp_dict['image_number'] = cnt
                self.image_to_label(tmp_dict)

                # label sub에 시그널 전달
                tmp_dict = {}
                self.image_to_label_sub(tmp_dict)

                # Display 에 시그널 전달
                tmp_dict = {}
                tmp_dict['mode'] = 'show'
                self.image_to_display(tmp_dict)

                # send signal to graph group
                tmp_dict = {}
                tmp_dict['imageNumber'] = cnt
                self.imageToGraphGroupSignal.emit(tmp_dict)

                #graph 에 시그널 전달
                tmp_dict = {}
                tmp_dict['mode'] = 'image'
                tmp_dict['image_number'] = cnt
                self.image_to_graph(tmp_dict)

                #graph_sub 에 시그널 전달
                tmp_dict = {}
                tmp_dict['mode'] = 1
                tmp_dict['image_number'] = cnt
                self.image_to_graph_sub(tmp_dict)

                # display sub rgb change에 시그널 전달
                tmp_dict = {}
                tmp_dict['mode'] = 'load'
                tmp_dict['image_number'] = cnt
                self.image_to_display_sub_rgb_change(tmp_dict)

                
                # emit signal to semi auto labeling
                tmp_dict = {}   
                tmp_dict['from'] = 'image'
                self.imageToSemiAutoLabeling(tmp_dict)

            else:
                if self.image_control_dict['select_image_number'] != cnt:
                    """
                        1. Update date : 202305091453
                        선택 번호가 기존과 동일하지 않을때, 다른 번호로 선택
                    """
                    old_image_number = self.image_control_dict['select_image_number']
                    self.connect_sw = False
                    # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
                    # image_obj_dict 개선된 코드로 수정
                    if self.image_obj_dict[old_image_number]['obj_dict']['select'].isChecked():
                        self.image_obj_dict[old_image_number]['obj_dict']['select'].toggle()
                    self.connect_sw = True
                    tmp_txt = self.image_obj_dict[cnt]["name"]
                    self.core_obj_dict['status_image_status'][1].setText(tmp_txt)
                    self.core_obj_dict['status_labeling_status'][1].setText("")
                    self.core_obj_dict['status_pointer_status'][1].setText("")
                    self.image_control_dict['select_image_number'] = cnt

                    # label list에 시그널 전달
                    tmp_dict = {}
                    tmp_dict['mode'] = 'unchecked'
                    tmp_dict['image_number'] = cnt
                    tmp_dict['image_info'] = self.image_obj_dict[cnt]
                    self.image_to_label(tmp_dict)

                    # label sub에 시그널 전달
                    tmp_dict = {}
                    self.image_to_label_sub(tmp_dict)

                    # Display 에 시그널 전달, 로고로 전환
                    tmp_dict = {}
                    tmp_dict['mode'] = 'unchecked'
                    self.image_to_display(tmp_dict)
                    
                    # label list에 시그널 전달
                    tmp_dict = {}
                    tmp_dict['mode'] = 'load'
                    self.image_to_label(tmp_dict)

                    # Display 에 시그널 전달
                    tmp_dict = {}
                    tmp_dict['mode'] = 'show'
                    self.image_to_display(tmp_dict)

                    # send signal to graph group
                    tmp_dict = {}
                    tmp_dict['imageNumber'] = cnt
                    self.imageToGraphGroupSignal.emit(tmp_dict)

                    #graph 에 시그널 전달
                    tmp_dict = {}
                    tmp_dict['mode'] = 'image'
                    tmp_dict['image_number'] = cnt
                    self.image_to_graph(tmp_dict)

                    #graph_sub 에 시그널 전달
                    tmp_dict = {}
                    tmp_dict['mode'] = 1
                    tmp_dict['image_number'] = cnt
                    self.image_to_graph_sub(tmp_dict)

                    # display sub rgb change에 시그널 전달
                    tmp_dict = {}
                    tmp_dict['mode'] = 'load'
                    tmp_dict['image_number'] = cnt
                    self.image_to_display_sub_rgb_change(tmp_dict)

                    # emit signal to semi auto labeling
                    tmp_dict = {}
                    tmp_dict['from'] = 'image'
                    self.imageToSemiAutoLabeling(tmp_dict)


                elif self.image_control_dict['select_image_number'] == cnt:
                    """
                        1. Update date : 202305091453
                        선택한 이미지(cnt)와 현재 선택된 이미지가 같은 이미지일때 and 선택 값(ch)이 False 일때
                        해제
                    """
                    self.core_obj_dict['status_image_status'][1].setText("")
                    self.core_obj_dict['status_labeling_status'][1].setText("")
                    self.core_obj_dict['status_pointer_status'][1].setText("")
                    self.image_control_dict['select_image_number'] = -1

                    #labeing mode main 에 시그널 전달, 라벨 비활성
                    tmp_dict = {}
                    tmp_dict['mode'] = 0 
                    self.image_to_labeling_mode_main(tmp_dict)

                    # label list에 시그널 전달
                    tmp_dict = {}
                    tmp_dict['mode'] = 'unchecked'
                    tmp_dict['image_number'] = cnt
                    tmp_dict['image_info'] = self.image_obj_dict[cnt]
                    self.image_to_label(tmp_dict)

                    # label sub에 시그널 전달
                    tmp_dict = {}
                    self.image_to_label_sub(tmp_dict)

                    # display sub rgb change에 시그널 전달, 비활성
                    tmp_dict = {}
                    tmp_dict['mode'] = 'unload'
                    tmp_dict['image_number'] = cnt
                    self.image_to_display_sub_rgb_change(tmp_dict)

                    # Display 에 시그널 전달, 로고로 전환
                    tmp_dict = {}
                    tmp_dict['mode'] = 'unchecked'
                    self.image_to_display(tmp_dict)

                    #graph_sub 에 시그널 전달
                    tmp_dict = {}
                    tmp_dict['mode'] = 0
                    tmp_dict['image_number'] = cnt
                    self.image_to_graph_sub(tmp_dict)


    def image_list_remove_function(self, cnt=0, mode=0):
        """
            @Description: Image 리스트를 삭제하기 위한 함수 선언문이다. 파라미터 값에 따라 선택적으로 삭제가 가능하며 전체 삭제가 가능하다.
            @Author: MyoungHwan
            @Parameters
                -	cnt(int): 삭제하고자 하는 이미지 번호
                -	mode(int)
                    - 0: 전체 리스트 제거
                    - 1: 선택적으로 제거
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
                2. Modified by MyoungHwan(25.06.13): Fix scroll position moves irregularly when deleting a specific row in a CustomUI table.
        """
        if mode == 0:
            # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
            # table list update를 위한 코드 추가
            #table list 초기화
            self.image_list_table.clear()
            self.image_list_table.setRowCount(0)
            self.image_list_table.setting_headerlabels(labels=self.image_list_table_headerlabels)

            #모드가 0일때 이미지 전체 제거
            self.image_control_dict['select_image_number'] = -1
            self.clear_data_list(mode=0)

            #labeing mode main 에 시그널 전달, 라벨 비활성
            tmp_dict = {}
            tmp_dict['mode'] = 0
            self.image_to_labeling_mode_main(tmp_dict)

            # Display 에 시그널 전달, 로고로 전환
            tmp_dict = {}
            tmp_dict['mode'] = 'unchecked'
            self.image_to_label(tmp_dict)

            # label sub에 시그널 전달
            tmp_dict = {}
            self.image_to_label_sub(tmp_dict)
            
            # Display 에 시그널 전달, 로고로 전환
            tmp_dict = {}
            tmp_dict['mode'] = 'unchecked'
            self.image_to_display(tmp_dict)

            tmp_dict = {}
            tmp_dict['mode'] = 'delete'
            tmp_dict['type'] = 'image'
            tmp_dict['select_type'] = 'all'
            self.image_to_core(tmp_dict)


        elif mode == 1:
            # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
            #table list 중 특정 row 선택해서 삭제
            full_path = self.image_obj_dict[cnt]['full_path']
            cur_row = self.data_list.index(full_path)
            # Modified by MyoungHwan(25.06.13): Fix scroll position moves irregularly when deleting a specific row in a CustomUI table.
            self.image_list_table.removeRow_(cur_row)

            #모드가 1일때 이미지 선택후 1개 삭제
            self.clear_data_list(cnt=cnt, cnt_idx=cur_row, mode=1)

            #선택한 이미지를 지웠을 경우, 디스플레이에서 로고 그림 출력, 라벨 비활성
            if cnt == self.image_control_dict['select_image_number']:
                self.image_control_dict['select_image_number'] = -1
                #labeing mode main 에 시그널 전달, 라벨 비활성
                tmp_dict = {}
                tmp_dict['mode'] = 0
                self.image_to_labeling_mode_main(tmp_dict)
                
                # Display 에 시그널 전달, 로고로 전환
                tmp_dict = {}
                tmp_dict['mode'] = 'unchecked'
                self.image_to_label(tmp_dict)

                # label sub에 시그널 전달
                tmp_dict = {}
                self.image_to_label_sub(tmp_dict)

                # Display 에 시그널 전달, 로고로 전환
                tmp_dict = {}
                tmp_dict['mode'] = 'unchecked'
                self.image_to_display(tmp_dict)

            tmp_dict = {}
            tmp_dict['mode'] = 'delete'
            tmp_dict['type'] = 'image'
            tmp_dict['select_type'] = 'one'
            tmp_dict['image_number'] = cnt
            self.image_to_core(tmp_dict)

        # Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
        self.image_detail_form.update_data_list()

    def clear_data_list(self, cnt=0, cnt_idx=0, mode=0):
        """
            @Description: 호출한 데이터 리스트를 초기화 함수
            @Author: MyoungHwan
            @Parameters
                -	cnt(int): 삭제하고자 하는 이미지 번호
                -   cnt_idx(int): 삭제하고자 하는 이미지의 table row 번호
                -	mode(int)
                    - 0: 전체 리스트 제거
                    - 1: 선택적으로 제거
            @History
                1. Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
        """
        if mode == 0:
            # Improvemented by MyoungHwan(2024.11.07): Image Main UI 코드 개선 (미사용 object 제거 및 수정)
            self.image_number = 1
            self.data_list = []
            tmp_list = list(self.image_obj_dict.keys())
            for key in tmp_list:
                del self.image_obj_dict[key]

        elif mode == 1:
            del self.data_list[cnt_idx]
            del self.image_obj_dict[cnt]
    
    def image_to_core(self, input):
        """Image에서 core로 시그널을 보내기 위한 함수 선언문이다. Core DB에 대한 값을 업데이트하거나 조정하기 위한 함수로 쓰인다.
                Parameters
                1.	input(dict): Core DB 업데이트를 위한 dictionary

        """
        self.image_to_core_signal.emit(input)

    def image_to_label(self, input):
        """image에서 label로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 label에 최종적으로 전달된다. label 리스트를 업데이트 하기위한 용도로 사용
                Parameters
                1.	input(dict): label 리스트 업데이트를 위한 dictionary

        """
        self.image_to_label_signal.emit(input)
    
    def image_to_label_sub(self, input):
        """image에서 label sub로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 label에 최종적으로 전달된다. label 리스트를 업데이트 하기위한 용도로 사용
                Parameters
                1.	input(dict): label 리스트 업데이트를 위한 dictionary

        """
        self.image_to_label_sub_signal.emit(input)

    def image_to_display(self, input):
        """image에서 display로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 display에 최종적으로 전달된다. 선택한 이미지로 display를 업데이트 하기위해 사용
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary

        """
        self.image_to_display_signal.emit(input)

    def image_to_display_sub_rgb_change(self, input):
        self.image_to_display_sub_rgb_change_signal.emit(input)

    def image_to_labeling_mode_main(self, input):
        self.image_to_labeling_mode_main_signal.emit(input)

    def image_to_graph(self, input):
        self.image_to_graph_signal.emit(input)

    def image_to_graph_sub(self, input):
        self.image_to_graph_sub_signal.emit(input)

    def image_main_to_sub(self, ch):
        """
            @Description: image에서 image sub detail을 요청하기 위한 함수 선언문이다. detail 버튼 활성화 시 Image sub detail form을 열어 기존에 존재하는 RGB, Label, raw 파일을 변경할 수 있다.
            @Author: MyoungHwan
            @Parameters
                1.	ch(bool)
                        - True : detail 버튼 활성화 시
                        - False : 비활성화 시
            @History
                1. Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
        """
        if ch:
            self.image_detail_form.show()
        else :
            self.image_detail_form.close()

    def imageToSemiAutoLabeling(self, input):
        self.imageToSemiAutoLabelingSignal.emit(input)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Image_Form()
    sys.exit(app.exec_())
