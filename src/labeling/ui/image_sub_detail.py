"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import pyqtSlot, Qt

from labeling.stylesheet.stylesheet_image_sub_detail import stylesheet
from constants.constants import QT_MAX_SIZE
from utils.custom_ui import custom_qtablewidget

class Image_detail_Form(QtWidgets.QWidget):
    """
        @Description : Image detail form과 관련된 모든 기능을 처리하기 위한 클래스
        @Author : MyougnHwan
        @History
            1. Improvemented by MyoungHwan (2024.12.13) : 초기 변수 선언을 위한 함수 선언
    """
    def __init__(self, Sync, Image_Obj, lang):
        super().__init__()
        self.image_main_obj = Image_Obj
        self.init(Sync=Sync, lang=lang)
        # Improvemented by MyoungHwan (2024.12.13) : 초기 변수 선언을 위한 함수 선언
        self.init_variable()
        self.init_Ui_image_sub_detail(self)
        self.setup_Ui_image_sub_detail(self)
        self.init_Function()
        
        if __name__ == "__main__":
            self.show()


    def init(self, Sync=None, lang=None):
        """
            @Description : Image detail ui 초기 상위 변수 선언함수
            @Author : MyougnHwan
            @Parameters
                1.Sync(Qobject) : PyQt slot/signal을 사용하기 위해 정의한 클래스
        """
        self.lang = lang
        self.Sync = Sync
        self.image_sub_to_core_signal = self.Sync.image_sub_to_core_signal
        self.image_sub_to_label_signal = self.Sync.image_sub_to_label_signal
        self.image_sub_to_display_signal = self.Sync.image_sub_to_display_signal
        self.image_sub_to_labeling_mode_main_signal = self.Sync.image_sub_to_labeling_mode_main_signal

        self.core_to_image_sub_signal = self.Sync.core_to_image_sub_signal
        self.core_to_image_sub_signal.connect(self.recv_core_to_image_sub)


    def init_variable(self):
        """
            @Description : Image detail ui 초기 변수 선언함수, 해당 클래스에서 사용할 변수 정의
            @Author : MyougnHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13) : 선택된 Image 데이터 불러오는 변수 추가
        """
        # Improvemented by MyoungHwan (2024.12.13): 선택된 Image 데이터 불러오는 변수 추가
        self.image_obj_dict = self.Sync.image_obj_dict
        self.image_control_dict = self.Sync.image_control_dict
        self.select_row_number = -1


    def init_Ui_image_sub_detail(self, Mainwindow):
        """
            @Description : Image detail UI 생성을 위한 초기 선언문이다.
            @Author : MyoungHwan
            @History
                1. Modified by MyoungHwan(20240507) : UI 구조 개선
                2. Improvemented by MyoungHwan (2024.12.13) : Image 데이터 리스트화를 위한 UI 변경
        """
        Mainwindow.setObjectName("MainWindow")
        Mainwindow.setFixedSize(600, 400)
        Mainwindow.setStyleSheet(stylesheet)
        # Ensure the settings window always stays on top for improved accessibility and user convenience.
        Mainwindow.setWindowModality(QtCore.Qt.ApplicationModal)
        Mainwindow.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)

        self.data_top_vertical = QtWidgets.QVBoxLayout(self)
        self.data_top_vertical.setObjectName("data_top_vertical")

        self.data_list_group = QtWidgets.QGroupBox()
        self.data_list_group.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.data_list_group.setObjectName("data_list_group")
        
        self.data_list_vertical = QtWidgets.QVBoxLayout()
        self.data_list_vertical.setContentsMargins(9, -1, -1, -1)
        self.data_list_vertical.setObjectName("data_list_vertical")
        
        self.data_list_detail_group = QtWidgets.QGroupBox()
        self.data_list_detail_group.setObjectName("data_list_detail_group")
        
        self.data_list_detail_main_vertical = QtWidgets.QVBoxLayout()
        self.data_list_detail_main_vertical.setObjectName("data_list_detail_main_vertical")
        
        self.data_list_detail_sub_vertical = QtWidgets.QVBoxLayout()
        self.data_list_detail_sub_vertical.setObjectName("data_list_detail_sub_vertical")
        
        self.data_list_detail_label_horizon = QtWidgets.QHBoxLayout()
        self.data_list_detail_label_horizon.setObjectName("data_list_detail_label_horizon")
        
        self.data_list_detail_label_label = QtWidgets.QLabel()
        self.data_list_detail_label_label.setMaximumSize(QtCore.QSize(100, QT_MAX_SIZE))
        self.data_list_detail_label_label.setAlignment(QtCore.Qt.AlignCenter)
        self.data_list_detail_label_label.setObjectName("data_list_detail_label_label")
        
        self.data_list_detail_label_line = QtWidgets.QLineEdit()
        self.data_list_detail_label_line.setMaximumSize(QtCore.QSize(400, QT_MAX_SIZE))
        self.data_list_detail_label_line.setReadOnly(True)
        self.data_list_detail_label_line.setObjectName("data_list_detail_label_line")

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("ico/labeling/imagebox/image_load.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.data_list_detail_label_search = QtWidgets.QPushButton()
        self.data_list_detail_label_search.setMaximumSize(QtCore.QSize(30, QT_MAX_SIZE))
        self.data_list_detail_label_search.setObjectName("data_list_detail_label_search")
        self.data_list_detail_label_search.setIcon(icon)

        # Improvemented by MyoungHwan (2024.12.13): Image 데이터 리스트화를 위한 UI 변경
        self.data_list_main_custom_tablewidget = custom_qtablewidget(obj_name="data_list_main_custom_tablewidget", col=2, row=3)
        self.data_list_main_custom_tablewidget_setting_header_labels = ["Num","Name"]
        self.data_list_main_custom_tablewidget.setting_headerlabels(labels=self.data_list_main_custom_tablewidget_setting_header_labels)
        self.data_list_main_custom_tablewidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.data_list_main_custom_tablewidget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.data_list_main_custom_tablewidget.setEnabled(False)
        self.create_obj = self.data_list_main_custom_tablewidget.create_obj

        QtCore.QMetaObject.connectSlotsByName(Mainwindow)


    def setup_Ui_image_sub_detail(self, Mainwindow):
        """
            @Description : 초기화된 Image detail ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
            @Author : MyougnHwan
            @History
                1. Modified by MyoungHwan(20240507) : UI 구조 개선
                2. Improvemented by MyoungHwan (2024.12.13) : UI 구조 및 언어팩 수정
        """
        _translate = QtCore.QCoreApplication.translate
        Mainwindow.setWindowTitle(_translate("Mainwindow", "Data detail setting Menu"))
        self.lang.set("labeling", "image_sub_detail", "data_list", self.data_list_group)
        self.lang.set("labeling", "image_sub_detail", "data_list_detail", self.data_list_detail_group)
        self.lang.set("labeling", "image_sub_detail", "data_list_detail_label_label", self.data_list_detail_label_label)
        
        # Image list 
        self.data_list_vertical.addWidget(self.data_list_main_custom_tablewidget)

        # Image list group
        self.data_list_group.setLayout(self.data_list_vertical)

        # Image list detail 
        self.data_list_detail_label_horizon.addWidget(self.data_list_detail_label_label)
        self.data_list_detail_label_horizon.addWidget(self.data_list_detail_label_line)
        self.data_list_detail_label_horizon.addWidget(self.data_list_detail_label_search)
        self.data_list_detail_sub_vertical.addLayout(self.data_list_detail_label_horizon)
        self.data_list_detail_main_vertical.addLayout(self.data_list_detail_sub_vertical)
        
        # Image list detail group
        self.data_list_detail_group.setLayout(self.data_list_detail_main_vertical)

        self.data_top_vertical.addWidget(self.data_list_group)
        self.data_top_vertical.addWidget(self.data_list_detail_group)

        self.update_ui_status(mode = 0)


    @pyqtSlot(dict)
    def recv_core_to_image_sub(self, output):
        """
            @Description : Image detail 리스트를 갱신하기 위해 signal을 통해 실시간으로 정보를 업데이트하기 위한 함수이다.
            @Author : MyoungHwan
            @Parameters
                1.output(dict): 요청한 데이터의 정보가 담긴 dictionary
            @History
                1. Improvemented by MyoungHwan (2024.12.13): Label 갱신을 위한 코드 수정
        """
        mode = output['mode']
        if mode == 1:
            if output['status']:
                image_number = int(self.data_list_main_custom_tablewidget.item(self.select_row_number, 0).text())
                self.image_obj_dict[image_number]['label_path'] = output['path']
                self.update_label_path(idx=self.select_row_number)
                if image_number == self.image_control_dict['select_image_number']:
                    tmp_dict = {}
                    tmp_dict['mode'] = 'load'
                    self.image_sub_to_label(tmp_dict)
                    tmp_dict = {}
                    tmp_dict['mode'] = 'show'
                    self.image_sub_to_display(tmp_dict)
            

    def init_Function(self):
        """
            @Description : Image detail ui에 존재하는 기능들에 대한 connect 함수를 정의한다.
            @Author : MyoungHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13): 일부 사용하지 않는 기능 제거
        """
        self.data_list_main_custom_tablewidget.cellClicked.connect(lambda value=self.data_list_main_custom_tablewidget: self.select_cell(value))
        self.data_list_detail_label_search.clicked.connect(self.update_data)


    def select_cell(self, value):
        """
            @Description : tablewidget 행 선택시 발생하는 이벤트 함수
            @Author : MyoungHwan (2024.12.13)
            @Parameters
                1.	value(int)
                    - 정수값: 행 번호
        """
        self.select_row_number = value
        self.update_label_path(idx=self.select_row_number)
    

    def update_ui_status(self, mode=None):
        """
            @Description : 데이터 리스트 업데이트에 따른 UI 제어함수
            @Author : MyoungHwan
            @Parameters
                1.	mode(int)
                    - 0 : UI 비활성화
                    - 1 : UI 활성화
            @History
                1. Improvemented by MyoungHwan (2024.12.13): UI 활성화 코드 수정
        """
        if mode == 1:
            self.data_list_detail_label_line.setEnabled(True)
            self.data_list_detail_label_search.setEnabled(True)
            self.data_list_main_custom_tablewidget.setEnabled(True)
        else:
            self.data_list_detail_label_line.setEnabled(False)
            self.data_list_detail_label_search.setEnabled(False)
            self.data_list_main_custom_tablewidget.setEnabled(False)


    def update_data(self):
        """
            @Description : 선택된 데이터의 파일들을 업데이트하는 함수를 정의한다.
            @Author : MyoungHwan
            @History
                1. Modified by MyoungHwan(20240529) : QFileDialog 통해 경로 불러올 경우에 대한 예외처리 수정, length 기준으로 크기가 0보다 큰 경우에만 처리
                2. Improvemented by MyoungHwan (2024.12.13): 파일경로 DB에 전달하기위한 코드 수정    
        """
        image_number = int(self.data_list_main_custom_tablewidget.item(self.select_row_number, 0).text())
        path = self.image_obj_dict[image_number]['label_path']
        fname = QFileDialog.getOpenFileName(self, 'Load Label File', path, filter='*.npy')

        # Modified by MyoungHwan(20240529) : QFileDialog 통해 경로 불러올 경우에 대한 예외처리 수정, length 기준으로 크기가 0보다 큰 경우에만 처리
        # Improvemented by MyoungHwan (2024.12.13): 파일경로 DB에 전달하기위한 코드 수정
        if len(fname[0]) > 0:
            tmp_dict = {}
            tmp_dict['mode'] = 'modify'
            tmp_dict['type'] = 'image'
            tmp_dict['type_detail'] = 'detail'
            tmp_dict['type_detail_2'] = 1
            tmp_dict['select_image_number'] = image_number
            tmp_dict['file_path'] = fname[0]
            self.image_sub_to_core(tmp_dict)


    def update_data_list(self):
        """
            @Description : 데이터 리스트를 업데이트하는 함수를 정의한다.
            @Author : MyoungHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13): image 데이터 리스트 업데이트 코드 수정
        """
        self.clear_data_list()
        self.data_list_main_custom_tablewidget.setRowCount(len(self.image_obj_dict.keys()))

        tmp_data_list_info = {}
        for _, (tmp_key, tmp_value) in enumerate(self.image_obj_dict.items()):
            number = tmp_value['number']
            name = tmp_value['name']
            tmp_data_list_info[tmp_key] = {
                "idx":number,
                "obj_idx":self.create_obj(number, obj_type="item", obj_list=number),
                "obj_name":self.create_obj(number, obj_type="item", obj_list=name),
            }

        for key, value in enumerate(tmp_data_list_info.values()):
            self.data_list_main_custom_tablewidget.setItem(key, 0, value["obj_idx"])
            self.data_list_main_custom_tablewidget.setItem(key, 1, value["obj_name"])

        self.update_ui_status(mode=1)
        

    def update_label_path(self, idx):
        """
            @Description : 선택된 데이터의 파일 경로들을 업데이트하는 함수를 정의한다.
            @Author : MyoungHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13): Label 파일경로 업데이트 코드 수정
        """
        image_number = int(self.data_list_main_custom_tablewidget.item(idx, 0).text())
        label_path = self.image_obj_dict[image_number]['label_path']
        self.data_list_detail_label_line.setText(label_path)


    def clear_data_list(self):
        """
            @Description : 선택된 데이터의 파일 경로들을 초기화하는 함수를 정의한다.
            @Author : MyoungHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13): UI 초기화 코드 수정
        """
        self.data_list_detail_label_line.setText("")
        self.data_list_main_custom_tablewidget.clear()
        self.data_list_main_custom_tablewidget.setting_headerlabels(labels=self.data_list_main_custom_tablewidget_setting_header_labels)
        self.update_ui_status(mode=0)


    def closeEvent(self, _):
        """
            @Description : image ui에서 setting 기능이 활성화 되어 있는 경우 비활성화로 전환
            @Author : MyoungHwan
        """
        if self.image_main_obj.image_setting.isChecked():
            self.image_main_obj.image_setting.toggle()
    

    def image_sub_to_core(self, input):
        """
            @Description : Image detail에서에서 core로 시그널을 보내기 위한 함수 선언문이다. Core DB에 대한 값을 업데이트하거나 조정하기 위한 함수로 쓰인다.
            @Author : MyoungHwan
            @Parameters
                    1.input(dict): Core DB 업데이트를 위한 dictionary
        """
        self.image_sub_to_core_signal.emit(input)
    

    def image_sub_to_label(self, input):
        """
            @Description : image detail에서에서 label로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 label에 최종적으로 전달된다.
            @Author : MyoungHwan
            @Parameters
                1.input(dict): label 리스트 업데이트를 위한 dictionary
        """
        self.image_sub_to_label_signal.emit(input)
    

    def image_sub_to_display(self, input):
        """
            @Description : image detail에서 display로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 display에 최종적으로 전달된다.
            @Author : MyoungHwan
            @Parameters
                1.input(dict): Dispaly 업데이트를 위한 dictionary
        """
        self.image_sub_to_display_signal.emit(input)
    

    def image_sub_to_labeling_mode_main(self, input):
        self.image_sub_to_labeling_mode_main_signal.emit(input)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Image_detail_Form()
    # ui.setupUi(Form)
    # Form.show()
    sys.exit(app.exec_())
