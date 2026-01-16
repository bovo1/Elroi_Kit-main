"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QLabel

from .sub_core_sync_labeling import Sub_Core_Sync_Labeling
from .sub_core_sync_training import Sub_Core_Sync_Training
from .sub_core_sync_advanced import Sub_Core_Sync_Advanced


class Main_Core_Sync(QObject):
    """
        @Description: 각 기등들 간 상태를 주고받기 위해 호출하는 클래스. Core DB를 통해 데이터 정보에 대해 저장할 수 있다.
        @Author: MyoungHwan
        @History
            1. Modified by MyoungHwan (2024.12.13): focus widget 변수 제거
            2. Modified by MyoungHwan (2025.03.14): current focus widget 변수 추가
    """
    def __init__(self):
        super().__init__()

        #function object
        self.core_obj_dict = {
            # Modified by MyoungHwan (2025.03.14): current focus widget 변수 추가
            "cur_focus_widget":None,
            "status_image_status": QLabel("Image :   "),
            "status_labeling_status": QLabel("Label :  "),
            "status_pointer_status": QLabel("Current Point :  "),
            "status_training_status": QLabel("")
        }
        self.core_obj_dict["status_image_status"].setMargin(5)
        self.core_obj_dict["status_labeling_status"].setMargin(5)
        self.core_obj_dict["status_pointer_status"].setMargin(5)
        self.core_obj_dict["status_training_status"].setMargin(5)

        self.Sub_Core_Sync_Labeling = Sub_Core_Sync_Labeling(self.core_obj_dict)
        self.Sub_Core_Sync_Training = Sub_Core_Sync_Training(self.core_obj_dict)
        self.Sub_Core_Sync_Advanced = Sub_Core_Sync_Advanced(self.core_obj_dict)