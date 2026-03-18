"""
    ELROILAB Kit

    Copyright 2024. Elroilab All rights reserved.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from constants.constants import VIEWER_ORIGINAL_WIDTH

class Display_viewer(QtWidgets.QGraphicsView):
    viewer_signal = QtCore.pyqtSignal(dict)
    def __init__(self, usescrollbar:bool=True):
        super(Display_viewer, self).__init__()
        self._zoom = 0
        self._zoom_max_value = 10
        self._graph_point_weight = 1
        self._isopened = False
        self._scene = QtWidgets.QGraphicsScene()
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._photo.setZValue(0)
        self._scene_graph_point = {}
        self._scene.addItem(self._photo)
        self.setScene(self._scene)

        self.preview_rect = QtWidgets.QGraphicsRectItem()
        self.pen = QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.DashLine)
        self.preview_rect.setPen(self.pen)
        self.preview_rect.setZValue(1)
        self._scene.addItem(self.preview_rect)
        self.start_pos = None
        self.rotation_count = 0
        self.originViewRectWidth = VIEWER_ORIGINAL_WIDTH # default value for fitting view when initializing viewer

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        if usescrollbar:
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        else:
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def hasPhoto(self):
        return self._isopened

    def fitInView(self):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
            self._scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            if viewrect.width() == 0:
                factor = min(self.originViewRectWidth / scenerect.width(),
                        viewrect.height() / scenerect.height())
            else:
                factor = min(viewrect.width() / scenerect.width(),
                        viewrect.height() / scenerect.height())
            self._scale(factor, factor)
            self._zoom = 0

    def initPhoto(self, pixmap=None, dragmode=1, init=False):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._photo.setPixmap(pixmap)
        else:
            self._photo.setPixmap(QtGui.QPixmap())

        if dragmode==0:
            self.updateDrag(False)

        if init:
            self._isopened = False
        else:
            self._isopened = True
        self.fitInView()

    def updatePhoto(self, pixmap, fitinview=False):
        self._isopened = True
        self._photo.setPixmap(pixmap)
        if fitinview:
            self.fitInView()

    def updateDrag(self, mode):
        if mode == 0:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        else:
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                mode = 0
            else:
                mode = 1
            self._modscale(mode)
            """
                Description: Improved wheel event signal emit
                Modified by GaEun Hwang (2025.10.20)
            """
            tmp_dict={
            "mode" : 3,
            "event":event,
            "under": False,
            "zoom":self._zoom
            }
            if self._photo.isUnderMouse():
                tmp_dict["under"] = True
            self.viewer_signal.emit(tmp_dict)

    def _modscale(self, mode):
        if mode == 0:
            factor = 1.25
            self._zoom += 1
        elif mode == 1:
            factor = 0.8
            self._zoom -= 1

        if 0 < self._zoom < self._zoom_max_value:
            self._scale(factor, factor)
            if len(self._scene_graph_point):
                self.update_graph_point()
        elif self._zoom == 0:
            self.fitInView()
        elif 0 > self._zoom:
            self._zoom = 0
        elif self._zoom >= self._zoom_max_value:
            self._zoom = self._zoom_max_value -1

    def _scale(self, factor_1= 1.25, factor_2= 1.25):
        self.scale(factor_1, factor_2)

    def init_rect_value(self, current_pos:list[int]=None, color:list[int]=None) -> None:
        if current_pos:
            self.start_pos = QtCore.QPoint(*current_pos)
        color = QtGui.QColor(*color)
        self.pen.setColor(color)
        self.preview_rect.setPen(self.pen)
        self.preview_rect.setVisible(True)

    def draw_rect_preview(self, current_pos:list[int]) -> None:
        current_pos = QtCore.QPoint(current_pos[0]+1, current_pos[1]+1)
        rect = QtCore.QRectF(self.start_pos, current_pos).normalized()
        self.preview_rect.setRect(rect)
        #self._scene.setSceneRect(self._scene.itemsBoundingRect())

    def remove_rect_preview(self) -> None:
        self.start_pos = None
        self.preview_rect.setRect(QtCore.QRectF())
        self.preview_rect.setVisible(False)

    def rotate_viewer(self, angle:int=90, clock_wise:bool=True) -> None:
        angle = abs(angle) if clock_wise else -abs(angle)
        self.rotate(angle)
        self.rotation_count += 1
    
    def reset_view(self) -> None:
        if self.isTransformed():
            self.resetTransform()
        self.rotation_count = 0

    def flip_horizontal(self):
        """X축 반전"""
        if self.rotation_count % 2 == 0:  # 짝수 회전 (0도, 180도)
            self.scale(-1, 1)
        else:  # 홀수 회전 (90도, 270도)
            self.scale(1, -1)

    def flip_vertical(self):
        """Y축 반전"""
        if self.rotation_count % 2 == 0:  # 짝수 회전 (0도, 180도)
            self.scale(1, -1)
        else:  # 홀수 회전 (90도, 270도)
            self.scale(-1, 1)

    def mousePressEvent(self, event) -> None:
        """
            @description : checking the mouse press event
            @author : MyoungHwan
            @history
                1.Modified by MyoungHwan(20240529)
                    - Add under variable and checking detect mouse point
        """
        tmp_dict={
            "mode" : 0,
            "point" : self.mapToScene(event.pos()), 
            "event":event,
            "under":False
        }

        if self._photo.isUnderMouse():
            tmp_dict["under"] = True
        self.viewer_signal.emit(tmp_dict)
        super(Display_viewer, self).mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """
            @description : checking the mouse move event
            @author : MyoungHwan
            @history
                1. Modified by MyoungHwan(20240529)
                    - Add under variable and checking detect mouse point
        """
        tmp_dict={
            "mode" : 1,
            "point" : self.mapToScene(event.pos()), 
            "event":event,
            "under":False
        }
        if self._photo.isUnderMouse():
            tmp_dict["under"] = True
        self.viewer_signal.emit(tmp_dict)
        super(Display_viewer, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """
            @description : checking the mouse release event
            @author : MyoungHwan
            @history
                1. Modified by MyoungHwan(20240529)
                    - Add under variable and checking detect mouse point
        """
        tmp_dict={
            "mode" : 2,
            "point" : self.mapToScene(event.pos()), 
            "event":event,
            "under":False
        }
        if self._photo.isUnderMouse():
            tmp_dict["under"] = True
        self.viewer_signal.emit(tmp_dict)
        super(Display_viewer, self).mouseReleaseEvent(event)

    def add_scene(self) -> None:
        self._scene.addItem(self._photo)
        self._scene.addItem(self.preview_rect)
    
    def clear_scene(self) -> None:
        for item in self._scene.items():
            self._scene.removeItem(item)
        
        self._scene_graph_point = {}

    def add_graph_point(self, cnt, obj_text, obj_rect, point, color) -> None:
        self._graph_point_weight = len(str(cnt)) - 1 
        x,y = point
        font = QtGui.QFont('Times',self._zoom_max_value - self._zoom)
        color = QtGui.QColor(color[0], color[1], color[2])
        obj_text.setDefaultTextColor(color)
        obj_text.setFont(font)
        obj_text.setPos(x - 4 - (self._zoom_max_value - self._zoom - 1)  - self._graph_point_weight   , y - 5 - (self._zoom_max_value - self._zoom  - 1 ) - self._graph_point_weight)
        self._scene_graph_point[cnt] = {
            "obj_text": obj_text,
            "obj_rect": obj_rect, 
            'pos': (x, y),
            'font':font, 
            "text":str(cnt),
            "value_weight": self._graph_point_weight,
            "color" : color
            }

    def update_graph_point(self) -> None:
        for _, _dict in self._scene_graph_point.items():
            if self._zoom !=0:
                tfont = QtGui.QFont('Times',self._zoom_max_value - self._zoom)
                x, y = _dict['pos']
                value_weight = _dict['value_weight']
                tmp_obj = _dict['obj_text']
                tmp_obj.setFont(tfont)
                tmp_obj.setPos(x - 4 - (self._zoom_max_value - self._zoom - 1)  - value_weight , y - 5 - (self._zoom_max_value - self._zoom -1) - value_weight)