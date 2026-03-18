"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

import json
from PyQt5.QtCore import QObject, pyqtSlot

import os
import cv2
import numpy as np
import copy
import spectral
import time

from .db_labeling import DB_Control_Labeling
from constants.constants import MESSAGE_BOX_WARNING, PEN_MODE_IMAGE, AGGREGATION_DATA, MESSAGE_BOX_INFORMATION
from utils.custom_ui import messageBox

from utils.shared import temp_path

class Sub_Core_Labeling(QObject):
    """각 기등들 간 상태를 주고받기 위해 호출하는 클래스. Core DB를 통해 데이터 정보에 대해 저장할 수 있다.
    """
    # def __init__(self, Sub_Core_Sync_Labeling = None):
    def __init__(self, Sync = None, lang=None):
        super().__init__()
        self.init(Sync, lang)
        self.init_DB()
        self.init_DBCTL()
        self.init_Sync()

    def init(self, Sync, lang):
        self.Sync = Sync # self.Main_Core_Sync
        self.lang=lang
        self.Sub_Core_Sync_Labeling = self.Sync.Sub_Core_Sync_Labeling
        self.image_control_dict = self.Sub_Core_Sync_Labeling.image_control_dict
        self.label_obj_dict = self.Sub_Core_Sync_Labeling.label_obj_dict
        self.semiAutoLabelingDict = self.Sub_Core_Sync_Labeling.semiAutoLabelingDict
        self.Core_DB_Labeling = self.Sub_Core_Sync_Labeling.Core_DB_Labeling

    def init_DB(self):
        """Core DB에 대한 초기 셋팅값을 설정하는 함수이다.
        """
        # self.Core_DB_Labeling = {}
        # self.Core_DB_Labeling['image_list'] = {}
        # self.Core_DB_Labeling['graph_info'] = {}
        self.Core_DB_Labeling['image_list'] = {}
        self.Core_DB_Labeling['graph_info'] = {}
        
    def init_DBCTL(self):
        functions = [self.load_data, self.load_label_info, self.send_core_db_to_label, self.send_core_to_image_sub, self.send_core_to_graph_sub]
        self.DB_Control_Labeling = DB_Control_Labeling(Core_DB_Labeling=self.Core_DB_Labeling, functions=functions, Sync=self.Sync)
        self.query_db_labeling = self.DB_Control_Labeling.query_db_labeling

    def init_Sync(self):
        """
            @description: Core를 통해 들어오는 모든 slot/signal을 초기 선언하는 함수.
            @author: MyoungHwan
            @history
                Implemented by MyoungHwan(2024.09.06): label_sub에서 display로 값을 전달하는 signal 추가
        """
        #mainwindow
        self.mainwindow_to_core_signal = self.Sub_Core_Sync_Labeling.mainwindow_to_core_signal
        self.mainwindow_to_core_signal.connect(self.recv_mainwindow_to_core)

        # image
        self.image_to_core_signal = self.Sub_Core_Sync_Labeling.image_to_core_signal
        self.image_to_core_signal.connect(self.recv_image_to_core)
        self.image_to_label_signal = self.Sub_Core_Sync_Labeling.image_to_label_signal
        self.image_to_label_signal.connect(self.send_image_to_label)
        self.image_to_label_sub_signal = self.Sub_Core_Sync_Labeling.image_to_label_sub_signal
        self.image_to_label_sub_signal.connect(self.send_image_to_label_sub)
        self.image_to_display_signal = self.Sub_Core_Sync_Labeling.image_to_display_signal
        self.image_to_display_signal.connect(self.send_image_to_display)
        self.image_to_display_sub_rgb_change_signal = self.Sub_Core_Sync_Labeling.image_to_display_sub_rgb_change_signal
        self.image_to_display_sub_rgb_change_signal.connect(self.send_image_to_display_sub_rgb_change)
        self.image_to_labeling_mode_main_signal = self.Sub_Core_Sync_Labeling.image_to_labeling_mode_main_signal
        self.image_to_labeling_mode_main_signal.connect(self.send_image_to_labeling_mode_main)
        self.imageToGraphGroupSignal = self.Sub_Core_Sync_Labeling.imageToGraphGroupSignal
        self.imageToGraphGroupSignal.connect(self.sendImageToGraphGroup)
        self.image_to_graph_signal = self.Sub_Core_Sync_Labeling.image_to_graph_signal
        self.image_to_graph_signal.connect(self.send_image_to_graph)
        self.image_to_graph_sub_signal = self.Sub_Core_Sync_Labeling.image_to_graph_sub_signal
        self.image_to_graph_sub_signal.connect(self.send_image_to_graph_sub)
        self.imageToSemiAutoLabelingSignal = self.Sub_Core_Sync_Labeling.imageToSemiAutoLabelingSignal
        self.imageToSemiAutoLabelingSignal.connect(self.sendImageToSemiAutoLabeling)

        #image detail
        self.image_sub_to_core_signal = self.Sub_Core_Sync_Labeling.image_sub_to_core_signal
        self.image_sub_to_core_signal.connect(self.recv_image_sub_to_core)
        
        self.image_sub_to_label_signal = self.Sub_Core_Sync_Labeling.image_sub_to_label_signal
        self.image_sub_to_label_signal.connect(self.send_image_sub_to_label)

        self.image_sub_to_display_signal = self.Sub_Core_Sync_Labeling.image_sub_to_display_signal
        self.image_sub_to_display_signal.connect(self.send_image_sub_to_display)

        self.image_sub_to_labeling_mode_main_signal = self.Sub_Core_Sync_Labeling.image_sub_to_labeling_mode_main_signal
        self.image_sub_to_labeling_mode_main_signal.connect(self.send_image_sub_to_labeling_mode_main)

        #label
        self.label_to_core_signal = self.Sub_Core_Sync_Labeling.label_to_core_signal
        self.label_to_core_signal.connect(self.recv_label_to_core)
        self.label_sub_to_core_signal = self.Sub_Core_Sync_Labeling.label_sub_to_core_signal
        self.label_sub_to_core_signal.connect(self.recv_label_sub_to_core)
        self.label_to_display_signal = self.Sub_Core_Sync_Labeling.label_to_display_signal
        self.label_to_display_signal.connect(self.send_label_to_display)
        self.label_to_pen_style_signal = self.Sub_Core_Sync_Labeling.label_to_pen_style_signal
        self.label_to_pen_style_signal.connect(self.send_label_to_pen_style)
        self.labelToGraphGroupSignal = self.Sub_Core_Sync_Labeling.labelToGraphGroupSignal
        self.labelToGraphGroupSignal.connect(self.sendLabelToGraphGroup)
        self.label_image_to_display_signal = self.Sub_Core_Sync_Labeling.label_image_to_display_signal
        self.label_image_to_display_signal.connect(self.send_image_to_display)
        """
            Description: label_sub에서 display로 값을 전달하기 위한 signal 추가
            Implemented by MyoungHwan (2024.09.06)
        """
        self.label_sub_to_display_signal = self.Sub_Core_Sync_Labeling.label_sub_to_display_signal
        self.label_sub_to_display_signal.connect(self.send_label_sub_to_display)
        

        #display
        self.display_to_core_signal =  self.Sub_Core_Sync_Labeling.display_to_core_signal
        self.display_to_core_signal.connect(self.recv_display_to_core)

        self.display_sub_rgb_change_to_display_signal = self.Sub_Core_Sync_Labeling.display_sub_rgb_change_to_display_signal
        self.display_sub_rgb_change_to_display_signal.connect(self.send_display_sub_rgb_change_to_display)

        self.display_sub_rgb_change_to_graph_sub_signal = self.Sub_Core_Sync_Labeling.display_sub_rgb_change_to_graph_sub_signal
        self.display_sub_rgb_change_to_graph_sub_signal.connect(self.send_display_sub_rgb_change_to_graph_sub)

        self.display_to_labeling_mode_main_signal = self.Sub_Core_Sync_Labeling.display_to_labeling_mode_main_signal
        self.display_to_labeling_mode_main_signal.connect(self.send_display_to_labeling_mode_main)

        self.displayToGraphGroupSignal = self.Sub_Core_Sync_Labeling.displayToGraphGroupSignal
        self.displayToGraphGroupSignal.connect(self.sendDisplayToGraphGroup)

        self.display_to_graph_signal = self.Sub_Core_Sync_Labeling.display_to_graph_signal
        self.display_to_graph_signal.connect(self.send_display_to_graph)

        self.display_to_pen_style_signal = self.Sub_Core_Sync_Labeling.display_to_pen_style_signal
        self.display_to_pen_style_signal.connect(self.send_display_to_pen_style)
        

        #core
        self.core_to_label_signal = self.Sub_Core_Sync_Labeling.core_to_label_signal
        self.core_to_label_sub_signal = self.Sub_Core_Sync_Labeling.core_to_label_sub_signal
        self.core_to_display_signal = self.Sub_Core_Sync_Labeling.core_to_display_signal
        self.core_to_image_sub_signal = self.Sub_Core_Sync_Labeling.core_to_image_sub_signal
        self.core_to_display_sub_rgb_change_signal = self.Sub_Core_Sync_Labeling.core_to_display_sub_rgb_change_signal
        self.core_to_labeling_mode_main_signal = self.Sub_Core_Sync_Labeling.core_to_labeling_mode_main_signal
        self.core_to_pen_signal = self.Sub_Core_Sync_Labeling.core_to_pen_signal
        self.core_to_pen_eraser_signal = self.Sub_Core_Sync_Labeling.core_to_pen_eraser_signal
        self.core_to_pen_style_signal = self.Sub_Core_Sync_Labeling.core_to_pen_style_signal
        self.coreToGraphGroupSignal = self.Sub_Core_Sync_Labeling.coreToGraphGroupSignal
        self.core_to_graph_signal = self.Sub_Core_Sync_Labeling.core_to_graph_signal
        self.core_to_graph_sub_signal = self.Sub_Core_Sync_Labeling.core_to_graph_sub_signal
        self.coreToSemiAutoLabelingSignal = self.Sub_Core_Sync_Labeling.coreToSemiAutoLabelingSignal
        

        #graph
        self.graphGroupToCoreSignal = self.Sub_Core_Sync_Labeling.graphGroupToCoreSignal
        self.graphGroupToCoreSignal.connect(self.recvGraphGroupToCore)
        self.graph_to_core_signal = self.Sub_Core_Sync_Labeling.graph_to_core_signal
        self.graph_to_core_signal.connect(self.recv_graph_to_core)
        self.graphToGraphGroupSignal = self.Sub_Core_Sync_Labeling.graphToGraphGroupSignal
        self.graphToGraphGroupSignal.connect(self.sendGraphToGraphGroup)
        self.graphGroupToDisplaySignal = self.Sub_Core_Sync_Labeling.graphGroupToDisplaySignal
        self.graphGroupToDisplaySignal.connect(self.sendGraphGroupToDisplay)
        self.graph_to_display_signal = self.Sub_Core_Sync_Labeling.graph_to_display_signal
        self.graph_to_display_signal.connect(self.send_graph_to_display)
        self.graph_sub_to_display_signal = self.Sub_Core_Sync_Labeling.graph_sub_to_display_signal
        self.graph_sub_to_display_signal.connect(self.send_graph_sub_to_display)
        self.graphGroupToGraphSignal = self.Sub_Core_Sync_Labeling.graphGroupToGraphSignal
        self.graphGroupToGraphSignal.connect(self.sendGraphGroupToGraph)

        #pen
        self.pen_to_core_signal = self.Sub_Core_Sync_Labeling.pen_to_core_signal
        self.pen_to_core_signal.connect(self.recv_pen_to_core)
        self.pen_to_display_signal = self.Sub_Core_Sync_Labeling.pen_to_display_signal
        self.pen_to_display_signal.connect(self.send_pen_to_display)
        self.penToSemiAutoLabelingSignal = self.Sub_Core_Sync_Labeling.penToSemiAutoLabelingSignal
        self.penToSemiAutoLabelingSignal.connect(self.sendPenToSemiAutoLabeling)

        #pen style
        self.pen_style_to_core_signal = self.Sub_Core_Sync_Labeling.pen_style_to_core_signal
        self.pen_style_to_core_signal.connect(self.recv_pen_style_to_core)
        self.pen_style_to_display_signal = self.Sub_Core_Sync_Labeling.pen_style_to_display_signal
        self.pen_style_to_display_signal.connect(self.send_pen_style_to_display)

        #pen eraser
        self.pen_eraser_to_core_signal = self.Sub_Core_Sync_Labeling.pen_eraser_to_core_signal
        self.pen_eraser_to_core_signal.connect(self.recv_pen_eraser_to_core)
        self.pen_eraser_to_display_signal = self.Sub_Core_Sync_Labeling.pen_eraser_to_display_signal
        self.pen_eraser_to_display_signal.connect(self.send_pen_eraser_to_display)


        """
            Description: label opacity 기능 위치 변경에 따른 signal 추가
            Implemented by HyunsuKim (2024.11.28)
        """
        #pen opacity
        self.pen_opacity_to_display_signal = self.Sub_Core_Sync_Labeling.pen_opacity_to_display_signal
        self.pen_opacity_to_display_signal.connect(self.send_pen_opacity_to_display)
        
    @pyqtSlot(dict)
    def recv_mainwindow_to_core(self, input):
        """mainwindow로부터 signal을 받기 위한 함수이다.
        """
        self.save_data(input)

    @pyqtSlot(dict)
    def recv_image_to_core(self, input):
        """image로부터 signal을 받기 위한 함수이다.
        """
        # print("recv image infomation")
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_image_sub_to_core(self, input):
        """image sub detail로부터 signal을 받기 위한 함수이다.
        """
        # print("recv image infomation")
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_label_to_core(self, input):
        """label로부터 signal을 받기 위한 함수이다.
        """
        # print("recv label infomation")
        if input['mode'] == 'save_label_class':
            self.save_class_data()
        else:
            self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_label_sub_to_core(self, input):
        """label sub로부터 signal을 받기 위한 함수이다.
        """
        # print("recv label infomation")
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_display_to_core(self, input):
        """display로부터 signal을 받기 위한 함수이다.
        """
        # print("recv display infomation")
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_pen_to_core(self, input):
        """pen으로부터 signal을 받기 위한 함수이다.
        """
        # print("recv pen infomation")
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_pen_eraser_to_core(self, input):
        """pen eraser로부터 signal을 받기 위한 함수이다.
        """
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_pen_semi_auto_labeling_to_core(self, input):
        """Receive signal from pen_sub_semi_auto_labeling
        """
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_pen_style_to_core(self, input):
        """pen style로부터 signal을 받기 위한 함수이다.
        """
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recvGraphGroupToCore(self, input):
        """
            description: Function to receive signal from "graph group" to "core"
            author: GaEun Hwang (2025.12.05)
        """
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def recv_graph_to_core(self, input):
        """graph로부터 signal을 받기 위한 함수이다.
        """
        # print("recv graph infomation")
        self.query_db_labeling(input)

    @pyqtSlot(dict)
    def send_image_to_label(self, output):
        """
            @description : image에서 label로 signal에 대한 요청 결과를 보내기 위한 함수이다.
            @author : MyoungHwan
            @history
                1. Modified by MyoungHwan(20240411) : input value 변경 및 개선
        """
        # print("send to image to label infomation")
        input = {}
        input['from'] = 'image'
        input['mode'] = output['mode']
        if 'image_info' in output:
            input['image_info'] = output['image_info']
        if  input['mode'] == 'load':
            image_number = self.image_control_dict['select_image_number']
            """
                description
                Modified by MyoungHwan(20240529) : data.json 에서 호출된 딕셔너리 정보 호출 및 저장
            """
            input['image_number'] = image_number
            input['label_dict'] = self.Core_DB_Labeling['image_list'][image_number]['label_list']

        self.send_core_to_label(input)

    @pyqtSlot(dict)
    def send_image_to_label_sub(self, output):
        """image에서 label sub로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        # print("send to image to label infomation")
        input = {}
        self.send_core_to_label_sub(input)

    @pyqtSlot(dict)
    def send_image_to_display(self, output):
        """image에서 display로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        # print("send to image to display infomation")
        input = {}
        input['from'] = 'image'
        input['mode'] = output['mode']
        if input['mode'] == "show":
            input['image_number'] = self.image_control_dict['select_image_number']
            input['image_rgb'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['image_data'])
            input['image_label'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['image_label'])
            input['image_raw'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['image_raw'])
            input['image_raw_origin'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['image_raw_origin'])
            input['hsi_wave_length'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['hsi_wave_length'])
            input['image_raw_white'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['image_raw_white'])
            input['image_raw_dark'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['image_raw_dark'])
            input['hsi_wave_length'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['hsi_wave_length'])
            input['hsi_default_bands'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][input['image_number']]['image_info']['hsi_default_bands'])
        
        elif input['mode'] == "status":
            # 이미지 선택했을 때 정보 전달
            input['image_number'] = self.image_control_dict['select_image_number']

        elif input['mode'] == "unchecked":
            pass
        self.send_core_to_display(input)

    @pyqtSlot(dict)
    def send_image_to_display_sub_rgb_change(self, output):
        input = {}
        input['from'] = 'image'
        input['mode'] = output['mode']
        if input['mode'] == "load":
            image_number = output['image_number']
            hsi_metadata = self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_metadata']
            if hsi_metadata:
                input['hsi_default_bands'] = self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_default_bands'] 
                input['hsi_wave_length'] = self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_wave_length'] 
                input['hsi_wave_count'] = self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_wave_count']
                self.send_core_to_display_sub_rgb_change(input)
            else:
                print("HSI Data is None. Can not load HSI wave length.")
        elif input['mode'] == "unload":
            self.send_core_to_display_sub_rgb_change(input)
    
    @pyqtSlot(dict)
    def send_image_to_labeling_mode_main(self, output):
        input = {}
        input['from'] = 'image'
        input['mode'] = output['mode']
        if input['mode'] != 0:
            select_image_number = output['image_number']
            if len(self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['hsi_metadata']) == 0 :
                #그래프 모드 off
                input['type_detail'] = 1
            else:
                input['type_detail'] = 0
        
        self.send_core_to_labeling_mode_main(input)

    @pyqtSlot(dict)
    def sendImageToGraphGroup(self, output):
        """
            description: Function to send signal from "image" to "graph group"
            author: GaEun Hwang (2025.12.05)
        """
        output['from'] = 'image'
        self.sendCoreToGraphGroup(output)

    @pyqtSlot(dict)
    def send_image_to_graph(self, output):
        output['from'] = 'image'
        image_number = output['image_number']
        output['data_name'] = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_name']
        output['save_path'] = temp_path
        if len(self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_metadata']) != 0 :
            output['hsi_metadata'] = self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_metadata']
        else:
            output['hsi_metadata'] = {}
        self.send_core_to_graph(output)

    @pyqtSlot(dict)
    def send_image_to_graph_sub(self, output):
        output['from'] = 'image'
        image_number = output['image_number']
        mode = output['mode']
        if mode: # image select
            if self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_white'].size == 0 or self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_dark'].size == 0:
                output['mode_detail'] = 0
            else:
                output['mode_detail'] = 1
        else: # image not select
            output['mode_detail'] = 0

        self.send_core_to_graph_sub(output)

    @pyqtSlot(dict)
    def sendImageToSemiAutoLabeling(self, output):
        output['data'] = self.Core_DB_Labeling['image_list'][self.image_control_dict['select_image_number']]['image_info']['image_raw']
        self.sendCoreToSemiAutoLabeling(output)

    @pyqtSlot(dict)
    def send_image_sub_to_label(self, output):
        """
            @description : image sub detail에서 label로 signal에 대한 요청 결과를 보내기 위한 함수이다.
            @author : MyoungHwan
            @history
                1. Modified by MyoungHwan(20240411) : input value 변경 및 개선
        """
        input = {}
        input['from'] = 'image'
        input['mode'] = output['mode']
        if  input['mode'] == 'load':
            image_number = self.image_control_dict['select_image_number']
            """
                description
                Modified by MyoungHwan(20240529) : data.json 에서 호출된 딕셔너리 정보 호출 및 저장
            """
            input['label_dict'] = self.Core_DB_Labeling['image_list'][image_number]['label_list']
            self.send_core_to_label(input)

    @pyqtSlot(dict)
    def send_image_sub_to_display(self, output):
        """image sub detail에서 display로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        input = {}
        input['from'] = 'image'
        input['mode'] = output['mode']
        if input['mode'] == "show":
            image_number = self.image_control_dict['select_image_number']
            if image_number > -1:
                input['image_number'] = image_number
                input['image_rgb'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_data'])
                input['image_label'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label'])
                input['image_raw'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw'])
                input['image_raw_origin'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_origin'])
                input['image_raw_white'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_white'])
                input['image_raw_dark'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_raw_dark'])
                input['hsi_wave_length'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_wave_length'])
                input['hsi_default_bands'] = copy.deepcopy(self.Core_DB_Labeling['image_list'][image_number]['image_info']['hsi_default_bands'])
                self.send_core_to_display(input)
                print("image is update, but not selected")

    @pyqtSlot(dict)
    def send_image_sub_to_labeling_mode_main(self, output):
        input = {}
        input['from'] = 'image_sub'
        input['mode'] = output['mode']
        self.send_core_to_labeling_mode_main(input)

    @pyqtSlot(dict)
    def send_display_sub_rgb_change_to_display(self, output):
        input = {}
        input['from'] = 'display_sub_rgb_change'
        input['mode'] = output['mode']
        if input['mode'] == 0:
            input['select_color_bands'] = output['hsi_cur_bands']
        
        self.send_core_to_display(input)

    @pyqtSlot(dict)
    def send_display_sub_rgb_change_to_graph_sub(self, output):
        input = {}
        input['from'] = 'display_sub_rgb_change'
        input['mode'] = output['mode']        
        self.send_core_to_graph_sub(input)
        
    @pyqtSlot(dict)
    def send_display_to_labeling_mode_main(self, output):
        input = {}
        input['from'] = 'display'
        input['mode'] = output['mode']
        if input['mode'] != 0:
            select_image_number = output['image_number']
            if len(self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['hsi_metadata']) == 0 :
                #그래프 모드 off
                input['type_detail'] = 1
            else:
                input['type_detail'] = 0
        self.send_core_to_labeling_mode_main(input)
    
    @pyqtSlot(dict)
    def send_display_to_pen_style(self, output):
        self.send_core_to_pen_style(output)

    @pyqtSlot(dict)
    def sendDisplayToGraphGroup(self, output):
        """
            description: Function to send signal from "display" to "graph group"
            author: GaEun Hwang (2025.12.05)
        """
        output['from'] = 'display'
        self.sendCoreToGraphGroup(output)

    @pyqtSlot(dict)
    def send_display_to_graph(self, output):
        output['from'] = 'display'
        self.send_core_to_graph(output)

    @pyqtSlot(dict)
    def send_label_to_display(self, output):
        """label에서 display로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        # print("send to image to display infomation")
        input = output
        input['from'] = 'label'
        if input['mode'] in ["hide", "color"]:
            image_number = self.image_control_dict['select_image_number']
            label_number = input['label_number']
            image_rgb = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_data']
            image_label = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label']
            input['label_number'] = label_number
            input['image_rgb'] = copy.deepcopy(image_rgb)
            input['image_label'] = copy.deepcopy(image_label)
        elif input['mode'] == "show":
            if input['type'] in ['reset', 'select_remove']:
                image_number = self.image_control_dict['select_image_number']
                image_label = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_label']
                input['image_label'] = copy.deepcopy(image_label)
        elif input['mode'] == "status":
            pass
        elif input['mode'] == 'all_hide_show':
            pass
        self.send_core_to_display(input)

    @pyqtSlot(dict)
    def send_label_to_pen_style(self, output):
        output['from'] = 'label'
        if output['mode'] == 'reset':
            pass
        elif output['mode'] == 'select':
            pass
        self.send_core_to_pen_style(output)
    
    @pyqtSlot(dict)
    def sendLabelToGraphGroup(self, output):
        """
            description: Function to send signal from "label" to "graph group"
            author: GaEun Hwang (2025.12.05)
        """
        output['from'] = 'label'
        self.sendCoreToGraphGroup(output)

    @pyqtSlot(dict)
    def send_label_sub_to_display(self, output):
        """
            @description: Function to transfer tmp_dict from "label_sub" to "display"
            @author: MyoungHwan (2024.09.06)
        """
        output['from'] = 'label_sub'
        self.send_core_to_display(output)

    @pyqtSlot(dict)
    def send_pen_to_display(self, output):
        """pen에서 display로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        print("recv pen to display core")
        input = {}
        input['from'] = 'pen'
        input['pen_mode'] = output['mode']
        input['toggle'] = output['toggle']
        if output['mode'] == PEN_MODE_IMAGE:
            image_number = self.image_control_dict['select_image_number']
            input['image_path'] = self.Core_DB_Labeling['image_list'][image_number]['image_info']['image_data_path']
        self.send_core_to_display(input)

    @pyqtSlot(dict)
    def sendPenToSemiAutoLabeling(self, output):
        self.sendCoreToSemiAutoLabeling(output)

    @pyqtSlot(dict)
    def sendPenSemiAutoLabelingToPen(self,output):
        self.sendCoreToPen(output)

    @pyqtSlot(dict)
    def send_pen_style_to_display(self, output):
        input = {}
        input['from'] = 'pen_sub'
        input['type'] = output['type']
        if input['type'] == 'style':
            pass
        elif input['type'] == 'sub_label':
            input['sub_label_number'] = output['sub_label_number']
        self.send_core_to_display(input)

    @pyqtSlot(dict)
    def send_pen_eraser_to_display(self, output):
        output['from'] = 'pen_sub'
        output['type'] = 'eraser'
        self.send_core_to_display(output)
    
    @pyqtSlot(dict)
    def send_pen_semi_auto_labeling_to_display(self, output):
        output['from'] = 'pen_sub'
        output['type'] = 'semi_auto_labeling'
        self.send_core_to_display(output)

    @pyqtSlot(dict)
    def send_pen_opacity_to_display(self, output):  
        """pen opacity에서 display로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        output['from'] = 'pen_opacity'
        self.send_core_to_display(output)  
    
    @pyqtSlot(dict)
    def sendGraphToGraphGroup(self, output):
        """
            description: Function to send signal from "graph" to "graph group"
            author: GaEun Hwang (2025.12.05)
        """
        output['from'] = "graph"
        self.sendCoreToGraphGroup(output)

    @pyqtSlot(dict)
    def sendGraphGroupToDisplay(self, output):
        """
            description: Function to send signal from "graph group" to "display"
            author: GaEun Hwang (2025.12.05)
        """
        output['from'] = "graphGroup"
        self.send_core_to_display(output)

    @pyqtSlot(dict)
    def send_graph_to_display(self, output):
        """graph에서 display로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        input = {}
        input['from'] = 'graph'
        input['type'] = output['type']
        if input['type'] == 'checked' or input['type'] == 'unchecked':
            input['number'] = output['number']
        elif input['type'] == 'all_select':
            input['checked'] = output['checked']
        elif input['type'] == 'select_delete':
            input['number'] = output['number']
        elif input['type'] == 'show partial' or input['type'] == 'hide partial':
            input['index'] = output['index']
        self.send_core_to_display(input)

    @pyqtSlot(dict)
    def send_graph_sub_to_display(self, output):
        output['from'] = 'graph_sub'
        self.send_core_to_display(output)
    
    @pyqtSlot(dict)
    def sendGraphGroupToGraph(self, output):
        """
            description: Function to send signal from "graph group" to "graph"
            author: GaEun Hwang (2025.12.05)
        """
        output['from'] = "graphGroup"
        self.send_core_to_graph(output)

    def send_core_db_to_label(self, output):
        """core에서 label로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        input = {}
        input['from'] = 'image'
        input['mode'] = output['mode']
        if input['mode'] == 'select':
            input['type'] = output['type']

            if input['type'] == 'value':
                input['value'] = output['value']

            elif input['type'] == 'object':
                input['object'] = output['object']
        elif input['mode'] == 'load':
            input['type'] = 'new'
            input['label_dict'] = output['label_info']
            input['image_info'] = output['image_info']
            input['image_number'] = output['image_number']
        self.send_core_to_label(input)

    def send_core_to_image_sub(self, input):
        """core에서 image sub detail로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        self.core_to_image_sub_signal.emit(input)

    def send_core_to_label(self, input):
        """core에서 label로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        self.core_to_label_signal.emit(input)

    def send_core_to_label_sub(self, input):
        """core에서 label sub로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        self.core_to_label_sub_signal.emit(input)
    
    def sendCoreToSemiAutoLabeling(self, input):
        """emit signal from core to semi auto labeling.
        """
        self.coreToSemiAutoLabelingSignal.emit(input)

    def sendCoreToPen(self,input):
        self.core_to_pen_signal.emit(input)

    def send_core_to_display(self, input):
        """core에서 display로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        self.core_to_display_signal.emit(input)

    def send_core_to_pen_style(self, input):
        """core에서 pen style로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        self.core_to_pen_style_signal.emit(input)

    def send_core_to_display_sub_rgb_change(self, input):
        """core에서 display rgb change로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        self.core_to_display_sub_rgb_change_signal.emit(input)

    def send_core_to_labeling_mode_main(self, input):
        """core에서 mid mainwindow로 signal에 대한 요청 결과를 보내기 위한 함수이다.
        """
        self.core_to_labeling_mode_main_signal.emit(input)
    
    def sendCoreToGraphGroup(self, input):
        """
            description: Function to send signal from "core" to "graph group"
            author: GaEun Hwang (2025.12.05)
        """
        self.coreToGraphGroupSignal.emit(input)

    def send_core_to_graph(self, input):
        self.core_to_graph_signal.emit(input)
    
    def send_core_to_graph_sub(self, input):
        self.core_to_graph_sub_signal.emit(input)

    def load_data(self, path, folder_name, mode=0, shape=[400,512,224], label_name="label.npy", raw_name='data.raw'):
        """
            @Description: 실제 경로에서 데이터를 불러오기 위한 함수이다.
            @Parameters
                1. path(str): 데이터 경로
                2. folder_name(str): 데이터 명
                3. mode(int)
                    - 0 : 일반 초기 image load
                    - 1 : image detail mode에서 image(rgb) 파일 변경 시
                    - 2 : image detail mode에서 image(label) 파일 변경 시
                    - 3 : image detail mode에서 image(hsi) 파일 변경 시
                4. shape(list) : mode가 2일 경우 image shape의 크기를 명시해야 함 (width, height, band)
            @History
                1. Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
                2. GaEun Hwang(26.02.03):
                    - Add branch for data generated by label aggregation
                3. Yugyeong Hong(26.02.24):
                    - Refactor message box with util method and language support
        """
        full_path = path

        if mode == 0:
            image_width = 400
            image_height = 512
            image_hsi_bands = 224
            dark_data = np.array([])
            white_data = np.array([])
            hsi_metadata = {}
            full_path = path  + "/" +  folder_name
            # 일반 모든 data load
            try:
                hsi_data_name = "data.raw"
                only_file_name = os.path.splitext(hsi_data_name)[0]
                spectral_data = spectral.io.envi.open(full_path + "/" + only_file_name + ".hdr", full_path + "/" + only_file_name + ".raw")
                hsi_data_origin = spectral_data.asarray().copy()
                hsi_data = spectral_data.asarray().copy()
                image_width, image_height, _ = hsi_data.shape
                hsi_metadata = spectral_data.metadata
                refFiles = ["DARKREF.hdr", "DARKREF.raw", "WHITEREF.hdr", "WHITEREF.raw"]

                if 'lines' in hsi_metadata:
                    image_width = int(hsi_metadata['lines'])
                if 'samples' in hsi_metadata:
                    image_height = int(hsi_metadata['samples'])
                if 'bands' in hsi_metadata:
                    image_hsi_bands = int(hsi_metadata['bands'])

                # calibration
                if all(os.path.exists(os.path.join(full_path, f)) for f in refFiles):
                    dark_spectral_data = spectral.io.envi.open(full_path + "/" + 'DARKREF.hdr', full_path + "/" + 'DARKREF.raw')
                    dark_data = dark_spectral_data.asarray()
                    white_spectral_data = spectral.io.envi.open(full_path + "/" + 'WHITEREF.hdr', full_path + "/" + 'WHITEREF.raw')
                    white_data = white_spectral_data.asarray()
                    # Add branch for data generated by label aggregation
                    if spectral_data.metadata.get("information") != AGGREGATION_DATA:
                        if dark_spectral_data.metadata.get("information") != AGGREGATION_DATA and white_spectral_data.metadata.get("information") != AGGREGATION_DATA:
                            dark_data = dark_spectral_data.asarray().mean(0)
                            white_data = white_spectral_data.asarray().mean(0)
                        else:
                            # notify user that reference data is aggregation data
                            message = f"{full_path}\n + {self.lang.get('labeling', 'core', 'advancedLabelAggregationInfoMessage')}"
                            messageBox(mode = MESSAGE_BOX_INFORMATION, 
                                       title = self.lang.get("labeling", "core", "advancedLabelAggregationInfoMessageTitle"), 
                                       text = message,
                                       buttons = {self.lang.get("main", "messageBox", "msgOk"):"accept"})
      
                    if len(dark_data) > 0 and len(white_data) > 0:
                        hsi_data = np.clip(((hsi_data_origin-dark_data)/(white_data-dark_data)), 0, 1) * 4095.0
            
            except:
                print(f"raw load error, Full path : {full_path}")
                hsi_data = np.array([])
                hsi_data_name = ""

            try:
                rgb_data_name = 'image_calibration.png'
                if rgb_data_name not in os.listdir(full_path):
                    rgb_data_name = 'image.png'
                # rgb_data = cv2.imread(full_path + "/" + rgb_data_name, cv2.IMREAD_COLOR)
                rgb_data = np.fromfile(full_path + "/" + rgb_data_name, np.uint8)
                rgb_data = cv2.imdecode(rgb_data, cv2.IMREAD_COLOR)
                rgb_data = cv2.cvtColor(rgb_data, cv2.COLOR_BGR2RGB)
                #hsi data 없을 경우 image size로
                if len(hsi_metadata) == 0:
                    image_width, image_height, _ = rgb_data.shape
            except:
                
                if len(hsi_metadata) == 0:
                    print(f"image load error, Full path : {full_path}")
                    rgb_data = np.array([])
                    rgb_data_name = ""
                else:
                    print(f"image load error, Load Image data from HSI DATA")
                    rgb_data_name = "image_from_spectral.png"
                    tmp_default_bands = list(map(int, hsi_metadata['default band']))
                    rgb_data = spectral.get_rgb(hsi_data, tmp_default_bands)
                    rgb_data = (rgb_data*255).astype(np.uint8)
                    cv2.imwrite(full_path + "/" + rgb_data_name, cv2.cvtColor(rgb_data, cv2.COLOR_BGR2RGB))
            
            try:
                label_data = np.load(full_path + "/" + label_name)
            except:
                label_data = np.full((image_width, image_height), 0)
                np.save(full_path + "/" + label_name, label_data)

            return rgb_data, label_data, hsi_data, rgb_data_name, label_name, hsi_data_name, hsi_metadata, hsi_data_origin, dark_data, white_data 
        # Improvemented by MyoungHwan(2024.12.13): image 리스트 업데이트 코드 추가
        # label 로딩항목 코드 수정
        elif mode == 1:
            # only label load
            width, height, _ = shape
            check_ = True
            try:
                label_data = np.load(full_path)
                label_w, label_h = label_data.shape
                if width != label_w or height != label_h:
                    raise Exception("label shape isn't matched")
            except Exception as e:
                print(f"label load error, Full path : {full_path}")
                label_data = np.full((width, height), 0)
                check_ = False
            return check_, label_data

    
    def load_label_info(self, path, folder_name, labelChange=False):
        """실제 경로에서 데이터를 불러오기 위한 함수이다.
            Parameters
            1. path(str): 데이터 경로
            2. folder_name(str): 데이터 명

            History
                1. Modified by HyunsuKim(2025.11.21) : Load commonLabelInfo or label_info according to conditions
        """
        
        full_path = path  + "/" +  folder_name

        try:
            with open(full_path+'/data.json', 'rb') as fp:
                # tmp_dict = pickle.load(fp)
                tmp_dict = json.load(fp)
            print("label info loading successfuly...")
        except:
            print("label info does not exist, create temp info...")
            tmp_dict = {
                "data_info": full_path,
                "label_info": {}
            }
        if labelChange:
            tmp_dict = {int(k): v for k, v in tmp_dict['commonLabelInfo'].items()}
        else:
            tmp_dict = {int(k): v for k, v in tmp_dict['label_info'].items()}
        # print(tmp_dict)

        return tmp_dict

    def save_data(self, input, save_folder_name=temp_path):
        """
            @Description: Labeled data save function.
            @Authore: MyoungHwan
            @Parameters
                1.  input(dict)
                    1. input['mode']: 저장방법
                        - 1 : save select image label
                        - 2 : save As select image label
                        - 3 : save all iamge label
            @History
                1. Modified by MyoungHwan(2024.02.15): Add MessageBox and Exception when labeled data saved.
                2. Modified by MyoungHwan(2024.03.14): Add Exception(ValueError) and delete signal code
                3. Modified by Yugyeong(2026.02.24): Refactor message box with util method and language support
        """
        mode = input['mode']
        select_image_number = self.image_control_dict['select_image_number']
        try:
            label_data = self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_label']
            if mode == 1:
                folder_path = self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_path'] + "/" + self.Core_DB_Labeling['image_list'][select_image_number]['image_info']['image_name']
                file_name = folder_path.split("/")[-1]
                np.save(folder_path + "/label.npy", label_data)

            elif mode == 2:
                save_as_path = input['save_as_path']
                if len(save_as_path) == 0:
                    # Modified by MyoungHwan(2024.03.14): Add Exception(ValueError) and delete signal code
                    raise ValueError("File path is empty.")
                np.save(save_as_path, label_data)
                file_full_name, ext = os.path.splitext(save_as_path)
                file_name = file_full_name.split("/")[-2]
                folder_path = os.path.split(file_full_name)[0]                            

            ctime_ = time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime(time.time()))
            tmp_dict = {
                "data_info": file_name,
                "time": ctime_,
                "label_info": {}
            }
            for label_number in self.label_obj_dict.keys():
                tmp_dict['label_info'][label_number] = {}
                tmp_dict['label_info'][label_number]['label_name'] = self.label_obj_dict[label_number]['name']
                tmp_dict['label_info'][label_number]['label_color'] = self.label_obj_dict[label_number]['color']
            
            with open(folder_path+'/data.json', 'w', encoding='utf-8') as fp:
                json.dump(tmp_dict, fp,indent="\t", ensure_ascii=False)
            
            messageBox(mode = MESSAGE_BOX_INFORMATION, 
                        title = self.lang.get("labeling", "core", "labelSaveTitle"),
                        text = self.lang.get("labeling", "core", "labelSavedMessage"),
                        buttons = {self.lang.get("main", "messageBox", "msgOk"):"accept"})
        # Modified by MyoungHwan(2024.03.14): Add Exception(ValueError) and delete signal code
        except ValueError as ve:
            print(ve)
        except Exception as e:
            print(e)
            messageBox(mode = MESSAGE_BOX_WARNING,
                        title = self.lang.get("labeling", "core", "labelSavedFailedMessageTitle"),
                        text = f'{self.lang.get("labeling", "core", "labelSavedFailedMessage")} {e}',
                        buttons = {self.lang.get("main", "messageBox", "msgOk"):"accept"})
            

    def save_class_data(self):
        """
            @ Description: send number, name, color of class saved in label_obj_dict(2025.03.19)
            @ Author: GaEun Hwang
            @ History
                1. Added by GaEun Hwang(2025.06.05): Add color data
        """
        tmp_dict = {
                "from": "core",
                "mode": "load saved class data",
                "label_number_list": [],
                "label_name_list": [],
                "label_color_list": []
            }
        for label_number in self.label_obj_dict.keys():
            tmp_dict['label_number_list'].append(label_number)
            tmp_dict['label_name_list'].append(self.label_obj_dict[label_number]['name'])
            tmp_dict['label_color_list'].append(self.label_obj_dict[label_number]['color'])
        
        messageBox(mode = MESSAGE_BOX_INFORMATION, 
                    title = self.lang.get("labeling", "core", "labelSaveTitle"),
                    text = self.lang.get("labeling", "core", "labelSavedInMemoryMessage"),
                    buttons = {self.lang.get("main", "messageBox", "msgOk"):"accept"})
        self.send_core_to_label(tmp_dict)
