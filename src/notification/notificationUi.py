"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    알림 화면 — 상태바의 종 버튼과 알림 목록, 토스트, 그리고 이를 메인 창에 붙이는 설치 함수.
    알림 규칙은 notificationCenter.py 에 있고, 여기서는 그 센터를 구독해서 그리기만 한다.

    - 종: 안 읽은 알림이 있으면 빨간 점이 붙고, 누르면 종 위로 알림 목록이 열린다. 목록은 읽기 전용이며
      열 때 안 읽은 알림이 읽음이 되지만 이번에 연 목록에는 안 읽음 점을 한 번 보여 준다.
    - 토스트: 그리기, 시간, 쌓기는 pyqttoast 라이브러리(conda_environment.yml 에 버전 고정)가 한다.
      showToast=True 인 새 알림만 띄우고, 앱 창이 앞에 없으면 미뤄 두었다가 앞으로 오면 띄운다.
      라이브러리의 위치, 개수 설정은 클래스 전체(static)에 걸리므로 ToastPresenter 는 앱에 하나만 둔다.
    - installNotificationUi: mid.py 가 한 줄로 부르는 설치 함수. 무엇을 어디에 붙일지는 여기서 정한다.

    위젯은 언어 모듈을 직접 모르고 textFunction(key) 으로 문구를 받는다(키는 언어 파일 main/notification 아래).
    아이콘은 ico/notification/ 의 PNG 이며 경로는 레포 루트 기준이다.
