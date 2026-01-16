"""
    ElroiKit

    Copyright 2024. Elroilab All rights reserved.
"""
import numpy as np

# pyqt
QT_MAX_SIZE = 16777215

# ui page index
LABELLING = 0

# pen mode
PEN_MODE_NONE = -1
PEN_MODE_ZOOM_IN = 0
PEN_MODE_ZOOM_OUT = 1
PEN_MODE_PARTIAL_ZOOM = 2
PEN_MODE_DRAWING = 3
PEN_MODE_IMAGE_MOVING = 4
PEN_MODE_ERASER = 5
PEN_MODE_BRIGHT = 6
PEN_MODE_UNDO = 7
PEN_MODE_REDO = 8
PEN_MODE_PAINTING = 9
PEN_MODE_MINIMAP = 10
PEN_MODE_ROT90 = 11
PEN_MODE_HFLIP = 12
PEN_MODE_VFLIP = 13
PEN_MODE_RECTANGLE = 14
PEN_MODE_POLYGON = 15
PEN_MODE_OPACITY = 16
PEN_MODE_IMAGE = 17

# pen sub ui mode
PEN_SUB_MODE_PEN = 0
PEN_SUB_MODE_ERASER = 1
PEN_SUB_MODE_BRIGHT = 2
PEN_SUB_MODE_MINIMAP = 3
PEN_SUB_MODE_OPACITY = 4

# drawing mode
DRAWING_MODE_NONE = -1
DRAWING_MODE_LABELING = 0
DRAWING_MODE_ERASING = 1
DRAWING_MODE_DRAW_GRAPH_POINT = 2
DRAWING_MODE_IMAGE_MOVING = 3
DRAWING_MODE_ZOOM_IN = 4
DRAWING_MODE_ERASE_GRAPH_POINT = 5
DRAWING_MODE_PAINTING = 6
DRAWING_MODE_RECTANGLE = 7
DRAWING_MODE_POLYGON = 8
DRAWING_MODE_OPACITY = 9
DRAWING_MODE_IMAGE = 10

# view type
VIEW_TYPE_RGB = 0
VIEW_TYPE_CMF = 1
VIEW_TYPE_DL = 2

# label
LABEL_UNSELECTED = -1
LABEL_IGNORED = 0

# image
IMAGE_UNSELECTED = -1

# graph view mode
GRAPH_VIEW_MODE_SELECTIVE_COLOR = 0
GRAPH_VIEW_MODE_LABEL_COLOR = 1

# graph filter
GRAPH_FILTER_NONE = "None"
GRAPH_FILTER_SAVITZKY_GOLAY = "Savitzky-Golay Filter"
GRAPH_FILTER_GAUSSIAN = "Gaussian Filter"
GRAPH_FILTER_LDA = "LDA"

# graph function
GRAPH_DISPLAY_ALL = 0
GRAPH_DISPLAY_PARTIAL = 1
GRAPH_DISPLAY_PREVIEW = 2
GRAPH_DISPLAY_SUB_FORM = 3
GRAPH_SETTING = 4
GRAPH_DRAW = 5
GRAPH_ERASE = 6
GRAPH_CLEAR = 7

# graph group signal (SEND)
GRAPH_GROUP_CONVERT_SELECTIVE_VIEW = "convert_selective_view_graph"
GRAPH_GROUP_CONVERT_LABEL_VIEW = "convert_label_view_graph"
GRAPH_GROUP_SELECT = "select_graph_group"
GRAPH_GROUP_COLOR_CHANGE = "select_graph_group_color"
GRAPH_GROUP_REMOVE = "remove_graph_group"
GRAPH_GROUP_REMOVE_ALL = "remove_all_graph_group"
GRAPH_GROUP_DRAW_GRAPH = "draw_graph"
GRAPH_GROUP_REMOVE_GRAPH = "remove_graph"

# graph group signal (RECEIVE)
# from label
ADD_LABEL_GRAPH_GROUP = "create_label_class"
CHANGE_LABEL_GRAPH_GROUP_NUMBER = "change_label_number"
CHANGE_LABEL_GRAPH_GROUP_NAME = "change_label_name"
CHANGE_LABEL_GRAPH_GROUP_COLOR = "change_label_color"
MERGE_LABEL = "merge_label_class"
REMOVE_LABEL_CLASS = "remove_label_class"
SELECT_LABEL_CLASS = "select_label_class"
SELECT_LABEL_PEN = "select_label_pen"

#from display
CHECK_GRAPH_POINT = "check_graph_point"
REMOVE_GRAPH_POINT = "remove_graph_point"

#from graph
GRAPH_CHECK_ON = "graph_draw_on"
GRAPH_CHECK_OFF = "graph_draw_off"
GRAPH_ERASE_ON = "graph_erase_on"
GRAPH_ERASE_OFF = "graph_erase_off"

# graph group
GRAPH_GROUP_NONE = -1
GRAPH_GROUP_SELECT = 0

# graph present
GRAPH_PRESENT_NONE = -1

# mouse event
MOUSE_EVENT_PRESS = 0
MOUSE_EVENT_MOVE = 1
MOUSE_EVENT_RELEASE = 2
MOUSE_EVENT_WHEEL = 3

# label correction mode
LABEL_CORRECTION_MODE_WORKER_1 = 0
LABEL_CORRECTION_MODE_WORKER_2 = 1
LABEL_CORRECTION_START = 2
LABEL_CORRECTION_STOP = 3
LABEL_CORRECTION_DATALIST = 4
LABEL_CORRECTION_CLEAR = 5
LABEL_CORRECTION_THRESHOLD = 6

