"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    오토라벨링 바 — 디스플레이 아래쪽에 떠 있는 한 줄(좁으면 묶음 단위로 두 줄).

    왼쪽 → 오른쪽: 그립, 유사도, 모델 탭, 임계값 칸 ┃ 학습 조건(배경, 원물, 이물) ┃ 모델 학습, 추론, 일괄 추론 ┃ ‹ › 설정
    창이 좁아 한 줄이 이미지 영역보다 넓어지면 fitWidth 가 줄을 나눈다. 최대화에서는 늘 한 줄(넘치면 오른쪽이 잘린다).
    fitWidth 를 부르는 쪽은 컨트롤러(_placeBar)다.

    화면만 맡는다 — 무엇이 켜지는지는 barState.evaluateBar 가 정하고 컨트롤러가 render 로 넣는다. 사용자 조작은 시그널로 내보낸다.

    꺼진 버튼은 setEnabled(False) 대신 'locked' 모양으로 둔다(LockableButton): 비활성 위젯은 툴팁이 안 뜰 수 있어서다.
"""

from typing import Callable, Optional, Sequence

from PyQt5 import QtCore, QtGui, QtWidgets

from autolabel.barState import TAB_MODEL, TAB_SIMILARITY, BarView, Control
from autolabel.thresholdField import ThresholdField, wrapTip
from notification.notificationUi import loadIcon


BAR_HEIGHT = 48
BAR_SPACING = 12
CONDITION_SPACING = 14
SEPARATOR_HEIGHT = 28
BAR_MARGINS = (4, 0, 10, 0)
CONDITION_WIDTH = 400  # 기본 폭. 글자에 맞춰 넓어진다(줄이지는 않는다)
BAR_EXTRA_ROW_HEIGHT = 40
CONDITION_NAME_GAP = 6
ICON_BUTTON_SIZE = QtCore.QSize(26, 26)
ICON_SIZE = QtCore.QSize(16, 16)
GRIP_ICON_PIXELS = 18
GRIP_SIZE = QtCore.QSize(GRIP_ICON_PIXELS, 32)
ICON_FOLDER = "ico/labeling/autolabel/"
LOCKED_PROPERTY = "locked"
JOB_BAR_SIZE = QtCore.QSize(56, 4)
JOB_BAR_FRAME_MS = 16
JOB_BAR_FOLLOW = 0.12
JOB_BAR_SETTLE = 0.0005


class LockableButton(QtWidgets.QPushButton):
    """잠글 수 있는 버튼 — 잠기면 흐리게 그리고 클릭을 무시하지만 툴팁은 뜬다."""
    activated = QtCore.pyqtSignal()

    def __init__(self, objectName: str, parent=None):
        super().__init__(parent)
        self.setObjectName(objectName)
        self.setProperty(LOCKED_PROPERTY, False)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.clicked.connect(self._onClicked)

    def setControl(self, control: Control, reasonText: str) -> None:
        """control → 모양과 툴팁. 모양이 바뀌면 스타일을 다시 입힌다(동적 속성은 polish 가 필요)."""
        isLocked = not control.enabled
        if self.property(LOCKED_PROPERTY) != isLocked:
            self.setProperty(LOCKED_PROPERTY, isLocked)
            self.style().unpolish(self)
            self.style().polish(self)
        self.setToolTip(wrapTip(reasonText) if isLocked else "")
        self.setCursor(QtCore.Qt.ArrowCursor if isLocked else QtCore.Qt.PointingHandCursor)

    def isLocked(self) -> bool:
        return bool(self.property(LOCKED_PROPERTY))

    def _onClicked(self) -> None:
        if not self.isLocked():
            self.activated.emit()


class ConditionSegment(QtWidgets.QWidget):
    """학습 조건 한 칸: 이름, 현재/최소 수, 채운 비율 막대, 이 이미지 몫 문구.

    수와 막대는 학습에 쓰는 전체 합이고, 채우면 흐려진다. 합에 넣을 이미지는 컨트롤러가 정한다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("autoLabelConditionSegment")
        self.nameLabel = QtWidgets.QLabel(self)
        self.nameLabel.setObjectName("autoLabelConditionName")
        self.countLabel = QtWidgets.QLabel(self)
        self.countLabel.setObjectName("autoLabelConditionCount")
        self.bar = QtWidgets.QProgressBar(self)
        self.bar.setObjectName("autoLabelConditionBar")
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(3)
        self.bar.setRange(0, 1000)
        self.imageLabel = QtWidgets.QLabel(self)
        self.imageLabel.setObjectName("autoLabelConditionImage")
        top = QtWidgets.QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(CONDITION_NAME_GAP)
        top.addWidget(self.nameLabel)
        top.addStretch(1)
        top.addWidget(self.countLabel)
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(3)
        column.addLayout(top)
        column.addWidget(self.bar)
        column.addWidget(self.imageLabel)

    def setValues(self, name: str, count: int, minimum: int, imageText: str = "") -> None:
        """imageText = 지금 이미지 몫 문구(없으면 빈 문자열 — 자리는 유지해 높이가 흔들리지 않게)."""
        self.nameLabel.setText(name)
        self.imageLabel.setText(imageText)
        self.countLabel.setText("%s/%s" % (format(count, ","), format(minimum, ",")))
        self.bar.setValue(int(min(1.0, count / minimum if minimum else 1.0) * 1000))
        # 글자가 다 보이는 폭을 직접 잰다(setText 직후 레이아웃 캐시는 옛 값)
        self.setMinimumWidth(max(self.nameLabel.sizeHint().width() + CONDITION_NAME_GAP + self.countLabel.sizeHint().width(),
                                 self.imageLabel.sizeHint().width()))
        isMet = count >= minimum
        if self.property("met") != isMet:
            self.setProperty("met", isMet)
            for widget in (self, self.nameLabel, self.countLabel, self.bar, self.imageLabel):
                widget.style().unpolish(widget)
                widget.style().polish(widget)