"""

import time

from PyQt5 import QtCore, QtGui, QtWidgets
from pyqttoast import Toast, ToastPosition
from pyqttoast.constants import DROP_SHADOW_SIZE

from notification.notificationCenter import (NOTIFICATION_INFO, NOTIFICATION_SUCCESS, EVENT_ADDED, EVENT_CLEARED,
                                             Notification, NotificationCenter, relativeTimeParts,
                                             getNotificationCenter)
from stylesheet.stylesheet_component import COLORS


ICON_FOLDER = "ico/notification"
BELL_ICON_PATH = ICON_FOLDER + "/bell.png"
BELL_UNREAD_ICON_PATH = ICON_FOLDER + "/bell_unread.png"
SUCCESS_ICON_PATH = ICON_FOLDER + "/notification_success.png"
FAILURE_ICON_PATH = ICON_FOLDER + "/notification_failure.png"
INFO_ICON_PATH = ICON_FOLDER + "/notification_info.png"
UNREAD_DOT_ICON_PATH = ICON_FOLDER + "/unread_dot.png"              # 목록 항목의 안 읽음 점


def kindIconPath(kind: str) -> str:
    """알림 종류 → 아이콘 파일. 모르는 종류는 실패 아이콘."""
    return {NOTIFICATION_SUCCESS: SUCCESS_ICON_PATH, NOTIFICATION_INFO: INFO_ICON_PATH}.get(kind, FAILURE_ICON_PATH)


def loadIcon(path: str, logicalSize: int, devicePixelRatio: float = 1.0) -> QtGui.QPixmap:
    """PNG 를 화면 배율에 맞춰 logicalSize 로 줄여 읽는다. 파일이 없으면 빈 QPixmap(아이콘 자리만 빈다)."""
    pixmap = QtGui.QPixmap(path)
    if pixmap.isNull():
        return pixmap
    physicalSize = int(round(logicalSize * devicePixelRatio))
    scaled = pixmap.scaled(physicalSize, physicalSize, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    scaled.setDevicePixelRatio(devicePixelRatio)
    return scaled


BELL_SIZE = QtCore.QSize(30, 24)
BELL_ICON_SIZE = 18
BELL_SIDE_MARGIN = 4
BELL_REOPEN_GUARD_SECONDS = 0.3  # 목록 안에서 종 위를 누른 직후의 종 누르기는 윈도가 다시 보낸 닫기 누르기로 본다
LIST_WIDTH = 280                # 제목이 길면 더 넓어진다
LIST_MAX_VISIBLE_ITEMS = 4              # 넘으면 목록만 스크롤
LIST_HEADER_MARGINS = (12, 8, 8, 8)      # 왼, 위, 오른, 아래
LIST_ITEM_MARGINS = (8, 8, 12, 8)
LIST_ITEM_SPACING = 8
LIST_TEXT_SPACING = 2
BREAKABLE_TOKEN_LENGTH = 20             # 띄어쓰기 없이 이보다 긴 덩어리는 아무 데서나 줄을 바꿀 수 있게 한다
ZERO_WIDTH_SPACE = "\u200b"             # QLabel 은 띄어쓰기에서만 줄을 바꿔서, 긴 경로가 목록 폭을 늘리지 않게 넣는다
LIST_EMPTY_MIN_HEIGHT = 56
LIST_ITEM_ICON_SIZE = 16
UNREAD_DOT_SIZE = 6
UNREAD_DOT_COLUMN = 12                   # 항목 왼쪽에서 점이 차지하는 폭
CLEAR_FADE_MS = 180

# textFunction 이 받는 키. 언어 파일 main → notification 아래의 이름과 같다.
TEXT_LIST_TITLE = "listTitle"
TEXT_CLEAR_ALL = "clearAll"
TEXT_EMPTY = "emptyList"
TEXT_JUST_NOW = "justNow"
TEXT_MINUTES_AGO = "minutesAgo"          # "{n}" 자리에 숫자가 들어간다
TEXT_HOURS_AGO = "hoursAgo"
TEXT_BELL_TOOLTIP = "bellTooltip"


def formatRelativeTime(createdAt: float, now: float, textFunction) -> str:
    """상대 시간 문구. 구간은 relativeTimeParts, 문구는 언어 파일이 정한다."""
    key, amount = relativeTimeParts(createdAt, now)
    return (textFunction(key) or "").replace("{n}", str(amount))


def fullBodyToolTip(body: str) -> str:
    """잘린 토스트에 올릴 전체 내용 툴팁(HTML). '<' '&' 를 해석하지 않고 줄바꿈되게 convertFromPlainText 로 감싼다."""
    return QtCore.Qt.convertFromPlainText(body, QtCore.Qt.WhiteSpaceNormal) if body else ""


def breakableText(text: str) -> str:
    """띄어쓰기 없는 긴 덩어리(파일 경로 등)의 글자 사이에 줄바꿈 자리를 넣는다. 보통 문장은 그대로."""
    return " ".join(ZERO_WIDTH_SPACE.join(word) if len(word) > BREAKABLE_TOKEN_LENGTH else word
                    for word in text.split(" "))


def plainLabel(text: str, objectName: str, parent: QtWidgets.QWidget) -> QtWidgets.QLabel:
    """알림 문구용 QLabel. 오류 문구의 '<' 등이 HTML 로 해석되지 않게 PlainText 로 고정한다."""
    label = QtWidgets.QLabel(text, parent)
    label.setObjectName(objectName)
    label.setTextFormat(QtCore.Qt.PlainText)
    return label


class BellButton(QtWidgets.QAbstractButton):
    """종 아이콘. checkable 버튼이라 목록이 열린 상태를 checked 로 표현한다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("notificationBellButton")
        self.setCheckable(True)
        self.setFixedSize(BELL_SIZE)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setAttribute(QtCore.Qt.WA_Hover)          # :hover 스타일에 필요
        self.hasUnread = False

    def setHasUnread(self, hasUnread: bool) -> None:
        """안 읽은 알림이 있는지(점 표시)."""
        if self.hasUnread != hasUnread:
            self.hasUnread = hasUnread
            self.update()

    def sizeHint(self):
        return BELL_SIZE

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        # 직접 그리는 위젯은 PE_Widget 을 그려야 스타일시트 배경(:hover, :checked)이 보인다.
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(QtWidgets.QStyle.PE_Widget, option, painter, self)
        icon = loadIcon(BELL_UNREAD_ICON_PATH if self.hasUnread else BELL_ICON_PATH, BELL_ICON_SIZE,
                        self.devicePixelRatioF())
        painter.drawPixmap(QtCore.QPointF((self.width() - BELL_ICON_SIZE) / 2, (self.height() - BELL_ICON_SIZE) / 2), icon)


class NotificationItemIcon(QtWidgets.QWidget):
    """목록 항목 왼쪽의 안 읽음 점 + 종류 아이콘."""

    def __init__(self, notification: Notification, showUnreadDot: bool, parent=None):
        super().__init__(parent)
        self.notification = notification
        self.showUnreadDot = showUnreadDot
        self.setFixedSize(UNREAD_DOT_COLUMN + LIST_ITEM_ICON_SIZE, LIST_ITEM_ICON_SIZE)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        ratio = self.devicePixelRatioF()
        if self.showUnreadDot:
            painter.drawPixmap(QtCore.QPointF(0, (self.height() - UNREAD_DOT_SIZE) / 2),
                               loadIcon(UNREAD_DOT_ICON_PATH, UNREAD_DOT_SIZE, ratio))
        painter.drawPixmap(QtCore.QPointF(UNREAD_DOT_COLUMN, 0),
                           loadIcon(kindIconPath(self.notification.kind), LIST_ITEM_ICON_SIZE, ratio))


