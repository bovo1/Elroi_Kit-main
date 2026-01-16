"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

from PyQt5 import QtCore


class Sub_Core_Sync_Advanced(QtCore.QObject):
    """기능들간 실시간 상태 업데이트를 위한 slot/signal 클래스
    """
   

    def __init__(self, core_obj_dict):
        super().__init__()
        self.core_obj_dict = core_obj_dict