# visualization mode
VISUALIZATION_MODE_CALIBRATION = 0
VISUALIZATION_MODE_ADVANCED = 1

# visualization rgb change
RGB_SLIDER_CHANGE = 0
RGB_COMBOBOX_CHANGE = 1

# model parameter
MODEL_SELECTION_AUPR = 0
MODEL_SELECTION_LOSS = 1

# data label type
DATA_IGNORED = 0
DATA_BACKGROUND = 1
DATA_NORMAL = 2
DATA_ABNORMAL = 3

# Common Abnormal Auto Labeling
PATCH_SIZE = 3
# remain time update size
UPDATE_SIZE = 200

# metadata data type
MI_INT:np.byte = 0
MI_FLOAT:np.byte = 1
MI_STRING: np.byte = 2
MI_BOOL: np.byte = 3
MI_INT_ARRAY: np.byte = 11
MI_FLOAT_ARRAY: np.byte = 12
MI_STRING_ARRAY: np.byte = 13
MI_BOOL_ARRAY: np.byte = 14
MI_INT_ARRAY_TUPLE: np.byte = 21
MI_FLOAT_ARRAY_TUPLE: np.byte  = 22
MI_STRING_ARRAY_TUPLE: np.byte  = 23
MI_BOOL_ARRAY_TUPLE: np.byte  = 24

pen_mode_to_draw_dict = {
    PEN_MODE_DRAWING: DRAWING_MODE_LABELING,
    PEN_MODE_PARTIAL_ZOOM: DRAWING_MODE_ZOOM_IN,
    PEN_MODE_IMAGE_MOVING: DRAWING_MODE_IMAGE_MOVING,
    PEN_MODE_ERASER: DRAWING_MODE_ERASING,
    PEN_MODE_PAINTING: DRAWING_MODE_PAINTING,
    PEN_MODE_RECTANGLE: DRAWING_MODE_RECTANGLE,
    PEN_MODE_POLYGON: DRAWING_MODE_POLYGON,
    PEN_MODE_OPACITY: DRAWING_MODE_OPACITY,
    PEN_MODE_IMAGE: DRAWING_MODE_IMAGE
}

draw_to_pen_dict = {v: k for k, v in pen_mode_to_draw_dict.items()}

pen_obj_key_to_mode_dict = {
    'pen_scale_up': PEN_MODE_ZOOM_IN,
    'pen_scale_down': PEN_MODE_ZOOM_OUT,
    'pen_part_scale_up': PEN_MODE_PARTIAL_ZOOM,
    'pen_part_move': PEN_MODE_IMAGE_MOVING,
    'pen_bright': PEN_MODE_BRIGHT,
    'pen_undo': PEN_MODE_UNDO,
    'pen_redo': PEN_MODE_REDO,
    'pen_minimap': PEN_MODE_MINIMAP,
    'pen_rot90': PEN_MODE_ROT90,
    'pen_hflip': PEN_MODE_HFLIP,
    'pen_vflip': PEN_MODE_VFLIP,
    'pen_draw_type': PEN_MODE_DRAWING,
    'pen_rectangle': PEN_MODE_RECTANGLE,
    'pen_polygon': PEN_MODE_POLYGON,
    'pen_eraser': PEN_MODE_ERASER,
    'pen_painting': PEN_MODE_PAINTING,
    'pen_opacity': PEN_MODE_OPACITY,
    'pen_image': PEN_MODE_IMAGE
}

commonAbnormalDict = {
    "3" : {"label_name": "플라스틱_검정"},
    "4" : {"label_name": "플라스틱_파랑"},
    "5" : {"label_name": "플라스틱_빨강"},
    "6" : {"label_name": "플라스틱_연두"},
    "7" : {"label_name": "비닐_파랑"},
    "8" : {"label_name": "파지"},
    "9" : {"label_name": "유리_파랑"},
    "10" : {"label_name": "유리_빨강"},
    "13" : {"label_name": "와셔"},
    "14" : {"label_name": "고무줄"},
    "15" : {"label_name": "칼날"},
    "16" : {"label_name": "헝겊"},
    "17" : {"label_name": "면봉"},
    "18" : {"label_name": "라텍스"},
    "19" : {"label_name": "플라스틱_노랑"},
    "20" : {"label_name": "전선"},
    "23" : {"label_name": "유리_초록"}
}

mode_to_pen_obj_key_dict = {v: k for k, v in pen_obj_key_to_mode_dict.items()}

def switch_pen_to_draw(value):
    """pen_mode를 drawing_mode로 또는 drawing_mode를 pen_mode로 변환합니다."""
    # pen_mode에서 drawing_mode로 변환 시도
    if value in pen_mode_to_draw_dict:
        return pen_mode_to_draw_dict[value]
    # drawing_mode에서 pen_mode로 변환 시도
    elif value in draw_to_pen_dict:
        return draw_to_pen_dict[value]
    # 둘 다 아닌 경우
    return "Invalid choice"


def switch_obj_key_to_pen(value):
    """오브젝트 키를 펜 모드로 또는 펜 모드를 오브젝트 키로 변환합니다."""
    # 오브젝트 키에서 펜 모드로 변환 시도
    if value in pen_obj_key_to_mode_dict:
        return pen_obj_key_to_mode_dict[value]
    # 펜 모드에서 오브젝트 키로 변환 시도
    elif value in mode_to_pen_obj_key_dict:
        return mode_to_pen_obj_key_dict[value]
    # 둘 다 아닌 경우
    return "Invalid choice"