class NotificationListPopup(QtWidgets.QFrame):
    """종 위로 열리는 알림 목록. Qt.Popup 이라 바깥을 누르거나 Esc 면 Qt 가 닫는다. 닫히면 closedSignal 을 보낸다."""
    closedSignal = QtCore.pyqtSignal()

    def __init__(self, center: NotificationCenter, textFunction, nowFunction=time.time, parent=None):
        super().__init__(parent, QtCore.Qt.Popup)
        self.setObjectName("notificationListPopup")
        self.setFixedWidth(LIST_WIDTH)                # 글자가 길면 rebuild 에서 늘린다(_fitWidth)
        self.setAttribute(QtCore.Qt.WA_NoMouseReplay)
        self.center = center
        self.textFunction = textFunction
        self.nowFunction = nowFunction

        self.titleLabel = plainLabel("", "notificationListTitle", self)
        self.clearButton = QtWidgets.QPushButton(self)
        self.clearButton.setObjectName("notificationClearAllButton")
        self.clearButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.clearButton.clicked.connect(self._fadeOutAndClear)
        self._clearAnimation = None
        self._fadingNotifications = []            # 모두 지우기를 누른 시점에 보이던 알림
        self.headerBand = QtWidgets.QWidget(self)
        self.headerBand.setObjectName("notificationListHeader")
        self.headerBand.setAttribute(QtCore.Qt.WA_StyledBackground)
        header = QtWidgets.QHBoxLayout(self.headerBand)
        header.setContentsMargins(*LIST_HEADER_MARGINS)
        header.addWidget(self.titleLabel)
        header.addStretch(1)
        header.addWidget(self.clearButton)

        self.itemContainer = QtWidgets.QWidget()
        self.itemContainer.setObjectName("notificationItemContainer")
        self.itemLayout = QtWidgets.QVBoxLayout(self.itemContainer)
        self.itemLayout.setContentsMargins(0, 0, 0, 0)
        self.itemLayout.setSpacing(0)
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setObjectName("notificationScrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setWidget(self.itemContainer)

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self.headerBand)
        outer.addWidget(self.scrollArea)

    def rebuild(self) -> None:
        """보관된 알림으로 목록을 통째로 다시 그린다. 지운 항목은 deleteLater 만으로는 한 프레임 겹쳐 보여서 setParent(None) 으로 바로 뗀다."""
        while self.itemLayout.count():
            widget = self.itemLayout.takeAt(0).widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        notificationList = self.center.keptNotifications()
        title = self.textFunction(TEXT_LIST_TITLE) or ""
        self.titleLabel.setText(title)
        self.clearButton.setText(self.textFunction(TEXT_CLEAR_ALL) or "")
        self.clearButton.setEnabled(bool(notificationList))
        if not notificationList:
            emptyLabel = plainLabel(self.textFunction(TEXT_EMPTY) or "", "notificationEmptyLabel", self.itemContainer)
            emptyLabel.setAlignment(QtCore.Qt.AlignCenter)
            emptyLabel.setMinimumHeight(LIST_EMPTY_MIN_HEIGHT)
            self.itemLayout.addWidget(emptyLabel)
        now = self.nowFunction()
        for notification in notificationList:
            self.itemLayout.addWidget(self._buildItem(notification, now))
        self.itemLayout.addStretch(1)
        self._fitWidth()
        self._fitHeight(len(notificationList))
        if self.isVisible() and getattr(self, "anchor", None) is not None:
            self._placeAbove()               # 열린 채 높이가 바뀌면 종 위에 다시 붙인다

    def _fadeOutAndClear(self) -> None:
        """모두 지우기. 항목을 흐려지게 한 뒤 지운다."""
        if self._clearAnimation is not None:
            return
        self._fadingNotifications = self.center.keptNotifications()    # 흐려지는 동안 온 알림은 지우지 않는다
        effect = QtWidgets.QGraphicsOpacityEffect(self.itemContainer)
        self.itemContainer.setGraphicsEffect(effect)
        self._clearAnimation = QtCore.QPropertyAnimation(effect, b"opacity", self)
        self._clearAnimation.setDuration(CLEAR_FADE_MS)
        self._clearAnimation.setStartValue(1.0)
        self._clearAnimation.setEndValue(0.0)
        self._clearAnimation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._clearAnimation.finished.connect(self._onFadeFinished)
        self._clearAnimation.start()

    def _onFadeFinished(self) -> None:
        self._clearAnimation.deleteLater()
        self._clearAnimation = None
        self.itemContainer.setGraphicsEffect(None)
        fading, self._fadingNotifications = self._fadingNotifications, []
        self.center.clearNotifications(fading)

    def _fitWidth(self) -> None:
        """폭 = max(기본 폭, 머리 줄, 알림 제목이 다 보이는 폭). 내용(body)은 줄바꿈이라 폭을 정하지 않는다."""
        scrollBar = self.scrollArea.verticalScrollBar().sizeHint().width()
        needed = max(self.layout().itemAt(0).sizeHint().width(), self.itemContainer.minimumSizeHint().width() + scrollBar)
        self.setFixedWidth(max(LIST_WIDTH, needed))

    def _buildItem(self, notification: Notification, now: float) -> QtWidgets.QWidget:
        """알림 한 건 → 목록 항목 위젯."""
        item = QtWidgets.QFrame(self.itemContainer)
        item.setObjectName("notificationListItem")
        titleLabel = plainLabel(notification.titleText, "notificationItemTitle", item)
        bodyLabel = plainLabel(breakableText(notification.bodyText), "notificationItemBody", item)
        bodyLabel.setWordWrap(True)
        # 줄바꿈 QLabel 의 최소 폭은 Qt 어림값이라 긴 문장이면 목록이 넓어진다. 폭은 무시하고 높이만 폭에 맞춘다
        bodyPolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        bodyPolicy.setHeightForWidth(True)
        bodyLabel.setSizePolicy(bodyPolicy)
        bodyLabel.setVisible(bool(notification.bodyText))
        timeLabel = plainLabel(formatRelativeTime(notification.createdAt, now, self.textFunction),
                               "notificationItemTime", item)
        textColumn = QtWidgets.QVBoxLayout()
        textColumn.setSpacing(LIST_TEXT_SPACING)
        textColumn.addWidget(titleLabel)
        textColumn.addWidget(bodyLabel)
        textColumn.addWidget(timeLabel)
        row = QtWidgets.QHBoxLayout(item)
        row.setContentsMargins(*LIST_ITEM_MARGINS)
        row.setSpacing(LIST_ITEM_SPACING)
        row.addWidget(NotificationItemIcon(notification, not notification.isRead, item), 0, QtCore.Qt.AlignTop)
        row.addLayout(textColumn, 1)
        return item

    def _fitHeight(self, itemCount: int) -> None:
        """보이는 높이를 정한다. 넘치면 스크롤. 줄바꿈 내용은 sizeHint 가 틀리므로 실제 폭에서의 높이(heightForWidth)로 잰다."""
        for index in range(self.itemLayout.count()):
            widget = self.itemLayout.itemAt(index).widget()
            if widget is not None:
                widget.show()
        maxHeight = self._screenHeight() - self.layout().itemAt(0).sizeHint().height()
        shownCount = max(1, min(itemCount, LIST_MAX_VISIBLE_ITEMS))
        scrollBarWidth = self.scrollArea.verticalScrollBar().sizeHint().width()
        for contentWidth in (self.width(), self.width() - scrollBarWidth):   # 스크롤이 생기면 좁아진 폭으로 다시 잰다
            heights = [self._itemHeight(self.itemLayout.itemAt(i), contentWidth) for i in range(self.itemLayout.count())]
            visibleHeight = min(sum(heights[:shownCount]), maxHeight)
            if visibleHeight >= sum(heights):
                break
        self.scrollArea.setFixedHeight(visibleHeight)
        self.adjustSize()

    def _screenHeight(self) -> int:
        """종이 있는 화면의 높이(목록은 아직 자리가 없어 종 위치로 찾는다).
        ponytail: 화면 높이만큼 긴 목록은 종을 덮을 수 있다. 종이 상태바에 있어 실제로는 거의 없다."""
        anchor = getattr(self, "anchor", None)
        point = anchor.mapToGlobal(QtCore.QPoint(0, 0)) if anchor is not None else QtCore.QPoint()
        screen = QtWidgets.QApplication.screenAt(point) or QtWidgets.QApplication.primaryScreen()
        return screen.availableGeometry().height()

    @staticmethod
    def _itemHeight(layoutItem: QtWidgets.QLayoutItem, width: int) -> int:
        return layoutItem.heightForWidth(width) if layoutItem.hasHeightForWidth() else layoutItem.sizeHint().height()

    def openAbove(self, anchor: QtWidgets.QWidget) -> None:
        """anchor(종 버튼) 위로 오른쪽 끝을 맞춰 연다."""
        self.anchor = anchor
        self.rebuild()
        self._placeAbove()
        self.show()
        # 연 목록의 점은 그대로 두고 데이터만 읽음으로 바꾼다(종의 점만 사라진다)
        self.center.markAllRead()

    def _placeAbove(self) -> None:
        anchor = self.anchor
        anchorTopRight = anchor.mapToGlobal(QtCore.QPoint(anchor.width(), 0))
        x = anchorTopRight.x() - self.width()
        y = anchorTopRight.y() - self.height()
        screen = QtWidgets.QApplication.screenAt(anchorTopRight) or QtWidgets.QApplication.primaryScreen()
        available = screen.availableGeometry()
        x = max(available.left(), min(x, available.right() - self.width()))
        y = max(available.top(), y)
        self.move(x, y)

    def mousePressEvent(self, event):
        """열린 채 종을 다시 누르면 닫기만 하게 한다. Qt.Popup 은 닫은 누르기를 종에 다시 보내 목록이 또 열리므로
        종 위를 누른 것이면 재전달 금지 표시를 켠다. Qt 가 누르기마다 표시를 지우므로 생성자가 아니라 여기서(super 뒤) 켠다."""
        super().mousePressEvent(event)
        anchor = getattr(self, "anchor", None)
        if anchor is not None and anchor.rect().contains(anchor.mapFromGlobal(event.globalPos())):
            self.setAttribute(QtCore.Qt.WA_NoMouseReplay, True)
            self.bellPressedAt = time.monotonic()        # 윈도에선 위 표시로도 재전달이 막히지 않아 종이 이 시각으로 가린다

    def hideEvent(self, event):
        super().hideEvent(event)
        # 열려 있는 동안 온 알림도 본 것이므로 닫을 때 한 번 더 읽음 처리한다
        self.center.markAllRead()
        self.closedSignal.emit()


