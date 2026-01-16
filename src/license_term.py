import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from utils.shared import license_txt_path
# from PyQt5.QtWidgets import QApplication


class License_slot(QObject):
    top_to_mid = pyqtSignal(dict)

class License_Form(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.init_class()
        self.init_variable()
        self.init_Ui()
        self.setup_Ui()
        self.init_Function()

        if __name__ == "__main__":
            self.show()

    def init_class(self):
        pass
        # self.license_slot = License_slot()
        # self.license_slot_signal = self.license_slot.top_to_mid
        # self.license_slot_signal.connect(self.recv_)
        # self.license_top_ui = License_top_Form(Sync=self.license_slot)
        # self.license_top_ui.show()

    def init_variable(self):
        self.title="OSS(Open Source Software) Notice | ELROILAB Kit"
        self.copylight_str = """
        This application is Copyright © ELROILAB Corp. All rights reserved.\n    
        The following sets forth attribution notices for third party software that may be contained in this application.
        """
        self.oss_term = ""
        with open(license_txt_path, encoding="UTF8") as data :
            # read함수는 전체 내용 전체를 문자열로 불러온다.
            self.oss_term = data.read()
        
        self.click_sw = False
        self.window_moveable = False
        self.init_sw = True
        self.normal_width = self.width()

    def init_Ui(self):

        # self.MainWindow = QtWidgets.QWidget()
        self.setObjectName("license_term_mid")
        self.setWindowTitle("")
        self.resize(450, 500)
        self.setWindowFlag(Qt.FramelessWindowHint)

        self.License_vertical = QtWidgets.QVBoxLayout()
        self.License_vertical.setObjectName("License_vertical")

        self.License_title_label = QtWidgets.QLabel()
        self.License_title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.License_title_label.setObjectName("License_title_label")
        self.License_title_label.setText(self.title)
        
        self.License_sub_title_label = QtWidgets.QLabel()
        # self.License_sub_title_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.License_sub_title_label.setObjectName("License_sub_title_label")
        self.License_sub_title_label.setText(self.copylight_str)

        self.License_ossterm_textedit = QtWidgets.QTextEdit()
        self.License_ossterm_textedit.setObjectName("License_ossterm_textedit")
        self.License_ossterm_textedit.setReadOnly(True)
        self.License_ossterm_textedit.setText(self.oss_term)

        self.License_horizon = QtWidgets.QHBoxLayout()
        self.License_horizon.setObjectName("License_horizon")

        self.License_exit_btn = QtWidgets.QPushButton()
        self.License_exit_btn.setObjectName("License_exit_btn")
        self.License_exit_btn.setText("Done")

        self.setLayout(self.License_vertical)

    def setup_Ui(self):
        self.License_exit_btn.setMinimumSize(QtCore.QSize(50, 25))
        self.License_exit_btn.setMaximumSize(QtCore.QSize(50, 25))

        # self.License_vertical.addWidget(self.license_top_ui)
        self.License_vertical.addWidget(self.License_title_label)
        self.License_vertical.addWidget(self.License_sub_title_label)
        self.License_vertical.addWidget(self.License_ossterm_textedit)
        self.License_horizon.addStretch()
        self.License_horizon.addWidget(self.License_exit_btn)
        self.License_vertical.addLayout(self.License_horizon)

        self.License_horizon.setContentsMargins(0,0,0,0)


    def init_Function(self):
        self.License_exit_btn.clicked.connect(self.close)
    
    def mousePressEvent(self, e):
        """윈도우 타이틀을 클릭했을 때 발동하는 함수이다. merge mainwindow에 상태를 전달한다.
        """
        if e.buttons() == QtCore.Qt.LeftButton:
            self.click_sw = True
            self.window_moveable = True
            self.offset= e.globalPos()

    def mouseReleaseEvent(self, e):
        """윈도우 타이틀을 클릭후 뗏을 때 발동하는 함수이다. merge mainwindow에 상태를 전달한다.
        """
        self.click_sw = False
        self.window_moveable = False
        self.offset = e.globalPos()

    def mouseMoveEvent(self, e):
        """윈도우 타이틀을 클릭후 움직일때 발동하는 함수이다. 드래그 하여 UI 위치를 이동하거나 최대일 때 최소로 바꿔준다.
        """
        if e.buttons() == QtCore.Qt.LeftButton and self.window_moveable:
            if self.init_sw:
                mid_value = self.normal_width//2
                po = QtCore.QPoint(mid_value, 10)
                value = e.globalPos() - po
                self.init_sw = False
            else:
                value = self.pos() + e.globalPos() - self.offset
            self.move(value)
            self.offset = e.globalPos()

    # @pyqtSlot(dict)
    # def recv_(self, output):
    #     if output['mode'] == 0:
    #         self.close()
    #     elif output['mode'] == 1:
    #         self.window_moveable =  output['bool']
    #         self.offset = output['offset']
    

    
# class License_top_Form(QtWidgets.QWidget):
#     def __init__(self, Sync = None):
#         super().__init__()
#         self.init_variable(Sync)
#         self.init_Ui(self)
#         self.setup_Ui(self)
#         self.init_Function()

#         if __name__ == "__main__":
#             self.show()

#     def init_variable(self, Sync=None):
#         self.Sync = Sync
#         self.license_slot_signal = self.Sync.top_to_mid
#         self.click_sw = False
        
#         self.top_title="OSS(Open Source Software) Notice | ELROILAB Kit"

#     def init_Ui(self, MainWindow):
#         MainWindow.setObjectName("license_term_top")
#         MainWindow.setWindowTitle("")
#         MainWindow.resize(450, 50)
#         MainWindow.setWindowFlag(Qt.FramelessWindowHint)

#         self.License_top_title_label = QtWidgets.QLabel()
#         self.License_top_title_label.setAlignment(QtCore.Qt.AlignCenter)
#         self.License_top_title_label.setObjectName("License_top_title_label")
#         self.License_top_title_label.setText("test")
  
#         self.License_top_horizon = QtWidgets.QHBoxLayout(MainWindow)
#         self.License_top_horizon.setObjectName("License_top_horizon")

#         self.License_top_exit_btn = QtWidgets.QPushButton()
#         self.License_top_exit_btn.setObjectName("License_top_exit_btn")
#         self.License_top_exit_btn.setText("Do")

#     def setup_Ui(self, MainWindow):
#         self.License_top_exit_btn.setMinimumSize(QtCore.QSize(50, 25))
#         self.License_top_exit_btn.setMaximumSize(QtCore.QSize(50, 25))

#         self.License_top_horizon.setContentsMargins(0,0,0,0)


#         self.License_top_horizon.addWidget(self.License_top_title_label)
#         self.License_top_horizon.addStretch()
#         self.License_top_horizon.addWidget(self.License_top_exit_btn)

#     def init_Function(self):
#         self.License_top_exit_btn.clicked.connect(lambda : self.mode_(mode=0))

#     def mode_(self, mode=None):
#         tmp_dict = {}
#         tmp_dict['mode'] = mode
#         self.license_slot_signal.emit(tmp_dict)
#         if mode == 0:#exit
#             self.close()

        
#     def mousePressEvent(self, e):
#         """윈도우 타이틀을 클릭했을 때 발동하는 함수이다. merge mainwindow에 상태를 전달한다.
#         """
#         if e.buttons() == QtCore.Qt.LeftButton:
#             self.click_sw = True
#             tmp_dict = {}
#             tmp_dict['mode'] = 1
#             tmp_dict['bool'] = True
#             tmp_dict['offset'] = e.globalPos()
#             self.license_slot_signal.emit(tmp_dict)

#     def mouseReleaseEvent(self, e):
#         """윈도우 타이틀을 클릭후 뗏을 때 발동하는 함수이다. merge mainwindow에 상태를 전달한다.
#         """
#         self.click_sw = False
#         tmp_dict = {}
#         tmp_dict['mode'] = 1
#         tmp_dict['bool'] = False
#         tmp_dict['offset'] = e.globalPos()
#         self.license_slot_signal.emit(tmp_dict)



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = License_Form()
    sys.exit(app.exec_())