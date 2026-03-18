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
    def __init__(self, lang=None):
        super().__init__()
        self.lang = lang

        self.status_image_status = QLabel()
        self.lang.set("main", "mainCoreSync", "statusImage", self.status_image_status)
        self.imagePathValue = QLabel()

        self.status_labeling_status = QLabel()
        self.lang.set("main", "mainCoreSync", "statusLabel", self.status_labeling_status)
        self.labelNumValue = QLabel()

        self.status_pointer_status = QLabel()
        self.lang.set("main", "mainCoreSync", "statusCoordinate", self.status_pointer_status)
        self.pixelCoordinateValue = QLabel()
        #function object
        self.core_obj_dict = {
            # Modified by MyoungHwan (2025.03.14): current focus widget 변수 추가
            "cur_focus_widget":None,
            "status_image_status": [self.status_image_status, self.imagePathValue],
            "status_labeling_status": [self.status_labeling_status, self.labelNumValue],
            "status_pointer_status": [self.status_pointer_status, self.pixelCoordinateValue],
            "status_training_status": QLabel("")
        }
        self.core_obj_dict["status_image_status"][0].setMargin(5)
        self.core_obj_dict["status_labeling_status"][0].setMargin(5)
        self.core_obj_dict["status_pointer_status"][0].setMargin(5)
        self.core_obj_dict["status_training_status"].setMargin(5)

        self.Sub_Core_Sync_Labeling = Sub_Core_Sync_Labeling(self.core_obj_dict)
        self.Sub_Core_Sync_Training = Sub_Core_Sync_Training(self.core_obj_dict)
        self.Sub_Core_Sync_Advanced = Sub_Core_Sync_Advanced(self.core_obj_dict)