class NotificationBell(QtWidgets.QWidget):
    """상태바에 붙이는 묶음: 종 버튼 + 목록 팝업 + 센터 구독.
    위젯이 지워지면 구독을 푼다 — 전역 센터가 지워진 위젯을 부르면 RuntimeError 가 난다.
    """
    _eventReceived = QtCore.pyqtSignal(str, object)       # 센터 이벤트를 화면 스레드로 넘기는 길

    def __init__(self, center: NotificationCenter, textFunction, parent=None):
        super().__init__(parent)
        self.setObjectName("notificationBell")
        self.center = center
        self.textFunction = textFunction
        self.bellButton = BellButton(self)
        self.popup = NotificationListPopup(center, textFunction, parent=self)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(BELL_SIDE_MARGIN, 0, BELL_SIDE_MARGIN, 0)
        layout.addWidget(self.bellButton)
        self.bellButton.clicked.connect(self._onBellClicked)
        self.bellButton.installEventFilter(self)
        self._isClosingPress = False              # 이번 종 누르기가 목록을 닫은 누르기의 재전달인가
        self.popup.closedSignal.connect(lambda: self.bellButton.setChecked(False))
        self._eventReceived.connect(self._handleNotificationEvent)
        center.subscribe(self._onNotificationEvent)
        self.destroyed.connect(lambda: center.unsubscribe(self._onNotificationEvent))
        self.refreshTexts()

    def refreshTexts(self) -> None:
        """언어가 바뀌면 lang.apply 가 부른다. 목록은 열 때마다 다시 그리므로 툴팁만 갱신한다."""
        self.bellButton.setToolTip(self.textFunction(TEXT_BELL_TOOLTIP) or "")

    def eventFilter(self, watched, event):
        """종에 온 누르기가 목록을 닫은 누르기의 재전달인지 표시한다."""
        if watched is self.bellButton and event.type() == QtCore.QEvent.MouseButtonPress:
            pressedAt = getattr(self.popup, "bellPressedAt", float("-inf"))
            self._isClosingPress = time.monotonic() - pressedAt < BELL_REOPEN_GUARD_SECONDS
        return False

    def _onBellClicked(self, checked: bool) -> None:
        """종 클릭 → 열기 / 닫기."""
        isClosingPress, self._isClosingPress = self._isClosingPress, False
        if checked and isClosingPress:
            # 목록은 그 누르기로 이미 닫혔으니 다시 열지 않는다
            self.bellButton.setChecked(False)
        elif checked:
            self.popup.openAbove(self.bellButton)
        else:
            self.popup.hide()

    def _onNotificationEvent(self, eventName, notification) -> None:
        """센터가 부르는 길. 어느 스레드에서 와도 시그널로 화면 스레드에 넘긴다."""
        self._eventReceived.emit(eventName, notification)

    def _handleNotificationEvent(self, eventName, notification) -> None:
        """센터 변화 → 종의 점 갱신, 열린 목록은 추가, 지우기일 때만 다시 그린다(읽음으로는 안 그린다)."""
        self.bellButton.setHasUnread(self.center.unreadCount() > 0)
        if self.popup.isVisible() and eventName in (EVENT_ADDED, EVENT_CLEARED):
            self.popup.rebuild()


