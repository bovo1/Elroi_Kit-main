"""
    Elroi Kit

    Copyright 2025. Elroilab All rights reserved.
"""

import numpy as np
from io import BytesIO

from pyqtgraph import ScatterPlotItem, exporters, PlotItem
from pyqtgraph import functions as fn
from pyqtgraph.widgets import MatplotlibWidget
from matplotlib import rcParams
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
        self.polygon = QtGui.QPolygonF(self.points[:])
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


class customGraphMatplotlibExporter(exporters.MatplotlibExporter):
    """
        @description : custom graph image exporter for exporting graph with custom parameter
        @author : GaEun Hwang (2026.04.14)
    """
    # pyqtgraph symbol → matplotlib marker mapping
    SYMBOL_PG_TO_MPL = {
        'o'           : 'o',    # circle
        's'           : 's',    # square
        't'           : 'v',    # triangle_down
        't1'          : '^',    # triangle_up
        't2'          : '>',    # triangle_right
        't3'          : '<',    # triangle_left
        'd'           : 'd',    # thin_diamond
        '+'           : 'P',    # plus (filled)
        'x'           : 'X',    # x (filled)
        'p'           : 'p',    # pentagon
        'h'           : 'h',    # hexagon1
        'star'        : '*',    # star
        'arrow_up'    : 6,      # caretup
        'arrow_right' : 5,      # caretright
        'arrow_down'  : 7,      # caretdown
        'arrow_left'  : 4,      # caretleft
        'crosshair'   : 'o',    # fallback: circle
        '|'           : '|',    # vertical line
        '_'           : '_',    # horizontal line
    }
    def __init__(self, item, parent=None):
        super().__init__(item)
        self.params = {}    # matplotlib export parameters
        self.matplotlibWindow = customMatplotlibWindow(parent)    # custom matplotlib window for showing exported graph and copying to clipboard
    
    def export(self, copy=False):
        """
            @description : export graph using matplotlib with custom parameters
                           this function is redefined based on original export function of MatplotlibExporter
            @author : GaEun Hwang (2026.04.14)
        """
        if not isinstance(self.item, PlotItem):
            raise Exception("MatplotlibExporter currently only works with PlotItem")
        
        customGraphMatplotlibExporter.windows.append(self.matplotlibWindow)
        fig = self.matplotlibWindow.getFigure()
        ax = fig.add_subplot(111, title=self.item.titleLabel.text)
        
        # clear previous plot data
        ax.clear()
        # clean axis ticks and spines
        self.cleanAxes(ax)

        # plot curve data on matplotlib window
        self.plotCurveItem(ax)
        # apply style to matplotlib window based on export parameters
        self.applySetting(ax, fig)

        # resize the canvas to fit the specified width and height in parameters
        self.matplotlibWindow.matplotlibWidget.getFigure().canvas.setFixedSize(self.params["width"], self.params["height"])
        self.matplotlibWindow.draw()

        if copy:
            self.matplotlibWindow.copyToClipboard(size=(self.params["width"], self.params["height"]))
        else:
            self.matplotlibWindow.show()

    def plotCurveItem(self, ax):
        """
            @description : plot data on matplotlib axis
            @author : GaEun Hwang (2026.04.15)
        """
        xAxis = self.item.getAxis("bottom")
        yAxis = self.item.getAxis("left")
        
        # if autoSIPrefix(default = enable) is enabled, pyqtgraph scales the display values (e.g. 1000 → 1k)
        # we must apply the same scale factor to keep matplotlib values consistent with pyqtgraph
        xScale = xAxis.autoSIPrefixScale if xAxis.autoSIPrefix else 1.0
        yScale = yAxis.autoSIPrefixScale if yAxis.autoSIPrefix else 1.0

        for item in self.item.curves:
            # skip curves hidden via setVisible(False) (e.g. hidden graph groups)
            if not item.isVisible():
                continue
            x, y = item.getData()
            # apply SI scale to match pyqtgraph's displayed axis values
            ax.plot(x * xScale, y * yScale, **self.makePlotKwargs(item))

            # if fillLevel and fillBrush are both set, draw a filled area under the curve
            if item.opts.get("fillLevel") is not None and item.opts.get("fillBrush") is not None:
                fillcolor = fn.mkBrush(item.opts["fillBrush"]).color().getRgbF()
                ax.fill_between(x=x * xScale, y1=y * yScale, y2=item.opts["fillLevel"], facecolor=fillcolor)

        # match the matplotlib view range exactly to pyqtgraph's current viewport
        # without this, matplotlib auto-scales and the result looks different from pyqtgraph
        xr, yr = self.item.viewRange()
        ax.set_xbound(xr[0] * xScale, xr[1] * xScale)
        ax.set_ybound(yr[0] * yScale, yr[1] * yScale)
        ax.set_xlabel(xAxis.label.toPlainText())
        ax.set_ylabel(yAxis.label.toPlainText())

    def makePlotKwargs(self, item):
        """
            @description : build plot keyword arguments for matplotlib plot function based on pyqtgraph curve item options
            @author : GaEun Hwang (2026.04.15)
        """
        opts = item.opts
        pen = fn.mkPen(opts["pen"]) # convert pyqtgraph pen definition to QPen object
        kwargs = {
            "color": pen.color().getRgbF(),
            "linewidth": pen.widthF(),
            "linestyle": "" if pen.style() == QtCore.Qt.PenStyle.NoPen else '-',
            "marker": None,
            "markersize": None,
            "markeredgecolor": None,
            "markerfacecolor": None,
        }

        # add marker-related kwargs only if a symbol is defined on the curve
        if opts.get("symbol") is not None:
            kwargs.update({
                # translate pyqtgraph symbol name to matplotlib marker identifier
                "marker": self.SYMBOL_PG_TO_MPL.get(opts["symbol"], ""),
                "markersize": opts["size"],
                "markeredgecolor": "none" if pen.style() == QtCore.Qt.PenStyle.NoPen else pen.color().getRgbF(),
                "markerfacecolor": fn.mkBrush(opts["brush"]).color().getRgbF() if opts["brush"] else None,
            })
        return kwargs

    def applySetting(self, ax, fig):
        """
            @description : apply setting to matplotlib axis and figure based on export parameters
            @author : GaEun Hwang (2026.04.15)
        """
        bg = self.params["backgroundColor"].getRgbF()
        axisColor = self.params["axisColor"].getRgbF()

        # set dpi for save operations via rcParams; applies globally to all subsequent saves
        rcParams["savefig.dpi"] = self.params["dpi"]
        # tight_layout automatically adjusts subplot padding
        fig.set_tight_layout(True)
        fig.set_facecolor(bg)
        ax.set_facecolor(bg)

        ax.tick_params(colors=axisColor)
        ax.title.set_color(axisColor)
        ax.xaxis.label.set_color(axisColor)
        ax.yaxis.label.set_color(axisColor)
        ax.spines["bottom"].set_color(axisColor)
        ax.spines["left"].set_color(axisColor)

        if self.params["xGridEnabled"]:
            ax.xaxis.grid(True, color=axisColor, alpha=self.params["gridOpacity"] / 100)
        if self.params["yGridEnabled"]:
            ax.yaxis.grid(True, color=axisColor, alpha=self.params["gridOpacity"] / 100)

