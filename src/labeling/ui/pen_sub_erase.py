from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtGui import QBrush, QPen
from PyQt5.QtCore import QSize, Qt
from labeling.stylesheet.stylesheet_pen_sub_erase import stylesheet
from constants.constants import QT_MAX_SIZE

class Pen_eraser_Form(QtWidgets.QWidget):
    """Pen sub eraser ui, 펜 설정에 대한 모든 기능을 처리하기 위한 클래스
    """
    def __init__(self, Pen_Sync, lang):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.init(Sync=Pen_Sync, lang=lang)
        self.init_Ui_label_main_pen_eraser(self)
        self.setup_Ui_label_main_pen_eraser()
        self.init_Function()

        if __name__ == "__main__":
            self.show()

    def init(self, Sync=None, lang=None):
        """Pen sub 리스트 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.lang = lang
        self.Sync = Sync
        self.pen_eraser_to_core_signal = self.Sync.pen_eraser_to_core_signal
        self.pen_eraser_to_display_signal = self.Sync.pen_eraser_to_display_signal
        self.pen_control_dict = self.Sync.pen_control_dict
        
        self.image_width = 150
        self.image_height = 60
        self.image = QImage(QSize(self.image_width, self.image_height), QImage.Format_RGB32)
        self.image.fill(QColor(83, 83, 83))



        
    def init_Ui_label_main_pen_eraser(self, Form):
        """Pen sub 리스트 UI 생성을 위한 초기 선언문이다.
                Parmeters
                1.	Form(object): PyQt widget object

        """
        Form.setObjectName("pen_sub_erase_form")
        Form.resize(150, 150)
        Form.setStyleSheet(stylesheet)


        self.pen_main_grid = QtWidgets.QGridLayout(Form)
        self.pen_main_grid.setObjectName("pen_main_grid")

        self.pen_eraser_main_title_widget = QtWidgets.QWidget()
        self.pen_eraser_main_title_widget.setObjectName("pen_eraser_main_title_widget")

        self.pen_eraser_main_title_horizon = QtWidgets.QHBoxLayout(self.pen_eraser_main_title_widget)
        self.pen_eraser_main_title_horizon.setObjectName("pen_eraser_main_title_horizon")

        self.pen_eraser_main_title = QtWidgets.QLabel()
        self.pen_eraser_main_title.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_eraser_main_title.setObjectName("pen_eraser_main_title")
        self.lang.set("labeling", "pen_sub_erase", "pen_eraser_main_title", self.pen_eraser_main_title)

        self.pen_eraser_picture_widget = QtWidgets.QWidget()
        self.pen_eraser_picture_widget.setObjectName("pen_eraser_picture_widget")

        self.pen_eraser_picture_vertical = QtWidgets.QVBoxLayout(self.pen_eraser_picture_widget)
        self.pen_eraser_picture_vertical.setObjectName("pen_eraser_picture_vertical")

        self.pen_eraser_picture_label = QtWidgets.QLabel()
        self.pen_eraser_picture_label.setText("")
        self.pen_eraser_picture_label.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_eraser_picture_label.setObjectName("pen_eraser_picture_label")


        self.pen_eraser_static_horizon = QtWidgets.QHBoxLayout()
        self.pen_eraser_static_horizon.setObjectName("pen_eraser_static_horizon")

        self.pen_eraser_static_size = QtWidgets.QLabel()
        self.pen_eraser_static_size.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_eraser_static_size.setObjectName("pen_eraser_static_size")
        self.lang.set("labeling", "pen_sub_erase", "pen_eraser_static_size", self.pen_eraser_static_size)

        self.pen_eraser_static_edit = QtWidgets.QLineEdit()
        self.pen_eraser_static_edit.setMaximumSize(QtCore.QSize(40, QT_MAX_SIZE))
        self.pen_eraser_static_edit.setObjectName("pen_eraser_static_edit")
        self.pen_eraser_static_edit.setReadOnly(True)
        self.pen_eraser_static_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_eraser_static_edit.setText("1")

        self.pen_eraser_static_pix = QtWidgets.QLabel()
        self.pen_eraser_static_pix.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_eraser_static_pix.setObjectName("pen_eraser_static_pix")
        self.lang.set("labeling", "pen_sub_erase", "pen_eraser_static_pix", self.pen_eraser_static_pix)

        self.pen_eraser_range_widget = QtWidgets.QWidget()
        self.pen_eraser_range_widget.setObjectName("pen_eraser_range_widget")

        self.pen_eraser_range_vertical = QtWidgets.QVBoxLayout(self.pen_eraser_range_widget)
        self.pen_eraser_range_vertical.setObjectName("pen_eraser_range_vertical")

        self.pen_eraser_range_slider = QtWidgets.QSlider()
        self.pen_eraser_range_slider.setOrientation(QtCore.Qt.Horizontal)
        self.pen_eraser_range_slider.setObjectName("pen_eraser_range_slider")
        self.pen_eraser_range_slider.setTickPosition(2)
        self.pen_eraser_range_slider.setPageStep(1)
        self.pen_eraser_range_slider.setRange(1, 5)

        QtCore.QMetaObject.connectSlotsByName(Form)


    def setup_Ui_label_main_pen_eraser(self):
        """초기화된 Pen sub ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
        """
        self.pen_main_grid.addWidget(self.pen_eraser_main_title_widget, 0, 0, 1, 1)
        self.pen_main_grid.addWidget(self.pen_eraser_picture_widget, 1, 0, 1, 1)
        self.pen_main_grid.addWidget(self.pen_eraser_range_widget, 2, 0, 1, 1)
        self.pen_main_grid.setContentsMargins(5,5,5,5)

        self.pen_eraser_main_title_horizon.addWidget(self.pen_eraser_main_title)

        self.pen_eraser_static_horizon.addWidget(self.pen_eraser_static_size)
        self.pen_eraser_static_horizon.addWidget(self.pen_eraser_static_edit)
        self.pen_eraser_static_horizon.addWidget(self.pen_eraser_static_pix)
        
        self.pen_eraser_picture_vertical.addWidget(self.pen_eraser_picture_label)
        self.pen_eraser_range_vertical.addLayout(self.pen_eraser_static_horizon)
        self.pen_eraser_range_vertical.addWidget(self.pen_eraser_range_slider)

        
        self.pix = QPixmap(self.image)
        self.pen_eraser_picture_label.setPixmap(self.pix)    
        self.painter = QtGui.QPainter(self.pix)
        self.painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        self.painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        size = 4
        self.painter.drawEllipse(self.image_width//2 - size//2, self.image_height//2 - size//2, size, size)
        self.painter.end()
        self.pen_eraser_picture_label.setPixmap(self.pix)


    def init_Function(self):
        """Pen sub Ui에 존재하는 기능들에 대한 connect 함수를 정의한다.
        """
        self.pen_eraser_range_slider.valueChanged.connect(lambda value=self.pen_eraser_range_slider : self.slider_value_change(value=value))

    def slider_value_change(self, value=0):
        """지우개 사이즈를 변경하기 위한 함수이다. 현재 사용하지 않으며 추후 업데이트할 예정
                Parameters
                1.  value(int) : 펜 사이즈
        """
        self.pen_eraser_static_edit.setText(str(value))
        self.pix = QPixmap(self.image)
        self.pen_eraser_picture_label.setPixmap(self.pix)    
        self.painter = QtGui.QPainter(self.pix)
        self.painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        self.painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        size = value * 4
        self.painter.drawEllipse(self.image_width//2 - size//2, self.image_height//2 - size//2, size, size)
        self.painter.end()
        self.pen_eraser_picture_label.setPixmap(self.pix)

        self.pen_control_dict['pen_eraser_size'] = value


    def send_sub_to_main(self, input):
        """pen sub에서 pen main으로 시그널을 보내기 위한 함수 선언문이다. Core DB와 display에 값을 업데이트 하기 위해 사용
                Parameters
                1.	input(dict): Core DB, pen 업데이트를 위한 dictionary
        """
        self.pen_main_from_sub_signal.emit(input)

    def pen_eraser_to_core(self, input):
        """pen sub에서 core으로 시그널을 보내기 위한 함수 선언문이다. Core DB에 값을 업데이트 하기 위해 사용
                Parameters
                1.	input(dict): Core DB, pen 업데이트를 위한 dictionary
        """
        self.pen_eraser_to_core_signal.emit(input)

    def pen_eraser_to_display(self, input):
        """pen sub에서 Display에 시그널을 보내기 위한 함수 선언문이다. Display에 값을 업데이트 하기 위해 사용
                Parameters
                1.	input(dict): Core DB, pen 업데이트를 위한 dictionary
        """
        self.pen_eraser_to_display_signal.emit(input)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Pen_eraser_Form()
    # ui.setupUi(Form)
    # Form.show()
    sys.exit(app.exec_())