class ConditionBox(QtWidgets.QWidget):
    """학습 조건 세 칸을 담는 자리. 폭은 글자가 다 보이는 만큼 CONDITION_WIDTH 이상."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def sizeHint(self):
        hint = super().sizeHint()
        return QtCore.QSize(max(CONDITION_WIDTH, hint.width()), hint.height())


class SmoothProgressBar(QtWidgets.QWidget):
    """얇은 진행 막대 — 채운 폭을 소수 픽셀까지 그리고 목표 값을 부드럽게 따라간다(QProgressBar 는 정수 픽셀로 끊긴다).
    색은 스타일시트(background, color)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self._target = 0.0
        self._shown = 0.0
        self._frameTimer = QtCore.QTimer(self)
        self._frameTimer.setInterval(JOB_BAR_FRAME_MS)
        self._frameTimer.timeout.connect(self._followTarget)

    def progress(self) -> float:
        """지금 그려진 진행(0~1)."""
        return self._shown

    def setProgress(self, fraction: float, isAnimated: bool = True) -> None:
        """목표 진행(0~1). 앞으로 갈 때만 애니메이션, 새 작업 시작이나 끝은 바로."""
        self._target = min(max(fraction, 0.0), 1.0)
        if not isAnimated or self._target <= self._shown:
            self._shown = self._target
            self._frameTimer.stop()
            self.update()
        elif not self._frameTimer.isActive():
            self._frameTimer.start()

    def _followTarget(self) -> None:
        self._shown += (self._target - self._shown) * JOB_BAR_FOLLOW
        if self._target - self._shown < JOB_BAR_SETTLE:
            self._shown = self._target
            self._frameTimer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(QtWidgets.QStyle.PE_Widget, option, painter, self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(QtCore.QRectF(0, 0, self.width() * self._shown, self.height()),
                         self.palette().color(QtGui.QPalette.WindowText))


class JobSlot(QtWidgets.QStackedWidget):
    """평소엔 버튼, 작업 중엔 진행 표시와 취소로 바뀌는 자리."""

    def __init__(self, button: LockableButton, parent=None):
        super().__init__(parent)
        self.button = button
        progress = QtWidgets.QWidget(self)
        self.progressPage = progress
        self.progressLabel = QtWidgets.QLabel(progress)
        self.progressLabel.setObjectName("autoLabelProgressLabel")
        self.progressBar = SmoothProgressBar(progress)
        self.progressBar.setObjectName("autoLabelJobBar")
        self.progressBar.setFixedSize(JOB_BAR_SIZE)
        self.progressLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.cancelButton = QtWidgets.QPushButton(progress)
        self.cancelButton.setObjectName("autoLabelCancelButton")
        self.cancelButton.setCursor(QtCore.Qt.PointingHandCursor)
        row = QtWidgets.QHBoxLayout(progress)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.progressBar, 0, QtCore.Qt.AlignVCenter)
        row.addWidget(self.progressLabel)
        row.addWidget(self.cancelButton)
        self.addWidget(button)
        self.addWidget(progress)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def showProgress(self, isRunning: bool, done: float = 0, total: int = 0) -> None:
        """작업 중이면 진행 표시, 아니면 원래 버튼. done 은 소수여도 된다(숫자는 정수 부분만)."""
        self.setCurrentIndex(1 if isRunning else 0)
        self.progressLabel.setText("%d / %d" % (int(done), total))
        # 자릿수가 늘 때마다 폭이 흔들리지 않게 전체 수의 자릿수로 폭을 고정한다
        digits = "8" * len(str(total))
        self.progressLabel.setFixedWidth(self.progressLabel.fontMetrics().horizontalAdvance("%s / %s" % (digits, digits)))
        self.progressBar.setProgress(done / total if total else 0.0, isAnimated=isRunning)
        self.updateGeometry()

    def setRemainingText(self, text: str) -> None:
        """남은 시간 — 진행 표시에 올리면 보이는 툴팁(바에 글로 넣으면 폭이 늘어난다)."""
        for widget in (self.progressPage, self.progressBar, self.progressLabel):
            widget.setToolTip(text)

    def sizeHint(self):
        return self.currentWidget().sizeHint()

    def minimumSizeHint(self):
        # 지금 보이는 페이지 폭만 — QStackedWidget 기본은 가장 넓은 페이지(진행 표시)라 학습 뒤에도 버튼 칸이 넓게 남는다
        return self.currentWidget().minimumSizeHint()


