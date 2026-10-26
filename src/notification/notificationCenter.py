"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    알림 기능의 코어 모델 (Qt 사용 안 함).

    알림을 보관하는 규칙(보관 개수, 읽음 처리, 안 읽은 수)만 여기에 두고, 토스트, 종, 목록 위젯은
    이 객체를 구독해서 그리기만 한다(notificationUi.py). Qt 를 쓰지 않아 화면 없이 규칙을 검사할 수 있고,
    다른 스레드에서 온 알림을 화면 스레드로 넘기는 일은 화면 쪽 구독자가 맡는다.

    - 알림 종류는 성공, 실패, 안내. 목록에서 아이콘만 다르다.
    - 종 목록에는 최신이 위로 쌓이고, 목록을 열면 안 읽은 알림이 모두 읽음이 된다(토스트를 닫아도 읽음은 아니다).
    - keepInList=False 알림은 토스트만 띄우고 목록에 쌓지 않는다.
    - 파일에 저장하지 않는다.
"""

import time
import traceback
from dataclasses import dataclass
from typing import Callable, List, Optional, Union

# 문자열, 또는 호출 시점의 언어로 문구를 만드는 함수(언어를 바꾸면 목록이 새 언어로 보이게)
Text = Union[str, Callable[[], str]]

NOTIFICATION_SUCCESS = "success"
NOTIFICATION_FAILURE = "failure"
NOTIFICATION_INFO = "info"          # 성공, 실패가 아닌 안내
NOTIFICATION_KINDS = (NOTIFICATION_SUCCESS, NOTIFICATION_FAILURE, NOTIFICATION_INFO)

# 종 목록 최대 보관 개수. 넘으면 오래된 것부터 버린다.
MAX_KEPT_NOTIFICATIONS = 50

# 구독자에게 알려 주는 변화의 종류
EVENT_ADDED = "added"
EVENT_READ = "read"              # 읽음 처리: 종의 점만 갱신하면 된다
EVENT_CLEARED = "cleared"        # 목록을 다시 그려야 한다
# 읽음과 지우기를 나눈 이유: 읽음 처리로 목록까지 다시 그리면 연 목록의 '안 읽음 점' 이 바로 사라진다.


@dataclass
class Notification:
    """알림 한 건. title, body 는 문자열 또는 함수이므로 titleText, bodyText 로 읽는다. createdAt 은 time.time() 초."""
    kind: str
    title: Text
    body: Text = ""
    createdAt: float = 0.0
    showToast: bool = True
    keepInList: bool = True
    isRead: bool = False

    @property
    def titleText(self) -> str:
        return self.title() if callable(self.title) else self.title

    @property
    def bodyText(self) -> str:
        return self.body() if callable(self.body) else self.body


class NotificationCenter:
    """알림을 받아 보관하고, 변화를 구독자에게 (eventName, notification 또는 None) 으로 알린다.

    nowFunction 은 테스트에서 시간을 고정하려고 바꿔 끼울 수 있게 했다.
    """

    def __init__(self, maxKept: int = MAX_KEPT_NOTIFICATIONS, nowFunction: Callable[[], float] = time.time):
        self.maxKept = maxKept
        self.nowFunction = nowFunction
        self._keptList: List[Notification] = []
        self._subscriberList: List[Callable[[str, Optional[Notification]], None]] = []

    # ------------------------------------------------------------------ 구독
    def subscribe(self, callback: Callable[[str, Optional[Notification]], None]) -> None:
        """변화가 생기면 callback(eventName, notification) 을 부른다. EVENT_READ, EVENT_CLEARED 는 notification=None."""
        self._subscriberList.append(callback)

    def unsubscribe(self, callback: Callable[[str, Optional[Notification]], None]) -> None:
        """subscribe 로 등록한 콜백을 뺀다."""
        if callback in self._subscriberList:
            self._subscriberList.remove(callback)

    def _publish(self, eventName: str, notification: Optional[Notification]) -> None:
        """구독자에게 차례로 알린다. 콜백 예외는 여기서 막는다 — 알림 화면의 버그가 알림을 보낸 쪽(예: 라벨 저장)을 실패시키면 안 된다."""
        for callback in list(self._subscriberList):
            try:
                callback(eventName, notification)
            except Exception:
                traceback.print_exc()

    # ------------------------------------------------------------------ 알림 추가
    def notify(self, kind: str, title: Text, body: Text = "", showToast: bool = True, keepInList: bool = True) -> Notification:
        """알림 한 건을 만들어 보관하고 EVENT_ADDED 로 알린다. 모르는 kind, 빈 제목, 토스트도 목록도 아닌 조합은 ValueError.

        notify 와 목록을 고치는 메서드는 메인 스레드에서만 부른다(잠금이 없다). 작업 스레드는 시그널로 넘겨 부른다.
        """
        if kind not in NOTIFICATION_KINDS:
            raise ValueError("kind 는 %s 중 하나여야 한다: %r" % (NOTIFICATION_KINDS, kind))
        if not (title() if callable(title) else title):
            raise ValueError("title 은 비어 있을 수 없다")
        if not showToast and not keepInList:
            raise ValueError("토스트도 목록도 아니면 보이는 곳이 없다")

        notification = Notification(kind=kind, title=title, body=body, createdAt=self.nowFunction(),
                                    showToast=showToast, keepInList=keepInList)
        if keepInList:
            self._keptList.insert(0, notification)
            del self._keptList[self.maxKept:]
        self._publish(EVENT_ADDED, notification)
        return notification

    # ------------------------------------------------------------------ 목록 조작
    def keptNotifications(self) -> List[Notification]:
        """종 목록에 보여 줄 알림들 (최신이 앞). 복사본이다."""
        return list(self._keptList)

    def unreadCount(self) -> int:
        """안 읽은 알림 수. 종의 점 표시 여부를 정한다."""
        return sum(1 for notification in self._keptList if not notification.isRead)

    def markAllRead(self) -> None:
        """목록을 열었을 때 부른다."""
        changed = False
        for notification in self._keptList:
            if not notification.isRead:
                notification.isRead = True
                changed = True
        if changed:
            self._publish(EVENT_READ, None)

    def clearAll(self) -> None:
        """목록을 모두 비운다."""
        self.clearNotifications(self._keptList)

    def clearNotifications(self, notifications) -> None:
        """주어진 알림만 목록에서 뺀다(객체 동일성으로 가린다). 모두 지우기 도중 새로 온 알림을 남기려고 따로 뒀다."""
        targets = {id(notification) for notification in notifications}
        remaining = [notification for notification in self._keptList if id(notification) not in targets]
        if len(remaining) != len(self._keptList):
            self._keptList[:] = remaining
            self._publish(EVENT_CLEARED, None)


def relativeTimeParts(createdAt: float, now: float):
    """알림 시간 표시용 (언어 키, 숫자). 문구는 언어 파일이 정하고 여기서는 구간만 정한다."""
    elapsedSeconds = max(0.0, now - createdAt)
    if elapsedSeconds < 60:
        return ("justNow", 0)
    minutes = int(elapsedSeconds // 60)
    if minutes < 60:
        return ("minutesAgo", minutes)
    return ("hoursAgo", minutes // 60)


_sharedCenter: Optional[NotificationCenter] = None


def getNotificationCenter() -> NotificationCenter:
    """앱 전체가 함께 쓰는 알림 센터. 만드는 쪽과 보여 주는 쪽이 서로 다른 위젯 트리에 있어 전역으로 뒀다. 테스트는 직접 만들어 쓴다."""
    global _sharedCenter
    if _sharedCenter is None:
        _sharedCenter = NotificationCenter()
    return _sharedCenter
