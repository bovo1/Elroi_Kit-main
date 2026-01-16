"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""
import sys
import os
import random
import copy
import numpy as np
from skimage.segmentation import flood
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, pyqtSlot
from labeling.stylesheet.stylesheet_display_main import stylesheet
from labeling.module.visualization import DLRGB, CMFRGB
from utils.viewer import Display_viewer
from utils.shared import background_image_path
from constants.constants import *
from utils.custom_item import customPolygonItem

## generate random color
random_color = lambda : [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

print(f"display cur path : "+ os.getcwd())

class Display_Form(QtWidgets.QWidget):
    def __init__(self, Sync=None, function_list=None, lang=None) -> None:
        super().__init__()
        """
            @Description: Display 관련 변수 초기화 부분
            @Author: MyoungHwan
            @History
                1. Added by MyoungHwan(2025.03.14): Added function to detect focus widget changed
                2. Modified by GaEun Hwang(2025.08.27): Added function to clear LDA Graph in function_list.
        """

        ## 그래프 리스트 클리어를 위한 함수
        self.clear_graph_list = function_list[0]
        # Add a function to clear LDA Graph.
        self.clearLDAGraph = function_list[1]
        self.update_graph_preview = function_list[2]

        #init variable
        self.init(Sync=Sync, lang=lang)
        self.init_variable()

        # Display UI setting
        self.init_Ui_label_main_display(self)
        self.setup_Ui_label_main_display()

        # Display UI moustracking mode on
        self.setMouseTracking(False)
        self.display_scrollAreaWidgetContents.setMouseTracking(True)
        # Added by MyoungHwan(2025.03.14): Added function to detect focus widget changed
        QtWidgets.QApplication.instance().focusChanged.connect(self.focus_changed)

        if __name__ == "__main__" :
            self.show()

    @pyqtSlot(dict)
    def recv_from_core(self, output):
        """
            @description: Display에 대한 업데이트를 위해 signal을 통해 실시간으로 정보를 업데이트하기 위한 함수이다. 모든 기능으로부터 받는 정보가 해당 함수에서 처리된다.
            @author: MyoungHwan
            @parameters
                1.output(dict): 딕셔너리 형탱로 signal을 다른 UI에서로 부터 값을 받아옴
            @history
                1. Modified by MyoungHwan (2024.09.06): 효율적인 연산을 위한 변수 최적화 및 추가, opacity 정보가 반영되도록 코드 수정
                2. Modified by MyoungHwan (2024.09.11): Opacity 적용관련 input 변경
                3. Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                4. Modified by MyoungHwan(2025.03.14): label opacity preview 조정 후 close 시 reset이 안되는 현상 수정
                5. Modified by MyoungHwan MyoungHwan (2025.03.14): 라벨데이터 저장 후 keypress 초기화 기능 제거
                6. Modified by MyoungHwan (2025.06.13): Fixed an issue when selecting "Not Used" in the Label ComboBox
                7. Modified by GaEun Hwang (2025.10.23): Modify about polygon drawing function for polygon refactoring
        """
        # print("recv_from_core", output)
        recv_from = output['from']
        if recv_from == 'image':
            image_mode = output['mode']
            if image_mode == 'show':
                #init
                self.reset_()
                self.select_image_number = output['image_number']
                """
                    Description: 효율적인 연산을 위한 변수 최적화 및 추가, opacity 정보가 반영되도록 코드 수정
                    Modified by MyoungHwan (2024.09.06)
                """
                #rgb iamge, visualization
                self.image_origin = copy.deepcopy(output['image_rgb']) # 원본 이미지, 바뀌지 않음
                self.image_rgb = copy.deepcopy(self.image_origin) # Display 표시용 이미지, 도화지(배경)용으로 주기적으로 바뀜
                self.image_width_origin, self.image_height_origin = self.image_rgb.shape[1], self.image_rgb.shape[0]

                #label infomation
                self.image_label = copy.deepcopy(output['image_label'].astype(int)) # 실제 라벨정보

                #New
                self.image_label_mask_dict = {
                    "show": np.full(self.image_label.shape, False, dtype=np.bool_), #이미지 showing 상태 저장용
                    "mask": np.full(self.image_rgb.shape, 0, dtype=np.uint8), #이미지 저장용
                    "alpha": np.full((self.image_height_origin, self.image_width_origin, 1), 1.0, dtype=np.float16), #이미지 저장용
                }

                #HSI raw
                self.image_raw = copy.deepcopy(output['image_raw'])
                self.image_raw_origin = copy.deepcopy(output['image_raw_origin'])
                self.image_raw_white = copy.deepcopy(output['image_raw_white'])
                self.image_raw_dark = copy.deepcopy(output['image_raw_dark'])
                self.hsi_wave_length = copy.deepcopy(output['hsi_wave_length'])
                self.select_color_bands = copy.deepcopy(output['hsi_default_bands'])
                #graph
                self.image_graph_rgb_label = np.full((2,) + self.image_label.shape, -1) # save graph (graph number, label number)
                self.image_graph_rgb_point = np.full((2,) + self.image_rgb.shape, -1) # for graph view mode (selective, label)
                for label_number in self.label_obj_dict.keys():
                    label_indices = np.where(self.image_label == label_number) 
                    select_color = self.label_obj_dict[label_number]['color']
                    self.image_label_mask_dict['mask'][label_indices] = select_color
                self.display_raw_image()

            elif image_mode == 'unchecked':
                #init
                self.reset_()
                self.default_background.scaled(self.display_scrollAreaWidgetContents.width(),self.display_scrollAreaWidgetContents.height())
                self.display_scrollAreaWidgetContents.initPhoto(self.default_background, dragmode=0, init=True)
                """
                    Description : Return it to the original window if the window is split
                    Author : Hyunsu Kim (2025.10.30)
                    History :
                        1. Modify the if statement to check if the object exists by Hyunsu Kim (2025.12.15)
                """
                if hasattr(self, 'splitter'):
                    self.splitter.setParent(None)
                    self.display_scrollAreaWidgetContents.setParent(self)
                    self.display_gridLayout.addWidget(self.display_scrollAreaWidgetContents, 0, 0, 1, 1)
                    self.display_scrollAreaWidgetContents.show()
        
        elif recv_from == 'label':
            label_mode = output['mode']
            if label_mode == 'hide':
                selected_label_number = output['label_number']
                self.image_label = copy.deepcopy(output['image_label']) # label numpy
                self.select_label_color = self.label_obj_dict[selected_label_number]['color']
                self.update_data_list(label_number=selected_label_number)
                self.update_graph()
                self.update_image_display(self.image_rgb)
            
            elif label_mode =='color':
                selected_label_number = output['label_number']
                self.image_label = copy.deepcopy(output['image_label']) # label numpy
                self.select_label_color = self.label_obj_dict[selected_label_number]['color']
                """
                    @ Description: Update mouse privew color when label color changed (update_mouse_preview)
                    @ History :
                        1. Modified by MyoungHwan (2024.02.05)
                        2. Modified by GaEun Hwang (2025.06.05) : Fixed rectangle's color change bug, when change not selected label color
                """
                if self.label_control_dict['select_main_label_number'] == selected_label_number != LABEL_UNSELECTED:
                    self.update_mouse_preview(change_color=True, color=self.select_label_color)
                    self.display_scrollAreaWidgetContents.init_rect_value(color=self.select_label_color)
                    self.polygonItem.setStyle(QtGui.QColor(*self.select_label_color))
                    
                self.update_data_list(label_number=selected_label_number)
                self.update_graph()
                self.update_image_display(self.image_rgb)

                # display에 있는 graph pointer, graph에 있는 viewer
                indice = np.where(self.image_graph_rgb_label[1] == selected_label_number)
                if indice[0].size:
                    self.image_graph_rgb_point[GRAPH_VIEW_MODE_LABEL_COLOR][indice] = self.select_label_color
                    self.update_graph()
                    self.update_image_display(self.image_rgb)
                    tmp_dict = {}
                    tmp_dict['mode'] = 5
                    tmp_dict['point_list'] = list(zip(*indice))
                    tmp_dict['color'] = self.select_label_color
                    self.display_to_graph(tmp_dict)

            elif label_mode == "number":
                old_label_number = output['old_label_number']
                new_label_number = output['new_label_number']
                """
                    Description: First adding to undo_memory
                    Author : Hyeok Yoon (2025.11.06)
                """
                if len(self.undo_memory) == 0:
                    self.check_diff(mode=0)
                    self.store_current_state()
                    self.add_undo_memory()
                    if old_label_number != 0:
                        self.undo_memory[0]['label'][self.undo_memory[0]['label'] == old_label_number] = 0

                self.image_label = np.where(self.image_label==old_label_number, new_label_number, self.image_label)
                self.image_graph_rgb_label[1] = np.where(self.image_graph_rgb_label[1] == old_label_number, new_label_number, self.image_graph_rgb_label[1])
                """
                    Description: update the labels classe in undo memory when changed the label class
                    Author : Hyeok Yoon (2025.10.17)
                    Modified by Hyeok Yoon (2025.11.06) - Prevent the updating until undo_memory got more than two items
                """
                if len(self.undo_memory) > 1:
                    for _undo_item_index in range(len(self.undo_memory)):
                        self.undo_memory[_undo_item_index]['label'][self.undo_memory[_undo_item_index]['label'] == old_label_number] = new_label_number

            elif label_mode == 'show':
                output_type = output['type']
                if output_type == 'reset':
                    # 라벨 클리어해서 0으로 초기화
                    self.image_label = copy.deepcopy(output['image_label'])
                    self.reset_memory()

                    # 그래프 0으로 변경
                    indice = np.where(self.image_graph_rgb_label[GRAPH_VIEW_MODE_LABEL_COLOR] > 0)
                    self.image_graph_rgb_label[GRAPH_VIEW_MODE_LABEL_COLOR] = 0
                    self.image_graph_rgb_point[GRAPH_VIEW_MODE_LABEL_COLOR][indice] = self.label_obj_dict[0]['color']
                    tmp_dict = {}
                    tmp_dict['mode'] = 5
                    tmp_dict['point_list'] = list(zip(*indice))
                    tmp_dict['color'] = self.label_obj_dict[0]['color']
                    self.display_to_graph(tmp_dict)
                    self.switch_objects(['pen'], enable=True, exclude=True)

                    """
                        Description: 효율적인 연산을 위한 코드 수정
                        Modified by MyoungHwan (2024.09.06)
                    """
                    self.update_data_list(label_number=LABEL_IGNORED)
                    self.update_graph()
                    self.disable_rect_preview()
                    self.disable_polygon_preview()

                elif output_type == 'select_remove':
                    if self.label_control_dict['select_main_label_number'] == LABEL_UNSELECTED:
                        """
                            description: disable rectangle, polygon preview when selected label is removed
                            author: GaEun Hwang (2025.10.30)
                        """
                        self.disable_rect_preview()
                        self.disable_polygon_preview()
                        self.pen_control_dict['pen_control_sw'] = False
                        self.pen_obj_dict['pen_draw_type']['obj'].setChecked(False)
                        self.pen_obj_dict['pen_painting']['obj'].setChecked(False)
                        self.pen_obj_dict['pen_rectangle']['obj'].setChecked(False)
                        self.pen_obj_dict['pen_polygon']['obj'].setChecked(False)
                        self.pen_control_dict['pen_control_sw'] = True

                    #기존 label로 point 찍힌 graph pointer 변경
                    label_number = output['label_number']
                    indice = np.where(self.image_graph_rgb_label[1] == label_number)
                    self.image_graph_rgb_label[1][indice] = 0
                    self.image_graph_rgb_point[GRAPH_VIEW_MODE_LABEL_COLOR][indice] = self.label_obj_dict[0]['color']
                    tmp_dict = {}
                    tmp_dict['mode'] = 5
                    tmp_dict['point_list'] = list(zip(*indice))
                    tmp_dict['color'] = self.label_obj_dict[0]['color']
                    self.display_to_graph(tmp_dict)

                    # 라벨 클리어해서 0으로 초기화
                    self.image_label = copy.deepcopy(output['image_label'])
                    self.update_data_list(label_number=LABEL_IGNORED)
                    self.update_graph()
                    """
                        Description: remove labels in undo redo memory when specific label deleted
                        Author : Hyeok Yoon (2025.10.27)
                    """
                    self.remove_undo_memory(label_number) # undo
                    self.remove_redo_memory(label_number) # redo
                    self.update_pen_buttons() # update button status

                self.update_image_display(self.image_rgb)

            elif label_mode == 'status':
                # 라벨선택시 발동
                self.display_control_dict['old_drawing_mode'] = self.display_control_dict['drawing_mode']
                prev_drawing_mode = self.display_control_dict['old_drawing_mode']
                # init rect, polygon preview when label is selected
                self.disable_rect_preview()
                self.disable_polygon_preview()

                if self.label_control_dict['select_main_label_number'] != LABEL_UNSELECTED: # 라벨 선택되었을 때
                    cur_label = self.label_control_dict['select_main_label_number']
                    self.update_mouse_preview(change_color=True, color=self.label_obj_dict[cur_label]['color'])
                    self.switch_objects(['pen'], enable=True, exclude=True)
                    self.polygonItem.setStyle(QtGui.QColor(*self.label_obj_dict[cur_label]['color']))
                    #현재 드로잉모드가 라벨링(0) 또는 페인팅(6)일 때 무시
                    self.pen_control_dict['pen_control_sw'] = False
                    cur_drawing_mode = self.display_control_dict['drawing_mode']
                    if cur_drawing_mode in [DRAWING_MODE_LABELING, DRAWING_MODE_NONE]:
                        self.display_control_dict['drawing_mode'] = DRAWING_MODE_LABELING
                        self.pen_obj_dict['pen_draw_type']['obj'].setChecked(True)

                    elif cur_drawing_mode == DRAWING_MODE_PAINTING:
                        """
                            description: modifiy '==' operator to '='
                            modified by GaEun Hwang 2025.08.27
                        """
                        self.display_control_dict['drawing_mode'] = DRAWING_MODE_PAINTING
                        self.pen_obj_dict['pen_painting']['obj'].setChecked(True)

                    elif cur_drawing_mode == DRAWING_MODE_RECTANGLE:
                        self.display_control_dict['drawing_mode'] = DRAWING_MODE_RECTANGLE
                        self.pen_obj_dict['pen_rectangle']['obj'].setChecked(True)

                    elif cur_drawing_mode == DRAWING_MODE_POLYGON:
                        self.display_control_dict['drawing_mode'] = DRAWING_MODE_POLYGON
                        self.pen_obj_dict['pen_polygon']['obj'].setChecked(True)

                    else:
                        if prev_drawing_mode in [DRAWING_MODE_LABELING, DRAWING_MODE_DRAW_GRAPH_POINT, DRAWING_MODE_ERASE_GRAPH_POINT]:
                            self.display_control_dict['drawing_mode'] = DRAWING_MODE_LABELING
                            self.pen_obj_dict['pen_draw_type']['obj'].setChecked(True)
                            """
                                description: Bug the graph pen is not unchecked when graph pen is checked and label is selected
                                Fixed by GaEun Hwang 2025.08.27
                            """
                            self.switch_objects(['graph'], enable=False, exclude=True)
                            self.switch_objects(['graph'], enable=True, exclude=True)

                        elif prev_drawing_mode == DRAWING_MODE_PAINTING:
                            self.display_control_dict['drawing_mode'] = DRAWING_MODE_PAINTING
                            self.pen_obj_dict['pen_painting']['obj'].setChecked(True)
                        
                        elif prev_drawing_mode == DRAWING_MODE_RECTANGLE:
                            self.display_control_dict['drawing_mode'] = DRAWING_MODE_RECTANGLE
                            self.pen_obj_dict['pen_rectangle']['obj'].setChecked(True)

                        elif prev_drawing_mode == DRAWING_MODE_POLYGON:
                            self.display_control_dict['drawing_mode'] = DRAWING_MODE_POLYGON
                            self.pen_obj_dict['pen_polygon']['obj'].setChecked(True)

                        self.pen_obj_dict['pen_eraser']['obj'].setChecked(False)
                    self.pen_control_dict['pen_control_sw'] = True

                else: # 라벨 선택 해제 되었을 때
                    self.update_mouse_preview(change_color=True)
                    self.disable_polygon_preview()
                    self.display_control_dict['drawing_mode'] = DRAWING_MODE_NONE
                    # self.display_scrollAreaWidgetContents.updateDrag(True)
                    self.pen_control_dict['pen_control_sw'] = False
                    self.pen_obj_dict['pen_draw_type']['obj'].setChecked(False)
                    self.pen_obj_dict['pen_painting']['obj'].setChecked(False)
                    self.pen_obj_dict['pen_eraser']['obj'].setChecked(False)
                    self.pen_obj_dict['pen_rectangle']['obj'].setChecked(False)
                    self.pen_obj_dict['pen_polygon']['obj'].setChecked(False)
                    self.pen_control_dict['pen_control_sw'] = True

            elif label_mode == 'all_hide_show':
                toggle = output['toggle']
                # Show All Label
                if toggle:
                    """
                        Description: opacity 정보가 반영되도록 코드 수정
                        Modified by MyoungHwan (2024.09.06)
                    """
                    mask_image = self.image_label_mask_dict['mask']
                    alpha_ratio = self.image_label_mask_dict['alpha']
                    tmp_image_rgb = (mask_image.astype(float) * alpha_ratio) + ( (1-alpha_ratio) * self.image_origin.astype(float))
                    self.image_rgb = tmp_image_rgb.astype(np.uint8)
                    self.image_label_mask_dict['show'][::] = True
                # HIde All Label
                else:
                    self.image_rgb = copy.deepcopy(self.image_origin)
                    self.image_label_mask_dict['show'][::] = False
                self.update_graph()
                self.update_image_display(self.image_rgb)

        elif recv_from == "graphGroup":
            mode = output['mode']
            if mode == GRAPH_GROUP_SELECT:
                # if graph group is selected, change to graph drawing mode
                if self.graph_obj_dict['graph_check']['obj'].isChecked():
                    self.display_control_dict['drawing_mode'] = DRAWING_MODE_DRAW_GRAPH_POINT
                elif self.graph_obj_dict['graph_eraser']['obj'].isChecked():
                    self.display_control_dict['drawing_mode'] = DRAWING_MODE_ERASE_GRAPH_POINT
                self.label_control_dict['old_select_label_number'] = self.label_control_dict['select_main_label_number']
                self.label_control_dict['select_main_label_number'] = LABEL_UNSELECTED
                self.switch_objects(['pen', 'label'], enable=False, exclude=True)
                self.switch_objects(['pen'], enable=True, exclude=False)
            
            elif mode == GRAPH_DISPLAY_PARTIAL:
                # Hide/Show partial graph group
                graphGroupIdx = output['index']
                view = output['view']
                self.hide_graph(partial=True, index=graphGroupIdx, labelView=(view=="label"))
                self.update_image_display(self.image_rgb)

            elif mode == GRAPH_DISPLAY_ALL:
                # Hide/Show all graph group
                hideState = output['hideState']
                view = output['view']
                self.hide_graph(partial=False, hideState=hideState, labelView=(view=="label"))
                self.update_image_display(self.image_rgb)
            
            elif mode == GRAPH_GROUP_COLOR_CHANGE:
                # Change color of graph group
                graphGroupIdx = output['index']
                indice = np.where(self.image_graph_rgb_label[GRAPH_VIEW_MODE_SELECTIVE_COLOR] == graphGroupIdx)
                self.image_graph_rgb_point[GRAPH_VIEW_MODE_SELECTIVE_COLOR][indice] = self.graphGroupDict[graphGroupIdx]["color"]
                self.update_graph()
                self.update_image_display(self.image_rgb)
            
            elif mode == GRAPH_GROUP_REMOVE:
                # remove graph group number from image_graph_rgb_label and image_graph_rgb_point
                graphGroupIdx = output['index']
                
                indice = np.where(self.image_graph_rgb_label[GRAPH_VIEW_MODE_SELECTIVE_COLOR] == graphGroupIdx)
                self.image_graph_rgb_label[GRAPH_VIEW_MODE_SELECTIVE_COLOR][indice] = GRAPH_PRESENT_NONE
                self.image_graph_rgb_label[GRAPH_VIEW_MODE_LABEL_COLOR][indice] = GRAPH_PRESENT_NONE
                self.image_graph_rgb_point[GRAPH_VIEW_MODE_SELECTIVE_COLOR][indice] = GRAPH_PRESENT_NONE
                self.image_graph_rgb_point[GRAPH_VIEW_MODE_LABEL_COLOR][indice] = GRAPH_PRESENT_NONE

                labelHideState = self.image_label_mask_dict['show'][indice]
                maskImage = self.image_label_mask_dict['mask'][indice]
                alphaRatio = self.image_label_mask_dict['alpha'][indice]
                rgbValue = (maskImage.astype(float) * alphaRatio) + ((1 - alphaRatio) * self.image_origin[indice].astype(float))
                self.image_rgb[indice] = np.where(np.expand_dims(labelHideState, axis=-1), rgbValue, self.image_origin[indice])

                self.update_image_display(self.image_rgb)
            
            elif mode == GRAPH_GROUP_REMOVE_ALL:
                # remove all graph group number from image_graph_rgb_label and image_graph_rgb_point
                indice = np.where(self.image_graph_rgb_label[GRAPH_VIEW_MODE_SELECTIVE_COLOR] != GRAPH_PRESENT_NONE)
                
                labelHideState = self.image_label_mask_dict['show'][indice]
                maskImage = self.image_label_mask_dict['mask'][indice]
                alphaRatio = self.image_label_mask_dict['alpha'][indice]
                rgbValue = (maskImage.astype(float) * alphaRatio) + ((1 - alphaRatio) * self.image_origin[indice].astype(float))
                self.image_rgb[indice] = np.where(np.expand_dims(labelHideState, axis=-1), rgbValue, self.image_origin[indice])

                self.image_graph_rgb_label = np.full((2,) + self.image_label.shape, -1)
                self.image_graph_rgb_point = np.full((2,) + self.image_rgb.shape, -1)
                self.update_image_display(self.image_rgb)

            elif mode == GRAPH_GROUP_CONVERT_LABEL_VIEW:
                # convert graph view mode from selective to label
                self.tempGraphIndex = output['tempGraphIndex']
                self.tempColor = output['tempColor']
                indice = np.where(self.image_graph_rgb_label[GRAPH_VIEW_MODE_SELECTIVE_COLOR] != GRAPH_PRESENT_NONE)
                self.image_rgb[indice] = self.image_graph_rgb_point[GRAPH_VIEW_MODE_LABEL_COLOR][indice]
                self.update_image_display(self.image_rgb)

            elif mode == GRAPH_GROUP_CONVERT_SELECTIVE_VIEW:
                # convert graph view mode from label to selective
                indice = np.where(self.image_graph_rgb_label[GRAPH_VIEW_MODE_LABEL_COLOR] != GRAPH_PRESENT_NONE)
                self.image_rgb[indice] = self.image_graph_rgb_point[GRAPH_VIEW_MODE_SELECTIVE_COLOR][indice]
                self.update_image_display(self.image_rgb)

        elif recv_from == 'graph':
            self.display_control_dict['old_drawing_mode'] = self.display_control_dict['drawing_mode']
            output_type = output['type']
            """
                description: disable rectangle, polygon preview when graph mode(draw, erase) changed
                author: GaEun Hwang (2025.10.30)
            """
            if output_type == "draw":
                self.display_control_dict['drawing_mode'] = DRAWING_MODE_DRAW_GRAPH_POINT
                """
                    description: allocate select_main_label_number and old_select_label_number in graph group was selected
                    modified by GaEun Hwang 2025.12.08
                """
                self.disable_rect_preview()
                self.disable_polygon_preview()
                self.switch_objects(['pen', 'label'], enable=False, exclude=True)
                self.switch_objects(['pen'], enable=True, exclude=False)

            elif output_type == "erase":
                self.display_control_dict['drawing_mode'] = DRAWING_MODE_ERASE_GRAPH_POINT
                """
                    description: allocate select_main_label_number and old_select_label_number in graph group was selected
                    modified by GaEun Hwang 2025.12.08
                """
                self.disable_rect_preview()
                self.disable_polygon_preview()
                self.switch_objects(['pen', 'label'], enable=False, exclude=True)
                self.switch_objects(['pen'], enable=True, exclude=False)

            elif output_type == "None":
                self.display_control_dict['drawing_mode'] = DRAWING_MODE_NONE

            elif output_type == "clear":
                #클리어 모드일 경우, 화면에 존재하는 graph point list 모두 초기화                
                self.hide_graph()
                self.image_graph_rgb_label = np.full((2,) + self.image_label.shape, -1)
                self.image_graph_rgb_point = np.full((2,) + self.image_rgb.shape, -1)
                #DB clear
                tmp_dict = {}
                tmp_dict['mode'] = 'delete'
                tmp_dict['type'] = 'display'
                tmp_dict['select_type'] = 'graph_data'
                tmp_dict['type_detail'] = 'all'
                self.display_to_core(tmp_dict)
                #image updatef
                self.update_image_display(self.image_rgb)

                """
                    추가예정
                """
                # self.display_scrollAreaWidgetContents.clear_scene()
                # self.display_scrollAreaWidgetContents.add_scene()
                # self.display_scene_cnt = 0


            elif output_type == "checked":
                """
                    Description: 현재사용안함, graph point select option
                    Modified by MyoungHwan (2024.09.06)
                """
                pass
                # select_graph_number = output['number']
                # indice = np.where(self.image_graph_rgb_label[0] == select_graph_number)
                # tmp_color = self.image_graph_rgb_point[self.graph_control_dict['graph_view_mode']][indice]
                # if self.graph_obj_dict['graph_hide']['obj'].isChecked():
                #     self.image_rgb[indice] = tmp_color
                #     self.image_label_mask_dict["show"][indice] = True
                # self.update_image_display(self.image_rgb)

            elif output_type == "unchecked":
                """
                    Description: 현재사용안함, graph point select option
                    Modified by MyoungHwan (2024.09.06)
                """
                pass
                # select_graph_number = output['number']
                # indice = np.where(self.image_graph_rgb_label[0] == select_graph_number)
                # label_number = self.image_label[indice][0]
                # tmp_color = self.label_obj_dict[label_number]['color']
                # if self.label_obj_dict[label_number]['hide'].isChecked():
                #     self.image_rgb[indice] = tmp_color
                #     self.image_label_mask_dict["show"][indice] = True
                # else:
                #     self.image_rgb[indice] = self.image_origin[indice]
                #     self.image_label_mask_dict["show"][indice] = False
                # self.update_image_display(self.image_rgb)

            elif output_type == "all_select":
                checked = output['checked']
                if checked: # all check 시 모두 보여지게
                    self.update_graph()
                else: #all check 해제시 모두 숨겨지게
                    self.hide_graph()
                self.update_image_display(self.image_rgb)

            elif output_type == "select_delete":
                select_graph_number = output['number']
                indice = np.where(self.image_graph_rgb_label[0] == select_graph_number)
                self.image_graph_rgb_label[0][indice] = -1
                self.image_graph_rgb_point[self.graph_control_dict['graph_view_mode']][indice] = [-1,-1,-1]
                label_number = self.image_label[indice][0]
                tmp_color = self.label_obj_dict[label_number]['color']
                """
                    Description: 효율적인 연산을 위한 코드 수정
                    Modified by MyoungHwan (2024.09.06)
                """
                # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                if self.label_obj_dict[label_number]['obj_dict']['show'].isChecked():
                    self.image_rgb[indice] = tmp_color
                    self.image_label_mask_dict['show'][indice] = True
                else:
                    self.image_rgb[indice] = self.image_origin[indice]
                    self.image_label_mask_dict['show'][indice] = False
                tmp_dict = {}
                tmp_dict['mode'] = 'delete'
                tmp_dict['type'] = 'display'
                tmp_dict['select_type'] = 'graph_data'
                tmp_dict['type_detail'] = 'one'
                tmp_dict['point_info'] = indice
                self.display_to_core(tmp_dict)
                self.update_image_display(self.image_rgb)
           
        elif recv_from == 'graph_sub':
            visualization_mode = output['mode']
            if visualization_mode == VISUALIZATION_MODE_CALIBRATION: # calibration mode 
                is_calibration_enabled = output['_type']
                calibrtion_ratio = output['value']
                if is_calibration_enabled: # calibration apply 
                    self.image_raw = ((self.image_raw_origin-self.image_raw_dark)/(self.image_raw_white-self.image_raw_dark))
                    self.image_raw = np.array(np.clip(calibrtion_ratio*self.image_raw*4095.0, 0, 4095), dtype=np.float32)
                else: # calibration mode off, only visualize raw data
                    self.image_raw = copy.deepcopy(self.image_raw_origin)
            elif visualization_mode == VISUALIZATION_MODE_ADVANCED: # advanced mode(norm visualization)
                #현재 이미지에서 norm 처리
                is_advanced_mode_enabled = output['_type']
                calibrtion_ratio = output['value']
                is_calibration_enabled = output['calib_mode']
                if is_advanced_mode_enabled: # norm visualization mode on
                    norm = np.linalg.norm(self.image_raw, axis=2)
                    norm = np.expand_dims(norm, axis=2)
                    self.image_raw = self.image_raw / norm  * 4095.0 * 10
                else: # norm visualization mode off, show before data
                    if is_calibration_enabled:
                        self.image_raw = ((self.image_raw_origin-self.image_raw_dark)/(self.image_raw_white-self.image_raw_dark))
                        self.image_raw = np.array(np.clip(calibrtion_ratio*self.image_raw*4095.0, 0, 4095), dtype=np.float32)
                    else:
                        self.image_raw = copy.deepcopy(self.image_raw_origin)
            red = self.image_raw[:,:,self.select_color_bands[0]]  /4095.0
            green = self.image_raw[:,:,self.select_color_bands[1]] / 4095.0 
            blue = self.image_raw[:,:,self.select_color_bands[2]] / 4095.0
            self.image_rgb = (np.array([red,green,blue]).transpose((1,2,0)) * 255).astype(np.uint8).copy()
            self.image_origin = copy.deepcopy(self.image_rgb)
            """
                Description: opacity 정보가 반영되도록 코드 수정
                Modified by MyoungHwan (2024.09.06)
            """
            indice = np.where(self.image_label_mask_dict['show'] == True) #-1이 아닌부분의 경우 showing되어지고 있는부분임, 그 영역들을 찾는다
            mask_image = self.image_label_mask_dict['mask'][indice]
            alpha_ratio = self.image_label_mask_dict['alpha'][indice]
            tmp_image_rgb = (mask_image.astype(float) * alpha_ratio) + ( (1-alpha_ratio) * self.image_origin[indice].astype(float))
            self.image_rgb[indice] = tmp_image_rgb.astype(np.uint8)
            self.update_graph()
            self.update_image_display(self.image_rgb)

        elif recv_from == 'pen':
            self.display_control_dict['old_drawing_mode'] = self.display_control_dict['drawing_mode']
            pen_mode = output['pen_mode']
            toggle = output['toggle']
            file_path = output['image_path'] if 'image_path' in output.keys() else None
            image_path = None

            if pen_mode not in [PEN_MODE_ZOOM_IN, PEN_MODE_ZOOM_OUT]:
                # disable rect, polygon preview when pen mode is not rectangle, polygon, zoom in, zoom out
                self.disable_rect_preview()
                if pen_mode not in [PEN_MODE_UNDO, PEN_MODE_REDO]:
                    self.disable_polygon_preview()

            if pen_mode not in [PEN_MODE_ZOOM_IN, PEN_MODE_ZOOM_OUT, PEN_MODE_BRIGHT, PEN_MODE_UNDO, PEN_MODE_REDO]:
                self.switch_objects(['graph'], enable=False, exclude=True)
                self.switch_objects(['graph'], enable=True, exclude=True)
            
            if pen_mode == PEN_MODE_POLYGON:
                pass

            #scale up
            if pen_mode == PEN_MODE_ZOOM_IN:
                print("image scale up")
                """
                    description: Fix bug not changed pen activation when zoom in and zoom out 
                    author: GaEun Hwang (2025.10.23)
                """
                if self.display_control_dict['drawing_mode'] == DRAWING_MODE_RECTANGLE:
                    self.pen_obj_dict['pen_rectangle']['obj'].setChecked(True)
                elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_POLYGON:
                    self.pen_obj_dict['pen_polygon']['obj'].setChecked(True)
                elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_LABELING:
                    self.pen_obj_dict['pen_draw_type']['obj'].setChecked(True)
                elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_ERASING:
                    self.pen_obj_dict['pen_eraser']['obj'].setChecked(True)
                elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_PAINTING:
                    self.pen_obj_dict['pen_painting']['obj'].setChecked(True)
                self.display_scrollAreaWidgetContents._modscale(mode=0)
            
            #scale down
            elif pen_mode == PEN_MODE_ZOOM_OUT:
                print("image scale down")
                if self.display_control_dict['drawing_mode'] == DRAWING_MODE_RECTANGLE:
                    self.pen_obj_dict['pen_rectangle']['obj'].setChecked(True)
                elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_POLYGON:
                    self.pen_obj_dict['pen_polygon']['obj'].setChecked(True)
                elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_LABELING:
                    self.pen_obj_dict['pen_draw_type']['obj'].setChecked(True)
                elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_ERASING:
                    self.pen_obj_dict['pen_eraser']['obj'].setChecked(True)
                elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_PAINTING:
                    self.pen_obj_dict['pen_painting']['obj'].setChecked(True)
                self.display_scrollAreaWidgetContents._modscale(mode=1)

            elif pen_mode == PEN_MODE_PARTIAL_ZOOM:
                # part scale mode
                print("part scale mode")
                if toggle :
                    self.display_control_dict['drawing_mode'] = switch_pen_to_draw(pen_mode)
                    self.label_control_dict['old_select_label_number'] = self.label_control_dict['select_main_label_number']
                    self.label_control_dict['select_main_label_number'] = LABEL_UNSELECTED
                    self.switch_objects(['label', 'graph'], enable=False, exclude=True)
                else:
                    self.display_control_dict['drawing_mode'] = DRAWING_MODE_NONE
                    self.update_image_display(self.image_rgb)
            elif pen_mode in [PEN_MODE_DRAWING, PEN_MODE_PAINTING, PEN_MODE_RECTANGLE, PEN_MODE_POLYGON]:
                #drawing mode
                print("drawing mode")
                if toggle:
                    self.display_control_dict['drawing_mode'] = switch_pen_to_draw(pen_mode)
                    # 이전에 마지막으로 선택한 라벨을 다시 선택
                    if self.label_control_dict['select_main_label_number'] == LABEL_UNSELECTED:
                        if self.label_control_dict['old_select_label_number'] in list(self.label_obj_dict.keys()):
                            self.label_control_dict['select_main_label_number'] = self.label_control_dict['old_select_label_number']
                        else:
                            self.label_control_dict['select_main_label_number'] = sorted(list(self.label_obj_dict.keys()))[0]
                        self.label_control_dict['label_control_sw'] = False
                        # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                        self.label_obj_dict[self.label_control_dict['select_main_label_number']]['obj_dict']['select'].setChecked(True)
                        self.label_control_dict['label_control_sw'] = True
                    emitDict = {}
                    emitDict['mode'] = SELECT_LABEL_PEN
                    self.displayToGraphGroupSignal.emit(emitDict)
                else:
                    self.display_control_dict['drawing_mode'] = DRAWING_MODE_NONE
                    self.label_control_dict['old_select_label_number'] = self.label_control_dict['select_main_label_number']
                    self.label_control_dict['select_main_label_number'] = LABEL_UNSELECTED
                    self.switch_objects(['label'], enable=False, exclude=True)
                
                if pen_mode == PEN_MODE_DRAWING:
                    tmp_dict = {}
                    tmp_dict['mode'] = 'select'
                    tmp_dict['type'] = 'main'
                    self.display_to_pen_style(tmp_dict)
            elif pen_mode == PEN_MODE_IMAGE_MOVING:
                print("part move")
                if toggle:
                    self.display_control_dict['drawing_mode'] = switch_pen_to_draw(pen_mode)
                else:
                    self.display_control_dict['drawing_mode'] = DRAWING_MODE_NONE
            elif pen_mode == PEN_MODE_ERASER:
                #erase
                print("eraser mode")
                if toggle:
                    self.display_control_dict['drawing_mode'] = switch_pen_to_draw(pen_mode)
                    self.label_control_dict['label_control_sw'] = False
                    self.switch_objects(['label'], enable=False, exclude=False)
                    self.label_control_dict['label_control_sw'] = True
                    self.label_control_dict['old_select_label_number'] = self.label_control_dict['select_main_label_number']
                    self.label_control_dict['select_main_label_number'] = LABEL_UNSELECTED
                    emitDict = {}
                    emitDict['mode'] = SELECT_LABEL_PEN
                    self.displayToGraphGroupSignal.emit(emitDict)
                else:
                    self.display_control_dict['drawing_mode'] = DRAWING_MODE_NONE
                
                tmp_dict = {}
                tmp_dict['mode'] = 'select'
                tmp_dict['type'] = 'main'
                self.display_to_pen_style(tmp_dict)
            elif pen_mode == PEN_MODE_BRIGHT:
                #bright
                pass
            elif pen_mode == PEN_MODE_UNDO:
                #undo
                # if Polygon drawing, process polygon undo first
                if self.polygonItem.isDrawing == True:
                    self.polygonItem.setUndo()
                    self.update_pen_buttons()
                    return
                
                if self.undo_memory:
                    # depending on polygon drawing mode, check diff mode
                    self.check_diff(mode=0)
                    self.store_current_state()
                    self.add_redo_memory()
                    self.pop_undo_memory()
                    
            elif pen_mode == PEN_MODE_REDO:
                #redo
                # # if Polygon drawing, process polygon redo first
                if self.polygonItem.isDrawing == True:
                    self.polygonItem.setRedo()
                    self.update_pen_buttons()
                    return
                
                if self.redo_memory:
                    # depending on polygon drawing mode, check diff mode
                    self.check_diff(mode=0)
                    self.store_current_state()
                    self.add_undo_memory()
                    self.pop_redo_memory()

            elif pen_mode == PEN_MODE_ROT90:
                self.display_scrollAreaWidgetContents.rotate_viewer(angle=90, clock_wise=True)
            elif pen_mode == PEN_MODE_HFLIP:
                self.display_scrollAreaWidgetContents.flip_horizontal()
            elif pen_mode == PEN_MODE_VFLIP:
                self.display_scrollAreaWidgetContents.flip_vertical()
            elif pen_mode == PEN_MODE_IMAGE:
                """
                    Description: Load image when image path exists
                    Author : Hyunsu Kim (2025.10.30)
                """
                if toggle == False:
                    self.splitter.setParent(None)
                    self.display_scrollAreaWidgetContents.setParent(self)
                    self.display_gridLayout.addWidget(self.display_scrollAreaWidgetContents, 0, 0, 1, 1)
                    self.display_scrollAreaWidgetContents.show()
                    self.pen_obj_dict['pen_image']['obj'].setChecked(False)
                else:
                    imageCount = 0
                    for file in os.listdir(file_path):
                        if file.endswith(('.tif', '.tiff', '.png', '.jpg', '.jpeg', '.bmp')):
                            if file.split('.')[0] != "image" and file.split('.')[0] != "image_calibration":
                                image_path = os.path.join(file_path, file)
                                imageCount +=1
                    if imageCount > 1:
                        msgBox = QMessageBox()
                        msgBox.setStandardButtons(QMessageBox.Ok)
                        msgBox.setIcon(QMessageBox.Warning)
                        msgBox.setWindowTitle("Warning")
                        msgBox.setText("Multiple image files detected in the folder. Please ensure only one image file.")
                        msgBox.exec_()
                        self.pen_obj_dict['pen_image']['obj'].setChecked(False)
                        return
                    if image_path is not None:
                        self.LoadImage(self, path=image_path)
                    else:
                        msgBox = QMessageBox()
                        msgBox.setStandardButtons(QMessageBox.Ok)
                        msgBox.setIcon(QMessageBox.Warning)
                        msgBox.setWindowTitle("Warning")
                        msgBox.setText("Image path is None!")
                        msgBox.exec_()
                        self.pen_obj_dict['pen_image']['obj'].setChecked(False)

        elif recv_from == 'pen_sub':
            output_type = output['type']
            if output_type == 'style':
                # self.pen_drawing_type = output['pen_drawing_type']
                pass
            elif output_type == 'eraser':
                pass
            elif output_type == 'sub_label':
                self.label_control_dict['select_sub_label_number'] = output['sub_label_number']
        elif recv_from == 'pen_opacity':
            mode = output['mode']
            if mode =='opacity':
                label_list = output['label_list']
                for label_number in label_list:
                    self.update_data_list(label_number=label_number)
                self.update_graph()

            elif mode == "preview_global":
                alpha_ratio = output["value"]
                mask_image = self.image_label_mask_dict['mask']
                tmp_image_rgb = (mask_image.astype(float) * alpha_ratio) + ( (1-alpha_ratio) * self.image_origin.astype(float))
                self.image_rgb = tmp_image_rgb.astype(np.uint8)

            elif mode == "preview_specific":
                label_number = output['label_list']
                alpha_ratio = output["value"]
                indice = np.where(self.image_label == label_number)
                mask_image = self.image_label_mask_dict['mask'][indice]
                tmp_image_rgb = (mask_image.astype(float) * alpha_ratio) + ( (1-alpha_ratio) * self.image_origin[indice].astype(float))
                self.image_rgb[indice] = tmp_image_rgb.astype(np.uint8)

            elif mode == "close":
                # Modified by MyoungHwan(2025.03.14): label opacity preview 조정 후 close 시 reset이 안되는 현상 수정
                self.image_rgb = copy.deepcopy(self.image_origin)
                indice = np.where(self.image_label_mask_dict['show'] == True) #-1이 아닌부분의 경우 showing되어지고 있는부분임, 그 영역들을 찾는다
                if len(indice[0]):
                    mask_image = self.image_label_mask_dict['mask'][indice]
                    alpha_ratio = self.image_label_mask_dict['alpha'][indice]
                    tmp_image_rgb = (mask_image.astype(float) * alpha_ratio) + ( (1-alpha_ratio) * self.image_origin[indice].astype(float))
                    self.image_rgb[indice] = tmp_image_rgb.astype(np.uint8)
                self.update_graph()

            self.update_image_display(self.image_rgb)
        elif recv_from == 'display_sub_rgb_change':
            view_mode = output['mode']
            if view_mode == VIEW_TYPE_RGB: #slider or combobox change
                self.select_color_bands = copy.deepcopy(output['select_color_bands'])
                red = self.image_raw[:,:,self.select_color_bands[0]]  /4095.0
                green = self.image_raw[:,:,self.select_color_bands[1]] / 4095.0 
                blue = self.image_raw[:,:,self.select_color_bands[2]] / 4095.0
                self.image_rgb = (np.array([red,green,blue]).transpose((1,2,0)) * 255).astype(np.uint8).copy()
            elif view_mode == VIEW_TYPE_CMF:
                self.image_rgb = CMFRGB(self.image_raw, self.hsi_wave_length)
            elif view_mode == VIEW_TYPE_DL:
                self.image_rgb = DLRGB(self.image_raw, self.hsi_wave_length)

            self.image_origin = copy.deepcopy(self.image_rgb)
            """
                Description: opacity 정보가 반영되도록 코드 수정
                Modified by MyoungHwan (2024.09.06)
            """
            indice = np.where(self.image_label_mask_dict['show'] == True) #-1이 아닌부분의 경우 showing되어지고 있는부분임, 그 영역들을 찾는다
            mask_image = self.image_label_mask_dict['mask'][indice]
            alpha_ratio = self.image_label_mask_dict['alpha'][indice]
            tmp_image_rgb = (mask_image.astype(float) * alpha_ratio) + ( (1-alpha_ratio) * self.image_origin[indice].astype(float))
            self.image_rgb[indice] = tmp_image_rgb.astype(np.uint8)
            self.update_graph()
            self.update_image_display(self.image_rgb)

        else:
            print("Exception recv_from:", output['from'])

    def focus_changed(self):
        """
            @Description: Display 외 focus 전환에 따른 Keypress 예외처리 추가
            @Author: MyoungHwan(2025.03.14)
        """
        if self.core_obj_dict["cur_focus_widget"] != "Display_viewer":
            if self.display_control_dict['key_pressed']:
                self.is_ctrl_key_pressed = False
                self.display_control_dict['drawing_mode'] = self.display_control_dict['temp_drawing_mode']
                self.display_control_dict['temp_drawing_mode'] = DRAWING_MODE_NONE
                self.display_scrollAreaWidgetContents.updateDrag(False)
                self.display_control_dict['key_pressed'] = False

    def init(self, Sync=None, lang=None):
        """
            @description : Diplay 초기 선언 시 시그널 선언문이다. 각종 시그널들이 이곳에서 선언된다.
            @author : MyoungHwan                
            @parameters
                1.	Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스
        """
        self.lang = lang
        self.Sync = Sync
        # signal
        self.core_to_display_signal = self.Sync.core_to_display_signal
        self.core_to_display_signal.connect(self.recv_from_core)
        self.display_to_core_signal = self.Sync.display_to_core_signal
        self.display_to_labeling_mode_main_signal = self.Sync.display_to_labeling_mode_main_signal
        self.display_to_graph_signal = self.Sync.display_to_graph_signal
        self.displayToGraphGroupSignal = self.Sync.displayToGraphGroupSignal
        self.display_to_pen_style_signal = self.Sync.display_to_pen_style_signal

        #function object 항목, UI의 위젯 제어시 사용
        self.core_obj_dict = self.Sync.core_obj_dict
        self.label_obj_dict = self.Sync.label_obj_dict
        self.pen_obj_dict = self.Sync.pen_obj_dict
        self.graph_obj_dict = self.Sync.graph_obj_dict

        self.display_control_dict = self.Sync.display_control_dict
        self.image_control_dict = self.Sync.image_control_dict
        self.label_control_dict = self.Sync.label_control_dict
        self.graph_control_dict = self.Sync.graph_control_dict
        self.graphGroupDict = self.Sync.graphGroupDict
        self.labelViewGraphGroupDict = self.Sync.labelViewGraphGroupDict
        self.pen_control_dict = self.Sync.pen_control_dict

    def init_variable(self):
        """Diplay 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
        """
        # 주기적으로 업데이트되는 정보
        self.select_image_number = IMAGE_UNSELECTED
        self.label_control_dict['select_main_label_number'] = LABEL_UNSELECTED
        self.label_control_dict['select_sub_label_number'] = LABEL_UNSELECTED
        self.select_color_bands = []
        self.select_label_color = []
        self.display_control_dict['drawing_mode'] = DRAWING_MODE_NONE
        self.display_control_dict['old_drawing_mode'] = DRAWING_MODE_NONE
        self.label_control_dict['old_select_label_number'] = LABEL_UNSELECTED
        self.pen_drawing_type = 0
        self.sub_window_sw = False
        self.prev_point = []

        #data information
        self.image_rgb = []
        self.image_raw = []
        self.image_raw_origin = []
        self.image_raw_white = []
        self.image_raw_dark = []
        self.image_label = []
        self.image_origin = []
        self.image_width_origin = 0
        self.image_height_origin = 0
        self.image_width_list = []
        self.image_height_list = []
        self.hsi_wave_length = []

        #memory setup
        self.reset_memory()

        #image scale count
        self.count = 1
        
        # mouse point
        self.x, self.y, self.old_x, self.old_y = 0, 0, 0, 0
        self.cal_x, self.cal_y = 0, 0
        self.cal_start_x, self.cal_start_y, self.cal_end_x, self.cal_end_y = 0, 0, 0, 0
        #mouse drag sw
        self.left_drawstart = False
        self.right_drawstart = False

        #pre-marking
        self.mark_sw = False

        # cursor tracking        
        self.preview_cursor = None
        self.preview_cursor_color_alpha = 100
        self.preview_cursor_color = QtGui.QColor(255,0,0,self.preview_cursor_color_alpha)
        self.preview_cursor_pen = QtGui.QPen(self.preview_cursor_color, 0.2)
        self.preview_cursor_pen_rad = 1

        self.tempGraphIndex = None
        self.tempColor = None
        
        """
            추가예정
        """
        # self.display_scene_cnt = 0

        #graph information
        self.image_graph_rgb_label = []
        self.image_graph_rgb_point = []

        #graph list clear
        for obj_name in list(self.graph_obj_dict.keys()):
            if obj_name not in ["graph_color"]:
                self.graph_obj_dict[obj_name]['obj'].setChecked(False)
            
        self.clear_graph_list()
        # clear LDA graph for initialization
        self.clearLDAGraph()

        # control key pressed
        self.is_ctrl_key_pressed = False

        #update init exclude list
        self.excluded_pen_objs = ['pen_undo', 'pen_redo']
        self.excluded_graph_objs = ['graph_linedrawing', 'graph_color', 'graph_view_mode']
        self.excluded_label_objs = []

        # polygon information
        self.polygonItem = customPolygonItem()
        self.polygonPainter = QtGui.QPainter()
        self.isSnapped = False # variable to check whether cursor is snapped to polygon point
        self.polygonInsidePoints = [] # if polygon is completed, this variable stores the points inside the polygon

    def reset_(self) -> None:
        print("reset_status")
        self.init_variable()
        # if drawing mode is on, remove polygon preview before reset
        for obj_name in list(self.pen_obj_dict.keys()):
            if obj_name not in self.excluded_pen_objs:
                self.pen_obj_dict[obj_name]['obj'].setEnabled(True)
        self.display_scrollAreaWidgetContents.reset_view()
        self.display_scrollAreaWidgetContents.clear_scene()
        self.display_scrollAreaWidgetContents.add_scene()
        self.display_scrollAreaWidgetContents.scene().addItem(self.polygonItem)
    
    def reset_memory(self):
        """
            @description : 작업을 메모리에 저장하기 위한 변수들을 초기화 하는 함수
            @author : MyoungHwan
            @history
                1. Modified by MyoungHwan (2024.09.06): 효율적인 연산을 위한 변수 수정
        """
        #memory information
        self.tmp_image_rgb = []
        self.tmp_image_label = []
        self.tmp_image_label_mask_dict = {}
        """
            description
            Modified by MyoungHwan(20240529) : define switching variable to store operations in memory
        """
        self.memory_record_status = False
        self.undo_memory = []
        self.redo_memory = []
        self.memory_dict = {}
        
        #Pen undo,redo disable
        for obj in list(self.pen_obj_dict.keys()):
            self.pen_obj_dict[obj]['obj'].setChecked(False)
            self.pen_obj_dict[obj]['obj'].setEnabled(False)

    def numpy_to_qpixmap(self, arr):
        """
            @description : Core DB에서 불러온 이미지 numpy array를 Display에서 출력하기 위해 qpixmap으로 변환하기 위한 함수이다.
            @author : MyoungHwan
            @parameters
                1. arr(numpy) : 이미지 데이터
            
            @history
                1. Modified by HyunsuKim : QImage 생성 시 bytesPerLine 옵션 부여 (2025.10.16)
        """
        image = QtGui.QImage(arr, arr.shape[1], arr.shape[0], arr.strides[0], QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap(image)
        return pixmap

    def numpy_to_qpixmap_minimap(self, arr):
        """
            @description : Core DB에서 불러온 이미지 numpy array를 Display에서 출력하기 위해 qpixmap으로 변환하기 위한 함수이다.
            @author : MyoungHwan
            @parameters
                1. arr(numpy) : 이미지 데이터
        """
        image = QtGui.QImage(arr, arr.shape[1], arr.shape[0], arr.shape[1] * 3, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap(image).scaled(self.pen_control_dict['pen_minimap_scale'],self.pen_control_dict['pen_minimap_scale'])
        return pixmap

    def getPos(self, point_x, point_y, mode=0):
        """
            @description : 이미지 확대 및 축소를 위한 함수
            @author : MyoungHwan
            @parameters
                1. mode(int)
                    - 0 : image scale down, 그래프 표시할 때 사용, 원본이미지 사이즈로 돌림
                    - 1 : image scale up, 확대된 이미지에 포인트 찍을때 사용
        """
        tmp_main_x = self.display_scrollAreaWidgetContents.width()
        tmp_main_y = self.display_scrollAreaWidgetContents.height()
        if mode == 0:
            tmp_origin_x, tmp_origin_y = self.image_width_origin, self.image_height_origin
        else:
            tmp_origin_x, tmp_origin_y = self.pix.width(), self.pix.height()
        tmp_cal_x = int(tmp_origin_x * (point_x + self.display_scrollAreaWidgetContents.horizontalScrollBar().value()) // tmp_main_x)
        tmp_cal_y = int(tmp_origin_y * (point_y + self.display_scrollAreaWidgetContents.verticalScrollBar().value()) // tmp_main_y)
        return [tmp_cal_x, tmp_cal_y]

    def update_image_display(self, image):
        """
            @description : 기능 업데이트에 대한 이미지 변경 시 해상도에 맞게 출력하기 위한 함수이다.
            @author : MyoungHwan
            @parameters
                1. image(numpy): 변경된 이미지 데이터
        """
        self.pix = self.numpy_to_qpixmap(image)
        self.display_scrollAreaWidgetContents.updatePhoto(self.pix)
    
    def display_raw_image(self):
        """
            @description : 초기 이미지를 출력하기 위한 함수이다.
            @author : Chansik Kim
        """
        self.pix = self.numpy_to_qpixmap(self.image_origin)
        self.display_scrollAreaWidgetContents.initPhoto(self.pix)
        
    def display_show_minimap(self, image):
        """
            @description : 기능 업데이트에 대한 이미지 변경 시 해상도에 맞게 출력하기 위한 함수이다.
            @author : MyoungHwan
            @parameters
                1. image(numpy: 변경된 이미지 데이터
                2. mode(int)
                    - 0 :  초기 image display
                    - 1 :  라벨 hide 및 color 변경에 따른 image display
        """
        self.pix_minimap = self.numpy_to_qpixmap_minimap(image)
        self.pen_obj_dict['pen_minimap']['label'].setPixmap(self.pix_minimap)
    
    def drag_image(self, point):
        """
            @description : 이미지 이동모드(drawing mode가 3일 경우에만 발동) 마우스 드래그를 통해 화면을 이동할 수 있다.
            @author : MyoungHwan
            @parameters
                1. point(list): 마우스 클릭시 좌표
        """
        moving_value = 7
        cur_x, cur_y = point
        scroll_horizon_cur_value = self.display_scrollAreaWidgetContents.horizontalScrollBar().value()
        scroll_vertical_cur_value = self.display_scrollAreaWidgetContents.verticalScrollBar().value()
        if cur_x - self.old_x  > 0:
            self.display_scrollAreaWidgetContents.horizontalScrollBar().setValue(scroll_horizon_cur_value-moving_value)
        elif cur_x - self.old_x < 0:
            self.display_scrollAreaWidgetContents.horizontalScrollBar().setValue(scroll_horizon_cur_value+moving_value)
        if cur_y - self.old_y  > 0:
            self.display_scrollAreaWidgetContents.verticalScrollBar().setValue(scroll_vertical_cur_value-moving_value)
        elif  cur_y - self.old_y < 0:
            self.display_scrollAreaWidgetContents.verticalScrollBar().setValue(scroll_vertical_cur_value+moving_value)
        self.old_x, self.old_y = point

    def update_point_range(self, cur_point=None):
        """
            @description : 펜,지우개 굵기 조정시 발동되는 함수이다.
            @author : MyoungHwan
            @parameters
                1. cur_point(list) : x,y 좌표
        """
        x, y = cur_point
        draw_size = 1
        if self.display_control_dict['drawing_mode'] == DRAWING_MODE_LABELING:
            draw_size = self.pen_control_dict['pen_drawing_size']
        elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_ERASING:
            draw_size = self.pen_control_dict['pen_eraser_size']

        cal_start_y = np.clip(y - (draw_size - 1), 0, self.image_height_origin - 1)
        cal_start_x = np.clip(x - (draw_size - 1), 0, self.image_width_origin - 1)
        cal_end_y = np.clip(y + (draw_size), 1, self.image_height_origin)
        cal_end_x = np.clip(x + (draw_size), 1, self.image_width_origin)
            
        return cal_start_x, cal_start_y, cal_end_x, cal_end_y

    def update_point_range_minimap(self, cur_point=None):
        """
            @description : 펜,지우개 굵기 조정대로 미니맵에서 보여지는 함수이다. 현재 사용안함(20240531)
            @author : MyoungHwan
            @parameters
                1. cur_point(list) : x,y 좌표
        """
        cal_x, cal_y = cur_point
        tmp_size = self.pen_control_dict['pen_minimap_size']
        cal_start_y = np.clip(cal_y - (tmp_size-1), 0, self.image_height_origin-1)
        cal_start_x = np.clip(cal_x - (tmp_size-1), 0, self.image_width_origin-1)
        cal_end_y = np.clip(cal_y + (tmp_size-1), 1, self.image_height_origin)
        cal_end_x = np.clip(cal_x + (tmp_size-1), 1, self.image_width_origin)
            
        return cal_start_x, cal_start_y, cal_end_x, cal_end_y

    def update_point_indice(self, cur_point=None, prev_point=None):
        if not prev_point: # pen or eraser size larger than 1
            start_x, start_y, end_x, end_y = self.update_point_range(cur_point=cur_point)
        else: # rectangle
            start_x, end_x = sorted([prev_point[0], cur_point[0]])
            start_y, end_y = sorted([prev_point[1], cur_point[1]])
            # Add 1 to the coordinates to label all points from the starting point to the endpoint of the rectangle.

            end_x += 1
            end_y += 1
        range_x = list(range(start_x, end_x)) or [start_x]
        range_y = list(range(start_y, end_y)) or [start_y]
        # x, y 좌표 생성
        x = np.repeat(range_x, len(range_y))
        y = np.tile(range_y, len(range_x))
        indice = (y, x)
        return indice

    def update_point_indice_minimap(self, cur_point=None):
        start_x, start_y, end_x, end_y = self.update_point_range_minimap(cur_point=cur_point)
        return start_x, start_y, end_x, end_y

    def close_pen_setting_form(self):
        """마우스 우클릭을 통해 펜 상세 설정 창이 열린 상태에서 Display를 클릭했을 때 close하기 위한 함수이다.
        """
        self.pen_obj_dict['pen_draw_type']['sub_form'].close()
        self.pen_obj_dict['pen_draw_type']['opened'] = False
    
    def close_eraser_setting_form(self):
        """마우스 우클릭을 통해 지우개 상세 설정 창이 열린 상태에서 Display를 클릭했을 때 close하기 위한 함수이다.
        """
        self.pen_obj_dict['pen_eraser']['sub_form'].close()
        self.pen_obj_dict['pen_eraser']['opened'] = False

    def toggle_all_controls(self, enable:bool=None) -> None:
        """
        모든 제어 스위치(pen, graph, label 등)를 활성화하거나 비활성화합니다.
        """
        self.image_control_dict['image_control_sw'] = enable
        self.label_control_dict['label_control_sw'] = enable
        self.pen_control_dict['pen_control_sw'] = enable
        self.graph_control_dict['graph_control_sw'] = enable

    def switch_pen_objects(self, enable:bool=None, exclude:bool=True) -> None:
        """
        펜 객체의 상태를 전환합니다.
        """
        for obj_name in self.pen_obj_dict.keys():
            if obj_name == 'pen_image' and self.pen_obj_dict['pen_image']['obj'].isChecked():
                continue
            if not enable and self.pen_obj_dict[obj_name]['obj'].isChecked():
                self.pen_obj_dict[obj_name]['obj'].toggle()
            if exclude and obj_name in self.excluded_pen_objs:
                continue
            self.pen_obj_dict[obj_name]['obj'].setEnabled(enable)

    def switch_graph_objects(self, enable:bool=None, exclude:bool=True) -> None:
        """
        그래프 객체의 상태를 전환합니다.
        """
        for obj_name in self.graph_obj_dict.keys():
            if not enable and obj_name not in self.excluded_graph_objs:
                self.graph_obj_dict[obj_name]['obj'].setChecked(enable)
            if exclude and obj_name in self.excluded_graph_objs:
                continue
            self.graph_obj_dict[obj_name]['obj'].setEnabled(enable)
        self.update_graph_preview()

    def switch_label_objects(self, enable:bool=None, exclude:bool=True) -> None:
        """
        라벨 객체의 상태를 전환합니다.
        """
        for obj_name in self.label_obj_dict.keys():
            if exclude and obj_name in self.excluded_label_objs:
                continue
            self.label_obj_dict[obj_name]['obj_dict']['select'].setChecked(enable)

    def switch_objects(self, objects_to_switch:list[str]=[], enable:bool=None, exclude:bool=None) -> None:
        """
        지정된 객체들의 상태를 비활성화 상태로 전환하기 위한 함수입니다.

        Parameters:
            objects_to_switch (list of str, optional): 
                - 비활성화할 객체의 리스트. 가능한 값은 'pen', 'graph', 'label'입니다.
                - 예: ['pen'], ['graph', 'label'], ['pen', 'graph', 'label']
        """
        self.toggle_all_controls(enable=False)
        # 객체 목록이 비어 있는 경우, 기본적으로 모든 객체를 비활성화
        if not objects_to_switch:
            objects_to_switch = ['pen', 'graph', 'label']
        
        # 리스트를 기반으로 객체 상태 비활성화 처리
        if 'pen' in objects_to_switch:
            self.switch_pen_objects(enable, exclude)
        if 'graph' in objects_to_switch:
            self.switch_graph_objects(enable, exclude)
        if 'label' in objects_to_switch:
            self.switch_label_objects(enable, exclude)

        # 모든 컨트롤 다시 활성화
        self.toggle_all_controls(enable=True)

    def disable_rect_preview(self):
        self.prev_point = []
        self.display_scrollAreaWidgetContents.remove_rect_preview()

    def disable_polygon_preview(self):
        """
            @Description: disable polygon preview
            @Author: GaEun Hwang
            @History:
                1. Improved by GaEun Hwang (2025.10.20): Improve polygon preview disable function
        """
        for item in self.display_scrollAreaWidgetContents.scene().items():
            if isinstance(item, customPolygonItem):
                self.display_scrollAreaWidgetContents.scene().removeItem(item)
                break
        self.polygonItem.init()
        self.update_pen_buttons()
        self.display_scrollAreaWidgetContents.scene().addItem(self.polygonItem)

    def update_data_list(self, label_number:int=None) -> None:
        """
            @description: label 기능 이용에 대한 데이터 정보를 업데이트하기 위한 함수
            @author: MyoungHwan
            @history
                1. Modified by MyoungHwan (2024.09.06): 효율적인 연산을 위한 변수 최적화 및 추가, opacity 정보가 반영되도록 코드 수정
                2. Modified by MyoungHwan (2024.09.11): alpha ratio 적용을 위한 코드 수정
                3. Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
        """
        if label_number in self.label_obj_dict.keys():
            indice = np.where(self.image_label == label_number)
            select_color = self.label_obj_dict[label_number]['color']
            alpha_ratio = self.label_obj_dict[label_number]['label_color_alpha']
            self.image_label_mask_dict['mask'][indice] = select_color            
            self.image_label_mask_dict['alpha'][indice] = alpha_ratio
            # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
            if self.label_obj_dict[label_number]['obj_dict']['show'].isChecked():
                tmp_image_rgb = (alpha_ratio * self.image_label_mask_dict['mask'][indice].astype(np.float32)) \
                    + ((1-alpha_ratio) * self.image_origin[indice].astype(np.float32))
                self.image_rgb[indice] = tmp_image_rgb.astype(np.uint8)
                self.image_label_mask_dict['show'][indice] = True
            else:
                self.image_rgb[indice] = self.image_origin[indice]
                self.image_label_mask_dict['show'][indice] = False
        else:
            print(f"debug,display_main.py, label: {label_number} is not in self.label_obj_dict")

    def update_drawing(self, label_number=None, indice=None):
        """
            @description: label 기능 이용에 대한 데이터 정보를 업데이트하기 위한 함수
            @author: MyoungHwan
            @history
                1. Modified by MyoungHwan (2024.09.06): 효율적인 연산을 위한 변수 최적화 및 추가, opacity 정보가 반영되도록 코드 수정
                2. Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
        """
        self.image_label[indice] = label_number
        select_color = self.label_obj_dict[label_number]['color']
        alpha_ratio = self.label_obj_dict[label_number]['label_color_alpha']
        self.image_label_mask_dict['mask'][indice] = select_color
        """
            Description: Add Alpha value update
            Modified by MyoungHwan (2024.09.10)
        """
        self.image_label_mask_dict['alpha'][indice] = alpha_ratio
        # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
        if self.label_obj_dict[label_number]['obj_dict']['show'].isChecked():
            tmp_image_rgb = (alpha_ratio * self.image_label_mask_dict['mask'][indice].astype(np.float32)) \
                    + ((1-alpha_ratio) * self.image_origin[indice].astype(np.float32))
            self.image_rgb[indice] = tmp_image_rgb.astype(np.uint8)
            self.image_label_mask_dict['show'][indice] = True
        else:
            self.image_rgb[indice] = self.image_origin[indice]
            self.image_label_mask_dict['show'][indice] = False
        self.update_graph()

    def update_undo_redo_data(self, data:dict, mode:str) -> None:
        """
            @description: 실행 취소/복구기능 이용에 대한 데이터 정보를 임시로 저장하기 위한 함수
            @author: MyoungHwan
            @history
                1. Modified by MyoungHwan (2024.09.06): 효율적인 연산을 위한 변수 최적화 및 추가, opacity 정보가 반영되도록 코드 수정
                2. Modified by MyoungHwan (2024.09.10): Add Alpha value update
                3. Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                4. Added by GaEun Hwang (2025.06.05): Add polygon undo/redo function
                5. Modified by GaEun Hwang (2025.10.23): Remove polygon undo/redo function
        """
        self.image_label = data['label'].copy()
        self.image_rgb = data['image'].copy()
        self.image_label_mask_dict = data['image_label_mask_dict'].copy()
        for label_number in self.label_obj_dict.keys():
            indice = np.where(self.image_label == label_number)
            select_color = self.label_obj_dict[label_number]['color']
            alpha_ratio = self.label_obj_dict[label_number]['label_color_alpha']
            self.image_label_mask_dict['mask'][indice] = select_color
            """
                Description: Add Alpha value update
                Modified by MyoungHwan (2024.09.10)
            """
            self.image_label_mask_dict['alpha'][indice] = alpha_ratio
            # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
            if self.label_obj_dict[label_number]['obj_dict']['show'].isChecked():
                tmp_image_rgb = (alpha_ratio * self.image_label_mask_dict['mask'][indice].astype(np.float32)) \
                        + ((1-alpha_ratio) * self.image_origin[indice].astype(np.float32))
                self.image_rgb[indice] = tmp_image_rgb.astype(np.uint8)
                self.image_label_mask_dict['show'][indice] = True
            else:
                self.image_rgb[indice] = self.image_origin[indice]
                self.image_label_mask_dict['show'][indice] = False

            self.update_graph()

            tmp_dict = {}
            tmp_dict['mode'] = 'modify'
            tmp_dict['type'] = 'display'
            tmp_dict['type_detail'] = 'label_data_from_memory'
            tmp_dict['label'] = copy.deepcopy(self.image_label)
            self.display_to_core(tmp_dict)

    def add_undo_memory(self) -> None:
        """Undo 메모리에 현재 상태를 추가합니다."""
        self.undo_memory.append(self.memory_dict)
        self.memory_dict = {}
        self._check_memory_size(self.undo_memory, "undo")
        self.update_pen_buttons()

    def add_redo_memory(self) -> None:
        """Redo 메모리에 현재 상태를 추가합니다."""
        self.redo_memory.append(self.memory_dict)
        self.memory_dict = {}
        self._check_memory_size(self.redo_memory, "redo")
        self.update_pen_buttons()
    
    """
        Description: remove undo memory to specific labels
        Author : Hyeok Yoon (2025.10.27)
    """
    def remove_undo_memory(self, label:int) -> None:
        self.remove_memory(self.undo_memory, label, True)
    
    """
        Description: remove redo memory to specific labels
        Author : Hyeok Yoon (2025.10.27)
    """
    def remove_redo_memory(self, label:int) -> None:
        self.remove_memory(self.redo_memory, label, False)

    """
        Description: remove memory to specific labels
        Author : Hyeok Yoon (2025.10.27)
    """
    def remove_memory(self, memory:list, label:int, is_undo:bool) -> None:
        if memory:
            relative_index = 0
            prev_labels = memory[0]["label"] if is_undo else memory[-1]["label"]
            for memory_index in range(len(memory)) if is_undo else reversed(range(len(memory))):
                # calculate relative index (consider of pop sequence)
                resolved_memory_index = memory_index - relative_index if is_undo else memory_index
                curr_labels = np.copy(memory[resolved_memory_index]["label"])
                
                # remove memory for specific indices
                if np.unique(curr_labels[prev_labels != curr_labels]) == label:
                    memory.pop(resolved_memory_index)
                    relative_index += 1
                else:
                    # update remained target labels to zero
                    memory[resolved_memory_index]["label"][memory[resolved_memory_index]["label"] == label] = 0

                    # remove memory for same with current labels (current origin labels)
                    if (memory[resolved_memory_index]["label"] == self.image_label).all():
                        memory.pop(resolved_memory_index)
                        relative_index += 1
                # update previous labels
                prev_labels = curr_labels
    
    def _check_memory_size(self, memory_list:list, memory_type:str) -> None:
        """메모리의 크기를 검사하여 제한을 초과하면 첫 번째 메모리를 제거합니다."""
        tmp_size = sys.getsizeof(memory_list)
        if tmp_size > 512:
            print(f"{memory_type} memory size({tmp_size}) is greater than 512, remove first memory")
            memory_list.pop(0)

    def pop_undo_memory(self) -> None:
        """Undo 메모리에서 마지막 상태를 복원합니다."""
        if self.undo_memory:
            tmp_memory = self.undo_memory.pop(-1)
            self.update_undo_redo_data(data=tmp_memory, mode='undo')
            self.update_image_display(self.image_rgb)
            self.update_pen_buttons()

    def pop_redo_memory(self) -> None:
        """Redo 메모리에서 마지막 상태를 복원합니다."""
        if self.redo_memory:
            tmp_memory = self.redo_memory.pop(-1)
            self.update_undo_redo_data(data=tmp_memory, mode='redo')
            self.update_image_display(self.image_rgb)
            self.update_pen_buttons()

    def update_pen_buttons(self) -> None:
        """
            @description: Undo와 Redo 버튼의 활성화 상태를 업데이트합니다.
        """
        self.pen_obj_dict['pen_undo']['obj'].setEnabled(bool(self.undo_memory) or bool(self.polygonItem.undo))
        self.pen_obj_dict['pen_redo']['obj'].setEnabled(bool(self.redo_memory) or bool(self.polygonItem.redo))

    def update_graph(self) -> None:
        """
            description: function for update graph information on display image
            author: MyoungHwan
            history:
                2024.09.06: remove unnecessary variable for efficient operation by MyoungHwan
                2025.12.08: modify code about random color information in image_graph_rgb_point/image_graph_rgb_label and logic by GaEun Hwang
        """
        if self.graph_control_dict['graph_view_mode'] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
            for key, graphGroup in self.graphGroupDict.items():
                if graphGroup['hide'] == True:
                    showGraphIndice = np.where(self.image_graph_rgb_label[self.graph_control_dict['graph_view_mode']] == key)
                    self.image_rgb[showGraphIndice] = self.image_graph_rgb_point[self.graph_control_dict['graph_view_mode']][showGraphIndice]
        else:
            for key, graphGroup in self.labelViewGraphGroupDict.items():
                if graphGroup['hide'] == True:
                    showGraphIndice = np.where(self.image_graph_rgb_label[self.graph_control_dict['graph_view_mode']] == key)
                    self.image_rgb[showGraphIndice] = self.image_graph_rgb_point[self.graph_control_dict['graph_view_mode']][showGraphIndice]
    
    def hide_graph(self, partial:bool=False, index:int=None, hideState:bool=False, labelView=False) -> None:
        """
            description: function for hide graph
            author: MyoungHwan
            history:
                2025.12.08: modify code about random color information in image_graph_rgb_point/image_graph_rgb_label and add partial/all update logic by GaEun Hwang
        """
        if partial == False:
            indice = np.where(self.image_graph_rgb_label[self.graph_control_dict['graph_view_mode']] !=-1)
            if hideState:
                self.image_rgb[indice] = self.image_graph_rgb_point[self.graph_control_dict['graph_view_mode']][indice]
            else:
                labelHideState = self.image_label_mask_dict['show'][indice]
                maskImage = self.image_label_mask_dict['mask'][indice]
                alphaRatio = self.image_label_mask_dict['alpha'][indice]
                rgbValue = (maskImage.astype(float) * alphaRatio) + ((1 - alphaRatio) * self.image_origin[indice].astype(float))
                self.image_rgb[indice] = np.where(np.expand_dims(labelHideState, axis=-1), rgbValue, self.image_origin[indice])

        else:
            indice = np.where(self.image_graph_rgb_label[self.graph_control_dict['graph_view_mode']] == index)
            if labelView == False:
                if self.graphGroupDict[index]['hide']:
                    self.image_rgb[indice] = self.image_graph_rgb_point[self.graph_control_dict['graph_view_mode']][indice]
                else:
                    labelHideState = self.image_label_mask_dict['show'][indice]
                    maskImage = self.image_label_mask_dict['mask'][indice]
                    alphaRatio = self.image_label_mask_dict['alpha'][indice]
                    rgbValue = (maskImage.astype(float) * alphaRatio) + ((1 - alphaRatio) * self.image_origin[indice].astype(float))
                    self.image_rgb[indice] = np.where(np.expand_dims(labelHideState, axis=-1), rgbValue, self.image_origin[indice])
            else:
                if self.labelViewGraphGroupDict[index]['hide']:
                    self.image_rgb[indice] = self.image_graph_rgb_point[self.graph_control_dict['graph_view_mode']][indice]
                else:
                    labelHideState = self.image_label_mask_dict['show'][indice]
                    maskImage = self.image_label_mask_dict['mask'][indice]
                    alphaRatio = self.image_label_mask_dict['alpha'][indice]
                    rgbValue = (maskImage.astype(float) * alphaRatio) + ((1 - alphaRatio) * self.image_origin[indice].astype(float))
                    self.image_rgb[indice] = np.where(np.expand_dims(labelHideState, axis=-1), rgbValue, self.image_origin[indice])

    def store_current_state(self) -> None:
        """
            @ Description: 효율적인 연산을 위한 코드 수정
            @ Author : MyoungHwan
            @ History
                1. Modified by MyoungHwan (2024.09.06)
                2. Added by GaEun Hwang (2025.06.05): save polygon item data in memory_dict
                3. Modified by GaEun Hwang (2025.10.23): Remove polygon item data from memory_dict
        """
        self.memory_dict['label'] = self.tmp_image_label.copy()
        self.memory_dict['image'] = self.tmp_image_rgb.copy()
        self.memory_dict['image_label_mask_dict'] = self.tmp_image_label_mask_dict.copy()

    def check_diff(self, mode:int=None) -> None:
        """
            @description : Undo/Redo 기능 구현을 위한 함수
            @author : MyoungHwan
            @parameters
                1.mode:0일때 현재시점의 Image 정보를 임시로 저장
                2.mode:1일때 라벨링된 Image 정보를 메모리에 저장, 임시로 저장한 정보와 다르지 않을경우 저장하지 않음
            @history
                1.Modified by MyoungHwan (2024.09.06): 효율적인 연산을 위한 변수 수정
                2.Added by Hwang GaEun (2025.06.02): create tmp_polygon_dict to save polygon data
                3.Modified by Hwang GaEun (2025.10.23): remove polygon data
        """
        if mode == 0:
            self.tmp_image_rgb = self.image_rgb.copy()
            self.tmp_image_label = self.image_label.copy()
            self.tmp_image_label_mask_dict = self.image_label_mask_dict.copy()
        elif mode == 1:
            bool_ = (self.tmp_image_label != self.image_label).any()
            if bool_:
                self.store_current_state()
                self.add_undo_memory()

    def setMouseSnap(self):
        """
            @description : A function to snap the mouse cursor to the first point of the polygon when drawing a polygon.
            @author : GaEun Hwang(2025.10.23)
        """
        if self.polygonItem.isDrawing:
            firstPoint = self.polygonItem.points[0]
            if self.polygonItem.isAvailableToSnap():
                if self.isSnapped == False:
                    snapCoordCenter = self.polygonItem.setPointCenter(firstPoint)
                    firstPointSceneCenter = self.display_scrollAreaWidgetContents.mapFromScene(snapCoordCenter)
                    firstPointGlobalCenter = self.display_scrollAreaWidgetContents.viewport().mapToGlobal(firstPointSceneCenter)
                    # if user use multi-monitor, check which monitor contains the cursor position
                    for screen in QtWidgets.QApplication.screens():
                        if screen.geometry().contains(firstPointGlobalCenter):
                            QtGui.QCursor.setPos(screen, firstPointGlobalCenter)
                            self.polygonItem.updateCursorPos(firstPoint)
                            self.isSnapped = True
                            break
            else:
                self.isSnapped = False
            # check distance between current cursor position and first point for checking it matched
            distance = self.polygonItem.getDistance(self.polygonItem.currentCursorPos, firstPoint)
            if distance == 0:
                self.polygonItem.isMatched = True
            else:
                self.polygonItem.isMatched = False
        else:
            pass

    def LoadImage(self, Form, path:str=None) -> None:
        """
            @description : 이미지 로드 함수이다. core로 부터 signal을 받아와 창을 분할한 뒤 이미지를 로드한다.
            @author : Hyunsu Kim (2025.10.30)
            @parameters
                1. path (str): image file path
        """
        Form.setObjectName("Form")
        Form.setWindowTitle("Display_Form")
        Form.setStyleSheet(stylesheet)

        self.display_scrollAreaWidgetContents.setParent(None)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)

        self.splitter.addWidget(self.display_scrollAreaWidgetContents)

        self.real_image_viewer = Display_viewer()

        realImage = QtGui.QPixmap(path)
        self.real_image_viewer.initPhoto(realImage)
        self.splitter.addWidget(self.real_image_viewer)

        half_width = self.display_scrollAreaWidgetContents.width() + self.real_image_viewer.width() // 2
        self.splitter.setSizes([half_width, half_width])

        self.display_gridLayout.addWidget(self.splitter, 0, 1, 1, 1)

        self.splitter.splitterMoved.connect(self.updateImageSize)
        self.real_image_viewer.updateDrag(True)
        self.real_image_viewer.setMinimumWidth(100)
        self.display_scrollAreaWidgetContents.setMinimumWidth(100)

        QtCore.QMetaObject.connectSlotsByName(Form)

    def updateImageSize(self) -> None:
        """
            @description : 이미지 뷰어 크기 조절 함수이다. 창을 분할한 뒤 이미지를 로드할 때 이미지 뷰어의 크기를 조절하기 위한 함수
            @author : Hyunsu Kim (2025.10.30)
        """
        if self.display_scrollAreaWidgetContents._zoom == 0:
            self.display_scrollAreaWidgetContents.fitInView()
        if self.real_image_viewer._zoom == 0:
            self.real_image_viewer.fitInView()

    def mouse_release(self, e) -> None:
        """
            @description : 마우스 클릭후 뗏을 때 활성화 되는 함수이다. 기능 사용의 끝을 지정하기위해 사용
            @author : MyoungHwan
            @history
                Modified by MyoungHwan(20240517) : 라벨링 중 작업물 기록을 메모리에 저장하기 위한 코드 보완수정
        """
        if self.select_image_number != IMAGE_UNSELECTED:
            if self.sub_window_sw:
                self.sub_window_sw = False
            else:
                if e.button() == Qt.LeftButton:
                    self.left_drawstart = False
                if e.button() == Qt.RightButton:
                    self.right_drawstart = False
                """
                    description
                    Modified by MyoungHwan(20240529) : 작업을 메모리에 저장하기 위한 스위칭변수 추가
                """
                if self.memory_record_status and (e.button() == Qt.LeftButton or e.button() == Qt.RightButton) : #현재 상태와 비교
                    self.memory_record_status = False
                    self.check_diff(mode=1)
                    self.redo_memory = []

    def mouse_control(self, dict_:dict) -> None:
        """
            @description : Display Viewer로 부터 마우스 좌표를 제어하기 위한 함수이며 'self.display_scrollAreaWidgetContents' 객체에서 좌표값을 signal로 받아온다.
            @author : MyoungHwan
            @history
                Modified by MyoungHwan(20240517) : Display 영역 위치를 감지하기 위한 코드 추가
                2. Modified by GaEun Hwang(2025.10.23): Add wheel event
        """
        mode = dict_['mode']
        event = dict_['event']
        if 'point' in dict_.keys():
            point = dict_['point']
            point = list(map(int,[point.x(), point.y()]))
        if 'zoom' in dict_.keys():
            zoom = dict_['zoom']
        """
            description
            Modified by MyoungHwan(20240529) : 마우스 포인터가 Display 영역인지 아닌지 체크하는 변수 추가
        """
        in_pixmap = dict_['under']
        if mode == MOUSE_EVENT_PRESS: #press event
            self.mouse_press(event, point, in_pixmap)
        elif mode == MOUSE_EVENT_MOVE: #move event
            self.mouse_move(event, point, in_pixmap)
        elif mode == MOUSE_EVENT_RELEASE: #release event
            self.mouse_release(event)
        elif mode == MOUSE_EVENT_WHEEL:
            self.mouse_wheel(event, zoom)

    def mouse_press(self, e, cur_point:list, in_pixmap:bool) -> None:
        """
            @Description : 마우스 클릭시 활성화 되는 함수이다. 라벨링, 지우개, 이미지 부분확대, 그래프 그리기, 그래프 지우개 모드에 대한 기능이 포함되어 있다.
            @Author : MyoungHwan
            @History
                1. Modified by MyoungHwan(2024.05.17) : 라벨링 중 작업물 기록을 메모리에 저장하기 위한 코드 보완수정
                2. Modified by MyoungHwan(2024.05.29) : 마우스 위치에 따른 조건 추가
                3. Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                4. Improvemented by GaEun Hwang (2025.10.20): Improve polygon drawing function
        """
        x, y = cur_point
        """
            description
            Modified by MyoungHwan(20240529) : 마우스 위치에 따른 조건 추가
        """
        if in_pixmap and self.select_image_number != IMAGE_UNSELECTED:
            if self.pen_obj_dict['pen_draw_type']['opened']:
                # close pen sub form
                self.sub_window_sw = True
                self.close_pen_setting_form()
            elif self.pen_obj_dict['pen_eraser']['opened']:
                self.sub_window_sw = True
                self.close_eraser_setting_form()
            else:
                if e.button() in [Qt.LeftButton, Qt.RightButton] : #현재상태 저장
                    """
                        description
                        Modified by MyoungHwan(20240529) : 현재 작업 상태를 변경하기 위한 변수 선언
                    """
                    self.memory_record_status = True
                    self.check_diff(mode=0)

                if e.button() == Qt.LeftButton:
                    self.left_drawstart = True
                    indice = []
                    drawing_mode = self.display_control_dict['drawing_mode']
                    if drawing_mode == DRAWING_MODE_LABELING:                    
                        # drawing(labeling) mode
                        selected_label_number = self.label_control_dict['select_main_label_number']
                        if selected_label_number == LABEL_UNSELECTED:
                            raise Exception("error select label number is None... please select label number....set change default label number(0)")
                        indice = self.update_point_indice(cur_point=cur_point)
                        self.update_drawing(label_number=selected_label_number, indice=indice)
                        self.update_image_display(self.image_rgb)

                    elif drawing_mode == DRAWING_MODE_ERASING:
                        # eraser mode
                        selected_label_number = LABEL_IGNORED
                        indice = self.update_point_indice(cur_point=cur_point)
                        # indice = self.update_point_indice(cur_point=[self.cal_x, self.cal_y])
                        self.update_drawing(label_number=selected_label_number, indice=indice)
                        self.update_image_display(self.image_rgb)

                    elif drawing_mode == DRAWING_MODE_DRAW_GRAPH_POINT:
                        #graph 표시용, 실제 그래프에 포인트 지정
                        if self.image_graph_rgb_label[self.graph_control_dict["graph_view_mode"]][y,x] == GRAPH_PRESENT_NONE:
                            # if drawing graph point when label view mode is on
                            if self.tempGraphIndex is not None and self.tempColor is not None:
                                selectedGraphGroupIdx = self.tempGraphIndex
                                selectiveColor = self.tempColor

                            labelClass = self.image_label[y,x]
                            labelColor = self.label_obj_dict[labelClass]['color']
                            if self.graph_control_dict['graph_view_mode'] == GRAPH_VIEW_MODE_SELECTIVE_COLOR and self.graph_control_dict['selectedGraphGroup'] != GRAPH_PRESENT_NONE:
                                selectedGraphGroupIdx = self.graph_control_dict['selectedGraphGroup']
                                selectiveColor = self.graphGroupDict[selectedGraphGroupIdx]['color']
                                color = selectiveColor
                                
                            elif self.graph_control_dict['graph_view_mode'] == GRAPH_VIEW_MODE_LABEL_COLOR:
                                color = labelColor
                            else:
                                return

                            self.image_graph_rgb_label[0][y,x] = selectedGraphGroupIdx
                            self.image_graph_rgb_label[1][y,x] = labelClass
                            self.image_graph_rgb_point[0][y,x] = selectiveColor
                            self.image_graph_rgb_point[1][y,x] = labelColor
                            if self.graph_control_dict['graph_view_mode'] == GRAPH_VIEW_MODE_SELECTIVE_COLOR:
                                if self.graphGroupDict[selectedGraphGroupIdx]['hide'] == True:
                                    self.image_rgb[y][x] = color
                            else:
                                if self.labelViewGraphGroupDict[labelClass]['hide'] == True:
                                    self.image_rgb[y][x] = color

                            """
                                추가예정
                            """
                            # tmp_rect_color = QtGui.QColor(tmp_color[0],tmp_color[1],tmp_color[2],self.preview_cursor_color_alpha)
                            # tmp_rect_pen = QtGui.QPen(tmp_rect_color, 0.2)
                            # tmp_text = self.display_scrollAreaWidgetContents._scene.addText(str(self.display_scene_cnt))
                            # tmp_rect = self.display_scrollAreaWidgetContents._scene.addRect(x, y, 1, 1, tmp_rect_pen)
                            # self.display_scrollAreaWidgetContents.add_graph_point(self.display_scene_cnt, tmp_text, tmp_rect, [x,y], tmp_color)
                            # self.display_scene_cnt += 1

                            self.update_image_display(self.image_rgb)
                            """
                                Description: 효율적인 연산을 위한 코드 수정
                                Modified by MyoungHwan (2024.09.06)
                            """                            
                            tmp_dict = {}
                            tmp_dict['mode'] = CHECK_GRAPH_POINT
                            tmp_dict['point'] = (y, x)
                            tmp_dict['data'] = copy.deepcopy(self.image_raw[y][x])
                            tmp_dict['selectiveGraphIdx'] = selectedGraphGroupIdx
                            tmp_dict['selectiveColor'] = copy.deepcopy(selectiveColor)
                            tmp_dict['labelClass'] = labelClass
                            tmp_dict['labelColor'] = copy.deepcopy(self.label_obj_dict[labelClass]['color'])
                            tmp_dict['shape'] = [self.image_width_origin, self.image_height_origin, self.image_raw.shape[-1]]
                            self.displayToGraphGroupSignal.emit(tmp_dict)

                            tmp_dict = {}
                            tmp_dict['mode'] = 'modify'
                            tmp_dict['type'] = 'display'
                            tmp_dict['type_detail'] = 'graph_data'
                            tmp_dict['point_info'] = [(y, x), color]
                            self.display_to_core(tmp_dict)
                        else:
                            print("this point is already exist")

                    elif drawing_mode == DRAWING_MODE_ZOOM_IN:
                        #part scale
                        self.count += 1
                        if self.count > 5 :
                            self.count = 5
                        # cur_point = [x, y]
                        # self.update_part_scale(cur_point)
                        # self.pix = self.pix.scaled(self.image_width_list[self.count], self.image_height_list[self.count])
                        # self.display_scrollAreaWidgetContents.updatePhoto(self.pix)
                        self.display_scrollAreaWidgetContents._scale()

                    elif drawing_mode == DRAWING_MODE_ERASE_GRAPH_POINT:
                        #graph point erase
                        if self.image_graph_rgb_label[self.graph_control_dict["graph_view_mode"]][y,x] != GRAPH_PRESENT_NONE: #그래프 있을때
                            removedSelectiveGraphNumber = self.image_graph_rgb_label[0][y,x]
                            removedLabelGraphNumber = self.image_graph_rgb_label[1][y,x]
                            self.image_graph_rgb_label[0][y,x] = GRAPH_PRESENT_NONE
                            self.image_graph_rgb_point[0][y,x] = self.image_origin[y][x]
                            self.image_graph_rgb_label[1][y,x] = GRAPH_PRESENT_NONE
                            self.image_graph_rgb_point[1][y,x] = self.image_origin[y][x]
                            label_number = self.image_label[y][x]
                            """
                                Description: 효율적인 연산 및 alpha 값 적용을 위한 코드 수정 
                                Modified by MyoungHwan (2024.09.11)
                            """
                            mask_image = self.image_label_mask_dict['mask'][y][x]
                            alpha_ratio = self.image_label_mask_dict['alpha'][y][x]
                            # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                            if self.label_obj_dict[label_number]['obj_dict']['show'].isChecked():
                                tmp_image_rgb = (mask_image.astype(np.float32) * alpha_ratio) + ( (1-alpha_ratio) * self.image_origin[y][x].astype(np.float32))
                                self.image_rgb[y][x] = tmp_image_rgb.astype(np.uint8)
                            else:
                                self.image_rgb[y][x] = self.image_origin[y][x]
                            self.update_image_display(self.image_rgb)

                            tmp_dict = {}
                            tmp_dict['mode'] = REMOVE_GRAPH_POINT
                            tmp_dict['point'] = (y, x)
                            tmp_dict['removedSelectiveGraph'] = removedSelectiveGraphNumber
                            tmp_dict['removedLabelGraph'] = removedLabelGraphNumber
                            self.displayToGraphGroupSignal.emit(tmp_dict)

                            tmp_dict = {}
                            tmp_dict['mode'] = 'delete'
                            tmp_dict['type'] = 'display'
                            tmp_dict['select_type'] = 'graph_data'
                            tmp_dict['type_detail'] = 'one'
                            tmp_dict['point_info'] = [(y, x)]
                            self.display_to_core(tmp_dict)

                    elif drawing_mode == DRAWING_MODE_PAINTING:
                        #paintmode
                        selected_label_number = self.label_control_dict['select_main_label_number']
                        if selected_label_number == LABEL_UNSELECTED:
                            raise Exception("error select label number is None... please select label number....set change default label number(0)")
                        indice = flood(self.image_label, (y, x), connectivity=1)
                        self.update_drawing(label_number=selected_label_number, indice=indice)
                        self.update_image_display(self.image_rgb)
                    
                    elif drawing_mode == DRAWING_MODE_RECTANGLE:
                        #rectangle mode
                        selected_label_number = self.label_control_dict['select_main_label_number']
                        if selected_label_number == LABEL_UNSELECTED:
                            raise Exception("error select label number is None... please select label number....set change default label number(0)")
                        if self.prev_point:
                            if self.prev_point == cur_point:
                                self.prev_point = []
                            indice = self.update_point_indice(cur_point=cur_point, prev_point=self.prev_point)
                            self.update_drawing(label_number=selected_label_number, indice=indice)
                            self.update_image_display(self.image_rgb)
                            self.disable_rect_preview()
                        else:
                            self.prev_point = cur_point
                            color = self.label_obj_dict[selected_label_number]['color']
                            self.display_scrollAreaWidgetContents.init_rect_value(self.prev_point, color)

                    elif drawing_mode == DRAWING_MODE_POLYGON:
                        #polygon mode
                        selected_label_number = self.label_control_dict['select_main_label_number']
                        self.polygonItem.setStyle(QtGui.QColor(*self.label_obj_dict[selected_label_number]['color']))
                        if selected_label_number == LABEL_UNSELECTED:
                            raise Exception("error select label number is None... please select label number....set change default label number(0)")
                        # draw polygon line and ellipse when self.prev_point has more than 2 points
                        self.polygonItem.addPoint(QtCore.QPointF(cur_point[0], cur_point[1]))
                        self.polygonItem.update()
                        self.update_pen_buttons()

                        # draw polygon when current point and first point are same
                        if self.polygonItem.polygon is not None:
                            self.polygonInsidePoints = self.polygonItem.getPointFromPolygon()
                            # when valid polygon
                            if len(self.polygonInsidePoints) > 0:
                                x_array, y_array = zip(*self.polygonInsidePoints)
                                indice = (np.array(y_array), np.array(x_array))
                                self.update_drawing(label_number=selected_label_number, indice=indice)
                                self.update_image_display(self.image_rgb)
                                self.polygonInsidePoints = []
                            else:
                                raise Exception("error, inside point in polygon is None")

                    if indice is not None and len(indice) > 0 and drawing_mode in [DRAWING_MODE_LABELING, DRAWING_MODE_ERASING, DRAWING_MODE_PAINTING, DRAWING_MODE_RECTANGLE, DRAWING_MODE_POLYGON]:
                        tmp_dict = {}
                        tmp_dict['mode'] = 'modify'
                        tmp_dict['type'] = 'display'
                        tmp_dict['type_detail'] = 'drawing_label_data'
                        tmp_dict['label_number'] = selected_label_number
                        tmp_dict['indice'] = indice
                        self.display_to_core(tmp_dict)
                    
                    if drawing_mode != DRAWING_MODE_RECTANGLE and drawing_mode != DRAWING_MODE_POLYGON:
                        # To enable drawing shapes while moving while pressed ctrl
                        if self.is_ctrl_key_pressed == False:
                            self.disable_rect_preview()
                            self.disable_polygon_preview()

                elif e.button() == Qt.RightButton:
                    self.right_drawstart = True
                    if self.display_control_dict['drawing_mode'] == DRAWING_MODE_LABELING:
                        # 드로잉 모드일때 오른쪽 마우스 클릭시 sub 드로잉펜
                        selected_label_number = self.label_control_dict['select_sub_label_number']
                        if selected_label_number != LABEL_UNSELECTED:
                            indice = self.update_point_indice(cur_point=cur_point)
                            self.update_drawing(label_number=selected_label_number, indice=indice)
                            self.update_image_display(self.image_rgb)

                            tmp_dict = {}
                            tmp_dict['mode'] = 'modify'
                            tmp_dict['type'] = 'display'
                            tmp_dict['type_detail'] = 'drawing_label_data'
                            tmp_dict['label_number'] = selected_label_number
                            tmp_dict['indice'] = indice
                            self.display_to_core(tmp_dict)

            if self.pen_obj_dict['pen_minimap']['form'].isVisible():
                start_x, start_y, end_x, end_y = self.update_point_indice_minimap(cur_point=cur_point)
                tmp_minimap = self.image_rgb[start_y:end_y, start_x:end_x].copy()
                self.update_image_display_minimap(tmp_minimap)
        
    def update_mouse_color(self, color:list[int]=[255,0,0]) -> None:
        self.preview_cursor_color = QtGui.QColor(color[0], color[1], color[2], self.preview_cursor_color_alpha)
        self.preview_cursor_pen = QtGui.QPen(self.preview_cursor_color, 0.2)

    def update_mouse_preview(self, change_color:bool=False, color:list[int]=[255,0,0]) -> None:
        if change_color:
            self.update_mouse_color(color)

        if self.preview_cursor is not None:
            self.display_scrollAreaWidgetContents._scene.removeItem(self.preview_cursor)

        if self.display_control_dict['drawing_mode'] == DRAWING_MODE_LABELING:
            self.preview_cursor_pen_rad = 2*self.pen_control_dict['pen_drawing_size'] - 1
            preview_cursor_pen_rad_alpha = self.pen_control_dict['pen_drawing_size']
        elif self.display_control_dict['drawing_mode'] == DRAWING_MODE_ERASING:
            self.preview_cursor_pen_rad = 2*self.pen_control_dict['pen_eraser_size'] - 1
            preview_cursor_pen_rad_alpha = self.pen_control_dict['pen_eraser_size']
        else:
            self.preview_cursor_pen_rad = 1
            preview_cursor_pen_rad_alpha = 1
        self.preview_cursor = self.display_scrollAreaWidgetContents._scene.addRect(self.x-self.preview_cursor_pen_rad+preview_cursor_pen_rad_alpha, 
            self.y-self.preview_cursor_pen_rad+preview_cursor_pen_rad_alpha, self.preview_cursor_pen_rad, self.preview_cursor_pen_rad, self.preview_cursor_pen)

    def mouse_move(self, e, cur_point:list, in_pixmap:bool) -> None:
        """
            @description: 마우스를 움직일 경우 활성화 되는 함수이다. 라벨링, 지우개, 이미지 부분확대, 이미지 이동, 그래프 그리기, 그래프 지우개 모드에 대한 기능이 포함되어 있다.
            @author : MyoungHwan
            @history
                Modified by MyoungHwan(20240517) : 라벨링 중 작업물 기록을 메모리에 저장하기 위한 코드 보완수정
                    
        """
        x,y = cur_point
        self.x, self.y = cur_point
        if self.select_image_number > -1:
            """
                description
                Modified by MyoungHwan(20240529) : 마우스 포인터가 Display 영역인지 아닌지 체크하는 조건 추가
            """
            drawing_mode = self.display_control_dict['drawing_mode']
            if in_pixmap:
                self.update_mouse_preview()
                self.core_obj_dict["status_pointer_status"].setText(f"Pixel Coordinates : ({x},{y})")
                if self.graph_obj_dict['graph_linedrawing']:
                    tmp_dict = {}
                    tmp_dict['mode'] = GRAPH_DISPLAY_PREVIEW
                    tmp_dict['point'] = [y, x]
                    tmp_dict['point_data'] = copy.deepcopy(self.image_raw[y][x])
                    tmp_dict['shape'] = [self.image_width_origin, self.image_height_origin, self.image_raw.shape[-1]]
                    self.display_to_graph(tmp_dict)
                    
                if (e.buttons() and Qt.LeftButton) and self.left_drawstart: # 드래그
                    if drawing_mode == DRAWING_MODE_LABELING:                    
                        # drawing(labeling) mode
                        selected_label_number = self.label_control_dict['select_main_label_number']
                        if selected_label_number == LABEL_UNSELECTED:
                            raise Exception("error select label number is None... please select label number....set change default label number(0)")
                        indice = self.update_point_indice(cur_point=cur_point)
                        self.update_drawing(label_number=selected_label_number, indice=indice)
                        self.update_image_display(self.image_rgb)
                        
                    elif drawing_mode == DRAWING_MODE_ERASING:
                        # eraser mode
                        selected_label_number = LABEL_IGNORED
                        indice = self.update_point_indice(cur_point=cur_point)
                        self.update_drawing(label_number=selected_label_number, indice=indice)
                        self.update_image_display(self.image_rgb)

                    elif drawing_mode == DRAWING_MODE_DRAW_GRAPH_POINT:
                        #graph mode
                        pass
                        
                    elif drawing_mode == DRAWING_MODE_IMAGE_MOVING:
                        # part image move
                        self.drag_image(cur_point)
        
                    elif drawing_mode == DRAWING_MODE_ZOOM_IN:
                        pass

                    if drawing_mode in [DRAWING_MODE_LABELING, DRAWING_MODE_ERASING]:
                        tmp_dict = {}
                        tmp_dict['mode'] = 'modify'
                        tmp_dict['type'] = 'display'
                        tmp_dict['type_detail'] = 'drawing_label_data'
                        tmp_dict['label_number'] = selected_label_number
                        tmp_dict['indice'] = indice
                        self.display_to_core(tmp_dict)

                elif (e.buttons() and Qt.RightButton) and self.right_drawstart: # 드래그
                    if drawing_mode == DRAWING_MODE_LABELING:
                        # 드로잉 모드일때 오른쪽 마우스 클릭시 sub 드로잉 펜
                        selected_label_number = self.label_control_dict['select_sub_label_number']
                        if selected_label_number != LABEL_UNSELECTED:
                            indice = self.update_point_indice(cur_point=cur_point)
                            self.update_drawing(label_number=selected_label_number, indice=indice)
                            self.update_image_display(self.image_rgb)

                            tmp_dict = {}
                            tmp_dict['mode'] = 'modify'
                            tmp_dict['type'] = 'display'
                            tmp_dict['type_detail'] = 'drawing_label_data'
                            tmp_dict['label_number'] = selected_label_number
                            tmp_dict['indice'] = indice
                            self.display_to_core(tmp_dict)

                else: #일반 마우스 움직일 때
                    # if drawing_mode == DRAWING_MODE_LABELING: # 드로잉 용
                    #     pass
                    # elif drawing_mode == DRAWING_MODE_ERASING: # 지우개 용
                    #     pass
                    """
                    description
                    Modified by MyoungHwan(20240205): add graph preview mode when graph point erase mode
                    """
                    if drawing_mode in [DRAWING_MODE_DRAW_GRAPH_POINT, DRAWING_MODE_ERASE_GRAPH_POINT]:
                        # graph 예비 표시용
                        tmp_color = [255,255,0]
                        tmp_dict = {}
                        tmp_dict['mode'] = 1
                        tmp_dict['point'] = [y, x]
                        tmp_dict['point_data'] = copy.deepcopy(self.image_raw[y][x])
                        tmp_dict['color'] = copy.deepcopy(tmp_color)
                        tmp_dict['shape'] = [self.image_width_origin, self.image_height_origin, self.image_raw.shape[-1]]
                        self.display_to_graph(tmp_dict)

                    elif drawing_mode == DRAWING_MODE_RECTANGLE:
                        if self.prev_point:
                            self.display_scrollAreaWidgetContents.draw_rect_preview(cur_point)
                        else:
                            self.display_scrollAreaWidgetContents.remove_rect_preview()
                            
                    elif drawing_mode == DRAWING_MODE_POLYGON:
                        # self.prev_point is not empty means ellipse item is already in scene -> draw line and polygon with ellipse
                        self.polygonItem.updateCursorPos(QtCore.QPointF(cur_point[0], cur_point[1]))
                        if len(self.polygonItem.points) > 0:
                            if len(self.polygonItem.points) >= 3:
                                self.setMouseSnap()
                            self.polygonItem.update()

                if self.pen_obj_dict['pen_minimap']['form'].isVisible():
                    start_x, start_y, end_x, end_y = self.update_point_indice_minimap(cur_point=cur_point)
                    tmp_minimap = self.image_rgb[start_y:end_y, start_x:end_x].copy()
                    self.update_image_display_minimap(tmp_minimap)
            else:
                """
                    description
                    Implemented by Myounghwan(20240517) : 라벨링 중 마우스 포인터가 Display 영역 외로 나갈 경우 메모리 저장을 위한 코드
                    Modified by Myounghwan(20240529) : 라벨링 중 마우스 포인터가 Display 영역 외로 나갈 경우 메모리 저장을 위한 코드 이동
                """    
                if self.memory_record_status:
                    self.memory_record_status = False
                    self.check_diff(mode=1)
                    self.redo_memory = []
    
    def mouse_wheel(self, e, zoom:int) -> None:
        """
            @description: A function that is activated when the mouse wheel is scrolled
            @author : GaEun Hwang(2025.10.23)
        """
        if self.select_image_number != IMAGE_UNSELECTED:
            # update polygon cursor position and radius when in polygon drawing mode
            if self.display_control_dict['drawing_mode'] == DRAWING_MODE_POLYGON:
                pos = self.display_scrollAreaWidgetContents.mapToScene(e.pos())
                self.polygonItem.updateCursorPos(QtCore.QPoint(pos.x(), pos.y()))
                if self.polygonItem.isAvailableToMatch() == False:
                    self.polygonItem.isMatched = False
                self.polygonItem.updateRadius(zoom)

    def keyPressEvent(self, e) -> None:
        """
            @Description : 키보드를 누를 경우 활성화 되는 함수이다.
            @Author : MyoungHwan
            @History
                1. Modified by MyoungHwan(20240226) : 컨트롤 버튼 pressed 상태로 변할 때 변수추가
                2. Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                3. Improvemented by GaEun Hwang (2025.09.29): Added shortcut key 'W', 'S' for selecting label
        """
        if self.select_image_number != IMAGE_UNSELECTED:
            if e.key() == Qt.Key_Control:
                self.is_ctrl_key_pressed = True
                """
                    description
                    Modified by MyoungHwan(20240226) : 컨트롤 버튼 pressed 상태로 변할 때 변수추가
                """
                self.display_control_dict['key_pressed'] = True
                self.display_control_dict['temp_drawing_mode'] = self.display_control_dict['drawing_mode']
                self.display_control_dict['drawing_mode'] = DRAWING_MODE_NONE
                self.display_scrollAreaWidgetContents.updateDrag(True)

            if 49 <= e.key() <= 57: # 49, 50 ~ 57 -> 1,2 ~ 9
                if len(self.label_obj_dict.keys()):
                    selected_number = e.key() - 49
                    # not using sorted list because if add label when existing label added label is end of list
                    labelList = list(self.label_obj_dict.keys())
                    try:
                        # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                        select_label_obj = self.label_obj_dict[labelList[selected_number]]['obj_dict']['select']
                        select_label_obj.toggle()
                    except:
                        print(f"Occured Exception, Key value({selected_number}) label list out of range")
                else:
                    print("no label")
            
            if e.key() == Qt.Key_W or e.key() == Qt.Key_S:
                # W key -> select previous label
                # S key -> select next label
                if len(self.label_obj_dict.keys()) and self.label_control_dict['select_main_label_number'] != LABEL_UNSELECTED:
                    labelKeyList = list(self.label_obj_dict.keys())
                    selectedNumber = self.label_control_dict['select_main_label_number']
                    selectedNumberIndex = labelKeyList.index(selectedNumber)
                    if selectedNumberIndex != 0 and e.key() == Qt.Key_W:
                        selectNumber = labelKeyList[selectedNumberIndex-1]
                        selectLabelObj = self.label_obj_dict[selectNumber]['obj_dict']['select']
                        selectLabelObj.toggle()
                    elif selectedNumberIndex != len(labelKeyList)-1 and e.key() == Qt.Key_S:
                        selectNumber = labelKeyList[selectedNumberIndex+1]
                        selectLabelObj = self.label_obj_dict[selectNumber]['obj_dict']['select']
                        selectLabelObj.toggle()
                    # else: do nothing (when first label is selected and W key is pressed or when last label is selected and S key is pressed)
            
    def keyReleaseEvent(self, e) -> None:
        """
            @description :  키보드를 누르고 뗀 경우 활성화 되는 함수이다.
            @author : MyoungHwan
        """
        if self.select_image_number != IMAGE_UNSELECTED:
            if e.key() == Qt.Key_Control and self.is_ctrl_key_pressed:
                if self.display_control_dict['key_pressed']:
                    """
                        description
                        Modified by MyoungHwan(20240226) : 키보드가 눌러져있을 경우 초기화 진행, 컨트롤 버튼 pressed 상태 -> Released 상태로 변할 때 변수 초기화
                    """
                    self.is_ctrl_key_pressed = False
                    self.display_control_dict['drawing_mode'] = self.display_control_dict['temp_drawing_mode']
                    self.display_control_dict['temp_drawing_mode'] = DRAWING_MODE_NONE
                    self.display_scrollAreaWidgetContents.updateDrag(False)
                    self.display_control_dict['key_pressed'] = False
        
    def display_to_core(self, input:dict) -> None:
        """
            @description :  Display에서 core로 시그널을 보내기 위한 함수 선언문이다. Core DB에 대한 값을 업데이트하거나 조정하기 위한 함수로 쓰인다.
            @author : MyoungHwan
            @parameters
                1.	input(dict): Core DB업데이트를 위한 dictionary

        """
        self.display_to_core_signal.emit(input)

    def display_to_pen_style(self, input:dict) -> None:
        """
            @description : display에서 pen style로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 pen style에 최종적으로 전달된다. 선택한 라벨번호에 대한 업데이트 하기위해 사용
            @author : MyoungHwan
            @parameters
                1.	input(dict): pen style 업데이트를 위한 dictionary

        """
        self.display_to_pen_style_signal.emit(input)
    
    def display_to_graph(self, input:dict) -> None:
        """
            @description : Display에서 graph로 시그널을 보내기 위한 함수 선언문이다. 해당 함수를 통해 그래프 기능을 사용한다.
            @author : MyoungHwan
            @parameters
                1.	input(dict): graph 기능을 사용하기 위한 dictionary
        """
        self.display_to_graph_signal.emit(input)

    def display_to_labeling_mode_main(self, input:dict) -> None:

        self.display_to_labeling_mode_main_signal.emit(input)

    def init_Ui_label_main_display(self, Form) -> None:
        """
            @description : Diplay UI 생성을 위한 초기 선언문이다.
            @author : MyoungHwan
            @parameters
                1.	Form(object): PyQt widget object
        """
        Form.setObjectName("Form")
        # Form.resize(1029, 738)
        Form.setWindowTitle("Display_Form")
        Form.setStyleSheet(stylesheet)

        self.display_gridLayout = QtWidgets.QGridLayout(Form)
        self.display_gridLayout.setObjectName("display_gridLayout")
        
        self.display_scrollAreaWidgetContents = Display_viewer()
        self.display_scrollAreaWidgetContents.viewer_signal.connect(self.mouse_control)

        self.display_scrollbar_vertical = self.display_scrollAreaWidgetContents.verticalScrollBar()
        self.display_scrollbar_horizon = self.display_scrollAreaWidgetContents.horizontalScrollBar()

        self.default_background = QtGui.QPixmap(background_image_path)
        self.display_scrollAreaWidgetContents.initPhoto(self.default_background, dragmode=0)

        QtCore.QMetaObject.connectSlotsByName(Form)

    def setup_Ui_label_main_display(self) -> None:
        """
            @Description : 초기화된 display 리스트의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
            @Author : MyoungHwan
            @History
                1. Modified by MyoungHwan (2024.12.13): focus widget 변수 제거
        """
        self.display_gridLayout.setContentsMargins(0, 0, 0, 0)
        self.display_scrollAreaWidgetContents.setContentsMargins(0, 0, 0, 0)
        self.display_gridLayout.addWidget(self.display_scrollAreaWidgetContents, 0, 0, 1, 1)

    def resizeEvent(self, _) -> None:
        """
            @description : GUI 창 크기 변경시 widget 사이즈를 변경하기 위한 함수이다.
            @author : MyoungHwan
        """
        print("display resize event")
        if self.select_image_number == IMAGE_UNSELECTED:
            self.display_scrollAreaWidgetContents.initPhoto(self.default_background, dragmode=0, init=True)
        else:
            self.update_image_display(self.image_rgb)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Display_Form()
    # ui.init_Ui_label_main_display(Form)
    # Form.show()
    sys.exit(app.exec_())
