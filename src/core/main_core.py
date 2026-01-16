from PyQt5.QtCore import QObject
from .main_core_sync import Main_Core_Sync
from .sub_core_labeling import Sub_Core_Labeling


class Main_Core(QObject):
    """각 기등들 간 상태를 주고받기 위해 호출하는 클래스. Core DB를 통해 데이터 정보에 대해 저장할 수 있다.
    """
    def __init__(self):
        super().__init__()
        self.Main_Core_Sync = Main_Core_Sync()

        self.Sub_Core_Sync_Labeling = self.Main_Core_Sync.Sub_Core_Sync_Labeling
        self.Sub_Core_Sync_Training = self.Main_Core_Sync.Sub_Core_Sync_Training
        self.Sub_Core_Sync_Advanced = self.Main_Core_Sync.Sub_Core_Sync_Advanced
        self.core_obj_dict = self.Main_Core_Sync.core_obj_dict


        # self.Sub_Core_Labeling = Sub_Core_Labeling(Sub_Core_Sync_Labeling=self.Sub_Core_Sync_Labeling)
        self.Sub_Core_Labeling = Sub_Core_Labeling(Sync=self.Main_Core_Sync)




"""
    - drawing_mode
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
"""