TOAST_WIDTH = 300               # 그림자 여백까지 넣은 실제 창 폭
# pyqttoast 는 넘긴 폭 바깥에 그림자 여백을 붙여 창을 키우고 끄는 설정도 없어서, 그만큼 뺀 폭을 넘긴다
TOAST_SHADOW_WIDTH = DROP_SHADOW_SIZE * 2
TOAST_BODY_MAX_LINES = 4        # 넘는 내용은 '…' 으로 자른다(전체는 종 목록과 툴팁에 있다)
ELLIPSIS = "…"
TOAST_MARGIN = 12              # 앱 창 오른쪽, 상태바 위 여백
TOAST_SPACING = 8
TOAST_DURATION_MS = 5000
PENDING_RETRY_MS = 500          # 미뤄 둔 토스트를 창이 보일 때까지 다시 보는 간격
TOAST_MAX_VISIBLE = 3
TOAST_ICON_SIZE = 18
TOAST_BORDER_RADIUS = 0
TOAST_MARGINS = QtCore.QMargins(10, 7, 6, 7)
TOAST_ICON_SECTION_MARGINS = QtCore.QMargins(0, 0, 8, 0)
TOAST_TEXT_SECTION_MARGINS = QtCore.QMargins(0, 0, 8, 0)
TOAST_TEXT_SECTION_SPACING = 2


