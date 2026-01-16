from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import QSize, Qt, pyqtSlot
from labeling.stylesheet.stylesheet_pen_sub_style import stylesheet
from constants.constants import QT_MAX_SIZE

class Pen_style_Form(QtWidgets.QMainWindow):
    """Pen sub style ui, 펜 설정에 대한 모든 기능을 처리하기 위한 클래스
    """
    def __init__(self, Pen_Sync, lang):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.init(Sync=Pen_Sync, lang=lang)
        self.init_Ui_label_main_pen_style(self)
        self.setup_Ui_label_main_pen_style()
        self.init_Function()

        if __name__ == "__main__":
            self.show()
    
    def init(self, Sync=None, lang=None):
        """Pen sub 리스트 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스
                @History
                1. Modified by MyoungHwan (2025.06.16): Add pen sub sytle condition switch and update None(-1) label status


        """
        self.lang = lang
        self.Sync = Sync
        self.core_to_pen_style_signal = self.Sync.core_to_pen_style_signal
        self.core_to_pen_style_signal.connect(self.recv_from_core)
        self.pen_style_to_core_signal = self.Sync.pen_style_to_core_signal
        self.pen_style_to_display_signal = self.Sync.pen_style_to_display_signal

        self.pen_style_list = []
        # Modified by MyoungHwan (2025.06.16): Add pen sub sytle condition switch and update None(-1) label status
        self.pen_style_sw = True
        self.image_width = 150
        self.image_height = 60
        self.image = QImage(QSize(self.image_width, self.image_height), QImage.Format_RGB32)
        self.image.fill(QColor(83, 83, 83))
        
        self.label_obj_dict = self.Sync.label_obj_dict
        self.label_control_dict = self.Sync.label_control_dict
        self.label_order_list = [-1]

        self.pen_control_dict = self.Sync.pen_control_dict

    def init_Ui_label_main_pen_style(self, Mainwindow):
        """Pen sub 리스트 UI 생성을 위한 초기 선언문이다.
                Parmeters
                1.	Form(object): PyQt widget object

        """
        Mainwindow.setObjectName("pen_style_form")
        Mainwindow.resize(150, 200)
        Mainwindow.setStyleSheet(stylesheet)

        self.centralwidget = QtWidgets.QWidget(Mainwindow)
        self.centralwidget.setObjectName("centralwidget")

        self.pen_main_grid = QtWidgets.QGridLayout(self.centralwidget)
        self.pen_main_grid.setObjectName("pen_main_grid")

        self.pen_style_main_title_widget = QtWidgets.QWidget()
        self.pen_style_main_title_widget.setObjectName("pen_style_main_title_widget")

        self.pen_style_main_title_horizon = QtWidgets.QHBoxLayout(self.pen_style_main_title_widget)
        self.pen_style_main_title_horizon.setObjectName("pen_style_main_title_horizon")

        self.pen_style_main_title = QtWidgets.QLabel()
        self.pen_style_main_title.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_main_title.setObjectName("pen_style_main_title")
        self.lang.set("labeling", "pen_sub_style", "pen_style_main_title", self.pen_style_main_title)

        self.pen_style_picture_widget = QtWidgets.QWidget()
        self.pen_style_picture_widget.setObjectName("pen_style_picture_widget")

        self.pen_style_picture_vertical = QtWidgets.QVBoxLayout(self.pen_style_picture_widget)
        self.pen_style_picture_vertical.setObjectName("pen_style_picture_vertical")

        self.pen_style_picture = QtWidgets.QWidget()
        self.pen_style_picture.setObjectName("pen_style_picture")
        self.pen_style_picture_label = QtWidgets.QLabel(self.pen_style_picture)
        self.pen_style_picture_label.setText("")
        self.pen_style_picture_label.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_picture_label.setObjectName("label")
        
        self.pen_style_static_vertical = QtWidgets.QVBoxLayout() 
        self.pen_style_static_vertical.setObjectName("pen_style_static_vertical")

        self.pen_style_static_widget = QtWidgets.QWidget()
        self.pen_style_static_widget.setObjectName("pen_style_static_widget")
        
        self.pen_style_static_horizon = QtWidgets.QHBoxLayout(self.pen_style_static_widget)
        self.pen_style_static_horizon.setObjectName("pen_style_static_horizon")

        self.pen_style_static_size = QtWidgets.QLabel()
        self.pen_style_static_size.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_static_size.setObjectName("pen_style_static_size")
        self.lang.set("labeling", "pen_sub_style", "pen_style_static_size", self.pen_style_static_size)

        self.pen_style_static_edit = QtWidgets.QLineEdit()
        self.pen_style_static_edit.setAlignment(QtCore.Qt.AlignJustify|QtCore.Qt.AlignVCenter)
        self.pen_style_static_edit.setObjectName("pen_style_static_edit")
        self.pen_style_static_edit.setReadOnly(True)
        self.pen_style_static_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_static_edit.setText("1")

        self.pen_style_static_pix = QtWidgets.QLabel()
        self.pen_style_static_pix.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_static_pix.setObjectName("pen_style_static_pix")
        self.lang.set("labeling", "pen_sub_style", "pen_style_static_pix", self.pen_style_static_pix)

        self.pen_style_static_range_widget = QtWidgets.QWidget()
        self.pen_style_static_range_widget.setObjectName("pen_style_static_range_widget")

        self.pen_style_static_range_horizon = QtWidgets.QHBoxLayout(self.pen_style_static_range_widget)
        self.pen_style_static_range_horizon.setObjectName("pen_style_static_range_horizon")

        self.pen_style_static_range_slider = QtWidgets.QSlider()
        self.pen_style_static_range_slider.setOrientation(QtCore.Qt.Horizontal)
        self.pen_style_static_range_slider.setObjectName("pen_style_static_range_slider")
        self.pen_style_static_range_slider.setTickPosition(2)
        self.pen_style_static_range_slider.setPageStep(1)
        self.pen_style_static_range_slider.setRange(0, 4)

        self.pen_style_title_widget = QtWidgets.QWidget()
        self.pen_style_title_widget.setObjectName("pen_style_title_widget")

        self.pen_style_title_horizon = QtWidgets.QHBoxLayout(self.pen_style_title_widget)
        self.pen_style_title_horizon.setObjectName("pen_style_title_horizon")

        self.pen_style_title_type = QtWidgets.QLabel()
        self.pen_style_title_type.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_title_type.setObjectName("pen_style_title_type")
        self.lang.set("labeling", "pen_sub_style", "pen_style_title_type", self.pen_style_title_type)

        self.pen_style_widget = QtWidgets.QWidget()
        self.pen_style_widget.setObjectName("pen_style_widget")
        
        self.pen_style_horizon = QtWidgets.QHBoxLayout(self.pen_style_widget)
        self.pen_style_horizon.setObjectName("pen_style_horizon")

        self.pen_style_pen = QtWidgets.QPushButton()
        self.pen_style_pen.setText("")
        pen_style_pen_icon = QtGui.QIcon()
        pen_style_pen_icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_detail/pen_pen_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        pen_style_pen_icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_detail/pen_pen_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.pen_style_pen.setIcon(pen_style_pen_icon)
        self.pen_style_pen.setObjectName("pen_style_pen")
        self.pen_style_pen.setEnabled(False)
        # self.pen_style_pen.setCheckable(True)
        # self.pen_style_pen.setChecked(True)

        self.pen_style_lasso = QtWidgets.QPushButton()
        self.pen_style_lasso.setText("")
        pen_style_lasso_icon = QtGui.QIcon()
        pen_style_lasso_icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_detail/pen_lasso_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        pen_style_lasso_icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_detail/pen_lasso_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.pen_style_lasso.setIcon(pen_style_lasso_icon)
        self.pen_style_lasso.setObjectName("pen_style_lasso")
        self.pen_style_lasso.setCheckable(True)

        self.pen_style_paint = QtWidgets.QPushButton()
        self.pen_style_paint.setText("")
        pen_style_paint_icon = QtGui.QIcon()
        pen_style_paint_icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_detail/pen_paint_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        pen_style_paint_icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_detail/pen_paint_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.pen_style_paint.setIcon(pen_style_paint_icon)
        self.pen_style_paint.setObjectName("pen_style_paint")
        self.pen_style_paint.setCheckable(True)

        self.pen_style_2_widget = QtWidgets.QWidget()
        self.pen_style_2_widget.setObjectName("pen_style_2_widget")
        self.pen_style_horizon_2 = QtWidgets.QHBoxLayout(self.pen_style_2_widget)
        self.pen_style_horizon_2.setObjectName("pen_style_horizon_2")
        self.pen_style_label_pen = QtWidgets.QLabel()
        self.pen_style_label_pen.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_label_pen.setObjectName("pen_style_label_pen")
        self.lang.set("labeling", "pen_sub_style", "pen_style_label_pen", self.pen_style_label_pen)

        self.pen_style_label_lasso = QtWidgets.QLabel()
        self.pen_style_label_lasso.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_label_lasso.setObjectName("pen_style_label_lasso")
        self.pen_style_label_lasso.setText("올가미")
        self.pen_style_label_paint = QtWidgets.QLabel()
        self.pen_style_label_paint.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_label_paint.setObjectName("pen_style_label_paint")
        self.pen_style_label_paint.setText("페인트")
        self.pen_style_list = [self.pen_style_pen, self.pen_style_lasso, self.pen_style_paint]

        self.pen_style_main_sub_widget = QtWidgets.QWidget()
        self.pen_style_main_sub_widget.setObjectName("pen_style_main_sub_widget")
        self.pen_style_main_sub_horizon = QtWidgets.QHBoxLayout(self.pen_style_main_sub_widget)
        self.pen_style_main_sub_horizon.setObjectName("pen_style_main_sub_horizon")

        self.pen_style_main_drawing_vertical = QtWidgets.QVBoxLayout()
        self.pen_style_main_drawing_vertical.setObjectName("pen_style_main_drawing_vertical")
        self.pen_style_main_drawing_color_button = QtWidgets.QPushButton()
        self.pen_style_main_drawing_color_button.setText("")
        self.pen_style_main_drawing_color_button.setObjectName("label_list_color1")
        self.pen_style_main_drawing_color_button.setEnabled(False)
        self.pen_style_main_drawing_color_button.setStyleSheet(f"background-color: transparent;")
        self.pen_style_main_drawing_color_button_horizon = QtWidgets.QHBoxLayout()
        self.pen_style_main_drawing_color_button_horizon.addWidget(self.pen_style_main_drawing_color_button)
        self.pen_style_main_drawing_label = QtWidgets.QLabel()
        self.pen_style_main_drawing_label.setObjectName("pen_style_main_drawing_label")
        self.lang.set("labeling", "pen_sub_style", "pen_style_main_drawing_label", self.pen_style_main_drawing_label)

        self.pen_style_main_drawing_label.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_main_drawing_combobox = QtWidgets.QComboBox()
        self.pen_style_main_drawing_combobox.setObjectName("pen_style_main_drawing_combobox")

        self.pen_style_sub_drawing_vertical = QtWidgets.QVBoxLayout()
        self.pen_style_sub_drawing_vertical.setObjectName("pen_style_sub_drawing_vertical")
        self.pen_style_sub_drawing_color_button = QtWidgets.QPushButton()
        self.pen_style_sub_drawing_color_button.setText("")
        self.pen_style_sub_drawing_color_button.setObjectName("label_list_color2")
        self.pen_style_sub_drawing_color_button.setEnabled(False)
        self.pen_style_sub_drawing_color_button.setStyleSheet(f"background-color: transparent;")
        self.pen_style_sub_drawing_color_button_horizon = QtWidgets.QHBoxLayout()
        self.pen_style_sub_drawing_color_button_horizon.addWidget(self.pen_style_sub_drawing_color_button)
        self.pen_style_sub_drawing_label = QtWidgets.QLabel()
        self.pen_style_sub_drawing_label.setObjectName("pen_style_sub_drawing_label")    
        self.lang.set("labeling", "pen_sub_style", "pen_style_sub_drawing_label", self.pen_style_sub_drawing_label)

        self.pen_style_sub_drawing_label.setAlignment(QtCore.Qt.AlignCenter)
        self.pen_style_sub_drawing_combobox = QtWidgets.QComboBox()
        self.pen_style_sub_drawing_combobox.setObjectName("pen_style_sub_drawing_combobox")

        QtCore.QMetaObject.connectSlotsByName(Mainwindow)
        Mainwindow.setCentralWidget(self.centralwidget)


    def setup_Ui_label_main_pen_style(self):
        """초기화된 Pen sub ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
        """
        self.pen_style_static_edit.setMaximumSize(QtCore.QSize(40, QT_MAX_SIZE))
        self.pen_style_pen.setIconSize(QtCore.QSize(30, 30))
        self.pen_style_lasso.setIconSize(QtCore.QSize(30, 30))
        self.pen_style_paint.setIconSize(QtCore.QSize(30, 30))

        self.pen_style_main_title_horizon.addWidget(self.pen_style_main_title)
        self.pen_style_static_range_horizon.addWidget(self.pen_style_static_range_slider)
        self.pen_style_title_horizon.addWidget(self.pen_style_title_type)

        self.pen_main_grid.addWidget(self.pen_style_main_title_widget, 0, 0, 1, 1)
        # self.pen_main_grid.addWidget(self.pen_style_picture_widget, 1, 0, 1, 1)
        self.pen_main_grid.addLayout(self.pen_style_static_vertical, 2, 0, 1, 1)
        self.pen_main_grid.addWidget(self.pen_style_title_widget, 3, 0, 1, 1)
        self.pen_main_grid.addWidget(self.pen_style_widget, 4, 0, 1, 1)
        self.pen_main_grid.addWidget(self.pen_style_2_widget, 5, 0, 1, 1)

        self.pen_main_grid.setContentsMargins(5,5,5,5)
        self.pen_style_main_title_horizon.setContentsMargins(0,3,0,3)
        self.pen_style_static_horizon.setContentsMargins(9,0,9,0)
        self.pen_style_static_range_horizon.setContentsMargins(9,0,9,0)
        self.pen_style_title_horizon.setContentsMargins(0,3,0,3)
        self.pen_style_horizon.setContentsMargins(0,3,0,3)
        self.pen_style_horizon_2.setContentsMargins(0,3,0,3)

        self.pen_style_main_sub_horizon.setContentsMargins(6,0,6,0)
        self.pen_style_main_drawing_vertical.setContentsMargins(6,6,6,6)
        self.pen_style_sub_drawing_vertical.setContentsMargins(6,6,6,6)

        # self.pen_style_picture_vertical.addWidget(self.pen_style_picture_label)

        self.pen_style_static_horizon.addWidget(self.pen_style_static_size)
        self.pen_style_static_horizon.addWidget(self.pen_style_static_edit)
        self.pen_style_static_horizon.addWidget(self.pen_style_static_pix)
        self.pen_style_static_vertical.addWidget(self.pen_style_static_widget)
        self.pen_style_static_vertical.addWidget(self.pen_style_static_range_widget)
        self.pen_style_horizon.addWidget(self.pen_style_pen)
        # self.pen_style_horizon.addWidget(self.pen_style_lasso)
        # self.pen_style_horizon.addWidget(self.pen_style_paint)
        self.pen_style_horizon_2.addWidget(self.pen_style_label_pen)
        # self.pen_style_horizon_2.addWidget(self.pen_style_label_lasso)
        # self.pen_style_horizon_2.addWidget(self.pen_style_label_paint)

        # self.pen_style_main_drawing_label.setMinimumSize(QtCore.QSize(30, 30))
        # self.pen_style_main_drawing_label.setMaximumSize(QtCore.QSize(30, 30))
        self.pen_style_main_drawing_color_button.setMinimumSize(QtCore.QSize(30, 30))
        self.pen_style_main_drawing_color_button.setMaximumSize(QtCore.QSize(30, 30))
        # self.pen_style_main_drawing_combobox.setMinimumSize(QtCore.QSize(70, 20))
        # self.pen_style_main_drawing_combobox.setMaximumSize(QtCore.QSize(70, 20))

        # self.pen_style_sub_drawing_label.setMinimumSize(QtCore.QSize(30, 30))
        # self.pen_style_sub_drawing_label.setMaximumSize(QtCore.QSize(30, 30))
        self.pen_style_sub_drawing_color_button.setMinimumSize(QtCore.QSize(30, 30))
        self.pen_style_sub_drawing_color_button.setMaximumSize(QtCore.QSize(30, 30))
        # self.pen_style_sub_drawing_combobox.setMinimumSize(QtCore.QSize(70, 20))
        # self.pen_style_sub_drawing_combobox.setMaximumSize(QtCore.QSize(70, 20))
        
        
        self.pen_style_main_drawing_vertical.addLayout(self.pen_style_main_drawing_color_button_horizon)
        self.pen_style_main_drawing_vertical.addWidget(self.pen_style_main_drawing_label)
        self.pen_style_main_drawing_vertical.addWidget(self.pen_style_main_drawing_combobox)
        
        self.pen_style_sub_drawing_vertical.addLayout(self.pen_style_sub_drawing_color_button_horizon)
        self.pen_style_sub_drawing_vertical.addWidget(self.pen_style_sub_drawing_label)
        self.pen_style_sub_drawing_vertical.addWidget(self.pen_style_sub_drawing_combobox)
        
        self.pen_style_main_sub_horizon.addLayout(self.pen_style_main_drawing_vertical)
        self.pen_style_main_sub_horizon.addLayout(self.pen_style_sub_drawing_vertical)
        self.pen_style_main_sub_horizon.addStretch()

        self.pen_main_grid.addWidget(self.pen_style_main_sub_widget, 6, 0, 1, 1)

        # self.pix = QPixmap(self.image)
        # self.pen_style_picture_label.setPixmap(self.pix)    
        # self.painter = QtGui.QPainter(self.pix)
        # self.painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        # self.painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        # size = 4
        # self.painter.drawEllipse(self.image_width//2 - size//2, self.image_height//2 - size//2, size, size)
        # self.painter.end()
        # self.pen_style_picture_label.setPixmap(self.pix)

    def init_Function(self):
        """Pen sub Ui에 존재하는 기능들에 대한 connect 함수를 정의한다.
        """
        self.pen_style_pen.clicked.connect(lambda ch=self.pen_style_pen : self.pen_mode_change(ch=ch, mode=0, obj=self.pen_style_pen ))
        self.pen_style_lasso.clicked.connect(lambda ch=self.pen_style_lasso : self.pen_mode_change(ch=ch, mode=1, obj=self.pen_style_lasso))
        self.pen_style_paint.clicked.connect(lambda ch=self.pen_style_paint : self.pen_mode_change(ch=ch, mode=2, obj=self.pen_style_paint))
        self.pen_style_static_range_slider.valueChanged.connect(lambda value=self.pen_style_static_range_slider : self.slider_value_change(value=value))
        self.pen_style_main_drawing_combobox.currentIndexChanged.connect(lambda value=self.pen_style_main_drawing_combobox : self.select_label_combobox(mode=0, value=value))
        self.pen_style_sub_drawing_combobox.currentIndexChanged.connect(lambda value=self.pen_style_sub_drawing_combobox : self.select_label_combobox(mode=1, value=value))

    def pen_mode_change(self, ch=0, obj=None, mode=None):
        """펜 모드를 변경하기 위한 함수이다. 현재 사용하지 않으며 추후 업데이트할 예정
                Parameters
                1.  ch(int) : 미사용
                2.  obj(object) : 미사용
                3.  mode(int) : 미사용
        """
        for pen_obj in self.pen_style_list:
            if pen_obj != obj:
                if pen_obj.isChecked():
                    pen_obj.toggle()

        tmp_dict = {}
        tmp_dict['from'] = 'style'
        tmp_dict['type_detail'] = 'pen_detail'
        tmp_dict['type_detail_2'] = 'pen_type'
        tmp_dict['value'] = mode
        self.send_sub_to_main(tmp_dict)
    
    def slider_value_change(self, value=0):
        """펜 사이즈를 변경하기 위한 함수이다. core db에 업데이트하고 display에 업데이트 하기 위한 함수
                Parameters
                1.  value(int) : 펜 사이즈 
        """
        vis_value = 2 * value + 1
        cal_value = value + 1
        self.pen_style_static_edit.setText(str(vis_value))
        # self.pix = QPixmap(self.image)
        # self.pen_style_picture_label.setPixmap(self.pix)    
        # self.painter = QtGui.QPainter(self.pix)
        # self.painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))
        # self.painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        # size = cal_value * 4
        # self.painter.drawEllipse(self.image_width//2 - size//2, self.image_height//2 - size//2, size, size)
        # self.painter.end()
        # self.pen_style_picture_label.setPixmap(self.pix)

        self.pen_control_dict['pen_drawing_size'] = cal_value
        # tmp_dict = {}
        # tmp_dict['mode'] = 'modify'
        # tmp_dict['type'] = 'pen'
        # tmp_dict['from'] = 'style'
        # tmp_dict['type_detail'] = 'pen_detail'
        # tmp_dict['type_detail_2'] = 'pen_size'
        # tmp_dict['value'] = value
        # self.pen_style_to_core(tmp_dict)
        
        tmp_dict = {}
        tmp_dict['type'] = 'style'
        self.pen_style_to_display(tmp_dict)

        
        
    def clear_data_list(self):
        """호출한 데이터들의 리스트를 초기화하기 위한 함수.
        """
        self.label_order_list = [-1]
        self.pen_style_main_drawing_combobox.clear()
        self.pen_style_sub_drawing_combobox.clear()

    def sort_and_additem(self):
        self.label_order_list = [-1] + sorted(list(self.label_obj_dict.keys()))
        for label_num in self.label_order_list:
            if label_num == -1:
                self.pen_style_main_drawing_combobox.addItem(self.lang.get("labeling", "pen_sub_style", "pen_style_not_used_label"))
                self.pen_style_sub_drawing_combobox.addItem(self.lang.get("labeling", "pen_sub_style", "pen_style_not_used_label"))
            else:
                self.pen_style_main_drawing_combobox.addItem(f"{self.lang.get('labeling', 'pen_sub_style', 'pen_style_used_label')}: {str(label_num)}")
                self.pen_style_sub_drawing_combobox.addItem(f"{self.lang.get('labeling', 'pen_sub_style', 'pen_style_used_label')}: {str(label_num)}")
                
    def select_label_combobox(self, mode=None, value=None):
        """
            @Description: 라벨 선택시 콤보박스 업데이트 해주는 기능
            @Author: MyoungHwan
            @History
                1. Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                2. Modified by MyoungHwan (2025.06.13): Fixed an issue when selecting "Not Used" in the Label ComboBox
                3. Modified by MyoungHwan (2025.06.16): Add pen sub sytle condition switch
                
        """
        # Modified by MyoungHwan (2025.06.16): Add pen sub sytle condition switch and update None(-1) label status
        if self.pen_style_sw:
            select_idx = value
            if select_idx > -1 :
                select_label_number = self.label_order_list[select_idx]
                if mode == 0: # main label mode, left mouse button
                    # Modified by MyoungHwan (2025.06.13): Fixed an issue when selecting "Not Used" in the Label ComboBox
                    current_label_number = self.label_control_dict['select_main_label_number']
                    if select_label_number != -1:
                        #main
                        self.label_control_dict['select_main_label_number'] = select_label_number
                        select_color = self.label_obj_dict[self.label_control_dict['select_main_label_number']]['color']
                        self.pen_style_main_drawing_color_button.setStyleSheet(f"background-color: rgb({select_color[0]}, {select_color[1]}, {select_color[2]});")
                        #update DB
                        # Improvemented by MyoungHwan (2024.12.13): label_obj_dict key 구조 수정
                        if self.label_obj_dict[select_label_number]['obj_dict']['select'].isChecked() == False:
                            self.label_obj_dict[select_label_number]['obj_dict']['select'].toggle()
                    else:
                        # Modified by MyoungHwan (2025.06.13): Fixed an issue when selecting "Not Used" in the Label ComboBox
                        # Pass code when label list initialized, select_label_number = -1 and current_label_number = -1
                        if current_label_number != -1:
                            if self.label_obj_dict[current_label_number]['obj_dict']['select'].isChecked():
                                self.label_obj_dict[current_label_number]['obj_dict']['select'].toggle()
                        self.pen_style_main_drawing_color_button.setStyleSheet(f"background-color: transparent;")

                elif mode == 1: # sub label mode, right mouse button
                    # Modified by MyoungHwan (2025.06.13): Fixed an issue when selecting "Not Used" in the Label ComboBox
                    self.label_control_dict['select_sub_label_number'] = select_label_number
                    if select_label_number != -1:
                        select_color = self.label_obj_dict[self.label_control_dict['select_sub_label_number']]['color']
                        self.pen_style_sub_drawing_color_button.setStyleSheet(f"background-color: rgb({select_color[0]}, {select_color[1]}, {select_color[2]});")
                    else:
                        self.pen_style_sub_drawing_color_button.setStyleSheet(f"background-color: transparent;")

    @pyqtSlot(dict)
    def recv_from_core(self, output):
        # Modified by MyoungHwan (2025.06.16): Add pen sub sytle condition switch and update None(-1) label status
        self.pen_style_sw = False
        mode = output['mode']
        if mode == "reset":
            self.clear_data_list()
            self.sort_and_additem()
            if len(self.label_order_list) > 1: # label이 있을경우
                if self.label_control_dict['select_main_label_number'] != -1:
                    cur_idx_main = self.label_order_list.index(self.label_control_dict['select_main_label_number'])
                    self.pen_style_main_drawing_combobox.setCurrentIndex(cur_idx_main)
                    cur_idx_main_color = self.label_obj_dict[self.label_control_dict['select_main_label_number']]['color']
                    self.pen_style_main_drawing_color_button.setStyleSheet(f"background-color: rgb({cur_idx_main_color[0]}, {cur_idx_main_color[1]}, {cur_idx_main_color[2]});")
                else:
                    self.pen_style_main_drawing_color_button.setStyleSheet(f"background-color: transparent;")
                    self.pen_style_main_drawing_combobox.setCurrentIndex(0)

                if self.label_control_dict['select_sub_label_number'] != -1:
                    cur_idx_sub = self.label_order_list.index(self.label_control_dict['select_sub_label_number'])
                    self.pen_style_sub_drawing_combobox.setCurrentIndex(cur_idx_sub)
                    cur_idx_sub_color = self.label_obj_dict[self.label_control_dict['select_sub_label_number']]['color']
                    self.pen_style_sub_drawing_color_button.setStyleSheet(f"background-color: rgb({cur_idx_sub_color[0]}, {cur_idx_sub_color[1]}, {cur_idx_sub_color[2]});")
                else:
                    self.pen_style_sub_drawing_color_button.setStyleSheet(f"background-color: transparent;")
                    self.pen_style_sub_drawing_combobox.setCurrentIndex(0)

        elif mode == 'select':
            type_ = output['type']
            if type_ == 'main':
                if self.label_control_dict['select_main_label_number'] != -1 :
                    select_label_color = self.label_obj_dict[self.label_control_dict['select_main_label_number']]['color']
                    self.pen_style_main_drawing_color_button.setStyleSheet(f"background-color: rgb({select_label_color[0]}, {select_label_color[1]}, {select_label_color[2]});")
                    self.pen_style_main_drawing_combobox.setCurrentIndex(self.label_order_list.index(self.label_control_dict['select_main_label_number']))
                else:
                    self.pen_style_main_drawing_color_button.setStyleSheet(f"background-color: transparent;")
                    self.pen_style_main_drawing_combobox.setCurrentIndex(0)
            elif type_ == 'sub':
                pass
        self.pen_style_sw = True


    def send_sub_to_main(self, input):
        """pen sub에서 pen main으로 시그널을 보내기 위한 함수 선언문이다. Core DB와 display에 값을 업데이트 하기 위해 사용
                Parameters
                1.	input(dict): Core DB, pen 업데이트를 위한 dictionary
        """
        self.pen_main_from_sub_signal.emit(input)

    def pen_style_to_core(self, input):
        """pen style에서 core로 시그널을 보내기 위한 함수 선언문이다. Core DB에 값을 업데이트 하기 위해 사용
                Parameters
                1.	input(dict): Core DB, pen 업데이트를 위한 dictionary
        """
        self.pen_style_to_core_signal.emit(input)

    def pen_style_to_display(self, input):
        """pen style에서 display로 시그널을 보내기 위한 함수 선언문이다. Display에 값을 업데이트 하기 위해 사용
                Parameters
                1.	input(dict): Core DB, pen 업데이트를 위한 dictionary
        """
        self.pen_style_to_display_signal.emit(input)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Mainwindow = QtWidgets.QWidget()
    ui = Pen_style_Form()
    # ui.setupUi(Mainwindow)
    # Mainwindow.show()
    sys.exit(app.exec_())