class customMatplotlibWindow(QtWidgets.QMainWindow):
    """
        @description : custom matplotlib window for showing exported graph and copying to clipboard
        @author : GaEun Hwang (2026.04.15)
    """
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self)
        self.setObjectName("graphExportMatplotlibWindow")
        self.matplotlibWidget = MatplotlibWidget.MatplotlibWidget()
        self.matplotlibWidget.canvas.setStyleSheet("background-color: transparent;")
        self.matplotlibWidget.toolbar.setMovable(False)
        self.matplotlibWidget.toolbar.setFloatable(False)

        # add copy action to matplotlib toolbar for copying the current figure to clipboard as image
        copyAction = QtWidgets.QAction("Copy", self.matplotlibWidget.toolbar)
        copyIcon = QtGui.QIcon()
        copyIcon.addPixmap(QtGui.QPixmap("ico/labeling/graphBox/graph_export_copy.png"))
        copyAction.setIcon(copyIcon)
        copyAction.triggered.connect(lambda: self.copyToClipboard(size=None))
        
        for action in self.matplotlibWidget.toolbar.actions():
            # insert copy action before the save action in the toolbar
            if action.text() == "Save":
                self.matplotlibWidget.toolbar.insertAction(action, copyAction)
                return
        
    def __getattr__(self, attr):
        return getattr(self.matplotlibWidget, attr)
        
    def closeEvent(self, event):
        customGraphMatplotlibExporter.windows.remove(self)
        self.deleteLater()

    def copyToClipboard(self, size=None):
        """
            @description : copy current matplotlib figure to clipboard as image
            @author : GaEun Hwang (2026.04.15)
        """
        buffer = BytesIO()
        fig = self.getFigure()
        matplotlibFigureDefaultDpi = fig.get_dpi()
        if size is not None:
            fig.set_size_inches(size[0] / matplotlibFigureDefaultDpi, size[1] / matplotlibFigureDefaultDpi, forward=False)
        else:
            currentCanvasSize = self.matplotlibWidget.canvas.size()
            fig.set_size_inches(currentCanvasSize.width() / matplotlibFigureDefaultDpi, currentCanvasSize.height() / matplotlibFigureDefaultDpi, forward=False)
            
        fig.canvas.print_figure(buffer, format="png")
        buffer.seek(0)
        
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        QtWidgets.QApplication.clipboard().setPixmap(pixmap)

    def show(self):
        """
            @description : show the matplotlib window and adjust its size and position based on the canvas size and screen size
            @author : GaEun Hwang (2026.04.27)
        """
        screenGeometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        canvasSize = self.matplotlibWidget.canvas.size()
        
        if canvasSize.width() > screenGeometry.width() or canvasSize.height() > screenGeometry.height():
            # if canvas size is larger than screen size, show the window with scroll area
            self.addToolBar(self.matplotlibWidget.toolbar)
            scrollArea = QtWidgets.QScrollArea()
            scrollArea.setWidgetResizable(True)
            scrollArea.setWidget(self.matplotlibWidget.canvas)
            self.setCentralWidget(scrollArea)
            super().showMaximized()
        else:
            # if canvas size fits within the screen, show the window without scroll area
            # anchor the toolbar/canvas to the top so they stay in place when the window is maximized
            self.matplotlibWidget.vbox.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            self.setCentralWidget(self.matplotlibWidget)
            self.adjustSize()
            super().show()