def tokenColor(token: str) -> QtGui.QColor:
    """스타일시트 색 토큰 → QColor. 라이브러리는 QSS 대신 QColor 를 받는다."""
    value = COLORS[token].strip()
    if value.startswith("rgb(") and value.endswith(")"):
        return QtGui.QColor(*[int(part) for part in value[4:-1].split(",")])
    return QtGui.QColor(value)


def shortToastBody(body: str, metrics: QtGui.QFontMetrics, width: int) -> str:
    """토스트에 보일 내용. TOAST_BODY_MAX_LINES 줄을 넘으면 들어가는 만큼 앞부분 + '…' (이분 탐색)."""
    def wrappedHeight(text: str) -> int:
        return metrics.boundingRect(QtCore.QRect(0, 0, width, 1 << 20), QtCore.Qt.TextWordWrap, text).height()

    # lineSpacing × N 이 아니라 실제 N 줄의 높이와 비교한다(글꼴에 따라 1px 어긋난다)
    maxHeight = wrappedHeight("\n".join(["0"] * TOAST_BODY_MAX_LINES))

    def fits(text: str) -> bool:
        return wrappedHeight(text) <= maxHeight

    text = breakableText(body)
    if fits(text):
        return text
    low, high = 0, len(text)
    while low < high:                    # fits(text[:n] + '…') 인 가장 큰 n
        middle = (low + high + 1) // 2
        low, high = (middle, high) if fits(text[:middle].rstrip() + ELLIPSIS) else (low, middle - 1)
    return text[:low].rstrip() + ELLIPSIS


def toastTextWidth(toast: Toast) -> int:
    """모양을 다 정한 토스트(띄우기 전)의 내용 글자 칸 폭. pyqttoast 의 폭 나누는 식을 공개 getter 로 거꾸로 푼다."""
    def horizontal(margins: QtCore.QMargins) -> int:
        return margins.left() + margins.right()

    iconSection = (horizontal(toast.getIconSectionMargins()) + horizontal(toast.getIconMargins())
                   + toast.getIconSize().width()
                   + (toast.getIconSeparatorWidth() if toast.isShowIconSeparator() else 0)) if toast.isShowIcon() else 0
    closeButton = (horizontal(toast.getCloseButtonMargins()) + toast.getCloseButtonWidth()) if toast.isShowCloseButton() else 0
    return (toast.maximumWidth() - horizontal(toast.getMargins()) - iconSection - horizontal(toast.getTextSectionMargins())
            - closeButton)


