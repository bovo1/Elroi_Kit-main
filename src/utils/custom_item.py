"""
    Elroi Kit

    Copyright 2025. Elroilab All rights reserved.
"""

import numpy as np

from pyqtgraph import ScatterPlotItem
from PyQt5 import QtCore, QtGui, QtWidgets

class customScatterItem(ScatterPlotItem):
    """
        @description : custom scatter plot item for stable hover function
        @author : GaEun Hwang (2025.08.28)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def hoverEvent(self, mouseEvent):
        """
            @description : hover event for custom scatter item
            @author : GaEun Hwang (2025.08.28)
        """
        # hoverEvent function is almost same as original
        # the reason for redefine event is to modify tooltip and for stable hover function
        # refer to this site for information on the meaning of variables and maintenance
        # https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/scatterplotitem.html#pyqtgraph.ScatterPlotItem

        # self.opts is a dictionary containing options for the scatter plot item
        # contains like [compositionMode, name, symbol, size, pen, brush, hoverable, tip ...]
        if self.opts['hoverable']:
            # self.data is array containing data about each scatter
            old = self.data['hovered']
            if mouseEvent.exit:
                new = np.zeros_like(self.data['hovered'])
            else:
                new = self._maskAt(mouseEvent.pos())

            if self._hasHoverStyle():
                self.data['sourceRect'][old ^ new] = 0
                self.data['hovered'] = new
                self.updateSpots()

            points = self.points()[new][::-1]
            # Show information about hovered points in a tooltip
            vb = self.getViewBox()
            if vb is not None and self.opts['tip'] is not None:
                if len(points) > 0:
                    # original cutoff value is 3
                    # because it is not necessary to show 3 item information in the tooltip
                    cutoff = 1
                    tip = [self.opts['tip'](x=pt.pos().x(), y=pt.pos().y(), data=pt.data())
                           for pt in points[:cutoff]]
                    if len(points) > cutoff:
                        tip.append('({} others...)'.format(len(points) - cutoff))
                    vb.setToolTip('\n\n'.join(tip))
                    self._toolTipCleared = False
                    # specify event was accepted
                    mouseEvent.accept()
                elif not self._toolTipCleared:
                    vb.setToolTip("")
                    self._toolTipCleared = True
                    # specify event was ignored
                    mouseEvent.ignore()

            self.sigHovered.emit(self, points, mouseEvent)

class customPolygonItem(QtWidgets.QGraphicsItem):
    """
        @description : custom polygon item for polygon drawing
        @author : GaEun Hwang (2025.10.01)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init()

    def init(self):
        """
            @description : init polygon components for polygon drawing
            @author : GaEun Hwang (2025.10.20)
        """
        self.isDrawing = False
        self.isSnapped = False
        self.isMatched = False

        self.points = []
        self.undo = []
        self.redo = []

        self.currentCursorPos = QtCore.QPointF(0, 0)
        self.polygon = None
        self.pointRadius = 0.5
        self.emphasizedPointRadius = 3.0
        self.minEmphasizedPointRadius = 1.0
        self.maxEmphasizedPointRadius = 3.0
        self.snapRadius = 10.0
        self.minSnapRadius = 2.0
        self.maxSnapRadius = 10.0
        self.shiftPointValue = 0.5

        self.polygonColorAlpha = 150
        self.matchColorAlpha = 50
        self.previewLinePen = QtGui.QPen(QtCore.Qt.white, 0.5, QtCore.Qt.PenStyle.DashLine)
        self.matchPen = QtGui.QPen(QtGui.QColor(255, 255, 255), 0.2)
        self.matchBrush = QtGui.QBrush(QtGui.QColor(255, 255, 255, self.matchColorAlpha))
        self.linePen = QtGui.QPen(QtCore.Qt.white, 0.5)
        self.pointBrush = QtGui.QBrush(QtCore.Qt.white)
        self.polygonBrush = QtGui.QBrush(QtGui.QColor(255, 255, 255, self.matchColorAlpha))

    def setStyle(self, color:QtGui.QColor):
        """
            @description : set polygon style color
            @author : GaEun Hwang (2025.10.20)
        """
        self.previewLinePen.setColor(color)
        self.linePen.setColor(color)
        self.matchPen.setColor(color)
        self.pointBrush.setColor(color)
        color.setAlpha(self.polygonColorAlpha)
        self.polygonBrush.setColor(color)
        self.update()

    def addPoint(self, point: QtCore.QPointF):
        """
            @description : add point to polygon drawing
            @author : GaEun Hwang (2025.10.20)
        """
        self.prepareGeometryChange()
        if len(self.points) == 0:
            self.isDrawing = True
            self.polygon = None
        self.undo.append(self.points.copy())
        self.redo.clear()
        self.points.append(point)
        # complete polygon
        if len(self.points) > 1 and self.points[0] == point:
            self.completeDrawing()
        self.updateCursorPos(point)
        self.update()

    def updateCursorPos(self, pos: QtCore.QPointF):
        """
            @description : update current cursor position while polygon drawing
            @author : GaEun Hwang (2025.10.20)
        """
        if self.isDrawing:
            self.currentCursorPos = pos
            self.update()

    def boundingRect(self):
        """
            @description : get bounding rect of polygon. boundingRect method is mandatory to override QGraphicsItem.
            @author : GaEun Hwang (2025.10.20)
        """
        all_points = self.points + ([self.currentCursorPos] if self.isDrawing else [])
        if not all_points:
            return QtCore.QRectF()
        
        if self.scene() and self.scene().views():
            # get first view in scene
            view = self.scene().views()[0]
            # get view rect and transform to scene coordinates
            viewRect = view.mapToScene(view.viewport().rect()).boundingRect()
            return viewRect

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionGraphicsItem, widget: QtWidgets.QWidget):
        # option, widget parameters are required for paint function override
        """
            @description : polygon painter
            @author : GaEun Hwang (2025.10.20)
        """
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        if self.isDrawing and len(self.points) > 0:
            # draw Line
            if len(self.points) > 1:
                painter.setPen(self.linePen)
                centerCoordList = [self.setPointCenter(p) for p in self.points]
                painter.drawPolyline(QtGui.QPolygonF(centerCoordList))

            # draw Point
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(self.pointBrush)
            for p in self.points:
                centerCoord = self.setPointCenter(p)
                painter.drawEllipse(centerCoord, self.pointRadius, self.pointRadius)
            
            # draw Preview Line
            currentCursorPosCenter = self.setPointCenter(self.currentCursorPos)
            painter.setPen(self.previewLinePen)
            if (currentCursorPosCenter - self.points[-1]).manhattanLength() > 1:
                centerCoord = self.setPointCenter(self.points[-1])
                painter.drawLine(centerCoord, currentCursorPosCenter)

            # draw Preview Point
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(self.pointBrush)
            painter.drawEllipse(currentCursorPosCenter, self.pointRadius, self.pointRadius)
            painter.setBrush(self.polygonBrush)
            centerCoordList = [self.setPointCenter(p) for p in self.points] + [currentCursorPosCenter]
            painter.drawPolygon(QtGui.QPolygonF(centerCoordList))

            # if same current point and first point, show match circle
            if self.isMatched:
                painter.setPen(self.matchPen)
                painter.setBrush(self.matchBrush)
                centerCoord = self.setPointCenter(self.points[0])
                # draw snap range circle
                painter.drawEllipse(centerCoord, self.snapRadius, self.snapRadius)
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(self.pointBrush)
                # draw emphasized first point
                painter.drawEllipse(centerCoord, self.emphasizedPointRadius, self.emphasizedPointRadius)
    
    def clear(self):
        """
            @description : clear polygon components
            @author : GaEun Hwang (2025.10.20)
        """
        self.init()
        self.update()

    def getDistance(self, currentCursorPos: QtCore.QPointF, otherPoint: QtCore.QPointF):
        """
            @description : get distance between current cursor position and other point
            @author : GaEun Hwang (2025.10.20)
        """
        if len(self.points) > 0:
            diffVector = currentCursorPos - otherPoint
            distance = diffVector.manhattanLength()
            return distance
        else:
            return None
        
    def isAvailableToSnap(self):
        """
            @description : check if available to snap to first point
            @author : GaEun Hwang (2025.10.20)
        """
        if len(self.points) > 2:
            distance = self.getDistance(self.currentCursorPos, self.points[0])
            if distance is not None and distance <= self.snapRadius:
                return True
            else: return False
        else: return False

    def isAvailableToMatch(self):
        """
            @description : check if available to match first point
            @author : GaEun Hwang (2025.10.20)
        """
        if len(self.points) > 2:
            distance = self.getDistance(self.currentCursorPos, self.points[0])
            if distance == 0:
                return True
            else:
                return False

    def updateRadius(self, scale):
        """
            @description : update point radius according to zoom scale
            @author : GaEun Hwang (2025.10.20)
        """
        scale += 1  # to avoid division by zero. scale -> 0~9
        # this formula is designed to keep snapRadius and emphasizedPointRadius within min and max values
        self.snapRadius = min(self.maxSnapRadius, max(self.minSnapRadius * (10/scale), self.minSnapRadius))
        self.emphasizedPointRadius = min(self.maxEmphasizedPointRadius, self.minEmphasizedPointRadius + (1/scale))
        self.update()

    def setPointCenter(self, Point: QtCore.QPointF):
        """
            @description : set point center position for better visibility
            @author : GaEun Hwang (2025.10.20)
        """
        return QtCore.QPointF(Point.x() + self.shiftPointValue, Point.y() + self.shiftPointValue)
    
    def completeDrawing(self):
        """
            @description : complete drawing and finalize polygon
            @author : GaEun Hwang (2025.10.20)
        """
        self.polygon = QtGui.QPolygonF(self.points[:-1])
        self.isDrawing = False
        self.isSnapped = False
        self.isMatched = False
        self.points.clear()
        self.undo.clear()
        self.redo.clear()

    def setUndo(self):
        """
            @description : set undo for polygon drawing
            @author : GaEun Hwang (2025.10.20)
        """
        if len(self.undo) > 0:
            # if undo stack exists, pop it and add to redo stack
            undoState = self.undo.pop()
            # add self.points to redo stack because undoState does not contain current points
            self.redo.append(self.points.copy())
            self.points = undoState
            if len(self.undo) == 0 and len(self.points) == 0:
                # if undo stack and self.points is empty, stop drawing mode
                self.prepareGeometryChange()
                self.isDrawing = False
                self.clearUndoRedoStack()
            self.update()

    def setRedo(self):
        """
            @description : set redo for polygon drawing
            @author : GaEun Hwang (2025.10.20)
        """
        if len(self.redo) > 0:
            # if redo stack exists, pop it and add to undo stack
            redoState = self.redo.pop()
            # add self.points to undo stack because redoState does not contain current points
            self.undo.append(self.points.copy())
            self.points = redoState
            self.update()
        
    def clearUndoRedoStack(self):
        """
            @description : clear undo and redo stack
            @author : GaEun Hwang (2025.10.20)
        """
        self.undo.clear()
        self.redo.clear()
        
    def getPointFromPolygon(self):
        """
            @description : get points from polygon including boundary points
            @author : GaEun Hwang (2025.10.20)
        """
        if self.polygon is None or self.polygon.isEmpty():
            return np.array([], dtype=np.int32)
        
        # calculate boundingRect
        rect = self.polygon.boundingRect()
        left, top = int(rect.left()), int(rect.top())
        right, bottom = int(rect.right()) + 1, int(rect.bottom()) + 1
        width, height = right - left, bottom - top

        # if width or height is smaller than or equal to 0, return empty array
        if width <= 0 or height <= 0:
            return np.array([], dtype=np.int32)
        
        # calculate internal + boundary points
        # create black and white Image
        img = QtGui.QImage(width, height, QtGui.QImage.Format_Alpha8)
        # 0 is black, 255 is white
        img.fill(0)
        
        # transform polygon points to local coordinates
        poly_local = QtGui.QPolygonF([QtCore.QPointF(p.x() - left, p.y() - top) for p in self.polygon])
        
        # create QPainter
        painter = QtGui.QPainter(img)
        
        # draw polygon with internal + boundary points using white color
        painter.setPen(QtGui.QPen(QtCore.Qt.white, 0.5))
        painter.setBrush(QtCore.Qt.white)
        painter.drawPolygon(poly_local)
        painter.end()
        
        ptr = img.bits()
        ptr.setsize(img.sizeInBytes())
        stride = img.bytesPerLine()
        # transform to numpy array
        arr = np.frombuffer(ptr, np.uint8).reshape((height, stride))
        mask = arr[:, :width]
        
        # find non-zero points
        ys, xs = np.nonzero(mask)
        # transform to original coordinate system
        points = np.column_stack((xs + left, ys + top)).astype(np.int32)
        
        # remove duplicate points
        if len(points) > 0:
            points = np.unique(points, axis=0)
        
        return points
