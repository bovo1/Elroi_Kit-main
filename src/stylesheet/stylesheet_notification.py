"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    알림(상태바 종, 알림 목록) 스타일. 토스트는 pyqttoast 가 그리므로 색을 코드(notificationUi.ToastPresenter)에서 토큰으로 넘긴다.
    모든 모드에서 보이는 위젯이라 모드별 파일이 아니라 따로 둔다. 선택자는 전부 알림 위젯의
    클래스명으로 시작하므로 다른 위젯의 스타일을 덮어쓰지 않는다.
    직각(둥근 모서리 없음), 성공/실패는 색이 아니라 아이콘 모양으로(원+체크 / 세모+느낌표).
    예외: 안 읽음 점만 빨간색 — 점은 PNG 그림에 들어 있다(ico/notification/).
"""

from stylesheet.stylesheet_component import COLORS, RULES

# '모두 지우기' 버튼의 안쪽 여백 (위아래 3px, 좌우 10px)
NOTIFICATION_BUTTON_PADDING = "3px 10px"
# 알림 목록 스크롤바 선택자 (세로만 쓴다)
SCROLLBAR = "NotificationListPopup QScrollBar"

NOTIFICATION_STYLESHEET = {
    # Bell (status bar)
    "BellButton#notificationBellButton": {
        "background-color": "transparent",
        "color": COLORS['textColor'],
        "border": "none",
    },
    "BellButton#notificationBellButton:hover": {
        "background-color": COLORS['backgroundLightColor'],
    },
    "BellButton#notificationBellButton:checked": {
        "background-color": COLORS['backgroundLightColor'],
    },
    # Notification list popup
    "NotificationListPopup#notificationListPopup": {
        "background-color": COLORS['backgroundDarkColor'],
        "border": f"1px solid {COLORS['backgroundLightColor']}",
        "color": COLORS['textColor'],
    },
    # 목록 머리(제목, 모두 지우기) — 목록과 다른 바탕색 띠(설정 독 머리와 같은 색)
    "NotificationListPopup QWidget#notificationListHeader": {
        "background-color": COLORS['backgroundSubColor'],
        "border-bottom": f"1px solid {COLORS['backgroundLightColor']}",
    },
    "NotificationListPopup QLabel#notificationListTitle": {
        "color": COLORS['textColor'],
        "font": f"bold {RULES['smallFontSize']}",
    },
    # '모두 지우기' — 배경이 있는 버튼 (다른 QPushButton 과 같이 마우스를 올리면 강조색)
    "NotificationListPopup QPushButton#notificationClearAllButton": {
        "background-color": COLORS['backgroundLightColor'],
        "color": COLORS['textColor'],
        "border": "none",
        "border-radius": "0px",                     # 직각(둥근 모서리 없음)
        "font-size": RULES['smallFontSize'],
        "padding": NOTIFICATION_BUTTON_PADDING,
    },
    "NotificationListPopup QPushButton#notificationClearAllButton:hover": {
        "background-color": COLORS['accentColor'],
    },
    "NotificationListPopup QPushButton#notificationClearAllButton:disabled": {
        "background-color": "transparent",
        "color": COLORS['disabledColor'],
    },
    "NotificationListPopup QScrollArea#notificationScrollArea, NotificationListPopup QWidget#notificationItemContainer": {
        "background-color": COLORS['backgroundDarkColor'],
    },
    # 목록 스크롤바 (stylesheet_labeling 의 세로 스크롤바와 같은 모양, 바탕만 목록 바탕색)
    f"{SCROLLBAR}:vertical": {
        "border": RULES['displayScrollBarHandleBorder'],
        "background-color": COLORS['backgroundDarkColor'],
        "margin": RULES['scrollBarMarginVertical'],
        "width": RULES['smallScrollBarWidth'],
        "border-radius": RULES['scrollBarBorderRadius'],
    },
    f"{SCROLLBAR}::handle:vertical": {
        "background-color": COLORS['scrollHandleColor'],
        "border-radius": RULES['scrollBarBorderRadius'],
        "min-height": RULES['scrollBarHandleMinHeight'],
    },
    f"{SCROLLBAR}::handle:vertical:hover, {SCROLLBAR}::handle:vertical:pressed": {
        "background-color": COLORS['accentColor'],
    },
    f"{SCROLLBAR}::add-page:vertical, {SCROLLBAR}::sub-page:vertical": {
        "background": "none",
    },
    f"{SCROLLBAR}::add-line:vertical, {SCROLLBAR}::sub-line:vertical": {
        "background-color": COLORS['backgroundDarkColor'],
        "border": "none",
        "height": "0px",
    },
    f"{SCROLLBAR}::up-arrow:vertical, {SCROLLBAR}::down-arrow:vertical": {
        "background": "none",
    },
    "NotificationListPopup QFrame#notificationListItem": {
        "border-top": f"1px solid {COLORS['backgroundSubColor']}",
        "color": COLORS['textColor'],
    },
    "NotificationListPopup QLabel#notificationItemTitle": {
        "color": COLORS['textColor'],
        "font": f"bold {RULES['smallFontSize']}",
    },
    "NotificationListPopup QLabel#notificationItemBody, NotificationListPopup QLabel#notificationItemTime, NotificationListPopup QLabel#notificationEmptyLabel": {
        "color": COLORS['textSubColor'],
        "font-size": RULES['smallFontSize'],
    },
}