class ToastPresenter(QtCore.QObject):
    """알림 센터의 새 알림(showToast=True) → pyqttoast 토스트.

    hostWidget 은 토스트를 붙일 앱 창, bottomOffsetFunction 은 아래에서 비울 높이(상태바)를 돌려준다.
    떠 있는 토스트는 shownToasts 에 남긴다.
    """

    _eventReceived = QtCore.pyqtSignal(str, object)       # 센터 이벤트를 화면 스레드로 넘기는 길

    def __init__(self, hostWidget: QtWidgets.QWidget, center: NotificationCenter, bottomOffsetFunction=None,
                 durationMs: int = TOAST_DURATION_MS, isHostActiveFunction=None):
        """isHostActiveFunction() 이 False 면 토스트를 미뤘다가 창이 다시 앞으로 올 때 띄운다."""
        super().__init__(hostWidget)
        self.hostWidget = hostWidget
        self.center = center
        self.bottomOffsetFunction = bottomOffsetFunction or (lambda: 0)
        self.durationMs = durationMs
        self.isHostActive = isHostActiveFunction or self._isWindowInFront
        self.shownToasts = []
        self.pendingNotifications = []          # 창이 뒤에 있을 때 온 알림
        self._retryTimer = QtCore.QTimer(self)  # 앱은 앞인데 창이 아직 안 보일 때 다시 보는 타이머
        self._retryTimer.setSingleShot(True)
        self._retryTimer.setInterval(PENDING_RETRY_MS)
        self._retryTimer.timeout.connect(self._flushPending)
        QtWidgets.QApplication.instance().applicationStateChanged.connect(self._onApplicationStateChanged)
        Toast.setMaximumOnScreen(TOAST_MAX_VISIBLE)
        Toast.setSpacing(TOAST_SPACING)
        Toast.setPosition(ToastPosition.BOTTOM_RIGHT)
        Toast.setPositionRelativeToWidget(hostWidget)
        self._eventReceived.connect(self._handleNotificationEvent)
        center.subscribe(self._onNotificationEvent)
        self.destroyed.connect(lambda: center.unsubscribe(self._onNotificationEvent))
        self.destroyed.connect(lambda: self._disconnectApplication())

    def _onNotificationEvent(self, eventName, notification) -> None:
        """센터가 부르는 길. 어느 스레드에서 와도 시그널로 화면 스레드에 넘긴다."""
        self._eventReceived.emit(eventName, notification)

    def _handleNotificationEvent(self, eventName, notification) -> None:
        """토스트로 띄울 새 알림만 받는다."""
        if eventName != EVENT_ADDED or not notification.showToast:
            return
        if self.isHostActive():
            self.showToast(notification)
            return
        self.pendingNotifications.append(notification)
        QtWidgets.QApplication.alert(self.hostWidget.window())  # 작업표시줄 깜빡임
        self._retryPendingWhileActive()

    def _isWindowInFront(self) -> bool:
        """앱이 앞에 있고 메인 창이 최소화되지 않았는가. 설치 때의 창(Mid)은 나중에 다른 창 안으로 들어가므로 매번 window() 로 다시 찾는다."""
        window = self.hostWidget.window()
        return QtWidgets.QApplication.applicationState() == QtCore.Qt.ApplicationActive and window.isVisible() \
            and not window.isMinimized()

    def _disconnectApplication(self) -> None:
        try:
            QtWidgets.QApplication.instance().applicationStateChanged.disconnect(self._onApplicationStateChanged)
        except (TypeError, RuntimeError):         # 이미 끊김, 앱 종료 중
            pass

    def _onApplicationStateChanged(self, state) -> None:
        """앱이 다시 앞으로 오면 미뤄 둔 토스트를 띄운다."""
        if state != QtCore.Qt.ApplicationActive or not self.pendingNotifications:
            return
        QtCore.QTimer.singleShot(0, self._flushPending)   # 복원 직후엔 창 상태가 아직 최소화일 수 있다

    def _retryPendingWhileActive(self) -> None:
        """앱은 앞인데 창이 아직 안 보이면 상태 변화가 없어 _flushPending 이 안 불리므로 타이머로 다시 본다."""
        if QtWidgets.QApplication.applicationState() == QtCore.Qt.ApplicationActive and not self._retryTimer.isActive():
            self._retryTimer.start()

    def _flushPending(self) -> None:
        if not self.isHostActive():
            if self.pendingNotifications:
                self._retryPendingWhileActive()
            return
        pending, self.pendingNotifications = self.pendingNotifications[-TOAST_MAX_VISIBLE:], []
        for notification in pending:
            self.showToast(notification)

    def showToast(self, notification: Notification) -> Toast:
        """알림 한 건으로 토스트를 만들어 띄운다."""
        # 상태바 높이는 바뀔 수 있어 띄울 때마다 다시 잰다
        Toast.setOffset(TOAST_MARGIN, self.bottomOffsetFunction() + TOAST_MARGIN)
        toast = Toast(self.hostWidget)
        self._applyLook(toast, notification.kind)
        toast.setDuration(self.durationMs)
        toast.setTitle(notification.titleText)
        body = shortToastBody(notification.bodyText, QtGui.QFontMetrics(QtWidgets.QApplication.font()), toastTextWidth(toast))
        toast.setText(body)
        toast.setToolTip(fullBodyToolTip(notification.bodyText) if body.endswith(ELLIPSIS) else "")
        toast.closed.connect(lambda: self.shownToasts.remove(toast) if toast in self.shownToasts else None)
        self.shownToasts.append(toast)
        toast.show()
        return toast

    def _applyLook(self, toast: Toast, kind: str) -> None:
        """토스트 모양을 정한다."""
        textColor = tokenColor("textColor")
        subTextColor = tokenColor("textSubColor")
        toast.setStayOnTop(False)
        toast.setResetDurationOnHover(False)
        toast.setMinimumWidth(TOAST_WIDTH - TOAST_SHADOW_WIDTH)      # 늘 같은 폭
        toast.setMaximumWidth(TOAST_WIDTH - TOAST_SHADOW_WIDTH)
        toast.setBorderRadius(TOAST_BORDER_RADIUS)
        toast.setBackgroundColor(tokenColor("backgroundDarkColor"))
        toast.setTitleColor(textColor)
        toast.setTextColor(subTextColor)
        toast.setDurationBarColor(subTextColor)
        toast.setCloseButtonIconColor(subTextColor)
        toast.setShowIcon(True)
        toast.setShowIconSeparator(False)
        toast.setIconColor(None)                            # None = 넘긴 그림 색 그대로(다시 칠하지 않음)
        toast.setIconSize(QtCore.QSize(TOAST_ICON_SIZE, TOAST_ICON_SIZE))
        toast.setIcon(loadIcon(kindIconPath(kind), TOAST_ICON_SIZE, self.hostWidget.devicePixelRatioF()))
        appFont = QtWidgets.QApplication.font()
        titleFont = QtGui.QFont(appFont)
        titleFont.setBold(True)
        toast.setTitleFont(titleFont)
        toast.setTextFont(appFont)
        toast.setMargins(TOAST_MARGINS)
        toast.setIconSectionMargins(TOAST_ICON_SECTION_MARGINS)
        toast.setTextSectionMargins(TOAST_TEXT_SECTION_MARGINS)
        toast.setTextSectionSpacing(TOAST_TEXT_SECTION_SPACING)
        # 라이브러리 라벨은 자동 판별(AutoText)이라 '<' 가 있으면 HTML 로 해석된다. 내부 라벨에 직접 PlainText 를 건다.
        # 1.3.3 의 내부 이름에 기대므로 버전을 올리면 테스트가 먼저 깨진다.
        for privateName in ("_Toast__title_label", "_Toast__text_label"):
            label = getattr(toast, privateName, None)
            if label is not None:
                label.setTextFormat(QtCore.Qt.PlainText)


