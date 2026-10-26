"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.

    오토라벨링 컨트롤러 — 오토라벨링의 규칙, 작업 스레드, 바를 기존 라벨링 모드에 잇는 유일한 곳.
    규칙은 barState, thresholdRules, trainingPlan 이, 학습, 모델 상태는 modelFlow 가 맡고, 여기서는 그것들을 바, 화면, 중앙 허브(Sync)에 잇는다:
        - 펜 툴바 매직완드 ↔ 바 보이기, 브러시 동작 분기
        - 디스플레이 연결점(autoLabel*Handler, autoLabelFrameComposer): 브러시 클릭, 그리기 직전 미리보기 얹기 등
        - Sync 시그널: 이미지 선택/해제, 저장 직전 → 미리보기 비우기, 적용
        - 유사도 계산 스레드(workers.SimilarityWorker) ↔ 미리보기(similarityCore.SimilarityPreview)
        - 바 버튼, 임계값 칸 ↔ modelFlow, settings
    기존 코드와 닿는 곳은 autolabel_codemap.md 참조.
"""

import time
from collections import deque
from typing import Callable, Optional, Set

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from autolabel.autoLabelBar import AutoLabelBar
from autolabel.autoLabelConfig import (CALIBRATION_RATE_DEFAULT, LABEL_ABNORMAL, LABEL_BACKGROUND, LABEL_NORMAL,
                                       WRITE_DECLINED, WRITE_DONE, WRITE_FAILED, AutoLabelSettings, imageKey)
from autolabel.barState import JOB_NONE, REASON_MISSING_CASES, TAB_MODEL, TAB_SIMILARITY, BarInputs, Control, evaluateBar
from autolabel.dsadModel import calibratedCube
from autolabel.labelFiles import (LABEL_COLOR_KEY, LABEL_NAME_KEY, addModelLabelsToList, modelLabelInfo, readLabel,
                                  writeInferenceLabel)
from autolabel.modelFlow import ModelFlow
from autolabel.settingsDock import SettingsDock
from autolabel.similarityCore import PreviewFrame, SimilarityClick, SimilarityPreview, composePreview
from autolabel.thresholdField import wrapTip
from autolabel.thresholdRules import SIMILARITY_RANGE, modelBaseRange
from autolabel.trainingPlan import (ClassPixelCounts, TrainingMinimums, countClassPixels,
                                    isSalImage, isTrainingReady, isTrainingStartCase, isTrainingTargetCase,
                                    missingRequiredCases, planBatch)
from autolabel.workers import SimilarityWorker
from constants.constants import (DRAWING_MODE_ADVANCED_LABELING, DRAWING_MODE_ERASING, DRAWING_MODE_LABELING,
                                 DRAWING_MODE_PAINTING, DRAWING_MODE_PIXEL_BASED_LABELING, DRAWING_MODE_POLYGON,
                                 DRAWING_MODE_RECTANGLE, DRAWING_MODE_SEMI_AUTO_LABELING, LABEL_UNSELECTED,
                                 MESSAGE_BOX_CONFIRMATION)
from utils.custom_ui import messageBox

LANGUAGE_MAIN_KEY = "labeling"
LANGUAGE_SUB_KEY = "autoLabel"
BAR_BOTTOM_MARGIN = 12            # 바를 디스플레이 아래 가장자리에서 띄우는 거리
SIMILARITY_DECIMALS = 2
SIMILARITY_STEP = 0.1
MODEL_DECIMALS = 3
RECOUNT_MIN_INTERVAL_MS = 150  # 그리는 동안 학습 조건을 다시 세는 최소 간격(마우스 이동마다 세면 끌린다)
MODEL_STEP_FACTOR = 1.05  # 모델 임계값 한 칸(곱셈 — 점수 폭이 모델마다 다르다)

# 유사도 모드에서 미리보기 위에서 쓰는 도구 — 그 밖의 도구로 라벨을 건드리면 남은 미리보기를 먼저 적용한다(_onStrokeStart)
PREVIEW_DRAWING_MODES = (DRAWING_MODE_LABELING, DRAWING_MODE_ERASING)
LABEL_EDITING_MODES = PREVIEW_DRAWING_MODES + (DRAWING_MODE_PAINTING, DRAWING_MODE_RECTANGLE, DRAWING_MODE_POLYGON,
                                               DRAWING_MODE_SEMI_AUTO_LABELING, DRAWING_MODE_PIXEL_BASED_LABELING,
                                               DRAWING_MODE_ADVANCED_LABELING)
LOCKED_PEN_TOOLS = ("penAdvancedLabeling", "pen_painting", "pen_rectangle", "pen_polygon")
LOCKED_DRAWING_MODES = tuple(mode for mode in LABEL_EDITING_MODES if mode not in PREVIEW_DRAWING_MODES)
REFERENCE_PEN_TOOL = "pen_draw_type"  # 잠금을 풀 때 이 버튼(브러시)의 켜짐을 따른다
# 이 위젯에 포커스가 있으면 ← →, 스페이스 단축키를 끈다(그 위젯이 키를 직접 쓴다)
KEY_OWNING_WIDGETS = (QtWidgets.QLineEdit, QtWidgets.QAbstractSpinBox, QtWidgets.QTextEdit, QtWidgets.QPlainTextEdit,
                      QtWidgets.QAbstractSlider, QtWidgets.QComboBox, QtWidgets.QAbstractItemView)

INFER_OVERWRITE_ALL, INFER_ONLY_CLASSES = "all", "only"  # 추론 쓰기 방식(_askInferenceMode)
INFER_MODE_HTML = "%s<br><table cellspacing='0' cellpadding='3'>%s</table><p style='color:#9a9a9a'>%s</p>"
INFER_MODE_OPTION_HTML = "<tr><td>%s</td><td>&nbsp;—&nbsp;%s</td></tr>"


def focusUsesKey(focus: Optional[QtWidgets.QWidget], key: int) -> bool:
    """focus 위젯이 이 키를 직접 쓰는가 — 그러면 같은 키의 단축키는 끈다. 일반 버튼은 쓰지 않는다(거기 포커스가 있어도 스페이스 = 추론이 먹어야 한다)."""
    if isinstance(focus, KEY_OWNING_WIDGETS):
        return True
    if key == QtCore.Qt.Key_Space:
        return isinstance(focus, QtWidgets.QAbstractButton) and focus.isCheckable()
    return isinstance(focus, QtWidgets.QTabBar)


def scrollTableTo(cellContent: QtWidgets.QWidget) -> None:
    """cellContent 가 들어 있는 표 줄이 보이게 표를 스크롤한다. 줄은 셀 위젯으로 찾는다(화면 위치로 찾으면 안 보이는 탭에서 -1)."""
    table = cellContent.parentWidget()
    while table is not None and not isinstance(table, QtWidgets.QTableWidget):
        table = table.parentWidget()
    if table is None:
        return
    for row in range(table.rowCount()):
        for column in range(table.columnCount()):
            cell = table.cellWidget(row, column)
            if cell is not None and (cell is cellContent or cell.isAncestorOf(cellContent)):
                table.scrollTo(table.model().index(row, column))
                return


class AutoLabelController(QtCore.QObject):
    """오토라벨링 한 덩어리. labeling_mode_main 이 한 번 만든다.

    입력 : display(Display_Form), sync(Sub_Core_Sync_Labeling), lang, barHost(바를 띄울 위젯 — 디스플레이를 감싼 칸)
    """

    def __init__(self, display, sync, lang, barHost: QtWidgets.QWidget):
        super().__init__(barHost)
        self.display = display
        self.sync = sync
        self.lang = lang
        self.barHost = barHost
        self.settings = AutoLabelSettings()
        self.isEnabled = False
        self._isAvailable = None  # 이미지가 하나라도 있는가 — 바뀔 때만 펜에 알린다
        self._counts = ClassPixelCounts()
        self._imageCounts = None
        self.similarityPreview = SimilarityPreview()
        self._isAssistOn = self.settings.similarityAssist  # 보조 라벨링을 끄는 순간을 알아채려고
        self._lockedTools = set()
        self._batchStartLabels = {}  # 일괄 추론 시작 때 이미지별 라벨 사본(도는 동안 고쳤는지 보려고)
        self._inferenceStartLabel = None
        self._generation = 0  # 미리보기를 비울 때마다 +1 — 그 전에 맡긴 클릭 결과는 버린다
        self._pendingGenerations = deque()
        self.similarityWorker = SimilarityWorker()
        self.similarityWorker.scoreReadySignal.connect(self._onSimilarityScoreReady)
        self.similarityWorker.failedSignal.connect(self._onSimilarityFailed)

        self.bar = AutoLabelBar(self.text, barHost)
        self.bar.hide()
        self.bar.threshold.setScale(SIMILARITY_RANGE, None, SIMILARITY_DECIMALS, stepSize=SIMILARITY_STEP)
        self.bar.threshold.setValue(self.settings.similarityFloor)
        self.bar.threshold.valueChanging.connect(self._onThresholdChanging)
        self.bar.threshold.valueCommitted.connect(self._onThresholdCommitted)
        self.bar.threshold.valueReverted.connect(self._onThresholdReverted)
        self.bar.threshold.autoToggled.connect(self._onAutoThresholdToggled)
        self.bar.tabSelected.connect(self._onTabSelected)
        barHost.installEventFilter(self)
        self.bar.installEventFilter(self)  # 바 폭이 바뀌면 다시 가운데로

        self.modelFlow = ModelFlow(self)
        self.modelFlow.changed.connect(self.refresh)
        self.bar.trainClicked.connect(self._onTrainClicked)
        self._removedLabelClasses = {}  # 이미지 키 → 추론으로 라벨 탭에서 뺀 클래스(되돌리기 대비)
        self.bar.trainCancelClicked.connect(self.modelFlow.cancelJob)
        self.bar.inferClicked.connect(self._onInferClicked)
        self.bar.batchClicked.connect(self._onBatchClicked)
        self.bar.batchCancelClicked.connect(self.modelFlow.cancelJob)
        self.bar.previousImageClicked.connect(lambda: self._selectNeighbourImage(-1))
        self.bar.nextImageClicked.connect(lambda: self._selectNeighbourImage(1))
        # 단축키: ← → 이전, 다음 이미지, 스페이스 = 추론. 창 전체에서 듣고, 그 키를 직접 쓰는 위젯에 포커스가 있으면 끈다(_updateShortcuts).
        self.shortcuts = []
        for key, button in ((QtCore.Qt.Key_Left, self.bar.previousButton), (QtCore.Qt.Key_Right, self.bar.nextButton),
                            (QtCore.Qt.Key_Space, self.bar.inferButton)):
            shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(key), barHost)
            shortcut.setContext(QtCore.Qt.WindowShortcut)
            shortcut.setAutoRepeat(False)
            shortcut.setEnabled(False)
            shortcut.activated.connect(button.click)
            self.shortcuts.append(shortcut)
        QtWidgets.QApplication.instance().focusChanged.connect(self._updateShortcuts)

        # 설정 독 — 이미지 영역 맨 아래 줄
        self.dock = SettingsDock(self.text, self.settings, barHost)
        self.dock.hide()
        barHost.layout().addWidget(self.dock)
        self.bar.settingsToggled.connect(self._setDockVisible)
        self.bar.refitted.connect(self._placeBar)
        self.dock.collapseClicked.connect(lambda: self.bar.settingsButton.setChecked(False))
        self.dock.settingsChanged.connect(self._onSettingsChanged)

        display.autoLabelBrushHandler = self._onBrushClick
        display.autoLabelFrameComposer = self._composeFrame
        display.autoLabelHistoryHandler = self._onHistory
        display.autoLabelEraseHandler = self._onErase
        display.autoLabelStrokeStartHandler = self._onStrokeStart
        display.autoLabelMenuHandler = self._menuPolicy
        display.autoLabelLabelChangedHandler = self._onLabelMaybeChanged
        self._isRefreshPending = False
        self._lastRecountTime = 0.0
        self._baseWindowMinWidth = None
        self._skipRecountOnce = False  # 임계값 미리보기 다시 그리기는 라벨을 안 바꾼다 — 다시 세지 않는다
        sync.penToAutoLabelSignal.connect(self.setEnabled)
        sync.autoLabelBeforeSaveSignal.connect(self._onBeforeSave)
        sync.image_to_display_signal.connect(self._onImageEvent)
        sync.label_image_to_display_signal.connect(self._onImageEvent)
        sync.image_sub_to_display_signal.connect(self._onImageEvent)
        sync.image_to_core_signal.connect(self._onImageListEvent)
        lang.set(LANGUAGE_MAIN_KEY, LANGUAGE_SUB_KEY, "refreshTexts", self._refreshTexts)
        QtWidgets.QApplication.instance().aboutToQuit.connect(self.shutdown)
        self._updateAvailability()

    # ------------------------------------------------------------------ 공용
    def text(self, key: str) -> str:
        return self.lang.get(LANGUAGE_MAIN_KEY, LANGUAGE_SUB_KEY, key) or ""

    def shutdown(self) -> None:
        """앱 종료 — 스레드를 끝낸다(살아 있는 QThread 가 지워지면 Qt 가 앱을 강제 종료한다)."""
        self.similarityWorker.stop()
        self.modelFlow.shutdown()

    def listedImages(self):
        """이미지 탭 목록 [(번호, 폴더 경로)] — 번호 순."""
        return [(number, entry['full_path']) for number, entry in sorted(self.sync.image_obj_dict.items())]

    def imageName(self, number: int) -> str:
        return self.sync.image_obj_dict[number]['name']

    def cubeOf(self, number: int):
        """DB 큐브(보정된 raw). 초분광 데이터가 없으면 None."""
        image = self.sync.Core_DB_Labeling['image_list'].get(number)
        cube = image['image_info'].get('image_raw') if image else None
        return cube if getattr(cube, "ndim", 0) == 3 else None

    def cubeProvider(self, number: int, cube: np.ndarray, rate: float) -> Callable[[], np.ndarray]:
        """학습, 추론이 쓸 큐브를 돌려주는 함수 — 설정의 보정 비율을 학습 모드와 같은 식으로 적용한다(calibratedCube).
        배율이 기본이면 DB 큐브 그대로, 아니면 호출할 때 계산한다(일괄 추론이 큐브 복사본을 한꺼번에 들지 않게). 보정 원본은 지금 잡아 둔다 — 계산 중 이미지를 목록에서 빼도 끝까지 간다."""
        if rate == CALIBRATION_RATE_DEFAULT:
            return lambda: cube
        info = self.sync.Core_DB_Labeling['image_list'].get(number, {}).get('image_info', {})
        sources = tuple(info.get(key) for key in ('image_raw_origin', 'image_raw_dark', 'image_raw_white'))
        if not all(isinstance(array, np.ndarray) and array.size for array in sources):
            sources = None                                      # 보정 파일이 없는 이미지 — 보정한 큐브에 곱한다
        return lambda: calibratedCube(cube, rate, sources)

    def _selectedImageNumber(self) -> int:
        return self.sync.image_control_dict['select_image_number']

    def _selectedImagePath(self) -> Optional[str]:
        number = self._selectedImageNumber()
        if number is None or number < 0 or number not in self.sync.image_obj_dict:
            return None
        return self.sync.image_obj_dict[number]['full_path']

    def _selectedCube(self):
        """선택 이미지의 DB 큐브. 디스플레이 쪽 image_raw 는 시각화 옵션으로 덮어써질 수 있어 쓰지 않는다. 초분광이 없거나 라벨과 크기가 다르면 None."""
        cube = self.cubeOf(self._selectedImageNumber())
        if cube is None or cube.shape[:2] != self.display.image_label.shape:
            return None
        return cube

    def _modelLabelColors(self) -> dict:
        return {LABEL_BACKGROUND: self.settings.backgroundColor, LABEL_NORMAL: self.settings.normalColor,
                LABEL_ABNORMAL: self.settings.abnormalColor}

    def _labelColor(self, labelNumber: int):
        """라벨 탭의 색. 없으면 모델 결과 라벨만 설정 독의 색, 그 밖은 None(그리지 않음)."""
        entry = self.sync.label_obj_dict.get(labelNumber)
        return entry['color'] if entry else self._modelLabelColors().get(labelNumber)

    # ------------------------------------------------------------------ 켜기/끄기, 상태 그리기
    def setEnabled(self, isEnabled: bool) -> None:
        """펜 툴바 매직완드. 끄면 미리보기를 버리고 바를 숨기며, 학습한 모델이 있으면 지울지 묻는다(아니오면 그대로 두어 다시 켜면 쓴다).
        켜면 지금 이미지의 라벨을 보이게 켠다. 이미지를 모두 지워 꺼질 때는 그 까닭부터 알린다 — 지우기 전에 물으면 이미지 삭제를 묻는 것처럼 보인다."""
        if not isEnabled and self.modelFlow.runningJob != JOB_NONE and self.sync.image_obj_dict:
            # 도는 중에 끈다: 아니요 = 켠 채 그대로(펜 버튼도 되돌린다). 이미지를 모두 지워 꺼질 때는 묻지 않고 취소한다
            if not self._confirm("jobRunningOffTitle", "jobRunningOffMessage"):
                self.sync.autoLabelKeepOnSignal.emit()
                return
            self.modelFlow.cancelJob()
        elif not isEnabled:
            self.modelFlow.cancelJob()
        self.isEnabled = isEnabled
        messageKey = "discardModelMessage" if self.sync.image_obj_dict else "discardModelNoImagesMessage"
        if not isEnabled and self.modelFlow.hasModel and self._confirm("discardModelTitle", messageKey):
            self.modelFlow.discardModel()
        self.modelFlow.prepareTraining(isEnabled)
        if isEnabled:
            self._showCurrentLabels()
        else:
            self._discardPreviewWithNotice()
            self._configureThresholdField()
        self._setDockVisible(self.bar.settingsButton.isChecked())
        self.refresh()
        self._placeBar()

    def _showCurrentLabels(self) -> None:
        """지금 이미지의 라벨 탭 줄(0 무시 제외)을 모두 보이게 — 오토라벨링이 켜져 있는 동안. 라벨 탭은 이미지를 열 때 줄을 숨김으로 만든다."""
        if not self.isEnabled or self._selectedImagePath() is None:
            return
        labels = {number: {LABEL_NAME_KEY: entry['name'], LABEL_COLOR_KEY: list(entry['color'])}
                  for number, entry in self.sync.label_obj_dict.items() if number != 0}
        if labels:
            self._ensureLabelClasses(self._selectedImageNumber(), labels)

    def _barInputs(self) -> BarInputs:
        path = self._selectedImagePath()
        flow = self.modelFlow
        hasScoreMap = flow.storedScore(path) is not None
        return BarInputs(isEnabled=self.isEnabled, activeTab=self.bar.activeTab(), hasImage=path is not None,
                         hasModel=flow.hasModel, isTrainingReady=isTrainingReady(self._counts),
                         runningJob=flow.runningJob, imageHasScoreMap=hasScoreMap,
                         isLabelInferenceResult=hasScoreMap and flow.isAdjustable(path, self.display.image_label),
                         missingCases=tuple(missingRequiredCases([listedPath for _, listedPath in self.listedImages()])),
                         isSimilarityAssistOn=self.settings.similarityAssist,
                         isTrainingCase=path is not None and isTrainingStartCase(path),
                         isSalImage=path is not None and isSalImage(path))

    def _reasonText(self, control: Control) -> str:
        if control.enabled or control.reason is None:
            return ""
        text = self.text("reason_" + control.reason)
        if control.reason == REASON_MISSING_CASES:
            text = text.replace("{cases}", " · ".join(str(case) for case in control.details))
        return text

    def _refreshTexts(self) -> None:
        self.dock.refreshTexts()
        self.refresh()
        QtCore.QTimer.singleShot(0, self._placeBar)  # 글자 폭이 반영된 뒤 한 번 더 맞춘다

    def _updateAvailability(self) -> None:
        """이미지가 하나도 없으면 펜의 오토라벨링을 끄고 잠근다(penToAutoLabelSignal → setEnabled(False)). 값을 먼저 바꾸고 알린다 — 그 사이 refresh 가 다시 알리지 않게."""
        isAvailable = bool(self.sync.image_obj_dict)
        if isAvailable != self._isAvailable:
            self._isAvailable = isAvailable
            self.sync.autoLabelAvailableSignal.emit(isAvailable)

    def refresh(self) -> None:
        """지금 상태를 바에 그린다(언어가 바뀌어도 불린다). 학습 조건은 여기서 한 번만 센다(디스크 확인)."""
        self._updateAvailability()
        self._counts, self._imageCounts = self._liveConditionCounts() if self.isEnabled else (ClassPixelCounts(), None)
        view = evaluateBar(self._barInputs())
        if not view.modelTab.enabled and self.bar.activeTab() == TAB_MODEL:
            self.bar.selectTab(TAB_SIMILARITY)
            return
        isModelTab = self.bar.activeTab() == TAB_MODEL
        self.bar.setVisible(view.isVisible)
        self._updateShortcuts()
        self._updateToolLock(view.brushIsSimilarity)
        self.bar.render(view, self._reasonText, self.modelFlow.hasModel)
        if self.modelFlow.runningJob == JOB_NONE:
            self._batchStartLabels = {}  # 일괄 추론이 끝났다 — 이미지별 라벨 사본을 놓는다
        hasPrevious, hasNext = self._neighbourImages()
        self.bar.previousButton.setEnabled(view.hasImage and hasPrevious)
        self.bar.nextButton.setEnabled(view.hasImage and hasNext)
        self.dock.setApplyView(self._selectedApplyRule())
        self.bar.threshold.setAutoVisible(isModelTab, self.settings.useAutoThreshold, self.text("auto"))
        inputTip = (self.text("thresholdRangeModel") if isModelTab else
                    self.text("thresholdRangeSimilarity").replace("{min}", format(SIMILARITY_RANGE[0], "g")).replace("{max}", format(SIMILARITY_RANGE[1], "g")))
        self.bar.threshold.setTexts(self.text("thresholdDown"), self.text("thresholdUp"), inputTip)
        isLocked = (isModelTab or not view.hasImage) and not view.thresholdAdjust.enabled   # 이미지가 없으면 유사도 탭도
        self.bar.threshold.setLocked(isLocked, self._reasonText(view.thresholdAdjust) if isLocked else "")
        counts, minimums = self._counts, TrainingMinimums()
        image = self._imageCounts
        imageText = (lambda value: "" if image is None
                     else self.text("conditionThisImage").replace("{count}", format(value, ",")))
        tips = (("conditionBackgroundTip", minimums.background), ("conditionNormalTip", minimums.normal),
                ("conditionAbnormalTip", minimums.abnormal))
        # 학습에 쓸 이미지가 목록에 없으면 0 인 까닭을 덧붙인다
        hasTrainingImages = any(isTrainingTargetCase(path) for _, path in self.listedImages())
        noImagesNote = "" if hasTrainingImages else "\n" + self.text("conditionNoTrainingImages")
        for segment, (tipKey, minimum) in zip(self.bar.conditions, tips):
            segment.setToolTip(wrapTip(self.text(tipKey).replace("{minimum}", format(minimum, ",")) + noImagesNote))
        self.bar.setConditions([
            (self.text("conditionBackground"), counts.background, minimums.background, imageText(image and image.background)),
            (self.text("conditionNormal"), counts.normal, minimums.normal, imageText(image and image.normal)),
            (self.text("conditionAbnormal"), counts.abnormal, minimums.abnormal, imageText(image and image.abnormal))])
        self._placeBar()

    def _configureThresholdField(self) -> None:
        """임계값 칸을 탭, 이미지에 맞춘다: 유사도 탭은 하한, 모델 탭은 점수 척도와 그 이미지의 임계값."""
        field = self.bar.threshold
        path = self._selectedImagePath()
        threshold = self.modelFlow.displayedThreshold(path)
        if self.bar.activeTab() == TAB_MODEL and threshold is not None:
            scores = self.modelFlow.displayedScores(path)
            field.setScale(modelBaseRange(scores, threshold), scores, MODEL_DECIMALS, MODEL_STEP_FACTOR)
            field.setValue(threshold)
        else:
            field.setScale(SIMILARITY_RANGE, self._similarityScores(), SIMILARITY_DECIMALS, stepSize=SIMILARITY_STEP)
            field.setValue(self.settings.similarityFloor)

    def _onTabSelected(self, tab: str) -> None:
        self.modelFlow.dropThresholdChanging()
        self._configureThresholdField()
        self.refresh()
        self._redraw()

    def onScoreMapsChanged(self) -> None:
        """점수 맵이 바뀜(새 모델, 추론) — 임계값 칸, 잠금, 미리보기를 다시."""
        self._configureThresholdField()
        self.refresh()
        self._redraw()

    # ------------------------------------------------------------------ 한 장 추론
    def _modelLabelDefaults(self) -> dict:
        """모델 결과 라벨의 기본 이름, 색 — 그 이미지 라벨 목록에 없을 때 만든다."""
        colors = self._modelLabelColors()
        return {LABEL_BACKGROUND: {LABEL_NAME_KEY: self.text("conditionBackground"),
                                   LABEL_COLOR_KEY: list(colors[LABEL_BACKGROUND])},
                LABEL_NORMAL: {LABEL_NAME_KEY: self.text("conditionNormal"), LABEL_COLOR_KEY: list(colors[LABEL_NORMAL])},
                LABEL_ABNORMAL: {LABEL_NAME_KEY: self.text("conditionAbnormal"), LABEL_COLOR_KEY: list(colors[LABEL_ABNORMAL])}}

    # ------------------------------------------------------------------ 일괄 추론
    def _batchPlan(self):
        return planBatch([path for _, path in self.listedImages()])

    def _onBatchClicked(self) -> None:
        """'일괄 추론'. 대상은 trainingPlan.planBatch 규칙. 쓸 수 없는 이미지는 빼고 알리고, 덮어쓰기 방식과 적용 안 한 유사도 클릭 폐기를 확인한다. 쓰기는 writeBatchLabel."""
        plan = self._batchPlan()
        if not plan.isAllowed:
            return
        includeOutside = False
        if plan.outsideTargets:
            names = [self._nameOfPath(path) for path in plan.outsideTargets]
            message = self.text("batchOutsideMessage").replace("{count}", str(len(names))).replace("{names}", " · ".join(names))
            includeOutside = self._askYesNoCancel(self.text("batchOutsideTitle"), message)
            if includeOutside is None:
                return
        numberOf = {path: number for number, path in self.listedImages()}
        # 덮어쓴 이미지는 검토 전 표시가 붙어 재학습에서 빠진다
        targets = plan.targets(includeOutside)
        db = self.sync.Core_DB_Labeling['image_list']
        jobs, skipped = [], []
        for path in targets:
            number = numberOf[path]
            cube, label = self.cubeOf(number), db[number]['image_info'].get('image_label')
            if cube is None or label is None or cube.shape[:2] != np.shape(label):
                skipped.append(self._nameOfPath(path))
            else:
                jobs.append((number, path, cube))
        if skipped:
            self.modelFlow.notifyBatchProblem("noCube", " · ".join(skipped))
        if not jobs:
            self.modelFlow.notifyBatchProblem("noTargets")
            return
        # 도는 동안 고쳤는지 보려고 시작 때 라벨을 기억한다(선택 이미지는 화면 라벨 — 한 장 추론과 같게)
        selectedNumber = self._selectedImageNumber()
        startLabels = {number: np.array(self.display.image_label if number == selectedNumber
                                        else db[number]['image_info']['image_label'], copy=True)
                       for number, _, _ in jobs}
        bases = None
        if any(label.any() for label in startLabels.values()):   # 라벨이 하나도 없으면 묻지 않고 덮어쓴다
            mode = self._askInferenceMode("batchModeQuestion",
                                          all(self._canWriteOnlyClasses(path) for _, path, _ in jobs))
            if mode is None:
                return
            if mode == INFER_ONLY_CLASSES:
                bases = {path: self.modelFlow.partialBase(path, startLabels[number]) for number, path, _ in jobs}
        isSelectedIncluded = selectedNumber in startLabels
        if isSelectedIncluded and not self.similarityPreview.isEmpty() and not self._confirm("reinferTitle", "previewDiscardMessage"):
            return  # 적용 안 한 클릭은 사라진다
        self._batchStartLabels = startLabels
        self.modelFlow.startBatch(jobs, bases)

    def _nameOfPath(self, path: str) -> str:
        for number, listedPath in self.listedImages():
            if listedPath == path:
                return self.imageName(number)
        return path

    def writeBatchLabel(self, number: int, path: str, label: np.ndarray) -> str:
        """일괄 추론 결과 한 장 → WRITE_DONE, WRITE_FAILED, WRITE_DECLINED. 선택 이미지면 한 장 추론과 같은 경로(화면까지), 아니면 디스크, DB 만. 시작한 뒤 사용자가 고친 라벨은 덮어쓰기 전에 묻는다."""
        isSelected = number == self._selectedImageNumber() and path == self._selectedImagePath()
        entry = self.sync.Core_DB_Labeling['image_list'].get(number)
        if isSelected:
            current = self.display.image_label
        elif entry is not None:
            current = entry['image_info'].get('image_label')
        else:
            return WRITE_FAILED
        startLabel = self._batchStartLabels.get(number)
        if startLabel is not None and np.shape(current) == label.shape and not np.array_equal(startLabel, current) \
                and not self._confirmText(self.text("reinferTitle"),
                                          self._nameOfPath(path) + "\n" + self.text("editedDuringInferenceMessage")):
            return WRITE_DECLINED
        if isSelected:
            self._inferenceStartLabel = None                    # 위에서 이미 물었다
            return WRITE_DONE if self.applyInferenceLabel(number, path, label) else WRITE_FAILED
        if np.shape(current) != label.shape:
            return WRITE_FAILED
        try:
            writeInferenceLabel(entry, path, label, self._modelLabelDefaults())   # 화면에 없는 이미지 — 라벨 탭은 열 때 다시 만든다
        except (OSError, ValueError) as error:
            print("[autolabel] batch write failed:", path, error)
            return WRITE_FAILED
        return WRITE_DONE

    # ------------------------------------------------------------------ 설정 독, 이미지 넘기기
    def _setDockVisible(self, isVisible: bool) -> None:
        """설정 독 — 켜져 있고 이미지를 골랐을 때만 보인다."""
        self.dock.setVisible(isVisible and self.isEnabled and self._selectedImagePath() is not None)
        QtCore.QTimer.singleShot(0, self._placeBar)

    def _selectedApplyRule(self):
        path = self._selectedImagePath()
        return self.modelFlow.applyRuleFor(path) if path else None

    def _onSettingsChanged(self) -> None:
        """설정 독 값이 바뀜 — 미리보기, 임계값 칸, 바를 다시. 학습 값은 다음 학습 때 읽는다."""
        if self._isAssistOn and not self.settings.similarityAssist and not self._confirmAssistOff():
            self.settings.similarityAssist = True                # 아니요 — 미리보기도 토글도 그대로
            self.dock.assistSwitch.setCheckedQuietly(True)      # 손잡이 자리까지(신호만 막으면 꺼진 모양으로 남는다)
        self._isAssistOn = self.settings.similarityAssist
        self._configureThresholdField()
        self.refresh()
        self._redraw()

    def _neighbourImages(self):
        """이미지 목록에서 지금 이미지의 앞, 뒤 이미지가 있는가. 출력 (앞, 뒤)."""
        numbers = [number for number, _ in self.listedImages()]
        current = self._selectedImageNumber()
        if current not in numbers:
            return False, False
        index = numbers.index(current)
        return index > 0, index < len(numbers) - 1

    def _selectNeighbourImage(self, step: int) -> None:
        """‹ › — 이미지 목록에서 앞, 뒤 이미지를 고른다(이미지 탭에서 고른 것과 같은 경로: 그 선택 버튼을 누른다)."""
        numbers = [number for number, _ in self.listedImages()]
        if not numbers:
            return
        current = self._selectedImageNumber()
        index = numbers.index(current) + step if current in numbers else (0 if step > 0 else len(numbers) - 1)
        if 0 <= index < len(numbers):
            selectButton = self.sync.image_obj_dict[numbers[index]]['obj_dict']['select']
            selectButton.click()
            scrollTableTo(selectButton)

    def _onInferClicked(self) -> None:
        """'추론'. 초분광이 없으면 알리고 멈춘다. 라벨이 있으면 덮어쓰기 방식을, 적용 안 한 미리보기가 있으면 폐기를 먼저 묻는다."""
        path, number = self._selectedImagePath(), self._selectedImageNumber()
        cube = self._selectedCube()
        if path is None:
            return
        if cube is None:
            self.modelFlow.notifyInferenceFailure("noCube")
            return
        baseLabel = None
        if self.display.image_label.any():
            mode = self._askInferenceMode("inferModeQuestion", self._canWriteOnlyClasses(path))
            if mode is None:
                return
            if mode == INFER_ONLY_CLASSES:
                baseLabel = self.modelFlow.partialBase(path, self.display.image_label)
        if not self.similarityPreview.isEmpty() and not self._confirm("reinferTitle", "previewDiscardMessage"):
            return  # 적용 안 한 클릭은 사라진다
        self._inferenceStartLabel = self.display.image_label.copy()
        self.modelFlow.startInference(number, path, cube, baseLabel)

    def _canWriteOnlyClasses(self, path: str) -> bool:
        """'해당 클래스만' 이 뜻이 있는 이미지인가. 정상, 비정상을 둘 다 적용하면 사실상 전부 덮어쓰기라 선택지를 숨긴다."""
        rule = self.modelFlow.applyRuleFor(path)
        return not (rule.applyNormal and rule.applyAbnormal)

    def _inferenceModeText(self, questionKey: str, canWriteOnlyClasses: bool) -> str:
        """추론 쓰기 방식 창의 글(서식 있는 글). '해당 클래스만' 을 숨기면 그 줄도 뺀다."""
        options = [("inferOverwriteAll", "inferOverwriteAllDesc")]
        if canWriteOnlyClasses:
            options.append(("inferOnlyClasses", "inferOnlyClassesDesc"))
        lines = "".join(INFER_MODE_OPTION_HTML % (self.text(name), self.text(desc)) for name, desc in options)
        return INFER_MODE_HTML % (self.text(questionKey), lines, self.text("inferModeNote"))

    def _askInferenceMode(self, questionKey: str, canWriteOnlyClasses: bool = True) -> Optional[str]:
        """전부 덮어쓰기, 해당 클래스만, 취소 중 묻는다. canWriteOnlyClasses 가 False 면 '해당 클래스만' 을 뺀다. 취소, X, Esc = None."""
        message = self._inferenceModeText(questionKey, canWriteOnlyClasses)
        buttons = {self.text("inferOverwriteAll"): "accept"}
        if canWriteOnlyClasses:
            buttons[self.text("inferOnlyClasses")] = "ignore"
        buttons[self.lang.get("main", "messageBox", "msgCancel")] = "reject"
        answer = messageBox(mode=MESSAGE_BOX_CONFIRMATION, title=self.text("reinferTitle"), text=message, buttons=buttons)
        return {"accept": INFER_OVERWRITE_ALL, "ignore": INFER_ONLY_CLASSES}.get(answer)

    def _confirm(self, titleKey: str, messageKey: str) -> bool:
        return self._confirmText(self.text(titleKey), self.text(messageKey))

    def _askYesNoCancel(self, title: str, message: str) -> Optional[bool]:
        """예 = True, 아니오 = False, 취소, X, Esc = None. 예/아니오 둘 다 작업을 이어 가는 질문에 쓴다 — 두 버튼만 두면 Qt 가 X 를 아니오로 처리해 창을 닫아도 작업이 진행된다."""
        button = lambda key: self.lang.get("main", "messageBox", key)
        answer = messageBox(mode=MESSAGE_BOX_CONFIRMATION, title=title, text=message,
                            buttons={button("msgYes"): "accept", button("msgNo"): "ignore", button("msgCancel"): "reject"})
        return {"accept": True, "ignore": False}.get(answer)

    def _confirmText(self, title: str, message: str) -> bool:
        answer = messageBox(mode=MESSAGE_BOX_CONFIRMATION, title=title, text=message,
                            buttons={self.lang.get("main", "messageBox", "msgYes"): "accept",
                                     self.lang.get("main", "messageBox", "msgNo"): "reject"})
        return answer == "accept"

    def applyInferenceLabel(self, number: int, path: str, label: np.ndarray) -> bool:
        """추론 라벨을 디스크, DB, 화면에 쓴다(선택 이미지). 출력: 썼는가. 계산 중 다른 이미지를 골랐으면 버린다 — 화면에 없는 이미지의 DB 라벨만 바뀌면 사용자 모르게 덮어쓰게 된다."""
        if number != self._selectedImageNumber() or path != self._selectedImagePath() \
                or label.shape != self.display.image_label.shape:
            self.modelFlow.notifyInferenceFailure("imageChanged")
            return False
        # 계산하는 동안 고쳤으면 다시 묻는다
        startLabel, self._inferenceStartLabel = self._inferenceStartLabel, None
        if startLabel is not None and not np.array_equal(startLabel, self.display.image_label) \
                and not self._confirm("reinferTitle", "editedDuringInferenceMessage"):
            return False
        try:
            info, removed = writeInferenceLabel(self.sync.Core_DB_Labeling['image_list'][number], path, label,
                                                self._modelLabelDefaults())
        except (OSError, ValueError) as error:
            self.modelFlow.notifyInferenceFailure("write", str(error))
            return False
        try:
            self._clearSimilarityPreview()
            self._showModelLabel(number, label)
            if removed:
                self._dropLabelClasses(path, removed)
        except Exception as error:                              # 디스크, DB 는 이미 썼다 — 화면 갱신 실패로 앱이 끝나지 않게
            print("[autolabel] inference written but screen update failed:", error)
        QtCore.QTimer.singleShot(0, self.refresh)
        return True

    def _ensureLabelClasses(self, number: int, info: dict, label: Optional[np.ndarray] = None) -> None:
        """라벨 탭에 클래스 줄을 만들거나 이름을 맞추게 보낸다 — 오토라벨링이 라벨 탭에 클래스를 보내는 길은 모두 여기를 지난다.
        순서가 중요하다: 1) 그 이미지의 DB 라벨 목록에 먼저(없으면 라벨 탭이 그 번호를 읽다 KeyError 로 앱이 죽는다), 2) label 이 있으면 화면 라벨 교체,
        3) 라벨 탭 갱신 — 보이기 켜기가 화면의 지금 라벨로 색을 칠하므로 반드시 2) 뒤에(아니면 되돌리기 기록이 안 남는다). 입력: info = {번호: {이름, 색}}"""
        addModelLabelsToList(self.sync.Core_DB_Labeling['image_list'][number]['label_list'], info)
        if label is not None:
            self.display.replaceAutoLabel(label)
        self.sync.autoLabelEnsureLabelsSignal.emit(info)

    def _showModelLabel(self, number: int, label: np.ndarray) -> None:
        """모델이 만든 라벨을 선택 이미지 화면에(되돌리기 한 번). 라벨 탭에 클래스가 없으면 만들고 보이게 켠다(순서는 _ensureLabelClasses 참고)."""
        labelList = self.sync.Core_DB_Labeling['image_list'][number]['label_list']
        self._ensureLabelClasses(number, modelLabelInfo(label, labelList, self._modelLabelDefaults()), label)

    # ------------------------------------------------------------------ 바 위치
    def _placeBar(self) -> None:
        """기본 자리는 디스플레이 아래 가운데. 사용자가 끌어 옮겼으면 그 자리를 지키되 창, 설정 독 밖으로는 안 나가게 — 매번 끌어 놓은 자리에서 다시 계산한다."""
        host = self.barHost
        window = host.window()
        # 이미지 영역보다 넓으면 두 줄로, 최대화면 늘 한 줄
        self.bar.fitWidth(host.width(), isOneRowOnly=window.isMaximized() or window.isFullScreen())
        self._updateWindowMinimum()
        bottom = host.height() - (self.dock.height() if self.dock.isVisible() else 0)   # 독이 열려 있으면 그 위까지
        wanted = self.bar.userPosition
        if wanted is None:
            self.bar.move(max(0, (host.width() - self.bar.width()) // 2),
                          max(0, bottom - self.bar.height() - BAR_BOTTOM_MARGIN))
        else:
            self.bar.move(min(wanted.x(), max(0, host.width() - self.bar.width())),
                          min(wanted.y(), max(0, bottom - self.bar.height())))
        self.bar.raise_()

    def _updateWindowMinimum(self) -> None:
        """바가 떠 있는 동안은 창을 두 줄 바가 들어가는 폭보다 좁게 줄이지 못하게 한다(요소가 겹친다). 바가 꺼지면 원래 최소 폭으로."""
        window = self.barHost.window()
        if self._baseWindowMinWidth is None:
            self._baseWindowMinWidth = window.minimumWidth()
        needed = self._baseWindowMinWidth
        if self.bar.isVisible():
            outside = window.width() - self.barHost.width()
            barWidth = max(self.bar.minimumFitWidth(), self.bar.width() if self.bar.rowCount() == 2 else 0)
            needed = max(needed, outside + barWidth)
        if window.minimumWidth() != needed:
            window.setMinimumWidth(needed)

    def _updateShortcuts(self, *_) -> None:
        """단축키는 바가 보이고, 그 키를 직접 쓰는 위젯(focusUsesKey)에 포커스가 없을 때만 켠다."""
        focus = QtWidgets.QApplication.focusWidget()
        for shortcut in self.shortcuts:
            shortcut.setEnabled(self.bar.isVisible() and not focusUsesKey(focus, shortcut.key()[0]))

    def _updateToolLock(self, isLocked: bool) -> None:
        """유사도 보조 라벨링 중(브러시 = 유사도 클릭)에는 다른 라벨 도구(LOCKED_PEN_TOOLS)를 못 누르게 한다 — 라벨을 바꾸면 미리보기 기록과 앱 되돌리기 기록이 섞인다.
        앱이 펜 버튼을 스스로 다시 켜므로 잠긴 동안 켜지면 바로 다시 끈다(eventFilter). 풀 때는 브러시 버튼의 켜짐을 따른다(잠긴 동안 앱이 바라던 상태를 알 수 없다)."""
        pens = self.sync.pen_obj_dict
        reference = pens.get(REFERENCE_PEN_TOOL)
        isLockStart = isLocked and not self._lockedTools
        for button in [pens[name]['obj'] for name in LOCKED_PEN_TOOLS if name in pens]:
            if isLocked and button not in self._lockedTools:
                self._lockedTools.add(button)
                button.installEventFilter(self)
                self._disableQuietly(button)
            elif not isLocked and button in self._lockedTools:
                self._lockedTools.discard(button)
                button.removeEventFilter(self)
                button.setEnabled(reference['obj'].isEnabled() if reference else True)
        if isLockStart and reference and self.display.display_control_dict['drawing_mode'] in LOCKED_DRAWING_MODES:
            reference['obj'].click()  # 버튼만 끄면 그리기 모드는 그대로라 그 도구로 그려진다 — 브러시로 바꾼다

    @staticmethod
    def _disableQuietly(button: QtWidgets.QWidget) -> None:
        """버튼을 끈다. 포커스를 가진 채 끄면 Qt 가 포커스를 다음 위젯으로 넘겨 거기에 점선 테두리가 생기고, clearFocus 만 하면 창 복귀 때 타이틀바 버튼에 생긴다. 창 자체에 포커스를 넘긴다."""
        if button.hasFocus():
            button.window().setFocus(QtCore.Qt.OtherFocusReason)
        button.setEnabled(False)

    def eventFilter(self, watched, event):
        if watched in self._lockedTools and event.type() == QtCore.QEvent.EnabledChange and watched.isEnabled():
            self._disableQuietly(watched)  # 앱이 다시 켜도 끈다(_updateToolLock)
        if watched is self.barHost and event.type() in (QtCore.QEvent.Resize, QtCore.QEvent.Show, QtCore.QEvent.Hide):
            self._placeBar()
            if event.type() != QtCore.QEvent.Resize:
                self._updateShortcuts()
        elif watched is self.bar and event.type() == QtCore.QEvent.Resize:
            QtCore.QTimer.singleShot(0, self._placeBar)
        return False

    # ------------------------------------------------------------------ 유사도
    def _onBrushClick(self, row: int, col: int, labelNumber: int) -> bool:
        """디스플레이 브러시 클릭. 유사도 클릭이면 계산을 맡기고 True(칠하지 않음), 아니면 False(원래 브러시)."""
        if not evaluateBar(self._barInputs()).brushIsSimilarity or labelNumber < 1:
            return False
        cube = self._selectedCube()
        height, width = self.display.image_label.shape
        if cube is None or not (0 <= row < height and 0 <= col < width):
            return False
        if self.display.image_label[row, col] != 0:
            return True  # 이미 라벨된 자리는 유사도 기준으로 쓰지 않는다
        self._pendingGenerations.append(self._generation)
        self.similarityWorker.request(imageKey(self._selectedImagePath()), cube, row, col, labelNumber)
        return True

    def _takePendingGeneration(self) -> Optional[int]:
        return self._pendingGenerations.popleft() if self._pendingGenerations else None

    def _onSimilarityScoreReady(self, key: str, row: int, col: int, labelNumber: int, scoreMap) -> None:
        """계산이 끝난 클릭을 미리보기에 쌓는다. 그 사이 미리보기를 비웠거나 이미지가 다르면 버린다. Ctrl+S 는 비우는 것이 아니다 — 저장 직후 도착한 클릭은 다음 미리보기로 남는다."""
        if self._takePendingGeneration() != self._generation:
            return
        path = self._selectedImagePath()
        if path is None or imageKey(path) != key or not self.isEnabled:
            return
        if np.shape(scoreMap) != self.display.image_label.shape:   # 크기가 다른 점수 맵 — 첫 클릭이면 addClick 이 못 걸러 뒤 계산이 예외를 낸다
            print("[autolabel] similarity click dropped: score map size", np.shape(scoreMap))
            return
        try:
            self.similarityPreview.addClick(path, SimilarityClick(row, col, labelNumber, scoreMap))
        except ValueError as error:          # 크기가 다른 점수 맵 등 — 슬롯 예외는 앱을 끝내므로 여기서 멈춘다
            print("[autolabel] similarity click dropped:", error)
            return
        self.display.redo_memory = []  # 새 작업 — 앱의 다시 실행 기록도 버린다
        self._updateSimilarityDistribution()
        self._redraw()
        self.display.update_pen_buttons()
        self._onLabelMaybeChanged()

    def _hasPreviewHere(self) -> bool:
        path = self._selectedImagePath()
        return self.isEnabled and path is not None and self.similarityPreview.imageKey == imageKey(path)

    def _onHistory(self, isRedo: bool, dryRun: bool) -> bool:
        """Ctrl+Z, Ctrl+Y, 버튼. 유사도 미리보기에 되돌릴, 다시 할 것이 있으면 그것부터 — 미리보기 기록은 늘 앱 기록보다 새것이다(_onStrokeStart). dryRun 이면 할 수 있는지만 답한다."""
        preview = self.similarityPreview
        if not self._hasPreviewHere() or not (preview.canRedo() if isRedo else preview.canUndo()):
            if not isRedo and not dryRun and self._hasPreviewHere() and self.display.undo_memory:
                preview.clear()  # 앱 기록을 되돌리면 미리보기 쪽은 버린다(다시 실행이 시간 순서를 거꾸로 타지 않게)
            return False
        if dryRun:
            return True
        preview.redo() if isRedo else preview.undo()
        self._updateSimilarityDistribution()
        self._redraw()
        self._onLabelMaybeChanged()
        return True

    def _onErase(self, indice) -> bool:
        """지우개가 지나간 자리. 유사도 미리보기가 있으면 미리보기만 지우고 True(라벨은 그대로). 없으면 False — 원래 지우개."""
        return self._hasPreviewHere() and self._isPreviewTool() and self.similarityPreview.erase(indice)

    def _onStrokeStart(self, drawingMode: int, isLeftButton: bool) -> bool:
        """디스플레이에서 누름(획 시작, 앱이 되돌리기용 상태를 뜨기 전). 출력: 오른쪽 버튼 보조 펜을 막는가(막으면 메뉴가 열린다, 항목은 _menuPolicy).
        유사도 모드의 브러시, 지우개는 미리보기 위의 작업이라 그대로 두고, 그 밖의 길로 라벨을 건드리면 남은 미리보기를 먼저 라벨에 적용해 되돌리기 기록이 둘로 섞이지 않게 한다."""
        if not isLeftButton:
            if self._isPreviewTool():
                return True
            isSubPen = drawingMode == DRAWING_MODE_LABELING and \
                self.sync.label_control_dict['select_sub_label_number'] != LABEL_UNSELECTED
            if drawingMode == DRAWING_MODE_LABELING and not isSubPen:
                return False                 # 보조 펜이 없으면 오른쪽 클릭은 메뉴만 연다 — 라벨을 안 바꾼다
        if drawingMode not in LABEL_EDITING_MODES or not self._hasPreviewHere():
            return False
        if self.similarityPreview.isEmpty():
            # 되돌려 둔 것만 남았다 — 이번 누름이 라벨을 바꾸면 그 뒤 Ctrl+Y 가 옛 클릭을 되살리지 않게 다시 실행 기록을 버린다
            self.similarityPreview.clear()
            return False
        if isLeftButton and drawingMode in PREVIEW_DRAWING_MODES and self._isPreviewTool():
            return False
        self._applySimilarityPreview()
        return False

    def _menuPolicy(self):
        """오른쪽 메뉴를 열 때 켤 항목. 출력 (라벨 지우기, 투명도 조절, 사각형 모드 바꾸기). 보조 라벨링 중 미리보기가 있으면 라벨을 건드리는 항목을 끄고(기록이 섞이지 않게),
        사각형 모드도 끈다."""
        isAssisting = self._isPreviewTool()
        hasPreview = self._hasPreviewHere() and not self.similarityPreview.isEmpty()
        return not (isAssisting and hasPreview), not isAssisting

    def _isPreviewTool(self) -> bool:
        """브러시, 지우개가 지금 미리보기 위의 도구인가(유사도 모드)."""
        return evaluateBar(self._barInputs()).brushIsSimilarity

    def _onLabelMaybeChanged(self) -> None:
        """획 끝, 되돌리기, 다시 실행, 버튼 갱신 때(디스플레이 연결점). 지우개 획을 닫고 학습 조건을 다음 이벤트에 한 번 다시 센다. 추론으로 뺀 클래스가 되돌리기로 돌아오면 라벨 탭에 다시 넣는다."""
        if not self.display.left_drawstart:  # 누른 채인 동안은 획을 끊지 않는다(한 획 = 되돌리기 한 번)
            self.similarityPreview.endStroke()
        self._restoreLabelClasses()
        self._scheduleRecount()

    def _dropLabelClasses(self, path: str, removed: dict) -> None:
        """전부 덮어써 픽셀이 없어진 클래스를 라벨 탭에서 뺀다(그 줄만 — 선택, 보이기, 그래프 그룹을 지킨다). 되돌리기 대비로 기억한다."""
        self._removedLabelClasses.setdefault(imageKey(path), {}).update(removed)
        self.sync.autoLabelRemoveLabelsSignal.emit(sorted(removed))

    def _restoreLabelClasses(self) -> None:
        """되돌리기로 뺀 클래스의 픽셀이 돌아왔으면 그 클래스를 DB 라벨 목록, 라벨 탭에 다시 넣는다 — 없으면 그 픽셀은 색 없이 보이고 저장 때 빠진다."""
        path = self._selectedImagePath()
        removed = self._removedLabelClasses.get(imageKey(path)) if path else None
        if not removed or not isinstance(self.display.image_label, np.ndarray):
            return
        present = set(int(value) for value in np.unique(self.display.image_label))
        back = {number: entry for number, entry in removed.items()
                if number in present and number not in self.sync.label_obj_dict}
        if back:
            self._ensureLabelClasses(self._selectedImageNumber(), back)

    def _scheduleRecount(self) -> None:
        """학습 조건을 한 번 다시 센다(한 동작에 여러 번 불려도 한 번). 직전에 센 지 RECOUNT_MIN_INTERVAL_MS 가 안 지났으면 그때까지 미룬다 — 지우개, 브러시 이동마다 세면 끌린다."""
        if self.isEnabled and not self._isRefreshPending:
            self._isRefreshPending = True
            elapsedMs = (time.monotonic() - self._lastRecountTime) * 1000
            QtCore.QTimer.singleShot(int(max(0, RECOUNT_MIN_INTERVAL_MS - elapsedMs)), self._refreshPending)

    def _refreshPending(self) -> None:
        self._isRefreshPending = False
        self._lastRecountTime = time.monotonic()
        self.refresh()

    # ------------------------------------------------------------------ 학습 조건, 학습 시작
    def _liveSelectedLabel(self) -> Optional[np.ndarray]:
        """선택 이미지를 지금 저장하면 될 라벨 — 화면 라벨 + 유사도 미리보기."""
        if self._selectedImagePath() is None or not isinstance(self.display.image_label, np.ndarray):
            return None
        label = self.display.image_label
        preview = self._similarityPreviewLabel() if self._hasPreviewHere() else None
        if preview is not None and preview.shape == label.shape and preview.any():
            label = np.where(preview != 0, preview, label)
        return label

    def _trainingKeys(self) -> Set[str]:
        """학습에 쓸 이미지 키(첫 학습, 재학습 같은 규칙): 불러온 학습 대상 case 이미지 중 저장, 검토된 라벨이 있는 것 + 지금 고른 학습 시작 case 이미지(저장 전 라벨도 센다).
        case 판정은 trainingPlan 이 한다. 학습 버튼은 학습 시작 case 를 골랐을 때만 켜진다(barState)."""
        path = self._selectedImagePath()
        keys = {imageKey(path)} if path is not None and isTrainingStartCase(path) else set()
        for _, listedPath in self.listedImages():
            if isTrainingTargetCase(listedPath):
                summary = self.modelFlow.summaries.summary(listedPath)
                if summary is not None and summary.isUsable:
                    keys.add(imageKey(listedPath))
        return keys

    def _liveConditionCounts(self):
        """학습 조건 숫자 = 학습에 쓸 이미지(_trainingKeys)의 합. 선택 이미지는 저장 전 라벨, 미리보기까지 센다.
        출력 (전체 합, 지금 이미지 픽셀 수 또는 None) — 이미지 픽셀 수는 학습에 안 들어가도 늘 보인다."""
        path, keys = self._selectedImagePath(), self._trainingKeys()
        counts = self.modelFlow.conditionCounts(keys, excludePath=path)
        label = self._liveSelectedLabel()
        if label is None:
            return counts, None
        imageCounts = countClassPixels(label)
        if imageKey(path) not in keys or self._isUntouchedUnreviewedInference(path):
            return counts, imageCounts
        return counts.add(imageCounts), imageCounts

    def _isUntouchedUnreviewedInference(self, path: str) -> bool:
        """검토 전 추론 그대로(저장 안 한 고침 없음) — 학습에서 빠지므로 조건 숫자에도 넣지 않는다(바 숫자와 학습이 어긋나지 않게)."""
        summary = self.modelFlow.summaries.summary(path)
        return summary is not None and summary.isUnreviewedInference and not self._hasUnsavedChanges()

    def _hasUnsavedChanges(self) -> bool:
        """선택 이미지에 저장 안 한 라벨, 미리보기가 있는가(디스크 label.npy 와 비교)."""
        path = self._selectedImagePath()
        if path is None or not isinstance(self.display.image_label, np.ndarray):
            return False
        if self._hasPreviewHere() and not self.similarityPreview.isEmpty():
            return True
        saved = readLabel(path)
        return saved is None or not np.array_equal(saved, self.display.image_label)

    def _onTrainClicked(self) -> None:
        """'모델 학습'. 선택 이미지에 저장 안 한 것이 있으면 저장하고 학습할지 묻는다(학습은 저장된 라벨로만 한다)."""
        keys, path = set(self._trainingKeys()), self._selectedImagePath()
        if path and imageKey(path) in keys and self._hasUnsavedChanges():
            save = self._askYesNoCancel(self.text("trainUnsavedTitle"), self.text("trainUnsavedMessage"))
            if save is None:
                return
            if save:
                self.sync.mainwindow_to_core_signal.emit({'mode': 1})
        self.modelFlow.startTraining(keys)

    def _onSimilarityFailed(self, message: str) -> None:
        self._takePendingGeneration()
        print("[autolabel] similarity failed:", message)

    def _similarityScores(self):
        if self._selectedImagePath() is None:
            return None
        return self.similarityPreview.latestCandidateScores(self.display.image_label != 0)

    def _updateSimilarityDistribution(self) -> None:
        if self.bar.activeTab() == TAB_SIMILARITY:
            self.bar.threshold.setScale(SIMILARITY_RANGE, self._similarityScores(), SIMILARITY_DECIMALS, stepSize=SIMILARITY_STEP)

    def _onThresholdChanging(self, value: float) -> None:
        """선을 끄는 동안 — 바뀔 때마다 미리보기를 다시 계산한다. 추론한 이미지인데 라벨을 고쳤으면 막는다."""
        if self.bar.activeTab() == TAB_SIMILARITY:
            self.settings.similarityFloor = value
        elif self._isEditedInference():
            self._refuseThreshold()
            return
        else:
            self.modelFlow.setThresholdChanging(value)
        self._skipRecountOnce = True                     # 미리보기만 바뀐 그리기 — 라벨은 그대로라 조건을 다시 세지 않는다
        try:
            self._redraw()
        finally:
            self._skipRecountOnce = False                # 그리지 않았으면(이미지 없음) 다음 진짜 그리기가 세기를 건너뛰지 않게

    def _onThresholdCommitted(self, value: float) -> None:
        """놓거나 입력함. 모델 탭이면 앞으로 추론의 기본 임계값이 되고, 추론한 이미지면 그 값으로 라벨을 다시 만든다
        (되돌리기 한 번, 저장은 Ctrl+S). 라벨을 펜으로 고쳤으면 바꾸지 않는다."""
        if self.bar.activeTab() == TAB_SIMILARITY:
            self.settings.similarityFloor = value
            self._redraw()
            return
        path = self._selectedImagePath()
        if self.modelFlow.storedScore(path) is None:
            self.modelFlow.commitThreshold(value)
            self._redraw()
            return
        label = self.modelFlow.relabelWithThreshold(path, value, self.display.image_label)
        if label is None:
            self._refuseThreshold()
            return
        self._showModelLabel(self._selectedImageNumber(), label)
        self.refresh()

    def _onThresholdReverted(self, value: float) -> None:
        """끌었다 시작 값으로 놓음 — 라벨은 그대로, 끄는 동안의 미리보기만 거둔다."""
        if self.bar.activeTab() == TAB_SIMILARITY:
            self.settings.similarityFloor = value
        else:
            self.modelFlow.dropThresholdChanging()
        self._redraw()

    def _isEditedInference(self) -> bool:
        path = self._selectedImagePath()
        return self.modelFlow.storedScore(path) is not None and not self.modelFlow.isAdjustable(path, self.display.image_label)

    def _refuseThreshold(self) -> None:
        """라벨을 고친 이미지 — 임계값 변경을 버리고 칸을 원래 값, 잠금으로 되돌린다."""
        self.modelFlow.dropThresholdChanging()
        self._configureThresholdField()
        self.refresh()
        self._redraw()

    def _onAutoThresholdToggled(self, isAuto: bool) -> None:
        """[자동] 켜기, 끄기 — 지금 이미지(추론한 것)의 라벨도 그 임계값으로 바로 다시 만든다(되돌리기 한 번)."""
        self.modelFlow.useAutoThreshold(isAuto)
        label = self.modelFlow.relabelWithCurrentThreshold(self._selectedImagePath(), self.display.image_label)
        if label is not None:
            self._showModelLabel(self._selectedImageNumber(), label)
            self.refresh()
        self._configureThresholdField()
        self._redraw()

    def _similarityPreviewLabel(self) -> Optional[np.ndarray]:
        """쌓인 클릭 → 미리보기 라벨. 다시 그릴 때마다 불린다. 지금 라벨이 있는 자리는 뺀다(미리보기 뒤에 라벨이 생겼으면 그 라벨이 이긴다)."""
        removed = {click.labelNumber for click in self.similarityPreview.clicks} - set(self.sync.label_obj_dict)
        if removed:
            self.similarityPreview.removeLabels(removed)  # 라벨 탭에서 지운 클래스는 미리보기에서도 지운다
        if self.similarityPreview.isEmpty():
            return None
        labeledMask = self.display.image_label != 0
        label = self.similarityPreview.currentLabel(self.settings.similarityFloor, labeledMask,
                                                    self.settings.normalCapPerClick, self.settings.abnormalCapPerClick)
        return np.where(labeledMask, 0, label)

    def _composeFrame(self, screenRgb):
        """디스플레이가 그리기 직전에 부른다 — 지금 이미지의 미리보기만 얹는다. 순서: 모델 탭의 임계값 끄는 중 라벨, 불확실 표시, 유사도 미리보기."""
        path = self._selectedImagePath()
        if not self.isEnabled or path is None or not isinstance(screenRgb, np.ndarray):
            return screenRgb
        # 라벨이 바뀌는 길은 많다 — 모두 결국 다시 그리므로 여기서 다시 센다
        if self._skipRecountOnce:
            self._skipRecountOnce = False
        else:
            self._scheduleRecount()
        try:
            frame = screenRgb
            if self.bar.activeTab() == TAB_MODEL:
                frame = self._composeThresholdPreview(frame, path)
            frame = self._composeUncertain(frame, path)
            previewLabel = self._similarityPreviewLabel() if self.similarityPreview.imageKey == imageKey(path) else None
            if previewLabel is not None:
                frame = composePreview(frame, self.display.image_origin,
                                       PreviewFrame(imageKey(path), previewLabel, hiddenLabels=self._hiddenLabelTabLabels()),
                                       self._labelColor)
            return frame
        except Exception as error:  # 예외가 나면 화면을 못 그리므로 미리보기만 포기
            print("[autolabel] preview draw failed:", error)
            return screenRgb

    def _composeThresholdPreview(self, frame, path: str):
        """모델 탭에서 추론한 이미지의 임계값을 끄는 동안의 라벨을 라벨 대신 얹는다."""
        shape = self.display.image_label.shape
        label = self.modelFlow.inferenceDragPreview(path)
        if label is None or label.shape != shape:
            return frame
        return composePreview(frame, self.display.image_origin,
                              PreviewFrame(imageKey(path), label, replaceLabels=True,
                                           hiddenLabels=self._hiddenModelLabels(path) | self._hiddenLabelTabLabels()),
                              self._labelColor)

    def _composeUncertain(self, frame, path: str):
        """불확실 표시(설정에서 켰을 때) — 점수 맵이 있는 이미지에만, 탭과 상관없이."""
        uncertain = self.modelFlow.uncertainFor(path) if self.settings.showUncertain else None
        shape = self.display.image_label.shape
        if uncertain is None or uncertain.shape != shape:
            return frame
        return composePreview(frame, self.display.image_origin,
                              PreviewFrame(imageKey(path), np.zeros(shape, np.int64), extraMask=uncertain,
                                           extraColor=self.settings.uncertainColor), self._labelColor)

    def _hiddenModelLabels(self, path: str) -> frozenset:
        """설정 독 표시를 끈 모델 결과 라벨. 자동이면 이미지 적용 규칙을 따른다."""
        if self.settings.useAutoApply:
            rule = self.modelFlow.applyRuleFor(path)
            shown = {LABEL_NORMAL: rule.applyNormal, LABEL_ABNORMAL: rule.applyAbnormal, LABEL_BACKGROUND: rule.applyBackground}
        else:
            shown = {LABEL_NORMAL: self.settings.showNormal, LABEL_ABNORMAL: self.settings.showAbnormal,
                     LABEL_BACKGROUND: self.settings.showBackground}
        return frozenset(number for number, isShown in shown.items() if not isShown)

    def _hiddenLabelTabLabels(self) -> frozenset:
        """라벨 탭에서 보기(눈)를 끈 클래스 — 미리보기도 숨긴다(숨김일 뿐 남아 있어 적용도 된다)."""
        hidden = set()
        for number, entry in self.sync.label_obj_dict.items():
            showButton = entry.get('obj_dict', {}).get('show') if isinstance(entry, dict) else None
            if showButton is not None and not showButton.isChecked():
                hidden.add(number)
        return frozenset(hidden)

    def _redraw(self) -> None:
        """지금 화면을 다시 그린다(미리보기 얹기). 이미지를 바꾸는 중에는 디스플레이가 빈 값이라 건너뛴다."""
        if self._selectedImagePath() is not None and isinstance(self.display.image_rgb, np.ndarray):
            self.display.update_image_display(self.display.image_rgb)

    def _discardPreviewWithNotice(self) -> None:
        """이미지를 바꾸거나 오토라벨링을 끌 때 적용 안 한 미리보기가 사라진다 — 클릭이 있었으면 알린다."""
        if not self.similarityPreview.isEmpty():
            self.modelFlow.notifyPreviewDiscarded()
        self._clearSimilarityPreview()

    def _clearSimilarityPreview(self) -> None:
        self.similarityPreview.clear()
        self._generation += 1
        self.similarityWorker.releaseImage()
        self._updateSimilarityDistribution()
        self._redraw()

    def _onBeforeSave(self, saveRequest: dict) -> None:
        """Ctrl+S 직전(같은 스레드): 유사도 미리보기를 라벨에 적용한다 → 이어지는 저장에 포함된다."""
        if saveRequest.get('mode') == 2 and not saveRequest.get('save_as_path'):
            return                           # 다른 이름으로 저장을 취소함 — 저장이 안 되므로 적용도 안 한다
        # 저장은 이 시그널 바로 뒤에 일어난다 — 다음 이벤트에서 저장된 라벨로 조건을 다시 센다(미리보기 없는 저장도 포함)
        QtCore.QTimer.singleShot(0, self.refresh)
        if self._hasPreviewHere():
            self._applySimilarityPreview()

    def _confirmAssistOff(self) -> bool:
        """보조 라벨링을 끄려 함 — 적용 안 한 미리보기가 있으면 먼저 묻는다. 예 = 적용하고 끔, 아니요 = False(토글을 되돌린다)."""
        if not self._hasPreviewHere() or self.similarityPreview.isEmpty():
            return True
        if not self._confirm("previewApplyTitle", "previewApplyOnAssistOffMessage"):
            return False
        self._applySimilarityPreview()
        return True

    def _applySimilarityPreview(self) -> bool:
        """미리보기를 라벨에 적용하고 비운다(앱 되돌리기 한 번으로 취소). 맡겨 둔 클릭은 버리지 않는다 — 적용 직후 도착한 클릭은 다음 미리보기로 남는다. 출력: 라벨에 칠한 것이 있었는가."""
        previewLabel = self._similarityPreviewLabel()
        self.similarityPreview.clear()
        isApplied = previewLabel is not None and bool(previewLabel.any())
        if isApplied:
            self.display.applyAutoLabelPixels(previewLabel)
        self._updateSimilarityDistribution()
        self._redraw()
        return isApplied

    def _onImageEvent(self, event: dict) -> None:
        """이미지 선택, 해제(이미지 탭) — 다른 이미지의 미리보기는 남기지 않는다."""
        if event.get('mode') in ('show', 'unchecked'):
            self.modelFlow.dropThresholdChanging()
            self._discardPreviewWithNotice()
            self._configureThresholdField()
            self.refresh()
            self._setDockVisible(self.bar.settingsButton.isChecked())
        if event.get('mode') == 'show' and self.isEnabled:
            QtCore.QTimer.singleShot(0, self._showCurrentLabels)   # 라벨 탭이 이 이미지 줄을 다 만든 다음에(숨김으로 만들어진다)

    def _onImageListEvent(self, event: dict) -> None:
        """이미지 추가, 삭제(core 로 가는 요청) — core 가 처리한 뒤에 목록을 다시 본다."""
        if event.get('mode') in ('create', 'delete') and event.get('type') == 'image':
            QtCore.QTimer.singleShot(0, self._onImageListChanged)

    def _onImageListChanged(self) -> None:
        self.modelFlow.pruneImages([path for _, path in self.listedImages()])
        self.refresh()
