"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    오토라벨링 설정 독 — 바의 설정 버튼으로 이미지 영역 아래에 연다.

    세 칸: 라벨링(보조 라벨링, 클릭당 최대 픽셀 수) / 학습(기본, 고급 스위치로 같은 자리의 내용만 바뀐다) /
    표시 및 적용([자동] + 클래스별 색, 표시, 적용 표).
    자동을 켜면 표시, 적용은 흐려지고 선택 이미지의 case 규칙(thresholdRules.applyRuleForImage)을 보여 주며 바꿀 수 없다.

    입력 칸의 범위는 INT_FIELD_RANGES, FLOAT_FIELD_SPECS(일부는 autoLabelConfig). 범위를 넘는 글자는 못 치고,
    덜 쓴 값은 포커스를 떼면 원래 값으로 돌아간다.
    화면만 맡는다 — settings 를 직접 고치고 settingsChanged 로 알릴 뿐, 값을 어디에 쓸지는 컨트롤러가 정한다. 접기는 collapseClicked.
"""

from typing import Callable, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from autolabel.autoLabelBar import noKeyboardFocus
from autolabel.autoLabelConfig import (CALIBRATION_RATE_RANGE, TRAINING_MAX_BATCH_SIZE, TRAINING_MIN_BATCH_SIZE,
                                       AutoLabelSettings)
from autolabel.thresholdField import STEP_BUTTON_SIZE, Switch, wrapTip
from autolabel.thresholdRules import ApplyRule
from notification.notificationUi import loadIcon

DOCK_HEIGHT = 212
HEADER_HEIGHT = 28
ROW_HEIGHT = 30
FIELD_WIDTH = 52
TABLE_CELL_WIDTH = 44
SWATCH_SIZE = 20
COLUMN_STRETCH = (2, 3, 2)
DOCK_MARGINS = (16, 6, 16, 10)
HEADER_MARGINS = (16, 0, 10, 0)
COLUMN_SPACING = 32
CAP_STEP = 10
CAP_RANGE = (1, 500)
# 정수 칸마다 범위
INT_FIELD_RANGES = {
    "epochs": (1, 100),
    "aeEpochs": (0, 10),
    "patience": (1, 100),
    "repDim": (1, 512),  # 밴드 수보다 작아야 한다(학습이 거절)
    "batchSize": (TRAINING_MIN_BATCH_SIZE, TRAINING_MAX_BATCH_SIZE),
    "numLayers": (1, 20),  # 크게 넣으면 학습 프로세스가 멈춘 것처럼 보인다
}
# 소수 칸마다 (범위, 소수 자리)
FLOAT_FIELD_SPECS = {
    "learningRate": ((1e-6, 1.0), 6),
    "calibrationRate": (CALIBRATION_RATE_RANGE, 1),
}

# 학습 칸 (설정 이름, 문구 키, 종류) — 기본, 고급 각각 왼쪽 열, 오른쪽 열
INT, FLOAT, SWITCH = "int", "float", "switch"
BASIC_FIELDS = ([("epochs", "epochs", INT), ("aeEpochs", "aeEpochs", INT), ("calibrationRate", "calibrationRate", FLOAT)],
                [("batchSize", "batchSize", INT), ("normalization", "normalization", SWITCH)])
ADVANCED_FIELDS = ([("learningRate", "learningRate", FLOAT), ("earlyStop", "earlyStop", SWITCH), ("patience", "patience", INT)],
                   [("numLayers", "numLayers", INT), ("repDim", "repDim", INT)])


class _RejectAboveTop:
    """범위 위로 넘는 글자는 아예 못 치게 한다(기본 검사기는 '덜 쓴 값' 으로 받아 범위 밖 값이 칸에 남는다)."""

    def validate(self, text, pos):
        state, text, pos = super().validate(text, pos)
        try:
            isAbove = float(text) > self.top()
        except ValueError:                                  # 빈 칸, '.' 같은 쓰는 중인 글자
            isAbove = False
        return (QtGui.QValidator.Invalid if state == QtGui.QValidator.Intermediate and isAbove else state), text, pos


class IntRangeValidator(_RejectAboveTop, QtGui.QIntValidator):
    pass


class FloatRangeValidator(_RejectAboveTop, QtGui.QDoubleValidator):
    pass


def _plainDecimal(value: float, decimals: int) -> str:
    """1e-05 대신 0.00001 로 — 입력 검사기가 받는 표준 표기. 소수는 늘 소수점 아래 한 자리 이상."""
    text = ("%.*f" % (decimals, value)).rstrip("0")
    return text + "0" if text.endswith(".") else text


def _caption(parent, objectName: str = "autoLabelDockLabel") -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(parent)
    label.setObjectName(objectName)
    return label


class Stepper(QtWidgets.QWidget):
    """−  값  + (스텝 입력). − + 는 바 임계값 칸과 같은 모양, 값은 직접 쳐도 된다.
    − + 는 다음, 이전 10 단위 경계로 가고, 값이 같으면 시그널을 내지 않는다. valueChanged(int)."""
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.minusButton = QtWidgets.QPushButton("−", self)
        self.plusButton = QtWidgets.QPushButton("+", self)
        self.valueInput = QtWidgets.QLineEdit(self)
        self.valueInput.setObjectName("autoLabelDockField")
        self.valueInput.setAlignment(QtCore.Qt.AlignCenter)
        self.valueInput.setFixedWidth(FIELD_WIDTH)
        self.valueInput.setValidator(IntRangeValidator(*CAP_RANGE, self.valueInput))
        self.valueInput.editingFinished.connect(self._commitTyped)
        self.valueInput.editingFinished.connect(self.valueInput.clearFocus)    # 엔터로 끝나도 커서가 계속 깜빡이지 않게
        self.valueInput.installEventFilter(self)     # 검사기가 '덜 씀'(빈 칸, 0)이면 editingFinished 가 안 온다 — 나갈 때 되돌린다
        for button in (self.minusButton, self.plusButton):
            button.setObjectName("autoLabelThresholdStep")
            button.setFixedSize(STEP_BUTTON_SIZE)
            button.setCursor(QtCore.Qt.PointingHandCursor)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.minusButton)
        row.addWidget(self.valueInput)
        row.addWidget(self.plusButton)
        self.minusButton.clicked.connect(lambda: self._step(-CAP_STEP))
        self.plusButton.clicked.connect(lambda: self._step(CAP_STEP))

    def setValue(self, value: int) -> None:
        self._value = int(min(max(value, CAP_RANGE[0]), CAP_RANGE[1]))
        self.valueInput.setText(str(self._value))

    def eventFilter(self, watched, event):
        if watched is self.valueInput and event.type() == QtCore.QEvent.FocusOut:
            self._commitTyped()
        return False

    def _commitTyped(self) -> None:
        """친 값이 범위 안 정수면 쓰고, 아니면 원래 값으로 되돌린다."""
        text = self.valueInput.text()
        isValid = self.valueInput.validator().validate(text, 0)[0] == QtGui.QValidator.Acceptable
        if isValid and int(text) != self._value:
            self.setValue(int(text))
            self.valueChanged.emit(self._value)
            return
        self.valueInput.setText(str(self._value))

    def value(self) -> int:
        return self._value

    def _step(self, delta: int) -> None:
        if delta > 0:
            target = (self._value // CAP_STEP + 1) * CAP_STEP
        else:
            target = ((self._value - 1) // CAP_STEP) * CAP_STEP
        before = self._value
        self.setValue(max(CAP_RANGE[0], target))
        if self._value != before:
            self.valueChanged.emit(self._value)


class SettingsDock(QtWidgets.QFrame):
    settingsChanged = QtCore.pyqtSignal()
    collapseClicked = QtCore.pyqtSignal()

    def __init__(self, text: Callable[[str], str], settings: AutoLabelSettings, parent=None):
        super().__init__(parent)
        self.setObjectName("autoLabelSettingsDock")
        self.setFixedHeight(DOCK_HEIGHT)
        self.text = text
        self.settings = settings
        self._texts = []  # (위젯, 문구 키) — 언어를 바꾸면 다시 넣는다
        self._tips = []  # (위젯, 툴팁 키)
        self._fields = {}
        self._rangeTips = []  # (입력 위젯, 종류, 최소, 최대, 소수 자리) — 받는 범위 툴팁
        self._autoRule: Optional[ApplyRule] = None

        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        column.addWidget(self._buildHeader())
        columns = QtWidgets.QHBoxLayout()
        columns.setContentsMargins(*DOCK_MARGINS)
        columns.setSpacing(COLUMN_SPACING)
        for widget, stretch in zip((self._buildLabeling(), self._buildTraining(), self._buildApply()), COLUMN_STRETCH):
            columns.addWidget(widget, stretch, QtCore.Qt.AlignTop)
        column.addLayout(columns, 1)
        self.refreshTexts()
        self.setApplyView(None)
        noKeyboardFocus(self)

    # ------------------------------------------------------------------ 만들기
    def _tr(self, widget, key: str):
        self._texts.append((widget, key))
        return widget

    def _buildHeader(self) -> QtWidgets.QWidget:
        header = QtWidgets.QWidget(self)
        header.setObjectName("autoLabelDockHeader")
        header.setAttribute(QtCore.Qt.WA_StyledBackground)       # 스타일시트 바탕색을 칠하려면 필요(일반 QWidget)
        header.setFixedHeight(HEADER_HEIGHT)
        row = QtWidgets.QHBoxLayout(header)
        row.setContentsMargins(*HEADER_MARGINS)
        icon = QtWidgets.QLabel(header)
        icon.setPixmap(loadIcon("ico/labeling/penbox/pen_autolabel_white.png", 18, icon.devicePixelRatioF()))
        row.addWidget(icon)
        row.addWidget(self._tr(_caption(header, "autoLabelDockTitle"), "dockTitle"), 1)
        self.collapseButton = QtWidgets.QPushButton(header)
        self.collapseButton.setObjectName("autoLabelIconButton")
        self.collapseButton.setIcon(QtGui.QIcon("ico/labeling/autolabel/chevron_down_white.png"))
        self.collapseButton.setFixedSize(24, 24)
        self.collapseButton.clicked.connect(self.collapseClicked.emit)
        row.addWidget(self.collapseButton)
        return header

    def _sectionTitle(self, parent, key: str) -> QtWidgets.QLabel:
        return self._tr(_caption(parent, "autoLabelDockSection"), key)

    def _row(self, parent, key: str, widget: QtWidgets.QWidget, tipKey: Optional[str] = None) -> QtWidgets.QWidget:
        """'이름 ........ 입력' 한 줄. 줄 전체에 설명 툴팁(tipKey, 없으면 '<key>Tip')."""
        row = QtWidgets.QWidget(parent)
        self._tips.append((row, tipKey or key + "Tip"))
        row.setFixedHeight(ROW_HEIGHT)
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tr(_caption(row), key), 1)
        layout.addWidget(widget, 0, QtCore.Qt.AlignRight)
        return row

    def _buildLabeling(self) -> QtWidgets.QWidget:
        box = QtWidgets.QWidget(self)
        column = QtWidgets.QVBoxLayout(box)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        title = QtWidgets.QWidget(box)
        title.setFixedHeight(24 + 8)
        QtWidgets.QHBoxLayout(title).addWidget(self._sectionTitle(title, "sectionLabeling"))
        title.layout().setContentsMargins(0, 0, 0, 8)
        column.addWidget(title)
        self.assistSwitch = Switch(box)
        self.assistSwitch.setChecked(self.settings.similarityAssist)
        self.assistSwitch.toggled.connect(lambda on: self._set("similarityAssist", on))
        column.addWidget(self._row(box, "similarityAssist", self.assistSwitch))
        column.addWidget(self._tr(_caption(box, "autoLabelDockSubLabel"), "capPerClick"))
        self.normalCap, self.abnormalCap = Stepper(box), Stepper(box)
        for stepper, name, key in ((self.normalCap, "normalCapPerClick", "classNormal"),
                                   (self.abnormalCap, "abnormalCapPerClick", "classAbnormal")):
            self._rangeTips.append((stepper.valueInput, INT, *CAP_RANGE, 0))
            stepper.setValue(getattr(self.settings, name))
            stepper.valueChanged.connect(lambda value, name=name: self._set(name, value))
            row = self._row(box, key, stepper, "capPerClickTip")
            row.layout().setContentsMargins(12, 0, 0, 0)
            column.addWidget(row)
        column.addStretch(1)
        return box

    def _field(self, parent, name: str, kind: str) -> QtWidgets.QWidget:
        if kind == SWITCH:
            widget = Switch(parent)
            widget.setChecked(bool(getattr(self.settings, name)))
            widget.toggled.connect(lambda on, name=name: self._set(name, on))
        else:
            widget = QtWidgets.QLineEdit(parent)
            widget.setObjectName("autoLabelDockField")
            widget.setFixedWidth(FIELD_WIDTH)
            widget.setAlignment(QtCore.Qt.AlignCenter)
            if kind == INT:
                intRange = INT_FIELD_RANGES[name]
                widget.setValidator(IntRangeValidator(*intRange, widget))
                self._rangeTips.append((widget, INT, *intRange, 0))
            else:
                floatRange, decimals = FLOAT_FIELD_SPECS[name]
                validator = FloatRangeValidator(*floatRange, decimals, widget)
                validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
                widget.setValidator(validator)
                self._rangeTips.append((widget, FLOAT, *floatRange, decimals))
            widget.setText(self._format(name))
            widget.editingFinished.connect(lambda name=name, kind=kind, widget=widget: self._onFieldEdited(name, kind, widget))
            widget.editingFinished.connect(widget.clearFocus)
            widget.installEventFilter(self)          # 검사기가 '아직 덜 씀'(0, 빈 칸, 범위 밖)이면 editingFinished 가 안 온다
        self._fields[name] = widget
        return widget

    def _fieldPage(self, parent, columns) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget(parent)
        row = QtWidgets.QHBoxLayout(page)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(24)
        for fields in columns:
            column = QtWidgets.QVBoxLayout()
            column.setSpacing(0)
            for name, key, kind in fields:
                column.addWidget(self._row(page, key, self._field(page, name, kind)))
            column.addStretch(1)
            row.addLayout(column, 1)
        return page

    def _buildTraining(self) -> QtWidgets.QWidget:
        box = QtWidgets.QWidget(self)
        column = QtWidgets.QVBoxLayout(box)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        title = QtWidgets.QWidget(box)
        titleRow = QtWidgets.QHBoxLayout(title)
        titleRow.setContentsMargins(0, 0, 0, 8)
        titleRow.addWidget(self._sectionTitle(title, "sectionTraining"), 1)
        self.basicButton = self._tr(QtWidgets.QPushButton(title), "modeBasic")
        self.advancedButton = self._tr(QtWidgets.QPushButton(title), "modeAdvanced")
        group = QtWidgets.QButtonGroup(title)
        for button in (self.basicButton, self.advancedButton):
            button.setObjectName("autoLabelDockSegment")
            button.setCheckable(True)
            button.setFixedHeight(20)
            group.addButton(button)
            titleRow.addWidget(button)
        self.basicButton.setChecked(True)
        column.addWidget(title)
        self.trainingPages = QtWidgets.QStackedWidget(box)
        self.trainingPages.addWidget(self._fieldPage(box, BASIC_FIELDS))
        self.trainingPages.addWidget(self._fieldPage(box, ADVANCED_FIELDS))
        self.basicButton.clicked.connect(lambda: self.trainingPages.setCurrentIndex(0))
        self.advancedButton.clicked.connect(lambda: self.trainingPages.setCurrentIndex(1))
        column.addWidget(self.trainingPages)
        column.addStretch(1)
        return box

    def _buildApply(self) -> QtWidgets.QWidget:
        box = QtWidgets.QWidget(self)
        column = QtWidgets.QVBoxLayout(box)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        title = QtWidgets.QWidget(box)
        titleRow = QtWidgets.QHBoxLayout(title)
        titleRow.setContentsMargins(0, 0, 0, 6)
        titleRow.addWidget(self._sectionTitle(title, "sectionApply"), 1)
        titleRow.addWidget(self._tr(_caption(title, "autoLabelDockCaption"), "applyAuto"))
        self.autoSwitch = Switch(title)
        self.autoSwitch.setChecked(self.settings.useAutoApply)
        self._tips.append((self.autoSwitch, "applyAutoTip"))
        self.autoSwitch.toggled.connect(lambda on: self._set("useAutoApply", on))
        titleRow.addWidget(self.autoSwitch)
        column.addWidget(title)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(0)
        grid.setColumnStretch(0, 1)
        for index, key in enumerate(("columnClass", "columnColor", "columnShow", "columnApply")):
            header = self._tr(_caption(box, "autoLabelDockCaption"), key)
            if index:
                header.setAlignment(QtCore.Qt.AlignCenter)
                grid.setColumnMinimumWidth(index, TABLE_CELL_WIDTH)
            grid.addWidget(header, 0, index)
        self.swatches, self.showSwitches, self.applySwitches = {}, {}, {}
        rows = (("background", "classBackground", "showBackground", "applyBackground", "backgroundColor"),
                ("normal", "classNormal", "showNormal", "applyNormal", "normalColor"),
                ("abnormal", "classAbnormal", "showAbnormal", "applyAbnormal", "abnormalColor"),
                ("uncertain", "classUncertain", "showUncertain", None, "uncertainColor"))
        for row, (key, textKey, showName, applyName, colorName) in enumerate(rows, start=1):
            name = self._tr(_caption(box, "autoLabelDockClass"), textKey)
            self._tips.append((name, "applyClass%sTip" % key.capitalize()))
            name.setFixedHeight(ROW_HEIGHT)
            grid.addWidget(name, row, 0)
            swatch = QtWidgets.QPushButton(box)
            swatch.setObjectName("autoLabelSwatch")
            swatch.setFixedSize(SWATCH_SIZE, SWATCH_SIZE)
            swatch.setCursor(QtCore.Qt.PointingHandCursor)
            swatch.clicked.connect(lambda checked=False, colorName=colorName: self._pickColor(colorName))
            self.swatches[colorName] = swatch
            grid.addWidget(swatch, row, 1, QtCore.Qt.AlignCenter)
            show = Switch(box)
            show.setChecked(bool(getattr(self.settings, showName)))
            show.toggled.connect(lambda on, showName=showName: self._set(showName, on))
            self.showSwitches[showName] = show
            grid.addWidget(show, row, 2, QtCore.Qt.AlignCenter)
            if applyName is not None:
                apply = Switch(box)
                apply.setChecked(bool(getattr(self.settings, applyName)))
                apply.toggled.connect(lambda on, applyName=applyName: self._set(applyName, on))
                self.applySwitches[applyName] = apply
                grid.addWidget(apply, row, 3, QtCore.Qt.AlignCenter)
        column.addLayout(grid)
        column.addStretch(1)
        self._paintSwatches()
        return box

    # ------------------------------------------------------------------ 값
    def _format(self, name: str) -> str:
        value = getattr(self.settings, name)
        return _plainDecimal(value, FLOAT_FIELD_SPECS[name][1]) if isinstance(value, float) else str(value)

    def _set(self, name: str, value) -> None:
        setattr(self.settings, name, value)
        if name == "useAutoApply":
            self.setApplyView(self._autoRule)
        self.settingsChanged.emit()

    def mousePressEvent(self, event):
        """독의 빈 곳을 누르면 입력 칸의 커서를 거둔다(포커스를 못 받는 곳이라 칸이 포커스를 쥔 채 남는다)."""
        focused = self.focusWidget()
        if focused is not None:
            focused.clearFocus()
        super().mousePressEvent(event)

    def eventFilter(self, watched, event):
        """입력 칸에서 포커스가 나가면 값을 확정하거나 되돌린다."""
        if event.type() == QtCore.QEvent.FocusOut:
            for name, widget in self._fields.items():
                if widget is watched:
                    self._onFieldEdited(name, INT if isinstance(getattr(self.settings, name), int) else FLOAT, widget)
        return False

    def _onFieldEdited(self, name: str, kind: str, widget: QtWidgets.QLineEdit) -> None:
        """입력 칸. 검사기가 '맞음' 으로 보는 값만 쓰고, 아니면(빈 칸, 0, 범위 밖) 원래 값으로 되돌린다."""
        state = widget.validator().validate(widget.text(), 0)[0]
        if state != QtGui.QValidator.Acceptable:
            widget.setText(self._format(name))
            return
        try:
            value = int(widget.text()) if kind == INT else float(widget.text())
        except ValueError:
            widget.setText(self._format(name))
            return
        if value != getattr(self.settings, name):
            self._set(name, value)
        widget.setText(self._format(name))

    def _pickColor(self, colorName: str) -> None:
        current = QtGui.QColor(*getattr(self.settings, colorName))
        chosen = QtWidgets.QColorDialog.getColor(current, self)
        if chosen.isValid():
            self._set(colorName, (chosen.red(), chosen.green(), chosen.blue()))
            self._paintSwatches()

    def _paintSwatches(self) -> None:
        for colorName, swatch in self.swatches.items():
            red, green, blue = getattr(self.settings, colorName)
            swatch.setStyleSheet("background-color: rgb(%d, %d, %d);" % (red, green, blue))

    # ------------------------------------------------------------------ 바깥에서 넣는 것
    def setApplyView(self, autoRule: Optional[ApplyRule]) -> None:
        """자동이 켜져 있으면 표시, 적용 칸을 흐리게 하고 그 이미지 규칙(autoRule)을 보여 준다. None = 이미지 없음(설정값 그대로). 보여 준 규칙은 settings 에 쓰지 않는다."""
        self._autoRule = autoRule
        isAuto = self.settings.useAutoApply
        pairs = (("showNormal", "applyNormal", "applyNormal"), ("showAbnormal", "applyAbnormal", "applyAbnormal"),
                 ("showBackground", "applyBackground", "applyBackground"))
        for showName, applyName, ruleName in pairs:
            for switch, settingName in ((self.showSwitches[showName], showName), (self.applySwitches[applyName], applyName)):
                switch.setEnabled(not isAuto)
                switch.setCheckedQuietly(getattr(autoRule, ruleName) if (isAuto and autoRule is not None)
                                         else bool(getattr(self.settings, settingName)))

    def refreshTexts(self) -> None:
        for widget, key in self._texts:
            widget.setText(self.text(key))
            widget.setToolTip(wrapTip(self.text(key + "Tip")))     # 설명이 없는 키는 빈 툴팁(안 뜬다)
        for widget, tipKey in self._tips:
            widget.setToolTip(wrapTip(self.text(tipKey)))
        for widget, kind, low, high, decimals in self._rangeTips:
            template = self.text("rangeTipInt" if kind == INT else "rangeTipFloat")
            bounds = (format(low, ","), format(high, ",")) if kind == INT else (_plainDecimal(low, decimals), _plainDecimal(high, decimals))
            widget.setToolTip(template.replace("{min}", bounds[0]).replace("{max}", bounds[1]).replace("{decimals}", str(decimals)))
        self.collapseButton.setToolTip(self.text("dockCollapse"))
        for swatch in self.swatches.values():
            swatch.setToolTip(wrapTip(self.text("swatchTooltip")))
