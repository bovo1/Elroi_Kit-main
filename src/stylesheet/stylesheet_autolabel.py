"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    오토라벨링(바, 설정 독) 스타일. 규칙: 다크, 직각(둥근 모서리 없음), 상태는 색이 아니라 밝기로
    (꺼짐 = 흐리게, 충족 = 흐리게, 미충족 = 또렷하게). 선택자는 전부 오토라벨링 위젯 클래스명으로 시작한다.
"""

from stylesheet.stylesheet_component import COLORS, RULES

AUTO_LABEL_BUTTON_HEIGHT = "28px"            # 버튼 높이와 여백. 바 폭을 줄이려고 낮게 잡았다
AUTO_LABEL_BUTTON_PADDING = "0px 9px"
AUTO_LABEL_BUTTON_FONT_SIZE = "12px"         # 앱 13px 보다 한 단계 작게: 최대화에서 바가 한 줄에 들어가게
AUTO_LABEL_BUTTON_BACKGROUND = "rgba(255, 255, 255, 10)"       # 버튼 바탕(흰색을 약 4% 불투명하게)
AUTO_LABEL_BUTTON_HOVER = "rgba(255, 255, 255, 28)"
AUTO_LABEL_TAB_PADDING = "5px 0px 4px 0px"
AUTO_LABEL_UNDERLINE = f"2px solid {COLORS['textColor']}"
AUTO_LABEL_INPUT_UNDERLINE = f"1px solid {COLORS['textSubColor']}"
AUTO_LABEL_CONDITION_IMAGE_SIZE = "10px"   # 학습 조건 칸 아래 '이 이미지 n'
AUTO_LABEL_DOCK_CAPTION_SIZE = "12px"      # 설정 독의 표 머리, 작은 설명, 진행 숫자
AUTO_LABEL_CANCEL_BORDER = "1px solid rgba(255, 255, 255, 41)"   # 취소 버튼 테두리(흰색을 약 16% 불투명하게)
AUTO_LABEL_THRESHOLD_END_SIZE = "9px"      # 그래프 양 끝 값의 글자 크기
AUTO_LABEL_STEP_FONT_SIZE = "14px"         # 숫자 칸 양옆 − +
AUTO_LABEL_MAGNIFIER_FONT_SIZE = "11px"    # 돋보기 눈금, 값, 안내문

AUTO_LABEL_STYLESHEET = {
    "AutoLabelBar#autoLabelBar": {
        "background-color": COLORS['backgroundDarkColor'],
        "border": f"1px solid {COLORS['backgroundLightColor']}",
    },
    "AutoLabelBar QLabel": {
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
        "background": "transparent",
    },
    # 유사도 | 모델 탭 — 밑줄 탭
    "AutoLabelBar QPushButton#autoLabelTab": {
        "background": "transparent",
        "border": "none",
        "border-bottom": "2px solid transparent",
        "color": COLORS['textSubColor'],
        "font": f"bold {RULES['smallFontSize']}",
        "padding": AUTO_LABEL_TAB_PADDING,
    },
    "AutoLabelBar QPushButton#autoLabelTab:hover": {
        "color": COLORS['textColor'],
        "border-bottom": f"2px solid {COLORS['backgroundLightColor']}",
    },
    "AutoLabelBar QPushButton#autoLabelTab:checked": {
        "color": COLORS['textColor'],
        "border-bottom": AUTO_LABEL_UNDERLINE,
    },
    "AutoLabelBar QPushButton#autoLabelTab[locked=\"true\"]": {
        "color": COLORS['disabledColor'],
    },
    "AutoLabelBar QPushButton#autoLabelTab[locked=\"true\"]:hover": {
        "border-bottom": "2px solid transparent",
    },
    # 모델 학습, 추론, 일괄 추론 — 같은 모양(모든 버튼이 같은 모양)
    "AutoLabelBar QPushButton#autoLabelActionButton, AutoLabelBar QPushButton#autoLabelCancelButton": {
        "min-height": AUTO_LABEL_BUTTON_HEIGHT,
        "max-height": AUTO_LABEL_BUTTON_HEIGHT,
        "padding": AUTO_LABEL_BUTTON_PADDING,
        "background-color": AUTO_LABEL_BUTTON_BACKGROUND,
        "border": "1px solid transparent",                           # 테두리 없음
        "color": COLORS['textColor'],
        "font": f"bold {AUTO_LABEL_BUTTON_FONT_SIZE}",
    },
    "AutoLabelBar QPushButton#autoLabelActionButton:hover, AutoLabelBar QPushButton#autoLabelCancelButton:hover": {
        "background-color": AUTO_LABEL_BUTTON_HOVER,
    },
    "AutoLabelBar QPushButton#autoLabelActionButton[locked=\"true\"]": {
        "color": COLORS['disabledColor'],
        "background-color": AUTO_LABEL_BUTTON_BACKGROUND,
    },
    # 묶음 사이 세로 구분선
    "AutoLabelBar QFrame#autoLabelSeparator": {
        "background-color": COLORS['backgroundSubColor'],
        "border": "none",
    },
    "AutoLabelBar QPushButton#autoLabelIconButton": {
        "background": "transparent",
        "border": "none",
    },
    # 켜진 설정 버튼의 밝은 바탕은 쓸 수 있을 때만 — 이미지가 없어 잠기면 독이 숨겨졌는데 버튼만 켜진 채 밝게 남았다
    "AutoLabelBar QPushButton#autoLabelIconButton:hover:enabled, AutoLabelBar QPushButton#autoLabelIconButton:checked:enabled": {
        "background-color": AUTO_LABEL_BUTTON_HOVER,
    },
    # 학습, 일괄 추론 진행: 숫자, 얇은 막대
    "AutoLabelBar QLabel#autoLabelProgressLabel": {
        "color": COLORS['textColor'],
        "font-size": AUTO_LABEL_DOCK_CAPTION_SIZE,
    },
    "AutoLabelBar SmoothProgressBar#autoLabelJobBar": {        # 바탕 = background, 채움 = color(막대가 직접 그린다)
        "background": COLORS['backgroundLightColor'],
        "color": COLORS['textColor'],
    },
    "AutoLabelBar QPushButton#autoLabelCancelButton": {
        "border": AUTO_LABEL_CANCEL_BORDER,
    },
    # 임계값 칸
    "ThresholdGraph#autoLabelThresholdGraph": {
        "color": COLORS['textColor'],
        "qproperty-frameColor": COLORS['accentColor'],   # 돋보기가 보는 구간 틀(파란 틀)
    },
    "AutoLabelBar QLineEdit#autoLabelThresholdInput": {
        "background": "transparent",
        "border": "none",
        "border-bottom": AUTO_LABEL_INPUT_UNDERLINE,
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    "AutoLabelBar QLineEdit#autoLabelThresholdInput:disabled": {
        "color": COLORS['disabledColor'],
    },
    "AutoLabelBar QLabel#autoLabelThresholdEnd": {
        "color": COLORS['textSubColor'],
        "font-size": AUTO_LABEL_THRESHOLD_END_SIZE,
    },
    # − + — 바 임계값 칸, 설정 독 '클릭당 최대 픽셀' 이 같은 모양
    "AutoLabelBar QPushButton#autoLabelThresholdStep, SettingsDock QPushButton#autoLabelThresholdStep": {
        "background": "transparent",
        "border": "none",
        "color": COLORS['textSubColor'],
        "font-size": AUTO_LABEL_STEP_FONT_SIZE,
        "padding": "0px",
    },
    "AutoLabelBar QPushButton#autoLabelThresholdStep:hover, SettingsDock QPushButton#autoLabelThresholdStep:hover": {
        "color": COLORS['textColor'],
    },
    "AutoLabelBar QPushButton#autoLabelThresholdStep:disabled, SettingsDock QPushButton#autoLabelThresholdStep:disabled": {
        "color": COLORS['disabledColor'],
    },
    # 돋보기 — 바 그래프 위에 뜨는 판(Qt.Popup 이라 바 밖의 최상위 창 — 선택자는 클래스명으로만)
    "ThresholdMagnifier#autoLabelMagnifier": {
        "background-color": COLORS['backgroundDarkColor'],
        "border": f"1px solid {COLORS['backgroundLightColor']}",
        "color": COLORS['textColor'],
        "font-size": AUTO_LABEL_MAGNIFIER_FONT_SIZE,
    },
    # 학습 조건 세그먼트 — 미충족 = 또렷하게, 충족 = 흐리게
    "ConditionSegment QLabel#autoLabelConditionName, ConditionSegment QLabel#autoLabelConditionCount": {
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    "ConditionSegment[met=\"true\"] QLabel#autoLabelConditionName, ConditionSegment[met=\"true\"] QLabel#autoLabelConditionCount": {
        "color": COLORS['textSubColor'],
    },
    "ConditionSegment QLabel#autoLabelConditionImage": {
        "color": COLORS['textSubColor'],
        "font-size": AUTO_LABEL_CONDITION_IMAGE_SIZE,
    },
    "ConditionSegment QProgressBar#autoLabelConditionBar": {
        "background": COLORS['backgroundLightColor'],
        "border": "none",
    },
    "ConditionSegment QProgressBar#autoLabelConditionBar::chunk": {
        "background": COLORS['textColor'],
    },
    "ConditionSegment[met=\"true\"] QProgressBar#autoLabelConditionBar::chunk": {
        "background": COLORS['textSubColor'],
    },
    # 설정 독 — 바와 같은 다크, 직각. 켜짐/꺼짐은 밝기로(켬 = 흰 칸, 끔 = 테두리만)
    "SettingsDock#autoLabelSettingsDock": {
        "background-color": COLORS['backgroundDarkColor'],
        "border-top": f"1px solid {COLORS['backgroundLightColor']}",
    },
    "SettingsDock QLabel": {
        "background": "transparent",
        "color": COLORS['textSubColor'],
        "font-size": RULES['smallFontSize'],
    },
    "SettingsDock QLabel#autoLabelDockClass": {
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    # 독 머리(제목 줄) — 옵션 칸과 다른 바탕색 띠
    "SettingsDock QWidget#autoLabelDockHeader": {
        "background-color": COLORS['backgroundSubColor'],
        "border-bottom": f"1px solid {COLORS['backgroundLightColor']}",
    },
    "SettingsDock QLabel#autoLabelDockTitle, SettingsDock QLabel#autoLabelDockSection": {
        "color": COLORS['textColor'],
        "font": f"bold {RULES['smallFontSize']}",
    },
    "SettingsDock QLabel#autoLabelDockSubLabel, SettingsDock QLabel#autoLabelDockCaption": {
        "font-size": AUTO_LABEL_DOCK_CAPTION_SIZE,
    },
    "SettingsDock QLineEdit#autoLabelDockField": {
        "background": "transparent",
        "border": "none",
        "border-bottom": AUTO_LABEL_INPUT_UNDERLINE,
        "color": COLORS['textColor'],
        "font-size": RULES['smallFontSize'],
    },
    "SettingsDock QPushButton#autoLabelDockSegment": {
        "background": "transparent",
        "border": f"1px solid {COLORS['backgroundLightColor']}",
        "color": COLORS['textSubColor'],
        "font-size": AUTO_LABEL_DOCK_CAPTION_SIZE,
        "padding": "0px 9px",
    },
    "SettingsDock QPushButton#autoLabelDockSegment:hover": {
        "background-color": AUTO_LABEL_BUTTON_HOVER,
    },
    "SettingsDock QPushButton#autoLabelDockSegment:checked": {
        "color": COLORS['textColor'],
        "background-color": AUTO_LABEL_BUTTON_HOVER,
        "border": f"1px solid {COLORS['textSubColor']}",
    },
    "SettingsDock QPushButton#autoLabelSwatch": {
        "border": f"1px solid {COLORS['backgroundLightColor']}",
    },
    "SettingsDock QPushButton#autoLabelIconButton": {
        "background": "transparent",
        "border": "none",
    },
    "SettingsDock QPushButton#autoLabelIconButton:hover": {
        "background-color": AUTO_LABEL_BUTTON_HOVER,
    },
}
