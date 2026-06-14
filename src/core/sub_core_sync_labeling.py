"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

from PyQt5 import QtCore


class Sub_Core_Sync_Labeling(QtCore.QObject):
    """
        @description: 초기 slot/signal 선언을 위한 클래스
        @author: MyoungHwan
        @history
            Implemented by MyoungHwan(2024.09.06): label_sub에서 display로 값을 전달하는 signal 생성
    """
    #main window
    mainwindow_to_core_signal = QtCore.pyqtSignal(dict)
    mainwindow_to_pen_signal = QtCore.pyqtSignal(dict)

    #image
    image_to_core_signal = QtCore.pyqtSignal(dict)
    image_to_label_signal = QtCore.pyqtSignal(dict)
    image_to_label_sub_signal = QtCore.pyqtSignal(dict)
    image_to_display_signal = QtCore.pyqtSignal(dict)
    image_to_display_sub_rgb_change_signal = QtCore.pyqtSignal(dict)
    imageToGraphGroupSignal = QtCore.pyqtSignal(dict)
    imageToPenSignal = QtCore.pyqtSignal(dict)
    image_to_graph_signal = QtCore.pyqtSignal(dict)
    image_to_graph_sub_signal = QtCore.pyqtSignal(dict)
    image_to_labeling_mode_main_signal = QtCore.pyqtSignal(dict)
    image_sub_to_core_signal = QtCore.pyqtSignal(dict)
    image_sub_to_label_signal = QtCore.pyqtSignal(dict)
    image_sub_to_display_signal = QtCore.pyqtSignal(dict)
    image_sub_to_labeling_mode_main_signal = QtCore.pyqtSignal(dict)
    imageToSemiAutoLabelingSignal = QtCore.pyqtSignal(dict)
    

    #label
    label_to_core_signal = QtCore.pyqtSignal(dict)
    label_to_display_signal = QtCore.pyqtSignal(dict)
    label_to_pen_style_signal = QtCore.pyqtSignal(dict)
    labelToGraphGroupSignal = QtCore.pyqtSignal(dict)
    label_sub_to_core_signal = QtCore.pyqtSignal(dict)
    label_image_to_display_signal = QtCore.pyqtSignal(dict)
    """
        Description: label_sub에서 display로 값을 전달하기 위한 signal 초기화
        Implemented by MyoungHwan (2024.09.06)
    """
    label_sub_to_display_signal = QtCore.pyqtSignal(dict)

    #core
    core_to_image_signal = QtCore.pyqtSignal(dict)
    core_to_image_sub_signal = QtCore.pyqtSignal(dict)
    core_to_label_signal = QtCore.pyqtSignal(dict)
    core_to_label_sub_signal = QtCore.pyqtSignal(dict)
    core_to_display_signal = QtCore.pyqtSignal(dict)
    coreToDisplayMenuSignal = QtCore.pyqtSignal(dict)
    core_to_display_sub_rgb_change_signal = QtCore.pyqtSignal(dict)
    core_to_labeling_mode_main_signal = QtCore.pyqtSignal(dict)
    core_to_pen_signal = QtCore.pyqtSignal(dict)
    core_to_pen_eraser_signal = QtCore.pyqtSignal(dict)
    core_to_pen_style_signal = QtCore.pyqtSignal(dict)
    coreToGraphGroupSignal = QtCore.pyqtSignal(dict)
    core_to_graph_signal = QtCore.pyqtSignal(dict)
    core_to_graph_sub_signal = QtCore.pyqtSignal(dict)
    coreToSemiAutoLabelingSignal = QtCore.pyqtSignal(dict)

    #display
    display_to_core_signal = QtCore.pyqtSignal(dict)
    displayToGraphGroupSignal = QtCore.pyqtSignal(dict)
    display_to_graph_signal = QtCore.pyqtSignal(dict)
    display_to_labeling_mode_main_signal = QtCore.pyqtSignal(dict)
    display_to_pen_style_signal = QtCore.pyqtSignal(dict)
    displayToDisplayMenuSignal = QtCore.pyqtSignal(dict)

    # display menu
    displayMenuToDisplaySignal = QtCore.pyqtSignal(dict)
    displayMenuToPenSignal = QtCore.pyqtSignal(dict)

    # Similarity Map
    similarityToCoreSignal = QtCore.pyqtSignal(dict)

    #display change
    display_sub_rgb_change_to_core_signal = QtCore.pyqtSignal(dict)
    display_sub_rgb_change_to_display_signal = QtCore.pyqtSignal(dict)
    display_sub_rgb_change_to_graph_sub_signal = QtCore.pyqtSignal(dict)
    displaySubRgbChangeToGraphSignal = QtCore.pyqtSignal(dict)

    # Pen
    pen_to_core_signal = QtCore.pyqtSignal(dict)
    pen_to_display_signal = QtCore.pyqtSignal(dict)
    penToSemiAutoLabelingSignal = QtCore.pyqtSignal(dict)
    penToDisplayMenuSignal = QtCore.pyqtSignal(dict)

    #Pen style
    pen_style_to_core_signal = QtCore.pyqtSignal(dict)
    pen_style_to_display_signal = QtCore.pyqtSignal(dict)

    #Pen erase
    pen_eraser_to_core_signal = QtCore.pyqtSignal(dict)
    pen_eraser_to_display_signal = QtCore.pyqtSignal(dict)

    #Pen opacity
    pen_opacity_to_display_signal = QtCore.pyqtSignal(dict)

    # graph
    graphGroupToCoreSignal = QtCore.pyqtSignal(dict)
    graph_to_core_signal = QtCore.pyqtSignal(dict)
    graphGroupToDisplaySignal = QtCore.pyqtSignal(dict)
    graph_to_display_signal = QtCore.pyqtSignal(dict)
    graph_sub_to_core_signal = QtCore.pyqtSignal(dict)
    graph_sub_to_display_signal= QtCore.pyqtSignal(dict)
    graphGroupToGraphSignal = QtCore.pyqtSignal(dict)
    graphToGraphGroupSignal = QtCore.pyqtSignal(dict)
    graphToDisplaySubRgbChangeSignal = QtCore.pyqtSignal(dict)
    graphOptionToGraphSignal = QtCore.pyqtSignal(dict)

    graphGroupDict = {}
    labelViewGraphGroupDict = {}

    semiAutoLabelingDict = {}
    image_obj_dict = {}
    label_obj_dict = {}
    pen_obj_dict = {}
    graph_obj_dict = {}

    sub_widget_dict = {}

    #function variable object

    """
        main_control_dict
            

        display_control_dict
            mode에 따라 라벨모드 변경됨
            -1: 초기 및 대기 상태
            0: 라벨링 모드
            1: 라벨링 지우개(0번 라벨링) 모드
            2: 스펙트럼 표시모드(그래프 포인트)
            3: 확대된 이미지를 드래그 이용해서 부분 이동
            4: 특정부분 확대 모드
            5: 표시된 스펙트럼 지우개 모드(그래프 포인트 제거)
            6: 페인팅 모드

        graph_control_dict
            graph_line_preview
            graph_view_mode : graph pointer 의 view mode를 지정
                - 0 : random
                - 1 : selective
                - 2 : label
    """
    main_control_dict = {
        'label_saved' : False

    }


    """
        @Description: Diplay control 관련 Dictionary, 기능에 대한 변수값 정의 및 사용부분
        @Author: MyoungHwan
        @History
            1. Modified by MyoungHwan(24.12.05): label_control_dict 사용하지 않는 변수 제거
    """
    display_control_dict ={
        'drawing_mode' : -1,
        'old_drawing_mode':-1,
        'temp_drawing_mode':-1,
        'key_pressed':0
    }
    displayMenuControlDict = {
        "opened": False
    }
    image_control_dict ={
        'select_image_number' : -1,
        'image_control_sw' : True
    }
    #Modified by MyoungHwan(24.12.05): label_control_dict 사용하지 않는 변수 제거
    label_control_dict ={
        'select_main_label_number' : -1,
        'select_sub_label_number' : -1,
        'old_select_label_number' : -1,
        'label_control_sw' : True
    }
    pen_control_dict ={
        'pen_drawing_mode':0,
        'pen_drawing_size':1,
        'pen_eraser_size':1,
        'pen_graph_size':1,
        'pen_minimap_size':10,
        'pen_minimap_scale':150,
        'pen_control_sw' : True,
        'penSemiStrictness':90,
        'penSemiTolerance':90
    }
    graph_control_dict ={
        'graph_control_sw' : True,
        'graph_line_preview' : False,
        'selectedGraphGroup': -1,
        'oldSelectedGraphGroup': -1,
        'graph_view_mode' : 0
    }

    pixelBasedLabelingDict = {
        'similarityMode': "Area",
        'threshold': 90.0,
        'modeDefaultThreshold': 90.0
    }

    Core_DB_Labeling = {

    }
    selected_data_dict ={
        'image':[],
        'label':[]
    }

    def __init__(self, core_obj_dict):
        super().__init__()
        self.core_obj_dict = core_obj_dict