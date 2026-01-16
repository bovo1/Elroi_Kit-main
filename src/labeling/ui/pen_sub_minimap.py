from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import QSize, Qt, pyqtSlot


class Pen_minimap_Form(QtWidgets.QMainWindow):
    """Pen sub style ui, 펜 설정에 대한 모든 기능을 처리하기 위한 클래스
    """
    def __init__(self, Pen_Sync=None):
        super().__init__()

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.init(Sync=Pen_Sync)
        self.init_variable()
        self.init_Ui_label_main_pen_minimap(self)
        self.setup_Ui_label_main_pen_minimap()
        self.init_Function()


        if __name__ == "__main__":
            self.show()
    
    def init(self, Sync=None):
        """Pen sub 리스트 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.Sync = Sync
        
        self.pen_control_dict = self.Sync.pen_control_dict
        self.pen_obj_dict = self.Sync.pen_obj_dict

    def init_variable(self):
        self.click_sw = False
        self.window_moveable = False
        self.init_sw = True
        self.normal_width = self.width()
        self.normal_height = self.height()

    def init_Ui_label_main_pen_minimap(self, Mainwindow):
        """Pen sub 리스트 UI 생성을 위한 초기 선언문이다.
                Parmeters
                1.	Form(object): PyQt widget object

        """
        Mainwindow.setObjectName("pen_minimap_form")
        Mainwindow.resize(150, 150)
        # Mainwindow.setStyleSheet(stylesheet)

        self.centralwidget = QtWidgets.QWidget(Mainwindow)
        self.centralwidget.setObjectName("centralwidget")

        self.pen_main_grid = QtWidgets.QGridLayout(self.centralwidget)
        self.pen_main_grid.setObjectName("pen_main_grid")

        self.pen_minimap_picture_widget = QtWidgets.QWidget()
        self.pen_minimap_picture_widget.setObjectName("pen_minimap_picture_widget")

        self.pen_minimap_picture_vertical = QtWidgets.QVBoxLayout(self.pen_minimap_picture_widget)
        self.pen_minimap_picture_vertical.setObjectName("pen_minimap_picture_vertical")

        self.pen_minimap_picture = QtWidgets.QWidget()
        self.pen_minimap_picture.setObjectName("pen_minimap_picture")

        self.pen_minimap_picture_label = QtWidgets.QLabel(self.pen_minimap_picture)
        self.pen_minimap_picture_label.setText("")
        self.pen_minimap_picture_label.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_minimap_picture_label.setObjectName("label")
        
        QtCore.QMetaObject.connectSlotsByName(Mainwindow)
        Mainwindow.setCentralWidget(self.centralwidget)


    def setup_Ui_label_main_pen_minimap(self):
        """초기화된 Pen sub ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
        """
        self.pen_main_grid.addWidget(self.pen_minimap_picture_widget, 1, 0, 1, 1)

        self.pen_main_grid.setContentsMargins(5,5,5,5)

        self.pen_minimap_picture_vertical.addWidget(self.pen_minimap_picture_label)


    def init_Function(self):
        """Pen sub Ui에 존재하는 기능들에 대한 connect 함수를 정의한다.
        """
        pass
    
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
                mid_value = self.normal_width//8
                mid_value2 = self.normal_height//8
                po = QtCore.QPoint(mid_value, mid_value2)
                value = e.globalPos() - po
                self.init_sw = False
            else:
                value = self.pos() + e.globalPos() - self.offset
            self.move(value)
            self.offset = e.globalPos()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Mainwindow = QtWidgets.QWidget()
    ui = Pen_minimap_Form()
    sys.exit(app.exec_())
