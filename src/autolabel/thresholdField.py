"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    바의 임계값 칸 — 분포 곡선 위의 끌 수 있는 임계값 선, 양 끝 값, − 숫자 +, [자동] 스위치.

    그래프의 선을 직접 끌어 값을 바꾼다(끄는 동안 미리보기, 놓으면 확정). 선이 아닌 곳을 누르면 돋보기 판이 떠서
    구간을 크게 보며 조절한다. 휠, − + 는 한 칸씩, 숫자를 쳐서 바꿀 수도 있다. 값은 숫자 칸에 보이는 소수 자리로 반올림한다.

    화면만 맡는다. 값, 범위, 분포, 잠금은 바깥(컨트롤러)이 넣고, 사용자가 바꾼 값은 시그널로 알린다.
        valueChanging  : 미리보기 갱신용(끄는 동안, 한 칸씩 바꾸는 동안)
        valueCommitted : 확정(라벨에 반영)
        valueReverted  : 확정 없이 미리보기만 거둠
        autoToggled    : [자동] 스위치(모델 탭에서만 보임)
    잠기면 그래프, − +, 숫자가 흐려지고 이유는 툴팁으로 보인다. 언제 잠글지는 barState 가 정한다.
"""

import math
import unicodedata
from decimal import Decimal
from typing import Optional, Tuple

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from qtwidgets import AnimatedToggle

from autolabel.thresholdRules import densityCurve, rangeIncluding, sortedFinite

SWITCH_SIZE = QtCore.QSize(30, 25)
SWITCH_SIDE_MARGIN = 2
AUTO_LABEL_SPACING = 2
SWITCH_DISABLED_OPACITY = 0.45
GRAPH_SIZE = QtCore.QSize(120, 30)
GRAPH_MARGIN = 3
GRAB_DISTANCE = 6
STEP_BUTTON_SIZE = QtCore.QSize(16, 26)
VALUE_INPUT_MIN_WIDTH = 36
VALUE_INPUT_HEIGHT = 26
VALUE_INPUT_PADDING = 4


TIP_COLUMNS = 44


def wrapTip(text: str, columns: int = TIP_COLUMNS) -> str:
    """긴 툴팁을 공백에서 줄바꿈한다 — Qt 툴팁은 줄바꿈이 없으면 한 줄로 끝없이 길어진다. 이미 있는 줄바꿈은 그대로 둔다."""
    def width(word: str) -> int:
        return sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in word)

    lines = []
    for paragraph in text.split("\n"):
        line, used = "", 0
        for word in paragraph.split(" "):
            if line and used + 1 + width(word) > columns:
                lines.append(line)
                line, used = word, width(word)
            else:
                line, used = (line + " " + word if line else word), used + (1 if line else 0) + width(word)
        lines.append(line)
    return "\n".join(lines)


class ValueInputValidator(QtGui.QRegularExpressionValidator):
    """칸 패턴에 더해 maximum(없으면 끝없음)을 넘는 글자는 못 치게 한다 — 유사도 칸에서 999 를 치려 해도 99 까지만 들어간다."""
    maximum: Optional[float] = None

    def validate(self, text, pos):
        state, text, pos = super().validate(text, pos)
        if state != QtGui.QValidator.Invalid and self.maximum is not None:
            try:
                if float(text) > self.maximum:
                    state = QtGui.QValidator.Invalid
            except ValueError:                              # 빈 칸, '.' 같은 쓰는 중인 글자
                pass
        return state, text, pos


# 숫자 칸 입력 — 숫자와 소수점만(QDoubleValidator 는 지수 표기, 지역 소수점을 받는다). 소수는 칸이 보이는 자리 수까지만
VALUE_INPUT_INTEGER_PATTERN = r"\d{0,9}"
VALUE_INPUT_DECIMAL_PATTERN = r"\d{0,9}(\.\d{0,%d})?"
INPUT_RESERVE_FACTOR = 1
PLACEHOLDER_ALPHA = 60
DIM_FILL_ALPHA = 87
BRIGHT_FILL_ALPHA = 255
OUTLINE_ALPHA = 178
LOCKED_LINE_ALPHA = 90
LINE_WIDTH = 1.5
CHEVRON_HALF = 3
STEP_COMMIT_DELAY_MS = 400  # 한 칸씩 바꿀 때 멈춘 뒤 한 번만 확정하는 지연

MAGNIFIER_PLOT_SIZE = QtCore.QSize(340, 89)
MAGNIFIER_TICK_SPACE = 22
MAGNIFIER_MARGINS = (12, 26, 12, MAGNIFIER_TICK_SPACE)
MAGNIFIER_GAP = 6
MAGNIFIER_START_SPAN = 0.3
MAGNIFIER_MIN_SPAN = 0.01
MAGNIFIER_ZOOM_STEP = 1.25
MAGNIFIER_BINS = 120
MAGNIFIER_TICKS = 5
TAG_BACKGROUND = QtGui.QColor(0, 0, 0, 150)     # 값 표시 바탕 — 밝은 곡선 위에서도 글자가 읽히게
TAG_ARROW_SPACE = 9


def _placeholderCurve(bins: int = 60) -> np.ndarray:
    """분포가 없을 때 그리는 흐릿한 자리 표시 곡선."""
    x = np.linspace(0, 1, bins)
    return 0.15 + 0.85 * np.exp(-((x - 0.25) / 0.12) ** 2) + 0.25 * np.exp(-((x - 0.8) / 0.08) ** 2)


def _formatEnd(value: float) -> str:
    """그래프 양 끝 값 — 둥근 수라 소수 자리를 붙이지 않는다(0.000 → 0). repr 을 고정 소수점으로 풀어 쓴다('%g' 는 큰 수를 지수로 쓴다)."""
    if value == 0:                                           # -0.0 도 여기로
        return "0"
    text = format(Decimal(repr(value)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


class Switch(AnimatedToggle):
    """켜기/끄기 스위치 — AnimatedToggle 의 크기만 줄이고, 잠기면 흐리게."""

    def __init__(self, parent=None):
        super().__init__(parent, pulse_checked_color="transparent", pulse_unchecked_color="transparent")
        self.setFixedSize(SWITCH_SIZE)
        self.setContentsMargins(SWITCH_SIDE_MARGIN, 0, SWITCH_SIDE_MARGIN, 0)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._dim = QtWidgets.QGraphicsOpacityEffect(self)
        self._dim.setOpacity(SWITCH_DISABLED_OPACITY)
        self._dim.setEnabled(False)
        self.setGraphicsEffect(self._dim)

    def setCheckedQuietly(self, isChecked: bool) -> None:
        """신호 없이 값만 바꾼다(손잡이 자리도 같이)."""
        self.blockSignals(True)
        self.setChecked(isChecked)
        self.blockSignals(False)
        self.handle_position = 1 if isChecked else 0

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.EnabledChange:
            self._dim.setEnabled(not self.isEnabled())
        super().changeEvent(event)


def valueToX(value: float, valueRange: Tuple[float, float], plot: QtCore.QRectF) -> float:
    low, high = valueRange
    return plot.left() if high <= low else plot.left() + (value - low) / (high - low) * plot.width()


def xToValue(x: float, valueRange: Tuple[float, float], plot: QtCore.QRectF, isOpenEnded: bool = False) -> float:
    """x → 값. isOpenEnded(위로 끝이 없음)면 오른쪽 끝 너머로도 계속 커진다."""
    low, high = valueRange
    ratio = max((x - plot.left()) / plot.width(), 0.0) if plot.width() > 0 else 0.0
    return low + (high - low) * (ratio if isOpenEnded else min(ratio, 1.0))


def paintCurve(painter: QtGui.QPainter, plot: QtCore.QRectF, curve: Optional[np.ndarray], color: QtGui.QColor,
               splitX: Optional[float]) -> None:
    """분포 곡선. splitX(선 자리)가 있으면 왼쪽은 흐리게, 오른쪽은 밝게, 없으면 흐린 모양만."""
    shape = curve if curve is not None else _placeholderCurve()
    outline = QtGui.QPainterPath(QtCore.QPointF(plot.left(), plot.bottom() - shape[0] * plot.height()))
    for index, level in enumerate(shape):
        outline.lineTo(QtCore.QPointF(plot.left() + index / (len(shape) - 1) * plot.width(),
                                      plot.bottom() - level * plot.height()))
    area = QtGui.QPainterPath(outline)
    area.lineTo(plot.bottomRight())
    area.lineTo(plot.bottomLeft())
    area.closeSubpath()
    if splitX is None:
        painter.fillPath(area, _withAlpha(color, PLACEHOLDER_ALPHA))
        if curve is None:
            return
    else:
        split = min(max(splitX, plot.left()), plot.right())
        painter.save()
        painter.setClipRect(QtCore.QRectF(plot.left(), plot.top() - 1, split - plot.left(), plot.height() + 2))
        painter.fillPath(area, _withAlpha(color, DIM_FILL_ALPHA))
        painter.setClipRect(QtCore.QRectF(split, plot.top() - 1, plot.right() - split, plot.height() + 2))
        painter.fillPath(area, _withAlpha(color, BRIGHT_FILL_ALPHA))
        painter.restore()
    painter.setPen(QtGui.QPen(_withAlpha(color, OUTLINE_ALPHA), 1))
    painter.drawPath(outline)


def paintLine(painter: QtGui.QPainter, x: float, top: float, bottom: float, color: QtGui.QColor, showChevrons: bool) -> None:
    """임계값 선 + (올렸을 때) 양옆 ‹ ›."""
    painter.setPen(QtGui.QPen(color, LINE_WIDTH))
    painter.drawLine(QtCore.QPointF(x, top), QtCore.QPointF(x, bottom))
    if not showChevrons:
        return
    middle = (top + bottom) / 2
    for side in (-1, 1):
        tip = x + side * (CHEVRON_HALF + 5)
        base = x + side * 5
        path = QtGui.QPainterPath(QtCore.QPointF(base, middle - CHEVRON_HALF * 1.4))
        path.lineTo(tip, middle)
        path.lineTo(base, middle + CHEVRON_HALF * 1.4)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 190), 3.2))
        painter.drawPath(path)
        painter.setPen(QtGui.QPen(color, 1.3))
        painter.drawPath(path)


def _withAlpha(color: QtGui.QColor, alpha: int) -> QtGui.QColor:
    copy = QtGui.QColor(color)
    copy.setAlpha(alpha)
    return copy


class ThresholdGraph(QtWidgets.QWidget):
    """바 안의 작은 그래프. 색은 스타일시트 color, 돋보기 구간 틀은 qproperty-frameColor.

    시그널로 선 끌기, 놓기, 돋보기 요청(눌러 열기, 누른 채 끌기), 휠 한 칸을 알린다."""
    lineDragged = QtCore.pyqtSignal(float)
    lineReleased = QtCore.pyqtSignal()
    magnifyRequested = QtCore.pyqtSignal(float)
    magnifyMoved = QtCore.pyqtSignal(float)
    stepped = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("autoLabelThresholdGraph")
        self.setFixedSize(GRAPH_SIZE)
        self.setMouseTracking(True)
        self.curve: Optional[np.ndarray] = None
        self.valueRange: Tuple[float, float] = (0.0, 100.0)
        self.value = 0.0
        self.isLocked = False
        self.viewWindow: Optional[Tuple[float, float]] = None
        self.isOpenEnded = False
        self._frameColor = QtGui.QColor(16, 97, 150)
        self._isDragging = False
        self._isFollowing = False           # 선이 아닌 곳을 누른 채 — 끌면 돋보기 구간이 따라간다
        self._isHovered = False

    def getFrameColor(self) -> QtGui.QColor:
        return self._frameColor

    def setFrameColor(self, color: QtGui.QColor) -> None:
        self._frameColor = QtGui.QColor(color)
        self.update()

    frameColor = QtCore.pyqtProperty(QtGui.QColor, getFrameColor, setFrameColor)

    def setState(self, curve: Optional[np.ndarray], valueRange: Tuple[float, float], value: float, isLocked: bool) -> None:
        self.curve, self.valueRange, self.value, self.isLocked = curve, valueRange, value, isLocked
        self.update()

    def cancelDrag(self) -> None:
        """끄는 중에 잠김 — 끌기만 끝내고 확정하지 않는다."""
        self._isDragging = False
        self.update()

    def setViewWindow(self, window: Optional[Tuple[float, float]]) -> None:
        self.viewWindow = window
        self.update()

    def plotRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(GRAPH_MARGIN, 1, self.width() - 2 * GRAPH_MARGIN, self.height() - 2)

    def isInteractive(self) -> bool:
        return self.curve is not None and not self.isLocked

    def _isNearLine(self, x: float) -> bool:
        return abs(x - self._lineX(self.plotRect())) <= GRAB_DISTANCE

    def _lineX(self, plot: QtCore.QRectF) -> float:
        """선 자리 — 값이 범위 끝보다 크면(모델, 끄는 중) 오른쪽 끝에 붙여 그린다."""
        return min(valueToX(self.value, self.valueRange, plot), plot.right())

    # ------------------------------------------------------------------ 그리기
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = self.palette().color(QtGui.QPalette.WindowText)
        plot = self.plotRect()
        lineX = self._lineX(plot)
        paintCurve(painter, plot, self.curve, color, lineX if self.isInteractive() else None)
        if self.curve is None:
            return
        if self.viewWindow is not None:
            # 구간이 그래프 끝 너머로 나가면 잘라 그린다
            left = max(valueToX(self.viewWindow[0], self.valueRange, plot), plot.left())
            right = min(valueToX(self.viewWindow[1], self.valueRange, plot), plot.right())
            painter.setPen(QtGui.QPen(self._frameColor, 1.5))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(QtCore.QRectF(left, 0.75, max(2.0, right - left), self.height() - 1.5))
        lineColor = _withAlpha(color, LOCKED_LINE_ALPHA if self.isLocked else 255)
        paintLine(painter, lineX, plot.top(), plot.bottom() - LINE_WIDTH, lineColor,
                  self._isHovered and self.isInteractive() and not self._isDragging)

    # ------------------------------------------------------------------ 조작
    def enterEvent(self, event):
        self._isHovered = True
        self.update()

    def leaveEvent(self, event):
        self._isHovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton or not self.isInteractive():
            return
        if self._isNearLine(event.x()):
            self._isDragging = True
            self.update()
        else:
            self._isFollowing = True
            self.magnifyRequested.emit(xToValue(event.x(), self.valueRange, self.plotRect()))

    def mouseMoveEvent(self, event):
        if self._isDragging:
            self.lineDragged.emit(xToValue(event.x(), self.valueRange, self.plotRect(), self.isOpenEnded))
            return
        if self._isFollowing:
            # 팝업이 마우스를 잡아 떼기가 안 올 수 있다 — 버튼이 안 눌려 있으면 따라가기를 끝낸다
            if event.buttons() & QtCore.Qt.LeftButton:
                self.magnifyMoved.emit(xToValue(event.x(), self.valueRange, self.plotRect()))
                return
            self._isFollowing = False
        isNear = self.isInteractive() and self._isNearLine(event.x())
        self.setCursor(QtCore.Qt.SizeHorCursor if isNear else
                       QtCore.Qt.PointingHandCursor if self.isInteractive() else QtCore.Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self._isFollowing = False
        if self._isDragging:  # 누르기, 떼기만으로는 값이 안 바뀐다
            self._isDragging = False
            self.update()
            self.lineReleased.emit()

    def wheelEvent(self, event):
        if self.isInteractive() and event.angleDelta().y():
            self.stepped.emit(1 if event.angleDelta().y() > 0 else -1)
        event.accept()


class ThresholdMagnifier(QtWidgets.QWidget):
    """돋보기 판 — 바 그래프 위에 뜨는 큰 그래프. 값은 field 를 통해 바꾼다."""

    def __init__(self, field: "ThresholdField"):
        super().__init__(field, QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        self.setObjectName("autoLabelMagnifier")
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setMouseTracking(True)
        self.field = field
        self.window_: Tuple[float, float] = (0.0, 1.0)
        self.curve: Optional[np.ndarray] = None
        self._dragMode = None
        self._hasOverrideCursor = False  # 열려 있는 동안 앱 전체 커서를 이 판이 정한다(showEvent)
        self._panAnchor = (0.0, (0.0, 1.0))
        self._lineDragWindow = (0.0, 1.0)  # 선을 잡은 순간의 구간 — 끄는 동안 마우스 자리 → 값의 기준
        left, top, right, bottom = MAGNIFIER_MARGINS
        self.setFixedSize(MAGNIFIER_PLOT_SIZE.width() + left + right, MAGNIFIER_PLOT_SIZE.height() + top + bottom)

    # ------------------------------------------------------------------ 열기, 닫기
    def openAround(self, centerValue: float, isFollowing: bool = False) -> None:
        """centerValue 둘레를 보여 주며 바 그래프 위에 띄운다. isFollowing = 바 그래프를 누른 채 열림(끌면 구간이 따라간다)."""
        self._dragMode = "follow" if isFollowing else None
        low, high = self.field.valueRange
        self._setWindow(centerValue - (high - low) * MAGNIFIER_START_SPAN / 2,
                        centerValue + (high - low) * MAGNIFIER_START_SPAN / 2)
        graph = self.field.graph
        anchor = graph.mapToGlobal(QtCore.QPoint(graph.width() // 2, 0))
        x = anchor.x() - self.width() // 2
        y = anchor.y() - MAGNIFIER_GAP - self.height()
        screen = QtWidgets.QApplication.screenAt(anchor)
        if screen is not None:
            area = screen.availableGeometry()
            x = max(area.left(), min(x, area.right() - self.width()))
            if y < area.top():
                y = graph.mapToGlobal(QtCore.QPoint(0, graph.height())).y() + MAGNIFIER_GAP
        self.move(x, y)
        self.show()

    def followTo(self, centerValue: float) -> None:
        """구간 폭은 그대로 두고 중심만 옮긴다."""
        start, end = self.window_
        half = (end - start) / 2
        self._setWindow(centerValue - half, centerValue + half, upperLimit=end)

    def showEvent(self, event):
        """앱 전체 커서를 잡는다 — 팝업이 마우스를 잡는 동안 메인 창이 옛 위젯의 커서를 계속 보여 주기 때문(위젯 커서로는 못 고친다)."""
        super().showEvent(event)
        if not self._hasOverrideCursor:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.ArrowCursor)
            self._hasOverrideCursor = True
        self._setCursorShape(QtCore.Qt.ClosedHandCursor if self._dragMode == "follow" else QtCore.Qt.ArrowCursor)

    def hideEvent(self, event):
        if self._hasOverrideCursor:                            # 먼저 — 아래 finishDrag 가 시그널을 내므로
            QtWidgets.QApplication.restoreOverrideCursor()
            self._hasOverrideCursor = False
        if self._dragMode == "line":
            self.field.finishDrag()
        self._dragMode = None
        self.field.graph._isFollowing = False
        self.field.graph.setViewWindow(None)
        super().hideEvent(event)

    def _setWindow(self, start: float, end: float, upperLimit: Optional[float] = None) -> None:
        """보는 구간을 바꾼다(폭은 유지하고 범위 안으로 민다). upperLimit = 위로 끝이 없는 모델에서 범위 끝 너머로 허용할 끝. 바 그래프 범위는 늘리지 않는다(축이 흔들린다)."""
        low, high = self.field.valueRange
        minimumSpan = (high - low) * MAGNIFIER_MIN_SPAN
        if self.field.graph.isOpenEnded and upperLimit is not None:
            high = max(high, upperLimit)
        span = min(max(end - start, minimumSpan), high - low)
        start = min(max(start, low), high - span)
        self.window_ = (start, start + span)
        self.curve = densityCurve(self.field.sortedScores, self.window_, MAGNIFIER_BINS, clipToRange=False, isSorted=True)
        self.field.graph.setViewWindow(self.window_)
        self.update()

    def refresh(self) -> None:
        """값, 분포가 바뀌었을 때 구간은 그대로 다시 그린다."""
        if self.isVisible():
            self._setWindow(*self.window_, upperLimit=self.window_[1])

    # ------------------------------------------------------------------ 그리기
    def plotRect(self) -> QtCore.QRectF:
        left, top, _, _ = MAGNIFIER_MARGINS
        return QtCore.QRectF(left, top, MAGNIFIER_PLOT_SIZE.width(), MAGNIFIER_PLOT_SIZE.height())

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = self.palette().color(QtGui.QPalette.WindowText)
        subColor = _withAlpha(color, 150)
        plot = self.plotRect()
        value = self.field.value
        lineX = valueToX(value, self.window_, plot)
        isInside = plot.left() <= lineX <= plot.right()
        paintCurve(painter, plot, self.curve if self.curve is not None else np.zeros(2), color, lineX)
        if isInside:
            paintLine(painter, lineX, plot.top() - 4, plot.bottom(), color, self._dragMode != "line")
        self._paintValueTag(painter, value, lineX, isInside, color)
        self._paintAxis(painter, plot, color, subColor)

    def _paintValueTag(self, painter, value: float, lineX: float, isInside: bool, color: QtGui.QColor) -> None:
        """선 위 값 표시. 선이 구간 밖이면 가장자리에 화살표 + 값. 화살표는 글꼴에 글자가 없어 직접 그린다."""
        plot = self.plotRect()
        text = self.field.formatValue(value)
        arrow = 0 if isInside else (-1 if lineX < plot.left() else 1)
        metrics = painter.fontMetrics()
        width = metrics.horizontalAdvance(text) + 10 + (TAG_ARROW_SPACE if arrow else 0)
        center = min(max(lineX, plot.left() + width / 2), plot.right() - width / 2)
        box = QtCore.QRectF(center - width / 2, 2, width, 16)
        painter.setPen(QtGui.QPen(_withAlpha(color, 128), 1))
        painter.setBrush(TAG_BACKGROUND)
        painter.drawRect(box)
        textBox = box.adjusted(TAG_ARROW_SPACE if arrow < 0 else 0, 0, -TAG_ARROW_SPACE if arrow > 0 else 0, 0)
        painter.setPen(color)
        painter.drawText(textBox, QtCore.Qt.AlignCenter, text)
        if arrow:
            tipX = box.left() + 4 if arrow < 0 else box.right() - 4
            baseX = tipX - arrow * 5
            painter.setBrush(color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(baseX, box.center().y() - 4),
                                                 QtCore.QPointF(tipX, box.center().y()),
                                                 QtCore.QPointF(baseX, box.center().y() + 4)]))

    def _paintAxis(self, painter, plot: QtCore.QRectF, color: QtGui.QColor, subColor: QtGui.QColor) -> None:
        """아래 축 + 눈금. 소수 자리는 구간 폭에 맞춘다."""
        start, end = self.window_
        painter.setPen(QtGui.QPen(_withAlpha(color, 77), 1))
        painter.drawLine(QtCore.QPointF(plot.left(), plot.bottom() + 1), QtCore.QPointF(plot.right(), plot.bottom() + 1))
        step = (end - start) / (MAGNIFIER_TICKS - 1)
        decimals = max(self.field.decimals, int(math.ceil(-math.log10(step))) if 0 < step < 1 else 0)
        for index in range(MAGNIFIER_TICKS):
            tickValue = start + step * index
            x = plot.left() + plot.width() * index / (MAGNIFIER_TICKS - 1)
            isEnd = index in (0, MAGNIFIER_TICKS - 1)
            painter.setPen(QtGui.QPen(color if isEnd else subColor, 1))
            painter.drawLine(QtCore.QPointF(x, plot.bottom() + 1), QtCore.QPointF(x, plot.bottom() + 5))
            align = QtCore.Qt.AlignLeft if index == 0 else QtCore.Qt.AlignRight if isEnd else QtCore.Qt.AlignHCenter
            box = QtCore.QRectF(x - (0 if index == 0 else 60 if isEnd else 30), plot.bottom() + 5, 60, 13)
            painter.drawText(box, align | QtCore.Qt.AlignVCenter, ("%." + str(decimals) + "f") % tickValue)

    # ------------------------------------------------------------------ 조작
    def _isOnLineOrMarker(self, x: float) -> bool:
        plot = self.plotRect()
        lineX = valueToX(self.field.value, self.window_, plot)
        if plot.left() <= lineX <= plot.right():
            return abs(x - lineX) <= GRAB_DISTANCE
        return x <= plot.left() + GRAB_DISTANCE * 4 if lineX < plot.left() else x >= plot.right() - GRAB_DISTANCE * 4

    def mousePressEvent(self, event):
        if not self.rect().contains(event.pos()):
            super().mousePressEvent(event)                     # 판 밖 → Qt.Popup 이 닫는다
            return
        if event.button() != QtCore.Qt.LeftButton or self.field.isLocked:
            return
        if self._isOnLineOrMarker(event.x()):
            self._dragMode = "line"  # 클릭만으로는 값이 안 바뀐다
            self._lineDragWindow = self.window_
        else:
            self._dragMode = "pan"
            self._panAnchor = (event.x(), self.window_)
        self.update()

    def mouseMoveEvent(self, event):
        if self._dragMode == "follow":
            # 팝업이 마우스를 잡아 바 그래프 대신 여기로 온다
            graph = self.field.graph
            x = graph.mapFromGlobal(event.globalPos()).x()
            self.followTo(xToValue(x, self.field.valueRange, graph.plotRect()))
            self._setCursorShape(QtCore.Qt.ClosedHandCursor)
            return
        if self._dragMode == "line":
            # 값은 잡은 순간의 구간 기준으로 바꾼다(따라 움직인 구간 기준이면 마우스를 멈춰도 계속 커진다). 선이 구간 밖으로 나가면 구간이 따라간다
            start, end = self._lineDragWindow
            plot = self.plotRect()
            self.field.dragTo(start + (end - start) * (event.x() - plot.left()) / plot.width())
            self._keepLineInWindow()
            self._setCursorShape(QtCore.Qt.SizeHorCursor)
        elif self._dragMode == "pan":
            anchorX, (start, end) = self._panAnchor
            shift = (anchorX - event.x()) / self.plotRect().width() * (end - start)
            self._setWindow(start + shift, end + shift, upperLimit=end)
            self._setCursorShape(QtCore.Qt.ClosedHandCursor)
        else:
            self._updateCursor(event.pos())

    def mouseReleaseEvent(self, event):
        if self._dragMode == "line":
            self.field.finishDrag()
        self._dragMode = None
        self._updateCursor(event.pos())
        self.update()

    def _keepLineInWindow(self) -> None:
        """끄는 선이 구간 밖으로 나가면 구간을 선까지 민다(폭 그대로)."""
        start, end = self.window_
        value = self.field.value
        if value > end:
            self._setWindow(value - (end - start), value, upperLimit=math.inf)
        elif value < start:
            self._setWindow(value, value + (end - start), upperLimit=math.inf)

    def _updateCursor(self, position: QtCore.QPoint) -> None:
        """판 위에서만 ↔(손잡이), 손바닥(빈 곳), 판 밖(이미지 위)이면 화살표."""
        if not self.rect().contains(position):
            self._setCursorShape(QtCore.Qt.ArrowCursor)
        elif self._isOnLineOrMarker(position.x()):
            self._setCursorShape(QtCore.Qt.SizeHorCursor)
        else:
            self._setCursorShape(QtCore.Qt.OpenHandCursor)

    def _setCursorShape(self, shape: QtCore.Qt.CursorShape) -> None:
        """앱 전체 커서를 바꾼다(showEvent). 닫혀 있으면 아무것도 안 한다."""
        if self._hasOverrideCursor:
            QtWidgets.QApplication.changeOverrideCursor(QtGui.QCursor(shape))

    def wheelEvent(self, event):
        """휠 = 배율, 마우스 자리의 값이 중심. 팝업이라 마우스가 판 밖(바 그래프 위)이어도 휠이 오므로 그때는 바 그래프 기준으로 한다."""
        delta = event.angleDelta().y()
        if delta:
            start, end = self.window_
            if self.rect().contains(event.pos()):
                anchor = xToValue(event.x(), self.window_, self.plotRect())
            else:
                graph = self.field.graph
                anchor = xToValue(graph.mapFromGlobal(event.globalPos()).x(), self.field.valueRange, graph.plotRect())
            factor = 1 / MAGNIFIER_ZOOM_STEP if delta > 0 else MAGNIFIER_ZOOM_STEP
            self._setWindow(anchor - (anchor - start) * factor, anchor + (end - anchor) * factor, upperLimit=math.inf)
        event.accept()


class ThresholdField(QtWidgets.QWidget):
    """임계값 칸 전체. 입력은 setter 들, 출력은 시그널 4개."""
    valueChanging = QtCore.pyqtSignal(float)
    valueCommitted = QtCore.pyqtSignal(float)
    valueReverted = QtCore.pyqtSignal(float)
    autoToggled = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("autoLabelThresholdField")
        self.baseRange: Tuple[float, float] = (0.0, 100.0)
        self.valueRange: Tuple[float, float] = (0.0, 100.0)
        self.scores: Optional[np.ndarray] = None
        self.sortedScores: Optional[np.ndarray] = None
        self.curve: Optional[np.ndarray] = None
        self.value = 0.0
        self.decimals = 0
        self.stepFactor: Optional[float] = None  # None = 더하기, 값 = 곱셈 단위(모델)
        self.stepSize: Optional[float] = None
        self.isLocked = False
        self._inputWidth = 0
        self._reserveValue = 0.0
        self._isDragDirty = False
        self._inputTip = ""
        self._committedValue = 0.0  # 마지막으로 확정했거나 바깥에서 정한 값 — 되돌릴 자리

        self.graph = ThresholdGraph(self)
        self.magnifier = ThresholdMagnifier(self)
        self.lowLabel = QtWidgets.QLabel(self)
        self.highLabel = QtWidgets.QLabel(self)
        for label in (self.lowLabel, self.highLabel):
            label.setObjectName("autoLabelThresholdEnd")
        self.minusButton = QtWidgets.QPushButton("−", self)
        self.plusButton = QtWidgets.QPushButton("+", self)
        for button in (self.minusButton, self.plusButton):
            button.setObjectName("autoLabelThresholdStep")
            button.setFixedSize(STEP_BUTTON_SIZE)
            button.setAutoRepeat(True)
            button.setCursor(QtCore.Qt.PointingHandCursor)
        self.valueInput = QtWidgets.QLineEdit(self)
        self.valueInput.setFixedWidth(VALUE_INPUT_MIN_WIDTH)
        self.valueInput.setObjectName("autoLabelThresholdInput")
        self.valueInput.setFixedHeight(VALUE_INPUT_HEIGHT)
        self.valueInput.setAlignment(QtCore.Qt.AlignCenter)
        self.valueInput.setValidator(ValueInputValidator(self.valueInput))
        self.autoButton = Switch(self)
        self.autoLabel = QtWidgets.QLabel(self)                 # AnimatedToggle 은 글자를 그리지 않는다

        ends = QtWidgets.QHBoxLayout()
        ends.setContentsMargins(GRAPH_MARGIN, 0, GRAPH_MARGIN, 0)
        ends.addWidget(self.lowLabel)
        ends.addStretch(1)
        ends.addWidget(self.highLabel)
        column = QtWidgets.QVBoxLayout()
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(1)
        column.addWidget(self.graph)
        column.addLayout(ends)
        stepper = QtWidgets.QHBoxLayout()
        stepper.setContentsMargins(0, 0, 0, 0)
        stepper.setSpacing(0)
        for widget in (self.minusButton, self.valueInput, self.plusButton):
            stepper.addWidget(widget, 0, QtCore.Qt.AlignVCenter)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addLayout(column)
        row.addLayout(stepper)
        auto = QtWidgets.QHBoxLayout()
        auto.setSpacing(AUTO_LABEL_SPACING)
        auto.addWidget(self.autoButton, 0, QtCore.Qt.AlignVCenter)
        auto.addWidget(self.autoLabel, 0, QtCore.Qt.AlignVCenter)
        row.addLayout(auto)

        self._stepCommitTimer = QtCore.QTimer(self)
        self._stepCommitTimer.setSingleShot(True)
        self._stepCommitTimer.setInterval(STEP_COMMIT_DELAY_MS)
        self._stepCommitTimer.timeout.connect(self._commit)
        self.graph.lineDragged.connect(self.dragTo)
        self.graph.lineReleased.connect(self.finishDrag)
        self.graph.stepped.connect(self.step)
        self.graph.magnifyRequested.connect(lambda value: self.magnifier.openAround(value, isFollowing=True))
        self.graph.magnifyMoved.connect(self.magnifier.followTo)
        self.minusButton.clicked.connect(lambda: self.step(-1))
        self.plusButton.clicked.connect(lambda: self.step(1))
        self.valueInput.editingFinished.connect(self._onValueTyped)
        self.valueInput.textChanged.connect(self._fitInputWidth)
        self.autoButton.toggled.connect(self.autoToggled.emit)

    # ------------------------------------------------------------------ 바깥에서 넣는 값
    def setScale(self, baseRange: Tuple[float, float], scores: Optional[np.ndarray], decimals: int,
                 stepFactor: Optional[float] = None, stepSize: Optional[float] = None) -> None:
        """기본 범위, 분포 점수(없으면 None), 숫자 칸 소수 자리, 한 칸 크기를 넣는다. stepFactor 를 주면 모델 모드(위로 끝 없음), 없으면 유사도 모드(baseRange 끝이 최댓값). 확정을 기다리던 한 칸이 있으면 취소한다(valueReverted). value 는 그대로 둔다."""
        self._cancelPendingStep()
        self.baseRange, self.scores, self.decimals, self.stepFactor = baseRange, scores, decimals, stepFactor
        self.stepSize = stepSize
        pattern = VALUE_INPUT_DECIMAL_PATTERN % decimals if decimals > 0 else VALUE_INPUT_INTEGER_PATTERN
        self.valueInput.validator().setRegularExpression(QtCore.QRegularExpression(pattern))
        self.valueInput.validator().maximum = baseRange[1] if stepFactor is None else None
        self.sortedScores = sortedFinite(scores)
        self.graph.isOpenEnded = stepFactor is not None
        self._inputWidth = 0
        self._reserveValue = max(baseRange[1], self.value) * INPUT_RESERVE_FACTOR
        self._refreshRange()
        self._fitInputWidth(self.valueInput.text())

    def setValue(self, value: float) -> None:
        """값을 바꾼다(확정 시그널은 내지 않는다). 확정을 기다리던 한 칸이 있으면 취소만 valueReverted 로 알린다."""
        self._cancelPendingStep()
        self.value = self._committedValue = float(value)
        self._refreshRange()
        self.valueInput.setText(self.formatValue(self.value))

    def setLocked(self, isLocked: bool, reasonText: str = "") -> None:
        """잠그면 그래프, − +, 숫자만 흐려진다. [자동] 은 그대로."""
        self.isLocked = isLocked
        if isLocked:
            self._cancelPendingStep()
            if self._isDragDirty:
                # 끄던 값은 버리고 확정한 값으로 되돌려 알린다(안 알리면 미리보기가 남는다)
                self.value = self._committedValue
                self.valueReverted.emit(self.value)
            self._isDragDirty = False
            self.graph.cancelDrag()
        for widget in (self.valueInput, self.minusButton, self.plusButton):
            widget.setEnabled(not isLocked)
        self.graph.setToolTip(wrapTip(reasonText) if isLocked else "")
        self.valueInput.setToolTip(wrapTip(reasonText) if isLocked else self._inputTip)
        if isLocked:
            self.magnifier.hide()
        self._refreshView()

    def setAutoVisible(self, isVisible: bool, isChecked: bool, text: str) -> None:
        for widget in (self.autoButton, self.autoLabel):
            widget.setVisible(isVisible)
        self.autoLabel.setText(text)
        self.autoButton.setCheckedQuietly(isChecked)

    def setTexts(self, minusTip: str, plusTip: str, inputTip: str) -> None:
        """언어가 바뀔 때 − + 툴팁, 숫자 칸의 범위 설명을 넣는다. 잠겨 있으면 잠긴 이유가 먼저 보인다."""
        self.minusButton.setToolTip(wrapTip(minusTip))
        self.plusButton.setToolTip(wrapTip(plusTip))
        self._inputTip = wrapTip(inputTip)
        if not self.isLocked:
            self.valueInput.setToolTip(self._inputTip)

    def formatValue(self, value: float) -> str:
        return ("%." + str(self.decimals) + "f") % value

    # ------------------------------------------------------------------ 사용자가 바꾸는 값
    def dragTo(self, value: float) -> None:
        """선을 끄는 중(바 그래프, 돋보기 공통) — 미리보기만. 끄는 동안 범위는 안 바꾼다."""
        if self.isLocked:
            return
        self._stepCommitTimer.stop()  # 끌기가 이어받는다 — 확정은 놓을 때
        low, high = self.valueRange
        value = max(round(float(value), self.decimals), low)  # 숫자 칸에 보이는 자릿수로 반올림
        if not self.graph.isOpenEnded:
            value = min(value, high)
        if value == self.value:
            return
        self._isDragDirty = True
        self.value = value
        self._refreshView()
        self.valueChanging.emit(self.value)

    def finishDrag(self) -> None:
        """끌기를 놓음 — 값이 정해졌을 때만 한 번 확정한다(잠겼으면 버린다)."""
        isDirty, self._isDragDirty = self._isDragDirty, False
        self._refreshRange()  # 끝 너머로 끌었으면(모델) 범위가 늘어난다
        if isDirty and not self.isLocked and self.value != self._committedValue:  # 제자리면 확정하지 않는다
            self._commit()
        elif isDirty:
            self.valueReverted.emit(self.value)

    def _commit(self) -> None:
        self._committedValue = self.value
        self.valueCommitted.emit(self.value)

    def _cancelPendingStep(self) -> None:
        """확정을 기다리던 휠, ± 한 칸을 취소하고 확정한 값으로 돌려 알린다(안 알리면 컨트롤러에 미리보기가 남는다)."""
        if self._stepCommitTimer.isActive():
            self._stepCommitTimer.stop()
            self.value = self._committedValue
            self.valueReverted.emit(self.value)

    def step(self, direction: int) -> None:
        """한 칸 이동. 멈춘 뒤 한 번만 확정한다. 아래는 baseRange 시작에서, 위는 유사도만 baseRange 끝에서 멈춘다."""
        if self.isLocked:
            return
        unit = 10 ** -self.decimals
        if self.stepFactor is None:
            value = self.value + direction * (self.stepSize or unit)
        else:
            value = self.value * (self.stepFactor if direction > 0 else 1 / self.stepFactor)
            if abs(value - self.value) < unit:                     # 0 근처에서 곱셈이 멈추지 않게
                value = self.value + direction * unit
        value = max(self.baseRange[0], round(value, self.decimals))
        if self.stepFactor is None and direction > 0 and self.value <= self.baseRange[1]:
            value = min(value, self.baseRange[1])
        if value == self.value:
            return
        self.value = value
        self._refreshRange()
        self.valueChanging.emit(self.value)
        self._stepCommitTimer.start()

    # ------------------------------------------------------------------ 안쪽
    def _refreshRange(self) -> None:
        """그래프 범위 = 기본 범위를 값(선)까지 늘린 것."""
        self.valueRange = rangeIncluding(self.baseRange, self.value)
        self.curve = densityCurve(self.sortedScores, self.valueRange, isSorted=True)
        self._refreshView()
        self.magnifier.refresh()

    def _refreshView(self) -> None:
        low, high = self.valueRange
        self.graph.setState(self.curve, self.valueRange, self.value, self.isLocked)
        if self.curve is None:
            self.magnifier.hide()
        self.magnifier.update()
        # 양 끝 숫자는 분포가 있고 유사도일 때만
        showEnds = self.curve is not None and not self.graph.isOpenEnded
        self.lowLabel.setText(_formatEnd(low) if showEnds else "")
        self.highLabel.setText(_formatEnd(high) if showEnds else "")
        if not self.valueInput.hasFocus():
            self.valueInput.setText(self.formatValue(self.value))

    def _fitInputWidth(self, text: str) -> None:
        """숫자 칸 폭. 척도마다 범위 끝 자릿수에 맞춰 한 번 잡고, 그보다 긴 값일 때만 넓힌다(값마다 맞추면 바가 계속 재배치된다)."""
        metrics = self.valueInput.fontMetrics()
        reserve = self.formatValue(self._reserveValue)
        width = max(VALUE_INPUT_MIN_WIDTH, metrics.horizontalAdvance(reserve) + VALUE_INPUT_PADDING * 2,
                    metrics.horizontalAdvance(text or "0") + VALUE_INPUT_PADDING * 2)
        if width > self._inputWidth:
            self._inputWidth = width
            self.valueInput.setFixedWidth(width)

    def _onValueTyped(self) -> None:
        try:
            typed = float(self.valueInput.text())
        except ValueError:
            self.valueInput.setText(self.formatValue(self.value))
            return
        low, high = self.baseRange
        typed = max(typed, low) if self.graph.isOpenEnded else min(max(typed, low), high)
        if abs(typed - self.value) < 10 ** -(self.decimals + 1):
            self.valueInput.setText(self.formatValue(self.value))
            return
        self._stepCommitTimer.stop()
        self.value = typed
        self.valueInput.clearFocus()
        self._refreshRange()
        self._commit()