def noKeyboardFocus(root: QtWidgets.QWidget) -> None:
    """root 안의 버튼이 클릭으로 포커스를 받지 않게 한다(점선 테두리가 남는다)."""
    for button in root.findChildren(QtWidgets.QAbstractButton):
        button.setFocusPolicy(QtCore.Qt.NoFocus)


def separatorLine(parent) -> QtWidgets.QFrame:
    """묶음 사이 세로 구분선(색은 스타일시트)."""
    line = QtWidgets.QFrame(parent)
    line.setObjectName("autoLabelSeparator")
    line.setFixedSize(1, SEPARATOR_HEIGHT)
    return line


def iconButton(name: str, objectName: str, parent) -> QtWidgets.QPushButton:
    button = QtWidgets.QPushButton(parent)
    button.setObjectName(objectName)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(ICON_FOLDER + name + "_white.png"), QtGui.QIcon.Normal)
    icon.addPixmap(QtGui.QPixmap(ICON_FOLDER + name + "_disabled.png"), QtGui.QIcon.Disabled)
    button.setIcon(icon)
    button.setIconSize(ICON_SIZE)
    button.setFixedSize(ICON_BUTTON_SIZE)
    button.setCursor(QtCore.Qt.PointingHandCursor)
    return button


class GripHandle(QtWidgets.QLabel):
    """끌어서 바를 옮기는 손잡이. 끄는 만큼의 이동을 dragged(dx, dy) 로 알린다."""
    dragged = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("autoLabelGrip")
        self.setFixedSize(GRIP_SIZE)
        self.setPixmap(loadIcon(ICON_FOLDER + "grip_white.png", GRIP_ICON_PIXELS, self.devicePixelRatioF()))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setCursor(QtCore.Qt.SizeAllCursor)
        self._lastPosition = None

    def mousePressEvent(self, event):
        self._lastPosition = event.globalPos()

    def mouseMoveEvent(self, event):
        if self._lastPosition is not None:
            delta = event.globalPos() - self._lastPosition
            self._lastPosition = event.globalPos()
            self.dragged.emit(delta.x(), delta.y())

    def mouseReleaseEvent(self, event):
        self._lastPosition = None


