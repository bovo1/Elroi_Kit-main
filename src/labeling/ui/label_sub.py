"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

import os
import numpy as np
import json
import time
import copy

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from utils.advanced import Kmeans, autoCommonLabel
from utils.worker import AutoLabel_Worker, Threading_Worker

import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.lines as mlines


"""
    Description: Opacity UI 사용을 위한 호출
    Implemented by MyoungHwan (2024.09.06)
"""
if __name__ == "__main__" :
    from label_sub_ess_option import label_sub_ess_option_Form
else:
    from .label_sub_ess_option import label_sub_ess_option_Form


class label_sub_Form(QtWidgets.QDialog):
    def __init__(self, Sync=None, lang=None, parent=None) -> None:
        super().__init__()

        self.init(Sync=Sync, lang=lang, parent=parent)
        self.init_ui(self)
        self.setup_ui()
        self.init_function()
        self.init_variable()

        if __name__ == "__main__":
            self.show()
    
    def init(self, Sync=None, lang=None, parent=None):
        """
            @description: 외부 변수 호출을 위한 초기 함수
            @author: MyoungHwan
            @history
                1. Implemented by MyoungHwan (2024.09.06)
                2. Added by Hyunsu Kim (2025.11.21) : Add the Worker for the Common Abnormal Auto Labeling
                3. Removed by GaEun Hwang (2026.03.12) : Remove the Worker for Relabeling Mode
        """
        self.lang = lang
        self.Sync = Sync
        self.parent = parent
        
        #signal
        self.core_to_label_sub_signal = self.Sync.core_to_label_sub_signal
        self.core_to_label_sub_signal.connect(self.recv_from_core)
        """
            Description: label_sub에서 display로 값을 전달하기 위한 signal 추가
            Implemented by MyoungHwan (2024.09.06)
        """
        self.label_sub_to_display_signal = self.Sync.label_sub_to_display_signal

        # obj_dict
        self.label_obj_dict = self.Sync.label_obj_dict
        self.image_obj_dict = self.Sync.image_obj_dict
        self.image_control_dict = self.Sync.image_control_dict
        self.Core_DB_Labeling = self.Sync.Core_DB_Labeling

        self.label_sub_ess_option_Form = label_sub_ess_option_Form(Sync=self.Sync, lang=self.lang, parent=self)

        self.worker_2 = AutoLabel_Worker()
        self.worker_2.Func = autoCommonLabel
        self.worker_2.output.connect(self.recv_from_threading)

        self.worker_3 = Threading_Worker()
        self.worker_3.output.connect(self.recv_from_threading)


    def init_variable(self):
        """
        """
        self.select_image_number = -1
        self.select_image_name = ""
        self.topk = 5
        self.tmp_fname = None
        self.worker_list = []
    
    @pyqtSlot(dict)
    def recv_from_threading(self, output):
        """
            Description: Recv threading process result
            Implement by MyoungHwan

            History
                1. Added by Hyunsu Kim(2025.11.21) : Add the process for the Common Abnormal Auto Labeling
                2. Removed by GaEun Hwang(2026.03.12) : Remove the process for Relabeling Mode
        """
        id_ = output['id']
        mode = output['mode']
        if mode == 2: # auto common labeling
            path = output['path'] + '/auto_common_label.npy'
            result = output['result']
            self.label_sub_adv_autoCommonLabel_mode_btn.setEnabled(True)
            np.save(path, result)
            print("Common Abnormal Auto Labeling is clear")
        elif mode == 3: # ESS
            self.worker_list.remove(id_)
            self.label_sub_anly_ess_btn.setEnabled(True)
            print("ESS is clear")

    @pyqtSlot(dict)
    def recv_from_core(self, output):
        """
            @description : recv output when image select
            @author : MyoungHwan
            @history
                1. Modified by MyoungHwan(20240529)
        """
        self.select_image_number = self.image_control_dict['select_image_number']
        """
            description: 데이터 선택 및 해제시 조건 추가 및 변수 초기화
            modified by MyoungHwan(20240529)
        """
        if self.select_image_number > -1:
            self.select_image_name = self.image_obj_dict[self.select_image_number]['name']
        else:
            self.select_image_name = ""

    def init_ui(self, Form):
        """
            @description: 초기 UI 선언부분
            @author: MyoungHwan
            @history
                1. Implemented by MyoungHwan (2024.09.06)
                2. Added by Hyunsu Kim (2025.11.21) : Add the UI for the Common Abnormal Auto Labeling
        """
        Form.setObjectName("label_sub_form")
        Form.setFixedSize(320, 160)
        self.lang.set("labeling", "labelSub", "labelSubTitle", Form)
        # Ensure the settings window always stays on top for improved accessibility and user convenience.
        Form.setWindowModality(QtCore.Qt.ApplicationModal)
        Form.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint)
        
        self.label_sub_main_vertical = QtWidgets.QVBoxLayout(Form)
        self.label_sub_main_vertical.setObjectName("label_sub_main_vertical")

        self.label_sub_adv_group = QtWidgets.QGroupBox()
        self.label_sub_adv_group.setObjectName("label_sub_adv_group")
        self.lang.set("labeling", "labelSub", "labelSubGroupBoxTitle", self.label_sub_adv_group)
        
        self.label_sub_adv_vertical = QtWidgets.QVBoxLayout(self.label_sub_adv_group)
        self.label_sub_adv_vertical.setObjectName("label_sub_adv_vertical")

        self.label_sub_adv_horizon = QtWidgets.QHBoxLayout()
        self.label_sub_adv_horizon.setObjectName("label_sub_adv_horizon")

        self.label_sub_adv_relabel_horizon = QtWidgets.QHBoxLayout()
        self.label_sub_adv_relabel_horizon.setObjectName("label_sub_adv_relabel_horizon")
        self.label_sub_adv_relabel_mode_label = QtWidgets.QLabel()
        self.label_sub_adv_relabel_mode_label.setObjectName("label_sub_adv_relabel_mode_label")
        self.lang.set("labeling", "labelSub", "labelSubRelabeling", self.label_sub_adv_relabel_mode_label)
        self.label_sub_adv_relabel_mode_btn = QtWidgets.QPushButton()
        self.label_sub_adv_relabel_mode_btn.setObjectName("label_sub_adv_relabel_mode_btn")
        self.lang.set("labeling", "labelSub", "labelSubApply", self.label_sub_adv_relabel_mode_btn)

        self.label_sub_adv_autoCommonLabel_horizon = QtWidgets.QHBoxLayout()
        self.label_sub_adv_autoCommonLabel_horizon.setObjectName("label_sub_adv_autoCommonLabel_horizon")
        self.label_sub_adv_autoCommonLabel_mode_label = QtWidgets.QLabel()
        self.label_sub_adv_autoCommonLabel_mode_label.setObjectName("label_sub_adv_autoCommonLabel_mode_label")
        self.lang.set("labeling", "labelSub", "labelSubCommonAbnormal",  self.label_sub_adv_autoCommonLabel_mode_label)
        self.label_sub_adv_autoCommonLabel_mode_btn = QtWidgets.QPushButton()
        self.label_sub_adv_autoCommonLabel_mode_btn.setObjectName("label_sub_adv_autoCommonLabel_mode_btn")
        self.lang.set("labeling", "labelSub", "labelSubApply", self.label_sub_adv_autoCommonLabel_mode_btn)


        self.label_sub_anly_group = QtWidgets.QGroupBox()
        self.label_sub_anly_group.setObjectName("label_sub_anly_group")
        self.lang.set("labeling", "labelSub", "labelSubAnalysis", self.label_sub_anly_group)

        self.label_sub_anly_vertical = QtWidgets.QVBoxLayout(self.label_sub_anly_group)
        self.label_sub_anly_vertical.setObjectName("label_sub_anly_vertical")

        self.label_sub_anly_horizon = QtWidgets.QHBoxLayout()
        self.label_sub_anly_horizon.setObjectName("label_sub_anly_horizon")

        self.label_sub_anly_ess_label = QtWidgets.QLabel()
        self.label_sub_anly_ess_label.setObjectName("label_sub_anly_ess_label")
        self.lang.set("labeling", "labelSub", "labelSubESS", self.label_sub_anly_ess_label)

        self.label_sub_anly_ess_option_btn = QtWidgets.QPushButton()
        self.label_sub_anly_ess_option_btn.setObjectName("label_sub_anly_ess_option_btn")
        self.lang.set("labeling", "labelSub", "labelSubOption", self.label_sub_anly_ess_option_btn)
        self.label_sub_anly_ess_btn = QtWidgets.QPushButton()
        self.label_sub_anly_ess_btn.setObjectName("label_sub_anly_ess_btn")
        self.lang.set("labeling", "labelSub", "labelSubApply", self.label_sub_anly_ess_btn)
        QtCore.QMetaObject.connectSlotsByName(Form)


    def setup_ui(self):
        """
            @description: 초기 UI 선언에 대한 설정 부분
            @author : MyoungHwan
            @history
                1. Implemented by MyoungHwan (2024.09.06)
                2. Added by Hyunsu Kim (2025.11.21) : Add the UI for the Common Abnormal Auto Labeling
        """
        self.label_sub_adv_autoCommonLabel_horizon.addWidget(self.label_sub_adv_autoCommonLabel_mode_label)
        self.label_sub_adv_autoCommonLabel_horizon.addWidget(self.label_sub_adv_autoCommonLabel_mode_btn)
        self.label_sub_anly_horizon.addWidget(self.label_sub_anly_ess_label)
        self.label_sub_anly_horizon.addWidget(self.label_sub_anly_ess_option_btn)
        self.label_sub_anly_horizon.addWidget(self.label_sub_anly_ess_btn)

        self.label_sub_adv_vertical.addLayout(self.label_sub_adv_autoCommonLabel_horizon)
        self.label_sub_adv_vertical.addStretch(1)

        self.label_sub_anly_vertical.addLayout(self.label_sub_anly_horizon)
        self.label_sub_adv_vertical.addStretch(1)

        """
            Description: adv setting 그룹 추가
            Implemented by MyoungHwan (2024.09.06)
        """
        self.label_sub_main_vertical.addWidget(self.label_sub_adv_group)
        self.label_sub_main_vertical.addWidget(self.label_sub_anly_group)


    
    def init_function(self):
        """
            @description: UI 내부 버튼 사용에 대한 signal 정의 부분
            @author : MyoungHwan
            @history
                1. Implemented by MyoungHwan (2024.09.06)
                2. Added by Hyunsu Kim (2025.11.21) : Add the function for the Common Abnormal Auto Labeling
                3. Removed by GaEun Hwang (2026.03.12) : Remove the connect code about Relabeling Mode
        """
        self.label_sub_adv_autoCommonLabel_mode_btn.clicked.connect(lambda ch = self.label_sub_adv_autoCommonLabel_mode_btn: self.label_sub_mode_adv(ch=ch, mode=2))
        self.label_sub_anly_ess_btn.clicked.connect(lambda ch = self.label_sub_anly_ess_btn: self.label_sub_mode_anly(ch=ch, mode=0))
        self.label_sub_anly_ess_option_btn.clicked.connect(lambda ch = self.label_sub_anly_ess_option_btn: self.label_sub_mode_anly(ch=ch, mode=1))

    def reset_(self):
        self.label_sub_adv_group.setEnabled(True)


    def label_sub_mode_adv(self, ch, mode):
        """
            @description: function using worker for advanced mode
            @history:
                1. Removed by GaEun Hwang (2026.03.12) : Remove the code about Relabeling Mode(was mode=1)
        """
        if mode == 2: # Auto Common Abnormal Labeling mode
            image_number = self.image_control_dict['select_image_number']
            raw_data = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw']
            label = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label']
            path = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_path'] + '/' + self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_name']
            self.worker_2.datapack = [raw_data, label, path]
            self.worker_2.output_dict = {
                'mode': 2
            }
            self.worker_2.start()
            self.label_sub_adv_autoCommonLabel_mode_btn.setEnabled(False)
    def label_sub_mode_anly(self, ch, mode):
        if mode == 0: # ESS Mode
            tmp_filedialog = QtWidgets.QFileDialog()
            tmp_filedialog.setOptions(QtWidgets.QFileDialog.ShowDirsOnly)
            fname = tmp_filedialog.getExistingDirectory(parent=self, caption=self.lang.get("labeling", "labelSubESSOption", "labelESSApplyTitle"), directory="")
            if fname:
                self.tmp_fname = fname
                self.worker_3.output_dict = {
                    'mode': 3
                }
                self.worker_3.staging(self.Extract_sparse_spectrum_mode)
                self.worker_list.append(self.worker_3.cur_id)
                self.worker_3.start()
                self.label_sub_anly_ess_btn.setEnabled(False)

        elif mode == 1: # ESS Option Mode
            self.label_sub_anly_ess_option_btn.setEnabled(False)
            self.label_sub_ess_option_Form.show()


    def Extract_sparse_spectrum_mode(self) -> None:
        """
            @description : ESS(Extract_sparse_spectrum_mode) function
            @author : MyoungHwan
        """
        if self.tmp_fname is not None:
            """
                description
                modified by Myounghwan(20240531) : cetner spectrum 저장하는 딕셔너리 변수 초기화
            """
            tmp_center_dict = {}
            ctime_ = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(time.time()))
            log_dict = {
                "time": ctime_,
                "path": self.Core_DB_Labeling['image_list'][self.select_image_number]['image_info']['image_path'],
                "data_name": self.Core_DB_Labeling['image_list'][self.select_image_number]['image_info']['image_name'],
                'data_info':{},
                "label_info": {}
            }
            self.tmp_fname +=  "/result"
            os.makedirs(self.tmp_fname , exist_ok=True)
            os.makedirs(self.tmp_fname + '/graph' , exist_ok=True)
            os.makedirs(self.tmp_fname + '/data', exist_ok=True)
            graph_full_path = self.tmp_fname + '/graph'
            data_full_path = self.tmp_fname + '/data'
            font_dirs = ['font/']
            font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
            for font_file in font_files:
                font_manager.fontManager.addfont(font_file)
            plt.rcParams['font.family'] = 'NanumGothic'
            
            tmp_label = self.Core_DB_Labeling['image_list'][self.select_image_number]['image_info']['image_label']
            w,h = tmp_label.shape
            log_dict['data_info'] = {
                'width(total frame)' : w,
                'height(spatial per frame)' : h,
                'total samples' : w*h
            }
            for label_number in self.label_obj_dict.keys():
                log_dict['label_info'][label_number] = {
                    'name':self.label_obj_dict[label_number]['name'],
                    'color':self.label_obj_dict[label_number]['color'],
                    'center_num':self.label_obj_dict[label_number]['center_num'],
                    'samples':0,
                }
                if label_number == 0:
                    continue
                indice = np.where(tmp_label==label_number)
                if len(indice[0]):
                    """
                        description
                        modified by Myounghwan(20240531) : cetner spectrum 저장하는 딕셔너리 변수명 변경
                    """
                    tmp_center_dict[label_number]={
                        "center":[],
                        "name":self.label_obj_dict[label_number]['name'],
                        "color":self.label_obj_dict[label_number]['color']
                    }
                    tmp_raw = self.Core_DB_Labeling['image_list'][self.select_image_number]['image_info']['image_raw'][indice]
                    """
                        description
                        modified by Myounghwan(20240531) : cetner spectrum 저장하는 딕셔너리 변수명 변경
                    """
                    np.save(data_full_path + f"/{self.select_image_name}_{tmp_center_dict[label_number]['name']}_data.npy", tmp_raw)
                    tmp_kmeans = Kmeans()
                    tmp_center_num = self.label_obj_dict[label_number]['center_num']
                    samples = tmp_raw.shape[0]
                    if tmp_center_num > samples:
                        tmp_center_num = samples
                    if self.topk < samples:
                        self.topk = samples
                    
                    log_dict['label_info'][label_number]['center_num'] = tmp_center_num
                    log_dict['label_info'][label_number]['samples'] = samples
                    """
                        description
                        modified by Myounghwan(20240531) : cetner spectrum 저장하는 딕셔너리 변수명 변경
                    """
                    tmp_center_dict[label_number]['center'] = tmp_kmeans.extract_sparse(tmp_raw, c_num=tmp_center_num)
                    tmp_center_dict[label_number]['centernearspectrum'] = []
                    tmp_center_dict[label_number]['centernearspectrum_topk'] = []
                    """
                        description
                        modified by Myounghwan(20240531) : cetner spectrum 저장하는 딕셔너리 변수명 변경
                    """
                    for center in tmp_center_dict[label_number]['center']:
                        dist = np.linalg.norm(tmp_raw-center, axis=1)
                        # topk_list = np.argpartition(dist, -self.topk)
                        index = np.argmin(dist)
                        tmp_center_dict[label_number]['centernearspectrum'].append(tmp_raw[index])
                    tmp_center_dict[label_number]['centernearspectrum'] = np.array(tmp_center_dict[label_number]['centernearspectrum'])
            """
                Description: Optimize code 
                Modified by MyoungHwan (20240216)
            """
            include_label_list = [ label_number for label_number in self.label_obj_dict.keys() \
                                  if self.label_obj_dict[label_number]['include_spectrum'] \
                                  ]
            self.merge_center_dict = {}
            for label_number in include_label_list:
                """
                    description
                    modified by Myounghwan(20240531) : cetner spectrum 저장하는 딕셔너리 변수명 변경
                """
                self.merge_center_dict[label_number] = copy.deepcopy(tmp_center_dict[label_number])
            for label_number in tmp_center_dict.keys():
                self.temp_merge_center_dict = copy.deepcopy(self.merge_center_dict)
                if label_number == 0 and label_number in self.temp_merge_center_dict.keys():
                    continue
                """
                    description
                    modified by Myounghwan(20240531) : cetner spectrum 저장하는 딕셔너리 변수명 변경
                """
                self.temp_merge_center_dict[label_number] = tmp_center_dict[label_number]
                self.plt_save(self.temp_merge_center_dict,
                                title=f"{self.temp_merge_center_dict[label_number]['name']} 주요 스펙트럼 분포", 
                                save_path=graph_full_path + f"/{self.select_image_name}_{self.temp_merge_center_dict[label_number]['name']}_graph.png"
                                )
            """
                description
                modified by Myounghwan(20240531) : cetner spectrum 저장하는 딕셔너리 변수명 변경
            """
            title = self.lang.get("labeling", "labelSub", "labelSubGraphTitle")
            self.plt_save(tmp_center_dict,
                          title=title, 
                          save_path=graph_full_path + f"/{self.select_image_name}_graph.png"
                          )
            with open(self.tmp_fname+'/result.json', 'w', encoding='utf-8') as fp:
                json.dump(log_dict, fp,indent="\t", ensure_ascii=False)
            self.tmp_fname = None

    def plt_save(self, data_list, title, save_path):
        plt.figure()
        ax = plt.axes()
        ax.set_facecolor('lightslategray')
        plt.grid(True)
        plt.xlabel("Bands")
        plt.ylabel("Reflectance")
        plt.ylim([0, 5000])
        label_handle_list = []
        for label_number in data_list.keys():
            if label_number == 0:
                continue
            name = data_list[label_number]['name']
            color = data_list[label_number]['color']
            centernearspectrum_list = data_list[label_number]['centernearspectrum']
            plt.plot(centernearspectrum_list.T, color=[color[0]/256.0, color[1]/256.0, color[2]/256.0])
            tmp_line = mlines.Line2D([], [], color=[color[0]/256.0, color[1]/256.0, color[2]/256.0], label=name)
            label_handle_list.append(tmp_line)
        plt.title(title)
        plt.legend(handles=label_handle_list, loc='lower left', bbox_to_anchor=(1.0,0.5))
        plt.savefig(save_path, bbox_inches='tight', dpi=200)
        plt.close()

    def label_sub_to_display(self, input):
        self.label_sub_to_display_signal.emit(input)

    def closeEvent(self, e):
        if self.parent.label_list_setting.isChecked():
            self.parent.label_list_setting.toggle()
        if self.label_sub_ess_option_Form.isVisible():
            self.label_sub_ess_option_Form.close()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = label_sub_Form()
    sys.exit(app.exec_())