LANGUAGE_MAIN_KEY = "main"
LANGUAGE_SUB_KEY = "notification"


def installNotificationUi(hostWindow: QtWidgets.QMainWindow, statusBar: QtWidgets.QStatusBar, lang,
                          center: NotificationCenter = None):
    """종을 상태바 맨 오른쪽에, 토스트를 hostWindow 오른쪽 아래에 붙인다. 상태바의 다른 permanent 위젯을 다 붙인 뒤에 불러야 종이 맨 오른쪽에 온다."""
    center = center or getNotificationCenter()

    def textFunction(key: str) -> str:
        return lang.get(LANGUAGE_MAIN_KEY, LANGUAGE_SUB_KEY, key) or ""

    bell = NotificationBell(center, textFunction)
    statusBar.addPermanentWidget(bell)
    # lang.apply 는 언어 파일에 있는 이름만 돌아서, ko/en.json 에 "refreshTexts" 자리표시 키가 있어야 한다.
    lang.set(LANGUAGE_MAIN_KEY, LANGUAGE_SUB_KEY, "refreshTexts", bell.refreshTexts)
    toastPresenter = ToastPresenter(hostWindow, center, bottomOffsetFunction=lambda: statusBarOffset(statusBar))
    return bell, toastPresenter


def statusBarOffset(statusBar: QtWidgets.QStatusBar) -> int:
    """토스트 아래에 비워 둘 높이 = 상태바 높이. 창이 아직 안 떴으면 sizeHint 로 잡아 첫 토스트가 상태바를 덮지 않게 한다."""
    if statusBar.isHidden():
        return 0
    return statusBar.height() if statusBar.isVisible() else statusBar.sizeHint().height()