class AutoLabelBar(QtWidgets.QFrame):
    """바 전체. 사용자 조작은 시그널로 낸다(임계값은 self.threshold 의 시그널을 그대로 쓴다).

    잠긴 버튼은 눌러도 시그널을 내지 않는다(LockableButton). refitted 는 크기가 바뀌었으니
    컨트롤러가 자리를 다시 잡으라는 알림이다."""
    tabSelected = QtCore.pyqtSignal(str)
    trainClicked = QtCore.pyqtSignal()
    trainCancelClicked = QtCore.pyqtSignal()
    inferClicked = QtCore.pyqtSignal()
    batchClicked = QtCore.pyqtSignal()
    batchCancelClicked = QtCore.pyqtSignal()
    previousImageClicked = QtCore.pyqtSignal()
    nextImageClicked = QtCore.pyqtSignal()
    settingsToggled = QtCore.pyqtSignal(bool)
    refitted = QtCore.pyqtSignal()

    def __init__(self, textFunction: Callable[[str], str], parent=None):
        super().__init__(parent)
        self.setObjectName("autoLabelBar")
        self.setFixedHeight(BAR_HEIGHT)
        self.text = textFunction

        self.grip = GripHandle(self)
        self.similarityTab = QtWidgets.QPushButton(self)
        self.similarityTab.setObjectName("autoLabelTab")
        self.similarityTab.setCursor(QtCore.Qt.PointingHandCursor)
        self.modelTab = LockableButton("autoLabelTab", self)
        for tab in (self.similarityTab, self.modelTab):
            tab.setCheckable(True)
        self.similarityTab.setChecked(True)
        self.threshold = ThresholdField(self)
        self.conditions = [ConditionSegment(self) for _ in range(3)]
        self.conditionBox = conditionBox = ConditionBox(self)
        conditionRow = QtWidgets.QHBoxLayout(conditionBox)
        conditionRow.setContentsMargins(0, 0, 0, 0)
        conditionRow.setSpacing(CONDITION_SPACING)
        for segment in self.conditions:
            conditionRow.addWidget(segment, 1)
        self.trainButton = LockableButton("autoLabelActionButton", self)
        self.trainSlot = JobSlot(self.trainButton, self)
        self.inferButton = LockableButton("autoLabelActionButton", self)
        self.batchButton = LockableButton("autoLabelActionButton", self)
        self.batchSlot = JobSlot(self.batchButton, self)
        self.previousButton = iconButton("chevron_left", "autoLabelIconButton", self)
        self.nextButton = iconButton("chevron_right", "autoLabelIconButton", self)
        self.settingsButton = iconButton("settings", "autoLabelIconButton", self)
        self.settingsButton.setCheckable(True)

        # 묶음 넷 — 좁으면 묶음 단위로 줄을 나눈다(fitWidth)
        self.thresholdGroup = self._group((self.grip, self.similarityTab, self.modelTab, self.threshold))
        self.conditionGroup = self._group((conditionBox,))
        self.buttonGroup = self._group((self.trainSlot, self.inferButton, self.batchSlot))
        self.navGroup = self._group((self.previousButton, self.nextButton, self.settingsButton))
        self.groups = (self.thresholdGroup, self.conditionGroup, self.buttonGroup, self.navGroup)
        self.separators = [separatorLine(self) for _ in range(len(self.groups) - 1)]
        self._rows = QtWidgets.QVBoxLayout(self)
        self._rows.setContentsMargins(*BAR_MARGINS)
        self._rows.setSpacing(0)
        self._rowCount = 0
        self._fitArgs = None                                   # 마지막 fitWidth 인자 — 진행 표시가 바뀌면 같은 규칙으로 다시 맞춘다
        self._arrange(1)

        self.similarityTab.clicked.connect(lambda: self._selectTab(TAB_SIMILARITY))
        self.modelTab.activated.connect(lambda: self._selectTab(TAB_MODEL))
        self.modelTab.clicked.connect(lambda: self.modelTab.setChecked(self._activeTab == TAB_MODEL))
        self.trainButton.activated.connect(self.trainClicked.emit)
        self.trainSlot.cancelButton.clicked.connect(self.trainCancelClicked.emit)
        self.inferButton.activated.connect(self.inferClicked.emit)
        self.batchButton.activated.connect(self.batchClicked.emit)
        self.batchSlot.cancelButton.clicked.connect(self.batchCancelClicked.emit)
        self.previousButton.clicked.connect(self.previousImageClicked.emit)
        self.nextButton.clicked.connect(self.nextImageClicked.emit)
        self.settingsButton.toggled.connect(self.settingsToggled.emit)
        self.grip.dragged.connect(self._moveBy)
        self._activeTab = TAB_SIMILARITY
        noKeyboardFocus(self)
        # 사용자가 끌어 놓은 자리(없으면 None = 기본 자리). 창 크기, 설정 독 때문에 밀려도 기억했다가 공간이 생기면 돌아간다
        self.userPosition: Optional[QtCore.QPoint] = None

    def _group(self, widgets) -> QtWidgets.QWidget:
        """가로 한 묶음."""
        group = QtWidgets.QWidget(self)
        row = QtWidgets.QHBoxLayout(group)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(BAR_SPACING)
        for widget in widgets:
            widget.setParent(group)
            row.addWidget(widget, 0, QtCore.Qt.AlignVCenter)
        return group

    # ------------------------------------------------------------------ 줄 나누기
    def _groupWidths(self):
        """묶음 폭(글자, 진행 표시에 따라 바뀌므로 매번 잰다)."""
        return [group.sizeHint().width() for group in self.groups]

    def oneRowWidth(self) -> int:
        """한 줄일 때 폭."""
        left, _, right, _ = BAR_MARGINS
        lineCount = len(self.separators)
        return left + right + sum(self._groupWidths()) + lineCount + 2 * lineCount * BAR_SPACING

    def rowCountFor(self, availableWidth: int) -> int:
        """availableWidth 에 한 줄이 들어가면 1, 아니면 2."""
        return 1 if self.oneRowWidth() <= availableWidth else 2

    def rowCount(self) -> int:
        return self._rowCount

    def minimumFitWidth(self) -> int:
        """두 줄일 때의 폭 — 창 최소 폭의 기준(이보다 좁으면 겹친다)."""
        left, _, right, _ = BAR_MARGINS
        threshold, condition, buttons, nav = self._groupWidths()
        return left + right + max(threshold + 1 + buttons + 2 * BAR_SPACING, condition + nav + BAR_SPACING)

    def fitWidth(self, availableWidth: int, isOneRowOnly: bool = False) -> None:
        """이미지 영역 폭에 맞춰 줄을 나누고 크기를 맞춘다. isOneRowOnly(창 최대화)면 두 줄로 나누지 않는다."""
        self._fitArgs = (availableWidth, isOneRowOnly)
        # 글자를 막 바꾼 직후는 안쪽 레이아웃 요청이 대기 중이라 옛 폭으로 잰다 — 먼저 처리한다
        self._flushLayouts()
        rowCount = 1 if isOneRowOnly else self.rowCountFor(availableWidth)
        if rowCount != self._rowCount:
            self._arrange(rowCount)
        hint = self.sizeHint()  # adjustSize 는 남는 폭을 버튼 묶음의 빈칸으로 남길 수 있다
        if rowCount == 2:  # 가운데 맞춤 빈자리는 폭이 모자라면 줄어든다(_arrange)
            hint.setWidth(max(self.minimumFitWidth(), min(hint.width(), availableWidth)))
        self.resize(hint)

    def _flushLayouts(self) -> None:
        """대기 중인 레이아웃 요청을 안쪽부터 처리하고 크기 캐시를 비운다(바깥부터 하면 옛 폭으로 잰다). 바 안만 처리한다."""
        for widget in reversed([self] + self.findChildren(QtWidgets.QWidget)):
            QtWidgets.QApplication.sendPostedEvents(widget, QtCore.QEvent.LayoutRequest)
        self._invalidateLayouts()

    def _invalidateLayouts(self) -> None:
        """안쪽 위젯, 레이아웃의 크기 캐시를 비운다 — 글자를 바꾼 직후에는 옛 글자 폭을 기억하고 있다."""
        def invalidate(layout: QtWidgets.QLayout) -> None:
            for index in range(layout.count()):
                child = layout.itemAt(index).layout()
                if child is not None:
                    invalidate(child)
            layout.invalidate()

        for widget in reversed([self] + self.findChildren(QtWidgets.QWidget)):   # 안쪽부터
            if widget.layout() is not None:
                invalidate(widget.layout())

    def _arrange(self, rowCount: int) -> None:
        while self._rows.count():                                # 줄을 비운다(묶음 위젯은 바에 그대로 남는다)
            item = self._rows.takeAt(0)
            if item.layout() is not None:
                while item.layout().count():
                    item.layout().takeAt(0)
                item.layout().deleteLater()
        STRETCH = None
        NAV_MIRROR = "navMirror"                          # ‹ › ⚙ 와 같은 폭의 빈 자리 — 학습 조건을 줄 가운데에 두려고
        first, second, third = self.separators
        # 두 줄: 윗줄 = 임계값 ┃ 버튼, 아랫줄 = 조건(가운데) + ‹ › ⚙ — 양쪽 끝 폭이 같아야 가운데가 된다
        layout = {1: [[self.thresholdGroup, first, self.conditionGroup, second, self.buttonGroup, third, self.navGroup,
                       STRETCH]],
                  2: [[self.thresholdGroup, first, self.buttonGroup, STRETCH],
                      [NAV_MIRROR, STRETCH, self.conditionGroup, STRETCH, self.navGroup]]}[rowCount]
        for line in (second, third):
            line.setVisible(rowCount == 1)
        for items in layout:
            row = QtWidgets.QHBoxLayout()
            row.setSpacing(BAR_SPACING)
            for item in items:
                if item is STRETCH:
                    row.addStretch(1)
                elif item is NAV_MIRROR:
                    # 오른쪽 끝(‹ › ⚙ + 간격 + 여백)과 같은 폭. 자리가 모자라면 이 빈자리가 먼저 줄어든다(창 최소 폭이 늘지 않게)
                    mirrorWidth = self.navGroup.sizeHint().width() + BAR_SPACING + BAR_MARGINS[2] - BAR_MARGINS[0]
                    row.addSpacerItem(QtWidgets.QSpacerItem(mirrorWidth, 0, QtWidgets.QSizePolicy.Preferred,
                                                            QtWidgets.QSizePolicy.Minimum))
                else:
                    row.addWidget(item, 0, QtCore.Qt.AlignVCenter)
            self._rows.addLayout(row)
        self._rowCount = rowCount
        self.setFixedHeight(BAR_HEIGHT + (rowCount - 1) * BAR_EXTRA_ROW_HEIGHT)

    # ------------------------------------------------------------------ 탭
    def activeTab(self) -> str:
        return self._activeTab

    def _selectTab(self, tab: str) -> None:
        self._activeTab = tab
        self.similarityTab.setChecked(tab == TAB_SIMILARITY)
        self.modelTab.setChecked(tab == TAB_MODEL)
        self.tabSelected.emit(tab)

    def selectTab(self, tab: str) -> None:
        """바깥에서 탭을 바꿀 때. 사용자가 누른 것처럼 tabSelected 도 나간다. 잠금은 사용자 클릭만 막는다."""
        self._selectTab(tab)

    # ------------------------------------------------------------------ 그리기
    def render(self, view: BarView, reasonText: Callable[[Control], str], isRetrain: bool) -> None:
        """BarView → 버튼 모양. reasonText(control) 은 꺼진 이유 문구. isRetrain = 모델이 있음('재학습').
        이미지가 없으면 대부분 끄고 모델 탭은 infer 의 이유로 잠근다."""
        self.similarityTab.setText(self.text("tabSimilarity"))
        self.modelTab.setText(self.text("tabModel"))
        modelTab = view.modelTab if view.hasImage else view.infer
        self.modelTab.setControl(modelTab, reasonText(modelTab))
        for button in (self.similarityTab, self.previousButton, self.nextButton, self.settingsButton, self.threshold.autoButton):
            button.setEnabled(view.hasImage)
        self.trainButton.setText(self.text("retrain" if isRetrain else "train"))
        self.trainButton.setControl(view.train, reasonText(view.train))
        if view.train.enabled:
            self.trainButton.setToolTip(wrapTip(self.text("retrainTip" if isRetrain else "trainTip")))
        self.inferButton.setText(self.text("infer"))
        self.inferButton.setControl(view.infer, reasonText(view.infer))
        if view.infer.enabled:
            self.inferButton.setToolTip(wrapTip(self.text("inferTip")))
        self.batchButton.setText(self.text("batchInfer"))
        self.batchButton.setControl(view.batch, reasonText(view.batch))
        if view.batch.enabled:
            self.batchButton.setToolTip(wrapTip(self.text("batchTip")))
        for slot in (self.trainSlot, self.batchSlot):
            slot.cancelButton.setText(self.text("cancel"))
        self.previousButton.setToolTip(self.text("previousImage"))
        self.nextButton.setToolTip(self.text("nextImage"))
        self.settingsButton.setToolTip(self.text("settings"))

    def setConditions(self, items: Sequence) -> None:
        """items = [(이름, 전체 수, 최소 수, 이 이미지 문구)] × 3 — 배경, 원물, 이물 순. 숫자를 세는 규칙은 컨트롤러가 정한다."""
        for segment, item in zip(self.conditions, items):
            segment.setValues(*item)
        for widget in (self.conditions[0].parentWidget(), self.conditionGroup):  # 칸 폭이 바뀌었을 수 있다
            widget.updateGeometry()

    def setTrainingProgress(self, isRunning: bool, epoch: float = 0, total: int = 0) -> None:
        self.trainSlot.showProgress(isRunning, epoch, total)
        self._refit()

    def setTrainingRemaining(self, text: str) -> None:
        self.trainSlot.setRemainingText(text)

    def setBatchRemaining(self, text: str) -> None:
        self.batchSlot.setRemainingText(text)

    def setBatchProgress(self, isRunning: bool, done: int = 0, total: int = 0) -> None:
        self.batchSlot.showProgress(isRunning, done, total)
        self._refit()

    def _refit(self) -> None:
        """버튼 ↔ 진행 표시는 폭이 달라 fitWidth 규칙으로 바 폭을 다시 맞춘다(adjustSize 는 오른쪽이 잘렸다). 자리는 컨트롤러가(refitted)."""
        if self._fitArgs is None:
            self.adjustSize()
        else:
            self.fitWidth(*self._fitArgs)
        self.refitted.emit()

    # ------------------------------------------------------------------ 끌어서 옮기기
    def _moveBy(self, dx: int, dy: int) -> None:
        """부모 영역 밖으로 나가지 않게 옮긴다."""
        parent = self.parentWidget()
        if parent is None:
            return
        x = max(0, min(self.x() + dx, parent.width() - self.width()))
        y = max(0, min(self.y() + dy, parent.height() - self.height()))
        self.move(x, y)
        self.userPosition = QtCore.QPoint(x, y)
