from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPoint, pyqtSlot
from PyQt5.QtGui import QCursor
from constants.constants import *
from utils.viewer import Display_viewer
from utils.custom_ui import messageBox

if __name__ == "__main__" :
    from pen_sub_style import Pen_style_Form
    from pen_sub_erase import Pen_eraser_Form
    from pen_sub_minimap import Pen_minimap_Form
    from display_sub_rgb_change import Display_rgb_change_Form
    from pen_sub_adv_opacity_option import pen_sub_adv_opacity_option_Form
    from pen_sub_semi_auto_labeling import PenSemiAutoLabelingForm
    from .pen_sub_rectangle import penRectangleSALForm, penRectangleSubMenu

else:
    from .pen_sub_minimap import Pen_minimap_Form
    from .pen_sub_style import Pen_style_Form
    from .pen_sub_erase import Pen_eraser_Form
    from .display_sub_rgb_change import Display_rgb_change_Form
    from .pen_sub_adv_opacity_option import pen_sub_adv_opacity_option_Form
    from .pen_sub_semi_auto_labeling import PenSemiAutoLabelingForm
    from .pen_sub_rectangle import penRectangleSALForm, penRectangleSubMenu



class Pen_Form(QtWidgets.QWidget):
    """Pen과 관련된 모든 기능을 처리하기 위한 클래스
    """
    def __init__(self, Sync, lang) -> None:
        super().__init__()       
        self.init(Sync=Sync, lang=lang)
        self.init_Ui_label_main_pen(self)
        self.init_Function()
        self.init_sub_fucntion()
        self.setup_Ui_label_main_pen()
        self.setMouseTracking(True)

        if __name__ == "__main__":
            self.show()

    def init(self, Sync=None, lang=None):
        """Pen 리스트 초기 선언 시 변수 선언문이다. 각종 변수들이 이곳에서 선언된다.
                Parameters
                1.   Sync(Qobject): PyQt slot/signal을 사용하기 위해 정의한 클래스

        """
        self.lang = lang
        self.Sync = Sync
        self.pen_obj_dict = self.Sync.pen_obj_dict
        self.pen_to_core_signal = self.Sync.pen_to_core_signal
        self.pen_to_display_signal = self.Sync.pen_to_display_signal
        self.core_to_pen_signal = self.Sync.core_to_pen_signal
        self.core_to_pen_signal.connect(self.recv_from_core)
        self.pen_opacity_to_display_signal = self.Sync.pen_opacity_to_display_signal
        self.penToDisplayMenuSignal = self.Sync.penToDisplayMenuSignal
        self.label_obj_dict = self.Sync.label_obj_dict
        self.label_control_dict = self.Sync.label_control_dict
        self.pen_control_dict = self.Sync.pen_control_dict
        self.sub_widget_dict = self.Sync.sub_widget_dict
        self.hflipCount = False
        self.vflipCount = False
        self.display_viewer = Display_viewer()

    def init_sub_fucntion(self):
        """Pen sub style/eraser 리스트 UI 생성을 위한 초기 선언문이다.

        """
        self.pen_eraser_form = Pen_eraser_Form(Pen_Sync=self.Sync, lang=self.lang)
        self.pen_style_form = Pen_style_Form(Pen_Sync=self.Sync, lang=self.lang)
        self.pen_minimap_form = Pen_minimap_Form(Pen_Sync=self.Sync)
        self.display_rgb_change_form = Display_rgb_change_Form(Sync=self.Sync, lang=self.lang)
        self.pen_opacity_form = pen_sub_adv_opacity_option_Form(Sync=self.Sync, lang=self.lang, parent=self)
        self.pen_semi_auto_labeling_form = PenSemiAutoLabelingForm(Pen_Sync=self.Sync, lang=self.lang, parent=self)
        self.penRectangleSALForm = penRectangleSALForm(sync=self.Sync, lang=self.lang)
        self.penRectangleSubMenu = penRectangleSubMenu(sync=self.Sync, lang=self.lang, parent=self)
        self.sub_widget_dict['pen_style_form'] = self.pen_style_form
        self.sub_widget_dict['pen_eraser_form'] = self.pen_eraser_form
        self.sub_widget_dict['pen_minimap_form'] = self.pen_minimap_form
        self.sub_widget_dict['display_rgb_change_form'] = self.display_rgb_change_form
        self.sub_widget_dict['penSemiAutoLabelingForm'] = self.pen_semi_auto_labeling_form
        self.sub_widget_dict['penRectangleSALForm'] = self.penRectangleSALForm
        self.sub_widget_dict['penRectangleSubMenu'] = self.penRectangleSubMenu

    def init_Ui_label_main_pen(self, Form):
        """Pen main 리스트 UI 생성을 위한 초기 선언문이다.
                Parmeters
                1.	Form(object): PyQt widget object
                History:
                    Yugyeong Hong(2026.02.04) - Add push button for Semi Auto Labeling

        """
        Form.setObjectName("Pen_Form")
        Form.setMaximumSize(QtCore.QSize(QT_MAX_SIZE, QT_MAX_SIZE))

        self.pen_list_main_grid = QtWidgets.QGridLayout(Form)
        self.pen_list_main_grid.setObjectName("pen_list_main_grid")
        self.pen_widget = QtWidgets.QWidget()
        self.pen_widget.setObjectName("pen_widget")

        self.pen_list_vertical = QtWidgets.QVBoxLayout(self.pen_widget)
        self.pen_list_vertical.setObjectName("pen_list_vertical")

        self.pen_scale_up = QtWidgets.QPushButton()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_scale_up_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_scale_up_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_scale_up_disabled.png"),  QtGui.QIcon.Disabled)
        self.pen_scale_up.setIcon(icon)
        self.pen_scale_up.setObjectName("pen_scale_up")
        self.lang.set("labeling", "pen_main", "pen_scale_up", self.pen_scale_up)

        self.pen_scale_down = QtWidgets.QPushButton()
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_scale_down_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_scale_down_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon1.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_scale_down_disabled.png"),  QtGui.QIcon.Disabled)
        self.pen_scale_down.setIcon(icon1)
        self.pen_scale_down.setObjectName("pen_scale_down")
        self.lang.set("labeling", "pen_main", "pen_scale_down", self.pen_scale_down)

        self.pen_part_scale_up = QtWidgets.QPushButton()
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_part_scale_up_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_part_scale_up_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon2.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_part_scale_up_disabled.png"),  QtGui.QIcon.Disabled)
        self.pen_part_scale_up.setIcon(icon2)
        self.pen_part_scale_up.setCheckable(True)
        self.pen_part_scale_up.setObjectName("pen_part_scale_up")
        self.lang.set("labeling", "pen_main", "pen_part_scale_up", self.pen_part_scale_up)

        self.pen_rot90 = QtWidgets.QPushButton()
        icon_rot90 = QtGui.QIcon()
        icon_rot90.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_rot90_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_rot90.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_rot90_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon_rot90.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_rot90_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_rot90.setIcon(icon_rot90)
        self.pen_rot90.setObjectName("pen_rot90")
        self.pen_rot90.setShortcut("Alt+R")
        self.lang.set("labeling", "pen_main", "pen_rot90", self.pen_rot90)

        self.pen_hflip = QtWidgets.QPushButton()
        icon_hflip = QtGui.QIcon()
        icon_hflip.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_hflip_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_hflip.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_hflip_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon_hflip.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_hflip_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_hflip.setIcon(icon_hflip)
        self.pen_hflip.setObjectName("pen_hflip")
        self.pen_hflip.setShortcut("H")
        self.lang.set("labeling", "pen_main", "pen_hflip", self.pen_hflip)

        self.pen_vflip = QtWidgets.QPushButton()
        icon_vflip = QtGui.QIcon()
        icon_vflip.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_vflip_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_vflip.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_vflip_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon_vflip.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_vflip_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_vflip.setIcon(icon_vflip)
        self.pen_vflip.setObjectName("pen_vflip")
        self.pen_vflip.setShortcut("V")
        self.lang.set("labeling", "pen_main", "pen_vflip", self.pen_vflip)

        self.pen_draw_type = QtWidgets.QPushButton()
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_draw_type_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_draw_type_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon3.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_draw_type_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_draw_type.setIcon(icon3)
        self.pen_draw_type.setCheckable(True)
        self.pen_draw_type.setObjectName("pen_draw_type")
        self.pen_draw_type.setShortcut("P")
        self.lang.set("labeling", "pen_main", "pen_draw_type", self.pen_draw_type)

        self.pen_part_move = QtWidgets.QPushButton()
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_part_move_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon4.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_part_move_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon4.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_part_move_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_part_move.setIcon(icon4)
        self.pen_part_move.setCheckable(True)
        self.pen_part_move.setObjectName("pen_part_move")
        self.lang.set("labeling", "pen_main", "pen_part_move", self.pen_part_move)

        self.pen_eraser = QtWidgets.QPushButton()
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_eraser_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon5.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_eraser_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon5.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_eraser_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_eraser.setIcon(icon5)
        self.pen_eraser.setCheckable(True)
        self.pen_eraser.setObjectName("pen_eraser")
        self.pen_eraser.setShortcut("E")
        self.lang.set("labeling", "pen_main", "pen_eraser", self.pen_eraser)

        self.pen_bright = QtWidgets.QPushButton()
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_bright_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon6.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_bright_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon6.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_bright_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_bright.setIcon(icon6)
        self.pen_bright.setCheckable(True)
        self.pen_bright.setObjectName("pen_bright")
        self.lang.set("labeling", "pen_main", "pen_bright", self.pen_bright)

        self.pen_undo = QtWidgets.QPushButton()
        self.pen_undo.setEnabled(False)
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_undo_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon7.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_undo_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon7.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_undo_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_undo.setIcon(icon7)
        self.pen_undo.setObjectName("pen_undo")
        self.pen_undo.setShortcut("Ctrl+Z")
        self.lang.set("labeling", "pen_main", "pen_undo", self.pen_undo)

        self.pen_redo = QtWidgets.QPushButton()
        self.pen_redo.setEnabled(False)
        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_redo_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon8.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_redo_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon8.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_redo_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_redo.setIcon(icon8)
        self.pen_redo.setObjectName("pen_redo")
        self.pen_redo.setShortcut("Ctrl+Y")
        self.lang.set("labeling", "pen_main", "pen_redo", self.pen_redo)

        self.pen_painting = QtWidgets.QPushButton()
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_paint_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon9.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_paint_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon9.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_paint_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_painting.setIcon(icon9)
        self.pen_painting.setCheckable(True)
        self.pen_painting.setObjectName("pen_painting")
        self.pen_painting.setShortcut("Alt+P")
        self.lang.set("labeling", "pen_main", "pen_painting", self.pen_painting)

        self.pen_rectangle = QtWidgets.QPushButton()
        icon_rectangle = QtGui.QIcon()
        icon_rectangle.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_rectangle_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_rectangle.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_rectangle_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon_rectangle.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_rectangle_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_rectangle.setIcon(icon_rectangle)
        self.pen_rectangle.setCheckable(True)
        self.pen_rectangle.setObjectName("pen_rectangle")
        self.pen_rectangle.setShortcut("R")
        self.lang.set("labeling", "pen_main", "pen_rectangle", self.pen_rectangle)

        self.pen_polygon = QtWidgets.QPushButton()
        icon_polygon = QtGui.QIcon()
        icon_polygon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_polygon_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_polygon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_polygon_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon_polygon.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_polygon_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_polygon.setIcon(icon_polygon)
        self.pen_polygon.setCheckable(True)
        self.pen_polygon.setObjectName("pen_polygon")
        self.lang.set("labeling", "pen_main", "pen_polygon", self.pen_polygon)

        self.pen_opacity = QtWidgets.QPushButton()
        icon_opacity = QtGui.QIcon()
        icon_opacity.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_opacity_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_opacity.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_opacity_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon_opacity.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_opacity_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_opacity.setIcon(icon_opacity)
        self.pen_opacity.setCheckable(True)
        self.pen_opacity.setObjectName("pen_opacity")
        self.lang.set("labeling", "pen_main", "pen_opacity", self.pen_opacity)

        self.pen_minimap = QtWidgets.QPushButton()
        self.pen_minimap.setText("")
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_minimap_hide.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon10.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_minimap_show.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon10.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_minimap_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_minimap.setIcon(icon10)
        self.pen_minimap.setCheckable(True)
        self.pen_minimap.setObjectName("pen_minimap")
        self.pen_minimap.setToolTip("미니맵")

        self.pen_image = QtWidgets.QPushButton()
        icon_image = QtGui.QIcon()
        icon_image.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_image_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon_image.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_image_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon_image.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_image_disabled.png"), QtGui.QIcon.Disabled)
        self.pen_image.setIcon(icon_image)
        self.pen_image.setCheckable(True)
        self.pen_image.setObjectName("pen_image")
        self.lang.set("labeling", "pen_main", "penImage", self.pen_image)

        self.penAdvancedLabeling = QtWidgets.QPushButton()
        iconPixel = QtGui.QIcon()
        iconPixel.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_advanced_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        iconPixel.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_advanced_yellow.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        iconPixel.addPixmap(QtGui.QPixmap("ico/labeling/penbox/pen_advanced_disabled.png"), QtGui.QIcon.Disabled)
        self.penAdvancedLabeling.setIcon(iconPixel)
        self.penAdvancedLabeling.setCheckable(True)
        self.penAdvancedLabeling.setObjectName("penAdvancedLabeling")
        self.lang.set("labeling", "pen_main", "penAdvancedLabeling", self.penAdvancedLabeling)


        self.blank_widget = QtWidgets.QWidget()
        self.blank_widget.setObjectName("blank_widget")
        
        QtCore.QMetaObject.connectSlotsByName(Form)
    
    def setup_Ui_label_main_pen(self):
        """초기화된 Pen main ui의 디자인을 정의한다. Widget의 크기, layout 마진정의 및 정렬을 해당함수에서 정의한다.
            또한 Pen object들을 dictionaray에 선언한다.
        """
        self.pen_scale_up.setIconSize(QtCore.QSize(20, 20))
        self.pen_scale_down.setIconSize(QtCore.QSize(20, 20))
        self.pen_part_scale_up.setIconSize(QtCore.QSize(20, 20))
        self.pen_rot90.setIconSize(QtCore.QSize(21, 21))
        self.pen_hflip.setIconSize(QtCore.QSize(21, 21))
        self.pen_vflip.setIconSize(QtCore.QSize(21, 21))
        self.pen_draw_type.setIconSize(QtCore.QSize(20, 20))
        self.pen_part_move.setIconSize(QtCore.QSize(20, 20))
        self.pen_eraser.setIconSize(QtCore.QSize(20, 20))
        self.pen_bright.setIconSize(QtCore.QSize(20, 20))
        self.pen_undo.setIconSize(QtCore.QSize(20, 20))
        self.pen_redo.setIconSize(QtCore.QSize(int(21.5), int(21.5)))
        self.pen_painting.setIconSize(QtCore.QSize(20, 20))
        self.pen_rectangle.setIconSize(QtCore.QSize(20, 20))
        self.pen_polygon.setIconSize(QtCore.QSize(20, 20))
        self.pen_opacity.setIconSize(QtCore.QSize(20, 20))
        self.pen_image.setIconSize(QtCore.QSize(20, 20))
        self.penAdvancedLabeling.setIconSize(QtCore.QSize(20, 20))
        self.pen_list_vertical.addStretch()
        self.pen_list_vertical.addWidget(self.pen_scale_up)
        self.pen_list_vertical.addWidget(self.pen_scale_down)
        # self.pen_list_vertical.addWidget(self.pen_part_scale_up)
        self.pen_list_vertical.addWidget(self.pen_draw_type)
        self.pen_list_vertical.addWidget(self.penAdvancedLabeling)
        self.pen_list_vertical.addWidget(self.pen_painting)
        self.pen_list_vertical.addWidget(self.pen_rectangle)
        self.pen_list_vertical.addWidget(self.pen_polygon)
        # self.pen_list_vertical.addWidget(self.pen_part_move)
        self.pen_list_vertical.addWidget(self.pen_eraser)
        self.pen_list_vertical.addWidget(self.pen_rot90)
        self.pen_list_vertical.addWidget(self.pen_hflip)
        self.pen_list_vertical.addWidget(self.pen_vflip)
        self.pen_list_vertical.addWidget(self.pen_bright)
        self.pen_list_vertical.addWidget(self.pen_opacity)
        self.pen_list_vertical.addWidget(self.pen_image)
        self.pen_list_vertical.addWidget(self.pen_undo)
        self.pen_list_vertical.addWidget(self.pen_redo)
        # self.pen_list_vertical.addWidget(self.pen_minimap)
        self.pen_list_vertical.addStretch()
        self.pen_list_main_grid.setContentsMargins(0, 0, 0, 0)
        self.pen_list_main_grid.addWidget(self.pen_widget, 0, 0, 1, 1)

        self.pen_obj_dict['pen_scale_up'] = {
            'obj':self.pen_scale_up
        }
        self.pen_obj_dict['pen_scale_down'] = {
            'obj':self.pen_scale_down
        }
        self.pen_obj_dict['pen_part_scale_up'] = {
            'obj':self.pen_part_scale_up
        }
        self.pen_obj_dict['pen_draw_type'] = {
            'obj':self.pen_draw_type,
            'opened':False,
            'sub_form':self.pen_style_form
        }
        self.pen_obj_dict['pen_part_move'] = {
            'obj':self.pen_part_move,
        }
        self.pen_obj_dict['pen_eraser'] = {
            'obj':self.pen_eraser,
            'opened':False,
            'sub_form' : self.pen_eraser_form
        }
        self.pen_obj_dict['pen_bright'] = {
            'obj':self.pen_bright,
            'opened':False,
            'sub_form' : self.display_rgb_change_form
        }
        self.pen_obj_dict['pen_undo'] = {
            'obj':self.pen_undo
        }
        self.pen_obj_dict['pen_redo'] = {
            'obj':self.pen_redo
        }
        self.pen_obj_dict['pen_painting'] = {
            'obj':self.pen_painting
        }
        self.pen_obj_dict['pen_minimap'] = {
            'obj' : self.pen_minimap,
            'form' :self.pen_minimap_form,
            'label' : self.pen_minimap_form.pen_minimap_picture_label
        }
        self.pen_obj_dict['pen_rot90'] = {
            'obj':self.pen_rot90
        }
        self.pen_obj_dict['pen_hflip'] = {
            'obj':self.pen_hflip
        }
        self.pen_obj_dict['pen_vflip'] = {
            'obj':self.pen_vflip
        }
        self.pen_obj_dict['pen_rectangle'] = {
            'obj':self.pen_rectangle,
            'menu_opened': False,
            'opened':False,
            'sub_menu' : self.penRectangleSubMenu,
            'sub_form' : self.penRectangleSALForm,
            'sub_mode' : None,
            'settings' : None
        }
        self.pen_obj_dict['pen_polygon'] = {
            'obj':self.pen_polygon,
        }
        self.pen_obj_dict['pen_opacity'] = {
            'obj':self.pen_opacity,
            'opened':False,
            'sub_form' : self.pen_opacity_form
        } 
        self.pen_obj_dict['pen_image'] = {
            'obj':self.pen_image,
        }
        self.pen_obj_dict['penAdvancedLabeling'] = {
            'obj':self.penAdvancedLabeling,
            'opened':False,
            'pixelBased': False,
            'semiAuto': False,
            'onMode': None, # A variable that stores the previous mode. It is needed to return to the previous mode when entering advanced labeling while using a different pen_mode.
            'semiAutoForm' : self.pen_semi_auto_labeling_form
        }
        """
            @Description: label opacity 기능 사용시 기존 pen object 비활성화 되는 문제 수정
            @author: Hyunsu
            @history
                1. Modified by Hyunsu(2025.03.19): Add object to maintain the non-closable pen objects

        """
        self.non_closable_pen_objs = ['pen_bright', 'pen_undo', 'pen_redo', 'pen_rot90', 'pen_hflip', 'pen_vflip', 'pen_opacity', 'pen_image']

    
    def init_Function(self):
        """Pen main Ui에 존재하는 기능들에 대한 connect 함수를 정의한다.
        """
        self.pen_scale_up.clicked.connect(lambda : self.pen_mode(mode=PEN_MODE_ZOOM_IN))
        self.pen_scale_down.clicked.connect(lambda : self.pen_mode(mode=PEN_MODE_ZOOM_OUT))
        self.pen_part_scale_up.clicked.connect(lambda ch=self.pen_part_scale_up : self.pen_mode(ch = ch, mode=PEN_MODE_PARTIAL_ZOOM))
        self.pen_draw_type.clicked.connect(lambda ch=self.pen_draw_type: self.pen_mode(ch = ch, mode=PEN_MODE_DRAWING))
        self.pen_rot90.clicked.connect(lambda ch=self.pen_rot90: self.pen_mode(ch = ch, mode=PEN_MODE_ROT90))
        self.pen_hflip.clicked.connect(lambda ch=self.pen_hflip: self.pen_mode(ch = ch, mode=PEN_MODE_HFLIP))
        self.pen_vflip.clicked.connect(lambda ch=self.pen_vflip: self.pen_mode(ch = ch, mode=PEN_MODE_VFLIP))
        self.pen_part_move.clicked.connect(lambda ch=self.pen_part_move: self.pen_mode(ch = ch, mode=PEN_MODE_IMAGE_MOVING))
        self.pen_eraser.clicked.connect(lambda ch=self.pen_eraser: self.pen_mode(ch = ch, mode=PEN_MODE_ERASER))
        self.pen_bright.clicked.connect(lambda ch=self.pen_bright: self.pen_mode(ch = ch, mode=PEN_MODE_BRIGHT))
        self.pen_undo.clicked.connect(lambda : self.pen_mode(mode=PEN_MODE_UNDO))
        self.pen_redo.clicked.connect(lambda : self.pen_mode(mode=PEN_MODE_REDO))
        self.pen_painting.clicked.connect(lambda ch=self.pen_painting: self.pen_mode(ch = ch, mode=PEN_MODE_PAINTING))
        self.pen_minimap.clicked.connect(lambda ch=self.pen_minimap: self.pen_mode(ch = ch, mode=PEN_MODE_MINIMAP))
        self.pen_rectangle.clicked.connect(lambda ch=self.pen_rectangle: self.pen_mode(ch = ch, mode=PEN_MODE_RECTANGLE))
        self.pen_polygon.clicked.connect(lambda ch=self.pen_polygon: self.pen_mode(ch = ch, mode=PEN_MODE_POLYGON))
        self.pen_opacity.clicked.connect(lambda ch=self.pen_opacity: self.pen_mode(ch = ch, mode=PEN_MODE_OPACITY))
        self.pen_image.clicked.connect(lambda ch=self.pen_image: self.pen_mode(ch=ch, mode=PEN_MODE_IMAGE))
        self.penAdvancedLabeling.clicked.connect(lambda ch=self.penAdvancedLabeling: self.pen_mode(ch=ch, mode=PEN_MODE_ADVANCED_LABELING))
        self.penAdvancedLabeling.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.penAdvancedLabeling.customContextMenuRequested.connect(self.onAdvancedLabelingRightClick)
        self.pen_draw_type.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.pen_draw_type.customContextMenuRequested.connect(lambda : self.pen_sub_open(mode=0))
        self.pen_rectangle.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.pen_rectangle.customContextMenuRequested.connect(lambda : self.pen_sub_open(mode=PEN_SUB_MODE_RECTANGLE))
        self.pen_eraser.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.pen_eraser.customContextMenuRequested.connect(lambda : self.pen_sub_open(mode=1))

        modeItems = [self.lang.get("labeling", "penSubAdvancedLabeling", "pixelBasedLabeling"),
                     self.lang.get("labeling", "penSubAdvancedLabeling", "semiAutoLabeling")]
        self.advancedLabelingMenu = QtWidgets.QMenu(self)
        self.actionPixelBased = QtWidgets.QAction(modeItems[0], self.advancedLabelingMenu)
        self.actionSemiAuto = QtWidgets.QAction(modeItems[1], self.advancedLabelingMenu)
        self.actionPixelBased.setCheckable(True)
        self.actionSemiAuto.setCheckable(True)
        self.advancedLabelingMenu.addAction(self.actionPixelBased)
        self.advancedLabelingMenu.addAction(self.actionSemiAuto)
        self.advancedLabelingActionGroup = QtWidgets.QActionGroup(self.advancedLabelingMenu)
        self.advancedLabelingActionGroup.setExclusive(True)
        self.advancedLabelingActionGroup.addAction(self.actionPixelBased)
        self.advancedLabelingActionGroup.addAction(self.actionSemiAuto)

    def close_pen_object(self, obj:str, fromSubFormOpen=True) -> None:
        """펜 객체의 서브 폼을 닫고 상태를 업데이트합니다."""
        if 'sub_form' in self.pen_obj_dict[obj]:
            if self.pen_obj_dict[obj]['opened']:
                self.pen_obj_dict[obj]['opened'] = False
                if obj == 'penAdvancedLabeling':
                    self.pen_obj_dict[obj]['semiAutoForm'].close()
                else:
                    self.pen_obj_dict[obj]['sub_form'].close()
        
        if 'sub_menu' in self.pen_obj_dict[obj]:
            if self.pen_obj_dict[obj]['menu_opened']:
                self.pen_obj_dict[obj]['menu_opened'] = False
                self.pen_obj_dict[obj]['sub_menu'].close()

        if not fromSubFormOpen:
            if obj == 'pen_image':
                pass
            else:
                self.pen_obj_dict[obj]['obj'].setChecked(False)

    def pen_mode(self, ch:bool=None, mode:int=0) -> None:
        """그리기 도구 모음 선택 시 동작하는 함수이다. 버튼 클릭시 Core_DB 업데이트 및 display에 값을 전달한다.
                Parameters
                1.  ch(bool)
                    - True : 선택 기능 활성화
                    - False : 선택 기능 비활성화
                2.  mode(int)
                    - 0 : 이미지 확대 모드
                    - 1 : 이미지 축소 모드
                    - 2 : 이미지 부분 확대 모드
                    - 3 : 라벨링 모드, 오른쪽 클릭시 pen sub style ui 활성화 및 펜 크기 설정 가능
                    - 4 : 이미지 이동 모드
                    - 5 : 지우개 모드, 오른쪽 클릭시 pen sub eraser ui 활성화 및 지우개 크기 설정 가능
                    - 6 : RGB 값 변경 모드
                    - 7 : 실행취소
                    - 8 : 실행취소 복구
                    - 9 : painting 모드
                    - 10 : minimap 모드(사용 안 함)
                    - 11 : 90도 회전 모드
                    - 12 : 좌우 반전 모드
                    - 13 : 상하 반전 모드
                    - 14 : Rectangle Mode, right click to open rectangle sub menu and sub form
                    - 15 : 다각형 모드
                    - 16 : 불투명도 조절 모드
                    - 17 : 이미지 추가 모드
                    - 18 : Advanced Labeling 모드
                History:
                    Yugyeong Hong(2026.02.04) - Added Semi Auto Labeling click event handler
                    Hyunsu Kim(2026.05.12) - Added flip count to maintain the flip state of the image and pass it to display to determine the exact direction of rotation
                    GaEun Hwang(2026.05.28) - Added the right-click event to open the rectangle sub menu.
                    
        """
        pen_mode = mode
        if self.pen_control_dict['pen_control_sw']:
            for i, obj in enumerate(self.pen_obj_dict.keys()):
                if (switch_obj_key_to_pen(obj) not in self.non_closable_pen_objs) and (mode_to_pen_obj_key_dict[pen_mode] not in self.non_closable_pen_objs):
                    if i != pen_mode :
                        self.close_pen_object(obj, False)

            if pen_mode == PEN_MODE_ZOOM_IN:
                # scale up
                pass 
            elif pen_mode == PEN_MODE_ZOOM_OUT:
                # scale down
                pass
            elif pen_mode == PEN_MODE_PARTIAL_ZOOM:
                # part scale up
                tmp_dict = {}
                tmp_dict['mode'] = 'modify'
                tmp_dict['type'] = 'pen'
                if ch:
                    tmp_dict['type_detail'] = 'part_scale'
                else:
                    tmp_dict['type_detail'] = 'none'
                self.pen_to_core(tmp_dict)
            elif pen_mode == PEN_MODE_DRAWING: # labeliong mode
                tmp_dict = {}
                tmp_dict['mode'] = 'modify'
                tmp_dict['type'] = 'pen'
                if ch:
                    print("pen draw mode")
                    tmp_dict['type_detail'] = 'drawing'
                else:
                    print("pen drawing None mode")
                    tmp_dict['type_detail'] = 'none'
                self.pen_to_core(tmp_dict)    
            elif pen_mode == PEN_MODE_IMAGE_MOVING: # part move
                if ch:
                    print("pen part moving mode")
                else:
                    print("pen part moving None mode")
            elif pen_mode == PEN_MODE_ERASER: # eraser
                if ch:
                    print("pen erase mode")
                else:
                    print("pen erase None mode")
            elif pen_mode == PEN_MODE_BRIGHT: # bright
                #pen bright
                self.pen_sub_open(mode=PEN_SUB_MODE_BRIGHT)           
            elif pen_mode == PEN_MODE_UNDO: #undo
                pass
            elif pen_mode == PEN_MODE_REDO: #redo
                pass
            elif pen_mode == PEN_MODE_PAINTING: #painting
                if ch:
                    print("pen painting mode")
                else:
                    print("pen painting None mode")
            elif pen_mode == PEN_MODE_MINIMAP: #minimap
                if ch:
                    print("pen minimap mode")
                else:
                    print("pen minimap None mode")
                self.pen_sub_open(mode=PEN_SUB_MODE_MINIMAP)
            
            elif pen_mode == PEN_MODE_RECTANGLE: # rectangle
                if ch:
                    print("pen rectangle mode")
                    if not self.penRectangleSubMenu.getCheckedMode():
                        # if not exist selected mode, open sub menu
                        penRectangleGlobalPos = self.pen_rectangle.mapToGlobal(QPoint())
                        self.pen_obj_dict['pen_rectangle']['menu_opened'] = True
                        chosen = self.penRectangleSubMenu.exec_(QPoint(penRectangleGlobalPos.x() + 45, penRectangleGlobalPos.y()))
                        if chosen is not None:
                            # if select mode, open sub form
                            self.rectangleModeChangeEvent(chosen)
                            self.penToDisplayMenuSignal.emit({'penType':'pen_rectangle', 'mode': chosen.data()})
                        else:
                            ch = False
                    else:
                        # if exist selected mode, open sub form
                        if self.pen_obj_dict['pen_rectangle']['sub_mode'] == DRAWING_SUB_MODE_RECTANGLE_SAL and self.pen_obj_dict['pen_rectangle']['settings'] is None:
                            self.rectangleModeChangeEvent(self.pen_obj_dict['pen_rectangle']['sub_mode'])
                else:
                    print("pen rectangle None mode")

            elif pen_mode == PEN_MODE_POLYGON: # polygon
                if ch:
                    print("pen polygon mode")
                else:
                    print("pen polygon None mode")
            elif pen_mode == PEN_MODE_OPACITY:
                if ch:
                    print("pen opacity mode")
                else:
                    print("pen opacity None mode")
                self.pen_sub_open(mode=PEN_SUB_MODE_OPACITY)
            elif pen_mode == PEN_MODE_IMAGE:
                if ch:
                    print("pen image mode")
                else:
                    print("pen image None mode")
            elif pen_mode == PEN_MODE_ROT90:
                pass
            elif pen_mode == PEN_MODE_HFLIP:
                if self.hflipCount == False:
                    self.hflipCount = True
                else:
                    self.hflipCount = False
            elif pen_mode == PEN_MODE_VFLIP:
                if self.vflipCount == False:
                    self.vflipCount = True
                else:
                    self.vflipCount = False
            elif pen_mode == PEN_MODE_ADVANCED_LABELING:
                """
                    description : When the advanced labeling button is clicked, the mode is switched according to the selected mode. 
                                    when the pixel based labeling mode is selected, the pixel based labeling mode is activated and the button is turned on.
                                    When the button is turned off, all modes are turned off and the sub form is closed.
                    author : Hyunsu Kim (2026.05.28)
                """
                if ch:
                    if self.pen_obj_dict['penAdvancedLabeling']['onMode'] == 'semiAuto':
                        self.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = True
                    elif self.pen_obj_dict['penAdvancedLabeling']['onMode'] == 'pixelBased':
                        self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] = True

                    isApplied = (self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] or
                                 self.pen_obj_dict['penAdvancedLabeling']['semiAuto'])
                    if not isApplied:
                        self.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(False)
                        if not self.showAdvancedLabelingMenu():
                            return
                else:
                    self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] = False
                    self.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = False
                    self.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(False)

            tmp_dict = {}
            tmp_dict['from'] = "main"
            tmp_dict['mode'] = pen_mode
            tmp_dict['flipCount'] = int(self.hflipCount) + int(self.vflipCount)
            tmp_dict['toggle'] = ch

            if pen_mode == PEN_MODE_ADVANCED_LABELING and ch == True:
                if self.pen_obj_dict['penAdvancedLabeling']['semiAuto'] == True:
                    tmp_dict['type_detail'] = 'semiAuto' 
                elif self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] == True:
                    tmp_dict['type_detail'] = 'pixelBased'
                else:
                    tmp_dict['type_detail'] = 'none'
                    tmp_dict['toggle'] = False
                if tmp_dict['type_detail'] == 'semiAuto':
                    tmp_dict['applyClicked'] = self.pen_obj_dict['penAdvancedLabeling']['semiAuto']
            self.pen_to_display(tmp_dict)

    def showAdvancedLabelingMenu(self):
        """
            description : Select a mode using QMenu. When selected, the function corresponding to each mode operates.
            author : Hyunsu Kim (2026.05.19)
            history:
                1. Modified by Hyunsu Kim (2026.06.04): 
                    - Modified so that the mode can be checked when clicking the menu.
                    - Modified to close the sub-form if it is open when the function is clicked.
                    - Modified semi-auto labeling to uncheck label when clicked.
                    - Modified so that the icon does not become disabled when the menu is not clicked or is right-clicked again after the feature is activated and the menu is activated.
        """
        try:
            x, y = self.penAdvancedLabeling.mapToGlobal(QPoint()).x(), self.penAdvancedLabeling.mapToGlobal(QPoint()).y()
            self.advancedLabelingMenu.move(x+45, y)
            action = self.advancedLabelingMenu.exec_()
            if action == self.actionPixelBased:
                self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] = True
                self.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = False
                self.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(True)
                self.pen_obj_dict['penAdvancedLabeling']['onMode'] = 'pixelBased'
                if self.pen_obj_dict['penAdvancedLabeling']['opened']:
                    self.pen_obj_dict['penAdvancedLabeling']['semiAutoForm'].close()
                    self.pen_obj_dict['penAdvancedLabeling']['opened'] = False
                for obj in self.pen_obj_dict.keys():
                    if obj != 'penAdvancedLabeling':
                        self.close_pen_object(obj)
                return True
            elif action == self.actionSemiAuto:
                self.advancedLabelingActionGroup.setExclusive(False)
                self.actionSemiAuto.setChecked(False)
                self.advancedLabelingActionGroup.setExclusive(True)
                self.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = False
                tmp_dict = {}
                tmp_dict["from"] = "main"
                tmp_dict["mode"] = PEN_MODE_ADVANCED_LABELING
                tmp_dict["toggle"] = False
                self.pen_to_display(tmp_dict)
                self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] = False
                for obj in self.pen_obj_dict.keys():
                    if obj != 'penAdvancedLabeling':
                        self.close_pen_object(obj)
                self.pen_sub_open(mode=PEN_SUB_MODE_SEMI_AUTO_LABELING)
                return True
            elif action is None:
                return True
            return False
        except Exception as e:
            print(f"Error showing advanced labeling menu: {e}")
            return False

    def onAdvancedLabelingRightClick(self):
        """
            description : Displays the mode selection menu when right-clicking. Does not display it if the settings window is open.
            author : Hyunsu Kim (2026.05.19)
            history:
                1. Modified by Hyunsu Kim (2026.06.04): Modified to resolve icon activation issue that occurs when the menu is not clicked after activation.
        """
        if not self.showAdvancedLabelingMenu():
            self.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(False)
            return
        tmp_dict = {}
        tmp_dict['from'] = "main"
        tmp_dict['mode'] = PEN_MODE_ADVANCED_LABELING
        tmp_dict['toggle'] = True
        if self.pen_obj_dict['penAdvancedLabeling']['semiAuto'] == True:
            tmp_dict['type_detail'] = 'semiAuto'
        elif self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] == True:
            tmp_dict['type_detail'] = 'pixelBased'
        else:
            tmp_dict['type_detail'] = 'none'
            tmp_dict['toggle'] = False
        if tmp_dict['type_detail'] == 'semiAuto':
            tmp_dict['applyClicked'] = self.pen_obj_dict['penAdvancedLabeling']['semiAuto']
        self.pen_to_display(tmp_dict)

    def pen_sub_open(self, mode=0):
        """pen sub ui를 활성화 하기 위한 함수이다.
                Parameters
                1.  mode(int)
                    - 0 : pen sub style 모드, pen 크기 설정 
                    - 1 : pen sub eraser 모드, 지우개 크기 설정
                    - 2 : display rgb change 모드, 이미지 rgb 값 변경
                History:
                    1. Yugyeong Hong(2026.02.04) - Add semi auto labeling mode for sub form open
                    2. GaEun Hwang(2026.05.28)
                        - Modified close the sub forms logic using existed close_pen_object function.
                        - Added the right-click event to open the rectangle sub menu, and implemented the corresponding logic in this function.
        """
        peb_sub_mode = mode
        if peb_sub_mode == PEN_SUB_MODE_PEN:
            if not self.sub_widget_dict['pen_style_form'].isVisible():
                self.pen_obj_dict['pen_draw_type']['opened'] = False
            if self.pen_obj_dict['pen_draw_type']['opened'] == False:
                self.pen_style_form.show()
                x, y = self.pen_draw_type.mapToGlobal(QPoint()).x(), self.pen_draw_type.mapToGlobal(QPoint()).y()
                self.pen_style_form.move(x+45,y-80)
                self.pen_obj_dict['pen_draw_type']['opened'] = True
                
                for key in ['pen_eraser', 'penAdvancedLabeling', 'pen_rectangle']:
                    self.close_pen_object(key)

            else:
                self.pen_style_form.close()
                self.pen_obj_dict['pen_draw_type']['opened'] = False
        
        elif peb_sub_mode == PEN_SUB_MODE_RECTANGLE:
            # if sub menu or sub form is opened, close them and return
            if self.pen_obj_dict['pen_rectangle']['opened']:
                if self.pen_obj_dict['pen_rectangle']['sub_mode'] == DRAWING_SUB_MODE_RECTANGLE_SAL and self.pen_obj_dict['pen_rectangle']['settings'] is None and self.pen_obj_dict['pen_rectangle']['obj'].isChecked():
                    self.pen_obj_dict['pen_rectangle']['obj'].click()
                self.penRectangleSALForm.close()
                self.pen_obj_dict['pen_rectangle']['opened'] = False
                return
            if self.pen_obj_dict['pen_rectangle']['menu_opened']:
                if self.pen_obj_dict['pen_rectangle']['sub_mode'] is None and self.pen_obj_dict['pen_rectangle']['obj'].isChecked():
                    self.pen_obj_dict['pen_rectangle']['obj'].click()
                self.penRectangleSubMenu.close()
                self.pen_obj_dict['pen_rectangle']['menu_opened'] = False
                return
            
            # if other pen's sub form is opened, close it
            for key in ['pen_draw_type', 'pen_eraser', 'penAdvancedLabeling']:
                self.close_pen_object(key)

            penRectangleGlobalPos = self.pen_rectangle.mapToGlobal(QPoint())
            checkedMode = self.penRectangleSubMenu.exec_(QPoint(penRectangleGlobalPos.x() + 45, penRectangleGlobalPos.y()))
            self.pen_obj_dict['pen_rectangle']['menu_opened'] = True
            if checkedMode is not None:
                self.rectangleModeChangeEvent(checkedMode)
                emitDict = {}
                emitDict['penType'] = 'pen_rectangle'
                emitDict['mode'] = self.pen_obj_dict['pen_rectangle']['sub_mode']
                self.penToDisplayMenuSignal.emit(emitDict)
                self.pen_obj_dict['pen_rectangle']['menu_opened'] = False

        elif peb_sub_mode == PEN_SUB_MODE_ERASER:
            if not self.sub_widget_dict['pen_eraser_form'].isVisible():
                self.pen_obj_dict['pen_eraser']['opened'] = False
            if self.pen_obj_dict['pen_eraser']['opened'] == False:
                self.pen_eraser_form.show()
                x, y = self.pen_eraser.mapToGlobal(QPoint()).x(), self.pen_eraser.mapToGlobal(QPoint()).y()
                self.pen_eraser_form.move(x+45,y-40)
                self.pen_obj_dict['pen_eraser']['opened'] = True
                
                for key in ['pen_draw_type', 'penAdvancedLabeling', 'pen_rectangle']:
                    self.close_pen_object(key)

            else:
                self.pen_eraser_form.close()
                self.pen_obj_dict['pen_eraser']['opened'] = False

        elif peb_sub_mode == PEN_SUB_MODE_BRIGHT:
            if self.pen_obj_dict['pen_bright']['opened'] == False:
                self.display_rgb_change_form.show()
                x, y = self.pen_bright.mapToGlobal(QPoint()).x(), self.pen_bright.mapToGlobal(QPoint()).y()
                self.display_rgb_change_form.move(x+45,y-40)
                self.pen_obj_dict['pen_bright']['opened'] = True
            else:
                self.display_rgb_change_form.close()
                self.pen_obj_dict['pen_bright']['opened'] = False
                if self.pen_bright.isChecked():
                    self.pen_bright.toggle()

        elif peb_sub_mode == PEN_SUB_MODE_MINIMAP:
            if self.pen_obj_dict['pen_minimap']['obj'].isChecked():
                self.pen_minimap_form.show()
                x, y = self.pen_minimap.mapToGlobal(QPoint()).x(), self.pen_minimap.mapToGlobal(QPoint()).y()
                self.pen_minimap_form.move(x+45,y-40)
            else:
                self.pen_minimap_form.close()
        
        elif peb_sub_mode == PEN_SUB_MODE_OPACITY:
            if self.pen_obj_dict['pen_opacity']['opened'] == False:
                self.pen_obj_dict['pen_opacity']['opened'] = True
                self.pen_opacity_form.show()
            else:
                self.pen_obj_dict['pen_opacity']['opened'] = False

        elif peb_sub_mode == PEN_SUB_MODE_SEMI_AUTO_LABELING:
            self.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(False)
            self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] = False
            self.pen_obj_dict['penAdvancedLabeling']['semiAutoForm'].show()
            x = self.penAdvancedLabeling.mapToGlobal(QPoint()).x()
            y = self.penAdvancedLabeling.mapToGlobal(QPoint()).y()
            self.pen_obj_dict['penAdvancedLabeling']['semiAutoForm'].move(x + 45, y - 80)
            self.pen_obj_dict['penAdvancedLabeling']['opened'] = True
    
    def rectangleModeChangeEvent(self, mode, open=True):
        """
            @ Description: A function to handle the event when the rectangle mode is changed.
            @ Author: GaEun Hwang (2026.05.28)
        """
        penRectangleGlobalPos = self.pen_rectangle.mapToGlobal(QPoint())
        if isinstance(mode, QtWidgets.QAction):
            mode = mode.data()
        if mode == DRAWING_SUB_MODE_RECTANGLE_SAL:
            # If the SAL mode is selected but the settings are not configured, open the settings form. Otherwise, just open the SAL form.
            if open == True or (self.pen_obj_dict['pen_rectangle']['settings'] is None):
                self.penRectangleSALForm.show()
                self.penRectangleSALForm.move(penRectangleGlobalPos.x() + 45, penRectangleGlobalPos.y() - 40)
                self.pen_obj_dict['pen_rectangle']['opened'] = True
        
        elif mode == DRAWING_SUB_MODE_RECTANGLE_DEFAULT:
            pass
 
        self.pen_obj_dict['pen_rectangle']['sub_mode'] = mode

        if not self.pen_obj_dict['pen_rectangle']['obj'].isChecked():
            self.pen_obj_dict['pen_rectangle']['obj'].click()
    
    @pyqtSlot(dict)
    def recv_from_core(self, output):
        if output["from"] == "image":
            if output["mode"] == "unchecked":
                self.hflipCount = False
                self.vflipCount = False
                for obj in self.pen_obj_dict.keys():
                    if "sub_form" in self.pen_obj_dict[obj]:
                        if obj == 'penAdvancedLabeling':
                            self.pen_obj_dict[obj]['semiAutoForm'].close()
                        else:
                            self.pen_obj_dict[obj]["sub_form"].close()
            
            if output["mode"] in ("unchecked", "checked"):
                self.pen_obj_dict['penAdvancedLabeling']['pixelBased'] = False
                self.pen_obj_dict['penAdvancedLabeling']['semiAuto'] = False
                self.pen_obj_dict['penAdvancedLabeling']['opened'] = False
                self.pen_obj_dict['penAdvancedLabeling']['obj'].setChecked(False)
                self.pen_obj_dict['penAdvancedLabeling']['onMode'] = None
                self.advancedLabelingActionGroup.setExclusive(False)
                self.actionPixelBased.setChecked(False)
                self.actionSemiAuto.setChecked(False)
                self.advancedLabelingActionGroup.setExclusive(True)
        
        elif output["from"] == "displayMenu":
            if output["mode"] == "changeRectangleMode":
                if output["changedMode"].data() == DRAWING_SUB_MODE_RECTANGLE_SAL:
                    self.penRectangleSubMenu.SALModeAction.setChecked(True)
                    
                elif output["changedMode"].data() == DRAWING_SUB_MODE_RECTANGLE_DEFAULT:
                    self.penRectangleSubMenu.defaultModeAction.setChecked(True)
                self.rectangleModeChangeEvent(output["changedMode"], open=False)
            
            elif output["mode"] == "adjustLabelOpacity":
                clickedLabelClass = output["labelClass"]
                self.pen_opacity.click()
                labelClassOrder = self.pen_opacity_form.label_order_list.index(clickedLabelClass)
                self.pen_opacity_form.pen_sub_adv_opacity_sub_specific_combo.setCurrentIndex(labelClassOrder)

    def pen_to_core(self, input):
        """pen에서 core로 시그널을 보내기 위한 함수 선언문이다. Core DB에 대한 값을 업데이트하거나 조정하기 위한 함수로 쓰인다.
                Parameters
                1.	input(dict): Core DB업데이트를 위한 dictionary
        """
        self.pen_to_core_signal.emit(input)


    def pen_to_display(self, input):
        """pen에서 display로 시그널을 보내기 위한 함수 선언문이다. Core에게 먼저 시그널을 보내어 display에 최종적으로 전달된다.
                Parameters
                1.	input(dict): Dispaly 업데이트를 위한 dictionary

        """
        self.pen_to_display_signal.emit(input)

    def pen_opacity_to_display(self, input):
        self.pen_opacity_to_display_signal.emit(input)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Pen_Form()
    # ui.setupUi(Form)
    # Form.show()
    sys.exit(app.exec_())
